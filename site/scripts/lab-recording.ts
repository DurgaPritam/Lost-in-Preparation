/**
 * A short recording of the Preparation Lab changing preparations, for review. Needs `npm run serve`.
 * Writes screenshots/lab-preparations.webm (Playwright video) and screenshots/lab-frames/*.png; the frames are joined
 * into screenshots/lab-preparations.gif by scripts/frames-to-gif.py. Everything goes to screenshots/ (git-ignored).
 */
import { chromium, type Page } from '@playwright/test';
import { mkdirSync, renameSync, rmSync } from 'node:fs';

const BASE = process.env.BASE_URL ?? 'http://localhost:4517';
const VIEW = { width: 1280, height: 860 };
const FRAMES = 'screenshots/lab-frames';

async function ready(page: Page) { await page.waitForSelector('[data-engine-status="ready"]', { timeout: 30000 }); }

(async () => {
  rmSync(FRAMES, { recursive: true, force: true });
  mkdirSync(FRAMES, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: VIEW, recordVideo: { dir: 'screenshots/video', size: VIEW } });
  const page = await context.newPage();
  await page.goto(`${BASE}/lab/?plant=Salvia%20sclarea&solvent=water&heat=cold&strained=true&acid=false`);
  await ready(page);
  const top = await page.locator('h1').first().boundingBox();
  await page.mouse.wheel(0, Math.max(0, (top?.y ?? 0) - 24));
  await page.waitForTimeout(400);

  let n = 0;
  let recording = true;
  const grab = (async () => {
    while (recording) {
      await page.screenshot({ path: `${FRAMES}/${String(n++).padStart(4, '0')}.png` });
      await page.waitForTimeout(90);
    }
  })();
  const pause = (ms: number) => page.waitForTimeout(ms);
  const pick = async (name: string) => { await page.getByRole('radio', { name, exact: true }).click(); await ready(page); await pause(1300); };

  await pause(1000);
  await pick('Boiled');
  await pick('Wine');
  await pick('Oil');
  await pick('Vinegar');
  await page.getByRole('switch', { name: /Filtration/ }).click(); await ready(page); await pause(1300);
  await page.getByRole('switch', { name: /modern/i }).click(); await ready(page); await pause(1800);
  recording = false;
  await grab;

  const video = page.video();
  await context.close();
  if (video) renameSync(await video.path(), 'screenshots/lab-preparations.webm');
  rmSync('screenshots/video', { recursive: true, force: true });
  await browser.close();
  console.log(`screenshots/lab-preparations.webm, ${n} frames in ${FRAMES}`);
})();
