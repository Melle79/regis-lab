# Regis-Lab

**Your Smart Home Command Center** — ein modulares Home Assistant Dashboard Addon.

> ⚠️ **Nutzung auf eigene Gefahr**  
> Dieses Addon befindet sich in aktiver Entwicklung. Die Nutzung erfolgt auf eigene Gefahr.  
> Insbesondere wenn der lokale KI-Assistent Zugriff auf Home Assistant erhält, können unbeabsichtigte Aktionen ausgeführt werden. Aktiviere die HA-Steuerung für den KI-Assistenten nur wenn du dir der Risiken bewusst bist.

---

## Features

- 🏠 **Geräte** — Stockwerke → Bereiche → Geräte → Entities (hierarchische Ansicht)
- ⚙️ **Automationen** — Automationen, Skripte, Szenen
- 🔧 **Helfer** — Input-Helfer, Timer, Counter und mehr
- 👥 **Personen** — Personen-Tracker und Zonen
- 🤖 **Lokaler KI-Assistent** — Chat mit lokalem Ollama-Modell, optional mit HA-Steuerung
- ⚙ **Einstellungen** — Alles konfigurierbar direkt im Dashboard

## Installation

1. Repository in Home Assistant hinzufügen:  
   **Einstellungen → Add-ons → Add-on Store → ⋮ → Repositories**  
   URL: `https://github.com/Melle79/regis-lab`

2. **Regis-Lab** installieren

3. App starten und über die Seitenleiste öffnen

4. Einstellungen über das ⚙-Symbol im Dashboard vornehmen

## Konfiguration

Alle Einstellungen werden direkt im Dashboard vorgenommen — kein Zugriff auf die HA-Konfigurationsdateien nötig.

### Home Assistant Token (optional)
Ein Long-Lived Access Token ermöglicht erweiterte Funktionen. Erstellen unter:  
**HA → Profil → Sicherheit → Langlebige Zugriffstoken**

### Lokaler KI-Assistent
- Ollama URL und Modell konfigurierbar
- Name des Assistenten frei wählbar in den Einstellungen
- **HA-Steuerung**: standardmäßig deaktiviert — aktiviere sie nur bewusst, da der KI-Assistent dann Geräte steuern kann

## Sicherheitshinweise

- Die KI-Steuerung von HA-Geräten ist experimentell
- Fehlerhafte KI-Antworten können unbeabsichtigte Schaltaktionen auslösen
- Der HA-Token wird im Addon gespeichert
- Nutzung ausschließlich auf eigene Gefahr

## Lizenz

Privates Projekt — keine Gewährleistung, keine Haftung, kein Support.
