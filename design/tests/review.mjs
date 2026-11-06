/**
 * Strict review harness (Phase 4). Builds the app, serves it, and for every
 * route × theme × width:
 *   - runs axe-core (WCAG 2.0/2.1 A + AA), including colour contrast
 *   - checks for horizontal page overflow (390px must not scroll sideways)
 * and, at 1440px light:
 *   - tabs through the page and flags any focused element without a visible
 *     focus indicator
 *   - opens each drawer / disclosure and re-runs axe on the opened state
 *
 * Usage:  npm run review            (needs `npx playwright install chromium` once
 *                                     if no Chromium is available)
 * Output: review-output/report.json, review-output/*.png (390px screenshots)
 * Exit code 1 if anything fails.
 */
import { build, preview } from 'vite';
import { chromium } from 'playwright';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const AXE = readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const OUT = 'review-output';
mkdirSync(OUT, { recursive: true });

const ROUTES = [
  ['gallery', '#/gallery'],
  ['home', '#/'],
  ['recipes', '#/recipes'],
  ['recipe-culpeper', '#/recipes/cul-wormwood-wine'],
  ['recipe-pliny', '#/recipes/pli-absinthium-vinegar'],
  ['recipe-toxic', '#/recipes/cul-hemlock-oil'],
  ['compare', '#/compare'],
  ['audit', '#/audit'],
  ['hypotheses', '#/hypotheses'],
  ['methods', '#/methods'],
  ['data', '#/data'],
];
// Interactions whose opened state must also pass axe.
const OPEN = {
  gallery: [{ name: 'drawer', click: 'role=button[name="View reasoning"] >> visible=true' }],
  compare: [
    { name: 'drivers', click: 'role=button[name="Drivers"] >> visible=true' },
    { name: 'table', click: 'summary >> visible=true' },
  ],
  audit: [
    { name: 'drawer', click: 'role=button[name=/^\\[MOCK\\] Study/] >> visible=true' },
    { name: 'table', click: 'summary >> visible=true' },
  ],
  hypotheses: [
    { name: 'trail', click: 'role=button[name="Evidence trail"] >> visible=true' },
    { name: 'table', click: 'summary >> visible=true' },
  ],
  methods: [{ name: 'table', click: 'summary >> visible=true' }],
  'recipe-culpeper': [{ name: 'sources', click: 'role=button[name=/source/] >> visible=true' }],
};

await build({ logLevel: 'warn' });
const server = await preview({ preview: { port: 4179, strictPort: true }, logLevel: 'warn' });
const BASE = 'http://localhost:4179/';

const browser = await chromium.launch();
const report = { axe: [], overflow: [], focus: [], errors: [] };

async function settle(page) {
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(() => !document.querySelector('[aria-busy="true"]'), null, { timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(150);
}
async function runAxe(page, where) {
  await page.addScriptTag({ content: AXE });
  const res = await page.evaluate(async () =>
    // eslint-disable-next-line no-undef
    (await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } })).violations.map((v) => ({
      id: v.id, impact: v.impact, help: v.help,
      nodes: v.nodes.slice(0, 5).map((n) => ({ target: n.target.join(' '), summary: n.failureSummary?.split('\n').slice(0, 3).join(' | ') })),
      count: v.nodes.length,
    })));
  for (const v of res) report.axe.push({ where, ...v });
}

for (const theme of ['light', 'dark']) {
  for (const width of [1440, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    page.on('pageerror', (e) => report.errors.push({ theme, width, error: String(e) }));
    page.on('console', (m) => { if (m.type() === 'error') report.errors.push({ theme, width, error: m.text() }); });
    for (const [name, hash] of ROUTES) {
      const where = `${name} · ${theme} · ${width}`;
      await page.goto(`${BASE}?theme=${theme}${hash}`);
      await page.reload();
      await settle(page);
      await runAxe(page, where);

      const ov = await page.evaluate(() => {
        const vw = document.documentElement.clientWidth;
        const sw = document.documentElement.scrollWidth;
        const culprits = [];
        if (sw > vw + 1) {
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            if (r.right > vw + 1 && r.width > 0) {
              let inScroller = false;
              for (let p = el.parentElement; p; p = p.parentElement) {
                const s = getComputedStyle(p);
                if (/(auto|scroll|hidden)/.test(s.overflowX) && p !== document.body && p !== document.documentElement) { inScroller = true; break; }
              }
              if (!inScroller) culprits.push(`${el.tagName.toLowerCase()}.${String(el.className).slice(0, 60)} → ${Math.round(r.right)}px`);
            }
            if (culprits.length > 6) break;
          }
        }
        return { vw, sw, culprits };
      });
      if (ov.sw > ov.vw + 1) report.overflow.push({ where, ...ov });

      if (width === 390) await page.screenshot({ path: `${OUT}/${name}-${theme}-390.png`, fullPage: true });

      for (const o of OPEN[name] ?? []) {
        try {
          await page.locator(o.click).first().click();
          await page.waitForTimeout(200);
          await runAxe(page, `${where} · open:${o.name}`);
          const isDialog = await page.evaluate(() => !!document.querySelector('[role="dialog"]'));
          if (isDialog) {
            // Focus must stay inside the dialog while tabbing, and return to the trigger on Escape.
            for (let i = 0; i < 15; i++) {
              await page.keyboard.press('Tab');
              const inside = await page.evaluate(() => !!document.activeElement?.closest('[role="dialog"]'));
              if (!inside) { report.focus.push({ where, element: `focus escaped the ${o.name} dialog after ${i + 1} Tab presses` }); break; }
            }
            await page.keyboard.press('Escape');
            const back = await page.evaluate(() => document.activeElement && document.activeElement !== document.body && !document.querySelector('[role="dialog"]'));
            if (!back) report.focus.push({ where, element: `focus not returned to the trigger after closing ${o.name}` });
          } else {
            await page.keyboard.press('Escape');
          }
        } catch (e) { report.errors.push({ where, error: `could not open ${o.name}: ${e.message.split('\n')[0]}` }); }
      }

      if (theme === 'light' && width === 1440) {
        await page.goto(`${BASE}?theme=${theme}${hash}`);
        await page.reload();
        await settle(page);
        const seen = new Set();
        for (let i = 0; i < 80; i++) {
          await page.keyboard.press('Tab');
          const f = await page.evaluate(() => {
            const el = document.activeElement;
            if (!el || el === document.body) return null;
            const s = getComputedStyle(el);
            const visible = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || (s.boxShadow && s.boxShadow !== 'none');
            const label = (el.getAttribute('aria-label') || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 50);
            return { key: el.tagName + '|' + label + '|' + el.getBoundingClientRect().top, tag: el.tagName.toLowerCase(), label, visible };
          });
          if (!f) break;
          if (seen.has(f.key)) break;
          seen.add(f.key);
          if (!f.visible) report.focus.push({ where, element: `${f.tag} "${f.label}"` });
        }
      }
    }
    await ctx.close();
  }
}

await browser.close();
server.httpServer.close();

writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 2));
const n = report.axe.length + report.overflow.length + report.focus.length + report.errors.length;
console.log(`axe violations: ${report.axe.length} · overflow: ${report.overflow.length} · focus: ${report.focus.length} · runtime errors: ${report.errors.length}`);
for (const v of report.axe) console.log(`AXE  ${v.where}  ${v.id} (${v.impact}) ×${v.count}  ${v.nodes[0]?.target}`);
for (const o of report.overflow) console.log(`OVERFLOW  ${o.where}  ${o.sw}>${o.vw}  ${o.culprits.slice(0, 3).join(' ; ')}`);
for (const f of report.focus) console.log(`FOCUS  ${f.where}  ${f.element}`);
for (const e of report.errors) console.log(`ERROR  ${e.where ?? e.theme + ' ' + e.width}  ${e.error}`);
process.exit(n ? 1 : 0);
