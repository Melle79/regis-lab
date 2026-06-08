# Regis-Lab

**Dein Smart Home Kommandozentrum** — ein modulares Home Assistant Dashboard-Addon.

> ⚠️ **Nutzung auf eigene Gefahr**  
> Dieses Addon befindet sich in aktiver Entwicklung und wird ohne Gewährleistung bereitgestellt.  
> Wenn der KI-Assistent Zugriff auf Home Assistant erhält, können unbeabsichtigte Aktionen ausgeführt werden. Aktiviere die HA-Steuerung nur, wenn du dir der damit verbundenen Risiken bewusst bist.

---

## Funktionen

### 🏠 Geräte
- Hierarchische Ansicht: Stockwerke → Bereiche → Geräte → Entitäten
- Brand-Icons und Integrations-Badges
- Alle Entitäten direkt ein- und ausklappbar
- Geräte manuell Bereichen zuordnen

### 🎙️ Sprachassistent-Verwaltung
- **Mikrofon-Symbol** bei jeder Entität — ein Klick macht sie für den HA-Sprachassistenten verfügbar
- **Verfügbarkeits-Zähler** im Zimmer-Header zeigt, wie viele Entitäten aktiviert sind
- **KI-Vorschläge** direkt aus dem Zimmer-Header: Der KI-Assistent analysiert die Geräte und empfiehlt geeignete Entitäten
  - Vorschläge können angepasst, erweitert oder abgewählt werden
  - Nur steuerbare Geräte werden berücksichtigt (Lichter, Schalter, Rollläden, Heizung usw.)

### 🤖 Jarvis KI-Assistent
- Chat mit lokalem Ollama-Modell (empfohlen: `qwen2.5:14b-instruct`)
- Mehrere persistente Chats mit automatisch generiertem Titel
- Chat-Titel per Doppelklick umbenennen
- Chats werden nach letzter Nutzung sortiert
- Code-Blöcke mit Syntax-Hervorhebung, Kopieren und Herunterladen
- Datei-Upload (Textdateien) — der Inhalt wird der KI übergeben
- **HA-Steuerung** — optional: Die KI kann Geräte steuern (Licht, Rollläden, Schalter usw.)
- Modellauswahl aus den verfügbaren Ollama-Modellen
- Zeitstempel und Modellname unter jeder Nachricht

### ⚙️ Automationen, Helfer & Zonen
- Automationen, Skripte und Szenen verwalten
- Eingabe-Helfer, Timer und Zähler
- Personen-Tracker und Zonen-Übersicht

### 🩺 Diagnose
- **Statusbericht** mit automatischer Analyse alle 15 Minuten:
  - Offline- und nicht verfügbare Geräte
  - Geräte mit niedrigem Akkustand
  - Deaktivierte Automationen
  - Log-Fehler
  - KI-gestützte Einschätzung des Systemzustands
- **Verlaufsdiagramm** der letzten 24 Stunden
- **Aufräumen** — problematische Integrationen gruppiert mit:
  - KI-gestützter Einschätzung pro Integration
  - Möglichkeit, Integrationen neu zu laden
  - Entitäten einzeln oder als Gruppe ignorieren
- **Aktivitätenprotokoll** mit Undo-Funktion:
  - Alle Änderungen werden aufgezeichnet
  - Aktionen können rückgängig gemacht werden
  - Neue Einträge werden hervorgehoben
  - Einzeln oder alle als gelesen markieren

### 🎨 Dashboard
- Dunkles und helles Design
- Uhr und Wetter im Header (konfigurierbar)
- Tab-Reihenfolge per Drag & Drop anpassen (wird gespeichert)
- Alle Einstellungen direkt im Dashboard — kein Zugriff auf HA-Konfigurationsdateien erforderlich

---

## Installation

1. Repository in Home Assistant hinzufügen:  
   **Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories**  
   URL: `https://github.com/Melle79/regis-lab`

2. **Regis-Lab** installieren und starten

3. Addon über die Seitenleiste öffnen

4. Einstellungen über das ⚙-Symbol im Dashboard vornehmen

---

## Konfiguration

### Home Assistant Token
Ein langlebiger Zugriffstoken ermöglicht erweiterte Funktionen wie die Sprachassistent-Verwaltung und die HA-Steuerung durch die KI.  
Erstellen unter: **HA → Profil → Sicherheit → Langlebige Zugriffstoken**

### Lokaler KI-Assistent (Ollama)
- Ollama-URL eingeben (z. B. `http://192.168.0.220:11434`)
- Modell auswählen (empfohlen: `qwen2.5:14b-instruct`)
- Name des Assistenten frei wählbar
- **HA-Steuerung**: standardmäßig deaktiviert — nur bewusst aktivieren

### Wetter
Wetter-Entität in den Einstellungen eintragen (z. B. `weather.forecast_home`)

---

## Sicherheitshinweise

- Die KI-Steuerung von HA-Geräten ist experimentell
- Fehlerhafte KI-Antworten können unbeabsichtigte Schaltaktionen auslösen
- Der HA-Token wird lokal im Addon gespeichert
- Nutzung ausschließlich auf eigene Gefahr

---

## Lizenz

Privates Projekt — keine Gewährleistung, keine Haftung, kein offizieller Support.
