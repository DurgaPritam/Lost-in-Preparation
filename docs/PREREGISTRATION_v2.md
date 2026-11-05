# Pre-registration: water-preparation check of the preparation model (v2)

Registered: 2026-11-05, **before** any v2 row was collected. The commit that adds this file is the registration. Any deviation from it will be listed under "Deviations" below and reported with the results.

## Why a second registration

The v1 check ([PREREGISTRATION.md](PREREGISTRATION.md)) found 19 rows. 18 of them were essential oils and all 19 were labelled `present`. It therefore barely tests what most historical recipes are: infusions, decoctions and juices. It also never tests the model's ability to predict that something is *not* carried.

v2 targets aqueous preparations only, and deliberately collects rows where a compound is reported absent or low. v1 and v2 are reported separately and are never pooled. The 9-row exploratory table is excluded from both.

## Model under test (frozen)

- **Primary model:**
  - model version `prep-model:f4c4c5ef8a` (hash of `config/prep_model.toml`);
  - descriptor `rdkit` (Crippen logP);
  - 13-preparation grid in `pipeline/lip/m4/model.py`;
  - repository commit `3c39a6a`.
- No change to the primary model, its parameters or its thresholds between this registration and the run.

## Plants (36, in this order)

**Study set (30, the proposed species in `data/interim/m3/study_set_proposal.csv`).** Each entry gives the Latin name, then the other names accepted in the title test.

1. *Artemisia absinthium*: wormwood, absinthe
2. *Agrimonia eupatoria*: agrimony
3. *Crocus sativus*: saffron
4. *Symphytum officinale*: comfrey
5. *Lavandula angustifolia*: lavender, *Lavandula officinalis*
6. *Ajuga chamaepitys*: ground pine, yellow bugle
7. *Ranunculus ficaria*: lesser celandine, *Ficaria verna*
8. *Glycyrrhiza glabra*: licorice, liquorice
9. *Melissa officinalis*: lemon balm
10. *Hyssopus officinalis*: hyssop
11. *Pastinaca sativa*: parsnip
12. *Galium aparine*: cleavers
13. *Centaurium erythraea*: centaury, *Centaurium umbellatum*
14. *Chelidonium majus*: greater celandine
15. *Hyoscyamus niger*: henbane
16. *Raphanus sativus*: radish
17. *Laser trilobum*
18. *Salvia sclarea*: clary sage
19. *Euphorbia antiquorum*
20. *Papaver somniferum*: opium poppy
21. *Humulus lupulus*: hop, hops
22. *Allium cepa*: onion
23. *Coriandrum sativum*: coriander, cilantro
24. *Carum carvi*: caraway
25. *Citrullus colocynthis*: colocynth
26. *Cotinus coggygria*: smoke tree, smoketree
27. *Dioscorea communis*: black bryony, *Tamus communis*
28. *Filipendula ulmaria*: meadowsweet
29. *Betonica officinalis*: betony, *Stachys officinalis*
30. *Moricandia arvensis*

**Well-studied tea plants (6).**

31. *Artemisia annua*: sweet wormwood
32. *Matricaria chamomilla*: chamomile, *Matricaria recutita*, *Chamomilla recutita*
33. *Mentha × piperita*: peppermint, *Mentha piperita*
34. *Thymus vulgaris*: thyme
35. *Salvia officinalis*: sage
36. *Salvia rosmarinus*: rosemary, *Rosmarinus officinalis*

*Artemisia annua* is included because it is the best-studied case of a plant whose active compound (artemisinin) is assessed in water preparations.

## Sources

### Search

- PMC web search (`https://pmc.ncbi.nlm.nih.gov/search/?term=…`), first result page, in the order returned.
- Two queries per plant, using the Latin name with "×" removed:
  - **Q1** `<Latin name> (infusion OR decoction OR tea OR "aqueous extract" OR juice)`
  - **Q2** `<Latin name> (infusion OR decoction OR tea OR "aqueous extract" OR juice) ("not detected" OR "below the limit")`
- Q2 deliberately surfaces articles that report absence.
- Screening order: the results of Q2 first, then the results of Q1 not already seen.
- **Syntax check before registration.** The boolean and phrase syntax was checked on *Hibiscus sabdariffa*, a plant not in this list. Only whether the two result sets differed was looked at, not their content.

### Article eligibility (screened in order)

1. The article page states a Creative Commons licence.
2. The title names the plant (any name listed above, case-insensitive, whole words).
3. The article text (excluding the reference list) contains an analytical-chemistry term: `HPLC`, `UHPLC`, `UPLC`, `LC-MS`, `LC–MS`, `GC-MS`, `GC–MS`, `chromatograph*`, `mass spectromet*` or `NMR`.
4. It is not one of the 5 exploratory PMCIDs or the 9 PMCIDs of the v1 rows:
   - exploratory: PMC2995283, PMC13074686, PMC7587570, PMC10217939, PMC11944828;
   - v1 rows: PMC10180401, PMC10707927, PMC10819686, PMC12309076, PMC13290042, PMC5622382, PMC6843575, PMC8398316, PMC9099978.

**Text used.** The article page, with the reference list and every HTML `<table>` removed. It is split into sentences at `.`, `!` or `?` followed by whitespace. Sentences longer than 600 characters are skipped as likely table or figure residue.

## Sentence rule (applied mechanically)

A sentence qualifies when **all** of these hold:

1. **Compound.** It names a compound from:
   - the v1 compound list (with its synonyms), or
   - the English labels (≥ 5 characters) of the compounds that LOTUS/Wikidata records for that plant, retrieved with the same `found in taxon` query as M3 (`pipeline/lip/m3/compounds.py`).

   Matching is case-insensitive and on whole words: neither side of the match may be a letter, digit or hyphen. A shorter aglycone name inside a longer matched name does not count. Solvent and reagent labels never count as compounds: water, ethanol, methanol, acetone, hexane, chloroform, ethyl acetate, acetonitrile, acetic acid, formic acid, dimethyl sulfoxide.
2. **Preparation.** It names exactly one aqueous preparation type from the table below, after mapping. Cold-water phrases are matched first and removed before the other patterns are tested, so "cold infusion" counts once, as cold.
3. **Cue.** It shows a presence cue or an absence cue (lists below).
4. **No exclusion term.** It mentions none of the following.
   - Non-aqueous preparations: `essential oil`, `volatile oil`, `\boil\b`, `distill*`, `tincture`, `ethanol*`, `methanol*`, `hydroalcoholic`, `hydroethanolic`, `acetone`, `hexane`, `supercritical`, `CO2`, `chloroform`, `ethyl acetate`, `dichloromethane`, `petroleum ether`, `butanol`.
   - The v1 exclusions: `fraction`, `partition`, `commercial`, `synthetic`, `derivative`, `total phenolic`, `activity`, `inhibit`, `IC50`, `MIC`.
   - Method sentences: `standard`, `calibration`, `spiked`, `recovery`.

### Aqueous preparation terms → model preparation

| Terms in text (regular expressions, case-insensitive) | Model preparation |
|---|---|
| `cold[- ]water`, `cold infusions?`, `cold[- ]brew\w*`, `cold macerat\w*` | cold water infusion |
| `\binfusions?\b`, `herbal teas?`, `\bteas?\b`, `aqueous extracts?`, `water extracts?`, `hot water` | hot water infusion (tea) |
| `\bdecoctions?\b` | decoction in water |
| `\bjuices?\b` | fresh juice |

### Cues

- **Absence cues:**
  `not detected` · `n\.d\.` · `not found` · `not present` · `undetect\w*` · `below the (limit|detection)` · `\babsent\b` · `\btraces?\b` · `low (concentration|amount|level|content)s?` · `lacking` · `free of` · `did not contain` · `(was|were) not extracted` · `poorly extracted` · `negligible`
- **Presence cues:**
  the v1 list (`main`, `major`, `predominant`, `principal`, `dominant`, `rich in`, `contain`, `identified`, `detected`, `found`, `%`, `mg`), plus `quantified`, `abundant` and `highest`.
- **Label.** Any absence cue → `low`. Otherwise → `present`.

### Rows

1. **Unit.** One row per (plant, compound, model preparation). The first qualifying sentence wins, in screening order, then article order, then sentence order.
2. **Caps:**
   - at most 2 rows per article;
   - per plant, at most 2 `present` rows and at most 2 `low` rows.
3. **Quotas:** **15 `present` + 15 `low` = 30 rows.** Each label is filled separately, round-robin over the plants in the order listed.
4. **Shortfall.** If a quota cannot be filled, the number found is reported and the rule is not relaxed. A shortfall in one label is not made up from the other.
5. **Structures:**
   - LOTUS-matched compounds use the M3 standardised structure;
   - v1-list compounds are resolved by PubChem name, as in v1.

   The model input is the RDKit descriptor set computed from that structure (`pipeline/lip/m4/chem.py`).

## Agreement rule and analysis

- **Agreement** (thresholds unchanged, `config/prep_model.toml [literature_check]`):
  - `present` → predicted median ≥ 0.40;
  - `low` → predicted median < 0.30.
- **Reported, for v1 and v2 separately, never pooled:**
  - rows found;
  - overall agreement with a Wilson 95% CI;
  - agreement on `present` rows and on `low` rows separately, each with a Wilson 95% CI;
  - agreement by model preparation.
- **Basis:** `ai_curated_literature_reference`, *provisional*. The rule and the code are written by an AI. This is not human-curated validation.
- **Known limitation, stated in advance.** A `low` report can mean either that the preparation does not carry the compound, or that the plant contains little of it. The sentence rule cannot tell these apart. The model only predicts the first.

## Secondary analysis: water-window calibration variant (evaluated on v2 rows only)

### Motivation

The motivation is written before any v2 row is seen.

The model's water window is `f = sigmoid(k · (upper − logP))`, with `k ~ U(1, 2)` and `upper ~ U(1.0, 2.5)`. This curve has exactly the shape of a two-phase partition equilibrium between water and a lipophilic plant phase, with phase ratio `r = 10^(−upper)`:

```
f = 1 / (1 + r · 10^logP)
```

In that equation the slope in log₁₀ units is fixed at `k = ln 10 ≈ 2.303`. The registered range `k ∈ [1, 2]` is shallower than this physical slope. A shallower slope raises predictions for lipophilic compounds and lowers them for polar ones.

Part of the shallowness can legitimately stand in for error in the logP descriptor. That error is better modelled explicitly.

### Variant `water-partition-slope`

Two changes; everything else is identical (same seeds, same factors, same thresholds):

1. `k = ln 10`, fixed, in every solvent window.
2. The lipophilicity of each Monte Carlo draw is `logP + ε`, with `ε ~ Normal(0, 0.8374)`. 0.8374 is the RMSE of the RDKit descriptor against experimental logP in `data/interim/m4/logp_validation.json` (`rdkit_all.rmse`).

### Use

- The variant is evaluated **only on the v2 rows**, with the same agreement rule, and reported beside the primary model. It is not evaluated against the artemisinin criterion.
- The primary model remains the default.
- Adopting the variant would need a further registration and evaluation on new rows. The v2 result alone does not change the default model.

## Deviations

None. The run used the frozen model, the registered queries, rule, caps, quotas and thresholds. Results are in [RESULTS.md](../RESULTS.md), generated from `data/interim/m4/literature_prereg_v2.json`.

**Implementation clarifications.** None of these changes a rule.
- The LOTUS labels for the 30 study-set species are taken from the M3 output, which is produced by the same `found in taxon` query. For the 6 well-studied plants, the query is run on every Latin name listed for the plant.
- When one LOTUS label names several Wikidata items, the item with the lowest QID is used.
- "A shorter aglycone name inside a longer matched name does not count" is applied generally: any compound match whose span lies inside a longer compound match is dropped.
- Each article's stated licence is recorded in the row output.

**Post-hoc, not registered.** After the run, the AI read every collected row and labelled the mechanical misreadings. Examples are a compound name taken from "total phenol content", and a sentence about a different plant cited inside the target plant's article. This audit is reported beside the registered result, never instead of it, with basis `ai_post_hoc_audit_unverified`.
