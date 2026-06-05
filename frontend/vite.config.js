import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: './',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8099',
      '/ws':  { target: 'ws://localhost:8099', ws: true },
    },
  },
})
