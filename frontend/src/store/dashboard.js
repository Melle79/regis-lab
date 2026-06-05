import { reactive, computed } from 'vue'

const state = reactive({
  entities:  {},
  connected: false,
  config:    {},
  modules:   [],
  health:    {},
  error:     null,
})

let ws = null

function connect() {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const base = location.pathname.replace(/\/$/, '')
  const wsUrl = `${protocol}://${location.host}${base}/ws`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    state.connected = true
    state.error = null
  }

  ws.onmessage = ({ data }) => {
    const msg = JSON.parse(data)
    if (msg.type === 'state_snapshot') {
      for (const s of msg.data)
        state.entities[s.entity_id] = s
    } else if (msg.type === 'state_changed') {
      state.entities[msg.data.entity_id] = msg.data
    }
  }

  ws.onclose = () => {
    state.connected = false
    setTimeout(connect, 5000)
  }

  ws.onerror = (e) => {
    state.error = 'WebSocket-Fehler'
  }
}

async function loadConfig() {
  try {
    const [rConfig, rModules, rHealth] = await Promise.all([
      fetch('api/config'),
      fetch('api/modules'),
      fetch('api/health'),
    ])
    state.config  = await rConfig.json()
    state.modules = await rModules.json()
    state.health  = await rHealth.json()
  } catch (e) {
    console.error('[Dashboard] Config laden fehlgeschlagen:', e)
  }
}

async function callService(domain, service, data = {}) {
  await fetch('api/entities/service', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain, service, data }),
  })
}

const entityList = computed(() => Object.values(state.entities))

function entitiesByDomain(domain) {
  return entityList.value.filter(e => e.entity_id.startsWith(`${domain}.`))
}

loadConfig()
connect()

export function useDashboardStore() {
  return { state, entityList, entitiesByDomain, callService, connect }
}
