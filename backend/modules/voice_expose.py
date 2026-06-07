"""
Modul: voice_expose
Verwaltet die Sprachassistent-Verfügbarkeit von Entitäten über HA WebSocket.
"""
import json
import threading
import websocket
from flask import jsonify, request
from modules.base import BaseModule


class Module(BaseModule):
    name    = "voice_expose"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/voice/expose")
        def get_exposed():
            """Gibt alle Entitäten mit ihrem Expose-Status zurück."""
            try:
                result = self._ws_call({"type": "config/entity_registry/list"})
                entities = []
                for e in (result or []):
                    options = e.get("options", {})
                    conv    = options.get("conversation", {})
                    exposed = conv.get("should_expose")
                    entities.append({
                        "entity_id":    e["entity_id"],
                        "name":         e.get("name") or e.get("original_name", e["entity_id"]),
                        "exposed":      exposed,
                        "platform":     e.get("platform", ""),
                    })
                return jsonify({"entities": entities})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/voice/expose/<entity_id>", methods=["POST"])
        def set_exposed(entity_id):
            """Setzt den Expose-Status einer Entität."""
            data    = request.get_json() or {}
            exposed = data.get("exposed", True)
            try:
                result = self._ws_call({
                    "type":      "config/entity_registry/update",
                    "entity_id": entity_id,
                    "options":   {"conversation": {"should_expose": exposed}},
                })
                return jsonify({"ok": True, "result": result})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        self.log.info("Voice-Expose-Modul registriert")

    def _ws_call(self, msg: dict) -> any:
        """Synchroner WebSocket-Call an HA."""
        token   = self.config.ha_long_token
        # Direkt HA WebSocket (nicht Supervisor-Proxy)
        ws_url  = "ws://homeassistant.local.hass.io:8123/api/websocket"
        result  = [None]
        error   = [None]
        done    = threading.Event()
        msg_id  = 1

        def on_message(ws, raw):
            nonlocal msg_id
            d = json.loads(raw)
            if d.get("type") == "auth_required":
                ws.send(json.dumps({"type": "auth", "access_token": token}))
            elif d.get("type") == "auth_ok":
                ws.send(json.dumps({**msg, "id": msg_id}))
            elif d.get("type") == "result" and d.get("id") == msg_id:
                if d.get("success"):
                    result[0] = d.get("result")
                else:
                    error[0] = d.get("error", {}).get("message", "Fehler")
                done.set()
                ws.close()

        def on_error(ws, err):
            error[0] = str(err)
            done.set()

        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error)
        t  = threading.Thread(target=ws.run_forever, daemon=True)
        t.start()
        done.wait(timeout=10)

        if error[0]:
            raise Exception(error[0])
        return result[0]
