# Data contract changelog

Changes after v1.0 are additive unless a major version says otherwise. New proposals are added at the top as **Proposed** and are implemented only once accepted.

## v1.8 — 2026-11-07 (additive; P39 **proposed**, implemented for the v2 site's plates and awaiting the project lead's approval)

| # | Change |
|---|---|
| P39 | **Botanical plates** (`site-data/plates.json`, `PlateRecord[]`, one per Lab species), for the v2 design's `PlateSlot`. Fields: `speciesId`, `taxon`, `caption`, `status` (`to_source` \| `sourced` \| `confirmed`), the Commons `licence` (LicenseShortName) and `licenceDetail` (UsageTerms), `host`, `fileUrl` (file page), `sourceUrl` (the image downloaded once), `author`, `date`, `work`, `matchedName`, `sha256`, `retrievedAt`, and `image` (`PlateImage`: AVIF and WebP `srcset`, fallback `src`, `width`, `height`). |
| | Written by `python -m lip plates`, which accepts only files whose Commons licence field is public domain. A species without a suitable file has status `to_source`, a caption saying so, and every source and image field `null`, so the site shows the design's empty slot. `sourced` means the licence was read by script; only a person's check makes it `confirmed`. The same records are written to `docs/IMAGE_CREDITS.md`. Nothing existing changes. |

## v1.7 — 2026-11-06 (additive; P38 **approved by the project lead on 2026-11-07**)

| # | Change |
|---|---|
| P38 | **Preparation Lab engine inputs** (`site-data/engine/`), so the browser can recompute the preparation model (M4) for any combination of solvent, heat, filtration and acidity, with the pipeline's exact Monte Carlo draws. Three files, all additive; nothing existing changes. |
| | `engine/model.json` (`EngineModel`): the parameters and uncertainty ranges of `config/prep_model.toml` (`EngineParams`), the model version (config hash), the descriptor-error SDs (`EngineDescriptorError`), the 13 pipeline preparations with their `seedOffset` (grid index), the noise-stream offset (10,000,019), the random-number scheme (`rng`) and the seed rule for an off-grid combination (`customSeedRule`: 1000 + FNV-1a of `<solvents>\|<heat>\|<filtered>\|<process>` mod 10^6). |
| | `engine/<speciesId>.json` (`EngineSpecies`): per compound, in the same order as `profiles/<speciesId>.json`: InChIKey, name, class (heuristic), descriptor used, lipophilicity, and the heuristic flags (basic nitrogen, heat alerts, volatile) and MW. These are the model's inputs; nothing new is computed. |
| | `engine/parity.json` (`EngineParityCase`): Python estimates for 9 preparations outside the grid, for the 3 species that together cover every model branch (basic nitrogen, MW > 1000, volatiles, each heat alert). A build-time test fixture for the TypeScript port; not published to the browser. |
| | Written by `python -m lip m4 engine-export`. It refuses to write unless the exported inputs reproduce all 34,645 published profile estimates exactly through `pipeline/lip/m4/model.py`. |

## v1.6 — 2026-11-06 (additive)

| # | Change |
|---|---|
| P37a | `Recipe.corrections`: a list of `{field, from, to, reason, evidence, requestedBy, appliedBy, date}` for logged field corrections (`config/m1_corrections.csv`). The recipe's own fields stay as extracted. Approved by the project lead. |
| P37b | `metrics.reportingGap`: `dict[str, Metric]` of descriptive reporting-gap shares (Wilson 95% CI), keyed `<set>:<coded from>:<variable>` and `v3:screening`. Approved. |
| P37c | `metrics.auditV2` (`AuditV2Section`) with the audit v2 fidelity rates, and `site-data/audit_v2.json` with the same shape as `audit.json`. `MatchCode` gains `no_analogue` (v2 only: the historical vehicle has no modern analogue; never scored as unfaithful). In `audit_v2.json`, `matchRate` counts faithful among faithful + not-faithful studies; no-analogue studies are in neither count. Approved. |
| P37d | `site-data/case_studies.json` (`CaseStudy`): a documented extraction correction, its corpus evidence and the Phase 6 rank and gap before and after. Added for the liquorice case-study page that the project lead requested; additive. **Approved by the project lead on 2026-11-06.** |
| — | `metrics.nameResolution` gains keys `disputedShare:culpeper` and `disputedShare:pliny` (no schema change: the field is a dict), so the site's source-confidence markers are driven by data. |

## v1.5.1 — 2026-11-06 (documentation only)

| # | Change |
|---|---|
| P36 | `provenance.provider` may be `groq`. For a hosted model, `modelVersion` is `<model id>@created=<unix time from GET /models>`, and `decoding.selectedOn` is the date the model was chosen. The schema is unchanged: `provider` was already a free string. |

## v1.5 — 2026-11-05

| # | Change |
|---|---|
| P35 | Hypothesis ranking relies only on profile gaps that hold across the uncertainty range. `profileGap` is now `{value: median, low: 5th, high: 95th percentile}` of the gap over coupled Monte Carlo draws, with descriptor error included. New optional `gapRanking {rule, gapP5, gapThreshold, pGapAboveThreshold, compoundsUsed, compoundsExcludedWide, rankByMedianGap}`. `rank` orders hypotheses by `gapP5`, then `pGapAboveThreshold`. Compounds whose 5th–95th range is wider than the rule's limit are excluded, because they cannot drive a ranking. Requested by the project lead. Additive: no hypotheses file has been published yet. |

## v1.4 — 2026-11-05

| # | Change |
|---|---|
| P34 | `toxicityFlag` values now describe what one cited source says: `toxic_reported`, `concern_reported`, `no_toxicity_reported`, `data_lacking`, `unknown`. `known_toxic` and `none_known` are deprecated and kept only for compatibility. The pipeline no longer emits them, and never emits `none_known`, because absence of a report is not evidence of safety. `ProfileIndexEntry` gains optional `toxicityEvidence {source, url, quote, licence, basis, verifiedBy}`. Entries are AI-drafted from EMA herbal documents or CC-licensed PMC articles (`basis = ai_drafted_unverified`, `verifiedBy` empty until a person reviews them). Requested by the project lead, to replace the Wikipedia-list screen in the study-set column. |

## v1.3 — 2026-11-05

| # | Change |
|---|---|
| P33 | Profiles are split: `site-data/profiles/index.json` (`ProfileIndexEntry {speciesId, acceptedName, file, preparations, compounds, toxicityFlag, toxicityNote}`) plus one `site-data/profiles/<speciesId>.json` per species (an array of `Profile`, unchanged shape). The site loads the index first and species files on demand. The full combined file is in the data release (`data/release/profiles_full.json.gz`). `site-data/profiles.json` is retired. |

## v1.2 — 2026-11-05

| # | Change |
|---|---|
| P31 | `metrics.provisional`: a map of `ProvisionalSection {basis, label, extraction, metrics}`. It holds results measured against AI-made references (`silver_ai_reference`, `ai_drafted_unverified`, `ai_curated_literature_reference`). These are **never** written to the gold fields (`extraction`, `interAnnotatorAgreement`, `nameResolution`). |
| P32 | `profiles.process` (optional) and `preparationLabel`. Distillation and other processes cannot be expressed by `preparationKey` alone. |

## v1.1 — 2026-11-05

| # | Change |
|---|---|
| P30 | `recipes.provenance` gains `provider` (`ollama` / `anthropic`), `modelVersion` (e.g. the Ollama model digest) and `decoding` (temperature, seed, context length, quantisation, effort). `metrics.extraction.run` records the provider, model, version, decoding and prompt version of the extraction run that the metrics describe. |

## v1.0 — 2026-11-05 (frozen)

The first frozen contract: seven files with generated JSON Schemas. It accepts P1–P29.

**Recipes**
- `solvent` is a list (P8) and includes `none` (P9).
- New `process` field (P10).
- Enums for `part`, `freshOrDried` and `form` (P11).
- `filtered` gains `not_applicable` (P12). New `heatText` field (P13).
- `passage.translation` (P19) and extraction provenance (P21).
- `recipeType`, `ingredients[]` and `excludedFromHeadline` (P27): compound recipes are stored but kept out of the headline analysis.
- Verbatim `evidence` quotes with offsets, plus `inHeading` (P28).
- `attributionCaveat` (P26).

**Sources**
- `workId` and `files[]` (P25).
- `originalYear` / `editionYear` (P24).
- `licenceVerified`, `licenceNote` and `translator` (P20).
- `editorialNote` (P26).

**Species**
- `id`, plus `speciesId = wfoId` (P3).
- `basis` adds `commentary_19c`, with `basisRef` (P29); these are candidates only.
- `toxicityFlag` (P18).

**Profiles**
- `preparationKey = part|freshOrDried|solvent|heat|filtered` (P4).
- Per-factor `drivers` and `heuristic` flags (P6).
- `compoundId` = InChIKey, plus `smiles` and source references (P14).

**Audit**
- `filtered` on studies (P1).
- `modernSolvent` enum (P2).
- A per-variable `match` object (P5).
- `evidenceSource` and `methodsSnippet` (P15).
- `matchRate {value, nKnown, nUnknown}` (P16).
- MeSH indications (P17).

**Hypotheses**
- `profileGap {value, low, high}` (P22).
- `toxicityFlag` (P18).

**Metrics**
- Every metric is `{status, value, low, high, n, sourceFile, note}` (P7). `not_computed` replaces placeholders.

**Conventions**
- `unknown` everywhere (P23).
- `mock: bool` on every record.

## v0.1 — 2026-11-05

The initial draft: seven files, three shared enums (`solvent`, `heat`, `filtered`).
