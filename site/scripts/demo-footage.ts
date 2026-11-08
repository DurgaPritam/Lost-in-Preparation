/**
 * Pitch-video footage: five clean 1920x1080 screen recordings (light theme) of the built site. Needs `npm run serve`.
 *   OUT=~/Desktop/LiP_demo_footage npx tsx scripts/demo-footage.ts
 *   ONLY=impact … records one clip; BASE_URL=https://lost-in-preparation.vercel.app records from the live site.
 * Headless Playwright video draws no cursor, so there is no cursor jitter; scrolling is eased (requestAnimationFrame)
 * and every pause is fixed, so pacing is steady and repeatable. Output: <OUT>/<n>-<name>.webm (eight clips) (VP8, as Playwright
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
      await ready(p); await p.waitForTimeout(3000);
      await glide(p, await top(p, '[data-engine-status="ready"]'), 1500); await p.waitForTimeout(1200);
      await p.getByRole('radio', { name: 'Decoction' }).click(); await ready(p); await p.waitForTimeout(3000);
      await p.getByLabel('Overlay modern lab method').check(); await p.waitForTimeout(3500);
      await glide(p, (await top(p, 'text=Explore recipes')) - 360, 3000); await p.waitForTimeout(3000);
    },
  },
  {
    name: 'atlas', url: '/atlas/', shot: 'Recipe Atlas: search “wormwood”, then a liquorice recipe page: the original passage and every extracted field with its quote.',
    run: async (p) => {
      await p.waitForTimeout(2500);
      const q = p.getByPlaceholder(/Try/); await q.click(); await q.pressSequentially('wormwood', { delay: 120 }); await p.waitForTimeout(3500);
      await glide(p, 500, 2000); await p.waitForTimeout(1500);
      await p.goto(BASE + '/recipes/culpeper-1652_herbal_liquoris_006_r00/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2500);
      await glide(p, await top(p, '#passage'), 1800); await p.waitForTimeout(3000);
      await glide(p, await top(p, '#fields'), 2500); await p.waitForTimeout(3500);
    },
  },
  {
    name: 'lab', url: '/lab/?plant=Salvia%20sclarea&solvent=water&heat=cold&strained=true&acid=false', shot: 'Preparation Lab: clary sage, cold water → boiled → wine → oil, unstrained, then the modern-method overlay; ranges update live.',
    run: async (p) => {
      await ready(p); await p.waitForTimeout(2500);
      for (const name of ['Boiled', 'Wine', 'Oil']) { await p.getByRole('radio', { name, exact: true }).click(); await ready(p); await p.waitForTimeout(2600); }
      await p.getByRole('switch', { name: /Filtration/ }).click(); await ready(p); await p.waitForTimeout(2600);
      await p.getByRole('switch', { name: /modern/i }).click(); await ready(p); await p.waitForTimeout(3500);
      await glide(p, 700, 3000); await p.waitForTimeout(2000);
    },
  },
  {
    name: 'evidence-gap', url: '/evidence-gap/', shot: 'The evidence gap: how rarely modern studies say how they prepared the plant, with intervals, and the re-sort.',
    run: async (p) => {
      await p.waitForTimeout(4000);
      await glide(p, await top(p, '#details'), 2500); await p.waitForTimeout(5000);
      await p.getByRole('radio', { name: 'Most reported first' }).click(); await p.waitForTimeout(3500);
      await glide(p, await top(p, '#match'), 3500); await p.waitForTimeout(4000);
    },
  },
  {
    name: 'case-hypotheses', url: '/case/liquorice/', shot: 'The liquorice case study (the correction), then the ranked hypotheses.',
    run: async (p) => {
      await p.waitForTimeout(2500);
      const h = await p.evaluate(() => document.documentElement.scrollHeight - innerHeight);
      for (let i = 1; i <= 3; i++) { await glide(p, Math.round((h * i) / 4), 1800); await p.waitForTimeout(900); }
      await p.goto(BASE + '/hypotheses/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2500);
      await glide(p, 600, 2500); await p.waitForTimeout(2500);
    },
  },
  {
    name: 'docs-quantum', url: '/docs/', shot: 'Methods & data: the pipeline, then “Where quantum helps”: GFN2-xTB quantum chemistry against measured logP, and the QAOA summary.',
    run: async (p) => {
      await p.waitForTimeout(2500);
      await glide(p, await top(p, '#pipeline'), 2000); await p.waitForTimeout(2000);
      await glide(p, await top(p, '#quantum'), 2500); await p.waitForTimeout(7000);
    },
  },
  {
    name: 'planner-quantum', url: '/planner/', shot: 'Lab Planner: the optimiser and panel sizes, the suggested panel, its stability, how it was chosen, then the quantum benchmark at n = 8, 12, 16 and the noise sweep.',
    run: async (p) => {
      await p.waitForTimeout(3000);
      await glide(p, await top(p, '#optimiser'), 1500); await p.waitForTimeout(1500);
      const size = p.locator('section[aria-labelledby="optimiser"]');
      for (const k of ['4', '6', '8']) { await size.getByRole('radio', { name: k, exact: true }).click(); await p.waitForTimeout(2000); }
      await glide(p, await top(p, '#panel'), 2000); await p.waitForTimeout(2500);
      await glide(p, await top(p, '#stable'), 2500); await p.waitForTimeout(2000);
      await p.locator('#how summary').click(); await p.waitForTimeout(500);
      await glide(p, await top(p, '#how'), 1500); await p.waitForTimeout(3500);
      await glide(p, await top(p, '#bench'), 2500); await p.waitForTimeout(3500);
      const bench = p.locator('section[aria-labelledby="bench"]');
      for (const n of ['12', '16', '8']) { await bench.getByRole('radio', { name: n, exact: true }).click(); await p.waitForTimeout(3000); }
      await glide(p, (await top(p, 'text=Under noise')) - 200, 2500); await p.waitForTimeout(4500);
    },
  },
  {
    name: 'impact', url: '/impact/', shot: 'Impact & ethics: who can use the outputs, the proposed preparation reporting checklist, the terms for traditional knowledge, and the plan beyond the hackathon.',
    run: async (p) => {
      await p.waitForTimeout(3000);
      await glide(p, await top(p, '#who'), 2000); await p.waitForTimeout(3500);
      await glide(p, await top(p, '#checklist'), 2500); await p.waitForTimeout(3500);
      await glide(p, await top(p, '#ethics'), 2500); await p.waitForTimeout(3500);
      await glide(p, await top(p, '#scale'), 2500); await p.waitForTimeout(3000);
    },
  },
];

(async () => {
  mkdirSync(OUT, { recursive: true });
  const tmp = path.join(OUT, '.tmp');
  const browser = await chromium.launch();
  const lines: string[] = [];
  for (const [i, c] of CLIPS.entries()) {
    if (process.env.ONLY && !process.env.ONLY.split(',').includes(c.name)) continue;
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
