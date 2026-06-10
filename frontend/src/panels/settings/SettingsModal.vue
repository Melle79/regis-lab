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
              <div v-else-if="tokenSaved" class="token-status ok">
                <MdiIcon icon="mdi:check-circle" :size="14" />
                Token erfolgreich gespeichert
              </div>
            </div>
          </div>

          <!-- Label-Filter -->
          <div class="settings-card">
            <div class="card-title">
              <MdiIcon icon="mdi:label-off-outline" :size="20" color="var(--accent)" />
              Label-Filter
            </div>
            <p class="card-desc">
              Entitäten mit diesen Labels werden im Dashboard <strong>nicht angezeigt</strong>.
            </p>
            <div class="field">
              <label>Gefilterte Labels</label>
              <div v-if="allLabels.length === 0" class="label-hint">Keine Labels in HA gefunden.</div>
              <div class="label-grid">
                <label v-for="l in allLabels" :key="l.id" class="label-checkbox">
                  <input type="checkbox" :value="l.id" v-model="form.filter_labels" />
                  <span class="label-dot" :style="l.color ? { background: l.color } : {}" />
                  {{ l.name }}
                </label>
              </div>
            </div>
          </div>

          <!-- Morgen-Briefing -->
          <div class="settings-card">
            <div class="card-title">
              <MdiIcon icon="mdi:weather-sunset-up" :size="20" color="var(--accent)" />
              Morgen-Briefing
            </div>
            <p class="card-desc">
              Täglich automatische Zusammenfassung per Push-Nachricht.
            </p>
            <div class="field">
              <label>Aktiviert</label>
              <label class="toggle-label">
                <input type="checkbox" v-model="form.briefing_enabled" class="toggle-input" />
                <span class="toggle-track">
                  <span class="toggle-thumb" />
                </span>
                <span>{{ form.briefing_enabled ? 'Ein' : 'Aus' }}</span>
              </label>
            </div>
            <template v-if="form.briefing_enabled">
            <div class="field">
              <label>Uhrzeit</label>
              <input type="time" v-model="form.briefing_time" class="input" style="width:120px" />
            </div>
            <div class="field">
              <label>Empfänger</label>
              <div v-if="notifyServices.length === 0" class="label-hint">Keine Geräte gefunden.</div>
              <div class="label-grid">
                <label v-for="svc in notifyServices" :key="svc.id" class="label-checkbox">
                  <input type="checkbox"
                    :checked="form.briefing_targets.includes(svc.id)"
                    @change="toggleTarget(svc.id)"
                  />
                  <MdiIcon icon="mdi:cellphone" :size="13" color="var(--accent)" />
                  {{ svc.name }}
                </label>
              </div>
            </div>
            <div class="field">
              <label>Externe HA-URL <small>(optional, für Push-Link)</small></label>
              <input v-model="form.ha_external_url" class="input" placeholder="https://mein-ha.duckdns.org" />
              <div class="field-hint" v-if="form.ha_external_url">Link: {{ form.ha_external_url }}/hassio/ingress/a291494a_regis_lab</div>
            </div>
            <div class="field">
              <button class="btn-test" @click="testBriefing" :disabled="testingBriefing">
                <MdiIcon :icon="testingBriefing ? 'mdi:loading' : 'mdi:send'" :size="14" :class="{ spin: testingBriefing }" />
                {{ testingBriefing ? 'Wird gesendet…' : 'Jetzt testen' }}
              </button>
            </div>
            </template>
          </div>

          <!-- Automations-Vorschläge -->
          <div class="settings-card">
            <div class="card-title">
              <MdiIcon icon="mdi:lightbulb-on" :size="20" color="var(--accent)" />
              Automations-Vorschläge
            </div>
            <p class="card-desc">Jarvis analysiert deine Nutzungsmuster und schlägt neue Automationen vor.</p>
            <div class="field">
              <label>Aktiviert</label>
              <label class="toggle-label">
                <input type="checkbox" v-model="form.suggestions_enabled" class="toggle-input" />
                <span class="toggle-track"><span class="toggle-thumb" /></span>
                <span>{{ form.suggestions_enabled ? 'Ein' : 'Aus' }}</span>
              </label>
            </div>
            <template v-if="form.suggestions_enabled">
            <div class="field">
              <label>Analyse-Uhrzeit</label>
              <input type="time" v-model="form.suggestions_time" class="input" style="width:120px" />
            </div>
            </template>
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
                  {{ form.ki_name || "KI" }} darf Geräte in HA steuern
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

          <!-- Cloud KI -->
          <div class="settings-card">
            <div class="card-title">
              <MdiIcon icon="mdi:cloud-outline" :size="20" color="var(--accent)" />
              Cloud KI
            </div>
            <p class="card-desc">Nutze einen Cloud-KI-Anbieter — direkt oder als Fallback wenn Ollama nicht erreichbar ist.</p>
            <div class="field">
              <label>Anbieter</label>
              <select v-model="form.cloud_provider" class="input" @change="onCloudProviderChange">
                <option value="">— Keinen Cloud-Anbieter nutzen —</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="openai">OpenAI (GPT)</option>
                <option value="google">Google (Gemini)</option>
                <option value="mistral">Mistral</option>
                <option value="groq">Groq</option>
              </select>
            </div>
            <template v-if="form.cloud_provider">
              <div class="field">
                <label>API-Key</label>
                <div class="token-row">
                  <input v-model="form[cloudKeyField]" :type="showCloudKey ? 'text' : 'password'" class="input" :placeholder="cloudKeyPlaceholder" />
                  <button class="btn-eye" @click="showCloudKey = !showCloudKey">
                    <MdiIcon :icon="showCloudKey ? 'mdi:eye-off' : 'mdi:eye'" :size="16" />
                  </button>
                </div>
              </div>
              <div class="field">
                <label>Als primäre KI nutzen</label>
                <div class="toggle-row">
                  <label class="toggle">
                    <input type="checkbox" v-model="form.use_cloud_primary" @change="updateProvider" />
                    <span class="toggle-slider"></span>
                  </label>
                  <span class="field-hint">Cloud-KI statt Ollama als Standard verwenden</span>
                </div>
              </div>
              <div class="field" v-if="!form.use_cloud_primary">
                <label>Als Fallback nutzen</label>
                <div class="toggle-row">
                  <label class="toggle">
                    <input type="checkbox" v-model="form.use_cloud_fallback" @change="updateProvider" />
                    <span class="toggle-slider"></span>
                  </label>
                  <span class="field-hint">Bei Ollama-Ausfall automatisch Cloud-KI nutzen</span>
                </div>
              </div>
            </template>
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
  jarvis_provider: 'ollama',
  use_anthropic_fallback: false,
  use_anthropic_primary: false,
  cloud_provider: '',
  use_cloud_primary: false,
  use_cloud_fallback: false,
  openai_api_key: '',
  google_api_key: '',
  mistral_api_key: '',
  groq_api_key: '',
  anthropic_api_key: '',
  anthropic_api_key_set: false,
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
  filter_labels: ['no-dboard'],
  briefing_enabled: true,
  suggestions_enabled: true,
  suggestions_time: '08:00',
  ha_external_url: '',
  briefing_targets: [],
  briefing_time: '07:00',
})

const showToken       = ref(false)
const availableModels = ref([])
const loadingModels   = ref(false)
const modelsError     = ref('')
const saving          = ref(false)
const saved           = ref(false)
const tokenError      = ref('')
const tokenSaved      = ref(false)
const allLabels       = ref([])
const iconRegistered      = ref(null)
const showCloudKey        = ref(false)
const cloudKeyField = computed(() => {
  const map = { anthropic: 'anthropic_api_key', openai: 'openai_api_key', google: 'google_api_key', mistral: 'mistral_api_key', groq: 'groq_api_key' }
  return map[form.value.cloud_provider] || 'anthropic_api_key'
})
const cloudKeyPlaceholder = computed(() => {
  const map = { anthropic: 'sk-ant-...', openai: 'sk-...', google: 'AIza...', mistral: '...', groq: 'gsk_...' }
  return map[form.value.cloud_provider] || ''
})
const notifyServices  = ref([])

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
  // Token-Feld leer lassen — wird nur befüllt wenn neu eingegeben
  const tokenSet = d.ha_token_set
  delete d.ha_token
  form.value = { ...form.value, ...d }
  form.value.ha_token_set = tokenSet
  // use_anthropic_fallback und use_anthropic_primary aus jarvis_provider ableiten
  form.value.use_anthropic_fallback = d.use_anthropic_fallback || d.jarvis_provider === 'ollama_with_fallback'
  form.value.use_anthropic_primary  = d.jarvis_provider === 'anthropic'
  // Cloud-Provider aus jarvis_provider ableiten
  const cloudProviders = ['anthropic', 'openai', 'google', 'mistral', 'groq']
  const jp = d.jarvis_provider || 'ollama'
  const baseProvider = jp.replace('_fallback', '')
  if (cloudProviders.includes(baseProvider)) {
    form.value.cloud_provider = baseProvider
    form.value.use_cloud_primary = !jp.endsWith('_fallback')
    form.value.use_cloud_fallback = jp.endsWith('_fallback')
  } else {
    form.value.cloud_provider = d.cloud_provider || ''
    form.value.use_cloud_primary = !!d.use_cloud_primary
    form.value.use_cloud_fallback = !!d.use_cloud_fallback
  }
  iconRegistered.value = null  // Reset beim Laden
  // Modelle laden wenn Ollama URL gesetzt
  if (form.value.jarvis_ollama_url) {
    await loadOllamaModels()
  }
  // Labels laden
  try {
    const lr = await fetch('api/settings/labels')
    const ld = await lr.json()
    allLabels.value = ld.labels || []
    if (!form.value.filter_labels) form.value.filter_labels = ld.filter_labels || ['no-dboard']
  } catch(e) {}
  // Notify-Services laden
  try {
    const nr = await fetch('api/settings/notify-services')
    const nd = await nr.json()
    notifyServices.value = nd.services || []
  } catch(e) {}
  // briefing_targets explizit als neues Array setzen (Vue-Reaktivität)
  if (Array.isArray(form.value.briefing_targets)) {
    form.value.briefing_targets = [...form.value.briefing_targets]
  }
}

const testingBriefing = ref(false)

async function testBriefing() {
  testingBriefing.value = true
  try {
    await fetch('api/briefing/send-now', { method: 'POST' })
  } catch(e) {}
  setTimeout(() => testingBriefing.value = false, 3000)
}

function onCloudProviderChange() {
  form.value.use_cloud_primary = false
  form.value.use_cloud_fallback = false
  updateProvider()
}

function updateProvider() {
  const p = form.value.cloud_provider
  if (!p) {
    form.value.jarvis_provider = 'ollama'
  } else if (form.value.use_cloud_primary) {
    form.value.jarvis_provider = p
  } else if (form.value.use_cloud_fallback) {
    form.value.jarvis_provider = p + '_fallback'
  } else {
    form.value.jarvis_provider = 'ollama'
  }
}

function toggleTarget(id) {
  const idx = form.value.briefing_targets.indexOf(id)
  if (idx === -1) {
    form.value.briefing_targets = [...form.value.briefing_targets, id]
  } else {
    form.value.briefing_targets = form.value.briefing_targets.filter(t => t !== id)
  }
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
        ...(form.value.ha_token ? { ha_token: form.value.ha_token } : {}),
        show_clock:           form.value.show_clock,
        show_weather:         form.value.show_weather,
        weather_entity:       form.value.weather_entity,
        ki_name:              form.value.ki_name,
        jarvis_ollama_url:    form.value.jarvis_ollama_url,
        jarvis_model:         form.value.jarvis_model,
        jarvis_temperature:   form.value.jarvis_temperature,
        jarvis_max_tokens:    form.value.jarvis_max_tokens,
        jarvis_system_prompt: form.value.jarvis_system_prompt,
        jarvis_ha_control:    !!form.value.jarvis_ha_control,
        tab_order:            form.value.tab_order,
        filter_labels:        form.value.filter_labels,
        briefing_enabled:     !!form.value.briefing_enabled,
        briefing_targets:     form.value.briefing_targets,
        briefing_time:        form.value.briefing_time,
        suggestions_enabled:  !!form.value.suggestions_enabled,
        suggestions_time:     form.value.suggestions_time,
        ha_external_url:      form.value.ha_external_url,
        jarvis_provider:      form.value.jarvis_provider,
        anthropic_api_key:    form.value.anthropic_api_key,
        use_anthropic_fallback: !!form.value.use_anthropic_fallback,
        cloud_provider:       form.value.cloud_provider,
        use_cloud_primary:    !!form.value.use_cloud_primary,
        use_cloud_fallback:   !!form.value.use_cloud_fallback,
        openai_api_key:       form.value.openai_api_key,
        google_api_key:       form.value.google_api_key,
        mistral_api_key:      form.value.mistral_api_key,
        groq_api_key:         form.value.groq_api_key,
      }),
    })
    const d = await r.json()
    if (d.ok) {
      saved.value = true
      setTimeout(() => saved.value = false, 3000)
      if (form.value.ha_token) {
        tokenSaved.value = true
        setTimeout(() => tokenSaved.value = false, 4000)
      }
      // Kurz warten damit Backend Label-Cache neu aufbauen kann
      setTimeout(async () => await load(), 1000)
    }
  } finally {
    saving.value = false
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
.label-grid { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; }
.label-checkbox { display: flex; align-items: center; gap: 6px; font-size: 12px; cursor: pointer; padding: 4px 10px; border-radius: 7px; border: 1px solid var(--border); background: var(--bg); }
.label-checkbox:hover { border-color: var(--accent); }
.label-checkbox input { cursor: pointer; }
.label-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }
.label-hint { font-size: 12px; color: var(--muted); }
.toggle-label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 13px; }
.toggle-label .toggle-input { display: none; }
.toggle-track {
  width: 40px; height: 22px; border-radius: 11px; background: var(--border);
  display: flex; align-items: center; padding: 2px; transition: background .2s;
}
.toggle-label .toggle-input:checked ~ .toggle-track { background: var(--accent); }
.toggle-thumb {
  width: 18px; height: 18px; border-radius: 50%; background: #fff;
  transition: transform .2s; box-shadow: 0 1px 3px rgba(0,0,0,.2);
}
.toggle-label .toggle-input:checked ~ .toggle-track .toggle-thumb { transform: translateX(18px); }
.btn-test {
  display: flex; align-items: center; gap: 6px; padding: 7px 16px;
  border-radius: 8px; border: 1px solid var(--accent); background: transparent;
  color: var(--accent); cursor: pointer; font-size: 12px;
}
.btn-test:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.btn-test:disabled { opacity: .5; cursor: default; }
/* v4-provider-select */

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
