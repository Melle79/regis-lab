<template>
  <div class="settings-panel">
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
    </div>

    <div class="settings-card">
      <div class="card-title">
        <MdiIcon icon="mdi:key" :size="20" color="var(--accent)" />
        Home Assistant Token
      </div>
      <p class="card-desc">
        Ein <strong>Long-Lived Access Token</strong> erlaubt erweiterte HA-Funktionen
        (z.B. Custom Icons in der Seitenleiste).<br>
        Erstellen unter: <em>HA → Profil → Sicherheit → Langlebige Zugriffstoken</em>
      </p>

      <div class="field">
        <label>Token {{ form.ha_token_set ? '(gesetzt ✓)' : '(nicht gesetzt)' }}</label>
        <div class="token-row">
          <input
            v-model="form.ha_token"
            :type="showToken ? 'text' : 'password'"
            class="input"
            :placeholder="form.ha_token_set ? '••••••••••••••••••••' : 'Token einfügen…'"
          />
          <button class="icon-btn" @click="showToken = !showToken">
            <MdiIcon :icon="showToken ? 'mdi:eye-off' : 'mdi:eye'" :size="18" />
          </button>
          <button v-if="form.ha_token_set" class="icon-btn danger" @click="clearToken">
            <MdiIcon icon="mdi:delete" :size="18" />
          </button>
        </div>
        <div v-if="iconRegistered !== null" :class="['token-status', iconRegistered ? 'ok' : 'err']">
          <MdiIcon :icon="iconRegistered ? 'mdi:check-circle' : 'mdi:alert-circle'" :size="14" />
          {{ iconRegistered ? 'Custom Icon erfolgreich registriert' : 'Icon-Registrierung fehlgeschlagen — Token prüfen' }}
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <span v-if="saved" class="saved-msg">
        <MdiIcon icon="mdi:check" :size="16" /> Gespeichert
      </span>
      <button class="btn-save" :disabled="saving" @click="save">
        {{ saving ? 'Speichern…' : 'Speichern' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MdiIcon from '../components/MdiIcon.vue'

const form          = ref({ title: '', theme: 'dark', ha_token: '', ha_token_set: false })
const showToken     = ref(false)
const saving        = ref(false)
const saved         = ref(false)
const iconRegistered = ref(null)

async function load() {
  const r = await fetch('api/settings')
  const d = await r.json()
  form.value = { ...d }
}

function clearToken() {
  form.value.ha_token = ''
  form.value.ha_token_set = false
}

async function save() {
  saving.value = true
  saved.value  = false
  try {
    const r = await fetch('api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title:    form.value.title,
        theme:    form.value.theme,
        ha_token: form.value.ha_token,
      }),
    })
    const d = await r.json()
    if (d.ok) {
      saved.value = true
      setTimeout(() => saved.value = false, 3000)
      // Icon-Registrierung testen
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
.settings-panel { display: flex; flex-direction: column; gap: 16px; max-width: 600px; }

.settings-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 14px;
}
.card-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 15px; font-weight: 600;
}
.card-desc { font-size: 12px; color: var(--muted); line-height: 1.6; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; color: var(--muted); font-weight: 500; }

.input {
  padding: 9px 12px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg); color: var(--text); font-size: 13px; outline: none; flex: 1;
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

.settings-actions {
  display: flex; align-items: center; justify-content: flex-end; gap: 12px;
}
.saved-msg { display: flex; align-items: center; gap: 4px; font-size: 13px; color: var(--green); }
.btn-save {
  padding: 9px 20px; border-radius: 8px; border: none;
  background: var(--accent); color: #fff; cursor: pointer; font-size: 13px; font-weight: 500;
}
.btn-save:disabled { opacity: .5; cursor: default; }
</style>
