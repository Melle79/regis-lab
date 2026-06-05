"""
Config Manager - Liest HA Addon options.json und Umgebungsvariablen
"""
import os
import json
import logging

log = logging.getLogger("regis_lab.config")

OPTIONS_PATH = "/data/options.json"


class AddonConfig:
    def __init__(self):
        self._options = self._load_options()
        self.ha_token = os.environ.get("SUPERVISOR_TOKEN", "")
        self.ha_url   = "http://supervisor/core"
        self._version = self._fetch_version()
        log.info(f"Config geladen: {list(self._options.keys())}, Version: {self._version}")

    def _load_options(self) -> dict:
        if os.path.exists(OPTIONS_PATH):
            with open(OPTIONS_PATH) as f:
                return json.load(f)
        log.warning(f"{OPTIONS_PATH} nicht gefunden, nutze Defaults")
        return {
            "title":   "Regis-Lab",
            "theme":   "dark",
            "modules": ["areas", "automations", "entities"],
        }

    def _fetch_version(self) -> str:
        """Version über Supervisor-API abrufen — immer aktuell."""
        try:
            import requests
            r = requests.get(
                "http://supervisor/addons/self/info",
                headers={"Authorization": f"Bearer {self.ha_token}"},
                timeout=5,
            )
            if r.status_code == 200:
                return r.json().get("data", {}).get("version", "?")
        except Exception:
            pass
        # Fallback: config.yaml im Image
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../config.yaml")
            with open(config_path) as f:
                for line in f:
                    if line.startswith("version:"):
                        return line.split(":")[1].strip().strip('"')
        except Exception:
            pass
        return "?"

    @property
    def version(self) -> str:
        return self._version

    @property
    def title(self) -> str:
        return self._options.get("title", "Regis-Lab")

    @property
    def theme(self) -> str:
        return self._options.get("theme", "dark")

    @property
    def enabled_modules(self) -> list:
        return self._options.get("modules", ["areas", "entities"])

    @property
    def ha_long_token(self) -> str:
        """Long-Lived Access Token für erweiterte HA API Zugriffe."""
        return self._options.get("ha_token", "")

    def frontend_config(self) -> dict:
        return {
            "title":   self.title,
            "theme":   self.theme,
            "modules": self.enabled_modules,
        }
