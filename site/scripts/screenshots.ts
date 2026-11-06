/** Full-page screenshots of every screen at 1440px and 390px (light theme) into screenshots/. Needs `npm run serve`. */
import { chromium } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const BASE = process.env.BASE_URL ?? 'http://localhost:4517';
export const SCREENS: [string, string][] = [
  ['home', '/'], ['recipes', '/recipes/'], ['recipe-detail', '/recipes/pliny-nh_b22_c011_001_r01/'],
  ['recipe-detail-culpeper', '/recipes/culpeper-1652_herbal_agrimony_008_r01/'], ['compare', '/compare/'], ['audit', '/audit/'],
  ['hypotheses', '/hypotheses/'], ['hypothesis', '/hypotheses/wfo-0000212813-D008107/'], ['case-study', '/case-studies/liquorice/'],
  ['methods', '/methods/'], ['data', '/data/'],
];
(async () => {
  mkdirSync('screenshots', { recursive: true });
  const browser = await chromium.launch();
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, colorScheme: 'light' });
    for (const [name, url] of SCREENS) {
      await page.goto(BASE + url, { waitUntil: 'networkidle' });
      if (name === 'compare') await page.waitForSelector('h2 i', { timeout: 20000 });
      await page.screenshot({ path: `screenshots/${name}-${w}.png`, fullPage: true });
      console.log(`screenshots/${name}-${w}.png`);
    }
    await page.close();
  }
  await browser.close();
})();
