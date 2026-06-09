"""
Config Manager - Liest HA Addon options.json und /data/regis_settings.json
"""
import os
import json
import logging

log = logging.getLogger("regis_lab.config")

OPTIONS_PATH  = "/data/options.json"
SETTINGS_PATH = "/data/regis_settings.json"

SETTINGS_DEFAULTS = {
    "title":                "Regis-Lab",
    "theme":                "dark",
    "show_clock":           True,
    "show_weather":         False,
    "weather_entity":       "",
    "ki_name":              "Jarvis",
    "jarvis_model":         "",
    "jarvis_temperature":   0.7,
    "jarvis_max_tokens":    2048,
    "jarvis_ollama_url":    "",
    "jarvis_system_prompt": "",
    "jarvis_ha_control":   False,
    "tab_order":           ["home", "geraete", "personen", "zonen", "jarvis", "analyse"],
    "filter_labels":       [],
    "briefing_targets":    ["mobile_app_svens_iphone"],
    "briefing_enabled":    True,
    "ha_external_url":     "",
    "briefing_time":       "07:00",
}


class AddonConfig:
    def __init__(self):
        self._options  = self._load_options()
        self._settings = self._load_settings()
        self.ha_token  = os.environ.get("SUPERVISOR_TOKEN", "")
        self.ha_url    = "http://supervisor/core"
        self._version  = self._fetch_version()
        log.info(f"Config geladen, Version: {self._version}")

    def _load_options(self) -> dict:
        if os.path.exists(OPTIONS_PATH):
            with open(OPTIONS_PATH) as f:
                return json.load(f)
        return {}

    def _load_settings(self) -> dict:
        s = dict(SETTINGS_DEFAULTS)
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH) as f:
                    s.update(json.load(f))
            except Exception as e:
                log.warning(f"Settings laden fehlgeschlagen: {e}")
        return s

    def save_settings(self, updates: dict):
        for k, v in updates.items():
            if k in SETTINGS_DEFAULTS or k == "ha_token":
                self._settings[k] = v
        # ha_token auch in options.json schreiben
        if "ha_token" in updates:
            self._options["ha_token"] = updates["ha_token"]
            try:
                with open(OPTIONS_PATH, "w") as f:
                    json.dump(self._options, f, indent=2)
            except Exception as e:
                log.warning(f"options.json schreiben fehlgeschlagen: {e}")
        # jarvis_ollama_url in options.json
        if "jarvis_ollama_url" in updates:
            self._options["jarvis_ollama_url"] = updates["jarvis_ollama_url"]
            try:
                with open(OPTIONS_PATH, "w") as f:
                    json.dump(self._options, f, indent=2)
            except Exception as e:
                log.warning(f"options.json schreiben fehlgeschlagen: {e}")
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            log.error(f"Settings speichern fehlgeschlagen: {e}")

    def _fetch_version(self) -> str:
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
    def ha_long_token(self) -> str:
        return self._options.get("ha_token", "") or self._settings.get("ha_token", "")

    @property
    def jarvis_ollama_url(self) -> str:
        return self._settings.get("jarvis_ollama_url", "") or self._options.get("jarvis_ollama_url", "")

    @property
    def enabled_modules(self) -> list:
        return ["areas", "automations", "entities", "jarvis", "settings", "voice_expose", "analyse", "briefing"]

    def frontend_config(self) -> dict:
        return {
            "version":              self._version,
            "title":                self._settings.get("title", "Regis-Lab"),
            "theme":                self._settings.get("theme", "dark"),
            "show_clock":           self._settings.get("show_clock", True),
            "show_weather":         self._settings.get("show_weather", False),
            "weather_entity":       self._settings.get("weather_entity", ""),
            "ki_name":              self._settings.get("ki_name", "Jarvis"),
            "jarvis_ollama_url":    self.jarvis_ollama_url,
            "jarvis_ollama_url":    self.jarvis_ollama_url,
            "jarvis_model":         self._settings.get("jarvis_model", ""),
            "jarvis_temperature":   self._settings.get("jarvis_temperature", 0.7),
            "jarvis_max_tokens":    self._settings.get("jarvis_max_tokens", 2048),
            "jarvis_system_prompt": self._settings.get("jarvis_system_prompt", ""),
            "jarvis_ha_control":    self._settings.get("jarvis_ha_control", False),
            "tab_order":            self._settings.get("tab_order", ["geraete", "personen", "zonen", "jarvis"]),
            "filter_labels":        self._settings.get("filter_labels", []),
            "briefing_targets":     self._settings.get("briefing_targets", ["mobile_app_svens_iphone"]),
            "briefing_enabled":     self._settings.get("briefing_enabled", True),
            "ha_external_url":      self._settings.get("ha_external_url", ""),
            "briefing_time":        self._settings.get("briefing_time", "07:00"),
            "ha_token_set":         bool(self.ha_long_token),
        }
