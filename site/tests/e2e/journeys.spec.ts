import { expect, test } from '@playwright/test';
import { ROUTES } from './routes';

/** Main journeys through the v2 information architecture. */

test('landing: the live demo switches preparations and overlays the modern method', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('[data-engine-status="ready"]');
  const bars = page.getByRole('img', { name: /cold water infusion: Predicted extraction between/ });
  await expect(bars.first()).toBeVisible();
  await page.getByRole('radio', { name: 'Decoction' }).click();
  await expect(page.getByRole('img', { name: /decoction in water: Predicted extraction between/ }).first()).toBeVisible();
  await page.getByLabel('Overlay modern lab method').check();
  await expect(page.getByRole('img', { name: /Compared with modern methanol extract: between/ }).first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(/5 of \d+ compounds: the largest predicted changes/)).toBeVisible();
});

test('lab: settings change the profile live, travel in the URL, and a stale computation never lands', async ({ page }) => {
  await page.goto('/lab/?plant=Salvia%20sclarea&solvent=water&heat=cold&strained=true&acid=false');
  await page.waitForSelector('[data-engine-status="ready"]');
  await page.getByRole('radio', { name: 'Boiled' }).click();
  await expect(page).toHaveURL(/heat=boiled/);
  await expect(page.locator('[data-engine-status="ready"][data-engine-key*="|boiled|"]')).toBeAttached();
  await expect(page.getByText(/↑ higher|↓ lower|≈ overlaps/).first()).toBeVisible();
  // rapid toggles: the last one wins (older requests are cancelled in the worker or ignored here)
  for (const s of ['Wine', 'Oil', 'Vinegar', 'Honey', 'Wine']) await page.getByRole('radio', { name: s, exact: true }).click();
  await expect(page.locator('[data-engine-status="ready"][data-engine-key*="|wine|boiled|"]')).toBeAttached({ timeout: 15000 });
  await expect(page).toHaveURL(/solvent=wine/);
  // the URL reproduces the configuration
  const url = page.url();
  await page.goto(url);
  await expect(page.locator('[data-engine-status="ready"][data-engine-key*="|wine|boiled|"]')).toBeAttached({ timeout: 15000 });
  await expect(page.getByRole('radio', { name: 'Wine', exact: true })).toHaveAttribute('aria-checked', 'true');
});

test('lab: "Why?" explains the drivers with heuristics marked, and Escape returns focus', async ({ page }) => {
  await page.goto('/lab/?plant=Salvia%20sclarea&solvent=water&heat=boiled&strained=false&acid=false');
  await page.waitForSelector('[data-engine-status="ready"]');
  const why = page.getByRole('button', { name: /^Why does/ }).first();
  await why.click();
  await expect(page.getByText(/Model multiplier ×/).first()).toBeVisible();
  await expect(page.getByRole('button', { name: /^Heuristic: Filtration carry-over/ }).first()).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(why).toBeFocused();
});

test('lab: a plant with toxicity reported shows the notice and no plan action', async ({ page }) => {
  await page.goto('/lab/?plant=Hyoscyamus%20niger&solvent=water&heat=boiled&strained=true&acid=false');
  await page.waitForSelector('[data-engine-status="ready"]');
  await expect(page.getByText(/not a preparation to make or take/)).toBeVisible();
  await expect(page.getByRole('link', { name: 'Plan an experiment' })).toHaveCount(0);
});

test('atlas: search, plant view and recipe page', async ({ page }) => {
  await page.goto('/atlas/');
  await page.getByLabel('Search the Atlas').fill('wormwood');
  await expect(page).toHaveURL(/q=wormwood/);
  await expect(page.getByText(/of \d+ recipes · [1-9]\d* plants/)).toBeVisible({ timeout: 15000 });
  await page.goto('/atlas/?plant=Glycyrrhiza%20glabra');
  await expect(page.getByText('Showing one plant:')).toBeVisible();
  await page.goto('/recipes/culpeper-1652_herbal_agrimony_008_r01/');
  await expect(page.getByRole('heading', { name: 'Original passage' })).toBeVisible();
  await expect(page.getByRole('button', { name: /^Field 1:/ })).toBeVisible();
  await expect(page.getByText('Not stated in source').first()).toBeVisible();
  const lab = page.getByRole('link', { name: 'Open this preparation in the Lab' });
  await expect(lab).toHaveAttribute('href', /\/lab\/\?plant=Agrimonia/);
});

test('evidence gap: sorted rows with intervals, the solvent caveat and a table fallback', async ({ page }) => {
  await page.goto('/evidence-gap/');
  await expect(page.getByText('Solvent share is inflated by construction.')).toBeVisible();
  await page.getByRole('radio', { name: 'Most reported first' }).click();
  const first = page.locator('ol li').first();
  await expect(first).toContainText('Solvent');
  await page.getByText('View as table').first().click();
  await expect(page.getByRole('table').first()).toContainText('95% interval');
});

test('case study: four chapters from the real analysis, the record, and no Lab action', async ({ page }) => {
  await page.goto('/case/liquorice/');
  for (const t of ['The misreading', 'The evidence', 'The correction', 'The new result']) await expect(page.getByRole('heading', { name: t })).toBeVisible();
  await expect(page.getByText(/field corrections? across \d+ recipes?/)).toBeVisible();
  await expect(page.getByText('[MOCK')).toHaveCount(0);
});

test('planner: the evidence trail opens in a dialog that returns focus', async ({ page }) => {
  await page.goto('/planner/');
  const open = page.getByRole('button', { name: 'Evidence trail' }).first();
  await open.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('dialog')).toContainText('hypothesis worth re-testing');
  await page.keyboard.press('Escape');
  await expect(open).toBeFocused();
});

test('planner: panel size switches the list; one entry per plant; toxic plants listed as excluded, never planned', async ({ page }) => {
  await page.goto('/planner/');
  const list = page.locator('section[aria-labelledby="panel"] ol > li');
  await expect(list).toHaveCount(8);
  await page.getByRole('radio', { name: '4', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Suggested panel (4)' })).toBeVisible();
  await expect(list).toHaveCount(4);
  const plants = (await list.locator('h3').allInnerTexts()).map((t) => t.split(':')[0].trim());
  expect(new Set(plants).size).toBe(plants.length);
  await expect(page.getByText(/not offered for planning because toxicity is reported/i)).toBeVisible();
  for (const toxic of ['Glycyrrhiza glabra', 'Hyoscyamus niger']) await expect(list.filter({ hasText: toxic })).toHaveCount(0);
});

test('planner: the original v1 result stays visible with its slot-8 note', async ({ page }) => {
  await page.goto('/planner/');
  await expect(page.getByRole('heading', { name: 'The original result (rule v1)' })).toBeVisible();
  await expect(page.locator('section[aria-labelledby="original"]').getByText(/selected on coverage, not value/)).toBeVisible();
});

test('planner: the benchmark switches size, states the winner, and has a table fallback', async ({ page }) => {
  await page.goto('/planner/');
  const bench = page.locator('section[aria-labelledby="bench"]');
  await bench.getByRole('radio', { name: '16', exact: true }).click();
  await expect(bench.getByText(/Which method wins at n = 16:/)).toBeVisible();
  await expect(bench.getByText(/only the ILP proves optimality/)).toBeVisible();
  await bench.getByText('View as table').click();
  await expect(bench.getByRole('table').first()).toContainText('QAOA, XY mixer');
  await page.getByRole('link', { name: 'How the panel was chosen' }).click();
  await expect(page.locator('#how')).toBeVisible();
});

test('methods: "Where quantum helps" is in the table of contents and shows both results', async ({ page }) => {
  await page.goto('/docs/');
  await page.getByRole('navigation', { name: 'On this page' }).getByRole('link', { name: 'Where quantum helps' }).click();
  const q = page.locator('#quantum');
  await expect(q.getByRole('heading', { name: 'Quantum chemistry for the descriptor' })).toBeVisible();
  await expect(q.getByRole('heading', { name: 'Quantum optimisation for the re-test panel' })).toBeVisible();
  await expect(q.getByRole('button', { name: 'Evidence: Validated against external data' })).toBeVisible();
});

test('docs: table of contents jumps, and audited studies load per version', async ({ page }) => {
  await page.goto('/docs/');
  await page.getByRole('navigation', { name: 'On this page' }).getByRole('link', { name: 'Audited studies' }).click();
  await expect(page.getByText('Design flaw.').first()).toBeVisible();
  await expect(page.getByRole('table', { name: /audit v2/ }).or(page.getByText(/Audited modern studies, audit v2/)).first()).toBeAttached({ timeout: 15000 });
  await page.getByRole('tab', { name: /v1 · as pre-registered/ }).click();
  await expect(page.getByText(/Audited modern studies, audit v1/).first()).toBeAttached({ timeout: 15000 });
});

test('credits list every sourced plate with its licence; downloads and old addresses work', async ({ page, request }) => {
  await page.goto('/credits/');
  await expect(page.getByText(/Botanical plates \(\d+ sourced\)/).first()).toBeAttached();
  for (const f of ['recipes.json', 'metrics.json', 'engine/model.json', 'plates.json']) expect((await request.get(`/data/${f}`)).ok()).toBe(true);
  await page.goto('/recipes/');
  await expect(page).toHaveURL(/\/atlas\/$/);
  await page.goto('/hypotheses/');
  await expect(page).toHaveURL(/\/planner\/$/);
});


for (const scheme of ['light', 'dark'] as const) {
  test(`no script errors on any screen (${scheme}), and the theme's fonts are preloaded`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(`${page.url()}: ${e.message}`));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(`${page.url()}: ${m.text()}`); });
    for (const r of ROUTES) {
      await page.goto(r.path);
      if (r.ready) await page.waitForSelector(r.ready, { timeout: 30000 });
    }
    expect(errors).toEqual([]);
    const preloads = await page.locator('link[rel="preload"][as="font"]').evaluateAll((ls) => ls.map((l) => (l as HTMLLinkElement).href));
    expect(preloads.some((h) => h.includes(scheme === 'dark' ? 'instrument-serif' : 'fraunces'))).toBe(true);
  });
}
