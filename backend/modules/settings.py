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
                "jarvis_temperature", "jarvis_max_tokens", "jarvis_system_prompt",
            ]
            updates = {k: v for k, v in data.items() if k in allowed}
            self.config.save_settings(updates)
            return jsonify({"ok": True})

        self.log.info("Settings-Modul registriert")
