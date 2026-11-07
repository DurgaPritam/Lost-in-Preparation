# HANDOFF: Lost in Preparation (v2)

For the build agent. Each screen is mapped to its route, its file, the components it uses and the contract fields it reads. DESIGN.md explains why; this file explains what goes where.

**The React code in `src/` is the reference implementation.** It typechecks in strict mode, builds, and passes `npm run review` with zero issues. Swap the hash router and the mock imports, and keep everything else.

---

## 0. Contract files and mock data

`mock-data/*.json` (and the copy in `public/data/`) is generated from the typed mocks in `src/contract/` by `npm run mock-data`, so the JSON always matches `src/types.ts`.

| File | Type | Read by | New in v2 |
|---|---|---|---|
| `recipes.json` | `Recipe[]` | Atlas, recipe page, Case study | |
| `species_profiles.json` | `SpeciesProfile[]` | Lab, Landing demo, Case study | more combinations |
| `studies.json` | `Study[]` | Docs (Audited studies) | `material?` |
| `audit_summary.json` | `AuditBreakdown[]` | Evidence gap ("did it match") | |
| `hypotheses.json` | `Hypothesis[]` | Planner (bars, drawer), Case study | liquorice lead |
| `validation.json` | `Validation` | Docs | |
| `heuristics.json` | `Heuristic[]` | Lab "Why?", Docs, Planner drawer, Case study | |
| `sources.json` | `SourcesFile` | Docs | 3 download rows |
| `coverage.json` | `Coverage` | Docs overview | |
| `reporting_gap.json` | `ReportingGapFile` | Evidence gap, Landing teaser | **new** |
| `plates.json` | `Plate[]` | Landing, Atlas, recipe page, Lab, Case study | **new** |
| `lab_plan.json` | `LabPlanFile` | Planner | **new** |

**Null means unknown or not stated, everywhere.** Never coerce null to 0, `false` or `""`. Render it with `UnknownValue`.

### Mock conventions
- Numbers are repeating digits (0.11, 0.22…).
- Study titles carry `[MOCK]`, and passages carry `[MOCK]` too.
- The case-study copy is `[MOCK STORY]`.
- PMIDs are `0000000n`.
- Real plant and compound names are used for layout realism only.

### The Lab's toy model
`src/contract/lab.ts` produces the profiles. It is a **placeholder generator, not science.** It exists so the Lab has many combinations to show; replace it with the pipeline's `species_profiles.json`. The ids follow `<solvent>-<heat>-<f|n>-<a|n>` (filtered, acidified), for example `water-boiled-f-n`.

---

## 1. Global

| Concern | Implementation |
|---|---|
| Shell | `SiteShell` (`current` = a route id from `src/ia.ts`; `bleed` for full-width pages) and `PageHeader` |
| Themes | `tokens/tokens.css`. Light is the default. `data-theme="dark"` on `<html>` forces Nocturne; with no attribute, `prefers-color-scheme` decides. `ThemeToggle` saves the choice to `localStorage['lip-theme']`. `applyStoredTheme()` runs before the first render in `main.tsx`, so the page doesn't flash the wrong theme. `?theme=light\|dark` forces a theme for review. |
| Fonts | `assets/fonts/fonts.css` (vendored, OFL). Font families are CSS variables per theme. |
| Router | `src/screens/App.tsx` is a stand-in **hash** router; the paths are listed there. Every internal link goes through `onNavigate(path)`, so swapping the router changes one file. Lab settings travel in the query: `?plant=&solvent=&heat=&strained=&acid=`. |
| Range comparison | `compareRanges(a, b)` in `src/lib/format.ts`. It is the only source of "higher", "lower" and "overlaps". |
| Statistics helpers | `wilson(k, n)` (95% interval), `pct`, `meanWidth` (the trigger for the wide-uncertainty banner). |
| Chart fallbacks | `ChartTable` ("View as table") after every chart. |
| Phone tables | `DataTable` stacks into labelled cards below 900px. |
| Botanical names | `Taxon` everywhere a taxon is printed as text. |
| Images | `PlateSlot` only. Never a bare `<img>` for a plate, because the slot carries the licence caption. |

---

## 2. Screens

### Landing: `/` → `screens/Landing.tsx`
- **Components:** `SegmentedControl` (Cold water / Decoction), `LikelihoodBar` (with `compare` when the overlay is on), `PlateSlot`, `ExtractionDetectionExplainer`, `EvidenceStatusBadge`, `SourceConfidenceMarker`, `ToxicityBadge`, `UnknownValue`, `LinkButton`.
- **Data:**
  - `species_profiles` for *Glycyrrhiza glabra*: `water-cold-f-n`, `water-boiled-f-n` and `modern-methanol`.
  - `reporting_gap.rows[field = headline.field]`.
  - `plates`.
- **Behaviour.** Changing the preparation animates the bars. The overlay checkbox draws the modern outline band.

### Preparation Lab: `/lab` → `screens/Lab.tsx`
- **Components:** `SegmentedControl` (solvent, heat), `Switch` (filtration, acidity, compare modern), `LikelihoodBar`, `Popover` ("Why?"), `HeuristicMarker`, `ToxicityBadge`, `ToxicityNotice`, `PrepTag`, `PrepLegend`, `PlateSlot`, `LoadingState`, `EmptyState`, `ChartTable`, `ExtractionDetectionExplainer`.
- **Data:**
  - `species_profiles[taxon].preparations[]`: `preparation.{vehicle, heat, filtered, acidified}` select the profile, and `estimates[].{compound, compoundClass, likelihood, drivers[]}` fill it.
  - The toxicity record.
  - `plates`.
- **Rules:**
  - Match on all four settings exactly. **No match means the no-data state**, which lists the available combinations as buttons.
  - Vinegar forces `acidified = true`.
  - A delta chip compares against the previous setting that had data, using `compareRanges`.
  - The wide banner appears when `meanWidth ≥ 0.4`.
  - `toxicity.category === 'toxic_reported'` shows `ToxicityNotice` and hides "Plan an experiment".
  - A genus-only plant (no profile) gets its own empty state.
  - An `aria-live` region announces each change.
- **Loader.** `loadLabProfile(taxon)` returns a Promise (700ms mock latency). Replace it with a fetch.

### Recipe Atlas: `/atlas` → `screens/Atlas.tsx` (`Atlas`)
- **Components:** `SearchField`, filter chips (`aria-pressed` buttons in a group labelled "Filters"), `PlantCard`, `DisputedName` (inline), `ToxicityBadge`, `EmptyState`.
- **Data:** `recipes[]`, grouped by `name.candidates[0].taxon` (or by the historical name when disputed or unresolved), and `plates`.
- **Search.** Covers the historical name, candidate taxa, the passage text and normalised field values, case-insensitive.

### Recipe page: `/recipes/:id` → `screens/Atlas.tsx` (`RecipePage`)
- **Components:** passage renderer (numbered highlighted spans, ⟦?⟧ `Tooltip`), field cards, `EvidenceStatusBadge`, `UnknownValue` ("Not stated in source"), `PlateSlot` (hero), `DisputedName` (block), `PrepTag`, `SourceConfidenceMarker`, `ToxicityBadge`, `ToxicityNotice`.
- **Data:** `recipe.passage.{text, fields[], illegible[], edition, locator}`, `recipe.name`, `recipe.preparation`, `recipe.toxicity` and `recipe.evidence`.
- **Lab link.** `/lab?plant=…&solvent=…&heat=…&strained=…`, built only from stated fields. Disputed names get one link per species candidate. **Toxic-reported recipes get no Lab link.**

### The evidence gap: `/evidence-gap` → `screens/EvidenceGap.tsx`
- **Components:** `Tooltip` on each row button, `SegmentedControl` (sort order), `ChartTable`, `EvidenceStatusBadge`, `SourceConfidenceMarker`, `UnknownValue`.
- **Data:** `reporting_gap.{headline, method, rows[].{field, label, stated, n, ci, evidence}}` and `audit_summary[]` (per source: `vehicle`, `heat`, `filtration` as `{matches, differs, not_stated}`).
- **Rule.** `ci: null` prints "not computed". Never draw a whisker without data.

### Case study: `/case/liquorice` → `screens/CaseStudy.tsx`
- **Components:** `LikelihoodBar`, `PrepTag`, `PrepLegend`, `HeuristicMarker`, `SourceConfidenceMarker`, `EvidenceStatusBadge`, `ToxicityBadge`, `ToxicityNotice`, `PlateSlot`, `ExtractionDetectionExplainer`.
- **Data:**
  - Liquorice `species_profiles` (`modern-methanol`, `water-boiled-f-n`).
  - The `recipes` entry `cul-liquorice-decoction`.
  - The `hypotheses` entry `h-glycyrrhizin-decoction`.
  - The `lab_plan` item for that hypothesis (for its Planner rank).
  - `heuristics.heat_sensitivity`.
- **Copy.** The chapter text is a `[MOCK STORY]` placeholder. Replace it with the team's analysis and keep the four-part structure.

### Lab Planner: `/planner` → `screens/LabPlanner.tsx`
- **Components:** `Switch` (disabled), `LikelihoodBar`, `MarkHist`/`MarkMod`, `EvidenceStatusBadge`, `ToxicityBadge`, `UnknownValue`, `Drawer` (evidence trail), `HeuristicMarker`, `ChartTable`.
- **Data:**
  - `lab_plan.feature.{name, status, release, description}`.
  - `lab_plan.items[].{title, compares, readout, effort, rank, rankRange, quantumScore, hypothesisId}`.
  - The linked `hypotheses[]` entry, for its bars, trail, evidence and toxicity.
- **Rules:**
  - `quantumScore === null` shows "Coming in this release".
  - Hypotheses whose toxicity is `toxic_reported` are **not** planned; a note counts and names them.
  - When the feature ships, set `status: 'available'` and fill `quantumScore` with a **range**. The switch may then reorder the list; leave the default order as the conservative gap.

### Methods & data: `/docs` → `screens/Docs.tsx`
- **Components:** table-of-contents nav (`aria-current="location"`), `DataTable`, `ChartTable`, `LikelihoodBar` (neutral family for metrics), `EvidenceStatusBadge`, an `OutcomeMarker` (local: Pass / Fail / Borderline / Not run yet, with an icon and a word), `HeuristicMarker`, `SourceConfidenceMarker`, `ExtractionDetectionExplainer` (panel), `UnknownValue`.
- **Data:** `validation.{pipeline, metrics, comparisons, positiveControls, preregistered, limitations}`, `studies[]`, `heuristics[]`, `sources.{sources, downloads}`, `coverage`, and `CONTRACT_FILES` (download list).
- **Rule.** A metric with no interval prints "interval unknown". A metric with no values prints "Not measured". Never print a bare point.
- **Sections** have ids for deep links: `overview`, `pipeline`, `metrics`, `findings`, `preregistered`, `heuristics`, `studies`, `limitations`, `sources`, `downloads`.

### Gallery: `#/gallery` → `gallery/Gallery.tsx`
Every component in every state, with the theme toggle. For review only, not for production.

---

## 3. Component → screens

| Component | Landing | Lab | Atlas | Recipe | Gap | Case | Planner | Docs |
|---|---|---|---|---|---|---|---|---|
| EvidenceStatusBadge | ● | | | ● | ● | ● | ● | ● |
| SourceConfidenceMarker | ● | | | ● | ● | ● | | ● |
| DisputedName | | | ● | ● | | | | |
| LikelihoodBar | ● | ● | | ● | | ● | ● | ● |
| ExtractionDetectionExplainer | ● | ● | | | | ● | | ● |
| HeuristicMarker | | ● | | | | ● | ● | ● |
| ToxicityBadge / Notice | ● | ● | ● | ● | | ● | ● | |
| UnknownValue | ● | ● | ● | ● | ● | | ● | ● |
| PlateSlot | ● | ● | ● | ● | | ● | | |
| ChartTable | | ● | | | ● | | ● | ● |

---

## 4. Acceptance checks (please keep them as tests)

1. No null contract value ever renders as `0`, `—`, an empty cell or `false`.
2. "Higher", "lower" and "overlaps" are computed only by `compareRanges`.
3. Every `LikelihoodBar` shows its range as text and speaks it in its `aria-label`.
4. Every screen with likelihoods shows `ExtractionDetectionExplainer`.
5. A `toxic_reported` record never gets a Lab link, a "Plan an experiment" action or a Planner slot, and always shows `ToxicityNotice` where its profile appears.
6. Culpeper and Pliny are never merged into one confidence value.
7. A disputed name is never displayed as one settled species.
8. The Lab never shows a profile for a combination that isn't in the data.
9. `quantumScore` null shows "Coming in this release", never 0.
10. Every plate slot shows its licence, host and status.
11. At 390px there is no horizontal page scroll.
12. No copy says "works", "safe", "effective", "cures", "treats", "heals" or "recommended".
13. Every chart has a `ChartTable` fallback with the same values.
14. Both themes pass. `npm run review` reports 0 axe violations, 0 overflow, 0 focus failures and 0 runtime errors (it does today; see DESIGN.md §12).
