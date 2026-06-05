<template>
  <div class="automations-panel">

    <div class="section-tabs">
      <button
        v-for="tab in tabs" :key="tab.id"
        :class="['section-tab', { active: activeSection === tab.id }]"
        @click="activeSection = tab.id"
      >
        <MdiIcon :icon="tab.icon" :size="14" />
        {{ tab.label }}
        <span class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <div v-if="loading" class="state-msg">Lade…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>

    <template v-else>

      <!-- Automationen -->
      <div v-if="activeSection === 'automations'" class="groups-list">
        <div v-for="group in autoGroups" :key="group.domain" class="group-block">
          <div class="group-header" @click="toggle(group.domain)">
            <MdiIcon :icon="domainIcon(group.domain)" :size="18" color="var(--accent)" />
            <span class="group-name">{{ group.label }}</span>
            <span class="badge">{{ group.entities.length }}</span>
            <span class="chevron" :class="{ open: expanded.has(group.domain) }">›</span>
          </div>
          <div v-if="expanded.has(group.domain)" class="group-body">
            <EntityTile v-for="e in group.entities" :key="e.entity_id" :entity="liveEntity(e)" @toggle="onToggle" />
          </div>
        </div>
      </div>

      <!-- Helfer -->
      <div v-else-if="activeSection === 'helpers'" class="groups-list">
        <div v-for="group in helperGroups" :key="group.domain" class="group-block">
          <div class="group-header" @click="toggle('h_' + group.domain)">
            <MdiIcon :icon="domainIcon(group.domain)" :size="18" color="var(--accent)" />
            <span class="group-name">{{ group.label }}</span>
            <span class="badge">{{ group.entities.length }}</span>
            <span class="chevron" :class="{ open: expanded.has('h_' + group.domain) }">›</span>
          </div>
          <div v-if="expanded.has('h_' + group.domain)" class="group-body">
            <EntityTile v-for="e in group.entities" :key="e.entity_id" :entity="liveEntity(e)" @toggle="onToggle" />
          </div>
        </div>
      </div>

      <!-- Personen -->
      <div v-else-if="activeSection === 'persons'" class="groups-list">

        <!-- Personen-Karten -->
        <div v-if="persons.length" class="group-block">
          <div class="group-header" @click="toggle('person')">
            <MdiIcon icon="mdi:account-group" :size="18" color="var(--accent)" />
            <span class="group-name">Personen</span>
            <span class="badge">{{ persons.length }}</span>
            <span class="chevron" :class="{ open: expanded.has('person') }">›</span>
          </div>
          <div v-if="expanded.has('person')" class="persons-grid">
            <div v-for="p in persons" :key="p.entity_id" class="person-card" @click="showMoreInfo(p.entity_id)">
              <div class="person-avatar">
                <img v-if="p.attributes?.entity_picture"
                  :src="haUrl + p.attributes.entity_picture"
                  class="avatar-img"
                  @error="$event.target.style.display='none'"
                />
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

        <!-- Tracker -->
        <div v-if="trackers.length" class="group-block">
          <div class="group-header" @click="toggle('device_tracker')">
            <MdiIcon icon="mdi:map-marker" :size="18" color="var(--accent)" />
            <span class="group-name">Geräte-Tracker</span>
            <span class="badge">{{ trackers.length }}</span>
            <span class="chevron" :class="{ open: expanded.has('device_tracker') }">›</span>
          </div>
          <div v-if="expanded.has('device_tracker')" class="group-body">
            <EntityTile v-for="e in trackers" :key="e.entity_id" :entity="liveEntity(e)" @toggle="onToggle" />
          </div>
        </div>

        <!-- Zonen -->
        <div v-if="zones.length" class="group-block">
          <div class="group-header" @click="toggle('zone')">
            <MdiIcon icon="mdi:map-marker-radius" :size="18" color="var(--accent)" />
            <span class="group-name">Zonen</span>
            <span class="badge">{{ zones.length }}</span>
            <span class="chevron" :class="{ open: expanded.has('zone') }">›</span>
          </div>
          <div v-if="expanded.has('zone')" class="group-body">
            <EntityTile v-for="e in zones" :key="e.entity_id" :entity="liveEntity(e)" @toggle="onToggle" />
          </div>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useDashboardStore } from '../store/dashboard.js'
import EntityTile from '../components/EntityTile.vue'
import MdiIcon from '../components/MdiIcon.vue'

const { state, callService } = useDashboardStore()

const loading       = ref(true)
const error         = ref(null)
const allGroups     = ref([])
const persons       = ref([])
const trackers      = ref([])
const zones         = ref([])
const activeSection = ref('automations')
const expanded      = ref(new Set())

const haUrl = computed(() => window.location.origin.replace(/:\d+/, ':8123'))

const AUTO_DOMAINS    = new Set(['automation','script','scene'])
const HELPER_DOMAINS  = new Set(['input_boolean','input_number','input_select','input_text','input_datetime','input_button','timer','counter','schedule','todo','calendar'])

const autoGroups   = computed(() => allGroups.value.filter(g => AUTO_DOMAINS.has(g.domain)))
const helperGroups = computed(() => allGroups.value.filter(g => HELPER_DOMAINS.has(g.domain)))

const tabs = computed(() => [
  { id: 'automations', label: 'Automationen', icon: 'mdi:robot',        count: autoGroups.value.reduce((s,g)=>s+g.entities.length,0) },
  { id: 'helpers',     label: 'Helfer',        icon: 'mdi:wrench',       count: helperGroups.value.reduce((s,g)=>s+g.entities.length,0) },
  { id: 'persons',     label: 'Personen',      icon: 'mdi:account-group',count: persons.value.length },
])

async function load() {
  loading.value = true
  try {
    const [rAuto, rPers] = await Promise.all([fetch('api/automations'), fetch('api/persons')])
    const auto = await rAuto.json()
    const pers = await rPers.json()
    allGroups.value = auto.groups || []
    persons.value   = pers.persons || []
    trackers.value  = pers.trackers || []
    zones.value     = pers.zones || []
    // Standard aufgeklappt
    autoGroups.value.forEach(g => expanded.value.add(g.domain))
    expanded.value.add('person')
  } catch(e) {
    error.value = `Fehler: ${e.message}`
  } finally {
    loading.value = false
  }
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
function showMoreInfo(entityId) {
  try {
    window.parent.document.querySelector('home-assistant').dispatchEvent(
      new CustomEvent('hass-more-info', { bubbles: true, composed: true, detail: { entityId } })
    )
  } catch(e) {}
}

const DOMAIN_ICONS = {
  automation:'mdi:robot', script:'mdi:script-text', scene:'mdi:palette',
  input_boolean:'mdi:toggle-switch-outline', input_number:'mdi:ray-vertex',
  input_select:'mdi:format-list-bulleted', input_text:'mdi:form-textbox',
  input_datetime:'mdi:calendar-clock', input_button:'mdi:gesture-tap-button',
  timer:'mdi:timer-outline', counter:'mdi:counter',
  schedule:'mdi:calendar-clock', todo:'mdi:clipboard-list', calendar:'mdi:calendar',
}
function domainIcon(d) { return DOMAIN_ICONS[d] || 'mdi:help-circle' }

onMounted(load)
</script>

<style scoped>
.section-tabs { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.section-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: 20px; border: 1px solid var(--border);
  background: var(--surface); color: var(--muted); cursor: pointer; font-size: 13px; transition: all .15s;
}
.section-tab:hover { color: var(--text); border-color: var(--accent); }
.section-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.tab-count { font-size: 10px; background: rgba(255,255,255,.2); padding: 1px 5px; border-radius: 8px; }
.section-tab:not(.active) .tab-count { background: var(--border); color: var(--muted); }

.groups-list { display: flex; flex-direction: column; gap: 8px; }
.group-block { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.group-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; cursor: pointer; transition: background .15s; }
.group-header:hover { background: color-mix(in srgb, var(--accent) 6%, var(--surface)); }
.group-name { font-size: 14px; font-weight: 600; flex: 1; }
.badge { font-size: 11px; padding: 2px 7px; border-radius: 10px; background: var(--border); color: var(--muted); }
.chevron { font-size: 18px; color: var(--muted); transition: transform .2s; }
.chevron.open { transform: rotate(90deg); }
.group-body { display: flex; flex-direction: column; padding: 4px 4px 8px 28px; }

.persons-grid { display: flex; flex-wrap: wrap; gap: 12px; padding: 12px 16px; }
.person-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 14px 18px; border-radius: 12px; border: 1px solid var(--border);
  cursor: pointer; transition: border-color .15s; min-width: 110px;
  background: color-mix(in srgb, var(--bg) 30%, var(--surface));
}
.person-card:hover { border-color: var(--accent); }
.person-avatar { width: 52px; height: 52px; border-radius: 50%; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.person-name { font-size: 13px; font-weight: 500; text-align: center; }
.person-state { display: flex; align-items: center; gap: 4px; font-size: 11px; }
.home { color: var(--green); }
.away { color: var(--muted); }

.state-msg { text-align: center; color: var(--muted); margin-top: 40px; }
.state-msg.error { color: var(--red); }
</style>
