<template>
  <div class="analyse-panel">

    <!-- Header -->
    <div class="analyse-header">
      <div class="analyse-title">
        <MdiIcon icon="mdi:chart-line" :size="20" color="var(--accent)" />
        Smart Home Analyse
      </div>
      <button class="refresh-btn" @click="runAnalysis" :disabled="loading">
        <MdiIcon :icon="loading ? 'mdi:loading' : 'mdi:refresh'" :size="16" :class="{ spin: loading }" />
        {{ loading ? 'Analysiere…' : 'Analyse starten' }}
      </button>
    </div>

    <!-- Leer -->
    <div v-if="!report && !loading" class="empty-state">
      <MdiIcon icon="mdi:robot-happy-outline" :size="48" color="var(--muted)" />
      <p>Klicke auf "Analyse starten" — Jarvis prüft deinen Smart Home Zustand.</p>
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
        Analyse vom {{ formatDate(report.timestamp) }}
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
            <button class="action-btn" @click="enableAutomation(a.entity_id)">
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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'

const loading     = ref(false)
const loadingStep = ref('Analysiere…')
const report      = ref(null)

async function runAnalysis() {
  loading.value = true
  loadingStep.value = 'Lade Entitäten…'
  report.value  = null
  try {
    const r = await fetch('api/analyse/run', { method: 'POST' })
    const d = await r.json()
    if (d.error) throw new Error(d.error)
    report.value = d
  } catch(e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function enableAutomation(entity_id) {
  await fetch('api/analyse/enable_automation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entity_id }),
  })
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
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
