// Runs Lighthouse CI against the static export, using Playwright's Chromium so no separate Chrome install is needed.
// LH_SCHEME=light|dark forces the colour scheme (otherwise headless Chrome follows the OS, e.g. dark on a dark Mac).
// Afterwards it writes perf/lighthouse-<scheme>.json: the median score per category, CLS and LCP for every URL.
import { spawnSync } from 'node:child_process';
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { chromium } from '@playwright/test';

const scheme = process.env.LH_SCHEME;
const args = [...process.argv.slice(2)];
if (scheme === 'light' || scheme === 'dark') {
  args.push(`--collect.settings.chromeFlags=--headless=new --no-sandbox --blink-settings=preferredColorScheme=${scheme === 'light' ? 1 : 0}`);
}
const env = { ...process.env, CHROME_PATH: process.env.CHROME_PATH || chromium.executablePath() };
const r = spawnSync('npx', ['lhci', 'autorun', ...args], { stdio: 'inherit', env });

try {
  const runs = {};
  for (const f of readdirSync('.lighthouseci').filter((f) => /^lhr-.*\.json$/.test(f))) {
    const lhr = JSON.parse(readFileSync(`.lighthouseci/${f}`, 'utf8'));
    const url = lhr.finalDisplayedUrl.replace(/^https?:\/\/[^/]+/, '');
    (runs[url] ??= []).push(lhr);
  }
  const median = (xs) => { const s = [...xs].sort((a, b) => a - b); return s[Math.floor(s.length / 2)]; };
  const pages = Object.entries(runs).sort().map(([url, ls]) => ({
    url, runs: ls.length,
    performance: median(ls.map((l) => Math.round(l.categories.performance.score * 100))),
    accessibility: median(ls.map((l) => Math.round(l.categories.accessibility.score * 100))),
    bestPractices: median(ls.map((l) => Math.round(l.categories['best-practices'].score * 100))),
    cls: median(ls.map((l) => Math.round(l.audits['cumulative-layout-shift'].numericValue * 1000) / 1000)),
    lcpMs: median(ls.map((l) => Math.round(l.audits['largest-contentful-paint'].numericValue))),
  }));
  const any = Object.values(runs)[0]?.[0];
  mkdirSync('perf', { recursive: true });
  const out = `perf/lighthouse-${scheme ?? 'os-default'}.json`;
  writeFileSync(out, JSON.stringify({
    scheme: scheme ?? 'os default', lighthouse: any?.lighthouseVersion, formFactor: any?.configSettings.formFactor,
    throttling: any?.configSettings.throttlingMethod, aggregation: 'median of runs', assertionsPassed: r.status === 0,
    pages, generatedAt: new Date().toISOString(),
  }, null, 2) + '\n');
  console.log(`wrote ${out}`);
} catch (e) {
  console.error('lighthouse summary not written:', e.message);
}
process.exit(r.status ?? 1);
