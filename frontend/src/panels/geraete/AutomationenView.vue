<template>
  <div class="automationen-view">
    <div v-if="loading" class="state-msg">Lade…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>
    <div v-else class="groups-list">
      <div v-for="group in groups" :key="group.domain" class="group-block">
        <div class="group-header" @click="toggle(group.domain)">
          <MdiIcon :icon="DOMAIN_ICONS[group.domain] || 'mdi:robot'" :size="18" color="var(--accent)" />
          <span class="group-name">{{ group.label }}</span>
          <span class="badge">{{ group.entities.length }}</span>
          <span class="chevron" :class="{ open: expanded.has(group.domain) }">›</span>
        </div>
        <div v-if="expanded.has(group.domain)" class="group-body">
          <EntityTile v-for="e in group.entities" :key="e.entity_id"
            :entity="liveEntity(e)" @toggle="onToggle" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'
import EntityTile from '../../components/EntityTile.vue'
import { useDashboardStore } from '../../store/dashboard.js'

const { state, callService } = useDashboardStore()
const loading  = ref(true)
const error    = ref(null)
const groups   = ref([])
const expanded = ref(new Set())

const DOMAIN_ICONS = {
  automation: 'mdi:robot', script: 'mdi:script-text', scene: 'mdi:palette',
}

async function load() {
  loading.value = true
  try {
    const r = await fetch('api/automations')
    const d = await r.json()
    const AUTO_DOMAINS = new Set(['automation', 'script', 'scene'])
    groups.value = (d.groups || []).filter(g => AUTO_DOMAINS.has(g.domain))
    groups.value.forEach(g => expanded.value.add(g.domain))
  } catch(e) { error.value = e.message }
  finally { loading.value = false }
}

function liveEntity(e) { return state.entities[e.entity_id] || e }
function toggle(key) {
  const s = new Set(expanded.value)
  s.has(key) ? s.delete(key) : s.add(key)
  expanded.value = s
}
function onToggle(entity) {
  const domain = entity.entity_id.split('.')[0]
  callService(domain, entity.state === 'on' ? 'turn_off' : 'turn_on', { entity_id: entity.entity_id })
}
onMounted(load)
</script>

<style scoped>
.groups-list { display: flex; flex-direction: column; gap: 8px; }
.group-block { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.group-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; cursor: pointer; transition: background .15s; }
.group-header:hover { background: color-mix(in srgb, var(--accent) 6%, var(--surface)); }
.group-name { font-size: 14px; font-weight: 600; flex: 1; }
.badge { font-size: 11px; padding: 2px 7px; border-radius: 10px; background: var(--border); color: var(--muted); }
.chevron { font-size: 18px; color: var(--muted); transition: transform .2s; }
.chevron.open { transform: rotate(90deg); }
.group-body { display: flex; flex-direction: column; padding: 4px 4px 8px 28px; }
.state-msg { text-align: center; color: var(--muted); padding: 40px; }
.state-msg.error { color: var(--red); }
</style>
