/**
 * Preparation Lab interaction latency under CPU slowdown (Chrome DevTools CPU throttling: 1x, 2x, 4x).
 * Needs `npm run serve`. Writes lib/engine/latency-report.json (committed: the reported latency numbers come from it).
 *
 * Each step clicks one setting (an in-page el.click(), so no automation round trip is timed) and records:
 *  - feedbackMs: click → the next animation frame after React has committed the change (the UI's response; while the
 *    engine runs, the previous profile stays visible and is marked "updating");
 *  - readyMs: click → the Lab's profile is ready for the new setting (data-engine-status="ready" with the new key);
 *  - the longest main-thread task seen during the step (Long Tasks API; tasks under 50 ms are not reported).
 * "Uncached" steps reach a (species, preparation) the page has not computed yet; "cached" steps return to one it has.
 *
 * Chrome's CPU throttling applies to the page's main thread only: Emulation.setCPUThrottlingRate is rejected for
 * worker targets ("only supported for pages"), and the engine runs in a Web Worker. So feedbackMs and longestTaskMs are
 * measured under the slowdown, while readyMs is measured with the worker at full speed. estReadyMs is therefore an
 * ESTIMATE (heuristic): readyMs + (rate - 1) * workerMs, where workerMs is the worker's own time for the request
 * (data-engine-ms: species fetch, compute and yields), assuming it scales linearly with the slowdown.
 */
import { chromium } from '@playwright/test';
import { writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const BASE = process.env.BASE_URL ?? 'http://localhost:4517';
const RATES = [1, 2, 4];
const REPEATS = Number(process.env.REPEATS ?? 3);
const PLANTS = ['Salvia sclarea', 'Humulus lupulus'];
// From water · cold · strained: five settings never computed on this page, then four returns to computed ones.
const STEPS: [string, 'uncached' | 'cached'][] = [
  ['Boiled', 'uncached'], ['Warm', 'uncached'], ['Wine', 'uncached'], ['Oil', 'uncached'], ['Honey', 'uncached'],
  ['Oil', 'cached'], ['Wine', 'cached'], ['Water', 'cached'], ['Boiled', 'cached'],
];

type Sample = { plant: string; rate: number; repeat: number; step: string; kind: string; feedbackMs: number; readyMs: number; workerMs: number; estReadyMs: number; longestTaskMs: number };

const median = (xs: number[]) => { const s = [...xs].sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const r1 = (x: number) => Math.round(x * 10) / 10;

(async () => {
  const browser = await chromium.launch();
  const chromiumVersion = browser.version();
  const samples: Sample[] = [];
  for (const rate of RATES) {
    for (const plant of PLANTS) {
      for (let repeat = 1; repeat <= REPEATS; repeat++) {
        const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
        const page = await context.newPage();
        await page.addInitScript('window.__name = (f) => f;'); // tsx's keep-names helper, referenced by the evaluated function
        const cdp = await context.newCDPSession(page);
        await cdp.send('Emulation.setCPUThrottlingRate', { rate });
        await page.goto(`${BASE}/lab/?plant=${encodeURIComponent(plant)}&solvent=water&heat=cold&strained=true&acid=false`);
        await page.waitForSelector('[data-engine-status="ready"]', { timeout: 60000 });
        for (const [step, kind] of STEPS) {
          const r = await page.evaluate(async (name) => {
            const host = document.querySelector('[data-engine-status]') as HTMLElement;
            const before = host.dataset.engineKey ?? '';
            const radio = Array.from(document.querySelectorAll<HTMLElement>('[role="radio"]')).find((e) => e.textContent?.trim() === name);
            if (!radio) throw new Error(`no radio ${name}`);
            let longest = 0;
            const po = new PerformanceObserver((l) => { for (const e of l.getEntries()) longest = Math.max(longest, e.duration); });
            try { po.observe({ type: 'longtask', buffered: false }); } catch { /* unsupported */ }
            const t0 = performance.now();
            const feedback = new Promise<number>((res) => {
              // React commits synchronously for a discrete event; the next frame after the click is the first paint of the change.
              requestAnimationFrame(() => setTimeout(() => res(performance.now() - t0), 0));
            });
            const ready = new Promise<number>((res, rej) => {
              const done = () => host.dataset.engineStatus === 'ready' && host.dataset.engineKey !== before;
              if (done()) return res(0);
              const mo = new MutationObserver(() => { if (done()) { mo.disconnect(); res(performance.now() - t0); } });
              mo.observe(host, { attributes: true, attributeFilter: ['data-engine-status', 'data-engine-key'] });
              setTimeout(() => { mo.disconnect(); rej(new Error('timeout')); }, 60000);
            });
            radio.click();
            const [f, d] = await Promise.all([feedback, ready]);
            await new Promise((res) => setTimeout(res, 50));
            po.disconnect();
            return { feedbackMs: f, readyMs: Math.max(f, d), workerMs: Number(host.dataset.engineMs || 0), longestTaskMs: longest };
          }, step);
          samples.push({ plant, rate, repeat, step, kind, ...r, estReadyMs: r.readyMs + (rate - 1) * r.workerMs });
        }
        await context.close();
      }
    }
  }
  await browser.close();

  const summary = RATES.flatMap((rate) => PLANTS.flatMap((plant) => (['uncached', 'cached'] as const).map((kind) => {
    const xs = samples.filter((s) => s.rate === rate && s.plant === plant && s.kind === kind);
    return {
      rate, plant, kind, n: xs.length,
      feedbackMedianMs: r1(median(xs.map((s) => s.feedbackMs))), feedbackMaxMs: r1(Math.max(...xs.map((s) => s.feedbackMs))),
      readyMedianMs: r1(median(xs.map((s) => s.readyMs))), readyMaxMs: r1(Math.max(...xs.map((s) => s.readyMs))),
      workerMedianMs: r1(median(xs.map((s) => s.workerMs))),
      estReadyMedianMs: r1(median(xs.map((s) => s.estReadyMs))), estReadyMaxMs: r1(Math.max(...xs.map((s) => s.estReadyMs))),
      longestTaskMs: r1(Math.max(...xs.map((s) => s.longestTaskMs))),
    };
  })));
  console.table(summary);
  const out = path.resolve(__dirname, '..', 'lib', 'engine', 'latency-report.json');
  writeFileSync(out, JSON.stringify({
    method: 'Chrome CPU throttling via DevTools Emulation.setCPUThrottlingRate on the page (main thread only; Chrome rejects it for workers, so the engine worker runs at full speed and estReadyMs is a heuristic linear estimate). Static build served by scripts/serve.mjs; production bundle. See scripts/lab-latency.ts.',
    machine: { cpu: os.cpus()[0]?.model ?? 'unknown', cores: os.cpus().length, platform: `${os.platform()} ${os.release()}`, node: process.version },
    chromium: chromiumVersion,
    repeats: REPEATS, steps: STEPS, summary, samples: samples.map((s) => ({ ...s, feedbackMs: r1(s.feedbackMs), readyMs: r1(s.readyMs), workerMs: r1(s.workerMs), estReadyMs: r1(s.estReadyMs), longestTaskMs: r1(s.longestTaskMs) })),
    generatedAt: new Date().toISOString(),
  }, null, 2) + '\n');
  console.log(out);
})();
