# Methods

This document describes how every dataset in this repository is produced. All counts quoted here come from files the pipeline writes; each section names its file.

## 1. Sources and ingestion

| Source | Copy | Profile |
|---|---|---|
| Culpeper, *The English Physitian* (London: Peter Cole, 1652) | EEBO-TCP A35365, TEI P5, CC0 | `tei` — **primary herbal source** |
| Culpeper, *The Complete Herbal* (London: Thomas Kelly, 1850) | Project Gutenberg #49513 | `culpeper` — dispensatory, directions; herbal kept for comparison |
| Pliny, *Natural History*, tr. Bostock & Riley (Bohn, 1856), vols 4–5 | Project Gutenberg #61113, #60688 | `pliny` — books XX–XXVII are in scope |

Licences and evidence: [docs/DATA_LICENCES.md](docs/DATA_LICENCES.md). Raw files are downloaded by `lip fetch`, which records the URL, SHA-256 and retrieval time in `data/raw/manifest.json`. Ingest refuses to run if a checksum differs.

**Passages.** Each source is split into passages with stable IDs and locations: book, chapter and paragraph for Pliny; entry and subsection for Culpeper. The output is `data/interim/passages.parquet`, and the counts are in `data/interim/ingest_report.json`.

- **Gutenberg texts.** Blocks are runs of non-blank lines. Every non-blank line belongs to exactly one passage, and the tests check this. Cleaning is limited to three steps: line unwrapping, removal of italic markers, and removal of footnote anchors (the anchors are kept as links). Spelling, hyphenation and punctuation are never changed, and the original text is stored next to the cleaned text. Pliny's footnotes are Bostock & Riley's 19th-century commentary. They are stored as separate passages linked to the paragraphs that cite them, and are never treated as Pliny's text.
- **TEI text (1652).** Passages are TEI block elements. The renderer applies four rules:
  1. Line-end word breaks (`<g ref="char:EOLhyphen"/>`) are joined.
  2. **Illegible letters stay visible** as `⟦?⟧`, with one `?` per missing letter (`⟦foreign⟧` for omitted foreign text). These markers are never removed downstream.
  3. Printed marginal notes are moved out of the running text into their own passages, linked to their paragraph.
  4. Page breaks set the page number.

  Part headings are normalised: "Vertues and Vse", "The Vertues" and "♄ Discription" become `vertues and use` and `description`. A test checks that every text node in the TEI body lands in exactly one passage.

## 2. 1850 ↔ 1652 crosswalk (heuristic)

The 1850 edition claims to add "upwards of one hundred additional herbs". Each 1850 herbal heading is matched to a 1652 heading to find them:

- **Normalisation:** early-modern spelling is mapped (vv→w, v→u, j→i, y→i, ph→f), doubled letters and word-final *e* are removed, and every alternative name in a heading is compared.
- **Assignment:** one-to-one, greedy by score.
- **Status:**
  - `in_1652` for a score of 0.90 or more;
  - `probable_1652` for 0.75–0.90;
  - otherwise `later_addition_candidate`.

The flag applies to **1850 herbal entries only**. The 1850 dispensatory and directions come from other works and have no 1652 counterpart by construction. Every pairing, with its score and nearest alternative, is in `data/interim/culpeper_1850_1652_crosswalk.csv` for review. Reviewer decisions go in `config/crosswalk_overrides.csv` and always override the heuristic.

Limitation: an 1850 herb that appears in 1652 under a completely different name is flagged as a candidate, not confirmed.

## 3. Recipe extraction (M1)

**Prompt.** One versioned prompt ([prompts/m1_extract/v1/](prompts/m1_extract/v1/)) holds the system text, the [annotation guidelines](prompts/m1_extract/v1/guidelines.md) and four Culpeper worked examples. The output is constrained to a strict JSON schema ([response.schema.json](prompts/m1_extract/v1/response.schema.json)). Human annotators and the model follow the same guidelines.

**Verbatim-quote rule.** Every recipe span, free-text value and non-`unknown` enum value must be supported by a verbatim quote from the passage. Plant names may instead come from the entry heading, and are then flagged `inHeading`. Matching ignores only typography: curly vs straight quotes, dash variants and whitespace. If a quote fails, the model sees the errors and retries, up to 2 times. A recipe that still fails is **rejected and logged**; it is never repaired by code.

**Providers.** The provider is set in [config/pipeline.toml](config/pipeline.toml), and both get identical prompts, schema and checks.

| Provider | Model | Decoding |
|---|---|---|
| `ollama` (default, local) | `qwen2.5:7b-instruct` (Q4_K_M, 4.7 GB), suited to a 16 GB RAM laptop. Alternatives are listed in the config. | temperature 0, seed 0, context 16,384 tokens |
| `anthropic` (optional) | `claude-opus-5-5` | effort `high`, server-side refusal fallback |

**Provenance and caching.** The provider, model, the exact model digest read from Ollama, the decoding settings and the prompt version are recorded on every extracted recipe and in `metrics.json`. Responses are cached on disk under a key that covers all of these, so re-runs are reproducible.

**Scope.** Only single-plant recipes enter the core analysis and the headline numbers. Compound recipes are stored with `excludedFromHeadline: true`.

## 4. Gold-set sample (v2)

The file is `data/gold/sample_v2.json` (seed `20261106`). It holds 50 passages drawn without replacement, stratified by source:

| Stratum | n | Frame |
|---|---|---|
| `culpeper1652_virtues` | 20 | 1652 herbal, body paragraphs in "Vertues and use" sections |
| `culpeper1850_dispensatory` | 10 | 1850 Family Dispensatory, body paragraphs |
| `pliny` | 20 | Pliny books XX–XXVII, body paragraphs |

Frame rules:
- Recipe-scope body passages only.
- The four few-shot passages are excluded, since they are in the prompt.
- Passages that contain any illegible-gap marker are excluded. Recipe spans aren't known before annotation, so excluding every passage with a gap is a conservative superset of "a gap inside recipe text".

Frame sizes and the number of passages excluded for gaps are recorded in the sample file (`frameSize`, `excludedForGap`).

## 5. Annotation and evaluation

**Annotation.** [annotation/index.html](annotation/index.html) is a static tool that needs no server and never shows model output. Two annotators work independently and save `data/gold/annotations/<name>.json`. An adjudicator then compares the two files in **Adjudicate** mode and saves `gold.json`.

**Evaluation** (`lip m1 eval` writes `site-data/metrics.json`):
- **Alignment:** recipes in a passage are paired by the character overlap (IoU) of their recipe spans, with ties broken by the number of agreeing fields.
- **Per-field P/R/F1:**
  - TP: both values known and equal.
  - FP + FN: both known but different.
  - FP: predicted known, gold unknown. FN: predicted unknown, gold known.
  - `solvent` and `ingredients` are scored as sets; free-text fields match at token-F1 ≥ 0.5.
- **Recipe detection P/R/F1:** paired vs unpaired recipes.
- **Intervals:** 95% bootstrap CIs over passages (B = 2000), stratified for the overall figures, reported per stratum and overall.
- **Agreement:** Cohen's kappa between annotators per categorical field, with `unknown` as a category. If both annotators use a single category, kappa is reported as not computed.
- **Missing inputs:** a metric whose inputs don't exist is written as `not_computed` with the reason. No placeholder numbers are written.

**Error analysis:** `lip m1 errors` writes [docs/extraction_errors.md](docs/extraction_errors.md).

## 6. Name resolution (M2)

**Name inventory** (`data/interim/m2/name_inventory.parquet`). M1 recipes don't exist yet, so names are taken from entry headings:
- **Culpeper 1652:** one name per herb. The queries are the alternatives in the heading, plus the crosswalked 1850 heading, which gives a modern spelling.
- **Pliny books XX–XXVII:** one name per plant in a chapter title. Count words ("TWENTY-SIX REMEDIES") and non-plant titles are dropped. Each name is linked to the Bostock & Riley footnotes anchored right after a word of the name ("strong"). In single-name chapters only, it can also be linked to footnotes on the heading and first paragraph ("weak").

**Candidates** (`data/interim/m2/name_candidates.parquet`, up to 3 per name). This is a heuristic with every weight stated in `pipeline/lip/m2/resolve.py`.

| Evidence | Basis | Weight |
|---|---|---|
| The name as written is a scientific binomial (GBIF backbone, strict) | `database` | 2.0 |
| The GBIF backbone species has an **exact** English vernacular match (plurals and possessives folded) | `database` | 1.0 per query, split by *support* (independent vernacular records). Multiplied by a regional prior from GBIF occurrences in Great Britain (Culpeper) or Europe (Pliny), and by 0.3 for Pliny names. |
| A binomial named in a linked Bostock & Riley footnote | `commentary_19c` | strong 2.0 / weak 1.0, divided by its order in the footnote; ×0.5 if the footnote hedges ("probably", "supposed", "some…", "doubt") |

- **Confidence:** scores are normalised per name, and each species is mapped to its **accepted WFO name and WFO ID**, following synonymy.
- **Disputed:** a name is flagged when any of these holds:
  - top confidence < 0.6;
  - the deciding footnote hedges;
  - the top two candidates are within 0.15;
  - the total evidence is < 0.5.
- **Not used:** POWO refused automated access, so it isn't used. No LLM (`model` basis) and no scholarly lists are used as candidates; scholarly identifications are reserved for evaluation.

**Evaluation.** `data/gold/name_identifications.csv` holds 30 names (15 Culpeper, 15 Pliny, seed `20261107`). A person fills in the scholarly accepted name and a citation for each row; rows without a citation are not scored. `lip m2 eval` reports top-1 and top-3 accuracy with Wilson 95% intervals, plus the share of names flagged disputed (written to `metrics.json`).

## 7. Compounds (M3)

**Source.** Compounds come from LOTUS natural-product occurrences on **Wikidata** (CC0): compounds with *found in taxon* (P703) for the accepted WFO name or the GBIF name it came from. Each occurrence keeps its LOTUS reference (*stated in*, P248). LOTUS is organism-level, so **plant part is `unknown`**. COCONUT's curated dump is CC0, but it is not integrated yet (see the licence register).

**Standardisation.** Structures are processed with RDKit in four steps: parse the isomeric SMILES (falling back to canonical), Cleanup, take the largest organic fragment, then neutralise. No tautomer canonicalisation is applied. Compounds are de-duplicated by the InChIKey of the standardised structure. A mismatch with the InChIKey stored in Wikidata is flagged.

**Outputs** (`data/interim/m3/`):
- `compounds.parquet` and `occurrences.parquet`;
- `coverage.csv`: compounds and references per species, with species below `poor_coverage_below` (default 10, a heuristic) flagged;
- `compounds_summary.json`.

## 8. Study-set proposal

`lip m3 studyset` writes [docs/STUDY_SET_PROPOSAL.md](docs/STUDY_SET_PROPOSAL.md) and a CSV with an `approved` column for human decisions.

- **Eligibility:** all of the following:
  - resolution not disputed, with confidence ≥ 0.6;
  - an attestation proxy of ≥ 3;
  - coverage that is not poor.
- **Attestation proxy:** recipe-scope passages per resolved name. A Pliny chapter's paragraphs are split across the plants it names.
- **Ranking:** by number of sources, then attestations, then compounds.
- **Not yet done:** toxicity has not been assessed.

## 9. Preparation model (M4)

For each compound and preparation the model estimates the **likelihood that the compound reaches the preparation**. It combines four separate, inspectable factors, and propagates uncertainty by Monte Carlo over every assumption in [config/prep_model.toml](config/prep_model.toml): 400 draws, fixed seed. Each estimate reports the median, the 5th–95th percentile range and the median of each factor (`drivers`: solvent, heat, filtration, acidity). These are model estimates, not chemical measurements.

**Solvent.** The descriptor is a compound's lipophilicity *h* (logP). Each vehicle has a logistic window:
- **Aqueous vehicles** (water, vinegar, honey, other aqueous liquids) have an upper bound.
- **Nonpolar vehicles** (oil, hexane) have a lower bound.
- **Alcohols** (methanol, ethanol, 70% ethanol) have both.

The window edges and the steepness are sampled from stated ranges. **Wine** is treated as a water–ethanol mixture: its upper edge shifts by ethanol fraction (10–14%) × a per-unit shift. That's an assumption. A mixed vehicle takes its best-extracting component. Juice is treated as aqueous cell sap. A powder taken whole carries everything. Very large molecules (MW > 1000) get a size penalty, which is a heuristic.

**Descriptor choice.** The descriptor is validated before use. RDKit Crippen logP and GFN2-xTB are compared against experimental logP for 150 neutral compounds from SangsterLogP, chosen with a fixed seed and stratified by quintile.
- **xTB protocol:** a single ETKDG conformer (seed fixed), gas-phase optimisation, then ALPB single points in water, hexadecane, ethanol and wet octanol. Results are cached by InChIKey. The installed xtb 6.7.1 supports these ALPB solvents (checked); its GBSA model lacks hexadecane, octanol and ethanol.
- **Choice:** the method with the lower MAE becomes the default.
- **Caveat:** Crippen was fitted to public logP data, which may overlap the reference set.

**Acidity** (heuristic). A SMARTS rule finds basic nitrogen. In vinegar such compounds get a logD shift of 1–3 log units, which raises aqueous extraction. The `acidity` driver reports the effect.

**Heat** (heuristic). SMARTS alerts flag heat-sensitive groups: endoperoxides and peroxides, labile esters, glucosinolates and cyanogenic glycosides. A volatility rule (MW < 250, HBD ≤ 1, TPSA < 40) marks steam-volatile compounds. Each alert has a degradation or loss range for warm and for boiled preparations; cold preparations lose nothing.
- **Distillation:** carries volatile compounds only.
- **Exploratory:** xTB Wiberg bond orders are recorded for flagged O–O bonds.

**Filtration.** An unfiltered preparation carries a fraction (5–30%) of the undissolved material as suspension. Poultices and ointments (material applied whole) carry 30–80%. When filtration is unknown, each draw is filtered or not with equal probability.

**Known-case test.** Artemisinin must:
- trigger the heat flag;
- predict a median below 0.30 for cold water;
- predict a median above 0.60 for low-temperature nonpolar extraction.

The thresholds were set in the config before running.

**Literature check.** This one is *provisional* (§10). There are 9 rows across 5 plants, reporting what teas, essential oils and alcoholic extracts contain. Thresholds were pre-registered: "present" requires a median ≥ 0.40 and "low" requires < 0.30.

**Outputs:** `site-data/profiles.json` (30 study-set species × 13 preparations, contract v1.2) and `data/interim/m4/profiles_long.parquet`.

## 10. Provisional references (AI-made; never presented as validation)

Until the human gold sets exist, three references made by an AI (Claude Code) let the pipeline be developed and checked. Each is stored separately, marked with a `basis`, and written only to `metrics.provisional`. None ever enters a gold field.

| Reference | basis | What it is | Limits |
|---|---|---|---|
| `data/silver/silver_v1.json` | `silver_ai_reference` | Recipe labels for the 50 sample passages, written by the AI directly from the guidelines (`data/silver/silver_v1_spec.py`). Every quote is checked verbatim by `lip m1 silver`. | Same author as the guidelines and few-shot examples, so agreement may be inflated by shared conventions. |
| `data/gold/name_identifications.csv`, `draft*` columns | `ai_drafted_unverified` | Candidate identifications drafted only from sources fetched in the run: Lewis & Short (PerseusDL TEI) and English Wikipedia. Each has a quoted line, checked against the fetched text on every run. Bostock & Riley are excluded. `verified_by` is empty. | Not scholarly verification; L&S and Wikipedia may share older sources with the system's inputs. |
| `data/reference/prep_literature_v1.csv` | `ai_curated_literature_reference` | 9 statements from 5 open-access PMC articles, each quote checked against the fetched article. | The rows were chosen by the same AI that built the model, after the model existed; n is small. |

The annotation tool's independent mode never shows any of these. **Review** mode, for adjudication only, shows human labels beside the silver labels.
