# Changelog

Alle wichtigen Änderungen an Regis-Lab werden hier dokumentiert.

---

## [1.11.9] - 2026-11-04

### Behoben
- **Falsche Modelle im Ollama-Feld.** Das Feld „Standard-Modell" im Bereich „Lokaler
  KI-Assistent" holte die Modellliste ohne Anbieter-Angabe – das Backend nahm dann
  den aktuell eingestellten Cloud-Anbieter und zeigte deshalb Claude-Modelle
  (`claude-haiku-5-5` …) in der lokalen Auswahl. Jetzt werden ausschließlich die
  Modelle der eingetragenen Ollama-Installation angezeigt.
- **API-Schlüssel-Felder waren unsichtbar.** Die sechs Felder erschienen nur, wenn
  unter „Cloud KI" ein Anbieter ausgewählt war – bei „Keinen Cloud-Anbieter nutzen"
  waren sie ausgeblendet. Sie stehen jetzt immer da; nur die Schalter
  „primär/Fallback" hängen weiter am gewählten Anbieter.

---

## [1.11.8] - 2026-11-04

### Hinzugefügt
- **Claude auch ohne Anthropic-Schlüssel:** In der OpenRouter-Auswahl stehen jetzt
  zusätzlich `anthropic/claude-haiku-5.5`, `anthropic/claude-sonnet-5.5` und
  `anthropic/claude-opus-5.5`. Damit laufen die Claude-Modelle über den bereits
  hinterlegten OpenRouter-Schlüssel (Guthaben dort) – inklusive Bildern, denn
  OpenRouter führt die Claude-Modelle mit Bild-Eingabe. Ein eigener Anthropic-API-Key
  (console.anthropic.com, eigenes Guthaben) ist nur nötig, wenn du Claude direkt
  ansteuern willst.

### Hinweis
- Das Claude-Pro-Abo (Claude Code) enthält **keinen** API-Schlüssel. Der auf dem
  Mac mini hinterlegte Zugang (`~/.claude/.credentials.json`,
  `sk-ant-oat01-…`) ist ein Abo-Token und für die Anthropic-API nicht geeignet.

---

## [1.11.7] - 2026-11-04

### Geändert
- **Alle API-Schlüssel auf einen Blick** (Einstellungen → „Cloud KI"). Bisher gab
  es dort nur ein Feld, das sich mit der Anbieter-Auswahl änderte – man musste den
  Anbieter umstellen und einzeln speichern und sah nicht, was schon hinterlegt war.
  Jetzt stehen **alle sechs** Anbieter untereinander: Claude (Anthropic),
  OpenRouter, OpenAI, Google (Gemini), Mistral, Groq – je mit Feld, Auge-Symbol
  und Status **„✓ gesetzt"** bzw. „—". Leer lassen ändert nichts, bestehende
  Schlüssel bleiben erhalten.

### Technisch
- `core/config.py`: `*_api_key_set`-Status gibt es jetzt für alle sechs Anbieter
  (vorher nur Anthropic und OpenRouter), damit die Oberfläche den Zustand zeigen
  kann.

---

## [1.11.6] - 2026-11-04

### Hinzugefügt
- **Der passende Cline-Verlauf geht automatisch mit.** Fragst du im Jarvis-Chat
  nach früherer Arbeit („womit haben wir zuletzt gearbeitet?", „setze das fort")
  oder passt ein Chat-Titel zum Thema deiner Frage, liest Jarvis den passenden
  Cline-Chat vom Mac mini und nutzt ihn als Kontext – ohne Knopf, ohne Nachfrage.
  Im Chat steht dabei „📄 Cline-Verlauf: … – als Kontext mitgegeben", und die
  Nachricht behält diesen Hinweis auch nach dem Neuladen. Das Werkzeug zum
  gezielten Lesen (`{"mini": {"action": "cline"}}`) bleibt zusätzlich erhalten.

---

## [1.11.5] - 2026-11-04

### Behoben
- **Cline-Chats waren zeitweise nicht zu sehen.** Die Liste wird über SSH vom
  Mac mini gelesen; die Cline-Datenbank ist während der Arbeit in VS Code oft
  kurz gesperrt. Dann stand dort nur „Antwort der Datenbank nicht lesbar" und die
  Liste blieb leer. Jetzt wird kurz gewartet und einmal erneut gelesen; klappt es
  weiterhin nicht, steht die Rohantwort in der Meldung (statt eines Rätseltexts).
  Dasselbe gilt für einen einzelnen Chat-Verlauf.
- **SSH-Warnungen machen JSON-Antworten nicht mehr kaputt.** Beim ersten
  Verbindungsaufbau schreibt SSH „Warning: Permanently added … to the list of
  known hosts" auf die Fehlerausgabe – die wurde an die Nutzausgabe gehängt und
  machte JSON-Antworten unlesbar. Diese Warnung wird jetzt herausgefiltert,
  echte Fehlermeldungen bleiben erhalten.

---

## [1.11.4] - 2026-11-04

### Behoben
- **Fehlermeldungen im Chat sind jetzt eindeutig.** Eine Meldung wie
  „Unexpected non-whitespace character after JSON at position 3" ließ sich keiner
  Stelle zuordnen. Jetzt steht dabei, woher sie kommt: „Fehler vom Server: …"
  (die KI-Antwort kam als Fehler zurück) oder „Fehler im Browser: …" (der Fehler
  entstand in der Oberfläche, z. B. weil eine Antwort kein JSON war).
- **Nachladen kann die Antwort nicht mehr verdrängen.** Nach einer Antwort lädt
  die Oberfläche den Chat neu. Schlug das fehl, erschien statt der Antwort eine
  Fehlermeldung. Jetzt wird ein Fehler beim Nachladen nur in der Browser-Konsole
  vermerkt, die Antwort bleibt stehen.
- Antworten, die kein JSON sind, werden mit HTTP-Code und Textanfang gemeldet
  (z. B. „Antwort von api/jarvis/chats war kein JSON (HTTP 404): …") – auch in der
  Schnellfrage der Übersicht.

### Technisch
- `JarvisPanel.vue`: neuer Helfer `fetchJson()` für die Chat-Aufrufe.
- `HomePanel.vue`: JSON-Antwort der Schnellfrage wird geprüft statt blind geparst.
- `jarvis.py`: Bricht der Antwort-Stream ab, wird die Ursache jetzt mit
  Traceback ins Add-on-Log geschrieben (`self.log.exception`).

---

## [1.11.3] - 2026-11-03

### Behoben
- **Veraltete Modellnamen bei Claude und Gemini.** In der Anbieterliste standen
  noch Modelle, die nicht mehr aktuell sind – bei Google war `gemini-2.0-flash`
  sogar bereits abgeschaltet. Claude steht jetzt mit `claude-haiku-5-5`,
  `claude-sonnet-5-5` und `claude-opus-5-5` bereit (die bisherigen 4.x-Modelle
  bleiben als Ausweichmöglichkeit in der Liste). Bei Gemini sind es
  `gemini-flash-latest`, `gemini-3.8-flash`, `gemini-3.6-flash` und
  `gemini-3.5-flash-lite`. Auch die Vorgabemodelle im Code wurden angepasst.

---

## [1.11.2] - 2026-11-03

### Hinzugefügt
- **Bilder auch bei Claude und Gemini**: Bisher ging ein angehängtes Bild nur an
  OpenRouter/Ollama. Jetzt bekommen auch die direkt eingetragenen Anbieter
  Anthropic (Claude) und Google (Gemini) das Bild – jeder im Format, das seine
  Schnittstelle erwartet.

### Technisch
- Neue Hilfsfunktionen in `ki_providers.py`: `image_content_parts()` baut den
  Nachrichteninhalt je Anbieter (Text + Bild), `image_base64_list()` das
  Ollama-Format, `_google_parts()` wandelt beliebige Inhalte in Gemini-Parts um.

---

## [1.11.1] - 2026-11-03

### Behoben
- **Werkzeug-Blöcke sind aus dem Chat verschwunden.** Den JSON-Block
  (`{"mini": {...}}`), mit dem Jarvis einen Auftrag für den Mac mini formuliert,
  hat das Modell mit in den Text geschrieben – er wurde mitgespeichert und war
  nach dem Neuladen als roher JSON sichtbar. Er wird jetzt weder gespeichert noch
  angezeigt; auch alte Chat-Verläufe zeigen ihn nicht mehr. Bricht man eine
  Antwort ab, bleibt der Block ebenfalls draußen.

---

## [1.11.0] - 2026-11-03

### Hinzugefügt
- **Bilder in den Chat ziehen**: Bilder lassen sich in den Jarvis-Chat ziehen,
  mit Strg/Cmd+V einfügen oder über das Bild-Symbol auswählen. Vor dem Senden
  erscheint eine kleine Vorschau; nach dem Senden steht das Bild in der Nachricht
  und lässt sich zum Ansehen anklicken.
- **Jarvis sieht das Bild**: Bei OpenAI-kompatiblen Anbietern (u. a. OpenRouter)
  und bei Ollama geht das Bild zusammen mit dem Text an das Modell – Fragen zu
  Screenshots oder Fotos sind damit direkt möglich.

### Technisch
- `POST /api/jarvis/chats/<id>/chat` nimmt zusätzlich `images` entgegen (DataURL
  oder Base64, max. vier Bilder). Der Verlauf wird beim Aufbau der Modellanfrage
  auf Rolle und Inhalt reduziert, damit Anzeigefelder nicht an den Anbieter gehen.
  Eine Anfrage nur mit Bild (ohne Text) ist möglich.

---

## [1.10.0] - 2026-11-03

### Hinzugefügt
- **Cline-Chats lesen** (optional): Neuer Bereich „Cline" zeigt die Chats, die am
  Mac mini mit Cline geführt wurden – Titel, Modell, Zeit und Verlauf.
  Eingeschaltet wird er in den Einstellungen im Abschnitt „Mac mini"; dort steht
  auch das Verzeichnis der Cline-Daten (Vorgabe `~/.cline/data`).
- Jarvis darf dieselben Chats lesen (`{"mini": {"action": "cline", "op": "list"}}`
  bzw. `… "op": "show", "id": …`), wenn die Cline-Chats eingeschaltet sind.

### Hinweise
- Der Bereich liest nur: Ein Cline-Chat lebt in der VS-Code-Erweiterung und lässt
  sich von hier aus **nicht** fortsetzen.
- Der Cline-Tab erscheint automatisch in der Kopfzeile, sobald der Schalter an ist.

## [1.9.0] - 2026-11-03

### Hinzugefügt
- **Jarvis darf auf dem Mac mini arbeiten.** Neuer Abschnitt „Mac mini" in den
  Einstellungen: Adresse, Benutzer, Arbeitswurzel, „ohne Rückfrage" und Schritte
  je Frage. Voreingestellt ist der Mac mini mit der Wurzel `~/Vibe_Coding` – alles
  bleibt änderbar, ein Schalter schaltet den Zugriff ganz ab.
- Werkzeuge im Chat: Datei lesen, Datei schreiben, Ordner auflisten, Befehl
  ausführen – nur innerhalb der Arbeitswurzel. Im Chat erscheint eine Zeile
  „🖥️ Mac mini · …", danach arbeitet Jarvis automatisch weiter (mehrere Schritte).
- Neue Endpunkte `/api/mini/info`, `/api/mini/test` und `/api/mini/run`.

### Hinweise
- Der SSH-Schlüssel wird im Add-on erzeugt (`/data/regis_mini_key`, bleibt beim
  Neubau erhalten); sein öffentlicher Teil steht in `/api/mini/info` und muss am
  mini in `~/.ssh/authorized_keys` liegen.
- Beide Rechner nutzen dieselben Arbeitskopien: Änderungen sind sofort in VS Code
  sichtbar – eine Synchronisation braucht es dafür nicht.

---
## [1.8.1] - 2026-11-03


### Korrigiert
- `openrouter_api_key` fehlte in der Liste der speicherbaren Einstellungen –
  der Schlüssel wurde beim Speichern stillschweigend verworfen (die
  Oberfläche meldete trotzdem Erfolg).
- Leere API-Schlüsselfelder überschreiben beim Speichern der Einstellungen
  nichts mehr: Bisher konnte ein leeres Feld einen hinterlegten Schlüssel
  löschen.

## [1.8.0] - 2026-11-03

### Hinzugefügt
- **OpenRouter als Anbieter.** Neben Ollama und den bisherigen Cloud-Anbietern
  lässt sich jetzt OpenRouter nutzen (eigener Schlüssel). Der Modellkatalog
  (mehrere hundert Modelle) wird live geladen statt fest verdrahtet.
- **Verbrauchsanzeige.** Jede Antwort zeigt Token (gesendet/empfangen) und –
  sofern der Anbieter es liefert – die Kosten in US-Dollar. Im Kopf des Chats
  steht die Summe des Chats, bei OpenRouter zusätzlich das Guthaben des
  Schlüssels. Fehlen Preisdaten, werden die Kosten aus dem OpenRouter-Katalog
  geschätzt und als „geschätzt“ gekennzeichnet.
- **Anbieter- und Modellwechsel direkt im Chat** – unabhängig von der
  Standardeinstellung in den Einstellungen.

### Geändert
- Die Anbieterprüfung im Chat ist generisch: Fehlt der Schlüssel des gewählten
  Anbieters, erscheint eine klare Meldung statt eines stillen Fehlschlags.
- Verbrauch wird je Nachricht im Chat gespeichert.

### Hinweise
- Token liefern alle Anbieter; verlässliche Kosten derzeit nur OpenRouter.
  Lokale Modelle werden mit 0 $ geführt.

---

## [1.7.0] - 2026-10-22

### Geändert
- **Morgen-Briefing: Heimkehr statt Stundenplan.** Das Briefing zählte bisher
  jede einzelne Schulstunde auf. Morgens interessiert aber nicht, welche Stunde
  wann ist, sondern **wann wieder jemand zu Hause ist**. Neue Zeile „Wer wann
  heimkommt" mit dem Schulschluss je Kind, nach Uhrzeit sortiert; die
  Stundenplan-Kalender sind aus dem Briefing raus.
- Wer keinen Unterricht hat, wird genannt statt verschwiegen — der Grund kommt
  aus dem Sensor „aktuelle Stunde" (etwa „Betrieb"), sonst „heute keine Schule".
- Neue Einstellung `briefing_heimweg`: Minuten vom Schultor bis zur Haustür je
  Person, etwa `{"Kind": 25}`. Gesetzt, nennt das Briefing zusätzlich die
  voraussichtliche Ankunft. Leer gelassen, bleibt es beim Schulschluss —
  lieber keine Angabe als eine erfundene.

### Behoben
- **Keine Haushaltsdaten mehr im Quelltext.** Die Standardliste der Kalender
  enthielt Entitäts-IDs mit echten Vor- und Nachnamen und war damit in einem
  öffentlichen Repository nachlesbar. Kalender und Kurz-Labels stehen jetzt
  ausschließlich in den Einstellungen unter `/data`; der Quelltext kennt keine
  Namen mehr. Die Schulschluss-Sensoren werden am Muster erkannt, der Name der
  Person kommt aus dem Attribut `kind`.
- Kalender-Labels kommen aus Home Assistant (Anzeigename), wenn in
  `briefing_calendar_labels` nichts hinterlegt ist — statt aus einer fest
  verdrahteten Tabelle.
- Ohne eigene Kalenderliste nimmt das Briefing alle Kalender, die Home
  Assistant kennt, statt einer leeren Liste.

---

## [1.4.0] - 2026-08-03

### Geändert
- **Morgen-Briefing neu ausgerichtet** — Fokus auf das Wesentliche:
  - **Wetter-Tagesvorhersage** (Bedingung, Min/Max, Regenwahrscheinlichkeit, Wind) statt nur aktuellem Ist-Wert
  - **Heutige Termine** aus den vorhandenen Kalendern (Müllabfuhr, Schule, Geburtstage, Ferien/Feiertage)
  - „Wer ist zuhause" und „welche Lichter an" entfernt
  - Kalender-Liste über Setting `briefing_calendars` anpassbar (Standardliste vorbelegt)

---

## [1.3.1] - 2026-08-03

### Verbessert
- **InfluxDB-Entity-Erkennung** für Jarvis — statt nur bei exakt genanntem Anzeigenamen greift jetzt ein Wort-basiertes Matching (Raum-/Gerätewörter, Komposita wie „Temperaturverlauf" → „temperatur"). Natürliche Fragen wie „Temperaturverlauf gestern in Ottobrunn" finden nun die passende Entity.

---

## [1.3.0] - 2026-07-27

### Neu
- **InfluxDB-Kontext für Jarvis** — der KI-Assistent kann historische Werte aus einer InfluxDB 1.x abfragen
  - Bei Verlaufs-Fragen (z.B. „Wie war der Temperaturverlauf gestern?") werden erwähnte Entities erkannt und echte Zeitreihen (aktuell/Ø/min/max) als Kontext an die KI gehängt — analog zum HA-Log
  - Zeitfenster wird grob aus der Frage abgeleitet (Stunden / Tag / Woche)
  - Neue Einstellungen unter ⚙ → „InfluxDB — Verlaufsdaten" (Host, Port, DB, User/Passwort, SSL) mit „Verbindung testen"
  - Neue Endpunkte: `POST /api/jarvis/influx/test`, `GET /api/jarvis/influx/history`
  - Nutzt die vorhandene `requests`-Abhängigkeit (kein zusätzliches Paket)

---

## [1.2.1] - 2026-07-27

### Behoben
- **Rollos schaltbar** — Geräte-Kacheln nutzen jetzt den `<domain>.toggle`-Service statt des für `cover` nicht existierenden `turn_on`; offene Rollos werden korrekt als „an" dargestellt
- **Schnellchat auf der Übersicht** — Antworten blieben leer, weil ein falsches Streaming-Format geparst wurde; jetzt identisch zum Jarvis-Panel
- **Diagnose** — blockierende Browser-Alerts durch einen dezenten Inline-Fehler-Toast ersetzt; Rückfrage vor dem Löschen von KI-Vorschlägen
- **Jarvis** — Stop-Button bricht laufende Antworten jetzt wirklich ab (AbortController); Rückfrage vor dem Löschen von Chats
- Zonen-Pluralisierung („1 Person" statt „1 Personen")

### Geändert
- Jarvis-Chat: intelligentes Auto-Scrollen (springt nur ans Ende, wenn man unten ist) mit „Nach-unten"-Button; Tipp-Indikator während die KI antwortet

### Entfernt
- Ungenutzte Legacy-Panels (`AutomationsPanel`, `EntitiesPanel`, `AreasPanel`, `SettingsPanel`, altes `JarvisPanel`)

---

## [1.2.0] - 2026-06-10

### Neu
- **Multi-Provider KI** — Unterstützung für 5 KI-Anbieter
  - Ollama (lokal)
  - Anthropic (Claude Haiku, Claude Sonnet)
  - OpenAI (GPT-4o mini, GPT-4o, GPT-4 Turbo)
  - Google (Gemini 1.5 Flash, Gemini 1.5 Pro, Gemini 2.0 Flash)
  - Mistral (Small, Medium, Large)
  - Groq (Llama 3.1, Llama 3.3, Mixtral)
- **Cloud KI Einstellungen** — Dropdown zur Anbieter-Auswahl, API-Key pro Anbieter
  - Primäre KI: Cloud-Anbieter statt Ollama
  - Fallback: Bei Ollama-Ausfall automatisch Cloud-KI nutzen
- **Provider-Badge** im Jarvis-Chat — zeigt ☁️ Cloud oder 🏠 Lokal
- **Zentrale KI-Abstraktion** (`ki_providers.py`) — alle Module nutzen einheitlich den konfigurierten Provider

### Geändert
- Morgen-Briefing, Automations-Vorschläge und Diagnose-Zusammenfassung nutzen jetzt ebenfalls den konfigurierten Provider
- "Als primäre KI nutzen" deaktiviert automatisch den Fallback-Toggle

---

## [1.1.2] - 2026-06-10

### Geändert
- GitHub URL in config.yaml eingetragen (Infoseite verlinkt jetzt korrekt auf GitHub)
- README und CHANGELOG hinzugefügt

---

## [1.1.1] - 2026-06-10

### Behoben
- Wetter-Widget verschwindet wenn Label-Filter aktiv ist — `weather.*` und `person.*` Entitäten werden jetzt immer angezeigt, unabhängig vom Label-Filter
- Labels verschwinden nach dem Speichern der Einstellungen — Label-Cache bleibt jetzt beim Reload erhalten
- Einstellungen wurden nach dem Speichern nicht korrekt wiederhergestellt (Toggle-Zustände)
- Briefing-Targets-Checkboxen konnten nicht geklickt werden (display:none Bug)

---

## [1.1.0] - 2026-06-09

### Neu
- **Morgen-Briefing** — Tägliche KI-Zusammenfassung per Push-Benachrichtigung
  - Konfigurierbare Uhrzeit und Empfänger in den Einstellungen
  - Persistente Benachrichtigung in HA (Glockensymbol)
  - Test-Button zum sofortigen Versenden
  - Aktivieren/Deaktivieren per Toggle
- **Automations-Vorschläge** — KI analysiert Nutzungsmuster und schlägt Automationen vor
  - Tägliche Analyse zur konfigurierbaren Uhrzeit
  - Vergleich mit vorhandenen Automationen (keine Duplikate)
  - Vorschau der generierten Automation vor dem Erstellen
  - Direkte Erstellung in HA mit Link zur HA-Automations-UI
  - Bearbeiten, Annehmen, Ablehnen und Löschen von Vorschlägen
  - Hinweis wenn Entitäten bereits in Automationen verwendet werden
- **Anthropic Cloud KI** — Claude API als Alternative oder Fallback zu Ollama
  - API-Key in den Einstellungen konfigurierbar
  - Automatischer Fallback bei Ollama-Ausfall
- **Automations-Vorschläge Einstellungen** — Analyse-Zeitplan konfigurierbar

### Verbessert
- Einstellungen in separate Karten aufgeteilt (übersichtlicher)
- Reihenfolge der Einstellungskarten optimiert
- Label-Filter schließt nun `weather.*`, `person.*` und `input_*` Entitäten grundsätzlich aus

---

## [1.0.46] - 2026-06-08

### Neu
- **Übersicht-Dashboard** — Neue Startseite mit Status-Kacheln
  - Begrüßung mit Personenname aus HA
  - Klickbare Kacheln: Personen zuhause, Offline-Geräte, Lichter an, Automationen aktiv
  - Schnellzugriff auf Lichter und Schalter
  - Letzte Diagnose-Zusammenfassung
  - Jarvis Schnellchat
- **Diagnose-Panel** komplett überarbeitet
  - Sub-Tabs: Status, Aufräumen, Aktivitäten, Vorschläge
  - Auto-Analyse alle 15 Minuten mit 24h Verlauf
  - Aufräumen: Problematische Integrationen mit KI-Einschätzung
  - Aktivitäten-Log mit Undo und Gelesen-Markierung
- **Label-Filter** — Entitäten mit bestimmten Labels ausblenden
- **entity-row display:flex Fix** in der Geräte-Ansicht

### Geändert
- Diagnose-Tab umbenannt zu "Diagnose" mit Stethoskop-Icon

---

## [1.0.0] - 2026-04-01

### Neu
- Initiale Version
- Geräte-Ansicht mit Bereichen und Stockwerken
- Jarvis KI-Assistent (Ollama)
- Sprachassistent-Verwaltung
- Grundlegende Einstellungen
