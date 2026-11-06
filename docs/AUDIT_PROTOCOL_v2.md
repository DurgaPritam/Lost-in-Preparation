# Phase 5 audit protocol v2: pre-registered re-analysis after v1's design flaw

Committed on 2026-11-06, **before** any v2 result was computed. Written by an AI (Claude, in Claude Code); the design decisions in §4 and §5 were set by the project lead.

## Why v2 exists

v1 ([AUDIT_PROTOCOL_v1.md](AUDIT_PROTOCOL_v1.md)) is reported exactly as pre-registered, and its result stands as the v1 result. Its design has three flaws:

1. **Solvent rule:** only a historical `[water]` preparation could ever match a modern solvent. Recipes made with wine, vinegar, oil, honey or no vehicle were therefore unmatchable, so v1's headline mostly reflects the protocol, not the literature.
2. **Eligibility:** a retrieved study could be judged "not faithful" on a plant-part mismatch alone, even if it never prepared the plant (pure-compound papers, surveys, case reports).
3. **Search:** the pair-level PubMed query was narrow, and most pairs got no hits.

v2 is a re-analysis with rules fixed in advance. v1 and v2 are reported side by side, and v2 is labelled **"pre-registered re-analysis after v1's design flaw"**.

## 1. Frame

The pairs are built exactly as in v1 (same attribution rule, same indication lexicon `config/m5_indications/v1.toml`, single-plant recipes only). The one difference is that the logged M1 corrections in `config/m1_corrections.csv` are applied first. These are field corrections requested by the project lead, with evidence; they change preparations, not the set of pairs.

Output: `data/interim/m5/v2/pairs.json`. The v1 `data/interim/m5/pairs.json` is left untouched.

## 2. Search: species-level literature, filtered by MeSH

- **Source:** the species-level PubMed records already collected in Phase 5 prep: `data/interim/m5/literature/<wfoId>.json`. These cover the accepted name and WFO synonyms in title or abstract, the first 300 by relevance, retrieved on 2026-11-06.
- **Membership:** a record belongs to pair (species, descriptor D) if any of its MeSH headings is D or a descendant of D in the MeSH tree.
- **Descendants:** taken from NLM's MeSH SPARQL endpoint (`id.nlm.nih.gov/mesh/sparql`, `meshv:broaderDescriptor*`, current MeSH year) and cached.
- **No MeSH indexing:** a record without MeSH headings (for example, not yet indexed) cannot match. It is counted.

## 3. Eligibility (rule fixed now)

A record is **excluded**, with the reason counted, if any of these holds:

1. **Publication type:** Review, Systematic Review, Meta-Analysis, Editorial, Comment, Letter, News, Published Erratum, Retracted Publication or Case Reports.
2. **Survey:** its title or abstract matches a survey pattern (ethnobotanical, ethnomedicinal, survey, questionnaire, interview, informants; lexicon v2 `[eligibility].survey`).
3. **No text:** it has neither an abstract nor open-access methods.
4. **No prepared plant material:** its coded text does not show that the plant material was prepared. Coded text is title plus open-access methods (`pmc_fulltext`), else title plus abstract (as in v1). A study passes this test if either:
   - (a) the rule extractor finds at least one preparation with a known solvent class (§5); or
   - (b) a plant-preparation phrase matches (lexicon v2 `[eligibility].plant_preparation`: "leaf extract", "extract of the roots", "aqueous extract", "decoction", "essential oil", and similar).

A pure-compound study (for example, of glycyrrhizin alone) meets neither (a) nor (b) and is excluded.

## 4. Coding

The rule-based extractor `pipeline/lip/m5/rules.py` uses lexicon `config/m5_lexicon/v2.toml`. This is v1 plus explicit categories for acidified aqueous, fresh juice, powder given whole, oil macerates and wine extracts, and the eligibility patterns; the changes are listed in its CHANGELOG. There is no LLM. Unstated values are `unknown`.

The 40-study hand-check sheet from v1 (`data/reference/m5_handcheck_v1.csv`) remains the human check on the extractor.

## 5. Solvent equivalence classes

**Historical class** (from the recipe's vehicle list, with `unknown` removed):

| Vehicles | Class |
|---|---|
| `[water]` | aqueous |
| `[vinegar]`, `[vinegar, water]` | acidified aqueous |
| `[wine]`, `[wine, water]` | low-ethanol hydroalcoholic |
| `[oil]` | oil |
| `[none]`, with part juice or process expression | fresh juice |
| `[none]`, with process powder | powder given whole |
| `[none]`, any other use (applied, worn, strewn) | **no modern analogue** |
| any list containing honey (hydromel, oxymel, honey alone) | **no modern analogue** |
| `[other]` (milk, ale, grease, rose water, broth …) or any other mixture | **no modern analogue** |
| nothing left (unknown) | unknown |

The project lead set the classes for water, wine, vinegar, honey/oxymel and none/fresh juice. Three were added by the AI and are flagged here as such: oil, powder given whole, and "other / other mixtures → no modern analogue".

**Modern class** (from the extractor's solvent category, matched text and ethanol fraction):
- **aqueous:** water, including infusion and decoction.
- **acidified aqueous:** acidified water, acetic-acid solution or vinegar extract.
- **low-ethanol hydroalcoholic:**
  - a hydroethanolic solvent with a stated ethanol fraction ≤ **0.20** (v/v);
  - or a wine extract.
- **high-ethanol hydroalcoholic:** a stated fraction above 0.20.
- **hydroalcoholic, strength unstated:** a hydroethanolic solvent with no stated fraction.
- **Other classes:** fresh juice; powder given whole; oil (oil macerate or oil extract); ethanol (≥ 95%), methanol, hexane, chloroform, ethyl acetate, dichloromethane, acetone, CO₂, other (each its own class).
- **unknown.**

**Why 0.20 is the cut-off for wine.** This is general background knowledge, not a source cited in this repository. Fermentation alone rarely takes wine much above about 15% ethanol by volume, and fortified wines such as sack are commonly around 15–22%. The cut-off of 20% v/v is a round upper bound that lets table wines and most fortified wines count as wine-like. It excludes the 30–96% ethanol typical of modern hydroalcoholic extracts, which dissolve a different range of compounds.
- **Sensitivity:** the solvent match rate is also reported at cut-offs of 0.15 and 0.25.
- **Not tested here:** a modern study that macerated a plant in actual wine is matched only if its text says so ("wine extract", "macerated in wine").

**Solvent comparison:**
- **no modern analogue:** if the historical class is "no modern analogue". These are reported separately and never scored as unfaithful.
- **unknown:** if either class is unknown. A low-ethanol historical class against a modern "strength unstated" class is also unknown.
- **match:** if the classes are equal.
- **mismatch:** otherwise.

## 6. Per-variable fidelity and the overall rate

**Other variables:** heat, part, fresh or dried, and filtration match when equal and mismatch otherwise. Unknown on either side stays unknown.

**Unit:** a (pair, eligible study). For each variable *v*:
- **match:** if any comparison of a study preparation with a historical preparation of the pair matches on *v*;
- **mismatch:** if every known comparison mismatches;
- **unknown:** if none is known;
- **solvent only, no modern analogue:** if every non-unknown comparison is no-analogue.

**Per-variable fidelity rate:** the share of units that match, among units that match or mismatch. It is reported for solvent, heat, part and fresh or dried (filtration is also reported). Each rate carries a 95% CI (bootstrap over pairs, B = 2000, seed `20261106`), the number known and the number unknown. The solvent rate also reports the number with no modern analogue.

**Overall, per comparison:**
- **no analogue:** if the solvent is no-analogue;
- **mismatch:** if any variable mismatches;
- **match:** if solvent and heat both match and nothing mismatches;
- **unknown:** otherwise.

**Overall, per unit:**
- **faithful:** if any comparison matches;
- **not faithful:** if every comparison that is not no-analogue mismatches, and there is at least one;
- **no modern analogue:** if every comparison is no-analogue;
- **unknown:** otherwise.

**Overall fidelity rate:** the share of units that are faithful, among faithful and not-faithful units, with a 95% CI and n. It is also reported as the share not faithful, for comparison with v1. No-analogue units are counted and reported separately.

**Breakdowns:** Pliny-only pairs are also reported separately (lower confidence), as are units coded from methods and units coded from abstracts.

## 7. Phase 6 under v2

Same rule as v1 §7 (`pipeline/lip/m6/hypotheses.py`), with these differences:
- **Statuses:** v2 statuses are used.
- **Corrections:** the logged corrections are applied.
- **Candidates:** pairs with at least one faithful or not-faithful unit and no faithful unit.

v1 and v2 hypotheses are reported side by side.

## 8. Reporting

- **RESULTS.md:** shows v1 and v2 side by side, with v2 labelled "pre-registered re-analysis after v1's design flaw".
- **v1 note:** v1 keeps its own note that its solvent rule makes non-water recipes unmatchable.
- **Contract file:** `site-data/audit.json` stays the v1 output.
- **v2 outputs:** written to `data/interim/m5/v2/` and `data/interim/m6/v2/`.
- **What the numbers mean:** they describe how studies prepared the plant compared with the recipes. They are not evidence that any preparation works or is safe.
