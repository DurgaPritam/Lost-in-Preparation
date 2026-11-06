// Runs Lighthouse CI against the static export, using Playwright's Chromium so no separate Chrome install is needed.
import { spawnSync } from 'node:child_process';
import { chromium } from '@playwright/test';

const env = { ...process.env, CHROME_PATH: process.env.CHROME_PATH || chromium.executablePath() };
const r = spawnSync('npx', ['lhci', 'autorun', ...process.argv.slice(2)], { stdio: 'inherit', env });
process.exit(r.status ?? 1);
