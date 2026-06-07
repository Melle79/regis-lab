<template>
  <div class="jarvis-layout">

    <!-- Seitenleiste: Chat-Liste -->
    <div class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createChat" title="Neuer Chat">
          <MdiIcon icon="mdi:plus" :size="16" />
          <span v-if="!sidebarCollapsed">Neuer Chat</span>
        </button>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          <MdiIcon :icon="sidebarCollapsed ? 'mdi:chevron-right' : 'mdi:chevron-left'" :size="16" />
        </button>
      </div>

      <div class="chat-list" v-if="!sidebarCollapsed">
        <div
          v-for="chat in chats"
          :key="chat.id"
          :class="['chat-item', { active: activeChatId === chat.id }]"
          @click="loadChat(chat.id)"
        >
          <MdiIcon icon="mdi:chat-outline" :size="14" color="var(--muted)" />
          <div class="chat-item-info">
            <div class="chat-item-title">{{ chat.title }}</div>
            <div class="chat-item-meta">{{ chat.message_count }} Nachrichten</div>
          </div>
          <button class="delete-chat-btn" @click.stop="deleteChat(chat.id)" title="Löschen">
            <MdiIcon icon="mdi:delete-outline" :size="13" />
          </button>
        </div>
        <div v-if="chats.length === 0" class="no-chats">Noch keine Chats</div>
      </div>
    </div>

    <!-- Haupt-Chat-Bereich -->
    <div class="chat-main">

      <!-- Header -->
      <div class="chat-header">
        <div class="chat-title-row">
          <MdiIcon icon="mdi:robot" :size="18" color="var(--accent)" />
          <span class="chat-title" v-if="activeChat">
            <input
              v-if="editingTitle"
              v-model="editTitle"
              class="title-input"
              @blur="saveTitle"
              @keydown.enter="saveTitle"
              @keydown.escape="editingTitle = false"
              ref="titleInput"
              autofocus
            />
            <span v-else @dblclick="startEditTitle">{{ activeChat.title }}</span>
          </span>
          <span v-else class="chat-title muted">{{ kiName }}</span>
        </div>
        <div class="chat-header-right">
          <select v-model="currentModel" class="model-select" @change="saveModel">
            <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
            <option v-if="!models.length" value="">Kein Modell</option>
          </select>
          <span class="ha-control-badge" :class="haControl ? 'active' : 'inactive'">
            <MdiIcon :icon="haControl ? 'mdi:home' : 'mdi:home-off'" :size="13" />
            {{ haControl ? 'HA aktiv' : 'HA aus' }}
          </span>
        </div>
      </div>

      <!-- HA-Steuerung Warnung -->
      <div v-if="haControlChanged" class="ha-changed-banner">
        <MdiIcon icon="mdi:information" :size="14" />
        {{ haControlChanged }}
        <button @click="createChat" class="banner-btn">Neuer Chat</button>
        <button @click="haControlChanged = ''" class="banner-close">
          <MdiIcon icon="mdi:close" :size="13" />
        </button>
      </div>

      <!-- Nachrichten -->
      <div class="messages-area" ref="messagesEl">
        <div v-if="!activeChat" class="empty-state">
          <MdiIcon icon="mdi:robot-outline" :size="52" color="var(--muted)" />
          <p>Wähle einen Chat oder erstelle einen neuen.</p>
          <button class="start-btn" @click="createChat">
            <MdiIcon icon="mdi:plus" :size="16" /> Neuer Chat
          </button>
        </div>

        <template v-else>
          <div v-if="activeChat.messages.length === 0" class="empty-state">
            <MdiIcon icon="mdi:chat-outline" :size="52" color="var(--muted)" />
            <p>Hallo! Ich bin {{ kiName }}.<br>Wie kann ich dir helfen?</p>
          </div>

          <div v-for="(msg, i) in activeChat.messages" :key="i" :class="['message', msg.role === 'system' ? 'system' : msg.role]">
            <!-- System-Nachricht -->
            <div v-if="msg.role === 'system'" class="system-msg">
              <MdiIcon icon="mdi:information-outline" :size="13" />
              {{ msg.content }}
              <button class="new-chat-inline" @click="createChat">Neuer Chat</button>
            </div>
            <template v-else>
            <div class="msg-avatar" :title="msg.role === 'assistant' ? (msg.ha_control ? 'HA-Steuerung aktiv' : 'HA-Steuerung inaktiv') : ''">
              <MdiIcon
                :icon="msg.role === 'user' ? 'mdi:account' : 'mdi:robot'"
                :size="15"
                :color="msg.role === 'user' ? 'var(--muted)' : (msg.ha_control ? 'var(--accent)' : 'var(--muted)')"
              />
            </div>
            <div class="msg-content">
              <div class="msg-text" v-html="formatMessage(msg.content)" />
              <div v-if="msg.action" class="msg-action">
                <MdiIcon icon="mdi:flash" :size="11" color="var(--amber)" />
                {{ msg.action }}
              </div>
            </div>
            </template>
          </div>

          <!-- Streaming -->
          <div v-if="streaming" class="message assistant">
            <div class="msg-avatar">
              <MdiIcon icon="mdi:robot" :size="15" :color="haControl ? 'var(--accent)' : 'var(--muted)'" />
            </div>
            <div class="msg-content">
              <div class="msg-text" v-html="formatMessage(streamText)" />
              <span class="cursor">▋</span>
            </div>
          </div>
        </template>
      </div>

      <!-- Upload-Vorschau -->
      <div v-if="uploadedFile" class="upload-preview">
        <MdiIcon icon="mdi:file" :size="14" color="var(--accent)" />
        <span>{{ uploadedFile.name }}</span>
        <button @click="uploadedFile = null">
          <MdiIcon icon="mdi:close" :size="13" />
        </button>
      </div>

      <!-- Input -->
      <div class="input-area" v-if="activeChat">
        <label class="upload-btn" title="Datei hochladen">
          <input type="file" style="display:none" @change="onFileUpload" accept="image/*,.pdf,.txt,.md" />
          <MdiIcon icon="mdi:paperclip" :size="18" />
        </label>
        <textarea
          v-model="inputText"
          class="msg-input"
          :placeholder="`Nachricht an ${kiName}… (Enter senden, Shift+Enter neue Zeile)`"
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @input="autoResize"
          ref="inputEl"
          :disabled="streaming || !activeChat"
        />
        <button class="send-btn" @click="sendMessage" :disabled="!canSend">
          <MdiIcon :icon="streaming ? 'mdi:stop-circle' : 'mdi:send'" :size="18" />
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import MdiIcon from '../../components/MdiIcon.vue'

const chats          = ref([])
const activeChatId   = ref(null)
const activeChat     = ref(null)
const models         = ref([])
const currentModel   = ref('')
const kiName         = ref('Assistent')
const haControl      = ref(false)
const haControlChanged = ref('')
const inputText      = ref('')
const streaming      = ref(false)
const streamText     = ref('')
const uploadedFile   = ref(null)
const sidebarCollapsed = ref(false)
const editingTitle   = ref(false)
const editTitle      = ref('')
const messagesEl     = ref(null)
const inputEl        = ref(null)
const titleInput     = ref(null)

const canSend = computed(() =>
  inputText.value.trim() && !streaming.value && activeChatId.value && currentModel.value
)

// ── Chat-Verwaltung ──────────────────────────────────────────────

async function loadChatList() {
  const r = await fetch('api/jarvis/chats')
  const d = await r.json()
  chats.value = d.chats || []
}

async function createChat() {
  const r = await fetch('api/jarvis/chats', { method: 'POST' })
  const d = await r.json()
  await loadChatList()
  await loadChat(d.id)
  await nextTick()
  inputEl.value?.focus()
}

async function loadChat(id) {
  activeChatId.value = id
  const r = await fetch(`api/jarvis/chats/${id}`)
  activeChat.value = await r.json()
  await scrollToBottom()
}

async function deleteChat(id) {
  await fetch(`api/jarvis/chats/${id}`, { method: 'DELETE' })
  if (activeChatId.value === id) {
    activeChatId.value = null
    activeChat.value   = null
  }
  await loadChatList()
}

function startEditTitle() {
  editTitle.value   = activeChat.value.title
  editingTitle.value = true
  nextTick(() => titleInput.value?.focus())
}

async function saveTitle() {
  if (!activeChatId.value) return
  await fetch(`api/jarvis/chats/${activeChatId.value}`, {
    method:  'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ title: editTitle.value }),
  })
  activeChat.value.title = editTitle.value
  editingTitle.value = false
  await loadChatList()
}

// ── Senden ──────────────────────────────────────────────────────

async function sendMessage() {
  if (!canSend.value) return
  const text = inputText.value.trim()
  inputText.value = ''
  streaming.value = true
  streamText.value = ''

  // Optimistisch zur UI hinzufügen
  activeChat.value.messages.push({ role: 'user', content: text })
  await scrollToBottom()

  try {
    const r = await fetch(`api/jarvis/chats/${activeChatId.value}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text, model: currentModel.value }),
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
          const data  = JSON.parse(line)
          if (data.error) { streamText.value = `Fehler: ${data.error}`; break }
          fullText += data.message?.content || ''
          streamText.value = fullText
          await scrollToBottom()
        } catch(e) {}
      }
    }

    // Antwort zur Chat-History hinzufügen
    activeChat.value.messages.push({ role: 'assistant', content: fullText })
    // Chat-Liste aktualisieren (Titel könnte sich geändert haben)
    await loadChatList()

  } catch(e) {
    activeChat.value.messages.push({ role: 'assistant', content: `Fehler: ${e.message}` })
  } finally {
    streaming.value  = false
    streamText.value = ''
    await scrollToBottom()
  }
}

// ── Hilfsfunktionen ─────────────────────────────────────────────

function onFileUpload(e) {
  uploadedFile.value = e.target.files[0] || null
}

function saveModel() {
  localStorage?.setItem?.('jarvis_model', currentModel.value)
}

function formatMessage(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 140) + 'px'
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value)
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

async function loadModels() {
  try {
    const r = await fetch('api/jarvis/models')
    const d = await r.json()
    if (d.models) {
      models.value = d.models
      const saved = localStorage?.getItem?.('jarvis_model')
      currentModel.value = saved && d.models.includes(saved)
        ? saved
        : (d.models[0] || '')
    }
  } catch(e) {}
}

watch(haControl, async (newVal, oldVal) => {
  if (oldVal !== undefined && newVal !== oldVal && activeChatId.value && activeChat.value) {
    const msg = newVal
      ? 'HA-Steuerung wurde aktiviert. Für beste Ergebnisse wird ein neuer Chat empfohlen.'
      : 'HA-Steuerung wurde deaktiviert. Für beste Ergebnisse wird ein neuer Chat empfohlen.'
    // Als System-Nachricht im Chat anzeigen und speichern
    activeChat.value.messages.push({ role: 'system', content: msg })
    haControlChanged.value = msg
    setTimeout(() => haControlChanged.value = '', 5000)
    // Im Backend speichern
    try {
      await fetch(`api/jarvis/chats/${activeChatId.value}/system-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: msg }),
      })
    } catch(e) {}
  }
})

// haControl alle 5 Sekunden aktualisieren
let configTimer = null
onUnmounted(() => clearInterval(configTimer))

onMounted(async () => {
  configTimer = setInterval(async () => {
    try {
      const r = await fetch('api/config')
      const d = await r.json()
      const newHaControl = d.jarvis_ha_control === true
      if (newHaControl !== haControl.value) {
        haControl.value = newHaControl
      }
    } catch(e) {}
  }, 5000)
  try {
    const r = await fetch('api/config')
    const d = await r.json()
    kiName.value    = d.ki_name || 'Assistent'
    haControl.value = d.jarvis_ha_control === true
  } catch(e) {}
  await loadModels()
  await loadChatList()
  // Letzten Chat laden
  if (chats.value.length > 0)
    await loadChat(chats.value[0].id)
})
</script>

<style scoped>
.jarvis-layout {
  display: flex; height: calc(100vh - 120px); gap: 0; overflow: hidden;
  background: var(--bg); border-radius: 12px; border: 1px solid var(--border);
}

/* Sidebar */
.chat-sidebar {
  width: 240px; flex-shrink: 0; border-right: 1px solid var(--border);
  display: flex; flex-direction: column; transition: width .2s; overflow: hidden;
  background: var(--surface);
}
.chat-sidebar.collapsed { width: 48px; }

.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 8px; border-bottom: 1px solid var(--border); gap: 6px; flex-shrink: 0;
}
.new-chat-btn {
  display: flex; align-items: center; gap: 6px; flex: 1;
  padding: 7px 10px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--bg); color: var(--text); cursor: pointer; font-size: 12px;
  white-space: nowrap; overflow: hidden;
}
.new-chat-btn:hover { border-color: var(--accent); color: var(--accent); }
.collapse-btn {
  padding: 6px; border-radius: 6px; border: none; background: transparent;
  color: var(--muted); cursor: pointer; flex-shrink: 0;
}
.collapse-btn:hover { color: var(--text); }

.chat-list { overflow-y: auto; flex: 1; padding: 6px; display: flex; flex-direction: column; gap: 2px; }
.chat-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  border-radius: 8px; cursor: pointer; transition: background .15s; position: relative;
}
.chat-item:hover { background: var(--border); }
.chat-item.active { background: color-mix(in srgb, var(--accent) 12%, var(--surface)); }
.chat-item-info { flex: 1; overflow: hidden; }
.chat-item-title { font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chat-item-meta  { font-size: 10px; color: var(--muted); }
.delete-chat-btn {
  opacity: 0; padding: 3px; border: none; background: transparent;
  color: var(--muted); cursor: pointer; border-radius: 4px; flex-shrink: 0;
}
.chat-item:hover .delete-chat-btn { opacity: 1; }
.delete-chat-btn:hover { color: var(--red); }
.no-chats { font-size: 12px; color: var(--muted); text-align: center; padding: 20px; }

/* Main */
.chat-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 16px; border-bottom: 1px solid var(--border); flex-shrink: 0;
  background: var(--surface);
}
.chat-title-row { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 14px; }
.title-input {
  font-size: 14px; font-weight: 600; border: none; outline: none;
  background: transparent; color: var(--text); width: 200px;
}
.chat-title.muted { color: var(--muted); font-weight: 400; }
.chat-header-right { display: flex; align-items: center; gap: 8px; }
.model-select {
  font-size: 11px; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--bg); color: var(--text); max-width: 160px;
}
.ha-control-badge {
  display: flex; align-items: center; gap: 4px; font-size: 10px; padding: 3px 8px;
  border-radius: 10px; font-weight: 500;
}
.ha-control-badge.active  { background: color-mix(in srgb, var(--green) 15%, var(--surface)); color: var(--green); }
.ha-control-badge.inactive { background: var(--border); color: var(--muted); }

.messages-area {
  flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px;
}

.empty-state {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 12px; color: var(--muted); text-align: center; font-size: 14px;
}
.start-btn {
  display: flex; align-items: center; gap: 6px; padding: 8px 16px;
  border-radius: 8px; border: 1px solid var(--border); background: var(--surface);
  color: var(--text); cursor: pointer; font-size: 13px;
}
.start-btn:hover { border-color: var(--accent); color: var(--accent); }

.message { display: flex; gap: 10px; align-items: flex-start; }
.message.user { flex-direction: row-reverse; }
.msg-avatar {
  width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; background: var(--border);
}
.msg-content { max-width: 78%; }
.message.user .msg-content { align-items: flex-end; display: flex; flex-direction: column; }
.msg-text {
  padding: 9px 13px; border-radius: 12px; font-size: 13px; line-height: 1.6;
  background: var(--surface); border: 1px solid var(--border);
}
.message.user .msg-text {
  background: color-mix(in srgb, var(--accent) 12%, var(--surface));
  border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
}
.msg-text code { background: var(--border); padding: 1px 4px; border-radius: 3px; font-size: 12px; }
.msg-action { display: flex; align-items: center; gap: 4px; font-size: 10px; color: var(--amber); margin-top: 4px; }
.cursor { animation: blink 1s infinite; color: var(--accent); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

.upload-preview {
  display: flex; align-items: center; gap: 8px; padding: 6px 16px;
  background: color-mix(in srgb, var(--accent) 8%, var(--surface));
  font-size: 12px; color: var(--text);
}
.upload-preview button { border: none; background: transparent; color: var(--muted); cursor: pointer; }

.input-area {
  display: flex; align-items: flex-end; gap: 8px;
  padding: 12px 16px; border-top: 1px solid var(--border); background: var(--surface);
}
.upload-btn {
  padding: 8px; color: var(--muted); cursor: pointer; border-radius: 8px;
  border: 1px solid var(--border); display: flex; align-items: center;
}
.upload-btn:hover { color: var(--accent); border-color: var(--accent); }
.msg-input {
  flex: 1; padding: 9px 12px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--bg); color: var(--text); font-size: 13px; resize: none;
  outline: none; line-height: 1.5; font-family: inherit;
}
.msg-input:focus { border-color: var(--accent); }
.send-btn {
  width: 38px; height: 38px; border-radius: 10px; border: none;
  background: var(--accent); color: #fff; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.send-btn:disabled { opacity: .4; cursor: default; }
.send-btn:hover:not(:disabled) { opacity: .85; }
.ha-changed-banner {
  display: flex; align-items: center; gap: 8px; padding: 8px 16px;
  background: color-mix(in srgb, var(--amber) 12%, var(--surface));
  border-bottom: 1px solid color-mix(in srgb, var(--amber) 30%, var(--border));
  font-size: 12px; color: var(--amber); flex-shrink: 0;
}
.banner-btn {
  padding: 3px 10px; border-radius: 6px; border: 1px solid var(--amber);
  background: transparent; color: var(--amber); cursor: pointer; font-size: 11px; margin-left: 4px;
}
.banner-btn:hover { background: color-mix(in srgb, var(--amber) 15%, transparent); }
.banner-close {
  margin-left: auto; padding: 2px; border: none; background: transparent;
  color: var(--amber); cursor: pointer;
}
.system-msg {
  display: flex; align-items: center; gap: 6px; width: 100%;
  padding: 6px 12px; border-radius: 8px; font-size: 11px;
  background: color-mix(in srgb, var(--amber) 8%, var(--surface));
  border: 1px solid color-mix(in srgb, var(--amber) 25%, var(--border));
  color: var(--amber);
}
.new-chat-inline {
  margin-left: auto; padding: 2px 8px; border-radius: 5px;
  border: 1px solid var(--amber); background: transparent;
  color: var(--amber); cursor: pointer; font-size: 10px;
}
.new-chat-inline:hover { background: color-mix(in srgb, var(--amber) 15%, transparent); }
</style>
