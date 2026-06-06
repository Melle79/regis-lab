<template>
  <header class="app-header">
    <!-- Links: Logo -->
    <div class="header-left">
      <RegisLabLogo :size="28" :show-text="true" />
      <span class="header-version">v{{ version }}</span>
    </div>

    <!-- Mitte: Haupt-Navigation -->
    <nav class="header-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['nav-tab', { active: activeTab === tab.id }]"
        @click="$emit('tab', tab.id)"
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
import RegisLabLogo from '../RegisLabLogo.vue'
import MdiIcon from '../MdiIcon.vue'
import HeaderClock from './HeaderClock.vue'
import HeaderWeather from './HeaderWeather.vue'

defineProps({
  tabs:      { type: Array,  default: () => [] },
  activeTab: { type: String, default: '' },
  version:   { type: String, default: '' },
  isLive:    { type: Boolean, default: false },
  settings:  { type: Object, default: () => ({}) },
})

defineEmits(['tab', 'settings'])
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
  background: transparent; color: var(--muted); cursor: pointer;
  font-size: 13px; font-weight: 500; transition: all .15s;
}
.nav-tab:hover { color: var(--text); background: var(--border); }
.nav-tab.active { background: var(--accent); color: #fff; }

.header-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }

.header-live {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: var(--muted);
}
.live-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--muted);
}
.header-live.live .live-dot { background: var(--green); }
.header-live.live { color: var(--green); }

.settings-btn {
  padding: 6px; border-radius: 8px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer; transition: all .15s;
}
.settings-btn:hover { color: var(--text); border-color: var(--accent); }
</style>
