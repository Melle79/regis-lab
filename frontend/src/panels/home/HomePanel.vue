<template>
  <div class="home-panel">

    <!-- Begrüßung -->
    <div class="greeting-row">
      <div class="greeting">
        <span class="greeting-text">{{ greeting }}, {{ firstName }}</span>
        <span class="greeting-sub">{{ dateStr }}</span>
      </div>
      <div class="header-weather" v-if="weather">
        <MdiIcon :icon="weatherIcon(weather.state)" :size="22" color="var(--accent)" />
        <span class="weather-temp">{{ weather.attributes?.temperature }}°</span>
        <span class="weather-desc">{{ weather.attributes?.friendly_name || weather.state }}</span>
      </div>
    </div>

    <!-- Status-Kacheln -->
    <div class="status-grid">
      <div class="stat-card">
        <MdiIcon icon="mdi:home-outline" :size="22" color="var(--accent)" />
        <div class="stat-number">{{ personsHome.length }}</div>
        <div class="stat-label">Personen zuhause</div>
        <div class="stat-detail">{{ personsHome.map(p => p.name).join(', ') || '–' }}</div>
      </div>
      <div class="stat-card" :class="offlineCount > 0 ? 'warn' : 'ok'">
        <MdiIcon :icon="offlineCount > 0 ? 'mdi:wifi-off' : 'mdi:wifi-check'" :size="22" />
        <div class="stat-number">{{ offlineCount }}</div>
        <div class="stat-label">Geräte offline</div>
        <div class="stat-detail">{{ offlineCount === 0 ? 'Alles in Ordnung' : 'Prüfe Diagnose' }}</div>
      </div>
      <div class="stat-card">
        <MdiIcon icon="mdi:lightning-bolt" :size="22" color="var(--accent)" />
        <div class="stat-number">{{ lightsOn }}</div>
        <div class="stat-label">Lichter an</div>
        <div class="stat-detail">von {{ lightsTotal }} gesamt</div>
      </div>
      <div class="stat-card">
        <MdiIcon icon="mdi:robot" :size="22" color="var(--accent)" />
        <div class="stat-number">{{ automationsOn }}</div>
        <div class="stat-label">Automationen aktiv</div>
        <div class="stat-detail">von {{ automationsTotal }} gesamt</div>
      </div>
    </div>

    <!-- Zwei Spalten -->
    <div class="two-col">

      <!-- Schnellzugriff: Lichter -->
      <div class="section-card">
        <div class="section-header">
          <MdiIcon icon="mdi:lightbulb-outline" :size="16" color="var(--accent)" />
          Lichter
        </div>
        <div class="quick-list">
          <div v-for="light in topLights" :key="light.entity_id" class="quick-item">
            <MdiIcon
              :icon="light.state === 'on' ? 'mdi:lightbulb' : 'mdi:lightbulb-off-outline'"
              :size="16"
              :color="light.state === 'on' ? '#f59e0b' : 'var(--muted)'"
            />
            <span class="quick-name">{{ light.attributes?.friendly_name || light.entity_id }}</span>
            <button class="toggle-btn" :class="light.state" @click="toggleEntity(light)">
              {{ light.state === 'on' ? 'An' : 'Aus' }}
            </button>
          </div>
          <div v-if="topLights.length === 0" class="empty-hint">Keine Lichter gefunden</div>
        </div>
      </div>

      <!-- Schnellzugriff: Schalter -->
      <div class="section-card">
        <div class="section-header">
          <MdiIcon icon="mdi:toggle-switch-outline" :size="16" color="var(--accent)" />
          Schalter
        </div>
        <div class="quick-list">
          <div v-for="sw in topSwitches" :key="sw.entity_id" class="quick-item">
            <MdiIcon
              :icon="sw.state === 'on' ? 'mdi:toggle-switch' : 'mdi:toggle-switch-off-outline'"
              :size="16"
              :color="sw.state === 'on' ? 'var(--accent)' : 'var(--muted)'"
            />
            <span class="quick-name">{{ sw.attributes?.friendly_name || sw.entity_id }}</span>
            <button class="toggle-btn" :class="sw.state" @click="toggleEntity(sw)">
              {{ sw.state === 'on' ? 'An' : 'Aus' }}
            </button>
          </div>
          <div v-if="topSwitches.length === 0" class="empty-hint">Keine Schalter gefunden</div>
        </div>
      </div>

      <!-- Letzte Diagnose -->
      <div class="section-card" v-if="lastDiagnose">
        <div class="section-header">
          <MdiIcon icon="mdi:stethoscope" :size="16" color="var(--accent)" />
          Letzte Diagnose
          <span class="section-time">{{ formatAge(lastDiagnose.timestamp) }}</span>
        </div>
        <div class="diagnose-row">
          <div class="diag-item" :class="lastDiagnose.counts?.offline > 0 ? 'warn' : 'ok'">
            <MdiIcon icon="mdi:wifi-off" :size="14" />
            {{ lastDiagnose.counts?.offline || 0 }} offline
          </div>
          <div class="diag-item" :class="lastDiagnose.counts?.battery > 0 ? 'warn' : 'ok'">
            <MdiIcon icon="mdi:battery-low" :size="14" />
            {{ lastDiagnose.counts?.battery || 0 }} Akku
          </div>
          <div class="diag-item" :class="lastDiagnose.counts?.errors > 0 ? 'error' : 'ok'">
            <MdiIcon icon="mdi:alert-circle" :size="14" />
            {{ lastDiagnose.counts?.errors || 0 }} Fehler
          </div>
        </div>
        <div v-if="lastDiagnose.summary" class="diag-summary">{{ lastDiagnose.summary.slice(0, 180) }}…</div>
      </div>

      <!-- Jarvis Schnellchat -->
      <div class="section-card jarvis-quick">
        <div class="section-header">
          <MdiIcon icon="mdi:robot" :size="16" color="var(--accent)" />
          {{ kiName }} fragen
        </div>
        <div class="jarvis-messages" ref="msgContainer">
          <div v-for="(m, i) in quickMessages" :key="i" class="qmsg" :class="m.role">
            <span v-html="m.text" />
          </div>
          <div v-if="jarvisLoading" class="qmsg assistant">
            <MdiIcon icon="mdi:loading" :size="14" class="spin" /> Denke nach…
          </div>
        </div>
        <div class="jarvis-input-row">
          <input
            v-model="quickInput"
            class="jarvis-input"
            :placeholder="'Frage ' + kiName + '…'"
            @keydown.enter="sendQuick"
          />
          <button class="jarvis-send" @click="sendQuick" :disabled="jarvisLoading || !quickInput.trim()">
            <MdiIcon icon="mdi:send" :size="15" />
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useDashboardStore } from '../../store/dashboard.js'
import MdiIcon from '../../components/MdiIcon.vue'

const store       = useDashboardStore()
const config      = ref({})
const allStates   = ref([])
const lastDiagnose = ref(null)
const quickMessages = ref([])
const quickInput   = ref('')
const jarvisLoading = ref(false)
const msgContainer  = ref(null)

const kiName = computed(() => config.value.ki_name || 'Jarvis')
const userName = ref('')

async function loadUserName() {
  try {
    const r = await fetch('api/entities?domain=person')
    const persons = await r.json()
    if (Array.isArray(persons) && persons.length > 0) {
      const name = persons[0].attributes?.friendly_name || persons[0].entity_id.split('.')[1]
      userName.value = name.split(' ')[0]
    }
  } catch(e) {}
}

const firstName = computed(() => {
  const name = userName.value || config.value.title || ''
  return name.split(' ')[0] || 'dort'
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Guten Morgen'
  if (h < 18) return 'Guten Tag'
  return 'Guten Abend'
})

const dateStr = computed(() => new Date().toLocaleDateString('de-DE', {
  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
}))

const weather = computed(() => allStates.value.find(s =>
  s.entity_id === (config.value.weather_entity || 'weather.forecast_home')
))

const personsHome = computed(() =>
  allStates.value.filter(s => s.entity_id.startsWith('person.') && s.state === 'home')
    .map(s => ({ name: s.attributes?.friendly_name || s.entity_id, entity_id: s.entity_id }))
)

const lightsOn    = computed(() => allStates.value.filter(s => s.entity_id.startsWith('light.') && s.state === 'on').length)
const lightsTotal = computed(() => allStates.value.filter(s => s.entity_id.startsWith('light.')).length)

const automationsOn    = computed(() => allStates.value.filter(s => s.entity_id.startsWith('automation.') && s.state === 'on').length)
const automationsTotal = computed(() => allStates.value.filter(s => s.entity_id.startsWith('automation.')).length)

const RELEVANT = ['light', 'switch', 'cover', 'climate', 'lock', 'fan', 'media_player']
const offlineCount = computed(() =>
  allStates.value.filter(s => RELEVANT.includes(s.entity_id.split('.')[0]) && ['unavailable', 'unknown'].includes(s.state)).length
)

const topLights = computed(() =>
  allStates.value.filter(s => s.entity_id.startsWith('light.') && s.state !== 'unavailable')
    .sort((a, b) => (b.state === 'on') - (a.state === 'on'))
    .slice(0, 6)
)

const SKIP_SWITCH = ['_config_', 'kamera', 'camera', 'motion', 'bewegung', 'pir', '_led_', 'videoaufnahme', 'gerauscherkennung', 'umdrehen', 'wasserzeichen', 'bewegungsalarm', 'datenschutz', 'music_mode', 'outlet', 'overtemp']

const topSwitches = computed(() =>
  allStates.value.filter(s => s.entity_id.startsWith('switch.') && s.state !== 'unavailable'
    && !SKIP_SWITCH.some(p => s.entity_id.includes(p)))
    .sort((a, b) => (b.state === 'on') - (a.state === 'on'))
    .slice(0, 6)
)

function weatherIcon(state) {
  const icons = {
    sunny: 'mdi:weather-sunny', clear: 'mdi:weather-night',
    cloudy: 'mdi:weather-cloudy', partlycloudy: 'mdi:weather-partly-cloudy',
    rainy: 'mdi:weather-rainy', snowy: 'mdi:weather-snowy',
    windy: 'mdi:weather-windy', fog: 'mdi:weather-fog',
    lightning: 'mdi:weather-lightning', hail: 'mdi:weather-hail',
  }
  return icons[state] || 'mdi:weather-partly-cloudy'
}

function formatAge(ts) {
  if (!ts) return ''
  const diff = Date.now() - new Date(ts).getTime()
  if (diff < 60000) return 'Gerade eben'
  if (diff < 3600000) return Math.floor(diff / 60000) + ' Min. her'
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' Std. her'
  return Math.floor(diff / 86400000) + ' Tage her'
}

async function toggleEntity(entity) {
  const domain = entity.entity_id.split('.')[0]
  const service = entity.state === 'on' ? 'turn_off' : 'turn_on'
  await store.callService(domain, service, { entity_id: entity.entity_id })
  // Optimistisch aktualisieren
  const s = allStates.value.find(s => s.entity_id === entity.entity_id)
  if (s) s.state = entity.state === 'on' ? 'off' : 'on'
}

async function sendQuick() {
  const text = quickInput.value.trim()
  if (!text || jarvisLoading.value) return
  quickInput.value = ''
  quickMessages.value.push({ role: 'user', text })
  jarvisLoading.value = true
  await nextTick()
  if (msgContainer.value) msgContainer.value.scrollTop = 99999

  try {
    // Neuen Chat erstellen
    const chatR = await fetch('api/jarvis/chats', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: text.slice(0, 40) }) })
    const chat  = await chatR.json()
    const resp  = await fetch(`api/jarvis/chats/${chat.id}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, model: config.value.jarvis_model || '' }),
    })
    let answer = ''
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      for (const line of chunk.split('\n')) {
        if (line.startsWith('data: ')) {
          try { answer += JSON.parse(line.slice(6)).token || '' } catch(e) {}
        }
      }
    }
    quickMessages.value.push({ role: 'assistant', text: answer.slice(0, 400) + (answer.length > 400 ? '…' : '') })
  } catch(e) {
    quickMessages.value.push({ role: 'assistant', text: 'Fehler: ' + e.message })
  }
  jarvisLoading.value = false
  await nextTick()
  if (msgContainer.value) msgContainer.value.scrollTop = 99999
}

onMounted(async () => {
  loadUserName()
  try {
    const [cr, sr, dr] = await Promise.all([
      fetch('api/config'),
      fetch('api/entities'),
      fetch('api/analyse/latest'),
    ])
    config.value    = await cr.json()
    const sd        = await sr.json()
    allStates.value = Array.isArray(sd) ? sd : (sd.states || sd.entities || [])
    const dd        = await dr.json()
    if (dd.timestamp) lastDiagnose.value = dd
  } catch(e) {}
})
</script>

<style scoped>
.home-panel { display: flex; flex-direction: column; gap: 16px; padding: 16px; overflow-y: auto; height: 100%; }

.greeting-row { display: flex; align-items: center; justify-content: space-between; }
.greeting { display: flex; flex-direction: column; }
.greeting-text { font-size: 20px; font-weight: 700; }
.greeting-sub  { font-size: 12px; color: var(--muted); margin-top: 2px; }
.header-weather { display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border); }
.weather-temp { font-size: 18px; font-weight: 700; }
.weather-desc { font-size: 12px; color: var(--muted); }

.status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.stat-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 14px 10px; border-radius: 12px; border: 1px solid var(--border);
  background: var(--surface); text-align: center; color: var(--accent);
}
.stat-card.warn  { color: #f59e0b; border-color: color-mix(in srgb, #f59e0b 30%, var(--border)); }
.stat-card.ok    { color: var(--green); border-color: color-mix(in srgb, var(--green) 30%, var(--border)); }
.stat-number { font-size: 26px; font-weight: 700; line-height: 1; }
.stat-label  { font-size: 11px; color: var(--muted); }
.stat-detail { font-size: 10px; color: var(--muted); opacity: .7; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.section-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.section-header {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  font-size: 13px; font-weight: 600; border-bottom: 1px solid var(--border);
}
.section-time { margin-left: auto; font-size: 10px; color: var(--muted); font-weight: 400; }

.quick-list { display: flex; flex-direction: column; }
.quick-item {
  display: flex; align-items: center; gap: 8px; padding: 7px 14px;
  border-bottom: 1px solid var(--border); font-size: 12px;
}
.quick-item:last-child { border-bottom: none; }
.quick-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.toggle-btn {
  padding: 2px 10px; border-radius: 5px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer; font-size: 10px; white-space: nowrap;
}
.toggle-btn.on { background: color-mix(in srgb, var(--accent) 12%, transparent); color: var(--accent); border-color: var(--accent); }
.empty-hint { padding: 10px 14px; font-size: 12px; color: var(--muted); }

.diagnose-row { display: flex; gap: 8px; padding: 10px 14px; }
.diag-item {
  display: flex; align-items: center; gap: 5px; padding: 4px 10px;
  border-radius: 7px; font-size: 11px; border: 1px solid var(--border);
}
.diag-item.ok   { color: var(--green); border-color: color-mix(in srgb, var(--green) 25%, var(--border)); }
.diag-item.warn { color: #f59e0b;      border-color: color-mix(in srgb, #f59e0b 25%, var(--border)); }
.diag-item.error{ color: var(--red);   border-color: color-mix(in srgb, var(--red)   25%, var(--border)); }
.diag-summary { padding: 8px 14px 12px; font-size: 11px; color: var(--muted); line-height: 1.5; }

.jarvis-quick { display: flex; flex-direction: column; }
.jarvis-messages { flex: 1; max-height: 160px; overflow-y: auto; padding: 8px 14px; display: flex; flex-direction: column; gap: 6px; }
.qmsg { font-size: 12px; line-height: 1.5; padding: 5px 10px; border-radius: 8px; max-width: 90%; }
.qmsg.user      { background: var(--accent); color: #fff; align-self: flex-end; }
.qmsg.assistant { background: var(--border); color: var(--text); align-self: flex-start; }
.jarvis-input-row { display: flex; gap: 6px; padding: 8px 12px; border-top: 1px solid var(--border); }
.jarvis-input {
  flex: 1; padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg); color: var(--text); font-size: 12px; outline: none;
}
.jarvis-send {
  padding: 6px 10px; border-radius: 8px; border: none;
  background: var(--accent); color: #fff; cursor: pointer;
}
.jarvis-send:disabled { opacity: .5; cursor: default; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
