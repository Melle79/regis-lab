<template>
  <div class="areas-panel">

    <!-- Stockwerk-Tabs -->
    <div class="floor-tabs">
      <button
        v-for="f in sortedFloors" :key="f.floor_id"
        :class="['floor-tab', { active: activeFloor === f.floor_id }]"
        @click="activeFloor = f.floor_id"
      >{{ f.name }}</button>
      <button :class="['floor-tab', { active: activeFloor === '__all__' }]" @click="activeFloor = '__all__'">Alle</button>
      <button :class="['floor-tab', { active: activeFloor === '__unassigned__' }]" @click="activeFloor = '__unassigned__'">Nicht zugeordnet</button>
    </div>

    <div class="areas-toolbar">
      <button class="toolbar-btn" @click="expandAll">
        <MdiIcon icon="mdi:unfold-more-horizontal" :size="14" /> Alle aufklappen
      </button>
      <button class="toolbar-btn" @click="collapseAll">
        <MdiIcon icon="mdi:unfold-less-horizontal" :size="14" /> Alle zuklappen
      </button>
    </div>
    <div v-if="loading" class="state-msg">Bereiche werden geladen…</div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>

    <template v-else>
      <div class="areas-list">

        <div v-for="area in visibleAreas" :key="area.area_id" class="area-block">
          <div class="area-header" @click="toggle('area_' + area.area_id)">
            <span class="area-icon">
              <MdiIcon :icon="area.icon || 'mdi:home'" :size="20" />
            </span>
            <span class="area-name">{{ area.name }}</span>
            <span v-if="area.floor_name && activeFloor === '__all__'" class="badge accent">{{ area.floor_name }}</span>
            <span class="badge">{{ countEntities(area) }}</span>
            <button class="ha-link-btn" @click.stop="openArea(area)" title="In HA öffnen">
              <MdiIcon icon="mdi:open-in-new" :size="13" />
            </button>
            <span class="chevron" :class="{ open: expanded.has('area_' + area.area_id) }">›</span>
          </div>

          <transition name="slide">
            <div v-if="expanded.has('area_' + area.area_id)" class="area-body">

              <div v-for="device in area.devices" :key="device.device_id" class="device-block">
                <div class="device-header" @click="toggle('dev_' + device.device_id)">
                  <span class="device-icon">
                                                            <img v-if="device.integration" :src="brandIconUrl(device.integration)"
                      :width="18" :height="18" style="object-fit:contain"
                      @error="$event.target.style.display='none'"
                    />
                    <MdiIcon v-else :icon="getDeviceIcon(device)" :size="16" />
                  </span>
                  <div class="device-info">
                    <div class="device-name-row">
                      <span class="device-name">{{ device.name }}</span>
                      <span v-if="device.integration" class="integration-badge">{{ device.integration }}</span>
                    </div>
                    <span v-if="device.model" class="device-model">{{ device.manufacturer }} · {{ device.model }}</span>
                  </div>
                  <span class="badge dim">{{ device.entities.length }}</span>
                  <button class="assign-btn" @click.stop="openAssignModal(device, null)" title="Bereich zuweisen">
                    <MdiIcon icon="mdi:pencil" :size="12" />
                  </button>
                  <span class="chevron small" :class="{ open: expanded.has('dev_' + device.device_id) }">›</span>
                </div>
                <div v-if="expanded.has('dev_' + device.device_id)" class="entity-list">
                  <EntityTile v-for="e in device.entities" :key="e.entity_id" :entity="liveEntity(e)" @toggle="onToggle"/>
                </div>
              </div>

            </div>
          </transition>
        </div>

      </div>

      <!-- Nicht zugeordnet -->
      <div v-if="activeFloor === '__unassigned__'" class="areas-list">
        <div v-for="device in unassignedDevices" :key="device.device_id" class="device-block">
          <div class="device-header" @click="toggle('dev_' + device.device_id)">
            <span class="device-icon">
              <img v-if="device.integration" :src="brandIconUrl(device.integration)"
                :width="18" :height="18" style="object-fit:contain"
                @error="$event.target.style.display='none'"
              />
              <MdiIcon v-else :icon="getDeviceIcon(device)" :size="16" />
            </span>
            <div class="device-info">
              <div class="device-name-row">
                <span class="device-name">{{ device.name }}</span>
                <span v-if="device.integration" class="integration-badge">{{ device.integration }}</span>
              </div>
              <span v-if="device.model" class="device-model">{{ device.manufacturer }} · {{ device.model }}</span>
            </div>
            <span class="badge dim">{{ device.entities.length }}</span>
            <button class="assign-btn" @click.stop="openAssignModal(device, null)" title="Bereich zuweisen">
              <MdiIcon icon="mdi:pencil" :size="12" />
            </button>
            <span class="chevron small" :class="{ open: expanded.has('dev_' + device.device_id) }">›</span>
          </div>
          <div v-if="expanded.has('dev_' + device.device_id)" class="entity-list">
            <EntityTile v-for="e in device.entities" :key="e.entity_id" :entity="liveEntity(e)" @toggle="onToggle"/>
          </div>
        </div>
      </div>

    </template>
  </div>
  <!-- Bereich-Zuweisungs-Modal -->
  <AssignAreaModal
    v-if="assignModal"
    :device="assignModal.device"
    :current-area="assignModal.currentArea"
    @close="assignModal = null"
    @assigned="onAssigned"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDashboardStore } from '../../store/dashboard.js'
import EntityTile from '../../components/EntityTile.vue'
import { getEntityIcon } from '../../utils/haIcons.js'
import AssignAreaModal from '../../components/AssignAreaModal.vue'
import MdiIcon    from '../../components/MdiIcon.vue'

const { callService, state } = useDashboardStore()

const loading            = ref(true)
const error              = ref(null)
const floors             = ref([])
const areas              = ref([])
const unassignedDevices  = ref([])
const unassignedEntities = ref([])
const activeFloor        = ref('__all__')
const expanded           = ref(new Set())  // leer = alles eingeklappt

function brandIconUrl(integration) {
  if (!integration) return null
  // HA offizielle Brand-Icons CDN - dark_icon Format
  return `https://brands.home-assistant.io/_/${integration}/icon.png`
}
const assignModal        = ref(null)  // { device, currentArea }

function openAssignModal(device, areaId = null) {
  assignModal.value = { device, currentArea: areaId }
}

async function onAssigned({ device_id, area_id }) {
  await loadAreas()
}

function openInHA(path) {
  try {
    if (window.parent !== window) {
      window.parent.history.pushState(null, '', path)
      window.parent.dispatchEvent(new PopStateEvent('popstate'))
    }
  } catch(e) {}
  // Fallback
  try {
    const haUrl = window.location.origin.replace(/:\d+/, ':8123')
    window.open(`${haUrl}${path}`, '_blank')
  } catch(e) {}
}

function openArea(area)   { openInHA(`/config/areas/area/${area.area_id}`) }
function openDevice(device) { openInHA(`/config/devices/device/${device.device_id}`) }
function openEntity(entity) {
  // Entity-Info Dialog über HA more-info
  const haUrl = window.location.origin.replace(/:\d+/, ':8123')
  try {
    if (window.parent !== window) {
      window.parent.dispatchEvent(new CustomEvent('hass-more-info', {
        bubbles: true, composed: true,
        detail: { entityId: entity.entity_id }
      }))
    } else {
      window.open(`${haUrl}/config/entities?search=${entity.entity_id}`, '_blank')
    }
  } catch(e) {
    window.open(`${haUrl}/config/entities?search=${entity.entity_id}`, '_blank')
  }
}

async function loadAreas() {
  loading.value = true
  error.value   = null
  try {
    const r = await fetch('api/areas')
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const data = await r.json()
    floors.value             = data.floors              || []
    areas.value              = data.areas               || []
    unassignedDevices.value  = data.unassigned_devices  || []
    unassignedEntities.value = data.unassigned_entities || []
    // Alles eingeklappt beim Start
    if (sortedFloors.value.length)
      activeFloor.value = sortedFloors.value[0].floor_id
  } catch (e) {
    error.value = `Fehler: ${e.message}`
  } finally {
    loading.value = false
  }
}

const sortedFloors = computed(() =>
  [...floors.value].sort((a, b) => (b.level ?? 0) - (a.level ?? 0))
)

const visibleAreas = computed(() =>
  activeFloor.value === '__all__'
    ? areas.value
    : areas.value.filter(a => a.floor_id === activeFloor.value)
)

function toggle(key) {
  const s = new Set(expanded.value)
  s.has(key) ? s.delete(key) : s.add(key)
  expanded.value = s
}

function liveEntity(e) { return state.entities[e.entity_id] || e }

function expandAll() {
  const s = new Set(expanded.value)
  visibleAreas.value.forEach(a => {
    s.add('area_' + a.area_id)
    a.devices.forEach(d => s.add('dev_' + d.device_id))
  })
  s.add('area___unassigned__')
  expanded.value = s
}

function collapseAll() {
  expanded.value = new Set()
}
function countEntities(area) { return area.devices.reduce((s, d) => s + d.entities.length, 0) + area.entities.length }

const TOGGLEABLE = ['light','switch','input_boolean','fan','cover']
function onToggle(entity) {
  const domain = entity.entity_id.split('.')[0]
  if (!TOGGLEABLE.includes(domain)) return
  callService(domain, entity.state === 'on' ? 'turn_off' : 'turn_on', { entity_id: entity.entity_id })
}

function getDeviceIcon(device) {
  const name = (device.name || '').toLowerCase()
  const mfr  = (device.manufacturer || '').toLowerCase()
  if (name.includes('licht') || name.includes('light') || name.includes('lampe')) return 'mdi:lightbulb'
  if (name.includes('steckdose') || name.includes('plug'))   return 'mdi:power-socket-de'
  if (name.includes('schalter') || name.includes('switch'))  return 'mdi:toggle-switch'
  if (name.includes('sensor') || name.includes('bewegung'))  return 'mdi:motion-sensor'
  if (name.includes('thermostat') || name.includes('heizung')) return 'mdi:thermostat'
  if (name.includes('rollo') || name.includes('jalousie'))   return 'mdi:window-shutter'
  if (name.includes('kamera') || name.includes('camera'))    return 'mdi:cctv'
  if (name.includes('echo') || name.includes('alexa'))       return 'mdi:amazon-alexa'
  if (name.includes('tv') || name.includes('fernseh'))       return 'mdi:television'
  if (name.includes('aquarium'))                             return 'mdi:fish'
  if (name.includes('drucker') || name.includes('print'))    return 'mdi:printer-3d'
  if (name.includes('phone') || name.includes('iphone'))     return 'mdi:cellphone'
  if (name.includes('ipad') || name.includes('tablet'))      return 'mdi:tablet'
  if (mfr.includes('apple'))                                 return 'mdi:apple'
  if (mfr.includes('philips') || mfr.includes('hue'))        return 'mdi:lightbulb'
  if (mfr.includes('shelly'))                                return 'mdi:power-plug'
  if (mfr.includes('sonos'))                                 return 'mdi:speaker'
  return 'mdi:chip'
}

onMounted(loadAreas)
</script>

<style scoped>
.floor-tabs { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.floor-tab { padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); background: var(--surface); color: var(--muted); cursor: pointer; font-size: 13px; transition: all .15s; }
.floor-tab:hover { color: var(--text); border-color: var(--accent); }
.floor-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }

.areas-list { display: flex; flex-direction: column; gap: 8px; }

.area-block { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.area-block.unassigned { opacity: .65; }

.area-header { display: flex; align-items: center; gap: 10px; padding: 13px 16px; cursor: pointer; user-select: none; transition: background .15s; }
.area-header:hover { background: color-mix(in srgb, var(--accent) 6%, var(--surface)); }
.area-icon { display: flex; align-items: center; color: var(--accent); }
.area-name { font-weight: 600; font-size: 14px; flex: 1; }

.badge { font-size: 11px; padding: 2px 7px; border-radius: 10px; background: var(--border); color: var(--muted); }
.badge.accent { background: color-mix(in srgb, var(--accent) 20%, var(--border)); color: var(--accent); }
.dim { opacity: .6; }

.chevron { font-size: 18px; color: var(--muted); transition: transform .2s; display: inline-block; }
.chevron.open { transform: rotate(90deg); }
.chevron.small { font-size: 14px; }

.area-body { padding: 4px 12px 12px; display: flex; flex-direction: column; gap: 6px; }
.empty { font-size: 12px; color: var(--muted); padding: 4px; }

.device-block { border-radius: 8px; border: 1px solid var(--border); overflow: hidden; background: color-mix(in srgb, var(--bg) 30%, var(--surface)); }
.device-header { display: flex; align-items: center; gap: 8px; padding: 9px 12px; cursor: pointer; user-select: none; transition: background .15s; }
.device-header:hover { background: color-mix(in srgb, var(--accent) 5%, transparent); }
.device-icon { display: flex; align-items: center; color: var(--muted); flex-shrink: 0; }
.device-info { flex: 1; min-width: 0; }
.device-name-row { display: flex; align-items: center; gap: 6px; }
.device-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.integration-badge { font-size: 9px; padding: 1px 5px; border-radius: 4px; background: color-mix(in srgb, var(--accent) 15%, var(--border)); color: var(--accent); flex-shrink: 0; margin-left: 4px; }
.device-model { font-size: 10px; color: var(--muted); display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.entity-list { display: flex; flex-direction: column; padding: 4px 4px 8px; }

.areas-toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.toolbar-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--surface); color: var(--muted); cursor: pointer; font-size: 12px;
  transition: all .15s;
}
.toolbar-btn:hover { color: var(--text); border-color: var(--accent); }
.state-msg { text-align: center; color: var(--muted); margin-top: 40px; }
.state-msg.error { color: var(--red); }

.assign-btn, .ha-link-btn {
  opacity: 0; padding: 4px; border-radius: 4px; border: none;
  background: transparent; color: var(--muted); cursor: pointer;
  transition: opacity .15s, background .15s; flex-shrink: 0;
}
.device-header:hover .assign-btn,
.device-header:hover .ha-link-btn,
.area-header:hover .ha-link-btn { opacity: 1; }
.assign-btn:hover, .ha-link-btn:hover { background: var(--border); color: var(--text); }

.slide-enter-active, .slide-leave-active { transition: all .2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
