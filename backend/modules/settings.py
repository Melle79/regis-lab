"""
Modul: settings
Liest und speichert Dashboard-Einstellungen.
"""
from flask import jsonify, request
from modules.base import BaseModule


class Module(BaseModule):
    name    = "settings"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/settings")
        def get_settings():
            return jsonify(self.config.frontend_config())

        @self.app.route("/api/settings", methods=["POST"])
        def save_settings():
            data = request.get_json() or {}
            allowed = [
                "title", "theme", "show_clock", "show_weather", "weather_entity",
                "ki_name", "ha_token", "jarvis_ollama_url", "jarvis_model",
                "jarvis_temperature", "jarvis_max_tokens", "jarvis_system_prompt", "jarvis_ha_control",
            ]
            updates = {k: v for k, v in data.items() if k in allowed}
            self.config.save_settings(updates)
            return jsonify({"ok": True})

        @self.app.route("/api/validate-token", methods=["POST"])
        def validate_token():
            """HA Long-Lived Token validieren."""
            data  = request.get_json() or {}
            token = data.get("token", "")
            if not token:
                return jsonify({"ok": False, "error": "Kein Token"})
            try:
                import requests as _req
                # Über Supervisor-Proxy gegen HA Core API
                r = _req.get(
                    "http://supervisor/core/api/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5,
                )
                if r.status_code == 200:
                    return jsonify({"ok": True})
                # Fallback: direkt gegen HA
                r2 = _req.get(
                    "http://homeassistant:8123/api/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5,
                )
                return jsonify({"ok": r2.status_code == 200})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)})

        self.log.info("Settings-Modul registriert")
