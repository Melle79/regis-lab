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
    def _call_ki(self, prompt: str) -> str:
        """KI-Aufruf über konfigurierten Provider."""
        try:
            from modules.jarvis import Module as JarvisModule
            jarvis = next((m for m in getattr(self, '_siblings', []) if isinstance(m, JarvisModule)), None)
            if jarvis:
                return jarvis.call_ki(prompt)
        except Exception:
            pass
        model  = self.config._settings.get("jarvis_model", "")
        ollama = self.config.jarvis_ollama_url.rstrip("/")
        if not model or not ollama:
            return ""
        try:
            r = requests.post(
                ollama + "/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            return r.json().get("response", "").strip() if r.status_code == 200 else ""
        except Exception:
            return ""

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

        @self.app.route("/api/analyse/cleanup")
        def get_cleanup():
            token = self.config.ha_long_token
            ha    = "http://homeassistant.local.hass.io:8123"
            hdrs  = {"Authorization": "Bearer " + token}
            try:
                states_r = requests.get(ha + "/api/states", headers=hdrs, timeout=15)
                states   = states_r.json() if states_r.status_code == 200 else []
                groups   = self._get_cleanup_data(states, token)
                return jsonify({"groups": groups})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/analyse/cleanup/suggest", methods=["POST"])
        def cleanup_suggest():
            data     = request.get_json() or {}
            platform = data.get("platform", "")
            entities = data.get("entities", [])
            model    = self.config._settings.get("jarvis_model", "")
            ollama   = self.config.jarvis_ollama_url.rstrip("/")
            if not model or not ollama:
                return jsonify({"error": "Ollama nicht konfiguriert"}), 400

            entity_list = "\n".join("- " + e['entity_id'] + " (" + e['name'] + ")" for e in entities[:20])
            prompt = (
                "Du bist ein Home Assistant Experte. Diese Geraete der Integration '" + platform + "' sind unavailable:\n\n"
                + entity_list + "\n\n"
                "Analysiere und gib eine kurze Einschaetzung (2-3 Saetze) auf Deutsch:\n"
                "- Was koennte der Grund sein?\n"
                "- Was sollte der Nutzer tun?\n"
                "Sei praegnant und konkret."
                "Sei praegnant und konkret."
            )
            try:
                r = requests.post(ollama + "/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False}, timeout=20)
                text = r.json().get("response", "").strip() if r.status_code == 200 else ""
                return jsonify({"suggestion": text})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        LOG_PATH = "/data/analyse_log.json"

        def _log_action(action_type, entity_id, name, extra=None):
            try:
                log = []
                if os.path.exists(LOG_PATH):
                    with open(LOG_PATH) as f:
                        log = json.load(f)
                log.insert(0, {
                    "id":        str(len(log) + 1) + "_" + datetime.now().strftime("%H%M%S"),
                    "timestamp": datetime.now().isoformat(),
                    "type":      action_type,
                    "entity_id": entity_id,
                    "name":      name,
                    "extra":     extra or {},
                    "undone":    False,
                })
                log = log[:200]
                with open(LOG_PATH, "w") as f:
                    json.dump(log, f)
            except Exception as e:
                self.log.warning("Log-Fehler: " + str(e))

        @self.app.route("/api/analyse/log")
        def get_log():
            try:
                if os.path.exists(LOG_PATH):
                    with open(LOG_PATH) as f:
                        return jsonify({"log": json.load(f)})
            except Exception:
                pass
            return jsonify({"log": []})

        @self.app.route("/api/analyse/log/undo", methods=["POST"])
        def undo_action():
            data   = request.get_json() or {}
            log_id = data.get("id", "")
            token  = self.config.ha_long_token
            ha     = "http://homeassistant.local.hass.io:8123"
            hdrs   = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            try:
                if not os.path.exists(LOG_PATH):
                    return jsonify({"error": "Kein Log"}), 404
                with open(LOG_PATH) as f:
                    log = json.load(f)
                entry = next((e for e in log if e["id"] == log_id), None)
                if not entry:
                    return jsonify({"error": "Eintrag nicht gefunden"}), 404

                action_type = entry["type"]
                entity_id   = entry["entity_id"]

                if action_type == "ignore":
                    # Aus Ignore-Liste entfernen
                    ignore_path = "/data/analyse_ignore.json"
                    if os.path.exists(ignore_path):
                        with open(ignore_path) as f:
                            ignored = json.load(f)
                        ignored = [e for e in ignored if e != entity_id]
                        with open(ignore_path, "w") as f:
                            json.dump(ignored, f)

                elif action_type == "enable_automation":
                    # Automation wieder deaktivieren
                    requests.post(ha + "/api/services/automation/turn_off",
                        headers=hdrs, json={"entity_id": entity_id}, timeout=10)

                elif action_type == "ignore_group":
                    # Alle Entitäten der Gruppe aus Ignore-Liste entfernen
                    entities = entry.get("extra", {}).get("entities", [])
                    ignore_path = "/data/analyse_ignore.json"
                    if os.path.exists(ignore_path):
                        with open(ignore_path) as f:
                            ignored = json.load(f)
                        ignored = [e for e in ignored if e not in entities]
                        with open(ignore_path, "w") as f:
                            json.dump(ignored, f)

                # Als rückgängig markieren
                entry["undone"] = True
                with open(LOG_PATH, "w") as f:
                    json.dump(log, f)

                return jsonify({"ok": True})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/analyse/cleanup/repair", methods=["POST"])
        def repair_integration():
            data      = request.get_json() or {}
            platform  = data.get("platform", "")
            token     = self.config.ha_long_token
            ha        = "http://homeassistant.local.hass.io:8123"
            hdrs      = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            try:
                # Config-Entries für diese Platform laden
                entries_r = requests.get(ha + "/api/config/config_entries/entry", headers=hdrs, timeout=10)
                entries   = entries_r.json() if entries_r.status_code == 200 else []
                reloaded  = 0
                for entry in entries:
                    if entry.get("domain") == platform and entry.get("state") not in ("loaded",):
                        requests.post(
                            ha + "/api/config/config_entries/entry/" + entry["entry_id"] + "/reload",
                            headers=hdrs, timeout=10,
                        )
                        reloaded += 1
                if reloaded == 0:
                    # Alle Entries dieser Platform neu laden
                    for entry in entries:
                        if entry.get("domain") == platform:
                            requests.post(
                                ha + "/api/config/config_entries/entry/" + entry["entry_id"] + "/reload",
                                headers=hdrs, timeout=10,
                            )
                            reloaded += 1
                _log_action("repair", platform, platform, {"reloaded": reloaded})
                return jsonify({"ok": True, "reloaded": reloaded})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/analyse/cleanup/ignore", methods=["POST"])
        def ignore_entities():
            data      = request.get_json() or {}
            entity_ids = data.get("entity_ids", [])
            try:
                ignore_path = "/data/analyse_ignore.json"
                ignored = []
                if os.path.exists(ignore_path):
                    with open(ignore_path) as f:
                        ignored = json.load(f)
                for eid in entity_ids:
                    if eid not in ignored:
                        ignored.append(eid)
                with open(ignore_path, "w") as f:
                    json.dump(ignored, f)
                for eid in entity_ids:
                    _log_action("ignore", eid, eid)
                return jsonify({"ok": True, "ignored": len(ignored)})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/analyse/cleanup/ignored")
        def get_ignored():
            try:
                ignore_path = "/data/analyse_ignore.json"
                if os.path.exists(ignore_path):
                    with open(ignore_path) as f:
                        return jsonify({"ignored": json.load(f)})
            except Exception:
                pass
            return jsonify({"ignored": []})

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
            SKIP_PATTERNS = [
                "_config_", "config_overtemp", "_outlet", "_music_mode",
                "_led_", "_debug", "_test", "testkamera_", "woox_smart_camera_",
                "_privacy", "_flip", "_watermark", "_motion", "_sound",
                "_videoaufnahme", "_gerauscherkennung", "_umdrehen",
                "_zeit_wasserzeichen", "_bewegungsalarm", "_bewegungsverfolgung",
                "_datenschutzmodus",
                "_shuffle", "_repeat", "_do_not_disturb", "_bitte_nicht_st",
                "fritz_box_", "fritz_repeater_", "event_stream", "internetzugang",
                "internet_access", "port_forward", "wi_fi_wlan", "gastzugang",
            ]

            # Entity-Registry laden für device_id → Gerätename
            try:
                reg_r = requests.get(
                    ha + "/api/config/entity_registry/list",
                    headers=hdrs, timeout=10
                )
                entity_reg = {e["entity_id"]: e for e in (reg_r.json() if reg_r.status_code == 200 else [])}
            except Exception:
                entity_reg = {}

            try:
                dev_r = requests.get(
                    ha + "/api/config/device_registry/list",
                    headers=hdrs, timeout=10
                )
                device_reg = {d["id"]: d for d in (dev_r.json() if dev_r.status_code == 200 else [])}
            except Exception:
                device_reg = {}

            # Pro Gerät nur einen Eintrag — Gerät gilt als offline wenn ALLE Entitäten unavailable
            device_entities = {}  # device_id → list of states
            no_device_offline = []  # Entitäten ohne device_id

            for s in states:
                domain = s.get("entity_id", "").split(".")[0]
                if domain not in RELEVANT_DOMAINS:
                    continue
                eid = s.get("entity_id", "")
                if any(p in eid for p in SKIP_PATTERNS):
                    continue
                reg = entity_reg.get(eid, {})
                did = reg.get("device_id")
                if did:
                    device_entities.setdefault(did, []).append(s)
                elif s.get("state") in ("unavailable", "unknown"):
                    no_device_offline.append({
                        "entity_id": eid,
                        "name":      s.get("attributes", {}).get("friendly_name", eid),
                        "state":     s["state"],
                    })

            offline = []
            for did, ents in device_entities.items():
                # Gerät offline wenn mindestens eine steuerbare Entität unavailable ist
                unavail = [e for e in ents if e.get("state") in ("unavailable", "unknown")]
                if not unavail:
                    continue
                dev = device_reg.get(did, {})
                dev_name = dev.get("name_by_user") or dev.get("name") or did
                # Erste unavailable Entität als Referenz
                ref = unavail[0]
                offline.append({
                    "entity_id": ref.get("entity_id", ""),
                    "name":      dev_name,
                    "state":     ref.get("state", "unavailable"),
                })
            offline.extend(no_device_offline)

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
                "offline":               offline,
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
                r2 = requests.post(
                    ha + "/api/services/automation/turn_on",
                    headers=hdrs,
                    json={"entity_id": entity_id},
                    timeout=10,
                )
                name = data.get("name", entity_id)
                _log_action("enable_automation", entity_id, name)
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


    def _get_cleanup_data(self, states, token):
        """Gruppiert problematische Entitäten nach Integration für das Aufräumen."""
        ha    = "http://homeassistant.local.hass.io:8123"
        hdrs  = {"Authorization": "Bearer " + token}

        # Entity-Registry laden für Integration-Info
        try:
            reg_r = requests.get(ha + "/api/config/entity_registry/list", headers=hdrs, timeout=10)
            registry = {e["entity_id"]: e for e in (reg_r.json() if reg_r.status_code == 200 else [])}
        except Exception:
            registry = {}

        # Ignorier-Liste laden
        ignore_path = "/data/analyse_ignore.json"
        ignored_set = set()
        try:
            if os.path.exists(ignore_path):
                with open(ignore_path) as f:
                    ignored_set = set(json.load(f))
        except Exception:
            pass

        # Alle unavailable/unknown Entitäten nach Platform gruppieren
        groups = {}
        for s in states:
            if s.get("state") not in ("unavailable", "unknown"):
                continue
            eid      = s["entity_id"]
            reg_info = registry.get(eid, {})
            platform = reg_info.get("platform", eid.split(".")[0])
            name     = s.get("attributes", {}).get("friendly_name", eid)
            if eid in ignored_set:
                continue
            if platform not in groups:
                groups[platform] = []
            groups[platform].append({"entity_id": eid, "name": name, "state": s["state"]})

        # Sortiert nach Anzahl, top 15 Integrationen
        result = sorted(
            [{"platform": k, "entities": v, "count": len(v)} for k, v in groups.items()],
            key=lambda x: x["count"], reverse=True
        )[:15]
        return result
