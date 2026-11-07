import { readFileSync } from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';
import { ROUTES } from './routes';

/** design v2 HANDOFF.md §4 acceptance checks, on the real pages. (2, ranges compared only by compareRanges, is a code
 *  rule covered by the unit tests; 11 and 14 are in a11y.spec.ts.) */
const BANNED = /\b(works|safe|effective|cures?|treats|heals|recommended)\b/i;
/** Sentences quoted from the data (the hypotheses' own caveats, which negate these words) are excluded from the copy check. */
const QUOTED: string[] = JSON.parse(readFileSync(path.resolve(__dirname, '../../../site-data/hypotheses.json'), 'utf8')).flatMap((h: { caveats: string[] }) => h.caveats);

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
  await expect(page.getByText(/not offered for planning because toxicity is reported/)).toBeVisible();
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

test('9: the quantum priority is "Coming in this release", never 0', async ({ page }) => {
  await page.goto('/planner/');
  await expect(page.getByText('Coming in this release').first()).toBeVisible();
  const dd = await page.locator('dt:has-text("Quantum priority") + dd').allInnerTexts();
  expect(dd.length).toBeGreaterThan(0);
  for (const t of dd) expect(t).toContain('Coming in this release');
});
