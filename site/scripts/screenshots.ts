/** Full-page screenshots of every v2 screen and designed state at 1440px and 390px into screenshots/ (git-ignored).
 *  Needs `npm run serve`. THEME=dark for Nocturne (default Herbarium). Pages that run the engine wait until it is done. */
import { chromium } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const BASE = process.env.BASE_URL ?? 'http://localhost:4517';
const THEME = process.env.THEME === 'dark' ? 'dark' : 'light';
export const SCREENS: [string, string, string?][] = [
  ['landing', '/', '[data-engine-status="ready"]'],
  ['lab', '/lab/?plant=Salvia%20sclarea&solvent=water&heat=boiled&strained=true&acid=false', '[data-engine-status="ready"]'],
  ['lab-modern', '/lab/?plant=Salvia%20sclarea&solvent=wine&heat=cold&strained=true&acid=false&modern=true', '[data-engine-status="ready"]'],
  ['lab-toxic', '/lab/?plant=Hyoscyamus%20niger&solvent=water&heat=boiled&strained=true&acid=false', '[data-engine-status="ready"]'],
  ['lab-nodata', '/lab/?plant=Salvia%20sclarea&solvent=water&heat=boiled&strained=true&acid=true', '[data-engine-status="nodata"]'],
  ['lab-noprofile', '/lab/?plant=Mentha', '[data-engine-status="nodata"]'],
  ['lab-wide', '/lab/?plant=Filipendula%20ulmaria&solvent=oil&heat=warm&strained=true&acid=false', '[data-engine-status="ready"]'],
  ['atlas', '/atlas/'],
  ['atlas-plant', '/atlas/?plant=Glycyrrhiza%20glabra'],
  ['recipe-culpeper', '/recipes/culpeper-1652_herbal_agrimony_008_r01/'],
  ['recipe-pliny-disputed', '/recipes/pliny-nh_b20_c099_002_r00/'],
  ['recipe-liquorice', '/recipes/culpeper-1652_herbal_liquoris_006_r00/'],
  ['evidence-gap', '/evidence-gap/'],
  ['case', '/case/liquorice/'],
  ['planner', '/planner/'],
  ['docs', '/docs/'],
  ['credits', '/credits/'],
];
(async () => {
  mkdirSync('screenshots', { recursive: true });
  const browser = await chromium.launch();
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, colorScheme: THEME });
    for (const [name, url, ready] of SCREENS) {
      await page.goto(BASE + url, { waitUntil: 'networkidle' });
      if (ready) await page.waitForSelector(ready, { timeout: 30000 });
      await page.waitForTimeout(700); // let bar transitions (480 ms) settle
      const file = `screenshots/${name}-${THEME}-${w}.png`;
      await page.screenshot({ path: file, fullPage: true });
      console.log(file);
    }
    await page.close();
  }
  await browser.close();
})();
