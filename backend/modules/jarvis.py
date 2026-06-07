"""
Modul: jarvis
KI-Assistent mit Ollama-Anbindung, HA-Zugriff und Chat-Persistenz.
"""
import json
import os
import uuid
import threading
from datetime import datetime
import requests
from flask import jsonify, request, Response, stream_with_context
from modules.base import BaseModule

CHATS_DIR = "/data/chats"


class Module(BaseModule):
    name    = "jarvis"
    version = "2.0.0"

    def register(self):
        os.makedirs(CHATS_DIR, exist_ok=True)

        # ── Chat-Verwaltung ──────────────────────────────────────────

        @self.app.route("/api/jarvis/chats")
        def list_chats():
            chats = []
            for f in sorted(os.listdir(CHATS_DIR), reverse=True):
                if not f.endswith(".json"): continue
                try:
                    with open(os.path.join(CHATS_DIR, f)) as fh:
                        d = json.load(fh)
                    chats.append({
                        "id":         d["id"],
                        "title":      d.get("title", "Neuer Chat"),
                        "updated_at": d.get("updated_at", ""),
                        "message_count": len(d.get("messages", [])),
                    })
                except Exception:
                    pass
            return jsonify({"chats": chats})

        @self.app.route("/api/jarvis/chats", methods=["POST"])
        def create_chat():
            chat_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            chat = {
                "id":         chat_id,
                "title":      "Neuer Chat",
                "created_at": now,
                "updated_at": now,
                "messages":   [],
            }
            _save_chat(chat)
            return jsonify(chat)

        @self.app.route("/api/jarvis/chats/<chat_id>")
        def get_chat(chat_id):
            chat = _load_chat(chat_id)
            if not chat:
                return jsonify({"error": "Chat nicht gefunden"}), 404
            return jsonify(chat)

        @self.app.route("/api/jarvis/chats/<chat_id>", methods=["PATCH"])
        def update_chat(chat_id):
            chat = _load_chat(chat_id)
            if not chat:
                return jsonify({"error": "Chat nicht gefunden"}), 404
            data = request.get_json() or {}
            if "title" in data:
                chat["title"] = data["title"]
            if "messages" in data:
                chat["messages"] = data["messages"]
            chat["updated_at"] = datetime.now().isoformat()
            _save_chat(chat)
            return jsonify({"ok": True})

        @self.app.route("/api/jarvis/chats/<chat_id>", methods=["DELETE"])
        def delete_chat(chat_id):
            path = os.path.join(CHATS_DIR, f"{chat_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return jsonify({"ok": True})

        # ── Chat ────────────────────────────────────────────────────

        @self.app.route("/api/jarvis/chats/<chat_id>/chat", methods=["POST"])
        def chat(chat_id):
            body    = request.get_json() or {}
            message = body.get("message", "")
            display  = body.get("display", message)  # Anzeige-Version (ohne Dateiinhalt)
            model   = body.get("model") or self._get_setting("jarvis_model", "")
            ollama_url = self._get_ollama_url()

            if not ollama_url:
                return jsonify({"error": "Ollama URL nicht konfiguriert"}), 400
            if not model:
                return jsonify({"error": "Kein Modell ausgewählt"}), 400
            if not message:
                return jsonify({"error": "Keine Nachricht"}), 400

            # Chat laden oder erstellen
            chat_data = _load_chat(chat_id)
            if not chat_data:
                return jsonify({"error": "Chat nicht gefunden"}), 404

            # Nachricht hinzufügen
            chat_data["messages"].append({"role": "user", "content": display, "timestamp": datetime.now().isoformat(), "model": model})

            # System-Prompt
            ha_control = self.config._settings.get("jarvis_ha_control", False)
            system_prompt = self._build_system_prompt() if ha_control else self._build_system_prompt_no_ha()

            # KI bekommt vollen Text (inkl. Dateiinhalt), gespeichert wird display-Version
            ki_messages = chat_data["messages"][:-1] + [{"role": "user", "content": message}]
            full_messages = [{"role": "system", "content": system_prompt}] + ki_messages

            def generate():
                full_text = ""
                try:
                    r = requests.post(
                        f"{ollama_url}/api/chat",
                        json={
                            "model":    model,
                            "messages": full_messages,
                            "stream":   True,
                        },
                        stream=True,
                        timeout=120,
                    )
                    for line in r.iter_lines():
                        if line:
                            decoded = line.decode()
                            try:
                                data = json.loads(decoded)
                                chunk = data.get("message", {}).get("content", "")
                                full_text += chunk
                            except Exception:
                                pass
                            yield decoded + "\n"
                except Exception as e:
                    yield json.dumps({"error": str(e)}) + "\n"
                    return

                # Antwort speichern mit ha_control Status
                chat_data["messages"].append({"role": "assistant", "content": full_text, "ha_control": ha_control, "timestamp": datetime.now().isoformat(), "model": model})
                chat_data["updated_at"] = datetime.now().isoformat()

                # Titel automatisch durch KI generieren (erste Nachricht)
                if chat_data.get("title") == "Neuer Chat" and message:
                    try:
                        title_r = requests.post(
                            f"{ollama_url}/api/generate",
                            json={
                                "model": model,
                                "prompt": f"Erstelle einen kurzen Titel (max. 5 Wörter, kein Anführungszeichen) für dieses Gespräch. Nur den Titel ausgeben, nichts sonst.

Nachricht: {message[:200]}",
                                "stream": False,
                            },
                            timeout=15,
                        )
                        if title_r.status_code == 200:
                            title = title_r.json().get("response", "").strip().strip('"'').strip()
                            chat_data["title"] = title[:60] if title else message[:50]
                        else:
                            chat_data["title"] = message[:50] + ("…" if len(message) > 50 else "")
                    except Exception:
                        chat_data["title"] = message[:50] + ("…" if len(message) > 50 else "")

                # HA-Action ausführen wenn erlaubt
                if ha_control:
                    import re
                    match = re.search(r'\{"action":\s*(\{[^}]+\})\}', full_text)
                    if match:
                        try:
                            action = json.loads(match.group(1))
                            self._call_ha_service(
                                action.get("domain", ""),
                                action.get("service", ""),
                                {"entity_id": action.get("entity_id", "")},
                            )
                        except Exception as e:
                            self.log.warning(f"Action-Fehler: {e}")

                _save_chat(chat_data)

            return Response(
                stream_with_context(generate()),
                mimetype="application/x-ndjson",
            )

        # ── Modelle ─────────────────────────────────────────────────

        @self.app.route("/api/jarvis/models")
        def get_models():
            ollama_url = self._get_ollama_url()
            if not ollama_url:
                return jsonify({"error": "Ollama URL nicht konfiguriert"}), 400
            try:
                r = requests.get(f"{ollama_url}/api/tags", timeout=5)
                if r.status_code == 200:
                    models = [m["name"] for m in r.json().get("models", [])]
                    return jsonify({"models": models})
                return jsonify({"error": f"Ollama Fehler: {r.status_code}"}), 500
            except Exception as e:
                return jsonify({"error": f"Ollama nicht erreichbar: {e}"}), 503

        @self.app.route("/api/jarvis/chats/<chat_id>/system-message", methods=["POST"])
        def add_system_message(chat_id):
            chat = _load_chat(chat_id)
            if not chat:
                return jsonify({"error": "Chat nicht gefunden"}), 404
            data = request.get_json() or {}
            content = data.get("content", "")
            if content:
                chat["messages"].append({"role": "system", "content": content})
                chat["updated_at"] = datetime.now().isoformat()
                _save_chat(chat)
            return jsonify({"ok": True})

        @self.app.route("/api/jarvis/chats/<chat_id>/attachments", methods=["POST"])
        def save_attachment(chat_id):
            """Datei-Anhang speichern."""
            data     = request.get_json() or {}
            filename = data.get("filename", "")
            content  = data.get("content", "")
            if not filename or not content:
                return jsonify({"error": "filename und content erforderlich"}), 400
            att_dir = os.path.join(CHATS_DIR, "attachments", chat_id)
            os.makedirs(att_dir, exist_ok=True)
            att_path = os.path.join(att_dir, filename)
            with open(att_path, "w", encoding="utf-8") as f:
                f.write(content)
            return jsonify({"ok": True, "path": att_path})

        @self.app.route("/api/jarvis/chats/<chat_id>/attachments/<filename>")
        def get_attachment(chat_id, filename):
            """Datei-Anhang abrufen."""
            att_path = os.path.join(CHATS_DIR, "attachments", chat_id, filename)
            if not os.path.exists(att_path):
                return jsonify({"error": "Datei nicht gefunden"}), 404
            with open(att_path, "r", encoding="utf-8") as f:
                content = f.read()
            return jsonify({"filename": filename, "content": content})

        self.log.info("Jarvis-Modul v2 registriert")

    # ── Hilfsfunktionen ──────────────────────────────────────────────

    def _get_ollama_url(self) -> str:
        return self.config.jarvis_ollama_url.rstrip("/")

    def _get_setting(self, key: str, default=""):
        return self.config._settings.get(key, default)

    def _build_system_prompt(self) -> str:
        custom  = self._get_setting("jarvis_system_prompt", "")
        ki_name = self._get_setting("ki_name", "Assistent")
        states  = self.ha.get_cached_states()
        summary = self._summarize_states(states)
        base = custom or (
            f"Du bist {ki_name}, ein intelligenter Smart Home Assistent für das Zuhause in Ottobrunn. "
            "Du hast direkten Zugriff auf den aktuellen Zustand aller Home Assistant Entitäten. "
            "Regeln: "
            "1. Antworte immer auf Deutsch, präzise und ohne Emojis. "
            "2. Nenne immer konkrete Werte aus dem HA-Status — keine abstrakten Aussagen wie 'alles läuft gut'. "
            "3. Wenn du nach dem Zustand von Geräten gefragt wirst, nenne die genauen Werte (Temperatur, Ein/Aus, Prozentwerte etc.). "
            "4. Rollo-Position: 100% = vollständig geöffnet, 0% = vollständig geschlossen. "
            "5. Erfinde keine Werte — wenn etwas nicht im HA-Status steht, sage es klar. "
            "6. Wenn du Geräte steuern sollst, füge am Ende deiner Antwort exakt diesen JSON-Block ein: "
            '{"action": {"domain": "light", "service": "turn_on", "entity_id": "light.beispiel"}}'
        )
        return f"{base}\n\nAktueller HA-Status:\n{summary}"

    def _build_system_prompt_no_ha(self) -> str:
        custom  = self._get_setting("jarvis_system_prompt", "")
        ki_name = self._get_setting("ki_name", "Assistent")
        return custom or (
            f"Du bist {ki_name}, ein intelligenter Assistent. "
            "Antworte immer auf Deutsch, präzise und hilfreich. Keine Emojis. "
            "Du hast keinen Zugriff auf Smart Home Geräte."
        )

    def _summarize_states(self, states: dict) -> str:
        lines = []
        important = {"light","switch","climate","cover","lock","person","sensor","binary_sensor"}
        for eid, state in list(states.items())[:150]:
            if eid.split(".")[0] not in important: continue
            name = state.get("attributes", {}).get("friendly_name", eid)
            val  = state.get("state", "?")
            unit = state.get("attributes", {}).get("unit_of_measurement", "")
            lines.append(f"- {name} ({eid}): {val}{' ' + unit if unit else ''}")
        return "\n".join(lines)

    def _call_ha_service(self, domain: str, service: str, data: dict) -> bool:
        if not self.config._settings.get("jarvis_ha_control", False):
            return False
        try:
            r = requests.post(
                f"{self.ha.ha_url}/api/services/{domain}/{service}",
                headers={"Authorization": f"Bearer {self.config.ha_long_token}"},
                json=data,
                timeout=10,
            )
            return r.status_code in (200, 201)
        except Exception as e:
            self.log.error(f"HA Service-Call Fehler: {e}")
            return False


def _load_chat(chat_id: str) -> dict | None:
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _save_chat(chat: dict):
    path = os.path.join(CHATS_DIR, f"{chat['id']}.json")
    with open(path, "w") as f:
        json.dump(chat, f, indent=2, ensure_ascii=False)
