# Phase 5 audit protocol v1 (fixed before retrieval)

Committed on 2026-11-06, **before** any study was retrieved for a species–indication pair and before any audit result existed. This follows the PRD instruction to define the plant–use frame before looking at audit results, which protects the headline number. Any later change goes in a new version (`AUDIT_PROTOCOL_v2.md`), with the reason, and both results are reported.

Written by an AI (Claude, in Claude Code). The rules, lexicons and code are AI-written. The hand-check (§6) is the human check on the extractor.

## 1. Frame: species–indication pairs (census, no sampling)

- **Source:** the frame is every pair in `data/interim/m5/pairs.json`, built by `pipeline/lip/m5/pairs.py` from the M1 session extraction of the 19 Phase 5 species (`data/interim/m1/predictions_approved.json`).
- **Attribution (heuristic, conservative):** a recipe counts for a species only if both hold:
  - its passage belongs to that species;
  - its plant name is not more specific than one of the species' entry names.
  Unattributed recipes are counted. Examples: "Sea Wormwood" in the Wormwood entry, "Leeks" in Onions, the antidote plants in Henbane.
- **Indications:** mapped to MeSH descriptors by the versioned lexicon `config/m5_indications/v1.toml` (heuristic). Each descriptor's ID was confirmed in NCBI MeSH. Indications that only refer back ("doth the same") map to nothing and are counted.
- **Recipe type:** only single-plant recipes define pairs. Compound recipes are excluded, as everywhere.
- **Historical preparations:** each pair keeps its distinct historical preparations as contract preparation keys (`part|freshOrDried|solvent|heat|filtered`).

## 2. Retrieval (per pair)

- **Query:** PubMed (NCBI E-utilities) esearch `(<accepted name and WFO synonyms>[tiab]) AND ("<MeSH descriptor>"[MeSH Terms] OR "<MeSH descriptor>"[tiab])`, sorted by relevance. The first **30** records are taken, and the total hit count is recorded.
- **Excluded:**
  - publication types Review, Systematic Review, Meta-Analysis, Editorial, Comment, Letter, News, Published Erratum and Retracted Publication;
  - records with neither an abstract nor open-access full text.
- **Licence:** for records with a PMCID, from Europe PMC (`isOpenAccess`, `license`).
- **Evidence source:**
  - **open-access records:** the methods text from Europe PMC `fullTextXML`, meaning the sections whose title matches material, method, experimental, extraction, preparation or plant. The article title is added (`evidenceSource = pmc_fulltext`).
  - **Fallback:** if there is no such section, or the record is not open access, the title plus abstract (`abstract`).
- **Storage:**
  - Abstract and methods text stay in the git-ignored cache.
  - Committed outputs carry a methods snippet only for open-access records, and offsets otherwise.

## 3. Coding

The rule-based extractor `pipeline/lip/m5/rules.py` uses lexicon `config/m5_lexicon/v1.toml` (`m5_rules/v1:<hash>`, recorded on every output). There is no LLM. Unstated values are `unknown`.

## 4. Matching rule (heuristic)

Each study preparation is compared with each historical preparation of the pair, field by field.
- **Unknown:** if either side is `unknown`, the field is `unknown`. It is never a mismatch.
- **solvent:** match only if the historical vehicle list is exactly `[water]` and the modern solvent is `water`. Any other pair of known values is a mismatch. This is because wine, vinegar, oil, honey, mixed vehicles and "no vehicle" have no equivalent among the modern solvent categories.
- **heat, part, freshOrDried, filtration:** match if the values are equal, otherwise mismatch. `not_applicable` vs `yes` is a mismatch.
- **overall:**
  - `mismatch` if any field is a mismatch;
  - `match` if no field is a mismatch **and** solvent and heat (the core variables) both match;
  - otherwise `unknown`.

**Study status for a pair:**
- **faithful:** at least one study preparation is an overall match with at least one historical preparation;
- **not faithful:** every comparison is a mismatch;
- **unknown:** anything else.

## 5. Headline (RQ1) and breakdowns

- **Headline:** among (pair, study) units whose status is known, the share that is **not faithful**.
  - The 95% CI comes from a bootstrap over pairs (B = 2000, seed 20261106). nKnown and nUnknown are always reported, per contract P16.
- **Also reported:**
  - the same share counting each study once (unique PMIDs);
  - per-field mismatch rates among known comparisons (solvent, heat, filtration, part, freshOrDried);
  - coverage: pairs with no retrieved study, and studies with every field unknown.
- **Confidence:** Pliny-derived pairs are reported separately as lower confidence.
- **What the number means:** it describes how the retrieved studies prepared the plant compared with the recipes. It is not a claim about efficacy, and a high share does not mean the historical preparations work.

## 6. Hand-check of the extractor (40 studies)

- **Sample:** 40 audited studies, drawn with seed `20261106` and stratified by evidence source: 20 open-access methods and 20 abstracts, or proportionally if one stratum is short.
- **Sheet:** `data/reference/m5_handcheck_v1.csv`. It holds the extractor's values and evidence, plus empty columns for the human reading: one per field, and notes.
- **Text for reading:** the full texts are written to a git-ignored local file.
- **Accuracy:** per-field accuracy, including unknown-vs-stated errors, is computed only from the filled sheet.

## 7. Phase 6 (hypothesis ranking)

A pair becomes a hypothesis candidate when it has at least one study with status known and **no faithful study** (`neverTestedFaithfully`).

**Faithful preparation:** the pair's historical preparation with the most recipes that maps to an M4 preparation (heuristic map):

| Historical preparation | M4 preparation |
|---|---|
| water + cold | cold water infusion |
| water + warm | hot water infusion |
| water + boiled | decoction in water |
| water + boiled + distillation | distilled water |
| wine + cold | steeped in wine |
| wine + boiled | decoction in wine |
| vinegar + cold | steeped in vinegar |
| oil + warm | infused oil |
| juice, with no vehicle or an unknown one, cold or unknown heat | fresh juice |
| powder, with no vehicle or an unknown one | powder taken whole |

Anything else is not modelled.

**Modern preparation:** the most frequent modern solvent among the pair's studies that maps to M4.
- water uses its stated heat;
- methanol, hydroethanolic and hexane map to the M4 maceration presets;
- when a study's heat is unstated, the preset is used and the caveat is recorded.

**Ranking:** candidates are scored and ranked by the existing M6 rule (`pipeline/lip/m6/ranking.py`, contract P35). Each output is a **hypothesis worth re-testing**, never a claim that a preparation works or is safe.
