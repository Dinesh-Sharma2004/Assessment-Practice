import { defineConfig } from '@playwright/test'

// The e2e server is started separately in test mode (see README): OA_TEST_MODE=1 gives a fake-clock endpoint.
export default defineConfig({
  testDir: './e2e',
  timeout: 180_000,
  workers: 1,
  use: { baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:8001', headless: true },
})
