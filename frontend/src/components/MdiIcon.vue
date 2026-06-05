<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    :style="{ display: 'inline-block', verticalAlign: 'middle', color: color || 'currentColor', flexShrink: 0 }"
    aria-hidden="true"
  >
    <path :d="iconPath" fill="currentColor" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'
import * as mdi from '@mdi/js'

const props = defineProps({
  icon:  { type: String, default: 'mdi:help-circle' },
  size:  { type: [Number, String], default: 20 },
  color: { type: String, default: '' },
})

// "mdi:home-outline" → "mdiHomeOutline"
function toMdiKey(icon) {
  if (!icon?.startsWith('mdi:')) return 'mdiHelpCircle'
  return 'mdi' + icon.slice(4)
    .split('-')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join('')
}

const iconPath = computed(() => mdi[toMdiKey(props.icon)] || mdi.mdiHelpCircle)
</script>
