import { expect, test } from '@playwright/test';

test('home leads with the reporting gap, with n, CI and the solvent caveat beside the solvent share', async ({ page }) => {
  await page.goto('/');
  const gap = page.locator('section[aria-labelledby="gap"]');
  await expect(gap.getByRole('heading', { name: /rarely say how the plant was prepared/ })).toBeVisible();
  for (const v of ['Heat', 'Fresh or dried', 'Filtration', 'Solvent', 'Plant part', 'None of the five stated']) {
    await expect(gap.getByRole('img', { name: new RegExp(`^${v}: \\d+% of \\d+ studies, 95% confidence interval`) }).first()).toBeVisible();
  }
  await expect(gap.getByText('Solvent share is inflated by construction.')).toBeVisible();
  await expect(gap.getByText(/compared two preparations of the same plant material/)).toBeVisible();
  // the story comes first, the gap after it
  const story = await page.locator('#story').boundingBox();
  const head = await page.locator('#gap').boundingBox();
  expect(story!.y).toBeLessThan(head!.y);
});

test('search the recipes, open one, and read its passage and fields', async ({ page }) => {
  await page.goto('/recipes/');
  await page.getByLabel('Search plants, names, uses and recipe text').fill('decoction');
  await expect(page.getByText(/^Showing/)).toContainText('of 631');
  await page.getByRole('list', { name: 'Recipes' }).getByRole('link').first().click();
  await expect(page.getByRole('heading', { name: 'Original passage' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Extracted fields' })).toBeVisible();
  await expect(page.getByRole('button', { name: /^Fields? \d/ }).first()).toBeVisible();
});

test('a toxic_reported recipe shows the notice, its logged corrections and no Compare link', async ({ page }) => {
  await page.goto('/recipes/pliny-nh_b22_c011_001_r01/');
  await expect(page.getByRole('note').filter({ hasText: 'Toxicity is reported for this plant' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Logged corrections' })).toBeVisible();
  await expect(page.getByRole('row', { name: /part juice root/ })).toBeVisible();
  await expect(page.getByRole('main').getByRole('link', { name: /Compare/ })).toHaveCount(0);
});

test('compare loads a profile on demand and keeps a shareable URL', async ({ page }) => {
  await page.goto('/compare/');
  await expect(page.getByRole('heading', { level: 2 }).first()).toBeVisible({ timeout: 15000 });
  await expect(page).toHaveURL(/species=wfo-.*&a=.*&b=/);
  const shared = page.url();
  const sel = page.getByLabel('Species');
  const other = await sel.locator('option').nth(2).getAttribute('value');
  await sel.selectOption(other!);
  await expect(page).toHaveURL(new RegExp(`species=${other}`));
  await page.goto(shared);
  await expect(page).toHaveURL(shared);
  await expect(page.getByText(/predicted extraction/).first()).toBeVisible();
});

test('audit shows v1 and v2 side by side; a study opens in a drawer that returns focus', async ({ page }) => {
  await page.goto('/audit/');
  await expect(page.getByText('Design flaw.')).toBeVisible();
  await expect(page.getByText('Small n.')).toBeVisible();
  await page.getByRole('tab', { name: /v2/ }).click();
  await expect(page.getByRole('tab', { name: /v2/ })).toHaveAttribute('aria-selected', 'true');
  await page.getByRole('tab', { name: /v1/ }).click();
  const panel = page.getByRole('tabpanel').first();
  const opener = panel.locator('button.text-left:visible').first();
  await opener.focus();
  await opener.press('Enter');
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(opener).toBeFocused();
});

test('hypotheses: the evidence trail opens, and each hypothesis has its own URL', async ({ page }) => {
  await page.goto('/hypotheses/');
  await page.getByRole('button', { name: 'Evidence trail' }).first().click();
  await expect(page.getByRole('dialog')).toContainText('Name resolved to');
  await page.keyboard.press('Escape');
  await page.getByRole('link', { name: 'Link to this hypothesis' }).first().click();
  await expect(page).toHaveURL(/\/hypotheses\/wfo-/);
  await expect(page.getByRole('heading', { name: 'Evidence trail' })).toBeVisible();
});

test('the liquorice case study shows the evidence, the logged corrections and the before/after ranking', async ({ page }) => {
  await page.goto('/case-studies/liquorice/');
  await expect(page.getByText('Spanish liquorice or Spanish juice').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /The logged corrections/ })).toBeVisible();
  await page.getByText('View the ranking as a table').click();
  await expect(page.getByRole('row', { name: /Before correction fresh juice/ })).toBeVisible();
  await expect(page.getByRole('row', { name: /After correction decoction in water/ })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open this comparison' })).toHaveCount(0);
});

test('every download on the Data page is served', async ({ page, request }) => {
  await page.goto('/data/');
  const hrefs = await page.locator('a[download]').evaluateAll((as) => as.map((a) => a.getAttribute('href')!));
  expect(hrefs.length).toBeGreaterThan(5);
  for (const h of hrefs) expect((await request.get(h)).status(), h).toBe(200);
});

test('the recipe explorer and the audit render their first screen without JavaScript', async ({ browser }) => {
  const ctx = await browser.newContext({ javaScriptEnabled: false });
  const page = await ctx.newPage();
  await page.goto('/recipes/');
  await expect(page.getByRole('list', { name: 'Recipes' }).getByRole('listitem')).toHaveCount(40);
  await page.goto('/audit/');
  await expect(page.getByRole('heading', { name: 'Two pre-registered analyses' })).toBeVisible();
  await ctx.close();
});
