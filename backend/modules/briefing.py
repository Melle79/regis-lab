"""
Modul: briefing
Generiert eine tägliche Morgen-Zusammenfassung via Ollama und sendet sie per Push.
"""
import json
import os
import requests
import threading
import time as _time
from datetime import datetime, timedelta
from flask import jsonify
from modules.base import BaseModule

DAYS_DE   = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
MONTHS_DE = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
WEATHER_DE = {
    "sunny": "Sonnig", "clear-night": "Klare Nacht", "cloudy": "Bewölkt",
    "partlycloudy": "Teils bewölkt", "rainy": "Regen", "snowy": "Schnee",
    "windy": "Windig", "fog": "Nebel", "lightning": "Gewitter", "pouring": "Starkregen",
    "exceptional": "Außergewöhnlich",
}


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
        # Fallback auf Ollama direkt
        model  = self.config._settings.get("jarvis_model", "")
        ollama = self.config.jarvis_ollama_url.rstrip("/")
        if not model or not ollama:
            return ""
        try:
            import requests
            r = requests.post(
                ollama + "/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            return r.json().get("response", "").strip() if r.status_code == 200 else ""
        except Exception:
            return ""

    name    = "briefing"
    version = "1.0.0"

    def _build_briefing(self) -> dict:
        """Daten sammeln und KI-Zusammenfassung erstellen."""
        ha   = "http://homeassistant.local.hass.io:8123"
        hdrs = {"Authorization": "Bearer " + self.config.ha_long_token,
                "Content-Type": "application/json"}

        try:
            states = requests.get(ha + "/api/states", headers=hdrs, timeout=15).json()
        except Exception:
            states = []

        # Personen zuhause
        persons_home = [
            s.get("attributes", {}).get("friendly_name", s["entity_id"])
            for s in states
            if s["entity_id"].startswith("person.") and s["state"] == "home"
        ]

        # Wetter
        weather_entity = self.config._settings.get("weather_entity", "")
        weather = next((s for s in states if s["entity_id"] == weather_entity), None)
        weather_text = ""
        if weather:
            temp = weather.get("attributes", {}).get("temperature", "?")
            weather_text = f"{WEATHER_DE.get(weather.get('state',''), weather.get('state',''))}, {temp}°C"

        # Offline-Geräte
        offline_count = 0
        try:
            if os.path.exists("/data/analyse_reports.json"):
                reports = json.load(open("/data/analyse_reports.json"))
                if reports:
                    offline_count = reports[0].get("counts", {}).get("offline", 0)
        except Exception:
            pass

        # Lichter an (ohne Segmente)
        seen, lights_on = set(), []
        for s in states:
            if not s["entity_id"].startswith("light.") or s["state"] != "on":
                continue
            name = s.get("attributes", {}).get("friendly_name", s["entity_id"])
            base = name.split(" Segment ")[0]
            if base not in seen:
                seen.add(base)
                lights_on.append(base)

        now = datetime.now()
        date_str = f"{DAYS_DE[now.weekday()]}, {now.day}. {MONTHS_DE[now.month-1]} {now.year}"

        context = f"Datum: {date_str}\n"
        if weather_text:   context += f"Wetter: {weather_text}\n"
        if persons_home:   context += f"Zuhause: {', '.join(persons_home)}\n"
        else:              context += "Niemand zuhause\n"
        if offline_count:  context += f"Offline-Geräte: {offline_count}\n"
        if lights_on:      context += f"Lichter noch an: {', '.join(lights_on[:5])}\n"

        # KI-Zusammenfassung über konfigurierten Provider
        summary = context
        prompt = (
            "Du bist ein Smart Home Assistent. Erstelle eine kurze freundliche Morgen-Zusammenfassung "
            "(2-3 Sätze) auf Deutsch ohne Emojis:\n\n" + context
        )
        result = self._call_ki(prompt)
        if result:
            summary = result

        return {
            "date": date_str, "weather": weather_text,
            "persons_home": persons_home, "offline_count": offline_count,
            "lights_on": lights_on, "summary": summary, "context": context,
        }

    def _send_push(self, data: dict):
        """Push-Nachricht an Svens iPhone senden."""
        ha   = "http://homeassistant.local.hass.io:8123"
        hdrs = {"Authorization": "Bearer " + self.config.ha_long_token,
                "Content-Type": "application/json"}

        # Kurze Infos für Subtitle
        infos = []
        if data["weather"]:       infos.append(data["weather"])
        if data["offline_count"]: infos.append(f"⚠️ {data['offline_count']} offline")
        if data["lights_on"]:     infos.append(f"💡 {len(data['lights_on'])} Lichter an")
        subtitle = " · ".join(infos)

        ext_url = self.config._settings.get("ha_external_url", "").rstrip("/")
        ingress_uri = "homeassistant://navigate/hassio/ingress/a291494a_regis_lab"
        payload = {
            "message": data["summary"],
            "title":   "☀️ Guten Morgen, Sven!",
            "data": {
                "subtitle": subtitle,
                "push": {
                    "sound": "default",
                    "interruption-level": "active",
                },
                "url": "homeassistant://navigate/config/notification",
            },
        }
        targets = self.config._settings.get("briefing_targets", ["mobile_app_svens_iphone"])
        for target in targets:
            try:
                requests.post(
                    ha + f"/api/services/notify/{target}",
                    headers=hdrs, data=json.dumps(payload), timeout=10,
                )
                self.log.info(f"Briefing gesendet an {target}")
            except Exception as e:
                self.log.error(f"Push-Fehler ({target}): {e}")

        # Persistente Benachrichtigung in HA anlegen
        try:
            from datetime import datetime as _dt
            now = _dt.now()
            persistent_payload = {
                "message": data["context"],
                "title":   f"☀️ Morgen-Briefing {now.strftime('%d.%m.%Y')}",
                "notification_id": "regis_lab_morning_briefing",
            }
            requests.post(
                ha + "/api/services/persistent_notification/create",
                headers=hdrs, data=json.dumps(persistent_payload), timeout=10,
            )
            self.log.info("Persistente Benachrichtigung angelegt")
        except Exception as e:
            self.log.error(f"Persistente Benachrichtigung Fehler: {e}")

    def _send_morning_briefing(self):
        data = self._build_briefing()
        self._send_push(data)

    def _scheduler(self):
        while True:
            now = datetime.now()
            # Uhrzeit aus Settings lesen
            time_str = self.config._settings.get("briefing_time", "07:00")
            try:
                hour, minute = int(time_str.split(":")[0]), int(time_str.split(":")[1])
            except Exception:
                hour, minute = 7, 0
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            wait = (target - now).total_seconds()
            self.log.info(f"Nächstes Briefing um {hour:02d}:{minute:02d} Uhr (in {wait/3600:.1f}h)")
            _time.sleep(wait)
            if self.config._settings.get("briefing_enabled", True):
                try:
                    self._send_morning_briefing()
                except Exception as e:
                    self.log.error(f"Briefing-Fehler: {e}")
            else:
                self.log.info("Briefing deaktiviert, wird übersprungen")

    def register(self):

        @self.app.route("/api/briefing/morning")
        def morning_briefing():
            return jsonify(self._build_briefing())

        @self.app.route("/api/briefing/send-now", methods=["POST"])
        def send_briefing_now():
            threading.Thread(target=self._send_morning_briefing, daemon=True).start()
            return jsonify({"ok": True, "message": "Briefing wird gesendet..."})

        threading.Thread(target=self._scheduler, daemon=True).start()
        self.log.info("Briefing-Modul registriert (Scheduler aktiv)")
