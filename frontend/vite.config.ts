/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  worker: { format: 'es' },
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },   // dev workflow: API from FastAPI on :8000
  build: { outDir: 'dist', emptyOutDir: true, chunkSizeWarningLimit: 1500 },
  test: { environment: 'jsdom', include: ['src/**/*.test.ts'] },
})
