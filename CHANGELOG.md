# Changelog

Alle wichtigen Änderungen an Regis-Lab werden hier dokumentiert.

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
