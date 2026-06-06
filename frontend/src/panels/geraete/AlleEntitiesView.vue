<template>
  <div class="entities-panel">

    <div class="panel-toolbar">
      <input
        v-model="search"
        class="search-input"
        placeholder="Entity suchen… (z.B. light, sensor.temp)"
      />
      <select v-model="filterDomain" class="domain-select">
        <option value="">Alle Domains</option>
        <option v-for="d in domains" :key="d" :value="d">{{ d }}</option>
      </select>
    </div>

    <div class="entity-grid">
      <EntityCard
        v-for="entity in filteredEntities"
        :key="entity.entity_id"
        :entity="entity"
        @toggle="onToggle"
      />
    </div>

    <p v-if="filteredEntities.length === 0" class="no-results">
      Keine Entities gefunden.
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDashboardStore } from '../store/dashboard.js'
import EntityCard from '../components/EntityTile.vue'

const { entityList, callService } = useDashboardStore()

const search       = ref('')
const filterDomain = ref('')

const domains = computed(() => {
  const set = new Set(entityList.value.map(e => e.entity_id.split('.')[0]))
  return [...set].sort()
})

const filteredEntities = computed(() => {
  let list = entityList.value
  if (filterDomain.value)
    list = list.filter(e => e.entity_id.startsWith(`${filterDomain.value}.`))
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(e =>
      e.entity_id.toLowerCase().includes(q) ||
      (e.attributes?.friendly_name || '').toLowerCase().includes(q)
    )
  }
  return list.sort((a, b) => a.entity_id.localeCompare(b.entity_id))
})

function onToggle(entity) {
  const domain = entity.entity_id.split('.')[0]
  const toggleable = ['light', 'switch', 'input_boolean', 'fan', 'cover']
  if (!toggleable.includes(domain)) return
  const svc = entity.state === 'on' ? 'turn_off' : 'turn_on'
  callService(domain, svc, { entity_id: entity.entity_id })
}
</script>

<style scoped>
.panel-toolbar {
  display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap;
}
.search-input, .domain-select {
  padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text); font-size: 13px; outline: none;
}
.search-input { flex: 1; min-width: 200px; }
.search-input:focus, .domain-select:focus { border-color: var(--accent); }

.entity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.no-results { color: var(--muted); text-align: center; margin-top: 40px; }
</style>
