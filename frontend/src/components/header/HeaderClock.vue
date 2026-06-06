<template>
  <div class="header-clock" v-if="visible">
    <MdiIcon icon="mdi:clock-outline" :size="14" />
    <span>{{ time }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import MdiIcon from '../MdiIcon.vue'

defineProps({ visible: { type: Boolean, default: true } })

const time = ref('')
let timer = null

function update() {
  const now = new Date()
  time.value = now.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => { update(); timer = setInterval(update, 1000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.header-clock {
  display: flex; align-items: center; gap: 5px;
  font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums;
}
</style>
