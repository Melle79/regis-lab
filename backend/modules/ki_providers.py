"""
KI-Provider Abstraktion für Regis-Lab.
Unterstützte Anbieter: Ollama, Anthropic, OpenRouter, OpenAI, Google, Mistral, Groq

Jeder Streaming-Chat liefert JSON-Zeilen:
  {"message": {"content": "..."}, "done": false}
  {"usage": {"prompt_tokens": 12, "completion_tokens": 34, "total_tokens": 46,
             "cost": 0.00012, "cost_currency": "USD"}, "done": false}
  {"done": true}
Dabei ist die usage-Zeile optional – nicht jeder Anbieter liefert Verbrauch
oder Kosten. Kosten in USD sind derzeit nur über OpenRouter verlässlich.
"""
import requests
import json
import logging

log = logging.getLogger("ha_dashboard.ki_providers")

OPENROUTER_URL = "https://openrouter.ai/api/v1"

PROVIDERS = {
    "ollama":     {"name": "Ollama (lokal)",     "models": [], "key_required": False},
    "openrouter": {"name": "OpenRouter",          "models": ["deepseek/deepseek-v4.1-flash", "deepseek/deepseek-v4-pro", "deepseek/deepseek-chat-v3.1"], "key_required": True},
    "anthropic":  {"name": "Anthropic (Claude)",  "models": ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"], "key_required": True},
    "openai":     {"name": "OpenAI (GPT)",        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"], "key_required": True},
    "google":     {"name": "Google (Gemini)",     "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"], "key_required": True},
    "mistral":    {"name": "Mistral",             "models": ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"], "key_required": True},
    "groq":       {"name": "Groq",                "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"], "key_required": True},
}


def usage_line(usage: dict, cost=None, model_pricing=None):
    """Baut die Verbrauchszeile. cost (USD) hat Vorrang, sonst aus Preisen rechnen."""
    if not usage:
        return None
    p = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    c = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    if p == 0 and c == 0:
        return None
    total = int(usage.get("total_tokens") or (p + c))
    out = {"prompt_tokens": p, "completion_tokens": c, "total_tokens": total}
    if isinstance(cost, (int, float)):
        out["cost"] = round(float(cost), 6)
        out["cost_currency"] = "USD"
        out["cost_estimated"] = False
    elif model_pricing:
        try:
            est = p * float(model_pricing.get("prompt") or 0) + c * float(model_pricing.get("completion") or 0)
            out["cost"] = round(est, 6)
            out["cost_currency"] = "USD"
            out["cost_estimated"] = True
        except Exception:
            pass
    return json.dumps({"usage": out, "done": False}) + "\n"


def chat_anthropic(messages: list, model: str, api_key: str, system: str = ""):
    """Streaming-Chat via Anthropic API."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    chat_msgs = [m for m in messages if m["role"] != "system"]
    if not system:
        system_msgs = [m for m in messages if m["role"] == "system"]
        system = system_msgs[-1]["content"] if system_msgs else ""
    with client.messages.stream(
        model=model or "claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=system,
        messages=chat_msgs,
    ) as stream:
        for text in stream.text_stream:
            yield json.dumps({"message": {"content": text}, "done": False}) + "\n"
        try:
            final = stream.get_final_message()
            line = usage_line(getattr(final, "usage", None) and {
                "prompt_tokens": getattr(final.usage, "input_tokens", 0),
                "completion_tokens": getattr(final.usage, "output_tokens", 0),
            })
            if line:
                yield line
        except Exception as e:
            log.debug(f"Anthropic usage nicht lesbar: {e}")
    yield json.dumps({"done": True}) + "\n"


def _openai_compatible(url, messages, model, api_key, extra_headers=None, include_usage=True):
    """Gemeinsamer Streaming-Chat fuer OpenAI-kompatible APIs."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_tokens": 4096,
    }
    if include_usage:
        payload["stream_options"] = {"include_usage": True}
    r = requests.post(url, headers=headers, json=payload, stream=True, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"{url} antwortete {r.status_code}: {r.text[:300]}")
    usage = None
    for line in r.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8")
        if not text.startswith("data: "):
            continue
        data = text[6:]
        if data.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except Exception:
            continue
        if chunk.get("usage"):
            usage = chunk["usage"]
        choices = chunk.get("choices") or []
        if choices:
            content = (choices[0].get("delta") or {}).get("content") or ""
            if content:
                yield json.dumps({"message": {"content": content}, "done": False}) + "\n"
    u = usage_line_for(model, usage)
    if u:
        yield u
    yield json.dumps({"done": True}) + "\n"


def usage_line_for(model, usage):
    """Verbrauchszeile inkl. Kosten, wenn der Anbieter sie liefert."""
    if not usage:
        return None
    cost = usage.get("cost")
    pricing = None
    if not isinstance(cost, (int, float)) and "/" in str(model):
        pricing = openrouter_pricing(model)
    return usage_line(usage, cost=cost, model_pricing=pricing)


_PRICING_CACHE = {}


def openrouter_pricing(model):
    """Preise pro Token aus dem OpenRouter-Katalog (einmal je Modell)."""
    if model in _PRICING_CACHE:
        return _PRICING_CACHE[model]
    info = None
    try:
        r = requests.get(OPENROUTER_URL + "/models", timeout=12)
        if r.status_code == 200:
            for m in r.json().get("data", []):
                if m.get("id") == model:
                    info = m.get("pricing") or {}
                    break
    except Exception as e:
        log.debug(f"OpenRouter-Preise nicht abrufbar: {e}")
    _PRICING_CACHE[model] = info
    return info


def openrouter_models(query="", limit=600):
    """Modellkatalog von OpenRouter, optional gefiltert."""
    try:
        r = requests.get(OPENROUTER_URL + "/models", timeout=20)
        if r.status_code != 200:
            return []
        items = r.json().get("data", [])
    except Exception as e:
        log.warning(f"OpenRouter-Katalog nicht abrufbar: {e}")
        return []
    q = (query or "").strip().lower()
    out = []
    for m in items:
        mid = m.get("id", "")
        if not mid:
            continue
        if q and q not in mid.lower() and q not in (m.get("name") or "").lower():
            continue
        pr = m.get("pricing") or {}
        out.append({
            "id": mid,
            "name": m.get("name") or mid,
            "context": m.get("context_length"),
            "prompt_price": pr.get("prompt"),
            "completion_price": pr.get("completion"),
        })
    out.sort(key=lambda x: x["id"])
    return out[:limit]


def openrouter_key_info(api_key):
    """Guthaben und Verbrauch des OpenRouter-Schluessels."""
    if not api_key:
        return {"error": "Kein OpenRouter-Schluessel hinterlegt"}
    try:
        r = requests.get(OPENROUTER_URL + "/key",
                         headers={"Authorization": f"Bearer {api_key}"}, timeout=12)
        if r.status_code != 200:
            return {"error": f"OpenRouter antwortete {r.status_code}"}
        d = r.json().get("data", {}) or {}
        return {
            "label": d.get("label"),
            "usage": d.get("usage"),
            "limit": d.get("limit"),
            "limit_remaining": d.get("limit_remaining"),
            "is_free_tier": d.get("is_free_tier"),
        }
    except Exception as e:
        return {"error": str(e)}


def chat_openai(messages: list, model: str, api_key: str):
    """Streaming-Chat via OpenAI API."""
    yield from _openai_compatible(
        "https://api.openai.com/v1/chat/completions",
        messages, model or "gpt-4o-mini", api_key,
    )


def chat_openrouter(messages: list, model: str, api_key: str):
    """Streaming-Chat via OpenRouter - liefert Token UND Kosten mit."""
    yield from _openai_compatible(
        OPENROUTER_URL + "/chat/completions",
        messages, model or "deepseek/deepseek-v4.1-flash", api_key,
        extra_headers={
            "HTTP-Referer": "https://github.com/Melle79/regis-lab",
            "X-Title": "Regis-Lab",
        },
    )


def chat_groq(messages: list, model: str, api_key: str):
    """Streaming-Chat via Groq API (OpenAI-kompatibel)."""
    yield from _openai_compatible(
        "https://api.groq.com/openai/v1/chat/completions",
        messages, model or "llama-3.1-8b-instant", api_key,
    )


def chat_mistral(messages: list, model: str, api_key: str):
    """Streaming-Chat via Mistral (ohne stream_options - Mistral lehnt das ab)."""
    yield from _openai_compatible(
        "https://api.mistral.ai/v1/chat/completions",
        messages, model or "mistral-small-latest", api_key,
        include_usage=False,
    )


def chat_google(messages: list, model: str, api_key: str):
    """Streaming-Chat via Google Gemini API."""
    # Nachrichten konvertieren
    contents = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    system_msgs = [m for m in messages if m["role"] == "system"]
    payload = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 4096},
    }
    if system_msgs:
        payload["systemInstruction"] = {"parts": [{"text": system_msgs[-1]["content"]}]}

    model_name = model or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?key={api_key}&alt=sse"
    r = requests.post(url, json=payload, stream=True, timeout=120)
    usage = None
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if data.get("usageMetadata"):
                        um = data["usageMetadata"]
                        usage = {
                            "prompt_tokens": um.get("promptTokenCount", 0),
                            "completion_tokens": um.get("candidatesTokenCount", 0),
                            "total_tokens": um.get("totalTokenCount", 0),
                        }
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    if content:
                        yield json.dumps({"message": {"content": content}, "done": False}) + "\n"
                except Exception:
                    pass
    u = usage_line(usage or {})
    if u:
        yield u
    yield json.dumps({"done": True}) + "\n"


def split_provider(provider: str):
    """Zerlegt die Provider-Einstellung in (Basis-Anbieter, ist_rückfall).

    Konvention der Einstellungsmaske:
      "anthropic"          → Cloud ist der Primärweg
      "anthropic_fallback" → Ollama ist der Primärweg, Cloud nur als Rückfall
      "ollama"             → nur lokal
      "ollama_with_fallback" → Altwert, entspricht "anthropic_fallback"
    """
    if provider == "ollama_with_fallback":
        return "anthropic", True
    if provider.endswith("_fallback"):
        return provider[: -len("_fallback")], True
    return provider, False


def generate_text(prompt: str, provider: str, model: str, api_key: str,
                  ollama_url: str = "", system: str = "") -> str:
    """Einfache Text-Completion (non-streaming) für alle Provider."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    full_text = ""
    try:
        if provider == "anthropic":
            for chunk in chat_anthropic(messages, model, api_key, system):
                data = json.loads(chunk)
                full_text += data.get("message", {}).get("content", "")
        elif provider == "openai":
            for chunk in chat_openai(messages, model, api_key):
                data = json.loads(chunk)
                full_text += data.get("message", {}).get("content", "")
        elif provider == "google":
            for chunk in chat_google(messages, model, api_key):
                data = json.loads(chunk)
                full_text += data.get("message", {}).get("content", "")
        elif provider == "mistral":
            for chunk in chat_mistral(messages, model, api_key):
                data = json.loads(chunk)
                full_text += data.get("message", {}).get("content", "")
        elif provider == "groq":
            for chunk in chat_groq(messages, model, api_key):
                data = json.loads(chunk)
                full_text += data.get("message", {}).get("content", "")
        elif provider == "openrouter":
            for chunk in chat_openrouter(messages, model, api_key):
                data = json.loads(chunk)
                full_text += data.get("message", {}).get("content", "")
        elif provider in ("ollama", "ollama_with_fallback") and ollama_url:
            r = requests.post(
                ollama_url + "/api/generate",
                json={"model": model, "prompt": prompt if not system else f"{system}\n\n{prompt}", "stream": False},
                timeout=60,
            )
            full_text = r.json().get("response", "").strip() if r.status_code == 200 else ""
    except Exception as e:
        log.error(f"generate_text Fehler ({provider}): {e}")
    return full_text.strip()
