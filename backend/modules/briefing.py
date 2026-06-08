"""
Modul: briefing
Generiert eine tägliche Morgen-Zusammenfassung via Ollama.
"""
import json
import requests
from datetime import datetime
from flask import jsonify
from modules.base import BaseModule


class Module(BaseModule):
    name    = "briefing"
    version = "1.0.0"

    def register(self):

        @self.app.route("/api/briefing/morning")
        def morning_briefing():
            """Tägliche Morgen-Zusammenfassung für Push-Nachricht."""
            ha    = "http://homeassistant.local.hass.io:8123"
            hdrs  = {"Authorization": "Bearer " + self.config.ha_long_token}
            model  = self.config._settings.get("jarvis_model", "")
            ollama = self.config.jarvis_ollama_url.rstrip("/")

            # States laden
            try:
                states_r = requests.get(ha + "/api/states", headers=hdrs, timeout=15)
                states   = states_r.json() if states_r.status_code == 200 else []
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
                temp   = weather.get("attributes", {}).get("temperature", "?")
                cond   = weather.get("attributes", {}).get("friendly_name", weather.get("state", ""))
                weather_text = f"{cond}, {temp}°C"

            # Offline-Geräte (aus letztem Diagnose-Bericht)
            offline_count = 0
            try:
                import os, json as _json
                if os.path.exists("/data/analyse_reports.json"):
                    reports = _json.load(open("/data/analyse_reports.json"))
                    if reports:
                        offline_count = reports[0].get("counts", {}).get("offline", 0)
            except Exception:
                pass

            # Lichter die noch an sind
            lights_on = [
                s.get("attributes", {}).get("friendly_name", s["entity_id"])
                for s in states
                if s["entity_id"].startswith("light.") and s["state"] == "on"
            ]

            # Kontext für KI
            context_parts = []
            context_parts.append(f"Datum: {datetime.now().strftime('%A, %d. %B %Y')}")
            context_parts.append(f"Uhrzeit: {datetime.now().strftime('%H:%M')} Uhr")
            if weather_text:
                context_parts.append(f"Wetter: {weather_text}")
            if persons_home:
                context_parts.append(f"Zuhause: {', '.join(persons_home)}")
            else:
                context_parts.append("Niemand zuhause")
            if offline_count > 0:
                context_parts.append(f"Offline-Geräte: {offline_count}")
            if lights_on:
                context_parts.append(f"Lichter noch an: {', '.join(lights_on[:5])}")

            context = "\n".join(context_parts)

            # KI-Zusammenfassung
            summary = ""
            if model and ollama:
                try:
                    prompt = (
                        "Du bist Jarvis, ein freundlicher Smart Home Assistent. "
                        "Erstelle eine kurze, freundliche Morgen-Zusammenfassung (max. 3 Sätze) auf Deutsch "
                        "basierend auf diesen Informationen:\n\n" + context + "\n\n"
                        "Keine Emojis. Sei prägnant und informativ."
                    )
                    r = requests.post(
                        ollama + "/api/generate",
                        json={"model": model, "prompt": prompt, "stream": False},
                        timeout=30,
                    )
                    summary = r.json().get("response", "").strip() if r.status_code == 200 else ""
                except Exception:
                    pass

            return jsonify({
                "date":          datetime.now().strftime("%A, %d. %B %Y"),
                "time":          datetime.now().strftime("%H:%M"),
                "weather":       weather_text,
                "persons_home":  persons_home,
                "offline_count": offline_count,
                "lights_on":     lights_on,
                "summary":       summary,
                "context":       context,
            })

        self.log.info("Briefing-Modul registriert")
