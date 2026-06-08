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
            WEATHER_DE = {
                "sunny": "Sonnig", "clear-night": "Klare Nacht",
                "cloudy": "Bewölkt", "partlycloudy": "Teils bewölkt",
                "rainy": "Regen", "snowy": "Schnee", "windy": "Windig",
                "fog": "Nebel", "lightning": "Gewitter", "hail": "Hagel",
                "pouring": "Starkregen", "exceptional": "Außergewöhnlich",
            }
            weather_text = ""
            if weather:
                temp  = weather.get("attributes", {}).get("temperature", "?")
                state = weather.get("state", "")
                cond  = WEATHER_DE.get(state, state)
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

            # Lichter die noch an sind — ohne Segmente
            lights_on = []
            seen_lights = set()
            for s in states:
                if not s["entity_id"].startswith("light.") or s["state"] != "on":
                    continue
                name = s.get("attributes", {}).get("friendly_name", s["entity_id"])
                # Segmente überspringen
                if " Segment " in name:
                    # Basisname ohne Segment merken
                    base = name.split(" Segment ")[0]
                    if base not in seen_lights:
                        seen_lights.add(base)
                        lights_on.append(base)
                    continue
                if name not in seen_lights:
                    seen_lights.add(name)
                    lights_on.append(name)

            # Kontext für KI
            context_parts = []
            import locale
            try:
                locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
            except Exception:
                pass
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
                "date":          datetime.now().strftime("%A, %d. %B %Y").replace("Monday","Montag").replace("Tuesday","Dienstag").replace("Wednesday","Mittwoch").replace("Thursday","Donnerstag").replace("Friday","Freitag").replace("Saturday","Samstag").replace("Sunday","Sonntag").replace("January","Januar").replace("February","Februar").replace("March","März").replace("April","April").replace("May","Mai").replace("June","Juni").replace("July","Juli").replace("August","August").replace("September","September").replace("October","Oktober").replace("November","November").replace("December","Dezember"),
                "time":          datetime.now().strftime("%H:%M"),
                "weather":       weather_text,
                "persons_home":  persons_home,
                "offline_count": offline_count,
                "lights_on":     lights_on,
                "summary":       summary,
                "context":       context,
            })

        self.log.info("Briefing-Modul registriert")
