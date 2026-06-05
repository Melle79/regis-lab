"""
Module Loader - Lädt Backend-Module dynamisch aus dem modules/-Verzeichnis.
Jedes Modul registriert eigene Flask-Routen und kann WS-Nachrichten verarbeiten.
"""
import os
import importlib
import logging
from flask import Flask

log = logging.getLogger("ha_dashboard.loader")

MODULES_PACKAGE = "modules"


class ModuleLoader:
    def __init__(self, app: Flask, ha_client, config):
        self.app     = app
        self.ha      = ha_client
        self.config  = config
        self._loaded: dict = {}  # name → Modul-Instanz

    def load_all(self):
        """Lädt alle in config.enabled_modules aufgeführten Module."""
        for name in self.config.enabled_modules:
            self._load_module(name)
        log.info(f"Geladene Module: {list(self._loaded.keys())}")

    def _load_module(self, name: str):
        try:
            mod = importlib.import_module(f"{MODULES_PACKAGE}.{name}")
            instance = mod.Module(self.app, self.ha, self.config)
            instance.register()
            self._loaded[name] = instance
            log.info(f"Modul '{name}' geladen")
        except ModuleNotFoundError:
            log.warning(f"Modul '{name}' nicht gefunden, wird übersprungen")
        except Exception as e:
            log.error(f"Fehler beim Laden von Modul '{name}': {e}")

    def module_info(self) -> list:
        return [
            {"name": name, "status": "active"}
            for name in self._loaded
        ]

    def handle_ws_message(self, ws, msg: dict):
        """Leitet WebSocket-Nachrichten an das richtige Modul weiter."""
        target = msg.get("module")
        if target and target in self._loaded:
            try:
                self._loaded[target].handle_ws(ws, msg)
            except Exception as e:
                log.error(f"WS-Handler Fehler in Modul '{target}': {e}")
