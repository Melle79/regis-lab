"""
BaseModule - Basisklasse für alle Dashboard-Module.
Jedes Modul erbt davon und implementiert register() und optional handle_ws().
"""
from flask import Flask
import logging


class BaseModule:
    """
    Basis für alle Dashboard-Module.

    Minimales Beispiel-Modul:

        from modules.base import BaseModule
        from flask import jsonify

        class Module(BaseModule):
            name = "my_module"
            version = "1.0.0"

            def register(self):
                @self.app.route("/api/my_module/data")
                def get_data():
                    return jsonify({"hello": "world"})

            def handle_ws(self, ws, msg):
                ws.send('{"type": "pong"}')
    """
    name    = "base"
    version = "0.0.0"

    def __init__(self, app: Flask, ha_client, config):
        self.app    = app
        self.ha     = ha_client
        self.config = config
        self.log    = logging.getLogger(f"ha_dashboard.module.{self.name}")

    def register(self):
        """Hier Flask-Routen und andere Initialisierungen registrieren."""
        raise NotImplementedError(f"Modul '{self.name}' muss register() implementieren")

    def handle_ws(self, ws, msg: dict):
        """Optional: WebSocket-Nachrichten verarbeiten."""
        pass
