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

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <MdiIcon icon="mdi:loading" :size="36" color="var(--accent)" class="spin" />
        <p>{{ kiName }} analysiert deine Geräte…</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-state">
        <MdiIcon icon="mdi:alert-circle" :size="36" color="var(--red)" />
        <p>{{ error }}</p>
        <button class="btn-secondary" @click="$emit('close')">Schließen</button>
      </div>

      <!-- Ergebnisse -->
      <div v-else class="suggestions">
        <p class="hint">
          {{ kiName }} empfiehlt {{ suggestions.length }} Entitäten. Passe die Auswahl an und bestätige.
        </p>

        <div class="suggestions-list">
          <div
            v-for="(s, i) in suggestions"
            :key="s.entity_id"
            class="suggestion-item"
            :class="{ selected: selected.has(s.entity_id) }"
            @click="toggleSelected(s.entity_id)"
          >
            <div class="suggestion-check">
              <MdiIcon
                :icon="selected.has(s.entity_id) ? 'mdi:checkbox-marked' : 'mdi:checkbox-blank-outline'"
                :size="18"
                :color="selected.has(s.entity_id) ? 'var(--accent)' : 'var(--muted)'"
              />
            </div>
            <div class="suggestion-info">
              <div class="suggestion-name">{{ s.name }}</div>
              <div class="suggestion-meta">
                <span class="entity-id">{{ s.entity_id }}</span>
                <span v-if="s.area" class="area-badge">{{ s.area }}</span>
                <span v-if="s.already_exposed" class="already-badge">bereits aktiv</span>
              </div>
              <div v-if="s.reason" class="suggestion-reason">{{ s.reason }}</div>
            </div>
            <MdiIcon
              :icon="selected.has(s.entity_id) ? 'mdi:microphone' : 'mdi:microphone-off'"
              :size="16"
              :color="selected.has(s.entity_id) ? 'var(--accent)' : 'var(--muted)'"
            />
          </div>
        </div>

        <div class="modal-footer">
          <span class="selection-count">{{ selected.size }} ausgewählt</span>
          <button class="btn-secondary" @click="$emit('close')">Abbrechen</button>
          <button class="btn-primary" @click="apply" :disabled="applying">
            <MdiIcon v-if="applying" icon="mdi:loading" :size="14" class="spin" />
            {{ applying ? 'Wird angewendet…' : 'Übernehmen' }}
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

const loading     = ref(true)
const error       = ref('')
const suggestions = ref([])
const selected    = ref(new Set())
const applying    = ref(false)

onMounted(async () => {
  try {
    const r = await fetch('api/voice/suggest', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ model: props.model }),
    })
    const d = await r.json()
    if (d.error) { error.value = d.error; loading.value = false; return }
    suggestions.value = d.suggestions || []
    // Alle vorauswählen
    selected.value = new Set(suggestions.value.map(s => s.entity_id))
  } catch(e) {
    error.value = `Fehler: ${e.message}`
  } finally {
    loading.value = false
  }
})

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
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-box {
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
  width: 560px; max-width: 95vw; max-height: 85vh;
  display: flex; flex-direction: column; overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
}
.modal-title { display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 600; }
.close-btn { padding: 6px; border: none; background: transparent; color: var(--muted); cursor: pointer; border-radius: 6px; }
.close-btn:hover { color: var(--text); background: var(--border); }

.loading-state, .error-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 16px; padding: 60px 20px; color: var(--muted);
}

.suggestions { display: flex; flex-direction: column; overflow: hidden; }
.hint { padding: 12px 20px; font-size: 13px; color: var(--muted); border-bottom: 1px solid var(--border); margin: 0; }

.suggestions-list { overflow-y: auto; flex: 1; padding: 8px 12px; display: flex; flex-direction: column; gap: 4px; }
.suggestion-item {
  display: flex; align-items: center; gap: 12px; padding: 10px 12px;
  border-radius: 10px; cursor: pointer; border: 1px solid transparent; transition: all .15s;
}
.suggestion-item:hover { background: var(--border); }
.suggestion-item.selected { background: color-mix(in srgb, var(--accent) 8%, var(--surface)); border-color: color-mix(in srgb, var(--accent) 30%, var(--border)); }

.suggestion-info { flex: 1; }
.suggestion-name { font-size: 13px; font-weight: 500; }
.suggestion-meta { display: flex; gap: 6px; align-items: center; margin-top: 2px; }
.entity-id { font-size: 11px; color: var(--muted); font-family: monospace; }
.area-badge { font-size: 10px; padding: 1px 6px; border-radius: 4px; background: var(--border); color: var(--muted); }
.already-badge { font-size: 10px; padding: 1px 6px; border-radius: 4px; background: color-mix(in srgb, var(--green) 15%, var(--surface)); color: var(--green); }
.suggestion-reason { font-size: 11px; color: var(--muted); margin-top: 2px; font-style: italic; }

.modal-footer {
  display: flex; align-items: center; gap: 10px; padding: 14px 20px;
  border-top: 1px solid var(--border);
}
.selection-count { font-size: 12px; color: var(--muted); flex: 1; }
.btn-secondary {
  padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); cursor: pointer; font-size: 13px;
}
.btn-primary {
  padding: 8px 20px; border-radius: 8px; border: none;
  background: var(--accent); color: #fff; cursor: pointer; font-size: 13px;
  display: flex; align-items: center; gap: 6px;
}
.btn-primary:disabled { opacity: .6; cursor: default; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
