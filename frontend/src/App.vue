<template>
  <div class="dashboard" :data-theme="store.state.config.theme || 'dark'">

    <header class="dash-header">
      <div class="header-left">
        <RegisLabLogo :size="32" :show-text="true" />
        <span class="dash-version">v{{ addonVersion }}</span>
      </div>
      <div class="header-right">
        <span
          v-for="m in store.state.modules"
          :key="m.name"
          class="module-badge"
          :title="`Modul: ${m.name}`"
        >{{ m.name }}</span>
        <span class="dash-status" :class="{ connected: store.state.connected }">
          {{ store.state.connected ? '● Live' : '○ Verbinde…' }}
        </span>
      </div>
    </header>

    <nav class="dash-nav">
      <button
        v-for="panel in availablePanels"
        :key="panel.id"
        :class="['nav-btn', { active: activePanel === panel.id }]"
        @click="activePanel = panel.id"
      >{{ panel.label }}</button>
    </nav>

    <main class="dash-main">
      <component :is="currentPanelComponent" v-if="currentPanelComponent"/>
      <div v-else class="empty-state">Kein Modul aktiv.</div>
    </main>

    <!-- Footer mit Versions-Info -->
    <footer class="dash-footer">
      <span>Regis-Lab v{{ addonVersion }}</span>
      <span class="sep">·</span>
      <span>Module: {{ store.state.modules.map(m => `${m.name}`).join(', ') }}</span>
      <span class="sep">·</span>
      <span :class="store.state.connected ? 'ok' : 'err'">
        {{ store.state.connected ? 'Verbunden' : 'Getrennt' }}
      </span>
    </footer>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDashboardStore } from './store/dashboard.js'
import AreasPanel        from './panels/AreasPanel.vue'
import { registerRegisIcon } from './utils/registerIcon.js'
import RegisLabLogo      from './components/RegisLabLogo.vue'
import EntitiesPanel     from './panels/EntitiesPanel.vue'
import AutomationsPanel  from './panels/AutomationsPanel.vue'
import SettingsPanel     from './panels/SettingsPanel.vue'
import JarvisPanel      from './panels/JarvisPanel.vue'

const store = useDashboardStore()

const addonVersion = computed(() => store.state.health?.version || '–')

const PANEL_REGISTRY = {
  areas:       { id: 'areas',       label: '🏠 Bereiche',           component: AreasPanel },
  automations: { id: 'automations', label: '⚙️ Steuerung',           component: AutomationsPanel },
  entities:    { id: 'entities',    label: '📋 Alle Entities',       component: EntitiesPanel },
  jarvis:      { id: 'jarvis',      label: '🤖 Jarvis',              component: JarvisPanel },
  settings:    { id: 'settings',    label: '⚙ Einstellungen',        component: SettingsPanel },
}

const availablePanels    = computed(() => Object.values(PANEL_REGISTRY))
const activePanel        = ref('areas')
const currentPanelComponent = computed(() => PANEL_REGISTRY[activePanel.value]?.component ?? null)
</script>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:      #111827;
  --surface: #1f2937;
  --border:  #374151;
  --text:    #f9fafb;
  --muted:   #9ca3af;
  --accent:  #3b82f6;
  --green:   #10b981;
  --red:     #ef4444;
  --amber:   #f59e0b;
}
[data-theme="light"] {
  --bg: #f3f4f6; --surface: #ffffff; --border: #e5e7eb;
  --text: #111827; --muted: #6b7280;
}

body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; }
.dashboard { display: flex; flex-direction: column; min-height: 100vh; }

/* Header */
.dash-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px; background: var(--surface); border-bottom: 1px solid var(--border);
  gap: 12px;
}
.header-left  { display: flex; align-items: center; gap: 8px; }
.header-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.dash-title   { font-size: 15px; font-weight: 600; }
.dash-version { font-size: 11px; color: var(--muted); background: var(--border); padding: 2px 6px; border-radius: 6px; }
.module-badge { font-size: 10px; color: var(--accent); background: color-mix(in srgb, var(--accent) 15%, var(--surface)); padding: 2px 7px; border-radius: 6px; border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent); }
.dash-status  { font-size: 12px; color: var(--red); white-space: nowrap; }
.dash-status.connected { color: var(--green); }

/* Nav */
.dash-nav {
  display: flex; gap: 4px; padding: 8px 16px;
  background: var(--surface); border-bottom: 1px solid var(--border);
}
.nav-btn {
  padding: 6px 14px; border-radius: 6px; border: none;
  background: transparent; color: var(--muted); cursor: pointer; font-size: 13px; transition: all .15s;
}
.nav-btn:hover  { background: var(--border); color: var(--text); }
.nav-btn.active { background: var(--accent); color: #fff; }

/* Main */
.dash-main   { flex: 1; padding: 20px; }
.empty-state { text-align: center; color: var(--muted); margin-top: 60px; }

/* Footer */
.dash-footer {
  display: flex; align-items: center; gap: 8px; justify-content: center;
  padding: 8px 20px; font-size: 11px; color: var(--muted);
  background: var(--surface); border-top: 1px solid var(--border);
}
.sep { opacity: .4; }
.ok  { color: var(--green); }
.err { color: var(--red); }
</style>
