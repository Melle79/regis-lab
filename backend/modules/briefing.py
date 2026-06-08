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

        # KI-Zusammenfassung
        model  = self.config._settings.get("jarvis_model", "")
        ollama = self.config.jarvis_ollama_url.rstrip("/")
        summary = context
        if model and ollama:
            try:
                prompt = (
                    "Du bist Jarvis. Erstelle eine kurze freundliche Morgen-Zusammenfassung "
                    "(2-3 Sätze) auf Deutsch ohne Emojis:\n\n" + context
                )
                r = requests.post(ollama + "/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False}, timeout=30)
                summary = r.json().get("response", "").strip() if r.status_code == 200 else context
            except Exception:
                pass

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
        payload = {
            "message": data["summary"],
            "title":   "☀️ Guten Morgen, Sven!",
            "data":    {"subtitle": f"{data['date']} · {data['weather']}"},
        }
        try:
            requests.post(
                ha + "/api/services/notify/mobile_app_svens_iphone",
                headers=hdrs, data=json.dumps(payload), timeout=10,
            )
            self.log.info("Morgen-Briefing gesendet")
        except Exception as e:
            self.log.error(f"Push-Fehler: {e}")

    def _send_morning_briefing(self):
        data = self._build_briefing()
        self._send_push(data)

    def _scheduler(self):
        while True:
            now    = datetime.now()
            target = now.replace(hour=7, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            wait = (target - now).total_seconds()
            self.log.info(f"Nächstes Briefing in {wait/3600:.1f} Stunden")
            _time.sleep(wait)
            try:
                self._send_morning_briefing()
            except Exception as e:
                self.log.error(f"Briefing-Fehler: {e}")

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
