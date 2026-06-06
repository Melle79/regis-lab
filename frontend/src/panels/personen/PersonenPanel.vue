<template>
  <div class="personen-panel">
    <div v-if="loading" class="state-msg">Lade…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>
    <template v-else>

      <!-- Personen-Karten -->
      <div v-if="persons.length" class="section">
        <div class="section-title">
          <MdiIcon icon="mdi:account-group" :size="16" color="var(--accent)" />
          Personen
        </div>
        <div class="persons-grid">
          <div v-for="p in persons" :key="p.entity_id"
            class="person-card" @click="showMoreInfo(p.entity_id)">
            <div class="person-avatar">
              <img v-if="liveEntity(p).attributes?.entity_picture"
                :src="haUrl + liveEntity(p).attributes.entity_picture"
                class="avatar-img" @error="$event.target.style.display='none'" />
              <MdiIcon v-else icon="mdi:account-circle" :size="44"
                :color="liveEntity(p).state === 'home' ? 'var(--green)' : 'var(--muted)'" />
            </div>
            <div class="person-name">{{ p.attributes?.friendly_name || p.entity_id.split('.')[1] }}</div>
            <div :class="['person-state', liveEntity(p).state === 'home' ? 'home' : 'away']">
              <MdiIcon :icon="liveEntity(p).state === 'home' ? 'mdi:home' : 'mdi:map-marker'" :size="11" />
              {{ liveEntity(p).state === 'home' ? 'Zuhause' : liveEntity(p).state }}
            </div>
          </div>
        </div>
      </div>

      <!-- Device Tracker -->
      <div v-if="trackers.length" class="section">
        <div class="section-title">
          <MdiIcon icon="mdi:map-marker" :size="16" color="var(--accent)" />
          Geräte-Tracker
          <span class="badge">{{ trackers.length }}</span>
        </div>
        <div class="entity-list">
          <EntityTile v-for="e in trackers" :key="e.entity_id"
            :entity="liveEntity(e)" @toggle="onToggle" />
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'
import EntityTile from '../../components/EntityTile.vue'
import { useDashboardStore } from '../../store/dashboard.js'

const { state, callService } = useDashboardStore()
const loading  = ref(true)
const error    = ref(null)
const persons  = ref([])
const trackers = ref([])

const haUrl = computed(() => window.location.origin.replace(/:\d+/, ':8123'))

async function load() {
  loading.value = true
  try {
    const r = await fetch('api/persons')
    const d = await r.json()
    persons.value  = d.persons  || []
    trackers.value = d.trackers || []
  } catch(e) { error.value = e.message }
  finally { loading.value = false }
}

function liveEntity(e) { return state.entities[e.entity_id] || e }
function onToggle(entity) {
  const domain = entity.entity_id.split('.')[0]
  callService(domain, entity.state === 'on' ? 'turn_off' : 'turn_on', { entity_id: entity.entity_id })
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
.section { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.section-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: var(--text);
}
.badge { font-size: 11px; padding: 1px 6px; border-radius: 8px; background: var(--border); color: var(--muted); }
.persons-grid { display: flex; flex-wrap: wrap; gap: 12px; }
.person-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 14px 18px; border-radius: 12px; border: 1px solid var(--border);
  cursor: pointer; transition: border-color .15s; min-width: 110px;
  background: var(--surface);
}
.person-card:hover { border-color: var(--accent); }
.person-avatar { width: 52px; height: 52px; border-radius: 50%; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.person-name { font-size: 13px; font-weight: 500; text-align: center; }
.person-state { display: flex; align-items: center; gap: 4px; font-size: 11px; }
.home { color: var(--green); }
.away { color: var(--muted); }
.entity-list { display: flex; flex-direction: column; padding: 4px 4px 8px 28px; }
.state-msg { text-align: center; color: var(--muted); padding: 40px; }
.state-msg.error { color: var(--red); }
</style>
