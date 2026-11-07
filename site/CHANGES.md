# Site changes from the Claude Design v2 handoff

The site is built from the v2 handoff in [`design/v2/lost-in-preparation-handoff/`](../design/v2/lost-in-preparation-handoff/) (extracted from `design/lost-in-preparation-handoff (1).zip`, which is kept). The v1 system (tokens, components, screens and routes) has been removed from `site/`; the two systems are not mixed.

- **Tokens:** used unchanged. [`styles/tokens.css`](styles/tokens.css) and [`styles/tokens.json`](styles/tokens.json) are byte-for-byte copies of the handoff's `tokens/`. `styles/globals.css` is the handoff's `src/styles.css`; `styles/fonts.css` is its `assets/fonts/fonts.css` with the URLs pointing at `/fonts/`.
- **Tailwind theme:** the handoff's file, with only the `content` globs changed.
- **Components:** [`components/`](components/) holds the handoff's files with the import paths rewritten and `'use client'` added where they hold state. 20 of the 26 are otherwise identical. The six that differ are listed below, and each change carries a `SITE:` comment in the code.

This file lists every change I could not avoid, and every addition.

## Changes to design components

| Component | Change | Why |
|---|---|---|
| `layout/SiteShell` | Links use Next's `Link`; the `onNavigate` prop is gone. | The handoff's hash router is a stand-in (HANDOFF §1); the site uses the real router. |
| `layout/SiteShell` | `THEME_BOOT_SCRIPT` exports the handoff's `applyStoredTheme` logic as an inline `<head>` script. | A statically exported page has to apply the stored theme (or `?theme=`) before the first paint. |
| `layout/SiteShell` | `ThemeToggle` starts as `light` and reads the theme after mount; it writes `data-theme` only on click. | The static HTML cannot know the reader's theme, so reading it during render caused a hydration mismatch. |
| `layout/SiteShell` | The footer has a Credits link beside Methods & data; `current` accepts `'credits'`. | The image licences need a public page (see Additions). |
| `base/PlantCard` | `recipes` holds one count per source: Culpeper 1652, Culpeper 1850 and Pliny. | The corpus has two Culpeper editions, and HANDOFF §4.6 says sources are never merged. |
| `base/PlateSlot` | Renders a `<picture>` with AVIF and WebP `srcset` (240, 480, 720 and 960 px, or the original's own width when smaller), `sizes` (the mobile size subtracts the page gutters), explicit `width`/`height`, and `loading="lazy"`, so a slot hidden at the current width (the recipe hero on phones) is never downloaded; the hero is fetched with high priority when shown. | The plates are downloaded and served locally, never hotlinked. Explicit sizes prevent layout shift. |
| `base/PrepTag` | Uses `vehicleLabel()`; adds "filtering not applicable". | The contract has solvent mixtures ("wine + honey") and a real `not_applicable` filtration value (ointments, amulets). |
| `honesty/DisputedName` | A candidate without an interval shows "Interval unknown", with the heuristic score in the reason. | M2 gives a heuristic match score with no interval. Drawing it as a range would invent one. |
| `honesty/LikelihoodBar` | The band's width is `clamp(high) − clamp(low)`. | An interval running past the track (e.g. 1.2 on a 0–1 track) widened the page at 390 px. The bar now stops at the edge, and the numbers are unchanged. |
| `base/Link` (site only) | next/link with prefetch off. | Prefetching pulled other pages' payloads on every load. |

## Changes forced by the real data

| Area | Handoff assumed | Real data, and what the site does |
|---|---|---|
| Landing and Lab default plant | Liquorice (*Glycyrrhiza glabra*) | Liquorice has toxicity reported in this data, and a front-door "try it" must never feature a toxic plant. The landing demo and the Lab default to *Salvia sclarea* (no toxicity reported). Liquorice remains in the Lab (with its toxicity notice), the Atlas and the case study. |
| Lab profiles | `species_profiles.json` with pre-computed combinations, matched exactly on four settings | Profiles are computed live by the preparation engine (`lib/engine`, contract v1.7 P38) in a Web Worker. The engine is the M4 model in TypeScript, and the build fails unless it reproduces every published Python estimate exactly. Each grid setting maps to a pipeline preparation (boiled → decoction, water → infusion, otherwise maceration). |
| Acidity | Any solvent can be acidified | The model represents acidity only through vinegar (basic nitrogen in an acid vehicle). "Acidified" with another solvent gets the designed no-data state, with buttons for the nearest modelled combinations; the Lab never invents an estimate. Vinegar forces acidity on, as specified. |
| Modern comparison | `modern-methanol` profile | The pipeline's modern preset, "modern methanol extract", computed by the same engine. |
| Lab list length | Every compound | A species can have hundreds of compounds. Each class shows its 12 highest medians first, with "Show all". |
| Lab "Plan an experiment" | Shown unless toxic | Unchanged. It links to the Planner, which is a placeholder. |
| `reporting_gap.json` | A separate file | Derived from `metrics.reportingGap` (contract v1.6, P37b). The headline field is fresh/dried, as in the handoff, stated as a count ("k / n studies state…") rather than the mock sentence. |
| Evidence gap: the solvent row | — | Carries the inflated-by-construction caveat wherever it appears: audit eligibility already requires a stated solvent. |
| Evidence gap: "did it match" | `audit_summary` | Uses audit v2 (the pre-registered re-analysis), with its small-n note, and links to v1 (as pre-registered, with its design flaw) in Methods & data. |
| `lab_plan.json` | A separate file with readout, effort and rank range | Derived from `hypotheses.json`. Readout and effort are not decided anywhere in the data, and the ranking records no rank interval, so they show "Not decided" / "Not estimated". The quantum score is null: "Coming in this release". |
| Planner: withheld leads | — | Hypotheses 1 and 2 have toxicity reported, so they are withheld and named, as specified. The list is the remaining lead(s). |
| Planner bar | A compound likelihood | A hypothesis is a species-level profile gap (1 − cosine similarity) with an interval, and the bar shows that gap. |
| Case study copy | `[MOCK STORY]` placeholder | Replaced by the project's own analysis from `case_studies.json` (P37d), the corrected recipes and the published profiles, in the four-part structure. The before/after figures are the five compounds whose medians separate most between the two published profiles. |
| Case study ending | "Try it in the Lab" and the Planner rank | Liquorice has toxicity reported, so the page ends on the ToxicityNotice with no Lab or Planner action (HANDOFF §4.5). The lead is withheld from the Planner, so there is no Planner rank to show. |
| Atlas source chips | Culpeper, Pliny | Three source chips (Culpeper 1652, Culpeper 1850, Pliny), plus the handoff's disputed, heat-stated and strained chips. |
| Atlas card subtitle | A common name | The data has no common names, so the card shows the historical name as written (in quotes when disputed). No names are invented. |
| Recipe page | Passage fields | The passage is the real transcription. Quotes that overlap a drawn span, or come from the entry heading, are listed in the field cards but not drawn. M1 never extracts quantity, so quantity is not listed as "not stated". Logged corrections (P37a) get their own section, with evidence. Lab links are built only from stated fields, one per species candidate with a profile, and none for toxic-reported plants. |
| Methods & data: studies | `studies[]` with duration and ratio | These are the real audit rows, loaded per version (v1 and v2 in tabs). The extractor codes neither duration nor ratio, so the columns are fresh/dried and plant part instead. An outcome recorded but not graded reads "Outcome not graded". |
| Plates | `plates.json` | Added as **contract v1.8, P39** (`PlateRecord`, written by `python -m lip plates`). The file is proposed and implemented; see `contract/CHANGELOG.md`. |

## Additions

- **Credits page** (`/credits/`): every botanical plate with its Commons source URL, author, date, work and licence, plus the font and code licences. The same records are in [docs/IMAGE_CREDITS.md](../docs/IMAGE_CREDITS.md); both are written from `site-data/plates.json`.
- **Plates:** 15 species have a plate, chosen by script from Köhler's *Medizinal-Pflanzen*, then Thomé, then Sturm, taking only files whose Commons licence field is public domain. They are downloaded once and resized to AVIF/WebP. The 4 species with no suitable file get the design's empty plate slot. Every plate's status is "sourced" (licence read from Commons by script), not "confirmed" (checked by a person).
- **Shareable addresses:**
  - every Lab configuration: `/lab/?plant=&solvent=&heat=&strained=&acid=&modern=` (`modern` is added for the comparison overlay);
  - every Atlas search: `?q=`;
  - every plant: `/atlas/?plant=`;
  - every recipe: `/recipes/<id>/`;
  - the case study: `/case/liquorice/`.
- **Old v1 addresses** (`/recipes/`, `/compare/`, `/audit/`, `/hypotheses/…`, `/methods/`, `/data/`, `/case-studies/liquorice/`) forward to their v2 pages. A static export cannot send a server redirect, so each is a stub page that replaces the location; `vercel.json` adds real 301s on the host.
- **Not shipped:** the handoff's Gallery (`#/gallery`), which is for review only.

## Engine responsiveness

- **Web Worker:** the engine runs in `lib/engine/worker.ts`, so the page never blocks. It computes in chunks of 24 compounds and yields between chunks.
- **Cancellation:** a newer request on the same channel cancels the older one in the worker, and the page ignores any stale result that still arrives.
- **Previous result:** while a new profile computes, the previous one stays visible, marked as updating (`data-engine-status="updating"`).
- **Cache:** results are cached in memory per (species, preparation), in both the worker and the page.
- **Parity:** `npm run engine:parity` runs in `prebuild` and fails the build on any difference.
- **Latency:** `npm run lab:latency` measures the UI's response and the time to a new profile at 1×, 2× and 4× CPU slowdown ([lib/engine/README.md](lib/engine/README.md#responsiveness-in-the-lab), results in `lib/engine/latency-report.json`). Chrome cannot throttle a worker, so the slowed engine time is a labelled estimate.

## Performance and accessibility

- **Font fallbacks:** `styles/font-fallbacks.css` adds metric-matched fallback faces for all six v2 families, written by [scripts/font-fallbacks.py](scripts/font-fallbacks.py) with fontTools.
  - **How:** each face is a local Times New Roman, Arial or Courier New (or the metric-compatible Liberation font on Linux), scaled to the web face's average character width and vertical metrics.
  - **Token stacks:** the design's stacks for both themes, with the fallback family inserted after the web font. `tokens.css` itself is untouched; the override is imported after it.
  - **Why:** headings and paragraphs re-wrapped when the web faces swapped in (a large Lighthouse layout-shift penalty on the recipe and docs pages).
- **Fraunces file size:** `scripts/pin-fraunces-opsz.py` writes the two Fraunces files with the optical-size axis pinned at 144, which roughly halves each file; the weight axis is kept. The site sets Fraunces only through `.font-display`, which always applies `opsz 144`, so rendering is unchanged (a pixel comparison across weights and styles showed only anti-aliasing differences). The OFL permits modified versions, and Fraunces declares no Reserved Font Name.
- **Font preload:** an inline script in `app/layout.tsx` preloads the active theme's display face and its body faces (400 and 600), after the theme script has decided the theme. A dark-theme reader therefore never downloads the light faces first.
- **Atlas:** the plant cards render statically. The recipe index (`/data/recipe-index.json`) loads only when a search or filter is used.
- **Methods & data:** the audited-study rows load per version, only when their section comes within about a screen of the viewport (IntersectionObserver; until 2026-11-07 they loaded on mount, which put about 7,000 nodes on the first load). The AI-assisted check metrics (provisional) sit in a second table that renders on request. Together these took the page's first-load DOM from about 10,400 to about 1,500 nodes, which brought CI Lighthouse back above 90.
- **Lighthouse:** runs in both themes (`LH_SCHEME=light|dark`; headless Chrome otherwise follows the OS theme), locally and in CI. Each run writes its medians to `perf/lighthouse-<theme>.json`.
- **Scroll regions:** wide tables are focusable regions with labels (axe `scrollable-region-focusable`).
- **Wrapping:** long compound names wrap (`break-words`, `min-w-0`), so no page scrolls sideways at 390 px.

## Validation wording (project lead, 2026-11-07)

- **Badge wording:** `EvidenceStatusBadge` takes an optional `wording="validation"`. Methods & data uses it, so each validation item reads "Human-validated", "AI-assisted check (provisional)" or "Human validation pending". The shape, border and colour are the design's; only the word and explanation change. Elsewhere (a recipe's fields, for example) "Provisional" still means "made by an AI, not yet checked", so the default wording stays there.
- **Stage statuses:** the preparation model (M4) is no longer shown as validated. Only its logP descriptor is human-validated (against measured data); the model itself has only AI-assisted checks. M5 shows its AI-assisted check. M1 shows "Human validation pending", because the AI reference set is never used to score it. The artemisinin test is an AI-assisted check, since an AI wrote its criteria.
- **Credits:** a column shows each plate's AI check (licence templates on the page, the statement "checked by AI agent on <date>; awaiting human confirmation", and any flags). The lead no longer calls all plates 19th-century (the Sturm plates are dated 1796).

## Four validation statuses and the reporting-gap sensitivity (project lead, 2026-11-07)

- **Four statuses:** Methods & data uses `ValidationStatus` = the three evidence statuses plus `external` ("Validated against external data": compared with an independent published dataset, such as measured logP values). The badge draws `external` with the design's solid "validated" shape and a brand border; the word tells it apart from a person's check. The logP descriptor check is `external`. A unit test guards this, and checks that no AI-assisted check is ever validated.
- **Evidence gap:** under each row, a line labelled "AI-assisted sensitivity check (provisional)" gives the share the row would have if the extractor's error rates from the AI check applied, with its interval, plus the counts on the 40 checked studies by the extractor and by the AI coder. Filtration reads "not computed", because it was not in the AI check. The frozen bar, numbers and interval are unchanged. The table fallback has the same column.
- **Köhler plates:** described by the series' publication span (1883–1898) instead of 1887, because no per-plate edition date could be read (see docs/IMAGE_CREDITS.md).

## Lab Planner and "Where quantum helps" (proposal approved 2026-11-07, docs/LAB_PLANNER_PROPOSAL.md)

- **Lab Planner:** the "Coming in this release" state is replaced by the re-test panel from `site-data/lab_panel.json` (contract v1.9, P40 with its v2 amendment).
  - **Which panel:** the displayed panel is rule v2 (pre-registered, docs/QUBO_v2_RULE.md). The original v1 result stays visible below it, with its notes (slot 8 entered on coverage alone).
  - **Layout:** the design's Planner sections and components are kept: a feature card with a panel-size SegmentedControl, a coverage strip, list items with MarkHist/MarkMod, LikelihoodBar, ToxicityBadge and a HeuristicMarker for "compounds likely to differ", the evidence trail Drawer, and a ChartTable fallback.
  - **Toxic plants:** there is no toxic toggle. Plants with toxicity reported are excluded and listed in a plain note.
  - **Heading:** "Suggested panel", because "recommended" is on the honesty copy rule's list.
- **Quantum benchmark (on the Planner):** an n SegmentedControl, the winner sentence for that size, bars for approximation ratio and P(optimum) with a uniform-random reference line, a ChartTable fallback, and a noise DataTable.
  - **Bars:** token fills only. The bars are decorative (`aria-hidden`), because each value is printed as text beside its bar.
  - **Label:** "Benchmark against exact optimum".
- **Methods & data:** a new section, `#quantum`, "Where quantum helps, and where it doesn't". It has two cards (xTB vs Crippen logP; QAOA vs the exact solver), filled entirely from metrics.json and lab_panel.json, and a closing list.
- **`EvidenceStatusBadge`:** a fifth, neutral validation word, `benchmark` ("Benchmark against exact optimum"), drawn with a plain border, ink-muted text and the info icon. It measures methods; it is not a validation.
- **Case study:** "withheld from the Planner" now comes from the panel's excluded-toxic list.

## Token lint

`.eslintrc.json` enforces the v2 tokens over `app/`, `components/`, `features/`, `lib/`, `scripts/` and `tests/`. It bans hex, `rgb()`/`hsl()` and raw pixel values in class names and styles, and Tailwind's default palette names. One exception: `underline-offset-[6px]`, which the handoff's own Atlas screen uses for the passage spans.

## Data and build

- **Data source:** at build time the site reads only `../site-data/`.
- **Validation:** `scripts/prepare-data.ts` validates every file with Zod schemas generated from `contract/schemas/` and exits 1 on any mismatch, which fails the build.
- **Mock data:** none. The design's `mock-data/`, `src/contract/lab.ts` (its "toy model") and its 700 ms mock latency are not used.
- **Honesty treatments:** all are driven by data fields: evidence status, source confidence, disputed names, ranges, heuristic flags, toxicity, unknowns, and extraction versus detection. Hard-coded strings are labels and explanations, never values.
