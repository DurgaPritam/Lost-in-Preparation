/**
 * Pitch-video footage: five clean 1920x1080 screen recordings (light theme) of the built site. Needs `npm run serve`.
 *   OUT=~/Desktop/LiP_demo_footage npx tsx scripts/demo-footage.ts
 * Headless Playwright video draws no cursor, so there is no cursor jitter; scrolling is eased (requestAnimationFrame)
 * and every pause is fixed, so pacing is steady and repeatable. Output: <OUT>/<n>-<name>.webm (VP8, as Playwright
 * records it). The first ~0.5 s of each clip is the page settling; trim it in the editor if needed.
 */
import { chromium, type Page } from '@playwright/test';
import { mkdirSync, renameSync, rmSync } from 'node:fs';
import path from 'node:path';

const BASE = process.env.BASE_URL ?? 'http://localhost:4517';
const OUT = process.env.OUT ?? 'screenshots/demo';
const SIZE = { width: 1920, height: 1080 };

async function glide(page: Page, to: number | 'bottom', ms: number) {
  await page.evaluate(async ({ to, ms }) => {
    const target = to === 'bottom' ? document.documentElement.scrollHeight - innerHeight : (to as number);
    const start = scrollY, t0 = performance.now();
    await new Promise<void>((res) => {
      const step = (t: number) => {
        const k = Math.min(1, (t - t0) / ms);
        const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;   // ease in-out
        scrollTo(0, start + (target - start) * e);
        if (k < 1) requestAnimationFrame(step); else res();
      };
      requestAnimationFrame(step);
    });
  }, { to, ms });
}
const top = (page: Page, sel: string) => page.locator(sel).first().evaluate((el) => el.getBoundingClientRect().top + scrollY - 96);
const ready = (page: Page) => page.waitForSelector('[data-engine-status="ready"]', { timeout: 30000 });

const CLIPS: { name: string; url: string; shot: string; run: (p: Page) => Promise<void> }[] = [
  {
    name: 'landing', url: '/', shot: 'Landing: the promise, then the live mini-demo switching cold water to decoction and overlaying the modern method; the three paths.',
    run: async (p) => {
      await ready(p); await p.waitForTimeout(3500);
      await glide(p, await top(p, '[data-engine-status="ready"]'), 1800); await p.waitForTimeout(1500);
      await p.getByRole('radio', { name: 'Decoction' }).click(); await ready(p); await p.waitForTimeout(3500);
      await p.getByLabel('Overlay modern lab method').check(); await p.waitForTimeout(4000);
      await p.getByRole('radio', { name: 'Cold water' }).click(); await ready(p); await p.waitForTimeout(3000);
      await glide(p, (await top(p, 'text=Explore recipes')) - 360, 3500); await p.waitForTimeout(3500);
    },
  },
  {
    name: 'lab', url: '/lab/?plant=Salvia%20sclarea&solvent=water&heat=cold&strained=true&acid=false', shot: 'Preparation Lab: clary sage, cold water → boiled → wine → oil → vinegar, unstrained, then the modern-method overlay; ranges and deltas update live.',
    run: async (p) => {
      await ready(p); await p.waitForTimeout(3000);
      for (const [role, name] of [['radio', 'Boiled'], ['radio', 'Wine'], ['radio', 'Oil'], ['radio', 'Vinegar']] as const) {
        await p.getByRole(role, { name, exact: true }).click(); await ready(p); await p.waitForTimeout(3000);
      }
      await p.getByRole('switch', { name: /Filtration/ }).click(); await ready(p); await p.waitForTimeout(3000);
      await p.getByRole('switch', { name: /modern/i }).click(); await ready(p); await p.waitForTimeout(4000);
      await glide(p, 900, 4000); await p.waitForTimeout(2500);
    },
  },
  {
    name: 'evidence-gap', url: '/evidence-gap/', shot: 'The evidence gap: how rarely modern studies say how they prepared the plant, with intervals, the AI-assisted sensitivity line, and the re-sort.',
    run: async (p) => {
      await p.waitForTimeout(3500);
      await glide(p, await top(p, '#details'), 2500); await p.waitForTimeout(4500);
      await p.getByRole('radio', { name: 'Most reported first' }).click(); await p.waitForTimeout(3500);
      await p.getByRole('radio', { name: 'Least reported first' }).click(); await p.waitForTimeout(2500);
      await glide(p, await top(p, '#match'), 4000); await p.waitForTimeout(4000);
    },
  },
  {
    name: 'case-liquorice', url: '/case/liquorice/', shot: 'The liquorice case study: a slow scroll through the four chapters (the misreading, the evidence, the correction, the new result).',
    run: async (p) => {
      await p.waitForTimeout(3500);
      const h = await p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
      for (let i = 1; i <= 6; i++) { await glide(p, Math.round((h * i) / 6), 3800); await p.waitForTimeout(1800); }
    },
  },
  {
    name: 'lab-planner', url: '/planner/', shot: 'Lab Planner: the suggested re-test panel, the panel-size switch (8 → 4 → 6 → 8), then the quantum benchmark across sizes.',
    run: async (p) => {
      await p.waitForTimeout(3000);
      await glide(p, await top(p, '#optimiser'), 1500); await p.waitForTimeout(1500);
      const size = p.locator('section[aria-labelledby="optimiser"]');
      for (const k of ['4', '6', '8']) { await size.getByRole('radio', { name: k, exact: true }).click(); await p.waitForTimeout(2600); }
      await glide(p, await top(p, '#panel'), 2500); await p.waitForTimeout(2500);
      await glide(p, await top(p, '#bench'), 4500); await p.waitForTimeout(2500);
      const bench = p.locator('section[aria-labelledby="bench"]');
      for (const n of ['12', '16', '8']) { await bench.getByRole('radio', { name: n, exact: true }).click(); await p.waitForTimeout(3000); }
    },
  },
];

(async () => {
  mkdirSync(OUT, { recursive: true });
  const tmp = path.join(OUT, '.tmp');
  const browser = await chromium.launch();
  const lines: string[] = [];
  for (const [i, c] of CLIPS.entries()) {
    rmSync(tmp, { recursive: true, force: true });
    const ctx = await browser.newContext({ viewport: SIZE, deviceScaleFactor: 1, colorScheme: 'light', recordVideo: { dir: tmp, size: SIZE } });
    const page = await ctx.newPage();
    await page.addInitScript('window.__name = (f) => f;'); // tsx's keep-names helper, referenced by evaluated functions
    const t0 = Date.now();
    await page.goto(BASE + c.url, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await c.run(page);
    const secs = (Date.now() - t0) / 1000;
    const v = page.video();
    await ctx.close();
    const file = `${i + 1}-${c.name}.webm`;
    if (v) renameSync(await v.path(), path.join(OUT, file));
    lines.push(`${file}\t${secs.toFixed(0)} s\t${c.url}\t${c.shot}`);
    console.log(file, secs.toFixed(1), 's');
  }
  rmSync(tmp, { recursive: true, force: true });
  await browser.close();
  console.log(lines.join('\n'));
})();
