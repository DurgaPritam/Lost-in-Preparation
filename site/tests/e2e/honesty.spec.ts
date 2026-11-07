import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';
import { ROUTES } from './routes';

/** design v2 HANDOFF.md §4 acceptance checks, on the real pages. (2, ranges compared only by compareRanges, is a code
 *  rule covered by the unit tests; 11 and 14 are in a11y.spec.ts.) */
const BANNED = /\b(works|safe|effective|cures?|treats|heals|recommended)\b/i;
/** Sentences quoted from the data (the hypotheses' own caveats, which negate these words) are excluded from the copy check. */
const QUOTED: string[] = [
  ...JSON.parse(readFileSync(path.resolve(__dirname, '../../../site-data/hypotheses.json'), 'utf8')).flatMap((h: { caveats: string[] }) => h.caveats),
  // the re-test panel's own caveats (lab_panel.json), which negate the same words
  ...((p: { panel: { caveats: string[] }[] }) => p.panel.flatMap((c) => c.caveats))(JSON.parse(readFileSync(path.resolve(__dirname, '../../../site-data/lab_panel.json'), 'utf8'))),
];

for (const r of ROUTES) {
  test(`acceptance · ${r.path}`, async ({ page }) => {
    await page.goto(r.path);
    if (r.ready) await page.waitForSelector(r.ready, { timeout: 30000 });
    const main = page.locator('main');
    const text = await main.innerText();
    // 1: no null rendered as a placeholder value
    expect(text).not.toMatch(/\bN\/A\b|\bNaN\b|\bundefined\b|\bnull\b/);
    // 3: every likelihood bar speaks its range
    for (const label of await main.locator('[role="img"]').evaluateAll((els) => els.map((e) => e.getAttribute('aria-label') ?? ''))) {
      expect(label).toMatch(/between \d|unknown|of \d|\d+ same/i);
    }
    // 4: a screen with predicted extraction bars shows the extraction ≠ detection explainer
    if ((await main.getByRole('img', { name: /Predicted extraction/ }).count()) > 0) {
      await expect(page.getByRole('button', { name: /Extraction is not detection/ }).first()).toBeAttached();
    }
    // 10: every plate slot with a caption shows its licence, host and status
    for (const cap of await main.locator('figure figcaption').allInnerTexts()) {
      expect(cap).toMatch(/·.*·.*(licence confirmed|licence to confirm|plate to source)/);
    }
    // 12: no medical-claim words in the copy ("not evidence of safety" is the required caveat)
    let own = text.toLowerCase();
    for (const q of QUOTED) own = own.split(q.toLowerCase()).join(' ');
    expect(own.replace(/not evidence of safety/gi, '')).not.toMatch(BANNED);
    // 13: every chart-like view has a table fallback
    if ((await main.locator('[role="img"]').count()) > 0 && !r.path.startsWith('/recipes/') && r.path !== '/') {
      expect(await main.getByText(/View as table|\(table\)/).count()).toBeGreaterThan(0);
    }
  });
}

test('5: a plant with toxicity reported gets the notice and never a Lab link, a plan action or a Planner slot', async ({ page }) => {
  await page.goto('/lab/?plant=Hyoscyamus%20niger&solvent=water&heat=boiled&strained=true&acid=false');
  await page.waitForSelector('[data-engine-status="ready"]');
  await expect(page.getByText(/Toxicity is reported for this plant/).first()).toBeVisible();
  await expect(page.getByRole('link', { name: 'Plan an experiment' })).toHaveCount(0);
  for (const url of ['/recipes/culpeper-1652_herbal_liquoris_006_r00/', '/case/liquorice/']) {
    await page.goto(url);
    await expect(page.getByText(/Toxicity is reported for this plant/).first()).toBeVisible();
    await expect(page.locator('main a[href^="/lab"]')).toHaveCount(0);
  }
  await page.goto('/planner/');
  await expect(page.getByText(/not offered for planning because toxicity is reported/i)).toBeVisible();
  await expect(page.locator('main ol li h3', { hasText: 'Glycyrrhiza glabra' })).toHaveCount(0);
});

test('6: Culpeper 1652, Culpeper 1850 and Pliny keep separate confidence markers', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: /^Source: Culpeper, The English Physitian/ })).toHaveCount(1);
  await expect(page.getByRole('button', { name: /^Source: Culpeper, The Complete Herbal/ })).toHaveCount(1);
  await expect(page.getByRole('button', { name: /^Source: Pliny/ })).toHaveCount(1);
});

test('7: a disputed name is never shown as one settled species', async ({ page }) => {
  await page.goto('/recipes/pliny-nh_b20_c099_002_r00/');
  await expect(page.getByText(/candidates · disputed/).first()).toBeVisible();
});

test('8: the Lab never shows a profile for a combination the model has no estimate for', async ({ page }) => {
  await page.goto('/lab/?plant=Salvia%20sclarea&solvent=water&heat=boiled&strained=true&acid=true');
  await page.waitForSelector('[data-engine-status="nodata"]');
  await expect(page.getByRole('heading', { name: 'No estimate for this combination' })).toBeVisible();
  await expect(page.locator('main').getByRole('img', { name: /Predicted extraction/ })).toHaveCount(0);
});

test('9: the quantum benchmark is labelled as a benchmark, never a validation, and claims no advantage', async ({ page }) => {
  await page.goto('/planner/');
  await expect(page.getByRole('button', { name: 'Evidence: Benchmark against exact optimum' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Quantum benchmark' })).toBeVisible();
  await expect(page.locator('main')).not.toContainText(/quantum advantage(?! is claimed)/i);
  await page.goto('/docs/');
  await expect(page.locator('#quantum').getByRole('button', { name: 'Evidence: Benchmark against exact optimum' })).toBeVisible();
  await expect(page.locator('#quantum')).toContainText('no quantum advantage is claimed');
});

/** SITE (project lead, 2026-11-08): the website names no AI tool or model anywhere; it states only the status
 *  (provisional, not independently validated). The repository keeps the full method record. Checked on the rendered
 *  copy: text (closed tooltips included, scripts excluded), aria-labels, titles, alt text and page metadata. */
const PROVENANCE = /\bAI\b|\bAI-|Claude|\bLLMs?\b|Groq|Llama|Anthropic|language model/i;
const copyOf = (page: import('@playwright/test').Page) => page.evaluate(() => {
  const b = document.body.cloneNode(true) as HTMLElement;
  b.querySelectorAll('script,style,noscript,template').forEach((e) => e.remove());
  const attrs = [...document.querySelectorAll('[aria-label],[title],[alt],[placeholder]')]
    .map((e) => ['aria-label', 'title', 'alt', 'placeholder'].map((a) => e.getAttribute(a) ?? '').join(' ')).join(' ');
  const meta = [...document.querySelectorAll('meta[name="description"],meta[property^="og:"],meta[name^="twitter:"]')].map((m) => m.getAttribute('content') ?? '').join(' ');
  return [document.title, meta, b.textContent ?? '', attrs].join('\n');
});
const leak = (s: string) => { const m = PROVENANCE.exec(s); return m ? s.slice(Math.max(0, m.index - 80), m.index + 80) : null; };

for (const r of ROUTES) {
  test(`no AI wording · ${r.path}`, async ({ page }) => {
    await page.goto(r.path);
    if (r.ready) await page.waitForSelector(r.ready, { timeout: 30000 });
    if (r.path === '/docs/') {
      await page.getByRole('button', { name: /Show the \d+ provisional check metrics/ }).click();
      await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { scrollTo(0, y); await new Promise((res) => setTimeout(res, 30)); } });
      await page.waitForTimeout(500);
    }
    expect(leak(await copyOf(page))).toBeNull();
  });
}

test('no AI wording in any built page (static HTML, scripts excluded)', () => {
  const root = path.resolve(__dirname, '../../out');
  const pages: string[] = [];
  const walk = (d: string) => { for (const e of readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else if (e.name.endsWith('.html')) pages.push(p); } };
  walk(root);
  expect(pages.length).toBeGreaterThan(100);
  const bad: string[] = [];
  for (const f of pages) {
    const html = readFileSync(f, 'utf8').replace(/<script\b[\s\S]*?<\/script>/g, ' ').replace(/<style\b[\s\S]*?<\/style>/g, ' ');
    const attrs = [...html.matchAll(/(?:alt|title|aria-label|content|placeholder)="([^"]*)"/g)].map((m) => m[1]).join(' ');
    const l = leak(html.replace(/<[^>]+>/g, ' ') + ' ' + attrs);
    if (l) bad.push(`${path.relative(root, f)}: ${l}`);
  }
  expect(bad.slice(0, 5)).toEqual([]);
});

test('unchecked items are never shown as validated', async ({ page }) => {
  await page.goto('/docs/');
  const stages = page.locator('#pipeline li');
  for (const name of ['Recipes (M1)', 'Preparation model (M4)', 'Audit (M5)', 'Ranking (M6)']) {
    const li = stages.filter({ hasText: name });
    await expect(li.getByRole('button', { name: /^Evidence: (Human-validated|Validated)$/ })).toHaveCount(0);
  }
  await page.goto('/credits/');
  await expect(page.locator('main')).not.toContainText(/licence confirmed/i);
  await expect(page.locator('main').getByRole('button', { name: 'Evidence: Provisional: not independently validated' }).first()).toBeVisible();
  await page.goto('/hypotheses/');
  await expect(page.locator('main')).toContainText('provisional, unverified');
});
