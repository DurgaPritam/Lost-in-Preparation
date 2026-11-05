# Data contract changelog

Changes after v1.0 are additive unless a major version says otherwise. New proposals are added at the top as **Proposed** and are implemented only once accepted.

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
