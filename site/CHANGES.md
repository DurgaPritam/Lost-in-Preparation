# Site changes from the Claude Design handoff

The site is built from the handoff in [`design/`](../design/) (extracted from `lost-in-preparation-handoff.zip`) without redesign.
- The tokens are used unchanged: [`styles/tokens.css`](styles/tokens.css) and [`styles/tokens.json`](styles/tokens.json) are byte-for-byte copies of `design/tokens/`.
- The Tailwind theme is the design's file, with only the `content` globs changed.
- The components in [`components/`](components/) are the design's files, with the import paths rewritten and `'use client'` added where they hold state.

This file lists every change I could not avoid, and every addition. In the code, each change carries a `SITE:` comment.

## Earlier decisions applied (before the site work)

| Decision | Where |
|---|---|
| P37 (contract changes for the corrections, reporting gap, audit v2 and case study) | Implemented as **contract v1.6**: P37a `Recipe.corrections`, P37b `Metrics.reportingGap`, P37c `Metrics.auditV2` and `site-data/audit_v2.json`, P37d `site-data/case_studies.json`. See [contract/CHANGELOG.md](../contract/CHANGELOG.md). P37d was added for the case-study page; approved by the project lead on 2026-11-06. |
| The 1850 rose-water note | `config/m1_corrections.csv`, recipe `culpeper-1850:herbal:liquorice:003#r03`. The part, solvent and filtration corrections are logged. The process was not changed: it stays "distillation", from this edition's wording "distilled in Rose-water" (the 1652 text says "dissolved"). The note says the Dispensatory evidence does not settle this. It is shown on that recipe's page and in the case study. |

## Additions (built from existing tokens and components only)

1. **Home: the reporting-gap section** ([features/home/ReportingGap.tsx](features/home/ReportingGap.tsx)). It sits after the artemisinin panels and shows:
   - for each of heat, fresh/dried, filtration, solvent and part: the share of studies stating it, with *k* of *n* and a 95% CI;
   - the share stating none of them;
   - the v3 screening result.

   Wherever the solvent share appears, the inflated-solvent caveat sits beside it (`InflatedSolventCaveat`). The caveat is driven by the data key (`prepared:*:solvent`), not by position.

   The bar is `features/shared/ShareBar.tsx`, a share with an interval drawn from tokens only, the same way as the design's local MatchBar and IntervalChart. Every number comes from `metrics.reportingGap` in `site-data/metrics.json`.
2. **The liquorice case-study page** ([features/case/LiquoriceCase.tsx](features/case/LiquoriceCase.tsx), `/case-studies/liquorice/`). It shows:
   - the misclassification;
   - the corpus evidence, quoted from the Dispensatory;
   - the 22 logged field corrections across 5 recipes;
   - the before/after ranking table (rank, gap and interval).

   All of it comes from `site-data/case_studies.json`. It is built from Card, DataTable, LikelihoodBar, ToxicityBadge and the AppShell. Its subtitle uses a new optional AppShell prop, `question`.
3. **Audit: v1 and v2 side by side** ([features/audit/Audit.tsx](features/audit/Audit.tsx)). There are two Cards:
   - **v1:** "as pre-registered", with its design-flaw note (its solvent rule makes non-water recipes unmatchable).
   - **v2:** "pre-registered re-analysis after v1's design flaw", with a "Small n" note that gives the known, unknown and no-analogue unit counts. Below it are the per-variable fidelity shares, each with *n* and a CI.

   Tabs switch the per-source breakdowns and the study table between versions. The study table is the design's.

Shareable URLs (also required):
- each recipe: `/recipes/<id>/`;
- each comparison: `/compare/?species=&a=&b=`;
- each hypothesis: `/hypotheses/<id>/`;
- the case study.

These are ordinary URLs in the address bar; I added no copy-link control. Every hypothesis card in the list links to its own page, and the case study links to its comparisons and hypothesis.

## Changes forced by the real data (the design's mock shapes differ from contract v1.6)

The view types are in [lib/types.ts](lib/types.ts). The selectors in `lib/data/selectors/` map contract records onto them.

| Area | Design assumed | Real data, and what the site does |
|---|---|---|
| Sources | Culpeper 1652 and Pliny | There is a third source, Culpeper 1850. It has its own label and confidence marker and is never merged with the other two. |
| Vehicle | One fixed enum | The contract has separate historical and modern solvent enums, with mixtures such as "wine + honey". A label for each is in `format.ts` (`vehicleLabel`). Solvent, heat and filtration stay separate fields (non-negotiable 4). |
| Filtration | Boolean or unknown | Adds `not_applicable` (ointments, amulets and similar), printed as such. |
| Extracted fields | Included quantity | M1 never extracts quantity, so the site does not list it as "not stated". It adds fresh/dried, process, form and indication. |
| Field highlighting | Every quote drawn inline | Quotes that overlap, or come from the entry heading, are listed in the field table but not drawn in the passage (a span cannot overlap another). |
| Name confidence | An interval for each candidate | M2 gives a heuristic score with no interval. DisputedName shows "Interval unknown" and puts the score in the tooltip; it is never drawn as a range. |
| Profiles | Tied to a recipe or study | M4 profiles are model presets per species (origin `model`). The driver text adds the model multiplier. |
| Match states | Matches, differs, not stated | Adds `no_analogue` (audit v2 only). It is a fourth bar segment and is never counted as "differs". |
| Study rows | Duration and ratio | Not in the contract, so the site has no such columns. It adds fresh/dried, and the evidence source (methods or abstract). |
| Hypotheses | Compound-level likelihood pairs | The contract hypothesis is a species-level profile gap (1 − cosine similarity) with an interval. The card's LikelihoodBar shows the gap. A lead is marked weak when the gap's 5th percentile is below the ranking rule's threshold; both values come from the data. |
| Methods outcomes | Pass, borderline or fail | Adds `reported`: a result exists in site-data but is not graded there. It is printed as "Outcome not graded". |
| Positive control | Structured ranges | The artemisinin check has no structured ranges, so no ranges are drawn. |
| Hypotheses question (IA) | — | Reworded to "Which plant–use pairs are worth re-testing in their historical preparation, and why?" to match the data. |
| Toxicity | Three values | Deprecated contract values map forward (`known_toxic` to `toxic_reported`). A `toxic_reported` plant never gets a Compare link anywhere (recipe, hypothesis trail, case study), and is never the default Compare species. |

## Changes for scale, performance and accessibility

- **Lists:** 631 recipes and 387 audit rows are shown in pages ("Show more"; 40 recipes and 50 studies at a time). The plant facet shows its 12 most frequent values, with "Show all".
- **Recipe explorer:** the facet logic moved from the component to [lib/data/selectors/recipeFacets.ts](lib/data/selectors/recipeFacets.ts), where it is unit-tested. The first 40 recipes and the unfiltered counts are rendered statically. The full list (`/data/recipe-index.json`) loads after the first screen. If someone searches or filters before it arrives, they see the design's LoadingState, never partial counts.
- **Audit:** the study rows load when the table is shown (`/data/audit-studies-v1.json` and `-v2.json`), and only the selected tab panel is rendered. Together these took the page from 2.1 MB and 16,000 DOM nodes to 48 KB.
- **Compare:** each species' profile loads on demand from `/data/compare/<speciesId>.json`. This is a compact form of `site-data/profiles/`, expanded and validated in `selectors/compare.ts`. The loading state holds a screen's height, which avoids a layout shift. Each compound class shows 12 rows, with "Show all".
- **Links:** `components/base/Link.tsx` is next/link with prefetch off (new). Prefetching pulled about 1 MB of other pages' payloads on every page load.
- **Wrapping:** long IUPAC compound names wrap (`break-words`, `min-w-0`) so that a 390px page never scrolls sideways.
- **Scroll regions:** the wide correction tables on recipe pages and the case study are focusable regions with labels (axe `scrollable-region-focusable`).
- **Target size:** PubMed links in the audit table get vertical padding.
- **Heading order:** the standalone hypothesis page adds a visually hidden h2 ("Hypothesis"), because the card's title is the design Card's h3.
- **Font fallbacks:** `styles/font-fallbacks.css` adds metric-matched fallback faces: local Times New Roman/Liberation Serif, Arial/Liberation Sans and Courier New/Liberation Mono. Their `size-adjust` and ascent/descent overrides were computed with fontTools from the vendored woff2 files.
  - **Why:** on Linux the fallback fonts reflowed whole pages when EB Garamond and IBM Plex swapped in (CLS 0.16–0.24 in CI Lighthouse).
  - **Token stacks:** each stack gains the fallback family right after the web font; the rest of the design's stack is unchanged. `tokens.css` itself is untouched; the override is in the new file, which is imported after it.
- **Favicon:** `app/icon.svg` is the design's `mark-historical.svg`, with the embedded metadata stripped.

## Data and build

- **Source of data:** at build time the site reads only `../site-data/`.
- **Generated types:**
  - [scripts/gen-contract.mjs](scripts/gen-contract.mjs) generates the TypeScript types and Zod schemas from `contract/schemas/*.schema.json`, writing them to `lib/data/generated/`.
  - Objects are closed: unknown fields are rejected, and every property is required, as the exported data always carries every key.
- **Validation:**
  - [scripts/prepare-data.ts](scripts/prepare-data.ts) validates every site-data file with Zod, and exits 1 on any mismatch, which fails the build.
  - It then writes `public/data/`: the downloads and the on-demand files listed above.
- **Mock data:** there is no mock data in the site; the design's `mock.ts` is not used.
- **Honesty treatments:** all of them are driven by data fields: evidence status, source confidence (disputed share ≥ 0.5 means lower confidence), disputed names, ranges, heuristic flags, toxicity, unknowns, and extraction versus detection.
- **Hard-coded text:** the only hard-coded strings are labels and explanations, never values.
- **Tests:** the local static server `scripts/serve.mjs` compresses responses with brotli or gzip, as Vercel does, so Lighthouse measures the deployed transfer sizes.
