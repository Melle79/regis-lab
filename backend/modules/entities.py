"""
Modul: entities
Stellt Entity-Zustände von HA bereit und erlaubt Service-Calls.
"""
import json
from flask import jsonify, request
from modules.base import BaseModule


class Module(BaseModule):
    name    = "entities"
    version = "1.0.0"

    def register(self):
        @self.app.route("/api/entities")
        def get_entities():
            """Alle gecachten Entity-Zustände zurückgeben."""
            domain = request.args.get("domain")   # ?domain=light
            states = list(self.ha.get_cached_states().values())
            if domain:
                states = [s for s in states if s["entity_id"].startswith(f"{domain}.")]
            return jsonify(states)

        @self.app.route("/api/entities/<entity_id>")
        def get_entity(entity_id):
            state = self.ha.get_cached_states().get(entity_id)
            if not state:
                return jsonify({"error": "nicht gefunden"}), 404
            return jsonify(state)

        @self.app.route("/api/entities/service", methods=["POST"])
        def call_service():
            """Service-Call an HA: {"domain":"light","service":"turn_on","data":{...}}"""
            body   = request.get_json() or {}
            domain  = body.get("domain")
            service = body.get("service")
            data    = body.get("data", {})
            if not domain or not service:
                return jsonify({"error": "domain und service erforderlich"}), 400
            ok = self.ha.call_service(domain, service, data)
            return jsonify({"ok": ok})

        # Entities initial laden (füllt Cache)
        self.ha.get_states()
        self.log.info("Entities-Modul registriert")

    def handle_ws(self, ws, msg: dict):
        """Frontend kann Entity-Refresh anfragen."""
        if msg.get("action") == "refresh":
            states = list(self.ha.get_cached_states().values())
            ws.send(json.dumps({"type": "state_snapshot", "data": states}))
