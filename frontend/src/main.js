import { createApp } from 'vue'
import App from './App.vue'
import { useDashboardStore } from './store/dashboard.js'

const app = createApp(App)
app.mount('#app')
