"""
Modul: jarvis
KI-Assistent mit Ollama-Anbindung und direktem HA-Zugriff.
"""
import json
import threading
import requests
from flask import jsonify, request, Response, stream_with_context
from modules.base import BaseModule


class Module(BaseModule):
    name    = "jarvis"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/jarvis/models")
        def get_models():
            """Verfügbare Ollama-Modelle abrufen."""
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

        @self.app.route("/api/jarvis/chat", methods=["POST"])
        def chat():
            """Chat mit Ollama — streamt die Antwort."""
            body     = request.get_json() or {}
            messages = body.get("messages", [])
            model    = body.get("model") or self._get_setting("jarvis_model", "")
            ollama_url = self._get_ollama_url()

            if not ollama_url:
                return jsonify({"error": "Ollama URL nicht konfiguriert"}), 400
            if not model:
                return jsonify({"error": "Kein Modell ausgewählt"}), 400

            # HA-Kontext aufbauen
            system_prompt = self._build_system_prompt()

            full_messages = [{"role": "system", "content": system_prompt}] + messages

            def generate():
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
                            yield line.decode() + "\n"
                except Exception as e:
                    yield json.dumps({"error": str(e)}) + "\n"

            return Response(
                stream_with_context(generate()),
                mimetype="application/x-ndjson",
            )

        @self.app.route("/api/jarvis/action", methods=["POST"])
        def action():
            """HA-Aktion ausführen (Service-Call)."""
            body      = request.get_json() or {}
            domain    = body.get("domain")
            service   = body.get("service")
            entity_id = body.get("entity_id")
            data      = body.get("data", {})

            if not domain or not service:
                return jsonify({"error": "domain und service erforderlich"}), 400

            if entity_id:
                data["entity_id"] = entity_id

            result = self._call_ha_service(domain, service, data)
            return jsonify({"ok": result})

        @self.app.route("/api/jarvis/context")
        def get_context():
            """Aktuellen HA-Kontext für Jarvis abrufen."""
            states  = self.ha.get_cached_states()
            context = self._summarize_states(states)
            return jsonify({"context": context, "entity_count": len(states)})

        self.log.info("Jarvis-Modul registriert")

    def _get_ollama_url(self) -> str:
        url = self.config.jarvis_ollama_url.rstrip("/")
        return url or ""

    def _get_setting(self, key: str, default="") -> str:
        return self.config._settings.get(key, default)

    def _build_system_prompt(self) -> str:
        """System-Prompt mit aktuellem HA-Kontext aufbauen."""
        custom = self._get_setting("jarvis_system_prompt", "")
        states = self.ha.get_cached_states()
        summary = self._summarize_states(states)

        ki_name = self.config._settings.get("ki_name", "Jarvis")
        base = custom or (
            f"Du bist {ki_name}, ein intelligenter Smart Home Assistent. "
            "Du hast Zugriff auf alle Home Assistant Entitäten und kannst Geräte steuern. "
            "Antworte immer auf Deutsch, präzise und hilfreich. Keine Emojis. "
            "Rollo-Position: 100% = offen, 0% = geschlossen. "
            "Wenn du Geräte steuern sollst, füge am Ende deiner Antwort einen JSON-Block ein: "
            '{"action": {"domain": "light", "service": "turn_on", "entity_id": "light.wohnzimmer"}}'
        )

        return f"{base}\n\nAktueller HA-Status:\n{summary}"

    def _summarize_states(self, states: dict) -> str:
        """Kompakte Zusammenfassung der wichtigsten Entity-States."""
        lines = []
        important_domains = {"light", "switch", "climate", "cover", "lock",
                             "alarm_control_panel", "person", "sensor", "binary_sensor"}
        for eid, state in list(states.items())[:150]:
            domain = eid.split(".")[0]
            if domain not in important_domains:
                continue
            name  = state.get("attributes", {}).get("friendly_name", eid)
            value = state.get("state", "?")
            unit  = state.get("attributes", {}).get("unit_of_measurement", "")
            lines.append(f"- {name} ({eid}): {value}{' ' + unit if unit else ''}")
        return "\n".join(lines)

    def _call_ha_service(self, domain: str, service: str, data: dict) -> bool:
        """HA Service über REST API aufrufen — nur wenn HA-Steuerung erlaubt."""
        if not self.config._settings.get("jarvis_ha_control", False):
            self.log.info("HA-Steuerung deaktiviert — Service-Call ignoriert")
            return False
        try:
            r = requests.post(
                f"{self.ha.ha_url}/api/services/{domain}/{service}",
                headers={
                    "Authorization": f"Bearer {self.ha.token}",
                    "Content-Type":  "application/json",
                },
                json=data,
                timeout=10,
            )
            return r.status_code in (200, 201)
        except Exception as e:
            self.log.error(f"HA Service-Call Fehler: {e}")
            return False
