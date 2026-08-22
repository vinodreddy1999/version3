import { existsSync } from 'node:fs'
import { defineConfig, devices } from '@playwright/test'

// Some sandboxes pre-bake a specific Chromium build and block downloading
// the exact revision @playwright/test wants (including its headless-shell
// variant). If that pinned build is present, launch it directly instead of
// letting Playwright pick its default executable; CI has full internet
// access and runs `playwright install` instead, so this path won't exist
// there and normal resolution applies.
const pinnedChromium = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
const launchOptions = existsSync(pinnedChromium) ? { executablePath: pinnedChromium } : {}

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['list']] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], launchOptions } }],
})
