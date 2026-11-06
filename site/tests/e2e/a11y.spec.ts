import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { ROUTES } from './routes';

for (const scheme of ['light', 'dark'] as const) {
  for (const route of ROUTES) {
    test(`axe WCAG 2.1 AA + no sideways scroll · ${scheme} · ${route}`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(route);
      if (route.startsWith('/compare')) await expect(page.getByRole('heading', { level: 2 }).first()).toBeVisible({ timeout: 15000 });
      const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      expect(r.violations.map((v) => `${v.id}: ${v.nodes.length} × ${v.nodes[0]?.target}`)).toEqual([]);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow).toBeLessThanOrEqual(0);
    });
  }
}
