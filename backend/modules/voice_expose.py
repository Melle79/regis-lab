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
            area_name  = data.get("area_name", "Unbekannt")
            entities   = data.get("entities", [])
            ollama_url = self.config.jarvis_ollama_url.rstrip("/")

            if not ollama_url or not model:
                return jsonify({"error": "Ollama nicht konfiguriert"}), 400

            if not entities:
                return jsonify({"suggestions": []})

            entity_list = ""
            for e in entities:
                entity_list += "- " + e.get("entity_id", "") + " (" + e.get("domain", "") + "): " + e.get("name", "") + "\n"

            prompt = (
                "Welche dieser Home Assistant Entitaeten im Zimmer '" + area_name + "' "
                "sollten per Sprachassistent steuerbar sein?\n\n"
                "Entitaeten:\n" + entity_list + "\n"
                "Regeln:\n"
                "- Nur steuerbare Geraete: Licht, Schalter, Rollo, Heizung, Schloss\n"
                "- Keine Sensoren oder Diagnose-Entitaeten\n"
                "- Max 5 Entitaeten\n\n"
                "Antworte AUSSCHLIESSLICH mit JSON-Array, kein Text:\n"
                '[{"entity_id": "light.beispiel", "name": "Licht", "reason": "Hauptlicht"}]'
            )

            try:
                r = requests.post(
                    ollama_url + "/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                    timeout=30,
                )
                if r.status_code != 200:
                    return jsonify({"error": "Ollama Fehler " + str(r.status_code)}), 500

                response_text = r.json().get("response", "").strip()
                self.log.info("KI Antwort fuer " + area_name + ": " + response_text[:150])

                match = re.search(r"\[[\s\S]*?\]", response_text)
                if not match:
                    return jsonify({"suggestions": [], "raw": response_text[:200]})

                import json as _json
                suggestions = _json.loads(match.group())
                for s in suggestions:
                    s["area"] = area_name
                    s["already_exposed"] = False

                return jsonify({"suggestions": suggestions})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        self.log.info("Voice-Expose-Modul registriert")

    def _get_areas_with_entities(self) -> list:
        # Direkt HA API nutzen statt eigener API (vermeidet Deadlock)
        token = self.config.ha_long_token
        ha = "http://homeassistant.local.hass.io:8123"
        headers = {"Authorization": "Bearer " + token}

        areas_r   = requests.get(ha + "/api/config/area_registry/list", headers=headers, timeout=10)
        devices_r = requests.get(ha + "/api/config/device_registry/list", headers=headers, timeout=10)
        entity_r  = requests.get(ha + "/api/config/entity_registry/list", headers=headers, timeout=10)
        states_r  = requests.get(ha + "/api/states", headers=headers, timeout=10)

        # Fallback: einfach alle States nach domain gruppieren
        states = states_r.json() if states_r.status_code == 200 else []
        result = [{"name": "Alle Geraete", "entities": [
            {"entity_id": s["entity_id"],
             "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
             "domain": s["entity_id"].split(".")[0]}
            for s in states
            if s["entity_id"].split(".")[0] in
               ["light", "switch", "cover", "climate", "lock", "fan", "media_player", "vacuum"]
        ][:40]}]
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
