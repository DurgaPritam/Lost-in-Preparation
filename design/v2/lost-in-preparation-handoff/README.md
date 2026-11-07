# Lost in Preparation: design handoff (v2)

A preparation-aware research tool for EthnoHack 2026, Track 1.

> Historical remedies were recipes, not just plants. See what each preparation actually extracts.

This folder holds everything the build agent needs, so nothing lives only in the design conversation:

- Design tokens.
- A React + TypeScript + Tailwind reference implementation of every component and screen, in two themes: **Herbarium** (light) and **Nocturne** (dark).
- Mock data in the contract shapes.
- Screenshots of every screen.
- The design-canvas source.
- The docs.

| Read first | For |
|---|---|
| `DESIGN.md` | Identity, themes, tokens, IA, screens, honesty treatments, motion, review log |
| `HANDOFF.md` | Screen → file → components → contract fields, plus acceptance checks |
| `screens/` | Every screen, light and dark, at 1440 and 390 (`<route>-<theme>-<width>.webp`) |

**The JSON Schemas were never attached.** `src/types.ts` is the design's assumption about the contract. v2 only adds to it (DESIGN.md §9).

## Quick start

Needs Node 20+ (built with Node 22.23.4 / npm 10.9.9).

```bash
npm ci
npm run dev            # http://localhost:5173
```

| Open | Shows |
|---|---|
| `#/` | Landing |
| `#/lab` | Preparation Lab (try `#/lab?plant=Conium%20maculatum` or `#/lab?solvent=honey&heat=warm`) |
| `#/atlas`, `#/recipes/cul-liquorice-decoction` | Recipe Atlas and a recipe page |
| `#/evidence-gap` | The evidence gap |
| `#/case/liquorice` | Case study |
| `#/planner` | Lab Planner |
| `#/docs` | Methods & data |
| `#/gallery` | Every component in every state |

**Theme.** Use the toggle in the header; the choice is remembered. Add `?theme=dark` or `?theme=light` before the `#` to force one.

## Scripts

| Script | Does |
|---|---|
| `npm run dev` / `build` / `preview` | Vite |
| `npm run typecheck` | `tsc --noEmit` (strict) |
| `npm run mock-data` | Writes `mock-data/*.json` and `public/data/*.json` from `src/contract/` |
| `npm run icons` | Exports `assets/icons/*.svg` from `src/components/icons.tsx` |
| `npm run review` | The accessibility, overflow and focus harness (below) |

### The review harness

`npm run review` builds and serves the app, then for **15 routes × 2 themes × 2 widths (1440, 390)** it:

- runs axe-core (WCAG 2.0/2.1 A + AA, including contrast);
- checks for horizontal page overflow;
- opens drawers, popovers, toggles and table fallbacks, re-running axe in each opened state;
- checks dialog focus trapping and return, and walks the focus order at 1440 light.

It writes `review-output/report.json` and full-page screenshots, and exits 1 on any issue. **Today it reports 0 issues.** Playwright needs a Chromium; run `npx playwright install chromium` once if none is available.

## Folder structure

```
assets/
  fonts/               six OFL families (woff2) + fonts.css + licences
  icons/               exported SVG icons
design-canvas/         canvas source (*.dc.html + canvas.json); visual reference only
docs/review-log-v1.md  Phase 4 review log (kept for the record)
mock-data/             the 12 contract files as JSON (generated)
public/data/           the same files, served for the Docs download links
screens/               screenshots of every screen + review-report.json
scripts/               export-mock-data.ts, export-icons.tsx
src/
  types.ts             the assumed contract (v2 additions at the end)
  ia.ts                routes, page questions, honesty treatments per page
  contract/            typed mocks: index.ts, recipes.ts, lab.ts (toy Lab model)
  lib/format.ts        compareRanges, wilson, pct, labels…
  components/
    base/              Button, Controls, Popover, Tooltip, Drawer, DataTable, ChartTable,
                       PlateSlot, PlantCard, PrepTag, States, SearchField, Filters, Tabs, Taxon, Card
    honesty/           the eight treatments
    layout/SiteShell   header, nav, theme toggle, footer
  screens/             Landing, Lab, Atlas (+ RecipePage), EvidenceGap, CaseStudy, LabPlanner, Docs, App (router)
  gallery/             Gallery.tsx + mock.ts
  styles.css           base styles, hatches, motion utilities
tests/review.mjs       review harness
tokens/                tokens.json (source), tokens.css (both themes)
tailwind.config.ts     token-only theme
```

## Dependencies (exact versions)

**Runtime**

| Package | Version | Why |
|---|---|---|
| react | 18.3.1 | UI |
| react-dom | 18.3.1 | UI, plus the portal used by Drawer |

**Development**

| Package | Version | Why |
|---|---|---|
| vite | 5.4.8 | Dev server and build |
| @vitejs/plugin-react | 4.3.2 | JSX / fast refresh |
| typescript | 5.5.4 | Strict typechecking |
| tailwindcss | 3.4.10 | Utility CSS, token-only theme |
| postcss | 8.4.47 | Tailwind pipeline |
| autoprefixer | 10.4.20 | Tailwind pipeline |
| tsx | 4.19.1 | Runs the TypeScript scripts |
| axe-core | 4.10.0 | Accessibility rules in `npm run review` |
| playwright | 1.63.0 | Browser automation in `npm run review` |
| @types/react | 18.3.3 | Types |
| @types/react-dom | 18.3.0 | Types |
| @types/node | 20.14.10 | Types for scripts |

**Fonts** (vendored from @fontsource 5.3.0, all SIL OFL 1.1, licence files included):

| Theme | Display | Text | Numbers |
|---|---|---|---|
| Herbarium | Fraunces | Instrument Sans | JetBrains Mono |
| Nocturne | Instrument Serif | Hanken Grotesk | DM Mono |

There are no CDN or network dependencies at runtime.

## Design canvas

`design-canvas/` holds the canvas source:

- Pages 1–3: the v1 design system and screens.
- Page 4: the two visual directions (you chose both, as themes).
- Page 5: v2 build screenshots of every screen.

These files render only inside the Claude Design canvas runtime. The live canvas is at https://claude.ai/artifact/SLuesjQExJ9a799m28wRMH; it is private to its owner until shared. **`src/` is the source of truth.**

## Rules for whoever builds on this

These are short versions. DESIGN.md §11 and HANDOFF.md §4 have the full lists.

- **Tokens only.** Record contrast in both themes.
- **Null means unknown.** Use `UnknownValue`.
- **Ranges first.** Comparisons come only from `compareRanges`.
- **Never merge Culpeper and Pliny**, and never settle a disputed name.
- **Toxicity reported** means `ToxicityNotice` and no action, anywhere.
- **The Lab never interpolates.** The Planner never fakes a quantum score.
- **Every plate shows its licence.** Confirm each Commons file before shipping.
- **No medical claims.**
- **Keep `npm run review` at zero.**
