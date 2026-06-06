<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="settings-modal">

        <div class="modal-header">
          <div class="modal-title">
            <MdiIcon icon="mdi:cog" :size="20" color="var(--accent)" />
            Einstellungen
          </div>
          <button class="close-btn" @click="$emit('close')">
            <MdiIcon icon="mdi:close" :size="18" />
          </button>
        </div>

        <div class="modal-body">

          <!-- Allgemein -->
          <div class="settings-card">
            <div class="card-title">
              <MdiIcon icon="mdi:tune" :size="20" color="var(--accent)" />
              Allgemein
            </div>

            <div class="field">
              <label>Dashboard-Titel</label>
              <input v-model="form.title" class="input" placeholder="Regis-Lab" />
            </div>

            <div class="field">
              <label>Theme</label>
              <div class="radio-group">
                <label v-for="t in ['dark','light','auto']" :key="t" class="radio-label">
                  <input type="radio" v-model="form.theme" :value="t" />
                  {{ t }}
                </label>
              </div>
            </div>

            <div class="field">
              <label>Uhr anzeigen</label>
              <div class="radio-group">
                <label class="radio-label"><input type="radio" v-model="form.show_clock" :value="true" /> Ja</label>
                <label class="radio-label"><input type="radio" v-model="form.show_clock" :value="false" /> Nein</label>
              </div>
            </div>

            <div class="field">
              <label>Wetter anzeigen</label>
              <div class="radio-group">
                <label class="radio-label"><input type="radio" v-model="form.show_weather" :value="true" /> Ja</label>
                <label class="radio-label"><input type="radio" v-model="form.show_weather" :value="false" /> Nein</label>
              </div>
            </div>

            <div class="field" v-if="form.show_weather">
              <label>Wetter-Entity ID</label>
              <input v-model="form.weather_entity" class="input" placeholder="weather.zuhause" />
            </div>
          </div>

          <!-- HA Token -->
          <div class="settings-card">
            <div class="card-title">
              <MdiIcon icon="mdi:key" :size="20" color="var(--accent)" />
              Home Assistant Token
            </div>
            <p class="card-desc">
              Ein <strong>Long-Lived Access Token</strong> erlaubt erweiterte HA-Funktionen (z.B. Custom Icons in der Seitenleiste).<br>
              Erstellen unter: <em>HA → Profil → Sicherheit → Langlebige Zugriffstoken</em>
            </p>

            <div class="field">
              <label>Token {{ form.ha_token_set ? '(gesetzt ✓)' : '(nicht gesetzt)' }}</label>
              <div class="token-row">
                <input
                  v-model="form.ha_token"
                  :type="showToken ? 'text' : 'password'"
                  class="input"
                  :placeholder="form.ha_token_set ? '********************' : 'Token einfügen…'"
                />
                <button class="icon-btn" @click="showToken = !showToken">
                  <MdiIcon :icon="showToken ? 'mdi:eye-off' : 'mdi:eye'" :size="18" />
                </button>
                <button v-if="form.ha_token_set" class="icon-btn danger" @click="clearToken">
                  <MdiIcon icon="mdi:delete" :size="18" />
                </button>
              </div>
              <div v-if="tokenError" class="token-status err">
                <MdiIcon icon="mdi:alert-circle" :size="14" />
                {{ tokenError }}
              </div>
              <div v-if="iconRegistered !== null && (iconRegistered || form.ha_token)" :class="['token-status', iconRegistered ? 'ok' : 'err']">
                <MdiIcon :icon="iconRegistered ? 'mdi:check-circle' : 'mdi:alert-circle'" :size="14" />
                {{ iconRegistered ? 'Custom Icon erfolgreich registriert' : 'Icon-Registrierung fehlgeschlagen — Token prüfen' }}
              </div>
            </div>
          </div>

          <!-- Lokaler KI-Assistent -->
          <div class="settings-card">
            <div class="card-title">
              <MdiIcon icon="mdi:robot" :size="20" color="var(--accent)" />
              Lokaler KI-Assistent
            </div>
            <p class="card-desc">Verbinde deinen KI-Assistenten mit einer lokalen Ollama-Installation.</p>

            <div class="field">
              <label>Name des Assistenten</label>
              <input v-model="form.ki_name" class="input" placeholder="Jarvis" />
            </div>

            <div class="field">
              <label>HA-Steuerung erlauben</label>
              <div class="toggle-row">
                <label class="toggle" :class="{ disabled: !form.ha_token_set && !form.ha_token }">
                  <input type="checkbox" v-model="form.jarvis_ha_control"
                    :disabled="!form.ha_token_set && !form.ha_token" />
                  <span class="toggle-slider"></span>
                </label>
                <span class="field-hint" v-if="!form.ha_token_set && !form.ha_token">
                  Erfordert einen HA-Token
                </span>
                <span class="field-hint" v-else>
                  Jarvis darf Geräte in HA steuern
                </span>
              </div>
            </div>

            <div class="field">
              <label>Ollama URL</label>
              <div class="token-row">
                <input v-model="form.jarvis_ollama_url" class="input" placeholder="http://192.168.0.220:11434" @blur="loadOllamaModels" />
                <button class="icon-btn" @click="loadOllamaModels" title="Modelle laden">
                  <MdiIcon :icon="loadingModels ? 'mdi:loading' : 'mdi:refresh'" :size="18" />
                </button>
              </div>
              <div v-if="modelsError" class="token-status err">{{ modelsError }}</div>
            </div>

            <div class="field">
              <label>Standard-Modell</label>
              <select v-if="availableModels.length" v-model="form.jarvis_model" class="input">
                <option value="">-- Modell wählen --</option>
                <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <input v-else v-model="form.jarvis_model" class="input" placeholder="z.B. llama3.1:8b" />
            </div>

            <div class="field">
              <label>Temperatur <span class="field-hint">(0 = präzise, 2 = kreativ)</span></label>
              <input v-model.number="form.jarvis_temperature" class="input" type="number" min="0" max="2" step="0.1" placeholder="0.7" />
            </div>

            <div class="field">
              <label>Max. Token <span class="field-hint">(Antwortlänge)</span></label>
              <input v-model.number="form.jarvis_max_tokens" class="input" type="number" min="256" max="8192" step="256" placeholder="2048" />
            </div>

            <div class="field">
              <label>System-Prompt <span class="field-hint">(optional)</span></label>
              <textarea v-model="form.jarvis_system_prompt" class="input" rows="4"
                placeholder="Du bist ein intelligenter Smart Home Assistent. Antworte auf Deutsch, praezise und hilfreich. Keine Emojis." />
            </div>
          </div>

        </div>

        <div class="modal-footer">
          <span v-if="saved" class="saved-msg">
            <MdiIcon icon="mdi:check" :size="16" /> Gespeichert
          </span>
          <button class="btn-save" :disabled="saving" @click="save">
            {{ saving ? 'Speichern…' : 'Speichern' }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'

const emit = defineEmits(['close'])

const form = ref({
  title: '',
  theme: 'dark',
  ha_token: '',
  ha_token_set: false,
  show_clock: true,
  show_weather: false,
  weather_entity: '',
  ki_name: 'Jarvis',
  jarvis_ollama_url: '',
  jarvis_model: '',
  jarvis_temperature: 0.7,
  jarvis_max_tokens: 2048,
  jarvis_system_prompt: '',
  jarvis_ha_control: false,
})

const showToken      = ref(false)
const availableModels = ref([])
const loadingModels   = ref(false)
const modelsError     = ref('')
const saving         = ref(false)
const saved          = ref(false)
const iconRegistered = ref(null)
const tokenError     = ref('')

async function loadOllamaModels() {
  const url = form.value.jarvis_ollama_url?.trim()
  if (!url) return
  loadingModels.value = true
  modelsError.value   = ''
  try {
    // Erst speichern damit Backend die URL kennt
    await fetch('api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jarvis_ollama_url: url }),
    })
    const r = await fetch('api/jarvis/models')
    const d = await r.json()
    if (d.models) {
      availableModels.value = d.models
      if (!form.value.jarvis_model && d.models.length) {
        form.value.jarvis_model = d.models[0]
      }
    } else {
      modelsError.value = d.error || 'Fehler beim Laden'
    }
  } catch(e) {
    modelsError.value = 'Ollama nicht erreichbar'
  } finally {
    loadingModels.value = false
  }
}

async function load() {
  const r = await fetch('api/settings')
  const d = await r.json()
  form.value = { ...form.value, ...d }
}

function clearToken() {
  form.value.ha_token = ''
  form.value.ha_token_set = false
}

async function validateToken(token) {
  if (!token) return false
  try {
    const r = await fetch('api/validate-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })
    const d = await r.json()
    return d.ok === true
  } catch(e) { return false }
}

async function save() {
  saving.value = true
  saved.value  = false
  // Token validieren wenn neu eingetragen
  if (form.value.ha_token && !form.value.ha_token_set) {
    const valid = await validateToken(form.value.ha_token)
    if (!valid) {
      tokenError.value = 'Token ungültig — bitte prüfen'
      saving.value = false
      return
    }
    tokenError.value = ''
  }
  try {
    const r = await fetch('api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title:                form.value.title,
        theme:                form.value.theme,
        ha_token:             form.value.ha_token,
        show_clock:           form.value.show_clock,
        show_weather:         form.value.show_weather,
        weather_entity:       form.value.weather_entity,
        ki_name:              form.value.ki_name,
        jarvis_ollama_url:    form.value.jarvis_ollama_url,
        jarvis_model:         form.value.jarvis_model,
        jarvis_temperature:   form.value.jarvis_temperature,
        jarvis_max_tokens:    form.value.jarvis_max_tokens,
        jarvis_system_prompt: form.value.jarvis_system_prompt,
        jarvis_ha_control:    form.value.jarvis_ha_control,
      }),
    })
    const d = await r.json()
    if (d.ok) {
      saved.value = true
      setTimeout(() => saved.value = false, 3000)
      await testIconRegistration()
      await load()
    }
  } finally {
    saving.value = false
  }
}

async function testIconRegistration() {
  try {
    const r = await fetch('api/register-icon', { method: 'POST' })
    const d = await r.json()
    iconRegistered.value = d.ok === true
  } catch(e) {
    iconRegistered.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000; backdrop-filter: blur(4px);
}
.settings-modal {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; width: min(560px, 95vw);
  max-height: 90vh; display: flex; flex-direction: column;
  box-shadow: 0 24px 64px rgba(0,0,0,.5);
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.modal-title { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 600; }
.close-btn { padding: 6px; border-radius: 8px; border: none; background: transparent; color: var(--muted); cursor: pointer; }
.close-btn:hover { background: var(--border); }

.modal-body { overflow-y: auto; padding: 16px 20px; flex: 1; display: flex; flex-direction: column; gap: 16px; }

.modal-footer {
  padding: 14px 20px; border-top: 1px solid var(--border);
  display: flex; align-items: center; justify-content: flex-end; gap: 12px; flex-shrink: 0;
}
.saved-msg { display: flex; align-items: center; gap: 4px; font-size: 13px; color: var(--green); }
.btn-save {
  padding: 9px 20px; border-radius: 8px; border: none;
  background: var(--accent); color: #fff; cursor: pointer; font-size: 13px; font-weight: 500;
}
.btn-save:disabled { opacity: .5; cursor: default; }

.settings-card {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px; display: flex; flex-direction: column; gap: 14px;
}
.card-title { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; }
.card-desc { font-size: 12px; color: var(--muted); line-height: 1.6; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; color: var(--muted); font-weight: 500; }
.field-hint { font-size: 10px; color: var(--muted); font-weight: 400; }

.input {
  padding: 9px 12px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); font-size: 13px; outline: none; flex: 1;
  font-family: inherit;
}
.input:focus { border-color: var(--accent); }

.radio-group { display: flex; gap: 16px; }
.radio-label { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }

.token-row { display: flex; gap: 8px; align-items: center; }
.icon-btn {
  padding: 8px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--surface); color: var(--muted); cursor: pointer; flex-shrink: 0;
}
.icon-btn:hover { color: var(--text); border-color: var(--accent); }
.icon-btn.danger:hover { color: var(--red); border-color: var(--red); }

.token-status {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; padding: 6px 10px; border-radius: 6px;
}
.token-status.ok  { color: var(--green); background: color-mix(in srgb, var(--green) 10%, var(--surface)); }
.token-status.err { color: var(--red);   background: color-mix(in srgb, var(--red)   10%, var(--surface)); }
.toggle-row { display: flex; align-items: center; gap: 10px; }
.toggle { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute; cursor: pointer; inset: 0; background: var(--border);
  border-radius: 24px; transition: .2s;
}
.toggle-slider:before {
  position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
  background: white; border-radius: 50%; transition: .2s;
}
.toggle input:checked + .toggle-slider { background: var(--accent); }
.toggle input:checked + .toggle-slider:before { transform: translateX(20px); }
.toggle.disabled { opacity: .4; cursor: not-allowed; }
</style>
