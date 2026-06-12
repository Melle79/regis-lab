"""
KI-Provider Abstraktion für Regis-Lab.
Unterstützte Anbieter: Ollama, Anthropic, OpenAI, Google, Mistral, Groq
"""
import requests
import json
import logging

log = logging.getLogger("ha_dashboard.ki_providers")

PROVIDERS = {
    "ollama":    {"name": "Ollama (lokal)",    "models": [], "key_required": False},
    "anthropic": {"name": "Anthropic (Claude)", "models": ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"], "key_required": True},
    "openai":    {"name": "OpenAI (GPT)",       "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"], "key_required": True},
    "google":    {"name": "Google (Gemini)",    "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"], "key_required": True},
    "mistral":   {"name": "Mistral",            "models": ["mistral-small-latest", "mistral-medium-latest", "mistral-large-latest"], "key_required": True},
    "groq":      {"name": "Groq",               "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"], "key_required": True},
}


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
    yield json.dumps({"done": True}) + "\n"


def chat_openai(messages: list, model: str, api_key: str):
    """Streaming-Chat via OpenAI API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "gpt-4o-mini",
        "messages": messages,
        "stream": True,
        "max_tokens": 4096,
    }
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers=headers, json=payload, stream=True, timeout=120)
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    yield json.dumps({"done": True}) + "\n"
                    return
                try:
                    chunk = json.loads(data)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield json.dumps({"message": {"content": content}, "done": False}) + "\n"
                except Exception:
                    pass
    yield json.dumps({"done": True}) + "\n"


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
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    if content:
                        yield json.dumps({"message": {"content": content}, "done": False}) + "\n"
                except Exception:
                    pass
    yield json.dumps({"done": True}) + "\n"


def chat_mistral(messages: list, model: str, api_key: str):
    """Streaming-Chat via Mistral API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "mistral-small-latest",
        "messages": messages,
        "stream": True,
        "max_tokens": 4096,
    }
    r = requests.post("https://api.mistral.ai/v1/chat/completions",
                      headers=headers, json=payload, stream=True, timeout=120)
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    yield json.dumps({"done": True}) + "\n"
                    return
                try:
                    chunk = json.loads(data)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield json.dumps({"message": {"content": content}, "done": False}) + "\n"
                except Exception:
                    pass
    yield json.dumps({"done": True}) + "\n"


def chat_groq(messages: list, model: str, api_key: str):
    """Streaming-Chat via Groq API (OpenAI-kompatibel)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or "llama-3.1-8b-instant",
        "messages": messages,
        "stream": True,
        "max_tokens": 4096,
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=payload, stream=True, timeout=120)
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    yield json.dumps({"done": True}) + "\n"
                    return
                try:
                    chunk = json.loads(data)
                    content = chunk["choices"][0]["delta"].get("content", "")
                    if content:
                        yield json.dumps({"message": {"content": content}, "done": False}) + "\n"
                except Exception:
                    pass
    yield json.dumps({"done": True}) + "\n"


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
