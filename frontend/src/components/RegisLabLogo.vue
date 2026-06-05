<template>
  <div class="regis-lab-logo">
    <svg :width="size" :height="size" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g transform="translate(128, 128)">
        <rect x="-88" y="-88" width="176" height="176" rx="14" fill="#3B82F6" transform="rotate(45)"/>
        <rect x="-74" y="-74" width="148" height="148" rx="10" fill="#0d1f3c" fill-opacity="0.55" transform="rotate(45)"/>
        <line x1="-88" y1="0" x2="88" y2="0" stroke="#93C5FD" stroke-width="2" opacity="0.5" transform="rotate(45)"/>
        <line x1="0" y1="-88" x2="0" y2="88" stroke="#93C5FD" stroke-width="2" opacity="0.5" transform="rotate(45)"/>
        <path d="M0,-52 L-42,-14 L-42,38 L42,38 L42,-14 Z" fill="none" stroke="white" stroke-width="5" stroke-linejoin="round"/>
        <path d="M-42,-14 L0,-52 L42,-14" fill="none" stroke="white" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="-14" y="10" width="28" height="28" rx="3.5" fill="none" stroke="white" stroke-width="4"/>
        <circle cx="0" cy="-88" r="6" fill="white" opacity="0.6" transform="rotate(45)"/>
        <circle cx="88" cy="0" r="6" fill="white" opacity="0.6" transform="rotate(45)"/>
        <circle cx="0" cy="88" r="6" fill="white" opacity="0.6" transform="rotate(45)"/>
        <circle cx="-88" cy="0" r="6" fill="white" opacity="0.6" transform="rotate(45)"/>
      </g>
    </svg>
    <div v-if="showText" class="logo-text">
      <span class="logo-homelab">REGIS</span>
      <span class="logo-melchior">LAB</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  size:     { type: Number, default: 36 },
  showText: { type: Boolean, default: true },
})
</script>

<style scoped>
.regis-lab-logo {
  display: flex; align-items: center; gap: 10px;
}
.logo-text {
  display: flex; flex-direction: column; line-height: 1.1;
}
.logo-homelab {
  font-size: 10px; font-weight: 400; letter-spacing: 2px;
  color: var(--text); opacity: .7;
  font-family: system-ui, sans-serif;
}
.logo-melchior {
  font-size: 14px; font-weight: 700; letter-spacing: 2px;
  color: var(--accent);
  font-family: system-ui, sans-serif;
}
</style>
