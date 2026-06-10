# Regis-Lab

**Dein Smart Home Kommandozentrum** — ein modulares Home Assistant Dashboard-Addon.

> ⚠️ **Nutzung auf eigene Gefahr**  
> Dieses Addon befindet sich in aktiver Entwicklung und wird ohne Gewährleistung bereitgestellt.  
> Wenn der KI-Assistent Zugriff auf Home Assistant erhält, können unbeabsichtigte Aktionen ausgeführt werden. Aktiviere die HA-Steuerung nur, wenn du dir der damit verbundenen Risiken bewusst bist.

---

## Version 1.1.0 — Änderungen

- Morgen-Briefing mit KI-Zusammenfassung und Push-Benachrichtigung
- Automations-Vorschläge mit Muster-Erkennung und direkter HA-Erstellung
- Anthropic Cloud KI als optionaler Fallback
- Diagnose-Panel mit Auto-Analyse, Aufräumen, Aktivitäten-Log

---

## Funktionen

### 🏠 Übersicht-Dashboard
- Begrüßung mit Personenname aus HA
- Klickbare Status-Kacheln: Personen zuhause, Offline-Geräte, Lichter an, Automationen aktiv
- Schnellzugriff auf Lichter und Schalter
- Letzte Diagnose-Zusammenfassung
- Jarvis Schnellchat

### 🔍 Geräte
- Hierarchische Ansicht: Stockwerke → Bereiche → Geräte → Entitäten
- Brand-Icons und Integrations-Badges
- Alle Entitäten direkt ein- und ausklappbar
- Geräte manuell Bereichen zuordnen

### 🎙️ Sprachassistent-Verwaltung
- Mikrofon-Symbol bei jeder Entität — ein Klick macht sie für den HA-Sprachassistenten verfügbar
- Verfügbarkeits-Zähler im Zimmer-Header
- KI-Vorschläge direkt aus dem Zimmer-Header

### 🤖 KI-Assistent
- Chat mit lokalem Ollama-Modell (empfohlen: `qwen2.5:14b-instruct`)
- Mehrere persistente Chats mit automatisch generiertem Titel
- Optional: Anthropic Claude API als Cloud-KI oder Fallback
- HA-Steuerung: Jarvis kann Geräte direkt steuern

### 🩺 Diagnose
- **Status**: 4 klickbare Kacheln, KI-Zusammenfassung, Trend-Chart
- **Aufräumen**: Problematische Integrationen mit KI-Einschätzung
- **Aktivitäten**: Log mit Undo und Gelesen-Markierung
- **Vorschläge**: Muster-Erkennung aus HA-Verlauf, Automations-Vorschau, direkte HA-Erstellung

### ☀️ Morgen-Briefing
- Täglich automatische KI-Zusammenfassung per Push-Benachrichtigung
- Persistente Benachrichtigung in HA
- Konfigurierbare Uhrzeit und Empfänger
- Test-Button in den Einstellungen

---

## Voraussetzungen

| Voraussetzung | Pflicht | Beschreibung |
|---|---|---|
| Home Assistant | ✅ | Core 2024.1 oder neuer |
| HA Long-Lived Access Token | ✅ | Für API-Zugriff |
| Ollama | ⚡ Optional | Lokale KI (empfohlen: `qwen2.5:14b-instruct`) |
| Anthropic API-Key | ⚡ Optional | Cloud-KI als Alternative oder Fallback |

> **Ollama oder Anthropic** — mindestens einer wird für KI-Funktionen (Briefing, Vorschläge, Jarvis) benötigt. Ohne KI sind Geräte-Ansicht und Diagnose-Kacheln weiterhin verfügbar.

---

## Installation

[![Add to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FMelle79%2Fregis-lab)

1. Klicke auf den Button oben oder füge dieses Repository manuell in Home Assistant hinzu:  
   `https://github.com/Melle79/regis-lab`
2. Installiere das Addon **Regis-Lab**
3. Starte das Addon
4. Öffne die Web-UI über **Ingress**
5. Gehe zu **Einstellungen** und trage deinen HA Long-Lived Access Token ein

---

## Einstellungen

### Allgemein
- **Dashboard-Titel** — Name der App
- **Wetter-Entity** — Entity-ID für das Wetter-Widget (z.B. `weather.forecast_home`)
- **Wetter anzeigen** — Wetter im Header ein/aus

### HA Token
- **Long-Lived Access Token** — unter HA → Profil → Sicherheit erstellen

### Label-Filter
- Entitäten mit bestimmten Labels im Dashboard ausblenden
- Empfehlung: Label `no_dboard` für Helfer und interne Entitäten verwenden

### Morgen-Briefing
- **Aktiviert** — Briefing ein/aus
- **Uhrzeit** — Wann das Briefing gesendet wird
- **Empfänger** — Welche Geräte die Push-Benachrichtigung erhalten

### Automations-Vorschläge
- **Aktiviert** — Tägliche Muster-Analyse ein/aus
- **Analyse-Uhrzeit** — Wann die Analyse läuft (Standard: 08:00)

### Lokaler KI-Assistent (Ollama)
- **Ollama URL** — z.B. `http://192.168.0.220:11434`
- **Modell** — Empfohlen: `qwen2.5:14b-instruct`

### Cloud KI (Anthropic)
- **API-Key** — Anthropic API-Key (`sk-ant-...`)
- **Als Fallback nutzen** — Bei Ollama-Ausfall automatisch Claude API verwenden

---

## Technischer Hintergrund

| Komponente | Technologie |
|---|---|
| Frontend | Vue 3 + Vite |
| Backend | Python Flask + flask-sock |
| Kommunikation | HA WebSocket + REST API |
| KI | Ollama (lokal) und/oder Anthropic API |

---

## Bekannte Einschränkungen

- InfluxDB-Integration derzeit nicht unterstützt (HA 2026.6 Bug)
- Supervisor-Auto-Update nicht verfügbar (manueller Image-Build nötig)
- Sehr große HA-Instanzen (>5000 Entitäten) können die Performance beeinflussen

---

## Lizenz

MIT License — Nutzung auf eigene Gefahr.
