"""
Modul: areas
Liest HA Bereiche, Stockwerke, Geräte und Entities via WebSocket.
Erlaubt auch Geräte-Bereich-Zuweisung via PATCH.
"""
import json
import threading
import websocket as ws_lib
from flask import jsonify, request
from modules.base import BaseModule

DOMAIN_ICONS = {
    "light": "mdi:lightbulb", "switch": "mdi:toggle-switch",
    "sensor": "mdi:gauge", "binary_sensor": "mdi:radiobox-marked",
    "climate": "mdi:thermostat", "cover": "mdi:window-shutter",
    "fan": "mdi:fan", "media_player": "mdi:speaker",
    "input_boolean": "mdi:toggle-switch-outline", "automation": "mdi:robot",
    "script": "mdi:script-text", "person": "mdi:account",
    "device_tracker": "mdi:map-marker", "camera": "mdi:cctv",
    "weather": "mdi:weather-partly-cloudy", "number": "mdi:ray-vertex",
    "input_number": "mdi:ray-vertex", "select": "mdi:format-list-bulleted",
    "input_select": "mdi:format-list-bulleted", "button": "mdi:gesture-tap-button",
    "update": "mdi:package-up", "timer": "mdi:timer-outline",
    "counter": "mdi:counter", "alarm_control_panel": "mdi:shield-home",
    "vacuum": "mdi:robot-vacuum", "lock": "mdi:lock",
}



DEVICE_DOMAINS = {
    'light', 'switch', 'sensor', 'binary_sensor', 'climate', 'cover',
    'fan', 'media_player', 'camera', 'lock', 'alarm_control_panel',
    'vacuum', 'water_heater', 'humidifier', 'valve', 'lawn_mower',
    'remote', 'siren', 'update', 'number', 'select', 'button', 'text',
    'weather', 'air_quality', 'event', 'image',
}

class Module(BaseModule):
    name    = "areas"
    version = "1.1.0"

    def register(self):

        @self.app.route("/api/areas")
        def get_areas():
            data = self._fetch_registry()
            if data is None:
                return jsonify({"error": "Registry nicht erreichbar"}), 503

            floors, areas, devices, entities = data
            floor_map   = {f["floor_id"]: f for f in floors}
            device_map  = {d["id"]: d for d in devices}
            device_area = {d["id"]: d.get("area_id") for d in devices}
            states = self.ha.get_cached_states()

            entity_info = {}
            for e in entities:
                area_id = e.get("area_id") or device_area.get(e.get("device_id"))
                entity_info[e["entity_id"]] = {
                    "area_id":   area_id,
                    "device_id": e.get("device_id"),
                }

            area_map = {}
            for a in areas:
                aid   = a["area_id"]
                floor = floor_map.get(a.get("floor_id") or "", {})
                area_map[aid] = {
                    "area_id":     aid,
                    "name":        a["name"],
                    "floor_id":    a.get("floor_id"),
                    "floor_name":  floor.get("name", ""),
                    "floor_level": floor.get("level") or 0,
                    "icon":        a.get("icon"),
                    "devices":     {},
                    "entities":    [],
                }

            assigned = set()
            for eid, info in entity_info.items():
                if eid not in states:
                    continue
                aid = info["area_id"]
                did = info["device_id"]
                if not aid or aid not in area_map:
                    continue
                # Nur echte Geraete-Domains in Bereiche
                if eid.split(".")[0] not in DEVICE_DOMAINS:
                    continue
                assigned.add(eid)
                entity_state = states[eid]

                if did and did in device_map:
                    dev = device_map[did]
                    if did not in area_map[aid]["devices"]:
                        area_map[aid]["devices"][did] = {
                            "device_id":    did,
                            "name":         dev.get("name_by_user") or dev.get("name") or did,
                            "model":        dev.get("model"),
                            "manufacturer": dev.get("manufacturer"),
                            "icon":         dev.get("icon"),
                            "integration":  dev.get("identifiers", [[None]])[0][0] if dev.get("identifiers") else None,
                            "entities":     [],
                            "_domains":     [],
                        }
                    area_map[aid]["devices"][did]["entities"].append(entity_state)
                    area_map[aid]["devices"][did]["_domains"].append(eid.split(".")[0])
                else:
                    area_map[aid]["entities"].append(entity_state)

            from collections import Counter
            for aid in area_map:
                devices_list = []
                for did, dev in area_map[aid]["devices"].items():
                    if not dev["icon"] and dev["_domains"]:
                        mc = Counter(dev["_domains"]).most_common(1)[0][0]
                        dev["icon"] = DOMAIN_ICONS.get(mc, "mdi:chip")
                    del dev["_domains"]
                    devices_list.append(dev)
                area_map[aid]["devices"] = sorted(devices_list, key=lambda d: d["name"].lower())

            unassigned_by_device = {}
            unassigned_no_device = []
            for eid, state in states.items():
                if eid in assigned:
                    continue
                info = entity_info.get(eid, {})
                did  = info.get("device_id")
                # Nur DEVICE_DOMAINS in nicht-zugeordnet
                if eid.split(".")[0] not in DEVICE_DOMAINS:
                    continue
                # Service-Geräte (Addons, HACS etc.) rausfiltern
                if did and device_map.get(did, {}).get("entry_type") == "service":
                    continue
                # Reine Netzwerk-Tracker ohne Config-Entry
                if did and not device_map.get(did, {}).get("identifiers") and not device_map.get(did, {}).get("primary_config_entry"):
                    continue
                if did and did in device_map:
                    dev = device_map[did]
                    if did not in unassigned_by_device:
                        unassigned_by_device[did] = {
                            "device_id":    did,
                            "name":         dev.get("name_by_user") or dev.get("name") or did,
                            "model":        dev.get("model"),
                            "manufacturer": dev.get("manufacturer"),
                            "icon":         dev.get("icon"),
                            "integration":  dev.get("identifiers", [[None]])[0][0] if dev.get("identifiers") else None,
                            "entities":     [],
                            "_domains":     [],
                        }
                    unassigned_by_device[did]["entities"].append(state)
                    unassigned_by_device[did]["_domains"].append(eid.split(".")[0])
                else:
                    unassigned_no_device.append(state)

            for did, dev in unassigned_by_device.items():
                if not dev["icon"] and dev["_domains"]:
                    from collections import Counter
                    mc = Counter(dev["_domains"]).most_common(1)[0][0]
                    dev["icon"] = DOMAIN_ICONS.get(mc, "mdi:chip")
                del dev["_domains"]

            sorted_areas = sorted(
                area_map.values(),
                key=lambda a: (a["floor_level"] if a["floor_level"] is not None else 0, a["name"])
            )

            return jsonify({
                "floors":              list(floor_map.values()),
                "areas":               sorted_areas,
                "unassigned_devices":  sorted(unassigned_by_device.values(), key=lambda d: d["name"].lower()),
                "unassigned_entities": unassigned_no_device,
            })

        @self.app.route("/api/areas/assign-device", methods=["POST"])
        def assign_device():
            """Weist ein Gerät einem Bereich zu (oder entfernt die Zuweisung)."""
            body      = request.get_json() or {}
            device_id = body.get("device_id")
            area_id   = body.get("area_id")  # None = Zuweisung entfernen

            if not device_id:
                return jsonify({"error": "device_id erforderlich"}), 400

            result = self._update_device_area(device_id, area_id)
            if result:
                return jsonify({"ok": True})
            return jsonify({"error": "Zuweisung fehlgeschlagen"}), 500

        @self.app.route("/api/areas/list")
        def list_areas():
            """Gibt nur Bereiche zurück (für Dropdown)."""
            data = self._fetch_registry()
            if data is None:
                return jsonify([])
            floors, areas, _, _ = data
            floor_map = {f["floor_id"]: f for f in floors}
            result = []
            for a in sorted(areas, key=lambda x: (floor_map.get(x.get("floor_id",""),{}).get("level",0) or 0, x["name"])):
                floor = floor_map.get(a.get("floor_id") or "", {})
                result.append({
                    "area_id":    a["area_id"],
                    "name":       a["name"],
                    "floor_name": floor.get("name", ""),
                    "icon":       a.get("icon"),
                })
            return jsonify(result)

        self.log.info("Areas-Modul registriert")

    def _update_device_area(self, device_id: str, area_id) -> bool:
        """Aktualisiert die Bereich-Zuweisung eines Geräts via HA WebSocket."""
        ws_url = self.ha.ha_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        success = [False]
        done    = threading.Event()

        def on_message(ws, raw):
            msg = json.loads(raw)
            t   = msg.get("type")
            if t == "auth_required":
                ws.send(json.dumps({"type": "auth", "access_token": self.ha.token}))
            elif t == "auth_ok":
                ws.send(json.dumps({
                    "id": 1,
                    "type": "config/device_registry/update",
                    "device_id": device_id,
                    "area_id": area_id,
                }))
            elif t == "result" and msg.get("id") == 1:
                success[0] = msg.get("success", False)
                ws.close()
                done.set()

        def on_error(ws, err):
            self.log.error(f"Device-Update WS Fehler: {err}")
            done.set()

        def on_close(ws, *args): done.set()

        conn = ws_lib.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        threading.Thread(target=conn.run_forever, daemon=True).start()
        done.wait(timeout=10)
        return success[0]

    def _fetch_registry(self):
        ws_url = self.ha.ha_url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        results = {}
        done    = threading.Event()
        REQUESTS = {2: "config/area_registry/list", 3: "config/floor_registry/list",
                    4: "config/device_registry/list", 5: "config/entity_registry/list"}

        def on_message(ws, raw):
            msg = json.loads(raw)
            t   = msg.get("type")
            if t == "auth_required":
                ws.send(json.dumps({"type": "auth", "access_token": self.ha.token}))
            elif t == "auth_ok":
                for mid, rtype in REQUESTS.items():
                    ws.send(json.dumps({"id": mid, "type": rtype}))
            elif t == "result":
                mid = msg.get("id")
                results[mid] = msg.get("result", []) if msg.get("success") else []
                if len(results) == len(REQUESTS):
                    ws.close()
                    done.set()

        def on_error(ws, err):
            self.log.error(f"Registry WS Fehler: {err}")
            done.set()

        def on_close(ws, *args): done.set()

        conn = ws_lib.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
        threading.Thread(target=conn.run_forever, daemon=True).start()
        done.wait(timeout=10)

        if len(results) < len(REQUESTS):
            self.log.error("Registry-Abruf Timeout")
            return None
        return results[3], results[2], results[4], results[5]
