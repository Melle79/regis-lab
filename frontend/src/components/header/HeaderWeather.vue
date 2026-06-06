<template>
  <div class="header-weather" v-if="visible && entity">
    <MdiIcon :icon="weatherIcon" :size="16" color="var(--accent)" />
    <span>{{ temperature }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MdiIcon from '../MdiIcon.vue'
import { useDashboardStore } from '../../store/dashboard.js'

const props = defineProps({
  visible:  { type: Boolean, default: true },
  entityId: { type: String, default: '' },
})

const { state } = useDashboardStore()

const entity = computed(() => {
  if (!props.entityId) return null
  return state.entities[props.entityId] || null
})

const WEATHER_ICONS = {
  'sunny':         'mdi:weather-sunny',
  'clear-night':   'mdi:weather-night',
  'partlycloudy':  'mdi:weather-partly-cloudy',
  'cloudy':        'mdi:weather-cloudy',
  'rainy':         'mdi:weather-rainy',
  'pouring':       'mdi:weather-pouring',
  'snowy':         'mdi:weather-snowy',
  'fog':           'mdi:weather-fog',
  'windy':         'mdi:weather-windy',
  'lightning':     'mdi:weather-lightning',
}

const weatherIcon = computed(() => {
  if (!entity.value) return 'mdi:weather-partly-cloudy'
  return WEATHER_ICONS[entity.value.state] || 'mdi:weather-partly-cloudy'
})

const temperature = computed(() => {
  if (!entity.value) return ''
  const temp = entity.value.attributes?.temperature
  const unit = entity.value.attributes?.temperature_unit || '°C'
  return temp ? `${Math.round(temp)}${unit}` : entity.value.state
})
</script>

<style scoped>
.header-weather {
  display: flex; align-items: center; gap: 5px;
  font-size: 13px; color: var(--muted); cursor: default;
}
</style>
