<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-box">

      <div class="modal-header">
        <div class="modal-title">
          <MdiIcon icon="mdi:robot" :size="20" color="var(--accent)" />
          KI-Vorschläge für Sprachassistent
        </div>
        <button class="close-btn" @click="$emit('close')">
          <MdiIcon icon="mdi:close" :size="18" />
        </button>
      </div>

      <!-- Zimmer-Auswahl -->
      <div v-if="step === 'select'" class="step-content">
        <p class="hint">Wähle ein Zimmer — {{ kiName }} schlägt vor welche Entitäten per Sprache steuerbar sein sollen. Du kannst die Auswahl anpassen.</p>
        <div v-if="loadingAreas" class="loading-hint">
          <MdiIcon icon="mdi:loading" :size="16" class="spin" /> Lade Zimmer…
        </div>
        <div class="area-list">
          <button
            v-for="area in areas"
            :key="area.name"
            class="area-btn"
            @click="analyzeArea(area)"
          >
            <MdiIcon :icon="area.icon || 'mdi:home-outline'" :size="20" color="var(--accent)" />
            <span class="area-btn-name">{{ area.name }}</span>
            <span class="area-count">{{ area.entities.length }} Entitäten</span>
            <MdiIcon icon="mdi:chevron-right" :size="16" color="var(--muted)" />
          </button>
        </div>
      </div>

      <!-- Analyse läuft -->
      <div v-else-if="step === 'loading'" class="loading-state">
        <MdiIcon icon="mdi:loading" :size="40" color="var(--accent)" class="spin" />
        <p>{{ kiName }} analysiert <strong>{{ currentArea?.name }}</strong>…</p>
      </div>

      <!-- Fehler -->
      <div v-else-if="step === 'error'" class="error-state">
        <MdiIcon icon="mdi:alert-circle" :size="36" color="var(--red)" />
        <p>{{ error }}</p>
        <button class="btn-secondary" @click="step = 'select'">Zurück</button>
      </div>

      <!-- Alle Entitäten mit KI-Markierung -->
      <div v-else-if="step === 'results'" class="suggestions">
        <div class="results-header">
          <button class="back-btn" @click="step = 'select'">
            <MdiIcon icon="mdi:chevron-left" :size="16" /> Zurück
          </button>
          <MdiIcon :icon="currentArea?.icon || 'mdi:home-outline'" :size="16" color="var(--accent)" />
          <span class="results-title">{{ currentArea?.name }}</span>
          <span class="ki-badge">
            <MdiIcon icon="mdi:robot" :size="12" /> {{ suggestedIds.size }} KI-Vorschläge
          </span>
        </div>
        <p class="hint">Alle Entitäten des Zimmers — blaue sind KI-Empfehlungen. Passe die Auswahl an.</p>

        <div class="suggestions-list">
          <div
            v-for="e in allEntities"
            :key="e.entity_id"
            class="suggestion-item"
            :class="{ selected: selected.has(e.entity_id), suggested: suggestedIds.has(e.entity_id) }"
            @click="toggleSelected(e.entity_id)"
          >
            <MdiIcon
              :icon="selected.has(e.entity_id) ? 'mdi:checkbox-marked' : 'mdi:checkbox-blank-outline'"
              :size="18"
              :color="selected.has(e.entity_id) ? 'var(--accent)' : 'var(--muted)'"
            />
            <div class="suggestion-info">
              <div class="suggestion-name">
                {{ e.name || e.entity_id }}
                <span v-if="suggestedIds.has(e.entity_id)" class="ki-chip">
                  <MdiIcon icon="mdi:robot" :size="10" /> KI
                </span>
              </div>
              <div class="suggestion-meta">
                <span class="entity-id">{{ e.entity_id }}</span>
                <span v-if="e.already_exposed" class="already-badge">bereits aktiv</span>
              </div>
              <div v-if="e.reason" class="suggestion-reason">{{ e.reason }}</div>
            </div>
            <MdiIcon
              :icon="selected.has(e.entity_id) ? 'mdi:microphone' : 'mdi:microphone-off'"
              :size="15"
              :color="selected.has(e.entity_id) ? 'var(--accent)' : 'var(--muted)'"
            />
          </div>
        </div>

        <div class="modal-footer">
          <span class="selection-count">{{ selected.size }} ausgewählt</span>
          <button class="btn-secondary" @click="step = 'select'">Anderes Zimmer</button>
          <button class="btn-primary" @click="apply" :disabled="applying || !selected.size">
            <MdiIcon v-if="applying" icon="mdi:loading" :size="14" class="spin" />
            {{ applying ? 'Wird gesetzt…' : 'Übernehmen' }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'

const props = defineProps({
  kiName:     { type: String, default: 'KI' },
  model:      { type: String, default: '' },
  exposeMap:  { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close', 'applied'])

const step         = ref('select')
const areas        = ref([])
const loadingAreas = ref(true)
const currentArea  = ref(null)
const allEntities  = ref([])
const suggestedIds = ref(new Set())
const selected     = ref(new Set())
const applying     = ref(false)
const error        = ref('')

onMounted(async () => {
  try {
    const r = await fetch('api/areas')
    const d = await r.json()
    areas.value = (d.areas || [])
      .filter(a => a.devices?.length > 0)
      .map(a => ({
        name: a.name,
        icon: a.icon || 'mdi:home-outline',
        entities: a.devices?.flatMap(dev => dev.entities || []) || [],
      }))
  } catch(e) {
    error.value = e.message
  } finally {
    loadingAreas.value = false
  }
})

async function analyzeArea(area) {
  currentArea.value = area
  step.value = 'loading'
  suggestedIds.value = new Set()
  selected.value = new Set()

  const CONTROLLABLE = ['light', 'switch', 'cover', 'climate', 'lock', 'fan', 'media_player', 'vacuum', 'input_boolean', 'script', 'scene']

  // Alle Entitäten aufbauen — steuerbare und nicht-steuerbare getrennt
  const allAreaEntities = area.entities.map(e => ({
    entity_id:       e.entity_id,
    name:            e.friendly_name || e.entity_id,
    domain:          e.entity_id.split('.')[0],
    already_exposed: props.exposeMap[e.entity_id] === true,
    reason:          '',
  }))
  const controllable = allAreaEntities.filter(e => CONTROLLABLE.includes(e.domain))

  try {
    // Nur steuerbare Entitäten an KI schicken
    const r = await fetch('api/voice/suggest', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        model:     props.model,
        area_name: area.name,
        entities:  controllable.map(e => ({
          entity_id: e.entity_id,
          name:      e.name,
          domain:    e.domain,
        })),
      }),
    })
    const d = await r.json()
    if (d.error) { error.value = d.error; step.value = 'error'; return }

    // KI-Vorschläge als Set speichern + reason hinzufügen
    const suggestions = d.suggestions || []
    const reasonMap = {}
    for (const s of suggestions) {
      suggestedIds.value.add(s.entity_id)
      reasonMap[s.entity_id] = s.reason || ''
    }

    // Nur steuerbare anzeigen: KI-Vorschläge zuerst, dann Rest
    const suggested = controllable.filter(e => suggestedIds.value.has(e.entity_id)).map(e => ({ ...e, reason: reasonMap[e.entity_id] || '' }))
    const rest      = controllable.filter(e => !suggestedIds.value.has(e.entity_id))
    allEntities.value = [...suggested, ...rest]

    // KI-Vorschläge vorauswählen
    selected.value = new Set(suggestions.map(s => s.entity_id))

    step.value = 'results'
  } catch(e) {
    error.value = e.message
    step.value = 'error'
  }
}

function toggleSelected(entity_id) {
  const s = new Set(selected.value)
  if (s.has(entity_id)) s.delete(entity_id)
  else s.add(entity_id)
  selected.value = s
}

async function apply() {
  applying.value = true
  let ok = 0
  for (const entity_id of selected.value) {
    try {
      await fetch(`api/voice/expose/${encodeURIComponent(entity_id)}`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ exposed: true }),
      })
      ok++
    } catch(e) {}
  }
  applying.value = false
  emit('applied', ok)
  step.value = 'select'
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-box {
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  width: 540px; max-width: 95vw; max-height: 82vh;
  display: flex; flex-direction: column; overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.modal-title { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 600; }
.close-btn { padding: 6px; border: none; background: transparent; color: var(--muted); cursor: pointer; border-radius: 6px; }
.close-btn:hover { color: var(--text); background: var(--border); }

.step-content { display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
.hint { padding: 10px 20px; font-size: 12px; color: var(--muted); border-bottom: 1px solid var(--border); margin: 0; flex-shrink: 0; }
.loading-hint { padding: 8px 20px; font-size: 12px; color: var(--muted); display: flex; align-items: center; gap: 6px; }

.area-list { overflow-y: auto; padding: 8px 12px; display: flex; flex-direction: column; gap: 4px; }
.area-btn {
  display: flex; align-items: center; gap: 10px; padding: 11px 14px;
  border-radius: 10px; border: 1px solid var(--border); background: var(--bg);
  color: var(--text); cursor: pointer; text-align: left; font-size: 13px;
  transition: all .15s;
}
.area-btn:hover { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 5%, var(--bg)); }
.area-btn-name { flex: 1; font-weight: 500; }
.area-count { font-size: 11px; color: var(--muted); }

.loading-state, .error-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 14px; padding: 50px 20px; color: var(--muted); font-size: 14px;
}

.results-header {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.back-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 8px;
  border-radius: 6px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 12px; margin-right: 4px;
}
.back-btn:hover { color: var(--text); }
.results-title { font-size: 14px; font-weight: 600; flex: 1; }
.ki-badge { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); padding: 2px 8px; border-radius: 10px; }

.suggestions { display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
.suggestions-list { overflow-y: auto; flex: 1; padding: 6px 12px; display: flex; flex-direction: column; gap: 3px; }

.suggestion-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 10px;
  border-radius: 9px; cursor: pointer; border: 1px solid transparent; transition: all .12s;
}
.suggestion-item:hover { background: var(--border); }
.suggestion-item.selected { background: color-mix(in srgb, var(--accent) 8%, var(--surface)); border-color: color-mix(in srgb, var(--accent) 25%, var(--border)); }
.suggestion-item.suggested:not(.selected) { opacity: 0.7; }

.suggestion-info { flex: 1; min-width: 0; }
.suggestion-name { font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 6px; }
.ki-chip { display: inline-flex; align-items: center; gap: 2px; font-size: 9px; font-weight: 600; color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); padding: 1px 5px; border-radius: 4px; }
.suggestion-meta { display: flex; gap: 6px; align-items: center; margin-top: 1px; }
.entity-id { font-size: 10px; color: var(--muted); font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.already-badge { font-size: 10px; padding: 1px 5px; border-radius: 4px; background: color-mix(in srgb, var(--green) 15%, var(--surface)); color: var(--green); flex-shrink: 0; }
.suggestion-reason { font-size: 10px; color: var(--muted); margin-top: 1px; font-style: italic; }

.modal-footer {
  display: flex; align-items: center; gap: 8px; padding: 12px 16px;
  border-top: 1px solid var(--border); flex-shrink: 0;
}
.selection-count { font-size: 12px; color: var(--muted); flex: 1; }
.btn-secondary { padding: 7px 14px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface); color: var(--text); cursor: pointer; font-size: 12px; }
.btn-primary {
  padding: 7px 16px; border-radius: 8px; border: none;
  background: var(--accent); color: #fff; cursor: pointer; font-size: 12px;
  display: flex; align-items: center; gap: 6px;
}
.btn-primary:disabled { opacity: .4; cursor: default; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
