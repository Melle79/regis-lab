<template>
  <div class="cline-panel">
    <aside class="cline-list">
      <div class="list-head">
        <strong>Cline-Chats</strong>
        <button class="mini-btn" title="Neu laden" @click="loadChats">⟳</button>
      </div>
      <input v-model="filter" class="list-filter" placeholder="filtern…" />
      <div v-if="error" class="list-error">{{ error }}</div>
      <div
        v-for="c in filtered"
        :key="c.session_id"
        class="chat-item"
        :class="{ active: c.session_id === activeId }"
        @click="openChat(c.session_id, c.title)"
      >
        <div class="chat-title">{{ c.title || c.session_id }}</div>
        <div class="chat-meta">{{ shortDate(c.updated_at) }}<span v-if="c.model"> · {{ c.model }}</span></div>
      </div>
      <div v-if="!chats.length && !error" class="list-empty">Keine Chats gefunden</div>
    </aside>

    <section class="cline-view">
      <div v-if="!activeId" class="view-empty">Links einen Chat auswählen</div>
      <template v-else>
        <header class="view-head">
          <strong>{{ activeTitle }}</strong>
          <span class="view-meta">{{ total }} Nachrichten<span v-if="updated"> · {{ shortDate(updated) }}</span></span>
          <button class="mini-btn" @click="openChat(activeId, activeTitle)">Neu laden</button>
        </header>
        <div class="messages">
          <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
            <div class="msg-role">{{ m.role }}</div>
            <div class="msg-text">{{ m.text }}</div>
          </div>
          <div v-if="!messages.length" class="view-empty">Keine lesbaren Nachrichten</div>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const chats       = ref([])
const filter      = ref('')
const error       = ref('')
const activeId    = ref('')
const activeTitle = ref('')
const messages    = ref([])
const total       = ref(0)
const updated     = ref('')

const filtered = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return chats.value
  return chats.value.filter(c =>
    (c.title || '').toLowerCase().includes(q) || (c.model || '').toLowerCase().includes(q))
})

function shortDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d)) return String(iso).slice(0, 16)
  return d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadChats() {
  error.value = ''
  try {
    const r = await fetch('api/cline/chats')
    const d = await r.json()
    chats.value = d.chats || []
    if (d.error) error.value = d.error
  } catch (e) {
    error.value = `Fehler: ${e.message}`
  }
}

async function openChat(id, title) {
  if (!id) return
  activeId.value = id
  activeTitle.value = title || id
  messages.value = []
  try {
    const r = await fetch(`api/cline/chats/${encodeURIComponent(id)}?limit=30`)
    const d = await r.json()
    if (d.error) { error.value = d.error; return }
    messages.value = d.messages || []
    total.value = d.total_messages || 0
    updated.value = d.updated_at || ''
  } catch (e) {
    error.value = `Fehler: ${e.message}`
  }
}

onMounted(loadChats)
</script>

<style scoped>
.cline-panel {
  display: grid; grid-template-columns: 320px 1fr; height: calc(100vh - 130px);
  border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--bg);
}
.cline-list { border-right: 1px solid var(--border); background: var(--surface); display: flex; flex-direction: column; overflow: hidden; }
.list-head { display: flex; align-items: center; justify-content: space-between; padding: 10px 10px 6px; }
.list-filter { margin: 0 10px 8px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 4px 7px; font-size: 12px; }
.chat-item { padding: 7px 10px; cursor: pointer; border-bottom: 1px solid var(--border); }
.chat-item:hover { background: var(--bg); }
.chat-item.active { background: var(--bg); border-left: 3px solid var(--accent); }
.chat-title { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-meta { font-size: 11px; color: var(--muted); }
.list-error { margin: 6px 10px; font-size: 12px; color: var(--amber); }
.list-empty, .view-empty { padding: 16px; color: var(--muted); font-size: 13px; }
.cline-view { display: flex; flex-direction: column; overflow: hidden; }
.view-head { display: flex; align-items: center; gap: 10px; padding: 10px; border-bottom: 1px solid var(--border); background: var(--surface); }
.view-meta { font-size: 11px; color: var(--muted); margin-left: auto; }
.messages { overflow: auto; padding: 10px; display: flex; flex-direction: column; gap: 10px; }
.msg { border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; background: var(--surface); }
.msg.user { border-left: 3px solid var(--accent); }
.msg-role { font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin-bottom: 4px; }
.msg-text { font-size: 13px; white-space: pre-wrap; word-break: break-word; }
.mini-btn { background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 3px 8px; font-size: 12px; cursor: pointer; }
</style>
