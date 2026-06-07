"""
Modul: voice_expose
Verwaltet die Sprachassistent-Verfügbarkeit von Entitäten über HA WebSocket.
"""
import json
import threading
import re
import requests
import websocket
from flask import jsonify, request
from modules.base import BaseModule


class Module(BaseModule):
    name    = "voice_expose"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/voice/expose")
        def get_exposed():
            try:
                result = self._ws_call({"type": "config/entity_registry/list"})
                entities = []
                for e in (result or []):
                    options = e.get("options", {})
                    conv    = options.get("conversation", {})
                    exposed = conv.get("should_expose")
                    entities.append({
                        "entity_id": e["entity_id"],
                        "name":      e.get("name") or e.get("original_name", e["entity_id"]),
                        "exposed":   exposed,
                        "platform":  e.get("platform", ""),
                    })
                return jsonify({"entities": entities})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/voice/expose/<entity_id>", methods=["POST"])
        def set_exposed(entity_id):
            data    = request.get_json() or {}
            exposed = data.get("exposed", True)
            try:
                self._ws_call({
                    "type":         "homeassistant/expose_entity",
                    "assistants":   ["conversation"],
                    "entity_ids":   [entity_id],
                    "should_expose": exposed,
                })
                return jsonify({"ok": True})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/voice/suggest", methods=["POST"])
        def suggest_expose():
            data       = request.get_json() or {}
            model      = data.get("model") or self.config._settings.get("jarvis_model", "")
            ollama_url = self.config.jarvis_ollama_url.rstrip("/")

            if not ollama_url or not model:
                return jsonify({"error": "Ollama nicht konfiguriert"}), 400

            try:
                areas_data = self._get_areas_with_entities()
            except Exception as e:
                return jsonify({"error": str(e)}), 500

            # exposed_entities: aus dem expose endpoint laden
            exposed_entities = set()
            try:
                expose_r = requests.get("http://127.0.0.1:8099/api/voice/expose", timeout=5)
                for e in expose_r.json().get("entities", []):
                    if e.get("exposed"):
                        exposed_entities.add(e["entity_id"])
            except Exception:
                pass

            areas_summary = []
            for area in areas_data:
                entities = [
                    "  - " + e["entity_id"] + " (" + e.get("domain", "") + ": " + e.get("name", e["entity_id"]) + ")"
                    for e in area.get("entities", [])
                ]
                if entities:
                    areas_summary.append("Zimmer: " + area["name"] + "\n" + "\n".join(entities))

            prompt = (
                "Du bist ein Smart Home Experte. Analysiere diese Home Assistant Entitaeten "
                "und waehle die sinnvollsten fuer den Sprachassistenten aus.\n\n"
                "Regeln:\n"
                "- Waehle Entitaeten die man per Sprache steuern moechte (Lichter, Schalter, Rollos, Heizung)\n"
                "- Keine Diagnose-Sensoren (Spannung, RSSI etc.)\n"
                "- Keine internen HA-Entitaeten\n"
                "- Max 3-5 Entitaeten pro Zimmer\n\n"
                "Antworte NUR mit einem JSON-Array ohne Erklaerung:\n"
                '[{"area": "Wohnzimmer", "entity_id": "light.wohnzimmer", "name": "Licht", "reason": "Hauptlicht"}]\n\n'
                "Entitaeten:\n" + "\n\n".join(areas_summary[:20])
            )

            try:
                r = requests.post(
                    ollama_url + "/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                    timeout=60,
                )
                if r.status_code != 200:
                    return jsonify({"error": "Ollama Fehler"}), 500

                response_text = r.json().get("response", "")
                match = re.search(r'\[[\s\S]*\]', response_text)
                if not match:
                    return jsonify({"error": "Kein gueltiges JSON", "raw": response_text[:200]}), 500

                import json as _json
                suggestions = _json.loads(match.group())
                for s in suggestions:
                    s["already_exposed"] = s.get("entity_id", "") in exposed_entities

                return jsonify({"suggestions": suggestions})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        self.log.info("Voice-Expose-Modul registriert")

    def _get_areas_with_entities(self) -> list:
        areas_api = requests.get("http://127.0.0.1:8099/api/areas", timeout=10)
        data = areas_api.json()
        result = []
        for area in data.get("areas", []):
            entities = []
            for device in area.get("devices", []):
                for e in device.get("entities", []):
                    entities.append({
                        "entity_id": e["entity_id"],
                        "name":      e.get("friendly_name", e["entity_id"]),
                        "domain":    e["entity_id"].split(".")[0],
                    })
            if entities:
                result.append({"name": area["name"], "entities": entities})
        return result

    def _ws_call(self, msg: dict) -> any:
        token   = self.config.ha_long_token
        ws_url  = "ws://homeassistant.local.hass.io:8123/api/websocket"
        result  = [None]
        error   = [None]
        done    = threading.Event()
        msg_id  = 1

        def on_message(ws, raw):
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
