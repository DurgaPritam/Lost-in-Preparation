/**
 * Exports every glyph in src/components/icons.tsx as a standalone SVG in
 * assets/icons/, for design tools and documentation. The React components
 * remain the source of truth. Run: npm run icons
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { createElement, type ComponentType } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import * as Icons from '../src/components/icons';

const out = join(process.cwd(), 'assets', 'icons');
mkdirSync(out, { recursive: true });
const kebab = (s: string) => s.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();

for (const [name, Icon] of Object.entries(Icons)) {
  if (typeof Icon !== 'function') continue;
  const props: Record<string, unknown> = name === 'IconSort' ? { dir: 'none' } : {};
  // currentColor → ink so the files are visible on their own; the validated
  // glyph's tick uses the surface token, so give it a literal fallback.
  const svg = renderToStaticMarkup(createElement(Icon as ComponentType<Record<string, unknown>>, props))
    .replace(/currentColor/g, '#1E1A15')
    .replace(/var\(--c-surface\)/g, '#FCFAF5')
    .replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
  writeFileSync(join(out, `${kebab(name)}.svg`), svg + '\n');
}
console.log('icons written to assets/icons/');
