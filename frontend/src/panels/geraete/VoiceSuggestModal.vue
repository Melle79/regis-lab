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
        <p class="hint">Wähle ein Zimmer — {{ kiName }} analysiert die Entitäten und schlägt vor welche per Sprache steuerbar sein sollen.</p>
        <div class="area-list">
          <button
            v-for="area in areas"
            :key="area.name"
            class="area-btn"
            @click="analyzeArea(area)"
          >
            <MdiIcon :icon="area.icon || 'mdi:home'" :size="18" />
            {{ area.name }}
            <span class="area-count">{{ area.entities.length }} Entitäten</span>
          </button>
        </div>
        <div v-if="loadingAreas" class="loading-hint">
          <MdiIcon icon="mdi:loading" :size="16" class="spin" /> Lade Zimmer…
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

      <!-- Vorschläge -->
      <div v-else-if="step === 'results'" class="suggestions">
        <div class="results-header">
          <button class="back-btn" @click="step = 'select'">
            <MdiIcon icon="mdi:chevron-left" :size="16" /> Zurück
          </button>
          <span class="results-title">{{ currentArea?.name }}</span>
        </div>
        <p class="hint">
          {{ suggestions.length ? `${kiName} empfiehlt ${suggestions.length} Entitäten. Passe die Auswahl an.` : 'Keine sinnvollen Entitäten für den Sprachassistenten gefunden.' }}
        </p>

        <div class="suggestions-list">
          <div
            v-for="s in suggestions"
            :key="s.entity_id"
            class="suggestion-item"
            :class="{ selected: selected.has(s.entity_id) }"
            @click="toggleSelected(s.entity_id)"
          >
            <MdiIcon
              :icon="selected.has(s.entity_id) ? 'mdi:checkbox-marked' : 'mdi:checkbox-blank-outline'"
              :size="18"
              :color="selected.has(s.entity_id) ? 'var(--accent)' : 'var(--muted)'"
            />
            <div class="suggestion-info">
              <div class="suggestion-name">{{ s.name || s.entity_id }}</div>
              <div class="suggestion-meta">
                <span class="entity-id">{{ s.entity_id }}</span>
                <span v-if="s.already_exposed" class="already-badge">bereits aktiv</span>
              </div>
              <div v-if="s.reason" class="suggestion-reason">{{ s.reason }}</div>
            </div>
            <MdiIcon
              :icon="selected.has(s.entity_id) ? 'mdi:microphone' : 'mdi:microphone-off'"
              :size="15"
              :color="selected.has(s.entity_id) ? 'var(--accent)' : 'var(--muted)'"
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
  kiName: { type: String, default: 'KI' },
  model:  { type: String, default: '' },
})
const emit = defineEmits(['close', 'applied'])

const step        = ref('select')
const areas       = ref([])
const loadingAreas = ref(true)
const currentArea = ref(null)
const suggestions = ref([])
const selected    = ref(new Set())
const applying    = ref(false)
const error       = ref('')

onMounted(async () => {
  try {
    const r = await fetch('api/areas')
    const d = await r.json()
    areas.value = (d.areas || []).filter(a => a.devices?.length > 0).map(a => ({
      name: a.name,
      icon: a.icon,
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
  suggestions.value = []
  selected.value = new Set()

  try {
    const r = await fetch('api/voice/suggest', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        model:     props.model,
        area_name: area.name,
        entities:  area.entities.map(e => ({
          entity_id: e.entity_id,
          name:      e.friendly_name || e.entity_id,
          domain:    e.entity_id.split('.')[0],
        })),
      }),
    })
    const d = await r.json()
    if (d.error) { error.value = d.error; step.value = 'error'; return }
    suggestions.value = d.suggestions || []
    selected.value = new Set(suggestions.value.map(s => s.entity_id))
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
  width: 520px; max-width: 95vw; max-height: 80vh;
  display: flex; flex-direction: column; overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.modal-title { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 600; }
.close-btn { padding: 6px; border: none; background: transparent; color: var(--muted); cursor: pointer; border-radius: 6px; }
.close-btn:hover { color: var(--text); background: var(--border); }

.step-content { display: flex; flex-direction: column; overflow: hidden; }
.hint { padding: 10px 20px; font-size: 12px; color: var(--muted); border-bottom: 1px solid var(--border); margin: 0; flex-shrink: 0; }
.loading-hint { padding: 10px 20px; font-size: 12px; color: var(--muted); display: flex; align-items: center; gap: 6px; }

.area-list { overflow-y: auto; padding: 8px 12px; display: flex; flex-direction: column; gap: 4px; }
.area-btn {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  border-radius: 10px; border: 1px solid var(--border); background: var(--bg);
  color: var(--text); cursor: pointer; text-align: left; font-size: 13px;
  transition: all .15s;
}
.area-btn:hover { border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 5%, var(--bg)); }
.area-count { margin-left: auto; font-size: 11px; color: var(--muted); }

.loading-state, .error-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 14px; padding: 50px 20px; color: var(--muted); font-size: 14px;
}

.results-header {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.back-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 8px;
  border-radius: 6px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 12px;
}
.back-btn:hover { color: var(--text); }
.results-title { font-size: 14px; font-weight: 600; }

.suggestions { display: flex; flex-direction: column; overflow: hidden; }
.suggestions-list { overflow-y: auto; flex: 1; padding: 8px 12px; display: flex; flex-direction: column; gap: 4px; }
.suggestion-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 10px; cursor: pointer; border: 1px solid transparent; transition: all .15s;
}
.suggestion-item:hover { background: var(--border); }
.suggestion-item.selected { background: color-mix(in srgb, var(--accent) 8%, var(--surface)); border-color: color-mix(in srgb, var(--accent) 30%, var(--border)); }
.suggestion-info { flex: 1; }
.suggestion-name { font-size: 13px; font-weight: 500; }
.suggestion-meta { display: flex; gap: 6px; align-items: center; margin-top: 2px; }
.entity-id { font-size: 10px; color: var(--muted); font-family: monospace; }
.already-badge { font-size: 10px; padding: 1px 6px; border-radius: 4px; background: color-mix(in srgb, var(--green) 15%, var(--surface)); color: var(--green); }
.suggestion-reason { font-size: 11px; color: var(--muted); margin-top: 2px; font-style: italic; }

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
