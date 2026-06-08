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
                "jarvis_temperature", "jarvis_max_tokens", "jarvis_system_prompt", "jarvis_ha_control", "tab_order",
            ]
            updates = {k: v for k, v in data.items() if k in allowed}
            # Token nur speichern wenn nicht leer
            if "ha_token" in updates and not updates["ha_token"]:
                del updates["ha_token"]
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
                # Direkt gegen HA (Long-Lived Token funktioniert nur hier)
                r = _req.get(
                    "http://homeassistant.local.hass.io:8123/api/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5,
                )
                return jsonify({"ok": r.status_code == 200})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)})

        @self.app.route("/api/user")
        def get_user():
            """Gibt den aktuell konfigurierten HA-Benutzer zurück."""
            import requests as _req
            token = self.config.ha_long_token
            try:
                r = _req.get(
                    "http://homeassistant.local.hass.io:8123/api/",
                    headers={"Authorization": "Bearer " + token},
                    timeout=5,
                )
                # Token-Info via /auth/token endpoint
                r2 = _req.get(
                    "http://homeassistant.local.hass.io:8123/auth/userinfo",
                    headers={"Authorization": "Bearer " + token},
                    timeout=5,
                )
                if r2.status_code == 200:
                    d = r2.json()
                    return jsonify({"name": d.get("name", ""), "username": d.get("username", "")})
            except Exception:
                pass
            return jsonify({"name": "", "username": ""})

        self.log.info("Settings-Modul registriert")
