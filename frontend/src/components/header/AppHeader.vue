<template>
  <header class="app-header">
    <!-- Links: Logo -->
    <div class="header-left">
      <RegisLabLogo :size="28" :show-text="true" />
      <span class="header-version">v{{ version }}</span>
    </div>

    <!-- Mitte: Haupt-Navigation mit Drag & Drop -->
    <nav class="header-nav" @dragover.prevent @drop="onDrop">
      <button
        v-for="tab in localTabs"
        :key="tab.id"
        :class="['nav-tab', { active: activeTab === tab.id, dragging: dragId === tab.id }]"
        draggable="true"
        @click="$emit('tab', tab.id)"
        @dragstart="onDragStart(tab.id)"
        @dragover.prevent="onDragOver(tab.id)"
        @dragend="onDragEnd"
      >
        <MdiIcon :icon="tab.icon" :size="15" />
        {{ tab.label }}
      </button>
    </nav>

    <!-- Rechts: Uhr, Wetter, Einstellungen -->
    <div class="header-right">
      <HeaderClock :visible="settings.show_clock" />
      <HeaderWeather :visible="settings.show_weather" :entity-id="settings.weather_entity" />
      <span class="header-live" :class="{ live: isLive }">
        <span class="live-dot" />
        {{ isLive ? 'Live' : 'Offline' }}
      </span>
      <button class="settings-btn" @click="$emit('settings')" title="Einstellungen">
        <MdiIcon icon="mdi:cog" :size="18" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, watch, inject } from 'vue'
import RegisLabLogo from '../RegisLabLogo.vue'
import MdiIcon from '../MdiIcon.vue'
import HeaderClock from './HeaderClock.vue'
import HeaderWeather from './HeaderWeather.vue'

const props = defineProps({
  tabs:      { type: Array,   default: () => [] },
  activeTab: { type: String,  default: '' },
  isLive:    { type: Boolean, default: false },
  settings:  { type: Object,  default: () => ({}) },
})

const emit = defineEmits(['tab', 'settings', 'reorder'])

const version   = inject('appVersion', '?')
const localTabs = ref([...props.tabs])
const dragId    = ref(null)
let   dragOver  = null

watch(() => props.tabs, (t) => {
  if (t && t.length) localTabs.value = [...t]
}, { immediate: true })

function onDragStart(id) { dragId.value = id }
function onDragOver(id)  { dragOver = id }
function onDrop()        {}
function onDragEnd() {
  if (dragId.value && dragOver && dragId.value !== dragOver) {
    const arr  = [...localTabs.value]
    const from = arr.findIndex(t => t.id === dragId.value)
    const to   = arr.findIndex(t => t.id === dragOver)
    arr.splice(to, 0, arr.splice(from, 1)[0])
    localTabs.value = arr
    emit('reorder', arr.map(t => t.id))
  }
  dragId.value = null
  dragOver     = null
}
</script>

<style scoped>
.app-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; height: 52px; flex-shrink: 0;
  background: var(--surface); border-bottom: 1px solid var(--border);
  gap: 12px;
}

.header-left { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.header-version { font-size: 10px; color: var(--muted); }

.header-nav { display: flex; gap: 4px; flex: 1; justify-content: center; }
.nav-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 8px; border: none;
  background: transparent; color: var(--muted); cursor: grab;
  font-size: 13px; font-weight: 500; transition: all .15s;
}
.nav-tab:hover  { color: var(--text); background: var(--border); }
.nav-tab.active { background: var(--accent); color: #fff; cursor: pointer; }
.nav-tab.dragging { opacity: .4; }

.header-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.header-live  { font-size: 11px; color: var(--muted); display: flex; align-items: center; gap: 5px; }
.header-live.live { color: var(--green); }
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.settings-btn {
  padding: 6px; border-radius: 8px; border: none; background: transparent;
  color: var(--muted); cursor: pointer;
}
.settings-btn:hover { color: var(--text); background: var(--border); }
</style>
