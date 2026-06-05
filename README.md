# Regis-Lab

**Your Smart Home Command Center**

A modular Home Assistant Dashboard Add-on — built for power users who want full control over their smart home.

## Features

- 🏠 **Areas** — Floors → Rooms → Devices → Entities (hierarchical view)
- ⚙️ **Automation** — Automations, Scripts, Scenes
- 🔧 **Helpers** — Input helpers, Timers, Counters
- 👥 **Persons** — People, Device Trackers, Zones  
- 📋 **All Entities** — Flat searchable list
- ⚙ **Settings** — Configure token, theme and title

## Installation

1. Add this repository to Home Assistant
2. Install **Regis-Lab** from Local Add-ons
3. Start the add-on
4. Open the UI via the Sidebar

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `title` | Regis-Lab | Dashboard title |
| `theme` | dark | `dark`, `light`, or `auto` |
| `ha_token` | — | Long-Lived Access Token (optional, for custom icon) |

## Custom Icon Setup (optional)

To show the Regis-Lab icon in the HA sidebar:
1. Create a Long-Lived Access Token in HA → Profile → Security
2. Enter it in the Regis-Lab Settings panel
3. Click Save — the icon will be registered automatically

## Architecture

```
regis-lab/
├── config.yaml          # HA Add-on Manifest
├── Dockerfile
├── backend/
│   ├── app.py           # Flask Server
│   ├── core/            # Config, HA Client, Module Loader
│   └── modules/         # areas, automations, entities, settings
└── frontend/
    ├── src/
    │   ├── panels/      # AreasPanel, AutomationsPanel, SettingsPanel
    │   ├── components/  # EntityTile, MdiIcon, RegisLabLogo
    │   └── utils/       # haIcons.js
    └── public/
        └── regis-icon.js  # Custom sidebar icon
```

## License

MIT © Sven Melchior
