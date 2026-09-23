import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      input: {
        portfolio: 'index.html',
        codebaseDemo: 'codebase-demo/index.html',
      },
    },
  },
  server: {
    proxy: {
      '/api/demo': 'http://127.0.0.1:8001',
    },
  },
})
