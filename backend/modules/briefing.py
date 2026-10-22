"""
Modul: briefing
Generiert eine tägliche Morgen-Zusammenfassung via Ollama und sendet sie per Push.
Fokus: Wetter, die wichtigen Termine des Tages und wer wann wieder daheim ist.
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

# Kalender fürs Briefing.
#
# Hier steht bewusst NICHTS drin: Welche Kalender ein Haushalt führt und wie
# die Personen darin heißen, geht niemanden etwas an, der dieses Repository
# liest. Die eigene Liste gehört in die Einstellung "briefing_calendars"
# (landet in /data, nicht im Quelltext). Ohne Eintrag greift die Erkennung
# unten: alle Kalender, die Home Assistant kennt.
DEFAULT_BRIEFING_CALENDARS: list = []

# Dasselbe für die Kurz-Labels: ohne Eintrag nimmt das Briefing den
# Anzeigenamen des Kalenders aus Home Assistant.
DEFAULT_CAL_LABELS: dict = {}

# Schulschluss-Sensoren werden erkannt, nicht aufgezählt – der
# Stundenplan-Manager legt sie nach diesem Muster an, und der Name des Kindes
# steht im Attribut "kind", nicht in unserem Quelltext.
SCHULSCHLUSS_PRAEFIX = "sensor.stundenplan_"
SCHULSCHLUSS_SUFFIX  = "_schulschluss_heute"

# Minuten vom Schultor bis zur Haustür, je Kind: {"<Kind>": 25}. Das weiß kein
# Sensor, das weiß nur der Haushalt – deshalb eine Einstellung. Leer gelassen,
# nennt das Briefing nur den Schulschluss, statt eine Ankunft zu erfinden.
DEFAULT_HEIMWEG_MIN: dict = {}

# Zustände, die „heute kein Unterricht" bedeuten
KEIN_UNTERRICHT = ("", "-", "–", "—", "unknown", "unavailable", "none")

# Mail-Sensor fürs Briefing (per Setting "briefing_mail_sensor" überschreibbar)
DEFAULT_MAIL_SENSOR = "sensor.outlook_mail_mail"

# So viele ungelesene Mails gehen maximal zur Bewertung an die KI
MAIL_TRIAGE_LIMIT = 25

# Absender-Bestandteile, die auf Massenversand hindeuten. Kein harter Filter —
# die Zeile wird nur markiert, entscheiden soll weiterhin die KI.
AUTOMATED_SENDER_HINTS = (
    "noreply", "no-reply", "donotreply", "do-not-reply", "nicht-antworten",
    "newsletter", "mailer", "notifications", "notification", "alert",
    "info@", "service@", "news@", "marketing@",
)


class Module(BaseModule):
    name    = "briefing"
    version = "2.2.0"

    # Anzeigenamen der Kalender werden je Lauf nur einmal geholt
    _label_cache: dict = {}

    # ── HA-Zugriff ───────────────────────────────────────────────────
    def _ha(self):
        return ("http://homeassistant.local.hass.io:8123",
                {"Authorization": "Bearer " + self.config.ha_long_token,
                 "Content-Type": "application/json"})

    def _call_ki(self, prompt: str, timeout: int = 60) -> str:
        """KI-Aufruf — bewusst fest auf das lokale Ollama verdrahtet.

        Das Briefing verarbeitet Kalendereinträge und Mail-Metadaten (Absender,
        Betreff). Die bleiben im Haus: kein Cloud-Provider, auch wenn Jarvis auf
        einen solchen konfiguriert ist.
        """
        model  = self.config._settings.get("jarvis_model", "")
        ollama = self.config.jarvis_ollama_url.rstrip("/")
        if not model or not ollama:
            return ""
        try:
            r = requests.post(
                ollama + "/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=timeout,
            )
            return r.json().get("response", "").strip() if r.status_code == 200 else ""
        except Exception as e:
            self.log.error(f"Ollama-Aufruf fehlgeschlagen: {e}")
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

    # ── Kalender-Labels ──────────────────────────────────────────────
    def _cal_label(self, entity_id: str) -> str:
        """Kurzname eines Kalenders – aus den Einstellungen oder aus HA.

        Eine fest verdrahtete Tabelle wäre bequemer, verriete aber jedem
        Leser des Repositories, wer hier wohnt. Der Anzeigename steht ohnehin
        in Home Assistant.
        """
        eigene = self.config._settings.get("briefing_calendar_labels", DEFAULT_CAL_LABELS) or {}
        if entity_id in eigene:
            return eigene[entity_id]
        if entity_id in self._label_cache:
            return self._label_cache[entity_id]
        ha, hdrs = self._ha()
        label = ""
        try:
            r = requests.get(ha + f"/api/states/{entity_id}", headers=hdrs, timeout=10)
            if r.status_code == 200:
                label = (r.json().get("attributes", {}) or {}).get("friendly_name", "") or ""
        except Exception:
            label = ""
        self._label_cache[entity_id] = label
        return label

    def _alle_kalender(self) -> list:
        """Jeden Kalender nehmen, den Home Assistant kennt – als Rückfallebene."""
        ha, hdrs = self._ha()
        try:
            r = requests.get(ha + "/api/calendars", headers=hdrs, timeout=10)
            if r.status_code != 200:
                return []
            return [c.get("entity_id") for c in r.json() if c.get("entity_id")]
        except Exception as e:
            self.log.error(f"Kalenderliste nicht lesbar: {e}")
            return []

    # ── Wer kommt wann heim ──────────────────────────────────────────
    def _heimkehr(self) -> list:
        """Schulschluss je Kind, auf Wunsch samt Heimweg.

        Das ist der einzige Teil des Stundenplans, der morgens zählt: nicht,
        welche Stunde wann ist, sondern ab wann wieder jemand im Haus ist.
        Ein Kind ohne Schulschluss (Ferien, Betrieb, Praktikum) wird genannt
        statt verschwiegen – „heute keine Schule" ist auch eine Auskunft.
        """
        heimweg = self.config._settings.get("briefing_heimweg", DEFAULT_HEIMWEG_MIN) or {}
        out = []
        for roh in self._schulschluss_sensoren():
            attrs   = roh.get("attributes", {}) or {}
            ent     = roh.get("entity_id", "")
            name    = (attrs.get("kind") or "").strip() or ent.split(".")[-1]
            zustand = (roh.get("state") or "").strip()

            if zustand.lower() in KEIN_UNTERRICHT:
                out.append({"name": name, "zeit": "",
                            "text": self._warum_frei(ent) or "heute keine Schule"})
                continue

            text    = f"Schluss {zustand}"
            minuten = heimweg.get(name)
            if minuten:
                daheim = self._plus_minuten(zustand, minuten)
                if daheim:
                    text = f"Schluss {zustand}, daheim gegen {daheim}"
            out.append({"name": name, "zeit": zustand, "text": text})

        # Wer zuerst daheim ist, steht oben; Kinder ohne Zeit ans Ende
        out.sort(key=lambda k: k["zeit"] or "99:99")
        return out

    def _schulschluss_sensoren(self) -> list:
        """Alle Schulschluss-Sensoren einsammeln – erkannt, nicht aufgezählt."""
        ha, hdrs = self._ha()
        gesetzt = self.config._settings.get("briefing_school_sensors") or []
        try:
            r = requests.get(ha + "/api/states", headers=hdrs, timeout=20)
            if r.status_code != 200:
                return []
            alle = r.json()
        except Exception as e:
            self.log.error(f"Zustandsliste nicht lesbar: {e}")
            return []
        if gesetzt:
            return [s for s in alle if s.get("entity_id") in gesetzt]
        return [s for s in alle
                if str(s.get("entity_id", "")).startswith(SCHULSCHLUSS_PRAEFIX)
                and str(s.get("entity_id", "")).endswith(SCHULSCHLUSS_SUFFIX)]

    def _warum_frei(self, schluss_sensor: str) -> str:
        """Der Nachbarsensor sagt, warum heute nichts anliegt (z. B. „Betrieb")."""
        ha, hdrs = self._ha()
        ent = schluss_sensor.replace(SCHULSCHLUSS_SUFFIX, "_aktuelle_stunde")
        try:
            r = requests.get(ha + f"/api/states/{ent}", headers=hdrs, timeout=10)
            if r.status_code != 200:
                return ""
            zustand = (r.json().get("state") or "").strip()
            return "" if zustand.lower() in KEIN_UNTERRICHT else zustand
        except Exception:
            return ""

    @staticmethod
    def _plus_minuten(uhrzeit: str, minuten) -> str:
        """„14:15" + 25 → „14:40". Unlesbare Eingaben geben leer zurück."""
        try:
            stunde, minute = (int(x) for x in uhrzeit.split(":")[:2])
            return (datetime(2000, 1, 1, stunde, minute)
                    + timedelta(minutes=int(minuten))).strftime("%H:%M")
        except Exception:
            return ""

    # ── Ungelesene Mails ─────────────────────────────────────────────
    def _unread_mails(self) -> list:
        """Ungelesene Mails aus dem ms365_mail-Sensor (nur Metadaten, kein Body)."""
        ha, hdrs = self._ha()
        ent = self.config._settings.get("briefing_mail_sensor", DEFAULT_MAIL_SENSOR)
        if not ent:
            return []
        try:
            r = requests.get(ha + f"/api/states/{ent}", headers=hdrs, timeout=10)
            if r.status_code != 200:
                return []
            data = r.json().get("attributes", {}).get("data", [])
            return data if isinstance(data, list) else []
        except Exception as e:
            self.log.error(f"Mail-Sensor {ent} nicht lesbar: {e}")
            return []

    def _triage_mails(self, mails: list) -> str:
        """Lässt die lokale KI entscheiden, welche Mails Aufmerksamkeit brauchen."""
        rows = []
        for m in mails[:MAIL_TRIAGE_LIMIT]:
            subject = (m.get("subject") or "").strip()
            sender  = (m.get("sender") or "").strip()
            if not subject and not sender:
                continue
            flags = []
            if m.get("importance") == "high":
                flags.append("Priorität hoch")
            if m.get("has_attachments"):
                flags.append("Anhang")
            if any(t in sender.lower() for t in AUTOMATED_SENDER_HINTS):
                flags.append("Automatik-Absender")
            suffix = f" [{', '.join(flags)}]" if flags else ""
            rows.append(f"- {sender or 'Unbekannt'} | {subject or '(kein Betreff)'}{suffix}")
        if not rows:
            return ""

        prompt = (
            "Du bist ein strenger Assistent und siebst einen Posteingang vor. "
            "Unten stehen ungelesene Mails als 'Absender | Betreff'.\n\n"
            "Nenne NUR Mails, bei denen eine Person heute etwas tun muss: antworten, "
            "einen Termin wahrnehmen, eine Frist einhalten, ein Problem lösen.\n\n"
            "Immer weglassen, ohne Ausnahme:\n"
            "- Newsletter, Werbung, Rabatte, Gutscheine, Umfragen\n"
            "- Stellenanzeigen und Job-Alarme\n"
            "- Social-Media- und App-Benachrichtigungen\n"
            "- Bestell-, Versand- und Zahlungsbestätigungen\n"
            "- Werbliche Kontostands- oder Aufladehinweise\n\n"
            "Mails mit dem Vermerk [Automatik-Absender] sind fast immer Massenversand. "
            "Nimm sie nur auf, wenn der Betreff ein echtes Problem oder eine Frist nennt "
            "— etwa Mahnung, Kündigung, Kontosperrung, Terminabsage, Rechnung fällig.\n\n"
            "Lieber zu wenig nennen als zu viel. Bist du unsicher, lass die Mail weg.\n\n"
            "Ausgabeformat, exakt so, ohne Einleitung und ohne Erklärung:\n"
            "- Absender: worum es geht\n\n"
            "Beispiel für eine gute Antwort:\n"
            "- Frau Weber (Schule): Rückmeldung zum Elternabend bis Freitag\n"
            "- Stadtwerke: Abschlagszahlung überfällig\n\n"
            "Höchstens vier Zeilen, je Zeile maximal acht Wörter. Statt des Absenders "
            "gern der erkennbare Name oder die Firma, nicht die rohe Mailadresse.\n"
            "Ist nichts dabei, antworte ausschließlich mit dem Wort KEINE.\n\n"
            "Ungelesene Mails:\n"
            + "\n".join(rows)
        )
        out = self._call_ki(prompt, timeout=120).strip()
        if not out or out.upper().startswith("KEINE"):
            return ""

        keep = []
        for line in out.splitlines():
            line = line.strip()
            # Nur Aufzählungszeilen; Vorgeplauder des Modells fliegt raus
            if not line.startswith(("-", "•", "*")):
                continue
            line = "- " + line.lstrip("-•* ").strip()
            if line.upper().startswith("- KEINE"):
                continue
            # Spiegelt das Modell das Eingabeformat "Absender | Betreff", in die
            # gewünschte Form umschreiben statt die Zeile zu verwerfen
            if " | " in line:
                sender, _, rest = line[2:].partition(" | ")
                rest = rest.split(" [")[0].strip()
                line = f"- {sender.strip()}: {rest}"
            keep.append(line)
        return "\n".join(keep[:4]) if keep else ""

    # ── Briefing zusammenbauen ───────────────────────────────────────
    def _build_briefing(self) -> dict:
        weather_text = self._weather_forecast_today()

        calendars = (self.config._settings.get("briefing_calendars", DEFAULT_BRIEFING_CALENDARS)
                     or self._alle_kalender())
        events    = self._today_events(calendars)
        heimkehr  = self._heimkehr()

        mails        = self._unread_mails()
        unread_count = len(mails)
        mail_digest  = self._triage_mails(mails)

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
                label  = self._cal_label(ev["calendar"])
                prefix = f"[{label}] " if label else ""
                tm     = f"{ev['time']} " if ev["time"] else ""
                lines.append(f"- {prefix}{tm}{ev['summary']}")
        else:
            lines.append("Heute keine Termine in den Kalendern.")
        if heimkehr:
            lines.append("Wer wann heimkommt:")
            for kind in heimkehr:
                lines.append(f"- {kind['name']}: {kind['text']}")
        if mail_digest:
            lines.append(f"Ungelesene Mails: {unread_count}, davon beachtenswert:")
            lines.extend(mail_digest.splitlines())
        elif unread_count:
            lines.append(f"Ungelesene Mails: {unread_count}, nichts Dringendes dabei.")
        if offline_count:
            lines.append(f"Hinweis: {offline_count} Geräte offline.")
        context = "\n".join(lines)

        prompt = (
            "Du bist ein persönlicher Assistent und erstellst ein kurzes, nützliches Morgen-Briefing "
            "auf Deutsch. Konzentriere dich auf das Wetter im Tagesverlauf und die wichtigen Termine "
            "des Tages. Nenne unter \"Wer wann heimkommt\" jede Person mit ihrer Zeit in einem "
            "einzigen Satz – das ist die wichtigste Zeile des Briefings. Einzelne Schulstunden "
            "nennst du nie. "
            "Erwähne beachtenswerte Mails in einem eigenen Satz am Ende; sind keine aufgeführt, lass "
            "das Thema Mail ganz weg. "
            "Schreibe 3–5 flüssige Sätze, freundlich, ohne Emojis und ohne Geräte-Aufzählungen.\n\n"
            + context
        )
        summary = self._call_ki(prompt) or context

        return {
            "date":          date_str,
            "weather":       weather_text,
            "events":        events,
            "heimkehr":      heimkehr,
            "unread_mails":  unread_count,
            "mail_digest":   mail_digest,
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
        if data.get("mail_digest"):
            infos.append("📬 Mails beachten")
        elif data.get("unread_mails"):
            infos.append(f"📬 {data['unread_mails']} ungelesen")
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

        @self.app.route("/api/briefing/mail-triage")
        def mail_triage():
            """Nur die Mail-Bewertung — zum Nachjustieren des Prompts."""
            mails = self._unread_mails()
            return jsonify({
                "unread":  len(mails),
                "digest":  self._triage_mails(mails),
            })

        @self.app.route("/api/briefing/send-now", methods=["POST"])
        def send_briefing_now():
            threading.Thread(target=self._send_morning_briefing, daemon=True).start()
            return jsonify({"ok": True, "message": "Briefing wird gesendet..."})

        threading.Thread(target=self._scheduler, daemon=True).start()
        self.log.info("Briefing-Modul v2 registriert (Scheduler aktiv)")
