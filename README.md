# Regis-Lab

**Your Smart Home Command Center** — ein modulares Home Assistant Dashboard Addon.

> ⚠️ **Nutzung auf eigene Gefahr**  
> Dieses Addon befindet sich in aktiver Entwicklung. Die Nutzung erfolgt auf eigene Gefahr.  
> Insbesondere wenn der lokale KI-Assistent Zugriff auf Home Assistant erhält, können unbeabsichtigte Aktionen ausgeführt werden. Aktiviere die HA-Steuerung für den KI-Assistenten nur wenn du dir der Risiken bewusst bist.

---

## Features

### 🏠 Geräte
- Hierarchische Ansicht: Stockwerke → Bereiche → Geräte → Entitäten
- Brand-Icons und Integration-Badges
- Alle Entitäten direkt ein-/ausklappen
- Geräte manuell Bereichen zuordnen

### 🎙️ Sprachassistent-Verwaltung
- **Mikrofon-Icon** bei jeder Entität — ein Klick macht sie für den HA-Sprachassistenten verfügbar
- **Expose-Zähler** im Zimmer-Header zeigt wie viele Entitäten verfügbar sind
- **KI-Vorschläge** — direkt aus dem Zimmer-Header: der lokale KI-Assistent analysiert die Geräte und schlägt sinnvolle Entitäten vor
  - Auswahl anpassbar (hinzufügen / abwählen)
  - Nur steuerbare Geräte werden vorgeschlagen (Lichter, Schalter, Rollos, Heizung...)

### 🤖 Jarvis KI-Assistent
- Chat mit lokalem Ollama-Modell (empfohlen: `qwen2.5:14b-instruct`)
- Mehrere persistente Chats mit automatischem KI-Titel
- Umbenennen per Doppelklick
- Code-Blöcke mit Syntax-Highlighting, Kopieren und Download
- Datei-Upload (Text-Dateien) — Inhalt wird an die KI übergeben
- **HA-Steuerung** — optional: KI kann Geräte steuern (Schalter, Rollläden, Beleuchtung etc.)
- Modell-Auswahl aus verfügbaren Ollama-Modellen
- Timestamp und Modell-Name unter jeder Nachricht

### ⚙️ Automationen, Helfer & Zonen
- Automationen, Skripte, Szenen verwalten
- Input-Helfer, Timer, Counter
- Personen-Tracker und Zonen-Übersicht

### 🎨 Dashboard
- Dark/Light Theme
- Uhr und Wetter im Header (konfigurierbar)
- **Tab-Reihenfolge** per Drag & Drop anpassbar und persistent gespeichert
- Alle Einstellungen direkt im Dashboard — kein Zugriff auf HA-Konfigurationsdateien nötig

---

## Installation

1. Repository in Home Assistant hinzufügen:  
   **Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories**  
   URL: `https://github.com/Melle79/regis-lab`

2. **Regis-Lab** installieren und starten

3. App über die Seitenleiste öffnen

4. Einstellungen über das ⚙-Symbol im Dashboard vornehmen

---

## Konfiguration

### Home Assistant Token
Ein Long-Lived Access Token ermöglicht erweiterte Funktionen (Sprachassistent-Verwaltung, HA-Steuerung).  
Erstellen unter: **HA → Profil → Sicherheit → Langlebige Zugriffstoken**

### Lokaler KI-Assistent (Ollama)
- Ollama URL eingeben (z.B. `http://192.168.0.220:11434`)
- Modell auswählen (empfohlen: `qwen2.5:14b-instruct`)
- Name des Assistenten frei wählbar
- **HA-Steuerung**: standardmäßig deaktiviert — nur bewusst aktivieren

### Wetter
Wetter-Entität in den Einstellungen eintragen (z.B. `weather.forecast_home`)

---

## Sicherheitshinweise

- Die KI-Steuerung von HA-Geräten ist experimentell
- Fehlerhafte KI-Antworten können unbeabsichtigte Schaltaktionen auslösen
- Der HA-Token wird lokal im Addon gespeichert (`/data/regis_settings.json`)
- Nutzung ausschließlich auf eigene Gefahr

---

## Lizenz

Privates Projekt — keine Gewährleistung, keine Haftung, kein Support.
