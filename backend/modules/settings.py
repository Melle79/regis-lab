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
                "jarvis_temperature", "jarvis_max_tokens", "jarvis_system_prompt", "jarvis_ha_control", "tab_order", "filter_labels",
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

        @self.app.route("/api/settings/labels")
        def get_labels():
            """Alle Labels aus gecachter Entity-Registry laden."""
            import threading
            import websocket as wslib
            token  = self.config.ha_long_token
            ws_url = self.ha.ha_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
            results = {}
            done    = threading.Event()

            def on_message(ws, raw):
                msg = json.loads(raw)
                t   = msg.get("type")
                if t == "auth_required":
                    ws.send(json.dumps({"type": "auth", "access_token": token}))
                elif t == "auth_ok":
                    ws.send(json.dumps({"id": 2, "type": "config/area_registry/list"}))
                    ws.send(json.dumps({"id": 3, "type": "config/floor_registry/list"}))
                    ws.send(json.dumps({"id": 4, "type": "config/device_registry/list"}))
                    ws.send(json.dumps({"id": 5, "type": "config/entity_registry/list"}))
                elif t == "result":
                    mid = msg.get("id")
                    results[mid] = msg.get("result", []) if msg.get("success") else []
                    if len(results) == 4:
                        ws.close()
                        done.set()

            conn = wslib.WebSocketApp(ws_url, on_message=on_message,
                                      on_error=lambda ws, e: done.set(),
                                      on_close=lambda ws, *a: done.set())
            threading.Thread(target=conn.run_forever, daemon=True).start()
            done.wait(timeout=10)

            # Labels aus Entity-Registry extrahieren
            entities = results.get(5, [])
            label_set = {}
            for e in entities:
                for lid in e.get("labels", []):
                    if lid not in label_set:
                        label_set[lid] = {"id": lid, "name": lid, "color": ""}

            filtered = self.config._settings.get("filter_labels", [])
            return jsonify({"labels": list(label_set.values()), "filter_labels": filtered})

        self.log.info("Settings-Modul registriert")
