"""
Modul: settings
Liest und speichert Dashboard-Einstellungen.
"""
import requests
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
                "jarvis_temperature", "jarvis_max_tokens", "jarvis_system_prompt", "jarvis_ha_control", "tab_order", "filter_labels", "briefing_targets", "briefing_time", "briefing_enabled", "ha_external_url", "jarvis_provider", "anthropic_api_key", "use_anthropic_fallback",
            ]
            updates = {k: v for k, v in data.items() if k in allowed}
            # Token nur speichern wenn nicht leer
            if "ha_token" in updates and not updates["ha_token"]:
                del updates["ha_token"]
            self.config.save_settings(updates)
            # Label-Filter Cache aktualisieren
            if "filter_labels" in updates:
                import threading
                threading.Thread(target=self._reload_label_cache, daemon=True).start()
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
            """Alle Labels aus gecachter Registry."""
            all_labels = list(getattr(self.config, "_all_labels", {}).values())
            filtered   = self.config._settings.get("filter_labels", [])
            return jsonify({"labels": all_labels, "filter_labels": filtered})

        @self.app.route("/api/settings/notify-services")
        def get_notify_services():
            """Alle verfügbaren notify.*-Services aus HA laden."""
            token = self.config.ha_long_token
            ha    = "http://homeassistant.local.hass.io:8123"
            hdrs  = {"Authorization": "Bearer " + token}
            try:
                r = requests.get(ha + "/api/services", headers=hdrs, timeout=10)
                services = r.json() if r.status_code == 200 else []
                notify = []
                for domain in services:
                    if domain.get("domain") == "notify":
                        for svc_name in domain.get("services", {}).keys():
                            if svc_name.startswith("mobile_app_"):
                                notify.append({
                                    "id":   svc_name,
                                    "name": svc_name.replace("mobile_app_", "").replace("_", " ").title()
                                })
                return jsonify({"services": notify})
            except Exception as e:
                return jsonify({"services": [], "error": str(e)})

        self.log.info("Settings-Modul registriert")

    def _reload_label_cache(self):
        """Label-Filter Cache nach Einstellungsänderung neu laden."""
        try:
            # areas Modul finden und _preload_labels aufrufen
            from modules.areas import Module as AreasModule
            for mod in getattr(self, '_siblings', []):
                if isinstance(mod, AreasModule):
                    mod._preload_labels()
                    break
            else:
                # Direkt neu laden
                import websocket as wslib, threading, json as _json
                token  = self.config.ha_long_token
                ws_url = self.ha.ha_url.replace("http://", "ws://") + "/api/websocket"
                results = {}
                done    = threading.Event()
                REQS    = {2: "config/area_registry/list", 3: "config/floor_registry/list",
                           4: "config/device_registry/list", 5: "config/entity_registry/list"}
                def on_msg(ws, raw):
                    msg = _json.loads(raw)
                    t   = msg.get("type")
                    if t == "auth_required":
                        ws.send(_json.dumps({"type": "auth", "access_token": token}))
                    elif t == "auth_ok":
                        for mid, rtype in REQS.items():
                            ws.send(_json.dumps({"id": mid, "type": rtype}))
                    elif t == "result":
                        results[msg["id"]] = msg.get("result", [])
                        if len(results) == len(REQS):
                            ws.close(); done.set()
                conn = wslib.WebSocketApp(ws_url, on_message=on_msg,
                    on_error=lambda ws,e: done.set(), on_close=lambda ws,*a: done.set())
                threading.Thread(target=conn.run_forever, daemon=True).start()
                done.wait(10)
                filter_labels = set(self.config._settings.get("filter_labels", []))
                entities = results.get(5, [])
                filtered = set()
                all_labels = {}
                for e in entities:
                    for lid in e.get("labels", []):
                        all_labels[lid] = {"id": lid, "name": lid, "color": ""}
                    if filter_labels & set(e.get("labels", [])):
                        filtered.add(e["entity_id"])
                self.config._label_filtered_ids = filtered
                self.config._all_labels = all_labels
                self.log.info(f"Label-Cache aktualisiert: {len(filtered)} gefiltert")
        except Exception as e:
            self.log.warning(f"Label-Cache-Reload fehlgeschlagen: {e}")
