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

**Prompt versions.** Prompts are versioned folders under `prompts/m1_extract/`, and the version in use is set in `config/pipeline.toml`. Changes are recorded in [prompts/m1_extract/CHANGELOG.md](prompts/m1_extract/CHANGELOG.md).

**v3** (2026-11-06, in use) is v2 plus three rules on evidence and quotes: evidence entries only for the 8 categorical fields; exact, continuous quotes with no ellipses; and a supporting quote for every categorical value other than "unknown". These address v2's frequent schema rejections. System prompt 2,602 tokens; fixed part 3,490 with the schema.

**v2** (2026-11-06) fits Groq's free tier, which counts the input, the JSON schema and the full completion allowance against 8,000 tokens per minute.
- **Size:** the fixed prompt is cut from 6,071 to 3,382 tokens (system prompt 5,183 → 2,494, plus the 888-token schema; `data/interim/m1/prompt_token_counts.json`). It keeps two of v1's four worked examples.
- **Unchanged:** the schema, the field definitions, the verbatim-quote rule and temperature 0.
- **Compact retries:** a retry sends only the passage, the validation errors and the failed recipes, never the full previous answer.
- **Annotation:** human annotators keep the full v1 guidelines.
- **Pacing:** each request's completion allowance is capped so the request fits the per-minute limit. A request or retry that will not fit the tokens left in the current minute waits for the next window instead of being sent.
- **Re-extraction:** every sample passage is re-extracted with the version in use (v3). Responses from v1 and v2 stay in the cache under their own prompt versions and are excluded from evaluation.

**Verbatim-quote rule.** Every recipe span, free-text value and non-`unknown` enum value must be supported by a verbatim quote from the passage. Plant names may instead come from the entry heading, and are then flagged `inHeading`. Matching ignores only typography: curly vs straight quotes, dash variants and whitespace. If a quote fails, the model sees the errors and retries, up to 2 times (v2: only the failed recipes are sent back). A recipe that still fails is **rejected and logged**; it is never repaired by code.

**Providers.** The provider is set in [config/pipeline.toml](config/pipeline.toml). All providers get identical prompts, schema and checks.

| Provider | Model | Decoding |
|---|---|---|
| `groq` (default, hosted) | An open-weight instruction model served by Groq, chosen at the first keyed run from the live `GET /models` list: the first configured candidate that supports strict JSON-schema output (`openai/gpt-oss-120b`, then `openai/gpt-oss-20b`, then `qwen/qwen3.8-27b`). The choice, the list snapshot and the date are in `data/interim/m1/groq_model_selection.json`. | temperature 0, seed 0, strict JSON-schema structured outputs, low reasoning effort (gpt-oss), at most 4,096 completion tokens |
| `ollama` (optional, local) | `qwen2.5:7b-instruct` (Q4_K_M, 4.7 GB). Not the default: on the 16 GB development machine it froze the system, so it was uninstalled. | temperature 0, seed 0, context 16,384 tokens |
| `anthropic` (optional) | `claude-opus-5-5` | effort `high`, server-side refusal fallback |

**Groq access.** The API key is read only from `GROQ_API_KEY` (the environment or a git-ignored `.env`). It is sent only in the request header and never written to code, config, logs, error messages, caches or outputs; a test scans tracked files for key-like strings. Free-tier limits are respected:
- a minimum gap between requests;
- pacing from Groq's `x-ratelimit-*` headers;
- exponential backoff on HTTP 429, honouring `retry-after`;
- a clean stop when a wait would exceed five minutes, such as a daily limit, so a later run resumes from the cache.

**Provenance and caching.** Every extracted recipe and `metrics.json` record:
- the provider and the exact model ID;
- the model version: for Ollama the digest, for Groq `<id>@created=<unix time>` from the model list;
- the selection date, the decoding settings and the prompt version.

Every response is cached under a key covering all of these. For Groq there are two cache levels:
- each raw API response, keyed by a hash of the request body, in `data/interim/m1/groq_responses/`;
- each finished passage result, in `data/interim/m1/raw/`.

So no request is ever sent twice. **Both caches are committed to the repository**, because hosted models can change, be updated in place or be retired, and a hosted run cannot otherwise be repeated. With no key set, the pipeline serves only cached responses, so the published results reproduce exactly without one.

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
| The GBIF backbone species has an **exact** English vernacular match (plurals and possessives folded) | `database` | 1.0 per query, split by *support* (independent vernacular records). Multiplied by a regional prior from GBIF occurrences in Great Britain (Culpeper) or Europe (Pliny), milder in v2 (0.5 + 0.5 × relative log-occurrences) so cultivated and traded plants stay plausible, and by 0.3 for Pliny names. |
| A binomial named in a linked Bostock & Riley footnote | `commentary_19c` | strong 2.0 / weak 1.0, divided by its order in the footnote; ×0.5 if the footnote hedges ("probably", "supposed", "queries whether", "inclined to", "impossible to speak positively"…) |
| **Classical genus** (v2): a word of the name, or a Latinised/transliterated variant (-on→-um, -os→-us, -e→-a, doubled consonants collapsed, Latin endings added), is an accepted plant genus (GBIF, synonyms followed) | `database` | candidates in that genus ×3 (keeps the ranking within the genus); if none, the genus's most-recorded species in the region is added (2.0, genus-level, disputed). Pliny: every word; Culpeper: Latin-looking words only, never English words |
| **Binomial from name tokens** (v2): genus + another Latin-looking word of the name matches a species ("Dodder … Epithimum" → *Cuscuta epithymum*) | `database` | 3.0 |

- **Confidence:** scores are normalised per name, and each species is mapped to its **accepted WFO name and WFO ID**, following synonymy.
- **Disputed:** a name is flagged when any of these holds:
  - top confidence < 0.6;
  - the deciding footnote hedges;
  - the top two candidates are within 0.15;
  - the total evidence is < 0.5;
  - the name resolves only to genus level;
  - **footnote rule (v3)**: a Bostock & Riley footnote binomial is **not used as the identification** in three cases:
    - its own sentence hedges it ("probably", "takes this to be", "thinks", "considers", "is right", "conjecture"…);
    - its own sentence contradicts it ("a totally different plant", "confounded", "mistake"…);
    - the footnote sets two or more named authorities against each other (e.g. Fée vs Sprengel).

    Such a binomial stays a low-confidence candidate (weight ×0.2). The name is disputed, and the trigger phrase is logged in `footnoteTriggers`. The effect on approved species is in `data/interim/m2/footnote_rule_changes.json`, measured against a snapshot taken just before the rule. Approved species whose counted entries changed are pending the project lead's re-review and stay out of the headline set until then.
  - **genus-signal false friend**: the classical-genus audit ([docs/GENUS_SIGNAL_AUDIT.md](docs/GENUS_SIGNAL_AUDIT.md), `pipeline/lip/m2/genus_audit.py`) lists the name. The audit screens every top-1 resolution that used the classical-genus signal, and checks each word against its Lewis & Short entry. It records three kinds of case:
    - a classical word with a different meaning (Pliny's *laser* is the juice of silphium, not the genus *Laser*);
    - an English word that spell-matches a genus (Culpeper's 'Cotton Thistle' → *Cotinus*);
    - chapter titles that are not plant names.

    Findings are AI-reviewed (`ai_drafted_unverified`), each with the dictionary sentence, and they mark the resolution disputed without deleting it.
  - **toxic confusion**: candidates with confidence ≥ 0.15 differ in known toxicity. For this screen only, toxicity is checked against Wikipedia's *List of poisonous plants* (CC BY-SA 4.0, revision recorded). The study-set column uses the curated entries in §8 instead. Absence from the list is recorded as `unknown`, never as safe. The list is incomplete: it omits, for example, *Papaver somniferum* and *Symphytum officinale*. It also lists some genera wholesale, such as *Allium* spp., mainly for animal toxicity.
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
- **Toxicity** (hand-curated, *provisional*): each proposed species has one entry in `data/reference/toxicity_curated.csv` (built by `pipeline/lip/m3/toxicity.py`).
  - **Source:** one reputable source opened in the run: an EMA herbal document (monograph, public summary or public statement) or a peer-reviewed PMC article with a Creative Commons licence.
  - **Quote:** one sentence, re-checked against the fetched source on every run. PDF text is extracted with pypdf and whitespace-normalised.
  - **Category:** says what the source reports, not a safety rating: `toxic_reported`, `concern_reported`, `no_toxicity_reported`, `data_lacking`, or `unknown` (no source located).
  - **Status:** every entry is `ai_drafted_unverified`, with `verified_by` empty for human review. `no_toxicity_reported` and `unknown` are never evidence of safety.
  - **Retention:** toxic species stay in the proposal; the flag is for a lab's risk assessment.
  - **Evidence scope:** each entry records what its evidence covers when that is narrower than "this species, in people": animal only, in vitro only, genus level, one preparation, or essential oil only. For example, the onion entry is `toxic_reported`, but its evidence is from animals only (veterinary).
- **Human review** ([docs/STUDY_SET_REVIEW.md](docs/STUDY_SET_REVIEW.md), generated by `lip m3 review`). The project lead reviewed every proposed species with:
  - its names as written and passage IDs;
  - a description excerpt;
  - resolution evidence and links;
  - vehicle and preparation-word counts (a heuristic proxy until M1 is run);
  - compounds and toxicity.

  Decisions are recorded in `config/study_set_review_decisions.csv` (approve / unsure / reject). **Unsure counts as reject**: only approved species form the headline set (`headline` in the proposal CSV). A name entry the reviewer identified as a different plant is removed from that species in `config/name_entry_exclusions.csv`, and a passage about a different plant inside a chapter (e.g. Culpeper's *Lavender Cotten*) in `config/passage_exclusions.csv`. Neither then counts towards attestation; removals never veto a species. A conditional approval ("approve if at least 3 attestations remain") is applied mechanically. A species can also be removed outright (`config/study_set_exclusions.csv`). Each file records who decided, when and why.

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

**Descriptor error in the reported ranges** (uncertainty reporting, not scoring). Every reported 5th–95th range (profiles, known case, literature tables) comes from the same Monte Carlo draws with Normal descriptor noise added to logP. The noise SD is chosen so that its mean absolute error equals the Crippen MAE against experiment: σ = MAE·√(π/2). Both values are read from `data/interim/m4/logp_validation.json`.
- The median and the drivers are the primary model's, unchanged. So every score that uses the median is unaffected: the exploratory set, v1 and v2 keep their results exactly, and a test checks this.
- The range without descriptor error is kept as `rangeModelOnly`.
- The model version hash is unchanged, because `config/prep_model.toml` is unchanged.

**Acidity** (heuristic). A SMARTS rule finds basic nitrogen. In vinegar such compounds get a logD shift of 1–3 log units, which raises aqueous extraction. The `acidity` driver reports the effect.

**Heat** (heuristic). SMARTS alerts flag heat-sensitive groups: endoperoxides and peroxides, labile esters, glucosinolates and cyanogenic glycosides. A volatility rule (MW < 250, HBD ≤ 1, TPSA < 40) marks steam-volatile compounds. Each alert has a degradation or loss range for warm and for boiled preparations; cold preparations lose nothing.
- **Distillation:** carries volatile compounds only.
- **Exploratory:** xTB Wiberg bond orders are recorded for flagged O–O bonds.

**Filtration.** An unfiltered preparation carries a fraction (5–30%) of the undissolved material as suspension. Poultices and ointments (material applied whole) carry 30–80%. When filtration is unknown, each draw is filtered or not with equal probability.

**Training overlap.** Crippen's training molecules (Wildman & Crippen 1999) are not distributed with RDKit, so exact overlap with the test set can't be determined. As a proxy, metrics are recomputed on compounds whose every cited measurement source was first published in 2000 or later (Crossref years). Those values cannot have entered the 1999 training set through those sources. The result is reported next to the main comparison.

**Known-case test.** Artemisinin must:
- trigger the heat flag;
- predict a median below 0.30 for cold water;
- predict a median above 0.60 for low-temperature nonpolar extraction.

The thresholds were set in the config before running. A pass whose 5th–95th percentile range crosses a threshold is reported as a **borderline pass**. The per-factor drivers are reported for every preparation, together with an unfiltered cold-water variant, to show the suspension assumption's effect.

**Literature checks** (*provisional*, §10). They are never pooled.
- **Exploratory:** 9 rows across 5 plants, selected after the model was built.
- **Pre-registered v1:** the rule in [docs/PREREGISTRATION.md](docs/PREREGISTRATION.md) was committed before any rows were collected: 6 plants, fixed PMC queries, a mechanical sentence rule, and a target of about 30 rows. It mostly found essential-oil rows.
- **Pre-registered v2 (water preparations):** the rule in [docs/PREREGISTRATION_v2.md](docs/PREREGISTRATION_v2.md) was committed and pushed before any v2 row was collected. It covers infusions, decoctions, juices and cold-water preparations of the 30 study-set species plus 6 well-studied tea plants. It sets separate quotas of 15 `present` and 15 `low` rows, and a second PMC query per plant that targets absence reports. Shortfalls are reported, not filled by relaxing the rule. A post-hoc row audit by the AI is reported beside the registered result, never instead of it.

The single-row checks (exploratory, v1, v2) use the same thresholds: "present" requires a median ≥ 0.40 and "low" requires < 0.30. Agreement is reported separately for `present` and `low` rows.

**Extraction is not detection.** The model predicts the *fraction* of a compound that a preparation carries. A published report records whether the compound was *detected* or how much was measured. That depends on three things:
- the plant's content of the compound;
- the fraction extracted;
- the method's detection limit.

LOTUS records which compounds occur in a plant, not how much, so the model cannot predict detection. Single-row checks (exploratory, v1, v2) therefore test a mixture of two questions. Two failure modes follow:
- A highly extractable compound that the plant barely contains can be "not detected" in a tea, even though the model is right that water would carry it.
- A poorly extracted compound that the plant contains in large amounts can still be detected, even when only a small fraction reaches the cup. Artemisinin in sweet wormwood tea is the example: the model predicts that a minority fraction reaches the tea, and the paper reports measurable artemisinin (value in RESULTS.md).

Neither case is evidence about the extraction fraction. The paired v3 design addresses this. It compares two compounds across two preparations of the same material in the same table, so plant content and detection limits cancel in the double ratio.

- **Pre-registered v3 (paired, within plant):** the rule in [docs/PREREGISTRATION_v3.md](docs/PREREGISTRATION_v3.md) was committed before collection, with one amendment, also committed before collection.
  - **Data:** tables in CC-licensed PMC articles that measure two or more preparations of the same plant material.
  - **Outcome:** the sign of the double ratio (X/Y in P1) ÷ (X/Y in P2), which the model predicts from extraction fractions alone.
  - **Analysis:** mean per-article agreement, with a cluster-bootstrap CI over articles.
- **v3 result and the screening finding.** v3 is reported as **inconclusive**: too few articles qualified to support or reject the model. The screening is reported as a finding in its own right. Across all 40 plants, very few articles directly compared two preparations of the same material in a usable table; the counts and the breakdown of exclusion reasons are in RESULTS.md. Within that sample, this is evidence that modern studies rarely test or report preparation effects in a comparable form, which is the gap Phase 5 is designed to measure. The screen's limits:
  - the first result page of two PMC queries per plant;
  - a Creative Commons licence and the plant's name in the title were required;
  - only HTML tables were read.
- **Complete chemical names (v3 onwards).** Compound names in future registered checks must match as complete chemical names (`pipeline/lip/m4/chemnames.py`). Table numbers in future registered checks use `pipeline/lip/m4/values.py`, which reads thousands separators (`1,234.5`, `1.234,5`, `1 234.5`) and returns *missing* for the ambiguous `1,234`. v3 keeps its registered parser and is not re-scored. This rejects class measures ("total phenol content"), aglycones followed by a glycoside or locant ("apigenin 7-O-glucoside"), and derivative or class words. Table labels must equal one known name. v1 and v2 keep the matcher they were registered with and are not re-scored.

**Water-window diagnostic (no model change).** `lip m4 water-calibration` plots the cold-water median and its 5–95% range against logP, for a logP grid and for every study-set compound. The output is [docs/figures/water_likelihood_vs_logp.svg](docs/figures/water_likelihood_vs_logp.svg) and `data/interim/m4/water_calibration.json`. For a filtered, cold, aqueous preparation, every factor except the solvent window is 1, so the prediction is a one-variable logistic in Crippen logP. The model has no solubility, melting-point, dose or contact-time term.

**Secondary variant `water-partition-slope`** (pre-registered in v2, evaluated on v2 rows only):
- the window slope is fixed at ln 10, the slope of a two-phase partition equilibrium;
- the logP descriptor gets explicit Normal noise with SD equal to its validation RMSE.

It does not replace the primary model. Adopting it would need a new registration and new rows.

**Outputs:** `site-data/profiles/` (one file per species plus `index.json`; study-set species × 13 preparations; index contract v1.4 with cited toxicity evidence) and `data/interim/m4/profiles_long.parquet`.

## 10. Provisional references (AI-made; never presented as validation)

Until the human gold sets exist, three references made by an AI (Claude Code) let the pipeline be developed and checked. Each is stored separately, marked with a `basis`, and written only to `metrics.provisional`. None ever enters a gold field.

| Reference | basis | What it is | Limits |
|---|---|---|---|
| `data/silver/silver_v1.json` | `silver_ai_reference` | Recipe labels for the 50 sample passages, written by the AI directly from the guidelines (`data/silver/silver_v1_spec.py`). Every quote is checked verbatim by `lip m1 silver`. | Same author as the guidelines and few-shot examples, so agreement may be inflated by shared conventions. |
| `data/gold/name_identifications.csv`, `draft*` columns | `ai_drafted_unverified` | Candidate identifications drafted only from sources fetched in the run: Lewis & Short (PerseusDL TEI) and English Wikipedia. Each has a quoted line, checked against the fetched text on every run. Bostock & Riley are excluded. `verified_by` is empty. | **Lewis & Short and Wikipedia are not independent modern scholarly sources.** L&S (1879) may rest on the same older commentators as the system's inputs, and Wikipedia is tertiary. The drafts stay unverified. |
| `data/reference/prep_literature_v1.csv` | `ai_curated_literature_reference` | **Exploratory:** 9 statements from 5 PMC articles. Each quote from an openly licensed article is checked against the fetched article. The one article with no stated licence (PMC2995283) is paraphrased and cited, not quoted, and checked by short anchor terms. | Selected after the model was built, by the same AI; n is small. |
| `data/reference/prep_literature_prereg_v1.csv` | `ai_curated_literature_reference` | **Pre-registered:** rows selected by the committed rule (docs/PREREGISTRATION.md). | The rule and code were written by an AI. The mechanical rule mostly yields essential-oil rows, which makes it a weak test of aqueous and alcoholic preparations. |
| `data/reference/prep_literature_prereg_v2.csv` | `ai_curated_literature_reference` | **Pre-registered v2:** aqueous-preparation rows selected by the committed rule (docs/PREREGISTRATION_v2.md), with each article's stated licence. | The rule and code were written by an AI. The sentence rule cannot tell "the preparation does not carry it" from "the plant has little of it". Some rows are mechanical misreadings; these are listed in the post-hoc audit (`ai_post_hoc_audit_unverified`). |

The annotation tool's independent mode never shows any of these. **Review** mode, for adjudication only, shows human labels beside the silver labels.

## 11. Hypothesis ranking (M6)

A hypothesis compares a species' **faithful** preparation (as the recipe made it) with the **modern** preparation a study used (from the Phase 5 audit). Its profile gap is 1 − cosine similarity of the two predicted compound profiles, with equal weights because LOTUS has no abundance data. The ranking uses only gaps that hold across the uncertainty range (`pipeline/lip/m6/ranking.py`, contract v1.5 P35):

1. **Coupled draws.** Each compound is simulated in both preparations. The descriptor-error draw (Normal, SD from the Crippen MAE) is shared between the two, because a compound's logP error is the same in both. Each draw gives one gap.
2. **Wide compounds cannot drive a rank** (heuristic). A compound whose reported 5th–95th range is wider than 0.8 in either preparation is left out of both profiles. A candidate needs at least 5 usable compounds to be ranked.
3. **Ranking key.** The gap's 5th percentile, which is the gap that holds in 95% of draws. Ties are broken by P(gap > 0.2), a heuristic threshold, then by the median gap.
4. **Contract fields.** `profileGap` is stored as `{median, 5th, 95th}`, with the rule's inputs in `gapRanking`. The median-gap rank is kept for comparison only.

**Stability test** (`python -m lip m6 rank-demo`). No audit data exist yet, so the rule is tested on model-only candidate pairs: every study-set species × historical preparation × modern extract. These are explicitly **not hypotheses**. Rank stability is measured two ways, for both the robust and the median-gap rankings:
- reseeding the Monte Carlo;
- a compound bootstrap that resamples each species' compound list.

Each uses Spearman correlation and top-20 overlap. Results are in RESULTS.md.

## 12. Limitations

- **Extraction is not detection** (§9). The model predicts extracted fractions, but validation rows record detection or amounts, which also depend on plant content and detection limits. LOTUS has no abundance data, so single-row agreement rates measure a mixture of the two. Only paired, within-plant comparisons (v3) cancel the content term, and v3 was inconclusive because few studies report such comparisons.
- **One descriptor.** The aqueous prediction is a logistic in Crippen logP. It has no solubility, melting-point, dose or contact-time term (§9, water-window diagnostic). Descriptor error (MAE against experiment) is now shown in every range but not removed.
- **Heuristic factors.** Heat alerts, volatility, filtration carry-over, acidity and the size penalty are heuristics with assumed ranges. They are not fitted to data.
- **References made by an AI.** Every validation reference so far was built or curated by an AI: the silver labels, the drafted name identifications, the literature tables, the toxicity entries and the genus audit. All are reported as provisional. None has been checked by a person yet.
- **Names.** Classical names often have several or uncertain identities. Disputed resolutions are kept with their candidates but are excluded from attestation counts. The genus-signal audit reviewed the undisputed resolutions that used that signal; other false friends may remain among the disputed ones.
- **Pliny is lower confidence** than Culpeper. It is a 19th-century English translation with classical plant names, and resolves with far more disputes (per-source table in RESULTS.md).
- **Coverage.** LOTUS records occurrences per organism, not per plant part, so the part named in a recipe cannot be matched to the part analysed.
