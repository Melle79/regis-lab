<template>
  <div class="zonen-panel">
    <div v-if="loading" class="state-msg">Lade…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>
    <div v-else class="zonen-list">
      <div v-for="zone in zones" :key="zone.entity_id"
        class="zone-card" @click="showMoreInfo(zone.entity_id)">
        <div class="zone-icon">
          <MdiIcon :icon="zone.attributes?.icon || 'mdi:map-marker-radius'" :size="24" color="var(--accent)" />
        </div>
        <div class="zone-info">
          <div class="zone-name">{{ zone.attributes?.friendly_name || zone.entity_id.split('.')[1] }}</div>
          <div class="zone-details">
            <span v-if="zone.attributes?.radius">Radius: {{ zone.attributes.radius }}m</span>
            <span>{{ zone.state }} Personen</span>
          </div>
        </div>
        <div class="zone-state" :class="parseInt(zone.state) > 0 ? 'occupied' : 'empty'">
          {{ zone.state }}
        </div>
      </div>
      <div v-if="zones.length === 0" class="state-msg">Keine Zonen gefunden</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'
import { useDashboardStore } from '../../store/dashboard.js'

const { state } = useDashboardStore()
const loading = ref(true)
const error   = ref(null)
const zones   = ref([])

async function load() {
  loading.value = true
  try {
    const r = await fetch('api/persons')
    const d = await r.json()
    zones.value = d.zones || []
  } catch(e) { error.value = e.message }
  finally { loading.value = false }
}

function showMoreInfo(entityId) {
  try {
    window.parent.document.querySelector('home-assistant')
      .dispatchEvent(new CustomEvent('hass-more-info', {
        bubbles: true, composed: true, detail: { entityId }
      }))
  } catch(e) {}
}

onMounted(load)
</script>

<style scoped>
.zonen-list { display: flex; flex-direction: column; gap: 8px; }
.zone-card {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 16px; border-radius: 12px; border: 1px solid var(--border);
  background: var(--surface); cursor: pointer; transition: border-color .15s;
}
.zone-card:hover { border-color: var(--accent); }
.zone-icon { width: 40px; height: 40px; border-radius: 10px; background: color-mix(in srgb, var(--accent) 10%, var(--surface)); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.zone-info { flex: 1; }
.zone-name { font-size: 14px; font-weight: 600; }
.zone-details { font-size: 12px; color: var(--muted); display: flex; gap: 10px; margin-top: 2px; }
.zone-state { font-size: 20px; font-weight: 700; min-width: 30px; text-align: center; }
.occupied { color: var(--green); }
.empty { color: var(--muted); }
.state-msg { text-align: center; color: var(--muted); padding: 40px; }
.state-msg.error { color: var(--red); }
</style>
