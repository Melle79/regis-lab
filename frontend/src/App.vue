<template>
  <div class="app" :data-theme="config.theme || 'dark'">

    <AppHeader
      :tabs="mainTabs"
      @reorder="saveTabOrder"
      :active-tab="activeTab"
      :version="addonVersion"
      :is-live="store.state.connected"
      :settings="headerSettings"
      @tab="activeTab = $event"
      @settings="showSettings = true"
    />

    <main class="app-content">
      <GeraetePanel   v-if="activeTab === 'geraete'" />
      <PersonenPanel  v-else-if="activeTab === 'personen'" />
      <ZonenPanel     v-else-if="activeTab === 'zonen'" />
      <JarvisPanel    v-else-if="activeTab === 'jarvis'" />
    </main>

    <!-- Settings Modal -->
    <SettingsModal v-if="showSettings" @close="showSettings = false; reloadConfig()" />

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDashboardStore } from './store/dashboard.js'
import { registerRegisIcon } from './utils/registerIcon.js'

import AppHeader    from './components/header/AppHeader.vue'
import GeraetePanel from './panels/geraete/GeraetePanel.vue'
import PersonenPanel from './panels/personen/PersonenPanel.vue'
import ZonenPanel   from './panels/zonen/ZonenPanel.vue'
import JarvisPanel  from './panels/jarvis/JarvisPanel.vue'
import SettingsModal from './panels/settings/SettingsModal.vue'

const store        = useDashboardStore()
const activeTab    = ref('geraete')
const showSettings = ref(false)
const config       = ref({})
const addonVersion = ref('?')

const ALL_TABS = [
  { id: 'geraete',  label: 'Geräte',  icon: 'mdi:home' },
  { id: 'personen', label: 'Personen', icon: 'mdi:account-group' },
  { id: 'zonen',    label: 'Zonen',   icon: 'mdi:map-marker-radius' },
  { id: 'jarvis',   label: config.value.ki_name || 'Jarvis', icon: 'mdi:robot' },
]

// Tab-Reihenfolge aus Backend laden
const tabOrder = ref(['geraete', 'personen', 'zonen', 'jarvis'])

async function loadTabOrder() {
  try {
    const r = await fetch('api/settings')
    const d = await r.json()
    if (d.tab_order && Array.isArray(d.tab_order)) {
      tabOrder.value = d.tab_order
    }
  } catch(e) {}
}

async function saveTabOrder(order) {
  tabOrder.value = order
  try {
    await fetch('api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tab_order: order }),
    })
  } catch(e) {}
}

const mainTabs = computed(() => {
  return tabOrder.value
    .map(id => ALL_TABS.find(t => t.id === id))
    .filter(Boolean)
    .map(t => t.id === 'jarvis' ? { ...t, label: config.value.ki_name || 'Jarvis' } : t)
}

])

const headerSettings = computed(() => ({
  show_clock:     config.value.show_clock   !== false,
  show_weather:   config.value.show_weather === true,
  weather_entity: config.value.weather_entity || '',
}))

loadTabOrder()

async function reloadConfig() {
  try {
    const r = await fetch('api/config')
    config.value = await r.json()
  } catch(e) {}
}

async function loadVersion() {
  try {
    const r = await fetch('api/health')
    const d = await r.json()
    addonVersion.value = d.version || '?'
  } catch(e) {}
}

onMounted(async () => {
  store.connect()
  await reloadConfig()
  await loadVersion()
  // Icon registrieren
  try {
    const ingressBase = window.location.pathname.replace(/\/[^\/]*$/, '/')
    await registerRegisIcon(ingressBase)
  } catch(e) {}
})
</script>

<style>
:root {
  --bg:      #0d1117;
  --surface: #161b22;
  --border:  #30363d;
  --text:    #e6edf3;
  --muted:   #7d8590;
  --accent:  #3B82F6;
  --green:   #3fb950;
  --red:     #f85149;
  --amber:   #d29922;
}
[data-theme="light"] {
  --bg:      #f6f8fa;
  --surface: #ffffff;
  --border:  #d0d7de;
  --text:    #1f2328;
  --muted:   #656d76;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; }

.app { display: flex; flex-direction: column; height: 100vh; background: var(--bg); }
.app-content { flex: 1; overflow-y: auto; padding: 16px; }
</style>

<style scoped>
</style>
