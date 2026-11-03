"""
Modul: mini_tools
Zugriff auf den Mac mini (Dateien lesen/schreiben, Befehle) fuer Jarvis und die
Oberflaeche. Die Verbindung laeuft per SSH; der Schluessel liegt in /data.
"""
from flask import jsonify, request
from modules.base import BaseModule
import modules.mini as mini


def cfg_of(config) -> dict:
    """Einstellungen des mini-Zugriffs (auch von anderen Modulen nutzbar)."""
    s = config._settings
    return {
        "mini_enabled":    s.get("mini_enabled", True),
        "mini_host":       s.get("mini_host", ""),
        "mini_user":       s.get("mini_user", "sven"),
        "mini_root":       s.get("mini_root", ""),
        "mini_key_path":   s.get("mini_key_path", ""),
        "mini_auto":       s.get("mini_auto", True),
        "mini_max_rounds": s.get("mini_max_rounds", 3),
    }


class Module(BaseModule):
    name    = "mini_tools"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/mini/info")
        def mini_info():
            cfg = cfg_of(self.config)
            return jsonify({
                "enabled":    cfg["mini_enabled"],
                "host":       cfg["mini_host"],
                "user":       cfg["mini_user"],
                "root":       mini.root_of(cfg),
                "auto":       cfg["mini_auto"],
                "max_rounds": cfg["mini_max_rounds"],
                "pubkey":     mini.pubkey_text(cfg.get("mini_key_path")),
            })

        @self.app.route("/api/mini/test", methods=["POST"])
        def mini_test():
            """Verbindung pruefen (liefert Hostname des mini)."""
            return jsonify(mini.status(cfg_of(self.config)))

        @self.app.route("/api/mini/run", methods=["POST"])
        def mini_run():
            """Werkzeug manuell ausfuehren: {action, path, cmd, content, cwd}."""
            cfg = cfg_of(self.config)
            if not cfg["mini_enabled"]:
                return jsonify({"error": "mini-Zugriff ist ausgeschaltet"}), 400
            return jsonify(mini.run_tool(cfg, request.get_json() or {}))

        self.log.info("mini_tools-Modul registriert")
