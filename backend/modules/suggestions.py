"""
Modul: suggestions
Analysiert HA-Verlauf und schlägt Automationen vor.
- Läuft im Hintergrund und erkennt Muster
- Täglicher Report mit Vorschlägen
- Push-Benachrichtigung bei neuen Vorschlägen
"""
import json
import os
import threading
import time as _time
import requests
from datetime import datetime, timedelta
from flask import jsonify, request
from modules.base import BaseModule

SUGGESTIONS_PATH = "/data/automation_suggestions.json"
MAX_SUGGESTIONS  = 50


class Module(BaseModule):
    name    = "suggestions"
    version = "1.0.0"

    def _fetch_history(self, entity_id: str, days: int = 7) -> list:
        """HA-Verlauf für eine Entität laden."""
        ha   = "http://homeassistant.local.hass.io:8123"
        hdrs = {"Authorization": "Bearer " + self.config.ha_long_token}
        end   = datetime.now()
        start = end - timedelta(days=days)
        try:
            r = requests.get(
                ha + f"/api/history/period/{start.isoformat()}",
                headers=hdrs,
                params={"filter_entity_id": entity_id, "end_time": end.isoformat()},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                return data[0] if data else []
        except Exception as e:
            self.log.warning(f"History-Fehler für {entity_id}: {e}")
        return []

    def _analyze_patterns(self, states: list) -> dict:
        """Muster in Zustandsänderungen erkennen."""
        patterns = {
            "by_hour":    {},  # {hour: count_on}
            "by_weekday": {},  # {weekday: count_on}
            "avg_on_duration_min": None,
            "total_changes": len(states),
        }
        if len(states) < 5:
            return patterns

        on_times = []
        for s in states:
            if s.get("state") == "on":
                try:
                    ts = datetime.fromisoformat(s["last_changed"].replace("Z", "+00:00"))
                    hour = ts.hour
                    weekday = ts.weekday()
                    patterns["by_hour"][hour] = patterns["by_hour"].get(hour, 0) + 1
                    patterns["by_weekday"][weekday] = patterns["by_weekday"].get(weekday, 0) + 1
                    on_times.append(ts)
                except Exception:
                    pass

        return patterns

    def _find_peak_hour(self, by_hour: dict) -> int | None:
        """Häufigste Einschaltstunde finden."""
        if not by_hour:
            return None
        return max(by_hour, key=by_hour.get)

    def _generate_suggestions(self) -> list:
        """Automationsvorschläge aus HA-Verlauf generieren."""
        ha   = "http://homeassistant.local.hass.io:8123"
        hdrs = {"Authorization": "Bearer " + self.config.ha_long_token}
        model  = self.config._settings.get("jarvis_model", "")
        ollama = self.config.jarvis_ollama_url.rstrip("/")

        # Alle Licht- und Schalter-Entitäten holen
        try:
            states_r = requests.get(ha + "/api/states", headers=hdrs, timeout=15)
            all_states = states_r.json() if states_r.status_code == 200 else []
        except Exception:
            return []

        candidates = [
            s for s in all_states
            if s["entity_id"].startswith(("light.", "switch.", "cover.", "climate."))
            and s["state"] not in ("unavailable", "unknown")
        ][:20]  # Max 20 Entitäten analysieren

        pattern_summary = []
        for entity in candidates:
            eid   = entity["entity_id"]
            name  = entity.get("attributes", {}).get("friendly_name", eid)
            history = self._fetch_history(eid, days=7)
            if len(history) < 5:
                continue
            patterns = self._analyze_patterns(history)
            peak_hour = self._find_peak_hour(patterns["by_hour"])
            if peak_hour is not None and patterns["by_hour"].get(peak_hour, 0) >= 3:
                pattern_summary.append(
                    f"- {name} ({eid}): wird oft um {peak_hour}:00 Uhr eingeschaltet "
                    f"({patterns['by_hour'][peak_hour]}x in 7 Tagen)"
                )

        if not pattern_summary or not model or not ollama:
            return []

        # Vorhandene Automationen mit Details laden
        existing_automations = []
        automation_entities = set()  # Alle Entitäten die bereits in Automationen verwendet werden
        try:
            auto_r = requests.get(ha + "/api/states", headers=hdrs, timeout=15)
            auto_states = auto_r.json() if auto_r.status_code == 200 else []
            for s in auto_states:
                if s["entity_id"].startswith("automation."):
                    name = s.get("attributes", {}).get("friendly_name", s["entity_id"])
                    existing_automations.append(name)
                    # Entitäten aus Automation-Attributen extrahieren
                    attrs = s.get("attributes", {})
                    for key in ["entity_id", "last_triggered"]:
                        if isinstance(attrs.get(key), str):
                            automation_entities.add(attrs[key])
                        elif isinstance(attrs.get(key), list):
                            automation_entities.update(attrs[key])
        except Exception:
            pass

        # Entitäten aus History mit Automation-Entitäten vergleichen
        for item in pattern_summary:
            # Entität ID aus dem Pattern extrahieren
            for eid in list(automation_entities):
                if eid in item:
                    item = item + " ⚠️ (Entität bereits in Automation verwendet)"
                    break

        # KI-Analyse
        auto_list = "\n".join(f"- {a}" for a in existing_automations[:50]) if existing_automations else "Keine"
        prompt = (
            "Du bist ein Home Assistant Experte. Analysiere diese Nutzungsmuster aus den letzten 7 Tagen:\n\n"
            + "\n".join(pattern_summary[:10])
            + "\n\nBereits vorhandene Automationen im System (insg. " + str(len(existing_automations)) + " Stück):\n"
            + auto_list
            + "\n\nWICHTIG: Schlage NUR Automationen vor die wirklich noch NICHT existieren. "
            "Prüfe sorgfältig ob eine ähnliche Automation (z.B. mit Bewegungsmeldern, Zeitplan, "
            "oder für dieselben Geräte) bereits vorhanden ist. "
            "Wenn du unsicher bist ob eine Automation bereits existiert, schlage sie NICHT vor.\n"
            "Schlage maximal 2-3 wirklich neue Automationen vor (auf Deutsch, ohne Emojis).\n"
            "Format: VORSCHLAG: [Kurztitel] | BESCHREIBUNG: [Details inkl. warum diese noch nicht existiert]"
        )

        try:
            r = requests.post(
                ollama + "/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response = r.json().get("response", "").strip() if r.status_code == 200 else ""
        except Exception:
            return []

        # Vorschläge parsen
        suggestions = []
        for line in response.split("\n"):
            if "VORSCHLAG:" in line and "BESCHREIBUNG:" in line:
                try:
                    title = line.split("VORSCHLAG:")[1].split("|")[0].strip()
                    desc  = line.split("BESCHREIBUNG:")[1].strip()
                    # Prüfen ob Entitäten aus dem Vorschlag bereits in Automationen
                    entities_used = []
                    for eid in automation_entities:
                        eid_short = eid.split(".")[-1] if "." in eid else eid
                        if eid_short.lower() in (title + desc).lower():
                            entities_used.append(eid)
                    suggestions.append({
                        "id":                   f"sug_{int(datetime.now().timestamp())}_{len(suggestions)}",
                        "title":                title,
                        "description":          desc,
                        "created_at":           datetime.now().isoformat(),
                        "status":               "new",
                        "patterns":             pattern_summary[:10],
                        "entities_in_automations": entities_used,
                    })
                except Exception:
                    pass

        return suggestions

    def _load_suggestions(self) -> list:
        try:
            if os.path.exists(SUGGESTIONS_PATH):
                with open(SUGGESTIONS_PATH) as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_suggestions(self, suggestions: list):
        try:
            with open(SUGGESTIONS_PATH, "w") as f:
                json.dump(suggestions[:MAX_SUGGESTIONS], f)
        except Exception as e:
            self.log.warning(f"Suggestions speichern fehlgeschlagen: {e}")

    def _send_push(self, title: str, message: str):
        """Push-Benachrichtigung senden."""
        ha   = "http://homeassistant.local.hass.io:8123"
        hdrs = {"Authorization": "Bearer " + self.config.ha_long_token,
                "Content-Type": "application/json"}
        targets = self.config._settings.get("briefing_targets", ["mobile_app_svens_iphone"])
        for target in targets:
            try:
                requests.post(
                    ha + f"/api/services/notify/{target}",
                    headers=hdrs,
                    data=json.dumps({"title": title, "message": message}),
                    timeout=10,
                )
            except Exception:
                pass

    def _generate_automation_json(self, suggestion: dict, model: str, ollama: str):
        """KI generiert eine HA-Automation als JSON."""
        import re
        # Echte Entity-IDs aus HA laden
        ha   = "http://homeassistant.local.hass.io:8123"
        hdrs = {"Authorization": "Bearer " + self.config.ha_long_token}
        entity_list = ""
        try:
            r0 = requests.get(ha + "/api/states", headers=hdrs, timeout=10)
            states = r0.json() if r0.status_code == 200 else []
            relevant = [
                s["entity_id"] + " (" + s.get("attributes", {}).get("friendly_name", "") + ")"
                for s in states
                if s["entity_id"].split(".")[0] in ("light", "switch", "cover", "climate", "input_boolean", "scene")
                and s["state"] not in ("unavailable", "unknown")
            ][:40]
            entity_list = " | ".join(relevant)
        except Exception:
            pass

        example = '{"alias":"Licht aus","description":"Schaltet Licht aus","trigger":[{"platform":"time","at":"22:00:00"}],"condition":[],"action":[{"service":"light.turn_off","target":{"entity_id":"light.wohnzimmer"}}],"mode":"single"}'
        prompt = (
            "Du bist ein Home Assistant Experte. Erstelle eine Automation."
            " Titel: " + suggestion["title"] +
            " Beschreibung: " + suggestion["description"] +
            " Verfuegbare Entitaeten (NUR diese verwenden): " + entity_list +
            " Antworte AUSSCHLIESSLICH mit einem JSON-Objekt ohne Text oder Erklaerung."
            " Beispiel: " + example
        )
        try:
            r = requests.post(
                ollama + "/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response = r.json().get("response", "").strip() if r.status_code == 200 else ""
            self.log.info(f"KI-Antwort (erste 300 Zeichen): {response[:300]}")
            # Bereinigen
            response = re.sub(r"```(?:json)?|```", "", response).strip()
            # Ersten { bis letzten } extrahieren
            start = response.find("{")
            end   = response.rfind("}") + 1
            if start == -1 or end == 0:
                self.log.warning(f"Kein JSON gefunden in: {response[:200]}")
                return None
            json_str = response[start:end]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.log.error(f"JSON-Parse-Fehler: {e} | Text: {json_str[:200] if 'json_str' in dir() else '?'}")
            return None
        except Exception as e:
            self.log.error(f"Automation-Generierung fehlgeschlagen: {e}")
            return None

    def _daily_analysis(self):
        """Tägliche Analyse um 08:00 Uhr."""
        while True:
            now    = datetime.now()
            target = now.replace(hour=8, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            wait = (target - now).total_seconds()
            self.log.info(f"Nächste Automations-Analyse in {wait/3600:.1f}h")
            _time.sleep(wait)
            try:
                self.log.info("Starte tägliche Automations-Analyse...")
                new_suggestions = self._generate_suggestions()
                if new_suggestions:
                    existing = self._load_suggestions()
                    existing = new_suggestions + existing
                    self._save_suggestions(existing)
                    self._send_push(
                        "💡 Neue Automations-Vorschläge",
                        f"Jarvis hat {len(new_suggestions)} neue Automations-Vorschläge basierend auf deinen Nutzungsmustern.",
                    )
                    self.log.info(f"{len(new_suggestions)} neue Vorschläge gespeichert")
            except Exception as e:
                self.log.error(f"Analyse-Fehler: {e}")

    def register(self):

        @self.app.route("/api/suggestions")
        def get_suggestions():
            suggestions = self._load_suggestions()
            return jsonify({"suggestions": suggestions})

        @self.app.route("/api/suggestions/<suggestion_id>", methods=["DELETE"])
        def delete_suggestion(suggestion_id):
            suggestions = self._load_suggestions()
            suggestions = [s for s in suggestions if s["id"] != suggestion_id]
            self._save_suggestions(suggestions)
            return jsonify({"ok": True})

        @self.app.route("/api/suggestions/<suggestion_id>", methods=["PATCH"])
        def update_suggestion(suggestion_id):
            data   = request.get_json() or {}
            suggestions = self._load_suggestions()
            for s in suggestions:
                if s["id"] == suggestion_id:
                    if "status" in data:
                        s["status"] = data["status"]
                    if "title" in data:
                        s["title"] = data["title"]
                    if "description" in data:
                        s["description"] = data["description"]
                    break
            self._save_suggestions(suggestions)
            return jsonify({"ok": True})

        @self.app.route("/api/suggestions/analyze", methods=["POST"])
        def run_suggestions_analysis():
            def _run():
                new = self._generate_suggestions()
                if new:
                    existing = self._load_suggestions()
                    self._save_suggestions(new + existing)
            threading.Thread(target=_run, daemon=True).start()
            return jsonify({"ok": True, "message": "Analyse gestartet..."})

        @self.app.route("/api/suggestions/<suggestion_id>/preview-automation", methods=["POST"])
        def preview_automation(suggestion_id):
            """Automation-Vorschau generieren ohne zu speichern."""
            model  = self.config._settings.get("jarvis_model", "")
            ollama = self.config.jarvis_ollama_url.rstrip("/")
            suggestions = self._load_suggestions()
            s = next((x for x in suggestions if x["id"] == suggestion_id), None)
            if not s:
                return jsonify({"error": "Vorschlag nicht gefunden"}), 404
            if not model or not ollama:
                return jsonify({"error": "Ollama nicht konfiguriert"}), 400

            auto_json = self._generate_automation_json(s, model, ollama)
            if auto_json is None:
                return jsonify({"error": "KI konnte keine valide Automation generieren"}), 400
            return jsonify({"ok": True, "automation": auto_json})

        @self.app.route("/api/suggestions/<suggestion_id>/create-automation", methods=["POST"])
        def create_automation(suggestion_id):
            """Aus einem Vorschlag eine echte HA-Automation erstellen."""
            ha    = "http://homeassistant.local.hass.io:8123"
            hdrs  = {"Authorization": "Bearer " + self.config.ha_long_token,
                     "Content-Type": "application/json"}
            model  = self.config._settings.get("jarvis_model", "")
            ollama = self.config.jarvis_ollama_url.rstrip("/")

            suggestions = self._load_suggestions()
            s = next((x for x in suggestions if x["id"] == suggestion_id), None)
            if not s:
                return jsonify({"error": "Vorschlag nicht gefunden"}), 404

            if not model or not ollama:
                return jsonify({"error": "Ollama nicht konfiguriert"}), 400

            # Automation über Hilfsmethode generieren
            auto_json = self._generate_automation_json(s, model, ollama)
            if auto_json is None:
                return jsonify({"error": "KI konnte keine valide Automation generieren"}), 400

            # Automation in HA speichern
            try:
                import uuid
                auto_id = str(uuid.uuid4()).replace("-", "")[:16]
                r2 = requests.post(
                    ha + f"/api/config/automation/config/{auto_id}",
                    headers=hdrs,
                    data=json.dumps(auto_json),
                    timeout=15,
                )
                if r2.status_code in (200, 201):
                    # Vorschlag als umgesetzt markieren
                    s["status"] = "accepted"
                    s["ha_automation_id"] = auto_id
                    self._save_suggestions(suggestions)
                    # HA Automationen neu laden
                    requests.post(ha + "/api/services/automation/reload", headers=hdrs, timeout=10)
                    return jsonify({"ok": True, "automation_id": auto_id, "automation": auto_json})
                else:
                    return jsonify({"error": f"HA Fehler: {r2.status_code} {r2.text}"}), 500
            except Exception as e:
                return jsonify({"error": f"HA-Fehler: {str(e)}"}), 500

        # Tägliche Analyse im Hintergrund
        threading.Thread(target=self._daily_analysis, daemon=True).start()
        self.log.info("Suggestions-Modul registriert")
