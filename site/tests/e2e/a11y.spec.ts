import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import { ROUTES } from './routes';

/** axe (WCAG 2.0/2.1 A + AA, contrast included) and no horizontal page scroll, in both themes, on every screen and
 *  designed state, and again with the interactive details opened (design v2 DESIGN.md §12). */
const axe = async (page: Page) => {
  // Let the design's entrance animations (fade-in etc.) finish, so contrast is measured at the final colours.
  await page.evaluate(() => Promise.all(document.getAnimations().filter((a) => a.effect?.getTiming().iterations !== Infinity).map((a) => a.finished.catch(() => null))));
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  return r.violations.map((v) => `${v.id}: ${v.nodes.length} × ${v.nodes[0]?.target}`);
};
const overflow = (page: Page) => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);

for (const theme of ['light', 'dark'] as const) {
  for (const r of ROUTES) {
    test(`axe + no sideways scroll · ${theme} · ${r.path}`, async ({ page }) => {
      await page.goto(`${r.path}${r.path.includes('?') ? '&' : '?'}theme=${theme}`);
      if (r.ready) await page.waitForSelector(r.ready, { timeout: 30000 });
      expect(await axe(page)).toEqual([]);
      expect(await overflow(page)).toBeLessThanOrEqual(0);
    });
  }
  test(`axe with details opened · ${theme}`, async ({ page }) => {
    await page.goto(`/lab/?plant=Salvia%20sclarea&solvent=water&heat=boiled&strained=true&acid=false&modern=true&theme=${theme}`);
    await page.waitForSelector('[data-engine-status="ready"]');
    await page.getByRole('button', { name: /^Why does/ }).first().click();
    await page.locator('details summary').first().click();
    expect(await axe(page)).toEqual([]);
    await page.goto(`/atlas/?theme=${theme}`);
    await page.getByRole('button', { name: 'Disputed names' }).click();
    await expect(page.getByText(/of \d+ recipes ·/)).toBeVisible();
    expect(await axe(page)).toEqual([]);
    await page.goto(`/planner/?theme=${theme}`);
    await page.getByRole('button', { name: 'Evidence trail' }).first().click();
    await expect(page.getByRole('dialog')).toBeVisible();
    expect(await axe(page)).toEqual([]);
    await page.goto(`/evidence-gap/?theme=${theme}`);
    for (const s of await page.locator('details summary').all()) await s.click();
    expect(await axe(page)).toEqual([]);
    expect(await overflow(page)).toBeLessThanOrEqual(0);
  });
}
