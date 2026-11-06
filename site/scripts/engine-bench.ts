/**
 * Engine performance (npm run engine:bench). "Full profile" = one preparation for every compound of a species,
 * including the descriptor-error pass (what the Preparation Lab recomputes on each change). Measured on the largest
 * species, in three cases:
 *   cold     a new Streams cache (random streams generated from the seed)
 *   warm     streams cached (the common case: the user changes a slider, the seed is the same or seen before)
 *   custom   a combination outside the grid with a cold cache (new seed)
 * Run in Node (V8) and in headless Chromium at CPU throttling 1x, 2x, 4x and 6x (Chrome DevTools' emulation). 2x is
 * the closest stand-in here for a mid-range laptop's single-thread speed relative to this machine; 4x is Lighthouse's
 * mid-tier-device setting (a slow device).
 * Writes lib/engine/bench-report.json (committed: the numbers in lib/engine/README.md come from it).
 */
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { build } from 'esbuild';
import { chromium } from '@playwright/test';
import { computeProfile, preparationFor, Streams } from '../lib/engine';
import { loadEngineModel, loadEngineSpecies, loadProfileIndex } from '../lib/data/load';

const RUNS = 25;
const model = loadEngineModel();
const largest = loadProfileIndex().reduce((a, b) => (b.compounds > a.compounds ? b : a));
const species = loadEngineSpecies(largest.speciesId);
const grid = model.preparations.find((p) => p.label === 'decoction in water')!;
const custom = preparationFor(model, { solvents: ['vinegar', 'water'], heat: 'unknown', filtered: 'unknown', process: 'decoction' });

const summarise = (xs: number[]) => {
  const s = [...xs].sort((a, b) => a - b);
  return { median: +s[Math.floor(s.length / 2)].toFixed(2), p95: +s[Math.min(s.length - 1, Math.floor(s.length * 0.95))].toFixed(2), max: +s[s.length - 1].toFixed(2) };
};

function benchNode() {
  for (let i = 0; i < 3; i++) computeProfile(species, grid, model); // JIT warm-up
  const cold: number[] = [], warm: number[] = [], cust: number[] = [];
  const cached = new Streams(model);
  computeProfile(species, grid, model, cached);
  for (let i = 0; i < RUNS; i++) {
    let t = performance.now(); computeProfile(species, grid, model, new Streams(model)); cold.push(performance.now() - t);
    t = performance.now(); computeProfile(species, grid, model, cached); warm.push(performance.now() - t);
    t = performance.now(); computeProfile(species, custom, model, new Streams(model)); cust.push(performance.now() - t);
  }
  const t = performance.now();
  const all = new Streams(model);
  for (const p of model.preparations) computeProfile(species, p, model, all);
  return { cold: summarise(cold), warm: summarise(warm), custom: summarise(cust), all13PreparationsMs: +(performance.now() - t).toFixed(1) };
}

const IN_PAGE = `(() => {
  const E = window.Engine; const { model, species, grid, custom, runs } = window.__args;
  const sum = (xs) => { const s = [...xs].sort((a, b) => a - b); return { median: +s[Math.floor(s.length / 2)].toFixed(1), p95: +s[Math.min(s.length - 1, Math.floor(s.length * 0.95))].toFixed(1) }; };
  for (let i = 0; i < 3; i++) E.computeProfile(species, grid, model);
  const cached = new E.Streams(model); E.computeProfile(species, grid, model, cached);
  const cold = [], warm = [], cust = [];
  for (let i = 0; i < runs; i++) {
    let t = performance.now(); E.computeProfile(species, grid, model, new E.Streams(model)); cold.push(performance.now() - t);
    t = performance.now(); E.computeProfile(species, grid, model, cached); warm.push(performance.now() - t);
    t = performance.now(); E.computeProfile(species, custom, model, new E.Streams(model)); cust.push(performance.now() - t);
  }
  return { cold: sum(cold), warm: sum(warm), custom: sum(cust) };
})()`;

async function benchBrowser() {
  const bundle = await build({
    stdin: { contents: "export * from './lib/engine';", resolveDir: path.resolve(__dirname, '..'), loader: 'ts' },
    bundle: true, format: 'iife', globalName: 'Engine', write: false, target: 'es2022', minify: true,
  });
  const code = bundle.outputFiles[0].text;
  const browser = await chromium.launch();
  const out: Record<string, unknown> = { bundleKiB: +(code.length / 1024).toFixed(1) };
  for (const rate of [1, 2, 4, 6]) {
    const page = await browser.newPage();
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate });
    await page.setContent('<!doctype html><title>bench</title>');
    await page.addScriptTag({ content: code });
    // a plain string: tsx would inject helpers (__name) into a function passed to the page
    await page.evaluate(`window.__args = ${JSON.stringify({ model, species, grid, custom, runs: rate === 1 ? RUNS : 12 })}`);
    out[`${rate}x`] = await page.evaluate(IN_PAGE);
    await page.close();
  }
  await browser.close();
  return out;
}

(async () => {
  const report = {
    machine: `${os.cpus()[0]?.model} (${os.cpus().length} cores), ${os.platform()} ${os.arch()}, Node ${process.version}`,
    species: `${largest.acceptedName} (${species.compounds.length} compounds, the largest)`, draws: model.params.draws,
    gridPreparation: grid.label, customPreparation: 'vinegar + water, heat and filtration not stated (unknown branches)',
    budgetMs: 50, node: benchNode(), chromium: await benchBrowser(),
  };
  writeFileSync(path.resolve(__dirname, '..', 'lib', 'engine', 'bench-report.json'), JSON.stringify({ ...report, generatedAt: new Date().toISOString() }, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
})();
