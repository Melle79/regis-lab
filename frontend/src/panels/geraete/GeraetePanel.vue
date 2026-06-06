<template>
  <div class="geraete-panel">
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

    <div class="sub-content">
      <BereicheView     v-if="activeSubTab === 'bereiche'" />
      <AutomationenView v-else-if="activeSubTab === 'automationen'" />
      <HelferView       v-else-if="activeSubTab === 'helfer'" />
      <AlleEntitiesView v-else-if="activeSubTab === 'entities'" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'
import BereicheView     from './BereicheView.vue'
import AutomationenView from './AutomationenView.vue'
import HelferView       from './HelferView.vue'
import AlleEntitiesView from './AlleEntitiesView.vue'

const activeSubTab = ref('bereiche')

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
</style>
