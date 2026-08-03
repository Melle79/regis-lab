<template>
  <div class="verlauf-panel">

    <!-- Steuerleiste -->
    <div class="controls">
      <div class="sensor-picker">
        <MdiIcon icon="mdi:magnify" :size="16" color="var(--muted)" />
        <input
          v-model="search"
          class="search-input"
          type="text"
          placeholder="Sensor suchen…"
        />
        <select v-model="selectedEntity" class="sensor-select">
          <option value="" disabled>Sensor wählen…</option>
          <option v-for="s in filteredSensors" :key="s.entity_id" :value="s.entity_id">
            {{ s.name }}{{ s.unit ? ' · ' + s.unit : '' }}
          </option>
        </select>
      </div>

      <div class="range-buttons">
        <button
          v-for="r in RANGES"
          :key="r.hours"
          :class="['range-btn', { active: hours === r.hours }]"
          @click="hours = r.hours"
        >{{ r.label }}</button>
      </div>
    </div>

    <!-- Diagramm -->
    <div class="chart-card">
      <div v-if="!selectedEntity" class="chart-empty">
        <MdiIcon icon="mdi:chart-line" :size="48" color="var(--muted)" />
        <p>Wähle einen Sensor, um seinen Verlauf zu sehen.</p>
        <p class="hint" v-if="!sensors.length">Lade Sensoren…</p>
      </div>

      <template v-else>
        <div class="chart-head">
          <div class="chart-title">
            <MdiIcon :icon="currentIcon" :size="18" color="var(--accent)" />
            {{ currentName }}
          </div>
          <div class="chart-stats" v-if="points.length">
            <span class="stat"><b>{{ fmt(last) }}{{ unit }}</b><small>aktuell</small></span>
            <span class="stat"><b>{{ fmt(avg) }}{{ unit }}</b><small>Ø</small></span>
            <span class="stat"><b>{{ fmt(min) }}{{ unit }}</b><small>min</small></span>
            <span class="stat"><b>{{ fmt(max) }}{{ unit }}</b><small>max</small></span>
          </div>
        </div>

        <div v-if="loading" class="chart-msg">
          <MdiIcon icon="mdi:loading" :size="20" class="spin" /> Lade Verlauf…
        </div>
        <div v-else-if="error" class="chart-msg error">
          <MdiIcon icon="mdi:alert-circle" :size="18" /> {{ error }}
        </div>
        <div v-else-if="!points.length" class="chart-msg">
          Keine Daten für diesen Zeitraum in der InfluxDB.
        </div>

        <svg v-else class="chart-svg" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none">
          <!-- Gitternetz + Y-Beschriftung -->
          <g v-for="g in yGrid" :key="'y'+g.v">
            <line :x1="padL" :y1="g.y" :x2="W-padR" :y2="g.y" class="grid" />
            <text :x="padL-6" :y="g.y+3" class="axis-label" text-anchor="end">{{ fmt(g.v) }}</text>
          </g>
          <!-- Fläche + Linie -->
          <path :d="areaPath" class="area" />
          <path :d="linePath" class="line" />
          <!-- X-Beschriftung -->
          <text :x="padL" :y="H-6" class="axis-label" text-anchor="start">{{ xStartLabel }}</text>
          <text :x="W-padR" :y="H-6" class="axis-label" text-anchor="end">{{ xEndLabel }}</text>
        </svg>

        <div v-if="points.length" class="chart-foot">
          {{ points.length }} Messpunkte · {{ rangeLabel }}
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'
import { useDashboardStore } from '../../store/dashboard.js'
import { getEntityIcon } from '../../utils/haIcons.js'

const store = useDashboardStore()

const RANGES = [
  { label: '24 h',    hours: 24 },
  { label: '7 Tage',  hours: 168 },
  { label: '30 Tage', hours: 720 },
]
const NUMERIC_DOMAINS = ['sensor', 'number', 'input_number', 'climate', 'counter']

const search         = ref('')
const selectedEntity = ref('')
const hours          = ref(24)
const points         = ref([])
const loading        = ref(false)
const error          = ref('')

// Chart-Geometrie
const W = 720, H = 260, padL = 46, padR = 14, padT = 14, padB = 26

// ── Sensorliste aus dem Store ────────────────────────────────────
const sensors = computed(() => {
  const out = []
  for (const e of store.entityList.value) {
    const domain = e.entity_id.split('.')[0]
    if (!NUMERIC_DOMAINS.includes(domain)) continue
    if (isNaN(parseFloat(e.state))) continue
    out.push({
      entity_id: e.entity_id,
      name: e.attributes?.friendly_name || e.entity_id.split('.')[1],
      unit: e.attributes?.unit_of_measurement || '',
    })
  }
  return out.sort((a, b) => a.name.localeCompare(b.name, 'de'))
})

const filteredSensors = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = q
    ? sensors.value.filter(s => s.name.toLowerCase().includes(q) || s.entity_id.includes(q))
    : sensors.value
  return list.slice(0, 300)
})

const currentSensor = computed(() =>
  sensors.value.find(s => s.entity_id === selectedEntity.value) || null
)
const currentName = computed(() => currentSensor.value?.name || selectedEntity.value)
const unit        = computed(() => currentSensor.value?.unit || '')
const currentIcon = computed(() => {
  const live = store.state.entities[selectedEntity.value]
  return live ? getEntityIcon(live) : 'mdi:chart-line'
})
const rangeLabel  = computed(() => RANGES.find(r => r.hours === hours.value)?.label || '')

// ── Kennzahlen ───────────────────────────────────────────────────
const vals = computed(() => points.value.map(p => p.v))
const last = computed(() => vals.value.length ? vals.value[vals.value.length - 1] : 0)
const min  = computed(() => vals.value.length ? Math.min(...vals.value) : 0)
const max  = computed(() => vals.value.length ? Math.max(...vals.value) : 0)
const avg  = computed(() => vals.value.length ? vals.value.reduce((a, b) => a + b, 0) / vals.value.length : 0)

function fmt(v) {
  if (v == null || isNaN(v)) return '–'
  return Math.abs(v) >= 100 ? Math.round(v) : Math.round(v * 10) / 10
}

// ── Chart-Berechnung ─────────────────────────────────────────────
const bounds = computed(() => {
  if (!points.value.length) return null
  const ts = points.value.map(p => p.t)
  let vMin = min.value, vMax = max.value
  if (vMin === vMax) { vMin -= 1; vMax += 1 }       // flache Linie mittig
  else { const pad = (vMax - vMin) * 0.08; vMin -= pad; vMax += pad }
  return { tMin: Math.min(...ts), tMax: Math.max(...ts), vMin, vMax }
})

function sx(t) {
  const b = bounds.value
  const span = b.tMax - b.tMin || 1
  return padL + ((t - b.tMin) / span) * (W - padL - padR)
}
function sy(v) {
  const b = bounds.value
  const span = b.vMax - b.vMin || 1
  return padT + (1 - (v - b.vMin) / span) * (H - padT - padB)
}

const linePath = computed(() => {
  if (!bounds.value) return ''
  return points.value.map((p, i) => `${i ? 'L' : 'M'}${sx(p.t).toFixed(1)},${sy(p.v).toFixed(1)}`).join(' ')
})
const areaPath = computed(() => {
  if (!bounds.value) return ''
  const base = (H - padB).toFixed(1)
  const first = sx(points.value[0].t).toFixed(1)
  const lastX = sx(points.value[points.value.length - 1].t).toFixed(1)
  return `M${first},${base} ` +
    points.value.map(p => `L${sx(p.t).toFixed(1)},${sy(p.v).toFixed(1)}`).join(' ') +
    ` L${lastX},${base} Z`
})
const yGrid = computed(() => {
  if (!bounds.value) return []
  const { vMin, vMax } = bounds.value
  const steps = 4
  return Array.from({ length: steps + 1 }, (_, i) => {
    const v = vMin + (vMax - vMin) * (i / steps)
    return { v, y: sy(v) }
  })
})

function tsLabel(ms) {
  const d = new Date(ms)
  return hours.value <= 48
    ? d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })
}
const xStartLabel = computed(() => points.value.length ? tsLabel(points.value[0].t) : '')
const xEndLabel   = computed(() => points.value.length ? tsLabel(points.value[points.value.length - 1].t) : '')

// ── Daten laden ──────────────────────────────────────────────────
async function loadHistory() {
  if (!selectedEntity.value) return
  loading.value = true
  error.value = ''
  points.value = []
  try {
    const r = await fetch(`api/jarvis/influx/history?entity_id=${encodeURIComponent(selectedEntity.value)}&hours=${hours.value}`)
    const d = await r.json()
    if (d.error) { error.value = d.error }
    else { points.value = Array.isArray(d.points) ? d.points : [] }
  } catch (e) {
    error.value = 'Verlauf konnte nicht geladen werden'
  } finally {
    loading.value = false
  }
}

watch([selectedEntity, hours], loadHistory)
onMounted(() => { if (selectedEntity.value) loadHistory() })
</script>

<style scoped>
.verlauf-panel { display: flex; flex-direction: column; gap: 14px; }

.controls {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap;
}
.sensor-picker {
  display: flex; align-items: center; gap: 8px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 6px 10px; flex: 1; min-width: 260px;
}
.search-input {
  border: none; outline: none; background: transparent; color: var(--text);
  font-size: 13px; width: 130px;
}
.sensor-select {
  flex: 1; border: none; outline: none; background: transparent;
  color: var(--text); font-size: 13px; max-width: 100%;
}
.sensor-select option { background: var(--surface); color: var(--text); }

.range-buttons { display: flex; gap: 6px; }
.range-btn {
  padding: 6px 14px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--surface); color: var(--muted); cursor: pointer; font-size: 12px;
  transition: all .15s;
}
.range-btn:hover { color: var(--text); border-color: var(--accent); }
.range-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

.chart-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px; min-height: 320px;
}
.chart-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; color: var(--muted); text-align: center; min-height: 288px;
}
.chart-empty .hint { font-size: 12px; opacity: .7; }

.chart-head {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-wrap: wrap; margin-bottom: 10px;
}
.chart-title { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 15px; }
.chart-stats { display: flex; gap: 16px; }
.stat { display: flex; flex-direction: column; align-items: flex-end; line-height: 1.2; }
.stat b { font-size: 15px; }
.stat small { font-size: 10px; color: var(--muted); }

.chart-msg {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  min-height: 220px; color: var(--muted); font-size: 13px;
}
.chart-msg.error { color: var(--red); }

.chart-svg { width: 100%; height: 260px; display: block; }
.grid { stroke: var(--border); stroke-width: 1; opacity: .5; }
.axis-label { fill: var(--muted); font-size: 10px; }
.line { fill: none; stroke: var(--accent); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.area { fill: color-mix(in srgb, var(--accent) 15%, transparent); stroke: none; }

.chart-foot { margin-top: 8px; font-size: 11px; color: var(--muted); text-align: right; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
