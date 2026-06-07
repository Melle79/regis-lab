<template>
  <div class="geraete-panel">
    <VoiceSuggestModal
      v-if="showSuggestModal"
      :ki-name="kiName"
      :model="currentModel"
      :expose-map="exposeMap"
      :initial-area="suggestArea"
      @close="showSuggestModal = false; suggestArea = null"
      @applied="onSuggestApplied"
    />
    <div class="sub-tabs-row">
    <div class="sub-tabs">
      <button
        v-for="tab in subTabs"
        :key="tab.id"
        :class="['sub-tab', { active: activeSubTab === tab.id }]"
        @click="activeSubTab = tab.id"
      >
        <MdiIcon :icon="tab.icon" :size="13" />
        {{ tab.label }}
      </button>
    </div>
    <button class="suggest-btn" @click="showSuggestModal = true" title="KI-Vorschläge für Sprachassistent">
      <MdiIcon icon="mdi:robot" :size="14" />
      KI-Vorschläge
    </button>
    </div>

    <div class="sub-content">
      <BereicheView     v-if="activeSubTab === 'bereiche'" @suggest="onAreaSuggest" />
      <AutomationenView v-else-if="activeSubTab === 'automationen'" />
      <HelferView       v-else-if="activeSubTab === 'helfer'" />
      <AlleEntitiesView v-else-if="activeSubTab === 'entities'" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'
import BereicheView     from './BereicheView.vue'
import AutomationenView from './AutomationenView.vue'
import HelferView       from './HelferView.vue'
import AlleEntitiesView from './AlleEntitiesView.vue'
import VoiceSuggestModal from './VoiceSuggestModal.vue'

const activeSubTab    = ref('bereiche')
const showSuggestModal = ref(false)
const kiName           = ref('KI')
const currentModel     = ref('')
const exposeMap        = ref({})
const suggestArea      = ref(null)

function onAreaSuggest(area) {
  suggestArea.value = {
    name:     area.name,
    icon:     area.icon,
    entities: area.devices?.flatMap(dev => dev.entities || []) || [],
  }
  showSuggestModal.value = true
}

onMounted(async () => {
  try {
    const r = await fetch('api/config')
    const d = await r.json()
    kiName.value       = d.ki_name || 'KI'
    currentModel.value = d.jarvis_model || ''
  } catch(e) {}
  try {
    const r = await fetch('api/voice/expose')
    const d = await r.json()
    const map = {}
    for (const e of (d.entities || [])) map[e.entity_id] = e.exposed
    exposeMap.value = map
  } catch(e) {}
})

function onSuggestApplied(count) {
  // Bereiche neu laden nach Anwenden
}

const subTabs = [
  { id: 'bereiche',     label: 'Bereiche',     icon: 'mdi:home-floor-1' },
  { id: 'automationen', label: 'Automationen', icon: 'mdi:robot' },
  { id: 'helfer',       label: 'Helfer',       icon: 'mdi:wrench' },
  { id: 'entities',     label: 'Alle Entities', icon: 'mdi:format-list-bulleted' },
]
</script>

<style scoped>
.geraete-panel { display: flex; flex-direction: column; gap: 12px; }
.sub-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.sub-tab {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 16px; border: 1px solid var(--border);
  background: var(--surface); color: var(--muted); cursor: pointer;
  font-size: 12px; transition: all .15s;
}
.sub-tab:hover { color: var(--text); border-color: var(--accent); }
.sub-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.sub-content { flex: 1; }
.sub-tabs-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 4px;
}
.suggest-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--surface); color: var(--muted); cursor: pointer; font-size: 11px;
  white-space: nowrap; flex-shrink: 0;
}
.suggest-btn:hover { color: var(--accent); border-color: var(--accent); }
</style>
