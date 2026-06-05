<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title-row">
            <img v-if="device.integration" :src="'api/brand-icon/' + device.integration" width="20" height="20" style="object-fit:contain" @error="$event.target.style.display='none'" />
            <MdiIcon v-else :icon="device.icon || 'mdi:chip'" :size="20" />
            <span class="modal-title">{{ device.name }}</span>
          </div>
          <span class="modal-sub" v-if="device.manufacturer">{{ device.manufacturer }} · {{ device.model }}</span>
        </div>

        <div class="modal-body">
          <label class="field-label">Bereich zuweisen</label>

          <div class="area-option" :class="{ selected: selectedArea === null }" @click="selectedArea = null">
            <MdiIcon icon="mdi:close-circle-outline" :size="16" color="var(--muted)" />
            <span>Kein Bereich</span>
          </div>

          <div
            v-for="area in areas"
            :key="area.area_id"
            class="area-option"
            :class="{ selected: selectedArea === area.area_id }"
            @click="selectedArea = area.area_id"
          >
            <MdiIcon :icon="area.icon || 'mdi:home'" :size="16" :color="selectedArea === area.area_id ? 'var(--accent)' : 'var(--muted)'" />
            <div class="area-option-info">
              <span>{{ area.name }}</span>
              <span v-if="area.floor_name" class="area-floor">{{ area.floor_name }}</span>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="$emit('close')">Abbrechen</button>
          <button class="btn-save" :disabled="saving" @click="save">
            {{ saving ? 'Speichern…' : 'Speichern' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MdiIcon from './MdiIcon.vue'

const props = defineProps({
  device:      { type: Object, required: true },
  currentArea: { type: String, default: null },
})
const emit = defineEmits(['close', 'assigned'])

const areas        = ref([])
const selectedArea = ref(props.currentArea)
const saving       = ref(false)

onMounted(async () => {
  const r = await fetch('api/areas/list')
  areas.value = await r.json()
})

async function save() {
  saving.value = true
  try {
    const r = await fetch('api/areas/assign-device', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        device_id: props.device.device_id,
        area_id:   selectedArea.value,
      }),
    })
    const data = await r.json()
    if (data.ok) {
      emit('assigned', { device_id: props.device.device_id, area_id: selectedArea.value })
      emit('close')
    }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; backdrop-filter: blur(4px);
}
.modal {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; width: min(420px, 92vw);
  max-height: 80vh; display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,.4);
}
.modal-header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--border);
}
.modal-title-row {
  display: flex; align-items: center; gap: 10px;
}
.modal-title { font-size: 15px; font-weight: 600; }
.modal-sub   { font-size: 12px; color: var(--muted); margin-top: 4px; display: block; }

.modal-body {
  padding: 12px 16px;
  overflow-y: auto; flex: 1;
  display: flex; flex-direction: column; gap: 4px;
}
.field-label {
  font-size: 11px; color: var(--muted); text-transform: uppercase;
  letter-spacing: .5px; margin-bottom: 4px; display: block;
}

.area-option {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
  border: 1px solid transparent; transition: all .15s;
}
.area-option:hover { background: color-mix(in srgb, var(--accent) 8%, var(--surface)); }
.area-option.selected {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, var(--surface));
}
.area-option-info { display: flex; flex-direction: column; }
.area-floor { font-size: 10px; color: var(--muted); }

.modal-footer {
  padding: 12px 20px; border-top: 1px solid var(--border);
  display: flex; justify-content: flex-end; gap: 8px;
}
.btn-cancel {
  padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer; font-size: 13px;
}
.btn-cancel:hover { color: var(--text); border-color: var(--text); }
.btn-save {
  padding: 8px 16px; border-radius: 8px; border: none;
  background: var(--accent); color: #fff; cursor: pointer; font-size: 13px; font-weight: 500;
}
.btn-save:hover   { opacity: .9; }
.btn-save:disabled { opacity: .5; cursor: default; }
</style>
