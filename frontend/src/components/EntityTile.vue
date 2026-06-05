<template>
  <div class="entity-row" @click="showMoreInfo">
    <div class="entity-row-icon">
      <MdiIcon :icon="icon" :size="16" :color="color" />
    </div>
    <div class="entity-row-body">
      <span class="entity-row-name">{{ friendlyName }}</span>
      <span class="entity-row-state" :class="stateClass">{{ displayState }}</span>
    </div>
    <div class="entity-row-action" @click.stop>
      <!-- Toggle für schaltbare Entities -->
      <button
        v-if="isToggleable"
        :class="['toggle-btn', { 'toggle-on': isOn }]"
        @click.stop="doToggle"
      >
        <MdiIcon :icon="isOn ? 'mdi:toggle-switch' : 'mdi:toggle-switch-off-outline'" :size="22" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MdiIcon from './MdiIcon.vue'
import { getEntityIcon, getEntityColor } from '../utils/haIcons.js'
import { useDashboardStore } from '../store/dashboard.js'

const props = defineProps({
  entity:       { type: Object, required: true },
  overrideIcon: { type: String, default: null },
})
const emit = defineEmits(['toggle'])

const { state } = useDashboardStore()
const liveEntity = computed(() => state.entities[props.entity.entity_id] || props.entity)

const TOGGLEABLE   = ['light','switch','input_boolean','fan','cover']
const domain       = computed(() => liveEntity.value.entity_id.split('.')[0])
const isOn         = computed(() => liveEntity.value.state === 'on')
const isToggleable = computed(() => TOGGLEABLE.includes(domain.value))
const friendlyName = computed(() =>
  liveEntity.value.attributes?.friendly_name || liveEntity.value.entity_id.split('.')[1]
)
const icon  = computed(() => getEntityIcon(liveEntity.value, props.overrideIcon))
const color = computed(() => getEntityColor(liveEntity.value))

const displayState = computed(() => {
  const s    = liveEntity.value.state
  const unit = liveEntity.value.attributes?.unit_of_measurement
  if (s === 'unavailable') return 'n/v'
  if (s === 'unknown')     return '?'
  if (unit) {
    const num = parseFloat(s)
    return isNaN(num) ? `${s} ${unit}` : `${num.toFixed(1)} ${unit}`
  }
  return s
})

const stateClass = computed(() => {
  const s = liveEntity.value.state
  return s === 'on' ? 'on' : s === 'off' ? 'off' : s === 'unavailable' ? 'unavail' : 'neutral'
})

function showMoreInfo() {
  try {
    window.parent.document
      .querySelector('home-assistant')
      .dispatchEvent(new CustomEvent('hass-more-info', {
        bubbles: true, composed: true,
        detail: { entityId: liveEntity.value.entity_id }
      }))
  } catch(e) {}
}

function doToggle() {
  emit('toggle', liveEntity.value)
}
</script>

<style scoped>
.entity-row {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 10px; border-radius: 8px; cursor: pointer;
  transition: background .15s; min-height: 42px;
}
.entity-row:hover { background: color-mix(in srgb, var(--accent) 6%, var(--surface)); }

.entity-row-icon {
  display: flex; align-items: center; flex-shrink: 0;
  width: 24px; justify-content: center;
}

.entity-row-body {
  flex: 1; min-width: 0;
  display: flex; align-items: baseline; gap: 8px;
}
.entity-row-name {
  font-size: 12px; font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  flex: 1;
}
.entity-row-state {
  font-size: 11px; white-space: nowrap; flex-shrink: 0;
}

.entity-row-action { flex-shrink: 0; }

.toggle-btn {
  display: flex; align-items: center;
  padding: 2px; border: none; background: transparent;
  cursor: pointer; border-radius: 4px; transition: opacity .15s;
  color: var(--muted);
}
.toggle-btn:hover  { opacity: .8; }
.toggle-btn.toggle-on { color: var(--green); }

.on      { color: var(--green); }
.off     { color: var(--muted); }
.unavail { color: var(--red); }
.neutral { color: var(--text); font-size: 11px; }
</style>
