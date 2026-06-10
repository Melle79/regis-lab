# Changelog

Alle wichtigen Änderungen an Regis-Lab werden hier dokumentiert.

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
