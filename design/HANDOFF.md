# HANDOFF: Lost in Preparation

This is for the build agent. For each of the 7 pages and 2 child routes it lists the route, the React file, the components it uses, and the **contract fields it reads**. DESIGN.md explains why things look the way they do. This file covers what to wire.

> **The contract is assumed.** No JSON Schemas were received in any phase. The nine contract files below and their shapes (`src/types.ts`) are the design's working assumption. When the real schemas arrive:
>
> 1. Generate types from them.
> 2. Diff them against `src/types.ts`.
> 3. Fix the mappers in `src/contract/index.ts`.
> 4. Re-run `npm run mock-data`.
>
> Every screen takes its data as props (defaulting to the mocks), so swapping in real data never requires a screen change.

## 0. Contract files and mock data

| File (`mock-data/`) | Type (`src/types.ts`) | Read by |
|---|---|---|
| `recipes.json` | `Recipe[]` | Recipe explorer, Recipe detail, (Home links) |
| `species_profiles.json` | `SpeciesProfile[]` | Compare |
| `studies.json` | `Study[]` | Audit |
| `audit_summary.json` | `AuditBreakdown[]` | Audit |
| `hypotheses.json` | `Hypothesis[]` | Hypotheses |
| `validation.json` | `Validation` | Methods & validation |
| `heuristics.json` | `Heuristic[]` | Methods, Hypotheses drawer, Compare drivers |
| `sources.json` | `SourcesFile` | Data & licences |
| `coverage.json` | `Coverage` | Home |

- **Where the mocks come from.** `mock-data/*.json` is generated from the typed mocks in `src/contract/index.ts` by `npm run mock-data`, so the JSON always typechecks against the types.
- **Mock conventions:**
  - Numbers are repeating digits (0.11, 0.22…).
  - Study titles are prefixed `[MOCK]`.
  - PMIDs are `0000000n`, so their PubMed links will 404.
  - Passages are invented text, not quotations.
  - Dates in `validation.json` are placeholders.
  - Real plant and compound names are used for layout realism only.
- **Null means unknown or not stated, everywhere.** Never coerce null to 0, `false` or `""`. Render it with `UnknownValue`.

## 1. Global

| Concern | Implementation |
|---|---|
| Shell, nav, footer | `AppShell` (`current` = route id from `src/ia.ts`; optional `title`) |
| Tokens / theme | `tokens/tokens.css` + `tailwind.config.ts` (token-only theme). Set `data-theme` on `<html>` for an explicit theme. |
| Source-confidence objects | `SourceConfidence` per source. Mocks: `sourceCulpeper`, `sourcePliny` in `src/gallery/mock.ts`. In production, derive them from `validation.json`, or add a `sources_confidence` contract field. |
| Range comparison | `compareRanges(a, b)` in `src/lib/format.ts`. It is the **only** function allowed to say "enriched" or "weak". |
| Router | `src/screens/App.tsx` is a stand-in **hash** router (`#/recipes`, `#/recipes/:id`, `#/compare?species=`, …) so every screen can be opened directly during review. Production paths are the same without `#`: `/`, `/recipes`, `/recipes/:id`, `/compare?species=`, `/audit`, `/hypotheses`, `/methods`, `/data`. Every internal link goes through an `onNavigate(path)` prop, so swapping the router changes one file. |
| Chart fallbacks | `ChartTable` ("View as table"), placed after every chart. Required by acceptance check 9. |
| Botanical names | `Taxon` (genus and epithet in italics, "sp."/"var." upright). Use it wherever a taxon is rendered as text. |
| Phone tables | `DataTable` stacks into labelled cards below 900px (`stackOnMobile`, on by default). |

## 2. Screens

### Home: `/` → `screens/Home.tsx`

- **Components:** `AppShell`, `Card`, `EvidenceStatusBadge`, `SourceConfidenceMarker`, `ExtractionDetectionExplainer` (panel).
- **Reads:**
  - `coverage.json` → `nameResolutions.validated | provisional | pending`
  - source-confidence objects
- **Static copy:** the artemisinin panels and their citation (Tu 2011, *Nat Med* 17:1217–1220). Ask the historian to check them.
- **Canvas:** `Home.dc.html`, `Home-390.dc.html`.

### Recipe explorer: `/recipes` → `screens/RecipeExplorer.tsx`

- **Components:** `SearchField`, `FilterGroup` ×5, `FilterSummary`, `Button` (mobile filter toggle), `DisputedName` (inline), `SourceConfidenceMarker` (compact), `PrepTag`, `EvidenceStatusBadge`, `ToxicityBadge`, `EmptyState`.
- **Reads, from `recipes.json[]`:**

  | Fields | Used for |
  |---|---|
  | `id` | Link to the detail page |
  | `source` | The source facet |
  | `name.historicalName`, `name.state`, `name.candidates[0].taxon` | The plant facet. `disputed` is its own value; `unresolved` → Unknown. |
  | `preparation.vehicle` | The solvent facet |
  | `preparation.heat` (null → "Not stated") | The heat facet |
  | `preparation.filtered` (null → "Not stated") | The filtration facet |
  | `passage.text` | Search |
  | `evidence`, `toxicity.category` | Badges |

- **Rules:**
  - Every facet includes an Unknown / "Not stated" option, with counts computed against the other active filters.
  - The empty state says what is hidden.
- **Canvas:** `Recipes.dc.html`, `Recipes-390.dc.html`.

### Recipe detail: `/recipes/:id` → `screens/RecipeDetail.tsx`

- **Components:** `SourceConfidenceMarker`, `EvidenceStatusBadge`, `ToxicityBadge` (with sources), `ToxicityNotice`, `Tooltip` (on ⟦?⟧), `UnknownValue`, `DisputedName` (block), `PrepTag`.
- **Reads, from one `Recipe`:**
  - `passage.text`, `passage.edition`, `passage.locator`
  - `passage.fields[].{id, kind, start, end, value, evidence}`. Offsets are `[start, end)` into `text`; `value` null → "Could not normalise".
  - `passage.illegible[].{id, at, estChars, note}`. A marker is inserted at `at`; `estChars` null → "length unknown".
  - `name` (all candidates, with `confidence` and `evidence`)
  - `preparation`, `toxicity.{category, sources, note}`, `evidence`, `source`
- **Rules:**
  - Kinds missing from `fields` are listed as "Not stated in source".
  - **Compare links:**
    - Resolved name, not toxic: one link.
    - Disputed name: one link per candidate.
    - `toxic_reported`: no link at all.
- **Canvas:** `RecipeDetail.dc.html`, `RecipeDetail-390.dc.html`.

### Compare: `/compare?species=` → `screens/Compare.tsx`

- **Components:** `ExtractionDetectionExplainer` (inline and panel), `LoadingState`, `ErrorState`, `ToxicityBadge`, `ToxicityNotice`, `PrepTag`, `PrepLegend`, `SourceConfidenceMarker`, `LikelihoodBar` ×2 per row, `HeuristicMarker`, `UnknownValue`.
- **Reads, from one `SpeciesProfile`** (loaded per species via the `load(taxon)` prop):
  - `taxon`, `fromName.{historicalName, candidateIndex, candidateCount}`, `toxicity`
  - `preparations[].{id, label, preparation, origin}`. `origin.kind` is `recipe` (`recipeId`, `source`) or `study` (`citation`).
  - `preparations[].estimates[].{compound, compoundClass, likelihood.{low, high, point}}`
  - `preparations[].estimates[].drivers[].{id, effect, strength, heuristic, note}`
- **Rules:**
  - "Enriched here" appears only when `compareRanges` returns `a` or `b`.
  - A compound missing from preparation B is shown as Unknown.
  - Loading, error and genus-only states are required.
- **Canvas:** `Compare.dc.html` (interactive; the `previewState` tweak shows loading and error), `Compare-390.dc.html`.

### Audit: `/audit` → `screens/Audit.tsx`

- **Components:** `SourceConfidenceMarker`, local `MatchBar` (tokens only), `FilterGroup`, `FilterSummary`, `DataTable`, local `MatchChip`, `UnknownValue`, `EvidenceStatusBadge`, `Drawer`.
- **Reads:**
  - `audit_summary.json[]` → `source`, `plants`, `studies`, and `vehicle`, `heat`, `filtration`, each holding `{matches, differs, not_stated}`.
  - `studies.json[]`:
    - `id`, `pmid`, `title`, `year`, `taxon`
    - `plantPart`, `solvent`, `heat`, `duration`, `filtered`, `ratio`, each as `{value, evidence}`
    - `comparedRecipeIds`, `match.{vehicle, heat, filtration}`
- **Rules:**
  - The PubMed link is `https://pubmed.ncbi.nlm.nih.gov/{pmid}/`. A null `pmid` shows "Not in PubMed".
  - A null field value renders as "Not stated".
  - The row's "Field evidence" badge shows the **weakest** field status. Per-field statuses are in the drawer.
  - The Pliny note says counts include every candidate species.
- **Canvas:** `Audit.dc.html` (the `openDrawer` tweak opens Study D, which has the most unknowns), `Audit-390.dc.html`.

### Hypotheses: `/hypotheses` → `screens/Hypotheses.tsx`

- **Components:** `Card`, `EvidenceStatusBadge`, `ToxicityBadge`, `ToxicityNotice`, `PrepTag`, `LikelihoodBar` ×2, `SourceConfidenceMarker` (compact), `Button`, `Drawer`, `HeuristicMarker`, `ExtractionDetectionExplainer`.
- **Reads, from `hypotheses.json[]`:**
  - `id`, `rank`, `rankRange`
  - `taxon`, `compound`, `compoundClass`
  - `faithful.{label, preparation}`, `modern.{label, preparation}`
  - `historicalLikelihood`, `modernLikelihood`
  - `attestation[].{source, recipes}`
  - `caveats[]`, `toxicity`, `evidence`
  - `trail[].{id, stage, title, detail, evidence, heuristics[], refs[]}`
  - `heuristics.json` resolves the ids in `trail[].heuristics`
- **Rules:**
  - The **backend** ranks by the conservative gap (`historical.low − modern.high`). The UI only displays `rank` and `rankRange`.
  - Overlapping ranges → the "Weak lead" label.
  - Caveats are always visible.
  - `toxic_reported` → `ToxicityNotice`. Wording stays analytical ("re-test whether … extracts more …").
  - An attestation count of 0 is a known zero, not Unknown.
- **Canvas:** `Hypotheses.dc.html` (the `openTrail` tweak opens rank 1's trail), `Hypotheses-390.dc.html`.

### Methods & validation: `/methods` → `screens/Methods.tsx`

- **Components:** `EvidenceStatusBadge`, `UnknownValue`, `ExtractionDetectionExplainer`, `DataTable` ×2, `Card`, local `IntervalChart` (tokens only), `LikelihoodBar`, `PrepTag`, local `OutcomeMarker`, `HeuristicMarker`.
- **Reads, from `validation.json`:**
  - `pipeline[].{id, name, does, tool (null → "Tool not documented yet"), validation}`
  - `metrics[].{stage, name, value.{point, low, high, unit}, n, evidence, note}`. All-null value → "Not yet measured".
  - `comparisons[].{question, preregisteredId, direction, methods[].{name, value}, finding, decision, evidence}`. This is the **xTB vs RDKit negative result**. `preregisteredId` pulls its Pass/Fail marker from `preregistered[]`.
  - `positiveControls[].{preregisteredId, taxon, compound, a, b, expected, outcome, explanation, evidence}`. This is the **borderline artemisinin result**.
  - A metric whose interval is null never shows its point value; it shows "Interval unknown".
  - `preregistered[].{criterion, registeredOn (null → Unknown), outcome, detail, evidence}`
  - `limitations[]`
  - `heuristics.json[]`
- **Rules:**
  - Outcome markers are ✓ Pass (filled), ✕ Fail (outlined), ◐ Borderline (dashed) and ? Not yet run. They never use toxicity red.
  - "Honest findings" carries the same visual weight as the other sections.
- **Canvas:** `Methods.dc.html`, `Methods-390.dc.html`.

### Data & licences: `/data` → `screens/DataLicences.tsx`

- **Components:** `DataTable`, `EvidenceStatusBadge`, `UnknownValue`.
- **Reads, from `sources.json`:**
  - `sources[].{id, title, role, edition, year, licence, licenceEvidence, url, note}`
  - `downloads[].{file, contract, description, format, licence}`
- **Rules:**
  - A null licence shows "Not yet determined" or "Licence not chosen".
  - `licenceEvidence` is shown beside every licence.
  - Download hrefs assume the contract files are served at `/data/{file}`.
- **Licence facts in the mock:**
  - Public-domain status for Culpeper (1652) and the Bostock & Riley translation, BSD-3 for RDKit, and LGPL-3.0 for xtb are entered as **provisional**.
  - The transcription source, taxonomy backbone and toxicity references are **pending**.
  - **The team must confirm every licence before publishing.**
- **Canvas:** `Data.dc.html`, `Data-390.dc.html`.

## 3. Component → screens matrix

| Component | Home | Recipes | Detail | Compare | Audit | Hypotheses | Methods | Data |
|---|---|---|---|---|---|---|---|---|
| EvidenceStatusBadge | ● | ● | ● | | ● | ● | ● | ● |
| SourceConfidenceMarker | ● | ● | ● | ● | ● | ● | | |
| DisputedName | | ● | ● | | | | | |
| LikelihoodBar | | | | ● | | ● | ● | |
| HeuristicMarker | | | | ● | | ● | ● | |
| ToxicityBadge / Notice | | ● | ● | ● | | ● | | |
| UnknownValue | | ● | ● | ● | ● | | ● | ● |
| ExtractionDetectionExplainer | ● | | | ● | | ● | ● | |
| DataTable | | | | | ● | | ● | ● |
| FilterGroup / Summary | | ● | | | ● | | | |
| Drawer | | | | | ● | ● | | |
| Loading / Error / Empty | | Empty | | Loading, Error | | | | |
| PrepTag / Legend | | ● | ● | ● | | ● | ● | |
| ChartTable | | | | ● | ● | ● | ● | |
| Taxon | | ● | ● | ● | ● | ● | ● | |

## 4. Acceptance checks (please keep them as tests)

1. No null contract value ever renders as `0`, `—`, an empty cell or `false`.
2. No "enriched" or "weak" label is computed anywhere except `compareRanges`.
3. Every `LikelihoodBar` has a visible range text and an `aria-label` with the range.
4. Every table or chart of likelihoods has an `ExtractionDetectionExplainer` on the same screen.
5. A `toxic_reported` record never shows a Compare link or a "try"-style action, and always shows `ToxicityNotice`.
6. Culpeper and Pliny are never merged into one confidence value.
7. At 390px there is no horizontal page scroll; wide tables scroll inside their own box.
8. No copy says "works", "safe", "effective", "cures", "treats" or "recommended".
9. Every chart has a `ChartTable` fallback with the same values.
10. `npm run review` reports 0 axe violations, 0 overflow, 0 focus failures and 0 runtime errors (it does today; see DESIGN.md §11).
