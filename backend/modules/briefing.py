"""
Modul: briefing
Generiert eine tägliche Morgen-Zusammenfassung via Ollama und sendet sie per Push.
Fokus: Wetter-Tagesvorhersage + die wichtigen Termine des Tages.
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
    "snowy-rainy": "Schneeregen", "hail": "Hagel",
    "windy": "Windig", "windy-variant": "Windig", "fog": "Nebel",
    "lightning": "Gewitter", "lightning-rainy": "Gewitter mit Regen",
    "pouring": "Starkregen", "exceptional": "Außergewöhnlich",
}

# Standard-Kalender fürs Briefing (per Setting "briefing_calendars" überschreibbar)
DEFAULT_BRIEFING_CALENDARS = [
    "calendar.abfall_app",
    "calendar.schule_luna_melchior_schultermine",
    "calendar.schule_luna_melchior_arbeiten",
    "calendar.schule_finn_melchior_schultermine",
    "calendar.schule_finn_melchior_arbeiten",
    "calendar.luna_melchior_stundenplan",
    "calendar.finn_melchior_stundenplan",
    "calendar.geburtstage_2",
    "calendar.ferien_feiertage_bayern",
]

# Lesbare Kurz-Labels pro Kalender
CAL_LABELS = {
    "calendar.abfall_app": "Müll",
    "calendar.schule_luna_melchior_schultermine": "Schule Luna",
    "calendar.schule_luna_melchior_arbeiten": "Arbeit Luna",
    "calendar.schule_finn_melchior_schultermine": "Schule Finn",
    "calendar.schule_finn_melchior_arbeiten": "Arbeit Finn",
    "calendar.luna_melchior_stundenplan": "Stundenplan Luna",
    "calendar.finn_melchior_stundenplan": "Stundenplan Finn",
    "calendar.geburtstage_2": "Geburtstag",
    "calendar.ferien_feiertage_bayern": "Ferien/Feiertag",
}


class Module(BaseModule):
    name    = "briefing"
    version = "2.0.0"

    # ── HA-Zugriff ───────────────────────────────────────────────────
    def _ha(self):
        return ("http://homeassistant.local.hass.io:8123",
                {"Authorization": "Bearer " + self.config.ha_long_token,
                 "Content-Type": "application/json"})

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
            r = requests.post(
                ollama + "/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            return r.json().get("response", "").strip() if r.status_code == 200 else ""
        except Exception:
            return ""

    # ── Wetter-Tagesvorhersage ───────────────────────────────────────
    def _weather_forecast_today(self) -> str:
        ha, hdrs = self._ha()
        ent = self.config._settings.get("briefing_weather_entity", "weather.forecast_home")
        try:
            r = requests.post(
                ha + "/api/services/weather/get_forecasts?return_response",
                headers=hdrs,
                data=json.dumps({"entity_id": ent, "type": "daily"}),
                timeout=15,
            )
            if r.status_code != 200:
                return ""
            resp = r.json().get("service_response", {}).get(ent, {})
            fc = resp.get("forecast", [])
            if not fc:
                return ""
            t = fc[0]
            cond = WEATHER_DE.get(t.get("condition", ""), t.get("condition", ""))
            hi, lo = t.get("temperature"), t.get("templow")
            pprob, precip = t.get("precipitation_probability"), t.get("precipitation")
            wind = t.get("wind_speed")
            parts = [cond] if cond else []
            if lo is not None and hi is not None:
                parts.append(f"{round(lo)}–{round(hi)}°C")
            elif hi is not None:
                parts.append(f"bis {round(hi)}°C")
            if pprob is not None:
                parts.append(f"Regen {round(pprob)}%")
            elif precip:
                parts.append(f"{precip} mm Regen")
            if wind is not None:
                parts.append(f"Wind {round(wind)} km/h")
            return ", ".join(str(p) for p in parts if p not in ("", None))
        except Exception:
            return ""

    # ── Heutige Termine ──────────────────────────────────────────────
    def _today_events(self, calendars: list) -> list:
        ha, hdrs = self._ha()
        now   = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = start + timedelta(days=1)
        out = []
        for cal in calendars:
            try:
                r = requests.get(
                    ha + f"/api/calendars/{cal}",
                    headers=hdrs,
                    params={"start": start.isoformat(), "end": end.isoformat()},
                    timeout=10,
                )
                if r.status_code != 200:
                    continue
                for ev in r.json():
                    summary = (ev.get("summary") or "").strip()
                    if not summary:
                        continue
                    st = ev.get("start", {})
                    tm = ""
                    if isinstance(st, dict) and st.get("dateTime"):
                        try:
                            tm = datetime.fromisoformat(
                                st["dateTime"].replace("Z", "+00:00")).strftime("%H:%M")
                        except Exception:
                            tm = ""
                    out.append({"calendar": cal, "summary": summary, "time": tm})
            except Exception:
                continue
        return out

    # ── Briefing zusammenbauen ───────────────────────────────────────
    def _build_briefing(self) -> dict:
        weather_text = self._weather_forecast_today()

        calendars = self.config._settings.get("briefing_calendars", DEFAULT_BRIEFING_CALENDARS)
        events    = self._today_events(calendars)

        # Offline-Geräte als kleiner Hinweis (aus letztem Analyse-Report)
        offline_count = 0
        try:
            if os.path.exists("/data/analyse_reports.json"):
                reports = json.load(open("/data/analyse_reports.json"))
                if reports:
                    offline_count = reports[0].get("counts", {}).get("offline", 0)
        except Exception:
            pass

        now = datetime.now()
        date_str = f"{DAYS_DE[now.weekday()]}, {now.day}. {MONTHS_DE[now.month-1]} {now.year}"

        # Kontext für die KI
        lines = [f"Datum: {date_str}"]
        if weather_text:
            lines.append(f"Wetter heute: {weather_text}")
        if events:
            lines.append("Heutige Termine:")
            for ev in events:
                label  = CAL_LABELS.get(ev["calendar"], "")
                prefix = f"[{label}] " if label else ""
                tm     = f"{ev['time']} " if ev["time"] else ""
                lines.append(f"- {prefix}{tm}{ev['summary']}")
        else:
            lines.append("Heute keine Termine in den Kalendern.")
        if offline_count:
            lines.append(f"Hinweis: {offline_count} Geräte offline.")
        context = "\n".join(lines)

        prompt = (
            "Du bist ein persönlicher Assistent und erstellst ein kurzes, nützliches Morgen-Briefing "
            "auf Deutsch. Konzentriere dich auf das Wetter im Tagesverlauf und die wichtigen Termine "
            "des Tages. Fasse Schul- und Stundenplan kurz zusammen (nicht jede Stunde einzeln nennen). "
            "Schreibe 3–5 flüssige Sätze, freundlich, ohne Emojis und ohne Geräte-Aufzählungen.\n\n"
            + context
        )
        summary = self._call_ki(prompt) or context

        return {
            "date":          date_str,
            "weather":       weather_text,
            "events":        events,
            "offline_count": offline_count,
            "summary":       summary,
            "context":       context,
        }

    # ── Push senden ──────────────────────────────────────────────────
    def _send_push(self, data: dict):
        ha, hdrs = self._ha()

        infos = []
        if data.get("weather"):
            infos.append(data["weather"])
        n = len(data.get("events", []))
        if n:
            infos.append(f"🗓️ {n} Termin{'e' if n != 1 else ''}")
        if data.get("offline_count"):
            infos.append(f"⚠️ {data['offline_count']} offline")
        subtitle = " · ".join(infos)

        payload = {
            "message": data["summary"],
            "title":   "☀️ Guten Morgen!",
            "data": {
                "subtitle": subtitle,
                "push": {"sound": "default", "interruption-level": "active"},
                "url": "homeassistant://navigate/lovelace/0",
            },
        }
        targets = self.config._settings.get("briefing_targets", ["mobile_app_svens_iphone"])
        for target in targets:
            try:
                requests.post(ha + f"/api/services/notify/{target}",
                              headers=hdrs, data=json.dumps(payload), timeout=10)
                self.log.info(f"Briefing gesendet an {target}")
            except Exception as e:
                self.log.error(f"Push-Fehler ({target}): {e}")

        # Persistente Benachrichtigung in HA anlegen
        try:
            now = datetime.now()
            requests.post(
                ha + "/api/services/persistent_notification/create",
                headers=hdrs,
                data=json.dumps({
                    "message": data["context"],
                    "title":   f"☀️ Morgen-Briefing {now.strftime('%d.%m.%Y')}",
                    "notification_id": "regis_lab_morning_briefing",
                }),
                timeout=10,
            )
        except Exception as e:
            self.log.error(f"Persistente Benachrichtigung Fehler: {e}")

    def _send_morning_briefing(self):
        data = self._build_briefing()
        self._send_push(data)

    # ── Scheduler ────────────────────────────────────────────────────
    def _scheduler(self):
        while True:
            now = datetime.now()
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
        self.log.info("Briefing-Modul v2 registriert (Scheduler aktiv)")
