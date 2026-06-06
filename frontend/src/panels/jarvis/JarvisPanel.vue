<template>
  <div class="jarvis-panel">

    <!-- Header -->
    <div class="jarvis-header">
      <div class="jarvis-title">
        <MdiIcon icon="mdi:robot" :size="22" color="var(--accent)" />
        <span>{{ kiName }}</span>
        <span class="model-badge" v-if="currentModel">{{ currentModel }}</span>
      </div>
      <div class="jarvis-controls">
        <button class="ctrl-btn" @click="clearChat" title="Chat leeren">
          <MdiIcon icon="mdi:delete-outline" :size="16" />
        </button>
        <button class="ctrl-btn" @click="showConfig = !showConfig" title="Einstellungen">
          <MdiIcon icon="mdi:tune" :size="16" />
        </button>
      </div>
    </div>

    <!-- Inline Config -->
    <div v-if="showConfig" class="jarvis-config">
      <div class="config-row">
        <label>Modell</label>
        <select v-model="currentModel" class="config-select" @change="saveModel">
          <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
        </select>
        <button class="config-btn" @click="loadModels">
          <MdiIcon icon="mdi:refresh" :size="14" />
        </button>
      </div>
      <div v-if="modelsError" class="config-error">{{ modelsError }}</div>
    </div>

    <!-- Messages -->
    <div class="jarvis-messages" ref="messagesEl">
      <div v-if="messages.length === 0" class="jarvis-empty">
        <MdiIcon icon="mdi:robot-outline" :size="48" color="var(--muted)" />
        <p>Hallo! Ich bin {{ kiName }}, dein Smart Home Assistent.<br>Frag mich alles über dein Zuhause.</p>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="message-icon">
          <MdiIcon
            :icon="msg.role === 'user' ? 'mdi:account' : 'mdi:robot'"
            :size="16"
            :color="msg.role === 'user' ? 'var(--muted)' : 'var(--accent)'"
          />
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(msg.content)"></div>
          <div v-if="msg.action" class="message-action">
            <MdiIcon icon="mdi:flash" :size="12" color="var(--amber)" />
            {{ msg.action }}
          </div>
        </div>
      </div>

      <!-- Streaming -->
      <div v-if="streaming" class="message assistant">
        <div class="message-icon">
          <MdiIcon icon="mdi:robot" :size="16" color="var(--accent)" />
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(streamingText)"></div>
          <span class="cursor">▋</span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="jarvis-input-row">
      <textarea
        v-model="inputText"
        class="jarvis-input"
        :placeholder="`Frag ${kiName}… (Enter zum Senden, Shift+Enter für neue Zeile)`"
        rows="1"
        @keydown.enter.exact.prevent="sendMessage"
        @input="autoResize"
        ref="inputEl"
        :disabled="streaming"
      />
      <button
        class="send-btn"
        @click="sendMessage"
        :disabled="!inputText.trim() || streaming"
      >
        <MdiIcon :icon="streaming ? 'mdi:stop' : 'mdi:send'" :size="18" />
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'
import { useDashboardStore } from '../../store/dashboard.js'
import { ref as _ref, onMounted as _om } from 'vue'

const { callService } = useDashboardStore()

const messages     = ref([])
const inputText    = ref('')
const streaming    = ref(false)
const streamingText = ref('')
const showConfig   = ref(false)
const models       = ref([])
const currentModel = ref('')
const modelsError  = ref('')
const messagesEl   = ref(null)
const inputEl      = ref(null)
const kiName       = ref('Jarvis')

async function loadModels() {
  modelsError.value = ''
  try {
    const r = await fetch('api/jarvis/models')
    const d = await r.json()
    if (d.models) {
      models.value = d.models
      if (!currentModel.value && d.models.length > 0) {
        currentModel.value = d.models[0]
      }
    } else {
      modelsError.value = d.error || 'Fehler'
    }
  } catch(e) {
    modelsError.value = `Nicht erreichbar: ${e.message}`
  }
}

function saveModel() {
  localStorage?.setItem?.('jarvis_model', currentModel.value)
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || streaming.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  streaming.value  = true
  streamingText.value = ''
  await scrollToBottom()

  try {
    const r = await fetch('api/jarvis/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        messages: messages.value.map(m => ({ role: m.role, content: m.content })),
        model:    currentModel.value,
      }),
    })

    const reader  = r.body.getReader()
    const decoder = new TextDecoder()
    let fullText  = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const lines = decoder.decode(value).split('\n').filter(Boolean)
      for (const line of lines) {
        try {
          const data = JSON.parse(line)
          if (data.error) {
            streamingText.value = `Fehler: ${data.error}`
            break
          }
          const chunk = data.message?.content || ''
          fullText += chunk
          streamingText.value = fullText
          await scrollToBottom()
        } catch(e) {}
      }
    }

    // Action aus Antwort extrahieren
    const actionMatch = fullText.match(/\{"action":\s*(\{[^}]+\})\}/)
    let actionText = null
    if (actionMatch) {
      try {
        const action = JSON.parse(actionMatch[1])
        await fetch('api/jarvis/action', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(action),
        })
        actionText = `${action.domain}.${action.service}(${action.entity_id || ''})`
      } catch(e) {}
    }

    messages.value.push({
      role:    'assistant',
      content: fullText,
      action:  actionText,
    })

  } catch(e) {
    messages.value.push({
      role:    'assistant',
      content: `Fehler: ${e.message}`,
    })
  } finally {
    streaming.value     = false
    streamingText.value = ''
    await scrollToBottom()
  }
}

function clearChat() {
  messages.value = []
}

function formatMessage(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

onMounted(async () => {
  loadModels()
  const saved = localStorage?.getItem?.('jarvis_model')
  if (saved) currentModel.value = saved
  try {
    const r = await fetch('api/config')
    const d = await r.json()
    if (d.ki_name) kiName.value = d.ki_name
    if (d.jarvis_model && !saved) currentModel.value = d.jarvis_model
  } catch(e) {}
})
</script>

<style scoped>
.jarvis-panel {
  display: flex; flex-direction: column; height: calc(100vh - 140px);
  min-height: 400px;
}

.jarvis-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 0 12px; border-bottom: 1px solid var(--border); margin-bottom: 0;
}
.jarvis-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 16px; font-weight: 600;
}
.model-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 10px;
  background: color-mix(in srgb, var(--accent) 15%, var(--border));
  color: var(--accent); font-weight: 400;
}
.jarvis-controls { display: flex; gap: 6px; }
.ctrl-btn {
  padding: 6px; border-radius: 6px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer;
}
.ctrl-btn:hover { color: var(--text); border-color: var(--accent); }

.jarvis-config {
  padding: 12px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; margin-bottom: 8px; display: flex; flex-direction: column; gap: 8px;
}
.config-row { display: flex; align-items: center; gap: 8px; }
.config-row label { font-size: 12px; color: var(--muted); min-width: 60px; }
.config-select {
  flex: 1; padding: 6px 10px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--bg); color: var(--text); font-size: 13px;
}
.config-btn {
  padding: 6px; border-radius: 6px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer;
}
.config-btn:hover { color: var(--accent); }
.config-error { font-size: 12px; color: var(--red); }

.jarvis-messages {
  flex: 1; overflow-y: auto; padding: 12px 0;
  display: flex; flex-direction: column; gap: 12px;
}

.jarvis-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 12px; color: var(--muted); text-align: center;
  font-size: 14px; line-height: 1.6;
}

.message {
  display: flex; gap: 10px; align-items: flex-start;
}
.message.user { flex-direction: row-reverse; }
.message-icon {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: var(--border);
}
.message-content { max-width: 80%; display: flex; flex-direction: column; gap: 4px; }
.message.user .message-content { align-items: flex-end; }

.message-text {
  padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.6;
  background: var(--surface); border: 1px solid var(--border);
}
.message.user .message-text {
  background: color-mix(in srgb, var(--accent) 15%, var(--surface));
  border-color: var(--accent);
}
.message-text code {
  background: var(--border); padding: 1px 4px; border-radius: 3px; font-size: 12px;
}

.message-action {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; color: var(--amber); padding: 0 4px;
}

.cursor { animation: blink 1s infinite; font-size: 14px; color: var(--accent); }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }

.jarvis-input-row {
  display: flex; gap: 8px; align-items: flex-end;
  padding-top: 12px; border-top: 1px solid var(--border);
}
.jarvis-input {
  flex: 1; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); font-size: 13px;
  resize: none; outline: none; line-height: 1.5; font-family: inherit;
  transition: border-color .15s;
}
.jarvis-input:focus { border-color: var(--accent); }
.jarvis-input:disabled { opacity: .5; }

.send-btn {
  width: 40px; height: 40px; border-radius: 10px; border: none;
  background: var(--accent); color: #fff; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: opacity .15s;
}
.send-btn:disabled { opacity: .4; cursor: default; }
.send-btn:hover:not(:disabled) { opacity: .85; }
</style>
