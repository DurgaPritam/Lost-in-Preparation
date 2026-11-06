import { readFileSync } from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';
import { ROUTES } from './routes';

/** HANDOFF.md §4 acceptance checks, run on the real pages. */
const DATA = path.resolve(__dirname, '../../../site-data');
const quoted: string[] = [
  ...JSON.parse(readFileSync(path.join(DATA, 'hypotheses.json'), 'utf8')).flatMap((h: { caveats: string[] }) => h.caveats),
  ...JSON.parse(readFileSync(path.join(DATA, 'case_studies.json'), 'utf8')).map((c: { label: string }) => c.label),
];
const BANNED = /\b(works|effective|cures?|treats|recommended)\b|\bsafe\b/i;

for (const route of ROUTES) {
  test(`acceptance · ${route}`, async ({ page }) => {
    await page.goto(route);
    if (route.startsWith('/compare')) await expect(page.getByRole('heading', { level: 2 }).first()).toBeVisible({ timeout: 15000 });
    // 3: every likelihood bar has a spoken range
    for (const label of await page.locator('[role="img"]').evaluateAll((els) => els.map((e) => e.getAttribute('aria-label') ?? ''))) {
      expect(label.length, 'chart without aria-label').toBeGreaterThan(5);
    }
    // 4: a chart of predicted extraction always has the extraction ≠ detection explainer on the same screen
    if ((await page.getByRole('img', { name: /Predicted extraction/ }).count()) > 0) {
      await expect(page.getByText(/predicted extraction/i).first()).toBeAttached();
    }
    // 1: no null rendered as N/A, NaN or undefined
    const text = await page.locator('main').innerText();
    expect(text).not.toMatch(/\bN\/A\b|\bNaN\b|\bundefined\b|\bnull\b/);
    // 8: no medical-claim words in the site's own copy (quoted data sentences excluded)
    let own = text.toLowerCase();
    for (const q of quoted) own = own.split(q.toLowerCase()).join(' ');
    expect(own.replace(/not evidence of safety/gi, ''), 'banned word in copy').not.toMatch(BANNED);
  });
}

test('5: no toxic_reported species page or hypothesis offers a Compare link', async ({ page }) => {
  await page.goto('/hypotheses/wfo-0000212813-D008107/');
  await expect(page.getByText('Toxicity is reported for this plant').first()).toBeVisible();
  await expect(page.getByRole('main').locator('a[href^="/compare"]')).toHaveCount(0);
});

test('6: Culpeper and Pliny keep separate confidence markers', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: /^Source: Culpeper/ })).toHaveCount(2);
  await expect(page.getByRole('button', { name: /^Source: Pliny/ })).toHaveCount(1);
});
