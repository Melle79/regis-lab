"""
Modul: analyse
KI-gestützte Smart Home Analyse: Statusbericht + Diagnose
"""
import json
import os
import re
import threading
import requests
from datetime import datetime
from flask import jsonify, request
from modules.base import BaseModule

REPORT_PATH   = "/data/analyse_reports.json"
MAX_REPORTS   = 96   # 96 x 15 Min = 24 Stunden


class Module(BaseModule):
    name    = "analyse"
    version = "1.0.0"

    def register(self):

        # Gespeicherte Berichte laden
        @self.app.route("/api/analyse/reports")
        def get_reports():
            reports = self._load_reports()
            return jsonify({"reports": reports})

        @self.app.route("/api/analyse/latest")
        def get_latest():
            reports = self._load_reports()
            return jsonify(reports[0] if reports else {})

        @self.app.route("/api/analyse/run", methods=["POST"])
        def run_analysis():
            token  = self.config.ha_long_token
            ha     = "http://homeassistant.local.hass.io:8123"
            hdrs   = {"Authorization": "Bearer " + token}

            try:
                states_r = requests.get(ha + "/api/states", headers=hdrs, timeout=15)
                states   = states_r.json() if states_r.status_code == 200 else []
            except Exception as e:
                return jsonify({"error": "HA nicht erreichbar: " + str(e)}), 500

            # Offline / Unavailable — nur steuerbare physische Geräte
            RELEVANT_DOMAINS = {
                "light", "switch", "cover", "climate", "lock", "fan",
                "vacuum", "alarm_control_panel",
            }
            # Interne/Konfigurations-Entitäten überspringen
            SKIP_PATTERNS = [
                "_config_", "config_overtemp", "_outlet", "_music_mode",
                "_led_", "_debug", "_test", "testkamera_", "woox_smart_camera_",
                "_privacy", "_flip", "_watermark", "_motion", "_sound",
                "_videoaufnahme", "_gerauscherkennung", "_umdrehen",
                "_zeit_wasserzeichen", "_bewegungsalarm", "_bewegungsverfolgung",
                "_datenschutzmodus",
            ]
            offline = []
            for s in states:
                domain = s.get("entity_id", "").split(".")[0]
                if domain not in RELEVANT_DOMAINS:
                    continue
                eid = s.get("entity_id", "")
                if any(p in eid for p in SKIP_PATTERNS):
                    continue
                if s.get("state") in ("unavailable", "unknown"):
                    offline.append({
                        "entity_id": eid,
                        "name":      s.get("attributes", {}).get("friendly_name", eid),
                        "state":     s["state"],
                    })

            # Niedriger Akku (< 20%)
            low_battery = []
            for s in states:
                eid = s.get("entity_id", "")
                if "battery" in eid and s.get("state", "").isdigit():
                    if int(s["state"]) < 20:
                        low_battery.append({
                            "entity_id": eid,
                            "name": s.get("attributes", {}).get("friendly_name", eid),
                            "state": s["state"],
                        })

            # Deaktivierte Automationen
            disabled_automations = []
            for s in states:
                if s.get("entity_id", "").startswith("automation.") and s.get("state") == "off":
                    disabled_automations.append({
                        "entity_id": s["entity_id"],
                        "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
                    })

            # Log-Fehler
            errors = []
            try:
                log_r = requests.get(ha + "/api/error_log", headers=hdrs, timeout=10)
                if log_r.status_code == 200:
                    lines = log_r.text.strip().split("\n")
                    for line in lines:
                        if "ERROR" in line or "CRITICAL" in line:
                            errors.append(line.strip()[:200])
                    errors = errors[-10:]  # Nur letzte 10 Fehler
            except Exception:
                pass

            # KI-Zusammenfassung
            summary = self._ki_summary(offline, low_battery, disabled_automations, errors)

            report = {
                "timestamp":             datetime.now().isoformat(),
                "offline":               offline[:20],
                "low_battery":           low_battery[:10],
                "disabled_automations":  disabled_automations[:20],
                "errors":                errors,
                "summary":               summary,
                "counts": {
                    "offline":  len(offline),
                    "battery":  len(low_battery),
                    "disabled": len(disabled_automations),
                    "errors":   len(errors),
                }
            }
            self._save_report(report)
            return jsonify(report)

        @self.app.route("/api/analyse/enable_automation", methods=["POST"])
        def enable_automation():
            data      = request.get_json() or {}
            entity_id = data.get("entity_id", "")
            token     = self.config.ha_long_token
            ha        = "http://homeassistant.local.hass.io:8123"
            hdrs      = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            try:
                requests.post(
                    ha + "/api/services/automation/turn_on",
                    headers=hdrs,
                    json={"entity_id": entity_id},
                    timeout=10,
                )
                return jsonify({"ok": True})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # Automatische Analyse alle 15 Minuten
        def auto_analyse():
            import time
            while True:
                time.sleep(15 * 60)
                try:
                    with self.app.test_request_context():
                        run_analysis()
                except Exception as e:
                    self.log.warning("Auto-Analyse Fehler: " + str(e))

        t = threading.Thread(target=auto_analyse, daemon=True)
        t.start()

        self.log.info("Analyse-Modul registriert (Auto-Analyse alle 15 Min)")

    def _load_reports(self) -> list:
        try:
            if os.path.exists(REPORT_PATH):
                with open(REPORT_PATH) as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_report(self, report: dict):
        try:
            reports = self._load_reports()
            reports.insert(0, report)
            reports = reports[:MAX_REPORTS]
            with open(REPORT_PATH, "w") as f:
                json.dump(reports, f)
        except Exception as e:
            self.log.warning("Report speichern fehlgeschlagen: " + str(e))

    def _ki_summary(self, offline, low_battery, disabled, errors):
        ollama_url = self.config.jarvis_ollama_url.rstrip("/")
        model      = self.config._settings.get("jarvis_model", "")
        if not ollama_url or not model:
            return None

        total = len(offline) + len(low_battery) + len(errors)
        prompt = (
            "Du bist ein Smart Home Experte. Analysiere diesen Status-Bericht und gib eine kurze deutschsprachige Einschaetzung (3-5 Saetze).\n\n"
            "Offline/Unavailable: " + str(len(offline)) + " Geraete\n"
        )
        if offline[:3]:
            prompt += "Beispiele: " + ", ".join(e["name"] for e in offline[:3]) + "\n"
        prompt += "Niedriger Akku: " + str(len(low_battery)) + " Geraete\n"
        prompt += "Deaktivierte Automationen: " + str(len(disabled)) + "\n"
        prompt += "Log-Fehler: " + str(len(errors)) + "\n"
        if errors:
            prompt += "Letzter Fehler: " + errors[-1][:150] + "\n"
        prompt += "\nGib eine praegnante Einschaetzung des Smart Home Zustands und die wichtigsten Handlungsempfehlungen."

        try:
            r = requests.post(
                ollama_url + "/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=30,
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
        except Exception:
            pass
        return None
