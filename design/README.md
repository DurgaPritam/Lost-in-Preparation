# Lost in Preparation: design handoff

This is the design system, components, seven screens, component gallery and mock data for **Lost in Preparation**, a research tool for EthnoHack 2026 (Track 1: Traditional Knowledge Mining). It is a React + TypeScript + Tailwind project you can run straight away, written so that Claude Code (or anyone) can pick it up and build the real site on top of it.

Everything produced in the design conversation is in this folder, so nothing depends on it.

| Read this | For |
|---|---|
| **DESIGN.md** | Why everything looks and behaves as it does. §4 covers the eight honesty treatments; §11 is the Phase 4 review log, listing every issue found and fixed. |
| **HANDOFF.md** | Screen by screen: route, React file, components used, and the exact contract fields each one reads. |
| **mock-data/README.md** | The mock data conventions. |

> **The data contract is assumed.** No JSON Schemas were provided during design. `src/types.ts` and the nine files in `mock-data/` are the working assumption. HANDOFF.md §0 says how to swap in the real schemas.

## Quick start

Requirements: Node 18.18 or later and npm. The project was verified with **Node 22.23.4 / npm 10.9.9**.

```bash
npm ci                 # installs the exact versions pinned in package-lock.json
npm run dev            # http://localhost:5173
```

Then open:

| URL | What |
|---|---|
| `http://localhost:5173/#/gallery` | Component gallery: every component in every state, with a theme toggle |
| `http://localhost:5173/#/` | Home |
| `…/#/recipes` | Recipe explorer |
| `…/#/recipes/pli-absinthium-vinegar` | Recipe detail: disputed name, illegible text, "could not normalise" |
| `…/#/recipes/cul-wormwood-wine` | Recipe detail: resolved name |
| `…/#/recipes/cul-hemlock-oil` | Recipe detail: toxicity reported, no call to action |
| `…/#/compare` (or `?species=Salvia%20officinalis`) | Compare (loads profiles per species) |
| `…/#/audit` | Audit |
| `…/#/hypotheses` | Hypotheses |
| `…/#/methods` | Methods & validation |
| `…/#/data` | Data & licences (downloads served from `public/data/`) |

To force a theme, add `?theme=dark` or `?theme=light` before the `#`, for example `http://localhost:5173/?theme=dark#/compare`. Without it, the system preference applies.

## Scripts

| Command | Does |
|---|---|
| `npm run dev` | Vite dev server on port 5173 |
| `npm run build` | Production build into `dist/` |
| `npm run preview` | Serves `dist/` on port 4173 |
| `npm run typecheck` | `tsc --noEmit`, strict |
| `npm run mock-data` | Regenerates `mock-data/*.json` and `public/data/*.json` from the typed mocks in `src/contract/index.ts`. Never edit the JSON by hand. |
| `npm run icons` | Re-exports every glyph in `src/components/icons.tsx` to `assets/icons/*.svg` |
| `npm run review` | The strict review harness (see below). Exits 1 on any failure. |

### The review harness

`npm run review` builds the app and serves it. Then, for 11 routes in both themes at 1440px and 390px, it:

- runs **axe-core** (WCAG 2.0/2.1 A + AA, including contrast)
- checks for sideways page scroll
- tabs through each page, checking every focus stop has a visible indicator
- checks that focus is trapped inside dialogs and returns to the trigger
- re-runs axe on each opened drawer, panel and "View as table" state

The report is written to `review-output/report.json`, with full-page 390px screenshots beside it.

It uses Playwright's Chromium. If none is installed, run `npx playwright install chromium` once.

Current result: **0 axe violations, 0 overflow, 0 focus failures, 0 runtime errors.**

## Folder structure

```
.
├── README.md                 this file
├── DESIGN.md                 design decisions + Phase 4 review log (§11)
├── HANDOFF.md                screen → components → contract fields; acceptance checks
├── package.json              exact dependency versions (no ranges)
├── package-lock.json         full lockfile; use `npm ci`
├── index.html                single entry page (gallery and screens via hash routes)
├── vite.config.ts
├── tailwind.config.ts        token-only theme: Tailwind's default palette, sizes and shadows are removed
├── postcss.config.cjs
├── tsconfig.json
├── tokens/
│   ├── tokens.json           SOURCE OF TRUTH: colour (light/dark, with measured contrast), type, space, radius, elevation, motion, layout
│   └── tokens.css            the same values as CSS custom properties (light, dark, system preference)
├── assets/
│   ├── fonts/                EB Garamond, IBM Plex Sans, IBM Plex Mono (woff2, Latin) + fonts.css + OFL licences
│   └── icons/                every glyph as a standalone SVG (generated; the React icons are the source)
├── src/
│   ├── main.tsx              entry: #/gallery → Gallery, anything else → screens
│   ├── styles.css            fonts + tokens + Tailwind layers, focus ring, hatch utility
│   ├── types.ts              ASSUMED contract types (replace with types generated from the schemas)
│   ├── ia.ts                 the 7 routes, the question each page answers, required honesty treatments
│   ├── index.ts              public exports
│   ├── lib/format.ts         formatting, labels, compareRanges() (the only "enriched" logic), slug()
│   ├── components/
│   │   ├── icons.tsx         all glyphs (shape-coded statuses; never emoji)
│   │   ├── honesty/          EvidenceStatusBadge, SourceConfidenceMarker, DisputedName, LikelihoodBar,
│   │   │                     HeuristicMarker, ToxicityBadge + ToxicityNotice, UnknownValue, ExtractionDetectionExplainer
│   │   ├── base/             Button, Tabs, DataTable, Filters, SearchField, Drawer, Tooltip, Card + SourcePassage,
│   │   │                     States (Empty/Loading/Error), PrepTag + PrepLegend, ChartTable, Taxon
│   │   └── layout/AppShell.tsx
│   ├── screens/              Home, RecipeExplorer, RecipeDetail, Compare, Audit, Hypotheses, Methods, DataLicences,
│   │                         App.tsx (stand-in router), mock.ts (recipe + species-profile mocks)
│   ├── gallery/              Gallery.tsx + mock.ts (component-level mocks)
│   └── contract/index.ts     typed mocks, one export per contract file
├── mock-data/                one JSON per contract file (generated) + README
├── public/data/              copy of mock-data/ served at /data/*.json (download links)
├── scripts/                  export-mock-data.ts, export-icons.tsx
├── tests/review.mjs          the review harness
└── design-canvas/            source of the design canvas mocks (see below)
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
| tsx | 4.19.1 | Runs the TypeScript scripts (`mock-data`, `icons`) |
| axe-core | 4.10.0 | Accessibility rules in `npm run review` |
| playwright | 1.63.0 | Browser automation in `npm run review` |
| @types/react | 18.3.3 | Types |
| @types/react-dom | 18.3.0 | Types |
| @types/node | 20.14.10 | Types for scripts |

**No CDN or network dependencies at runtime.** The fonts are vendored in `assets/fonts/`, taken from the @fontsource packages v5.1.0. All three families are under the SIL Open Font License 1.1, and the licence files are included.

## Design canvas

`design-canvas/` holds the source of the visual design canvas (`*.dc.html` artboards plus `canvas.json`), across three pages: the design system, the core screens and the remaining screens. Each is shown at desktop width and at 390px.

These files are **a visual reference only**. They render inside the Claude Design canvas runtime (`support.js`), not in a normal browser. The live canvas is at https://claude.ai/artifact/SLuesjQExJ9a799m28wRMH; it is private to its owner until shared.

**The React code in `src/` is the source of truth.** Where they differ (the "View as table" fallbacks and the stacked mobile tables exist only in React), follow `src/`. DESIGN.md §11 lists the differences.

## Rules for whoever builds on this

These are short versions; DESIGN.md §10 and HANDOFF.md §4 have the full lists.

- **Use tokens only.** Need a new colour or size? Add it to `tokens/tokens.json`, `tokens.css` and `tailwind.config.ts`, and record its contrast.
- **Null means unknown.** Never render null as 0, "—", blank or "no". Use `UnknownValue`.
- **Ranges first.** Never show a likelihood without its range, and never decide "enriched" anywhere except `compareRanges`.
- **Culpeper and Pliny are never merged.** Disputed names are never collapsed to one species.
- **Toxicity reported** means `ToxicityNotice` and no call to action.
- **No medical claims.** Avoid "works", "safe", "effective", "cures", "treats", "recommended" and similar words.
- **Keep the review green.** Run `npm run review` before merging. It must stay at zero.
