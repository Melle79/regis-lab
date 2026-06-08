<template>
  <div class="analyse-panel">

    <!-- Header -->
    <div class="analyse-header">
      <div class="analyse-title">
        <MdiIcon icon="mdi:stethoscope" :size="20" color="var(--accent)" />
        Smart Home Diagnose
      </div>
      <button class="refresh-btn" @click="runAnalysis" :disabled="loading">
        <MdiIcon :icon="loading ? 'mdi:loading' : 'mdi:refresh'" :size="16" :class="{ spin: loading }" />
        {{ loading ? 'Diagnostiziere…' : 'Diagnose starten' }}
      </button>
    </div>

    <!-- Sub-Tabs -->
    <div class="sub-tabs">
      <button :class="['sub-tab', { active: activeTab === 'status' }]" @click="if (activeTab === 'log') markLogSeen(); activeTab = 'status'">
        <MdiIcon icon="mdi:pulse" :size="14" /> Status
      </button>
      <button :class="['sub-tab', { active: activeTab === 'cleanup' }]" @click="if (activeTab === 'log') markLogSeen(); activeTab = 'cleanup'; loadCleanup()">
        <MdiIcon icon="mdi:broom" :size="14" /> Aufräumen
      </button>
      <button :class="['sub-tab', { active: activeTab === 'log' }]" @click="activeTab = 'log'; loadLog()">
        <MdiIcon icon="mdi:history" :size="14" /> Aktivitäten
        <span v-if="unreadLogCount > 0" class="log-count">{{ unreadLogCount }}</span>
      </button>
    </div>

    <template v-if="activeTab === 'status'">
    <!-- Leer -->
    <div v-if="!report && !loading" class="empty-state">
      <MdiIcon icon="mdi:robot-happy-outline" :size="48" color="var(--muted)" />
      <p>Klicke auf "Diagnose starten" — Jarvis prüft deinen Smart Home Zustand.</p>
    </div>

    <!-- Lädt -->
    <div v-else-if="loading" class="loading-state">
      <MdiIcon icon="mdi:loading" :size="40" color="var(--accent)" class="spin" />
      <p>{{ loadingStep }}</p>
    </div>

    <!-- Bericht -->
    <div v-else-if="report" class="report">

      <div class="report-meta">
        <MdiIcon icon="mdi:clock-outline" :size="13" />
        Diagnose vom {{ formatDate(report.timestamp) }}
      </div>

      <!-- Status-Kacheln -->
      <div class="status-grid">
        <div class="status-card" :class="report.offline.length > 0 ? 'warn' : 'ok'">
          <MdiIcon :icon="report.offline.length > 0 ? 'mdi:wifi-off' : 'mdi:wifi-check'" :size="24" />
          <div class="status-number">{{ report.offline.length }}</div>
          <div class="status-label">Offline / Unavailable</div>
        </div>
        <div class="status-card" :class="report.low_battery.length > 0 ? 'warn' : 'ok'">
          <MdiIcon :icon="report.low_battery.length > 0 ? 'mdi:battery-low' : 'mdi:battery-check'" :size="24" />
          <div class="status-number">{{ report.low_battery.length }}</div>
          <div class="status-label">Niedriger Akku</div>
        </div>
        <div class="status-card" :class="report.disabled_automations.length > 0 ? 'info' : 'ok'">
          <MdiIcon icon="mdi:robot-off" :size="24" />
          <div class="status-number">{{ report.disabled_automations.length }}</div>
          <div class="status-label">Automationen deaktiviert</div>
        </div>
        <div class="status-card" :class="report.errors.length > 0 ? 'error' : 'ok'">
          <MdiIcon :icon="report.errors.length > 0 ? 'mdi:alert-circle' : 'mdi:check-circle'" :size="24" />
          <div class="status-number">{{ report.errors.length }}</div>
          <div class="status-label">Log-Fehler</div>
        </div>
      </div>

      <!-- Trend-Miniatur -->
      <div v-if="trendData.length > 1" class="trend-section">
        <div class="trend-title">
          <MdiIcon icon="mdi:chart-timeline-variant" :size="14" />
          Verlauf (letzte {{ trendData.length }} Messungen)
        </div>
        <div class="trend-bars">
          <div
            v-for="(t, i) in trendData"
            :key="i"
            class="trend-bar-wrap"
            :title="formatDate(t.timestamp) + ': ' + (t.counts?.offline || 0) + ' offline'"
          >
            <div
              class="trend-bar"
              :style="{ height: Math.max(4, Math.min(40, (t.counts?.offline || 0) * 2)) + 'px' }"
              :class="(t.counts?.offline || 0) > 10 ? 'bar-warn' : 'bar-ok'"
            />
          </div>
        </div>
        <div class="trend-labels">
          <span>älter</span>
          <span>jetzt</span>
        </div>
      </div>

      <!-- KI-Zusammenfassung -->
      <div class="ki-summary" v-if="report.summary">
        <div class="ki-summary-header">
          <MdiIcon icon="mdi:robot" :size="16" color="var(--accent)" />
          Jarvis Einschätzung
        </div>
        <div class="ki-summary-text" v-html="formatSummary(report.summary)" />
      </div>

      <!-- Offline -->
      <div v-if="report.offline.length > 0" class="detail-section">
        <div class="detail-header warn">
          <MdiIcon icon="mdi:wifi-off" :size="15" />
          Offline / Unavailable ({{ report.offline.length }})
        </div>
        <div class="detail-list">
          <div v-for="e in report.offline" :key="e.entity_id" class="detail-item">
            <span class="detail-entity">{{ e.name || e.entity_id }}</span>
            <span class="detail-meta">{{ e.entity_id }}</span>
            <span class="state-badge warn">{{ e.state }}</span>
          </div>
        </div>
      </div>

      <!-- Akku -->
      <div v-if="report.low_battery.length > 0" class="detail-section">
        <div class="detail-header warn">
          <MdiIcon icon="mdi:battery-low" :size="15" />
          Niedriger Akku ({{ report.low_battery.length }})
        </div>
        <div class="detail-list">
          <div v-for="e in report.low_battery" :key="e.entity_id" class="detail-item">
            <span class="detail-entity">{{ e.name || e.entity_id }}</span>
            <span class="detail-meta">{{ e.entity_id }}</span>
            <span class="state-badge warn">{{ e.state }}%</span>
          </div>
        </div>
      </div>

      <!-- Deaktivierte Automationen -->
      <div v-if="report.disabled_automations.length > 0" class="detail-section">
        <div class="detail-header info">
          <MdiIcon icon="mdi:robot-off" :size="15" />
          Deaktivierte Automationen ({{ report.disabled_automations.length }})
        </div>
        <div class="detail-list">
          <div v-for="a in report.disabled_automations" :key="a.entity_id" class="detail-item">
            <span class="detail-entity">{{ a.name }}</span>
            <button class="action-btn" @click="enableAutomation(a.entity_id, a.name)">
              <MdiIcon icon="mdi:play" :size="12" /> Aktivieren
            </button>
          </div>
        </div>
      </div>

      <!-- Log-Fehler -->
      <div v-if="report.errors.length > 0" class="detail-section">
        <div class="detail-header error">
          <MdiIcon icon="mdi:alert-circle" :size="15" />
          Log-Fehler ({{ report.errors.length }})
        </div>
        <div class="detail-list">
          <div v-for="(e, i) in report.errors" :key="i" class="detail-item error-item">
            <span class="error-text">{{ e }}</span>
          </div>
        </div>
      </div>

    </div>
      </template>

    <!-- Aufräumen Tab -->
    <template v-if="activeTab === 'cleanup'">
      <div v-if="cleanupLoading" class="loading-state">
        <MdiIcon icon="mdi:loading" :size="36" color="var(--accent)" class="spin" />
        <p>Lade Integrations-Status...</p>
      </div>
      <div v-else class="cleanup-list">
        <div v-for="group in cleanupGroups" :key="group.platform" class="cleanup-group">
          <div class="cleanup-header" @click="toggleCleanupGroup(group.platform)">
            <MdiIcon icon="mdi:puzzle-outline" :size="16" color="var(--accent)" />
            <span class="cleanup-platform">{{ group.platform }}</span>
            <span class="badge warn">{{ group.count }} offline</span>
            <div class="cleanup-actions">
              <button class="ki-btn" @click.stop="suggestCleanup(group)" :disabled="group.suggesting" title="Jarvis um Einschätzung bitten">
                <MdiIcon :icon="group.suggesting ? 'mdi:loading' : 'mdi:robot'" :size="13" :class="{ spin: group.suggesting }" />
                Jarvis
              </button>
              <button class="repair-btn" @click.stop="repairIntegration(group)" :disabled="group.repairing" title="Integration neu laden">
                <MdiIcon :icon="group.repairing ? 'mdi:loading' : 'mdi:reload'" :size="13" :class="{ spin: group.repairing }" />
                Neu laden
              </button>
            </div>
            <MdiIcon :icon="expandedGroups.has(group.platform) ? 'mdi:chevron-up' : 'mdi:chevron-down'" :size="16" color="var(--muted)" />
          </div>
          <div v-if="group.suggestion" class="cleanup-suggestion">
            <MdiIcon icon="mdi:robot" :size="13" color="var(--accent)" />
            {{ group.suggestion }}
          </div>
          <div v-if="expandedGroups.has(group.platform)" class="cleanup-entities">
            <div v-for="e in group.entities.slice(0,10)" :key="e.entity_id" class="cleanup-entity">
              <span class="detail-entity">{{ e.name || e.entity_id }}</span>
              <span class="detail-meta">{{ e.entity_id }}</span>
              <span class="state-badge warn">{{ e.state }}</span>
              <div class="entity-actions">
                <button class="entity-action-btn repair" @click.stop="repairEntity(e, group)" title="Gerät neu starten">
                  <MdiIcon icon="mdi:wrench" :size="12" /> Reparieren
                </button>
                <button class="entity-action-btn ignore" @click.stop="ignoreEntity(e.entity_id, group)" title="Ignorieren">
                  <MdiIcon icon="mdi:eye-off" :size="12" /> Ignorieren
                </button>
              </div>
            </div>
            <div v-if="group.entities.length > 10" class="cleanup-more">+ {{ group.entities.length - 10 }} weitere</div>
          </div>
        </div>
        <div v-if="cleanupGroups.length === 0" class="empty-state">
          <MdiIcon icon="mdi:check-circle" :size="40" color="var(--green)" />
          <p>Keine problematischen Integrationen gefunden!</p>
        </div>
      </div>
    </template>

    <!-- Log Tab -->
    <template v-if="activeTab === 'log'">
      <div class="log-header">
        <span class="log-header-title">{{ logEntries.length }} Einträge</span>
        <button v-if="unreadLogCount > 0" class="mark-all-btn" @click="markAllRead">
          <MdiIcon icon="mdi:check-all" :size="13" /> Alle als gelesen
        </button>
      </div>
      <div v-if="logLoading" class="loading-state">
        <MdiIcon icon="mdi:loading" :size="36" color="var(--accent)" class="spin" />
        <p>Lade Aktivitäten...</p>
      </div>
      <div v-else-if="logEntries.length === 0" class="empty-state">
        <MdiIcon icon="mdi:history" :size="40" color="var(--muted)" />
        <p>Noch keine Aktivitäten aufgezeichnet.</p>
      </div>
      <div v-else class="log-list">
        <div v-for="entry in logEntries" :key="entry.id" class="log-entry" :class="{ undone: entry.undone, 'new-entry': !entry.undone && !readIds.value.has(entry.id) }">
          <div class="log-icon">
            <MdiIcon :icon="logIcon(entry.type)" :size="16" :color="logColor(entry.type)" />
          </div>
          <div class="log-info">
            <div class="log-action">{{ logLabel(entry.type) }}</div>
            <div class="log-entity">{{ entry.name || entry.entity_id }}</div>
            <div class="log-time">{{ formatDate(entry.timestamp) }}</div>
          </div>
          <div class="log-status">
            <span v-if="entry.undone" class="undone-badge">Rückgängig</span>
            <template v-else>
              <button v-if="!readIds.has(entry.id)" class="mark-read-btn" @click.stop="markEntryRead(entry)" title="Als gelesen">
                <MdiIcon icon="mdi:check" :size="13" />
              </button>
              <button v-if="canUndo(entry.type)" class="undo-btn" @click="undoAction(entry)">
                <MdiIcon icon="mdi:undo" :size="13" /> Rückgängig
              </button>
            </template>
          </div>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'

const loading     = ref(false)
const loadingStep = ref('Diagnostiziere…')
const report      = ref(null)
const trendData      = ref([])
const activeTab      = ref('status')
const cleanupGroups  = ref([])
const cleanupLoading = ref(false)
const expandedGroups = ref(new Set())
const logEntries     = ref([])
const logLoading     = ref(false)
const lastSeenLog    = ref(localStorage.getItem('regis_log_seen') || '')
const readIds        = ref(new Set(JSON.parse(localStorage.getItem('regis_log_read') || '[]')))

onMounted(async () => {
  try {
    const r = await fetch('api/analyse/latest')
    const d = await r.json()
    if (d.timestamp) report.value = d
    const tr = await fetch('api/analyse/reports')
    const td = await tr.json()
    trendData.value = (td.reports || []).slice(0, 48).reverse()
  } catch(e) {}
  // Log immer beim Start laden für Badge-Zähler
  loadLog()
})

async function runAnalysis() {
  loading.value = true
  loadingStep.value = 'Lade Entitäten…'
  try {
    const r = await fetch('api/analyse/run', { method: 'POST' })
    const d = await r.json()
    if (d.error) throw new Error(d.error)
    report.value = d
    // Trend aktualisieren
    const tr = await fetch('api/analyse/reports')
    const td = await tr.json()
    trendData.value = (td.reports || []).slice(0, 48).reverse()
  } catch(e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadCleanup() {
  if (cleanupGroups.value.length > 0) return
  cleanupLoading.value = true
  try {
    const r = await fetch('api/analyse/cleanup')
    const d = await r.json()
    cleanupGroups.value = (d.groups || []).map(g => ({ ...g, suggestion: '', suggesting: false, repairing: false }))
  } catch(e) {}
  cleanupLoading.value = false
}

function toggleCleanupGroup(platform) {
  const s = new Set(expandedGroups.value)
  if (s.has(platform)) s.delete(platform)
  else s.add(platform)
  expandedGroups.value = s
}

const unreadLogCount = computed(() => {
  return logEntries.value.filter(e => !e.undone && !readIds.value.has(e.id)).length
})

function markAllRead() {
  const ids = logEntries.value.filter(e => !e.undone).map(e => e.id)
  ids.forEach(id => readIds.value.add(id))
  localStorage.setItem('regis_log_read', JSON.stringify([...readIds.value]))
}

function markEntryRead(entry) {
  readIds.value.add(entry.id)
  localStorage.setItem('regis_log_read', JSON.stringify([...readIds.value]))
}

function markLogSeen() {
  markAllRead()
}

async function loadLog() {
  logLoading.value = true
  try {
    const r = await fetch('api/analyse/log')
    const d = await r.json()
    logEntries.value = d.log || []
  } catch(e) {}
  logLoading.value = false
}

async function undoAction(entry) {
  try {
    await fetch('api/analyse/log/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: entry.id }),
    })
    entry.undone = true
    // Cleanup neu laden wenn nötig
    if (entry.type === 'ignore' || entry.type === 'ignore_group') {
      cleanupGroups.value = []
    }
  } catch(e) {}
}

function canUndo(type) {
  return ['ignore', 'ignore_group', 'enable_automation'].includes(type)
}

function logIcon(type) {
  const icons = {
    ignore: 'mdi:eye-off', ignore_group: 'mdi:eye-off',
    repair: 'mdi:reload', enable_automation: 'mdi:robot',
    repairEntity: 'mdi:wrench',
  }
  return icons[type] || 'mdi:information'
}

function logColor(type) {
  if (type === 'ignore' || type === 'ignore_group') return 'var(--muted)'
  if (type === 'repair' || type === 'repairEntity') return 'var(--green)'
  if (type === 'enable_automation') return 'var(--accent)'
  return 'var(--text)'
}

function logLabel(type) {
  const labels = {
    ignore: 'Entität ignoriert',
    ignore_group: 'Gruppe ignoriert',
    repair: 'Integration neu geladen',
    repairEntity: 'Gerät repariert',
    enable_automation: 'Automation aktiviert',
  }
  return labels[type] || type
}

async function repairEntity(entity, group) {
  // Versuche das Gerät über HA-Services neu zu starten
  try {
    const domain = entity.entity_id.split('.')[0]
    // Für bekannte Domains: reload service aufrufen
    const reloadServices = {
      'switch': 'homeassistant/reload_core_config',
    }
    await fetch('api/analyse/cleanup/repair', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform: group.platform, entity_id: entity.entity_id }),
    })
    entity.repaired = true
    group.suggestion = 'Reparatur-Versuch für ' + (entity.name || entity.entity_id) + ' gestartet. Bitte warte einen Moment.'
  } catch(e) {
    group.suggestion = 'Fehler: ' + e.message
  }
}

async function repairIntegration(group) {
  group.repairing = true
  try {
    const r = await fetch('api/analyse/cleanup/repair', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform: group.platform }),
    })
    const d = await r.json()
    group.suggestion = d.error || ('Integration neu geladen (' + (d.reloaded || 0) + ' Einträge). Bitte warte einen Moment und lade dann die Liste neu.')
  } catch(e) { group.suggestion = 'Fehler: ' + e.message }
  group.repairing = false
  await loadLog()
}

async function ignoreGroup(group) {
  const ids = group.entities.map(e => e.entity_id)
  await fetch('api/analyse/cleanup/ignore', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entity_ids: ids }),
  })
  cleanupGroups.value = cleanupGroups.value.filter(g => g.platform !== group.platform)
  await loadLog()
}

async function ignoreEntity(entity_id, group) {
  await fetch('api/analyse/cleanup/ignore', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entity_ids: [entity_id] }),
  })
  group.entities = group.entities.filter(e => e.entity_id !== entity_id)
  group.count    = group.entities.length
  if (group.entities.length === 0)
    cleanupGroups.value = cleanupGroups.value.filter(g => g.platform !== group.platform)
  await loadLog()
}

async function suggestCleanup(group) {
  group.suggesting = true
  try {
    const r = await fetch('api/analyse/cleanup/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform: group.platform, entities: group.entities }),
    })
    const d = await r.json()
    group.suggestion = d.suggestion || ''
  } catch(e) {}
  group.suggesting = false
}

async function enableAutomation(entity_id, name) {
  await fetch('api/analyse/enable_automation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entity_id, name }),
  })
  logEntries.value = []
  runAnalysis()
}

function formatDate(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function formatSummary(text) {
  return text.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.analyse-panel { display: flex; flex-direction: column; height: 100%; overflow-y: auto; padding: 16px; gap: 16px; }
.analyse-header { display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
.analyse-title { display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 600; }
.refresh-btn {
  display: flex; align-items: center; gap: 7px; padding: 8px 16px;
  border-radius: 9px; border: 1px solid var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent);
  color: var(--accent); cursor: pointer; font-size: 13px; font-weight: 500; transition: all .15s;
}
.refresh-btn:hover:not(:disabled) { background: color-mix(in srgb, var(--accent) 20%, transparent); }
.refresh-btn:disabled { opacity: .5; cursor: default; }
.empty-state, .loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 16px; padding: 60px 20px; color: var(--muted); font-size: 14px; text-align: center;
}
.report { display: flex; flex-direction: column; gap: 14px; }
.report-meta { font-size: 11px; color: var(--muted); display: flex; align-items: center; gap: 5px; }
.status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.status-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 16px 10px; border-radius: 12px; border: 1px solid var(--border);
  background: var(--surface); text-align: center;
}
.status-card.ok  { border-color: color-mix(in srgb, var(--green)  30%, var(--border)); color: var(--green); }
.status-card.warn  { border-color: color-mix(in srgb, #f59e0b 30%, var(--border)); color: #f59e0b; }
.status-card.error { border-color: color-mix(in srgb, var(--red)   30%, var(--border)); color: var(--red); }
.status-card.info  { border-color: color-mix(in srgb, var(--accent) 30%, var(--border)); color: var(--accent); }
.status-number { font-size: 28px; font-weight: 700; line-height: 1; }
.status-label  { font-size: 11px; color: var(--muted); }
.ki-summary {
  background: color-mix(in srgb, var(--accent) 6%, var(--surface));
  border: 1px solid color-mix(in srgb, var(--accent) 20%, var(--border));
  border-radius: 12px; padding: 14px 16px;
}
.ki-summary-header { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: var(--accent); margin-bottom: 8px; }
.ki-summary-text   { font-size: 13px; line-height: 1.6; color: var(--text); }
.detail-section { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.detail-header {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  font-size: 13px; font-weight: 600; background: var(--surface); border-bottom: 1px solid var(--border);
}
.detail-header.warn  { color: #f59e0b; }
.detail-header.error { color: var(--red); }
.detail-header.info  { color: var(--accent); }
.detail-list { display: flex; flex-direction: column; }
.detail-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 14px;
  border-bottom: 1px solid var(--border); font-size: 12px;
}
.detail-item:last-child { border-bottom: none; }
.detail-entity { font-weight: 500; flex: 1; }
.detail-meta   { color: var(--muted); font-family: monospace; font-size: 10px; }
.state-badge   { padding: 2px 7px; border-radius: 5px; font-size: 10px; font-weight: 600; }
.state-badge.warn { background: color-mix(in srgb, #f59e0b 15%, transparent); color: #f59e0b; }
.error-item  { flex-direction: column; align-items: flex-start; gap: 2px; }
.error-text  { font-size: 11px; color: var(--red); font-family: monospace; white-space: pre-wrap; word-break: break-all; }
.action-btn {
  display: flex; align-items: center; gap: 4px; padding: 3px 10px;
  border-radius: 6px; border: 1px solid var(--accent); background: transparent;
  color: var(--accent); cursor: pointer; font-size: 11px; white-space: nowrap;
}
.action-btn:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.trend-section { border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.trend-title { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); margin-bottom: 8px; }
.trend-bars { display: flex; align-items: flex-end; gap: 2px; height: 44px; }
.trend-bar-wrap { flex: 1; display: flex; align-items: flex-end; }
.trend-bar { width: 100%; border-radius: 2px 2px 0 0; min-height: 4px; transition: height .3s; }
.trend-bar.bar-ok   { background: var(--green); opacity: .7; }
.trend-bar.bar-warn { background: #f59e0b; opacity: .8; }
.trend-labels { display: flex; justify-content: space-between; font-size: 10px; color: var(--muted); margin-top: 4px; }
.sub-tabs { display: flex; gap: 4px; flex-shrink: 0; }
.sub-tab {
  display: flex; align-items: center; gap: 6px; padding: 6px 14px;
  border-radius: 8px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 12px; transition: all .15s;
}
.sub-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.cleanup-list { display: flex; flex-direction: column; gap: 8px; }
.cleanup-group { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.cleanup-header {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  background: var(--surface); cursor: pointer;
}
.cleanup-header:hover { background: var(--border); }
.cleanup-platform { font-size: 13px; font-weight: 600; flex: 1; }
.cleanup-actions { display: flex; gap: 4px; }
.ki-btn {
  display: flex; align-items: center; gap: 4px; padding: 3px 10px;
  border-radius: 6px; border: 1px solid var(--accent); background: transparent;
  color: var(--accent); cursor: pointer; font-size: 11px;
}
.ki-btn:disabled { opacity: .5; cursor: default; }
.repair-btn {
  display: flex; align-items: center; gap: 4px; padding: 3px 8px;
  border-radius: 6px; border: 1px solid var(--green); background: transparent;
  color: var(--green); cursor: pointer; font-size: 11px;
}
.repair-btn:disabled { opacity: .5; cursor: default; }
.ignore-btn {
  display: flex; align-items: center; gap: 4px; padding: 3px 8px;
  border-radius: 6px; border: 1px solid var(--muted); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 11px;
}
.ignore-btn:hover { border-color: var(--red); color: var(--red); }
.log-count { background: var(--accent); color: #fff; border-radius: 10px; font-size: 10px; padding: 0 5px; min-width: 16px; text-align: center; }
.log-list { display: flex; flex-direction: column; gap: 4px; }
.log-entry {
  display: flex; align-items: center; gap: 12px; padding: 10px 14px;
  border: 1px solid var(--border); border-radius: 9px; background: var(--surface);
  transition: opacity .2s;
}
.log-entry.undone { opacity: .45; }
.log-icon { flex-shrink: 0; }
.log-info { flex: 1; }
.log-action { font-size: 12px; font-weight: 600; }
.log-entity { font-size: 11px; color: var(--muted); font-family: monospace; }
.log-time { font-size: 10px; color: var(--muted); margin-top: 2px; }
.log-status { flex-shrink: 0; }
.undone-badge { font-size: 10px; color: var(--muted); padding: 2px 7px; border-radius: 5px; background: var(--border); }
.undo-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px;
  border-radius: 6px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 11px;
}
.undo-btn:hover { color: var(--accent); border-color: var(--accent); }
.log-header { display: flex; align-items: center; justify-content: space-between; padding: 4px 0 8px; flex-shrink: 0; }
.log-header-title { font-size: 12px; color: var(--muted); }
.mark-all-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 12px;
  border-radius: 7px; border: 1px solid var(--accent); background: transparent;
  color: var(--accent); cursor: pointer; font-size: 11px;
}
.mark-all-btn:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.mark-read-btn {
  padding: 3px 6px; border-radius: 5px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer;
}
.mark-read-btn:hover { color: var(--accent); border-color: var(--accent); }
.new-entry {
  background: color-mix(in srgb, var(--accent) 6%, var(--surface));
  border-color: color-mix(in srgb, var(--accent) 25%, var(--border));
}
.new-entry .log-action::after {
  content: ' •';
  color: var(--accent);
  font-size: 14px;
}
.entity-actions { display: flex; gap: 4px; margin-left: auto; opacity: 0; transition: opacity .15s; }
.cleanup-entity:hover .log-count { background: var(--accent); color: #fff; border-radius: 10px; font-size: 10px; padding: 0 5px; min-width: 16px; text-align: center; }
.log-list { display: flex; flex-direction: column; gap: 4px; }
.log-entry {
  display: flex; align-items: center; gap: 12px; padding: 10px 14px;
  border: 1px solid var(--border); border-radius: 9px; background: var(--surface);
  transition: opacity .2s;
}
.log-entry.undone { opacity: .45; }
.log-icon { flex-shrink: 0; }
.log-info { flex: 1; }
.log-action { font-size: 12px; font-weight: 600; }
.log-entity { font-size: 11px; color: var(--muted); font-family: monospace; }
.log-time { font-size: 10px; color: var(--muted); margin-top: 2px; }
.log-status { flex-shrink: 0; }
.undone-badge { font-size: 10px; color: var(--muted); padding: 2px 7px; border-radius: 5px; background: var(--border); }
.undo-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px;
  border-radius: 6px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 11px;
}
.undo-btn:hover { color: var(--accent); border-color: var(--accent); }
.log-header { display: flex; align-items: center; justify-content: space-between; padding: 4px 0 8px; flex-shrink: 0; }
.log-header-title { font-size: 12px; color: var(--muted); }
.mark-all-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 12px;
  border-radius: 7px; border: 1px solid var(--accent); background: transparent;
  color: var(--accent); cursor: pointer; font-size: 11px;
}
.mark-all-btn:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.mark-read-btn {
  padding: 3px 6px; border-radius: 5px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer;
}
.mark-read-btn:hover { color: var(--accent); border-color: var(--accent); }
.new-entry {
  background: color-mix(in srgb, var(--accent) 6%, var(--surface));
  border-color: color-mix(in srgb, var(--accent) 25%, var(--border));
}
.new-entry .log-action::after {
  content: ' •';
  color: var(--accent);
  font-size: 14px;
}
.entity-actions { opacity: 1; }
.entity-action-btn {
  display: flex; align-items: center; gap: 3px; padding: 2px 8px;
  border-radius: 5px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 10px; white-space: nowrap;
}
.entity-action-btn.repair:hover { color: var(--green); border-color: var(--green); }
.entity-action-btn.ignore:hover { color: var(--red); border-color: var(--red); }
.ignore-btn-sm {
  padding: 2px 4px; border-radius: 4px; border: none; background: transparent;
  color: var(--muted); cursor: pointer; opacity: 0; transition: opacity .15s;
}
.cleanup-entity:hover .log-count { background: var(--accent); color: #fff; border-radius: 10px; font-size: 10px; padding: 0 5px; min-width: 16px; text-align: center; }
.log-list { display: flex; flex-direction: column; gap: 4px; }
.log-entry {
  display: flex; align-items: center; gap: 12px; padding: 10px 14px;
  border: 1px solid var(--border); border-radius: 9px; background: var(--surface);
  transition: opacity .2s;
}
.log-entry.undone { opacity: .45; }
.log-icon { flex-shrink: 0; }
.log-info { flex: 1; }
.log-action { font-size: 12px; font-weight: 600; }
.log-entity { font-size: 11px; color: var(--muted); font-family: monospace; }
.log-time { font-size: 10px; color: var(--muted); margin-top: 2px; }
.log-status { flex-shrink: 0; }
.undone-badge { font-size: 10px; color: var(--muted); padding: 2px 7px; border-radius: 5px; background: var(--border); }
.undo-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px;
  border-radius: 6px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 11px;
}
.undo-btn:hover { color: var(--accent); border-color: var(--accent); }
.log-header { display: flex; align-items: center; justify-content: space-between; padding: 4px 0 8px; flex-shrink: 0; }
.log-header-title { font-size: 12px; color: var(--muted); }
.mark-all-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 12px;
  border-radius: 7px; border: 1px solid var(--accent); background: transparent;
  color: var(--accent); cursor: pointer; font-size: 11px;
}
.mark-all-btn:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.mark-read-btn {
  padding: 3px 6px; border-radius: 5px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer;
}
.mark-read-btn:hover { color: var(--accent); border-color: var(--accent); }
.new-entry {
  background: color-mix(in srgb, var(--accent) 6%, var(--surface));
  border-color: color-mix(in srgb, var(--accent) 25%, var(--border));
}
.new-entry .log-action::after {
  content: ' •';
  color: var(--accent);
  font-size: 14px;
}
.entity-actions { display: flex; gap: 4px; margin-left: auto; opacity: 0; transition: opacity .15s; }
.cleanup-entity:hover .log-count { background: var(--accent); color: #fff; border-radius: 10px; font-size: 10px; padding: 0 5px; min-width: 16px; text-align: center; }
.log-list { display: flex; flex-direction: column; gap: 4px; }
.log-entry {
  display: flex; align-items: center; gap: 12px; padding: 10px 14px;
  border: 1px solid var(--border); border-radius: 9px; background: var(--surface);
  transition: opacity .2s;
}
.log-entry.undone { opacity: .45; }
.log-icon { flex-shrink: 0; }
.log-info { flex: 1; }
.log-action { font-size: 12px; font-weight: 600; }
.log-entity { font-size: 11px; color: var(--muted); font-family: monospace; }
.log-time { font-size: 10px; color: var(--muted); margin-top: 2px; }
.log-status { flex-shrink: 0; }
.undone-badge { font-size: 10px; color: var(--muted); padding: 2px 7px; border-radius: 5px; background: var(--border); }
.undo-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px;
  border-radius: 6px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 11px;
}
.undo-btn:hover { color: var(--accent); border-color: var(--accent); }
.log-header { display: flex; align-items: center; justify-content: space-between; padding: 4px 0 8px; flex-shrink: 0; }
.log-header-title { font-size: 12px; color: var(--muted); }
.mark-all-btn {
  display: flex; align-items: center; gap: 4px; padding: 4px 12px;
  border-radius: 7px; border: 1px solid var(--accent); background: transparent;
  color: var(--accent); cursor: pointer; font-size: 11px;
}
.mark-all-btn:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.mark-read-btn {
  padding: 3px 6px; border-radius: 5px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer;
}
.mark-read-btn:hover { color: var(--accent); border-color: var(--accent); }
.new-entry {
  background: color-mix(in srgb, var(--accent) 6%, var(--surface));
  border-color: color-mix(in srgb, var(--accent) 25%, var(--border));
}
.new-entry .log-action::after {
  content: ' •';
  color: var(--accent);
  font-size: 14px;
}
.entity-actions { opacity: 1; }
.entity-action-btn {
  display: flex; align-items: center; gap: 3px; padding: 2px 8px;
  border-radius: 5px; border: 1px solid var(--border); background: transparent;
  color: var(--muted); cursor: pointer; font-size: 10px; white-space: nowrap;
}
.entity-action-btn.repair:hover { color: var(--green); border-color: var(--green); }
.entity-action-btn.ignore:hover { color: var(--red); border-color: var(--red); }
.ignore-btn-sm { opacity: 1; }
.cleanup-suggestion {
  display: flex; align-items: flex-start; gap: 8px; padding: 10px 14px;
  background: color-mix(in srgb, var(--accent) 5%, var(--surface));
  border-top: 1px solid var(--border); font-size: 12px; line-height: 1.5; color: var(--text);
}
.cleanup-entities { padding: 4px 0; border-top: 1px solid var(--border); }
.cleanup-entity {
  display: flex; align-items: center; gap: 8px; padding: 6px 14px;
  font-size: 11px; border-bottom: 1px solid var(--border);
}
.cleanup-entity:last-child { border-bottom: none; }
.cleanup-more { padding: 6px 14px; font-size: 11px; color: var(--muted); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
