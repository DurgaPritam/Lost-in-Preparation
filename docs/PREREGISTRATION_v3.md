# Pre-registration: paired within-plant check of the preparation model (v3)

Registered: 2026-11-05, **before** any v3 row was collected and before any article for a listed plant was opened for v3. The commit that adds this file is the registration. Any deviation from it will be listed under "Deviations" below and reported with the results.

## Why a paired design

v1 and v2 scored single rows: "compound X was found, or not found, in preparation P". Whether a compound is *detected* depends on three things:

- how much of it the plant contains;
- the fraction a preparation extracts;
- the method's detection limit.

The model predicts only the extracted fraction, and LOTUS gives no amounts, so single-row checks mix the model's question with two others it cannot answer (METHODS §9, "Extraction is not detection").

A within-plant, within-study comparison removes most of that. Take two compounds X and Y, measured in two preparations P1 and P2 of the same plant material, in the same table of the same study. The **double ratio**

```
DR = (X in P1 / Y in P1) / (X in P2 / Y in P2)
```

cancels the plant's content of X and of Y, and it cancels each preparation's overall yield and the table's unit. What remains is the ratio of the extracted fractions, which is what the model predicts:

```
DR_model = (f_X,P1 / f_Y,P1) / (f_X,P2 / f_Y,P2)
```

The test asks whether the model gets the **sign** of log DR right: which compound is relatively enriched in which preparation.

## Model under test (frozen)

- Primary model `prep-model:f4c4c5ef8a`, descriptor `rdkit` (Crippen logP), repository commit `b1e5c54`.
- **Predicted medians only.** The descriptor-error ranges added in `b1e5c54` are not used.
- No change to the model, its parameters or the rules below between this registration and the run.

## Plants (40, in this order)

**Study set as of commit `b1e5c54` (28).** Titles may name a plant by its Latin name or by the common names used in v2:

*Artemisia absinthium*, *Agrimonia eupatoria*, *Crocus sativus*, *Symphytum officinale*, *Lavandula angustifolia*, *Ajuga chamaepitys*, *Ranunculus ficaria*, *Glycyrrhiza glabra*, *Melissa officinalis*, *Hyssopus officinalis*, *Pastinaca sativa*, *Galium aparine*, *Centaurium erythraea*, *Chelidonium majus*, *Hyoscyamus niger*, *Raphanus sativus*, *Salvia sclarea*, *Euphorbia antiquorum*, *Papaver somniferum*, *Humulus lupulus*, *Allium cepa*, *Coriandrum sativum*, *Carum carvi*, *Citrullus colocynthis*, *Dioscorea communis*, *Filipendula ulmaria*, *Betonica officinalis*, *Moricandia arvensis*.

**Well-studied plants (12).** For each, the Latin name is followed by the other names accepted in the title test:

- *Artemisia annua*: sweet wormwood
- *Matricaria chamomilla*: chamomile, *Matricaria recutita*, *Chamomilla recutita*
- *Mentha × piperita*: peppermint, *Mentha piperita*
- *Thymus vulgaris*: thyme
- *Salvia officinalis*: sage
- *Salvia rosmarinus*: rosemary, *Rosmarinus officinalis*
- *Foeniculum vulgare*: fennel
- *Origanum vulgare*: oregano
- *Hypericum perforatum*: St John's wort
- *Calendula officinalis*: calendula, marigold
- *Achillea millefolium*: yarrow
- *Mentha spicata*: spearmint

## Sources

### Search

- PMC web search, first result page, in the order returned.
- Two queries per plant, using the Latin name with "×" removed:
  - **Q1** `<Latin name> (infusion OR decoction OR tea OR "aqueous extract") ("essential oil" OR hydrodistillation OR ethanolic OR methanolic OR hydroethanolic OR hydroalcoholic) (HPLC OR "LC-MS" OR "GC-MS")`
  - **Q2** `<Latin name> ("essential oil" OR hydrolate OR ethanolic OR methanolic) (infusion OR decoction) composition`
- Screening order: Q1 results, then Q2 results not already seen.

### Article eligibility (in order)

1. The article page states a Creative Commons licence.
2. The title names the plant (whole words, case-insensitive).
3. It is not one of the PMCIDs used in the exploratory table, in v1 rows or in v2 rows (listed in `pipeline/lip/m4/prereg_v2.py` `EXCLUDED`, plus the v2 row PMCIDs in `data/reference/prep_literature_prereg_v2.csv`).
4. It has at least one **eligible table** (below).

**Cap.** At most **3 eligible articles per plant**, taken in screening order.

## Table rule (applied mechanically)

Only HTML tables in the article body are used, never the reference list. Free text is not used in v3.

### Reading tables

1. **Grid.** Each `<table>` is read into a grid with `rowspan`/`colspan` expanded.
   - Header rows are the rows inside `<thead>`. Without a `<thead>`, the header is the first row.
   - A column's **label** is its header cells joined by spaces.
2. **Orientation A (compounds in rows).**
   - **Column preparation:** a column's preparation is the single model preparation its label maps to (table below). A label that maps to none, or to more than one, is not a preparation column.
   - **Row compound:** a row's compound is given by its first cell. The cell must match one known compound as a **complete chemical name**, using `Matcher.exact_label` in `pipeline/lip/m4/chemnames.py` (commit `b1e5c54`).
3. **Orientation B (transposed).** Preparations are in the first column and compounds in the header cells.
4. **Choosing the orientation.** The orientation that yields more (compound, preparation) value cells is used; on a tie, orientation A.
5. **Same material.** A column's **condition** is its label with the preparation terms removed, lower-cased, with non-alphanumerics collapsed. Two preparation columns are compared only when their conditions are equal. This keeps different plant parts or samples apart.
6. **Eligible table.** At least one comparable pair of columns with different model preparations, and at least 2 compounds with values in both columns.

### Cell values

- **Number:** the first number in the cell (mean of "mean ± SD"). A comma is read as a decimal point only in `\d+,\d{1,2}` with no dot in the cell.
- **Not detected:** `nd`, `n.d.`, `ND`, `<LOD`, `<LOQ`, `bdl`, `tr`, `traces`, or a lone `-`, `–` or `−`. These are recorded as 0.
- **Missing:** an empty cell or any other text.

### Preparation terms → model preparation

Cold-water phrases are matched first and removed, as in v2.

| Terms in a column label (case-insensitive) | Model preparation |
|---|---|
| `cold[- ]water`, `cold infusions?`, `cold macerat\w*` | cold water infusion |
| `\binfusions?\b`, `herbal teas?`, `\bteas?\b`, `aqueous`, `water extracts?`, `hot water`, `\bH2O\b` | hot water infusion (tea) |
| `\bdecoctions?\b` | decoction in water |
| `essential oils?`, `\bEO\b`, `hydrodistill\w*`, `steam distill\w*`, `hydrolates?`, `hydrosols?` | distilled water |
| `ethanol\w*`, `\bEtOH\b`, `hydroethanolic`, `hydroalcoholic`, `tinctures?` | modern 70% ethanol extract |
| `methanol\w*`, `\bMeOH\b` | modern methanol extract |
| `hexane`, `petroleum ether` | low-temperature nonpolar extract (hexane) |
| `\bjuices?\b` | fresh juice |

### Compounds and structures

- **Known compounds:** the v1 compound list, plus the LOTUS labels for the plant, retrieved exactly as in v2.
- **Structures:**
  - LOTUS compounds use the M3 standardised structure;
  - v1-list compounds are resolved by PubChem name.
  - A compound without a structure is dropped and the number dropped is reported.

## Outcome

For each eligible table, each comparable column pair (P1, P2) with different model preparations, and each unordered compound pair (X, Y) with values in both columns:

1. **Skip uninformative pairs.** A pair is skipped if X and Y are both 0 in the same column, or if either compound is 0 in both columns.
2. **Replace zeros.** A remaining 0 is replaced by half the smallest positive value in its column (a limit-of-detection substitution).
3. **Observed.** `Δobs = ln(X1/Y1) − ln(X2/Y2)`.
   - **No clear difference:** if `|Δobs| < ln 1.25`, the pair is excluded.
4. **Predicted.** `Δpred = ln(LX1/LY1) − ln(LX2/LY2)`, with L the model's median likelihoods, floored at 1e-4.
   - **Abstention:** if `|Δpred| < ln 1.25`, the model is recorded as abstaining, which is reported but not scored.
5. **Agreement.** `sign(Δobs) = sign(Δpred)`.

## Analysis

- **Primary.**
  - **Per article:** agreement = agreeing pairs ÷ scored (non-abstaining) pairs.
  - **Overall:** the mean of the per-article rates, over articles with at least one scored pair.
  - **Uncertainty:** a 95% CI from a cluster bootstrap over articles (B = 2000, seed 20261106).
  - **Decision rule:** the model ranks within-plant enrichment **better than chance** if the CI's lower bound is above 0.5. "Not distinguishable from chance" otherwise. "Worse than chance" if the upper bound is below 0.5.
- **Secondary (descriptive):**
  - pooled pair-level agreement;
  - agreement by contrast class (aqueous vs distillation, aqueous vs alcohol, aqueous vs aqueous, alcohol vs distillation, other);
  - abstention rate;
  - number of articles, tables, pairs and compounds;
  - the share of pairs excluded as "no clear difference".
- **Shortfall.** Fewer eligible articles than the caps allow is reported as found. The rule is not relaxed.
- **Basis:** `ai_curated_literature_reference`, *provisional*. The rule and the code are written by an AI. v3 is never pooled with v1, v2 or the exploratory table.

## Known limitations, stated in advance

- **Units.** The rule assumes all values in one column share a unit. A table mixing units within a column would add noise; the rule does not check for this.
- **Relative versus absolute values.** Essential-oil columns are usually relative percentages, and extract columns absolute amounts. The double ratio cancels each column's unit, so this does not bias the sign. It does mean "not detected" in an essential oil can reflect the oil's composition as well as extraction.
- **Same material.** "Same material" rests on label equality. Mislabelled or merged headers can pair different materials.
- **Abstentions.** The model predicts distillation from a volatility rule and aqueous preparations from logP. Many pairs where both compounds share these features will therefore be abstentions.

## Implementation

The collector (`pipeline/lip/m4/prereg_v3.py`) is written after this registration and committed with the results. Before the run it is tested only on synthetic tables and on articles about *Hibiscus sabdariffa*, a plant not in the list.

## Amendment 1 (2026-11-05, before collection)

Committed **before** any article for a listed plant was opened for v3. Testing the collector on synthetic tables and on *Hibiscus sabdariffa* (not in the list) showed three defects in the table rule as first written:

1. **Word boundaries.** `ethanol\w*` also matched inside "methanol", so every methanol column mapped to two preparations and was dropped. Both alcohol patterns now require a word start: `\bethanol\w*`, `\bmethanol\w*`.
2. **Aqueous alcohol.** A label naming an alcohol together with "aqueous", "water" or "H2O" (e.g. "70% aqueous ethanol", "MeOH:H2O 80:20") is an aqueous-alcohol extract. The aqueous term is ignored for such a label, so it maps to the alcohol preparation instead of to two preparations.
3. **Same-material condition.** Solvent strengths and generic words made columns of the same material look different (e.g. "Infusion" vs "Methanol extract", or "(mg/g)" vs "(%)"). The condition now also removes:
   - solvent strengths (`n%`, `n:n`, `(v/v)`);
   - generic words and units: extract, sample, mean, SD, SE, RSD, area, relative, content, concentration, amount, mg, g, kg, µg, ug, ng, mL, L, DW, FW, dry, fresh weight, weight, ppm, ppb, per, of, in, the.

Nothing else changes: plants, queries, eligibility, outcome, thresholds and analysis are as registered above.

## Deviations

None. The run used the frozen model and the registered rule, as amended before collection (Amendment 1). Results are in [RESULTS.md](../RESULTS.md), generated from `data/interim/m4/literature_prereg_v3.json`.

**Implementation clarifications.** None of these changes a rule.
- Model medians use `seed_offset` equal to the preparation's index in the grid, as for the published profiles.
- When one LOTUS label names several Wikidata items, the item with the lowest QID is used, as in v2.
- "First number in the cell" is applied literally: a thousands separator such as `1,234.5` is not handled and reads as 1.

**Post-hoc notes** (not registered; basis `ai_post_hoc_audit_unverified`). Reported beside the registered result, never instead of it.
- One scored pair (PMC9504179) comes from columns for a second species in the same table (*Alnus glutinosa*), not the target plant.
- One article supplies most of the scored pairs, so pooled pair agreement differs from the registered per-article mean.
