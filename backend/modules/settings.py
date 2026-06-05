"""
Modul: settings
Liest und schreibt Addon-Einstellungen direkt in /data/options.json
"""
import json
import os
from flask import jsonify, request
from modules.base import BaseModule

OPTIONS_PATH = "/data/options.json"

DEFAULTS = {
    "title":    "Regis-Lab",
    "theme":    "dark",
    "modules":  ["areas", "automations", "entities"],
    "ha_token": "",
}


class Module(BaseModule):
    name    = "settings"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/settings", methods=["GET"])
        def get_settings():
            try:
                if os.path.exists(OPTIONS_PATH):
                    with open(OPTIONS_PATH) as f:
                        data = json.load(f)
                else:
                    data = {}
                # Defaults auffüllen
                result = {**DEFAULTS, **data}
                # Token maskieren für Frontend
                if result.get("ha_token"):
                    result["ha_token_set"] = True
                    result["ha_token"] = "••••••••••••••••••••"
                else:
                    result["ha_token_set"] = False
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/settings", methods=["POST"])
        def save_settings():
            try:
                new = request.get_json() or {}

                # Bestehende laden
                if os.path.exists(OPTIONS_PATH):
                    with open(OPTIONS_PATH) as f:
                        current = json.load(f)
                else:
                    current = dict(DEFAULTS)

                # Token: nur überschreiben wenn nicht maskiert
                if "ha_token" in new:
                    if new["ha_token"] and "•" not in new["ha_token"]:
                        current["ha_token"] = new["ha_token"]
                    elif not new["ha_token"]:
                        current["ha_token"] = ""
                    # sonst: unveränderter Token bleibt

                # Andere Felder übernehmen
                for key in ["title", "theme"]:
                    if key in new:
                        current[key] = new[key]

                with open(OPTIONS_PATH, "w") as f:
                    json.dump(current, f, indent=2)

                # Config neu laden
                self.config._options = current

                return jsonify({"ok": True})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        self.log.info("Settings-Modul registriert")
