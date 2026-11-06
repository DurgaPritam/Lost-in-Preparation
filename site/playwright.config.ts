import { defineConfig, devices } from '@playwright/test';

/** E2E journeys, accessibility (axe) and honesty acceptance checks against the static export (run `npm run build` first). */
export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 60000,
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: { baseURL: 'http://localhost:4517', trace: 'retain-on-failure' },
  webServer: { command: 'node scripts/serve.mjs out 4517', url: 'http://localhost:4517/', reuseExistingServer: !process.env.CI },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile-390', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 }, hasTouch: true } },
  ],
});
