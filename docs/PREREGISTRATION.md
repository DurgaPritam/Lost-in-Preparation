# Pre-registration: literature check of the preparation model (v1)

Registered: 2026-11-05, **before** the check was run. It is committed to the repository before any of its rows are collected, and the commit that adds this file is the registration. Any deviation from this plan will be listed under "Deviations" below, and reported with the results.

## Purpose

To test whether the preparation model (M4) predicts what published papers report teas, decoctions, essential oils and alcoholic extracts to contain. This check is separate from the earlier 9-row table, which is labelled **exploratory (selected after model build)** and is never pooled with this one.

## Model under test (frozen)

- Model version `prep-model:f4c4c5ef8a` (hash of `config/prep_model.toml`), descriptor `rdkit` (Crippen logP), 13-preparation grid in `pipeline/lip/m4/model.py`, at repository commit `52cdfa8`.
- No change to the model, its parameters or its thresholds between this registration and the run.

## Plants (6)

*Matricaria chamomilla* (chamomile), *Mentha × piperita* (peppermint), *Thymus vulgaris* (thyme), *Salvia rosmarinus* (rosemary), *Salvia officinalis* (sage), *Melissa officinalis* (lemon balm).

## Sources

- **Search.** PMC web search (`https://pmc.ncbi.nlm.nih.gov/search/?term=…`). The query per plant is `<common name> <Latin name> composition`. The results are taken from the first result page, in the order returned.
- **Article eligibility** (screened in result order):
  1. The article page states a Creative Commons licence.
  2. The article title names the plant (Latin or common name from the name list below).
  3. It is not one of the five PMCIDs used in the exploratory table (PMC2995283, PMC13074686, PMC7587570, PMC10217939, PMC11944828).

## Sentence rule (applied mechanically by `pipeline/lip/m4/prereg_literature.py`)

A sentence qualifies when **all** of these hold:

1. It names a compound from the compound list (synonyms listed).
2. It names exactly one preparation term from the preparation list.
3. It shows a presence cue (`main`, `major`, `predominant`, `principal`, `dominant`, `rich in`, `contain`, `identified`, `detected`, `found`, `%`, `mg`) or an absence cue (`not detected`, `absent`, `trace`, `low concentration`, `low amount`, `lacking`, `free of`, `did not contain`).
4. It mentions none of: `supercritical`, `CO2`, `fraction`, `partition`, `hexane`, `chloroform`, `ethyl acetate`, `commercial`, `synthetic`, `derivative`, `total phenolic`, `activity`, `inhibit`, `IC50`, `MIC`.

**Label:** an absence cue → `low`; otherwise → `present`.

**Rows:**
- One row per (plant, compound, preparation). The first qualifying sentence wins, in article order then sentence order.
- At most 3 rows per article and 6 per plant.
- Rows are taken round-robin over the plants, in the order listed, up to 30.
- If fewer than 30 qualify, the number found is reported. The rule is not relaxed.

### Compound list (PubChem name ← synonyms matched in text)

menthol · menthone · pulegone · carvone · limonene · 1,8-cineole ← eucalyptol, cineole · camphor · alpha-pinene ← α-pinene · borneol · thymol · carvacrol · p-cymene · gamma-terpinene ← γ-terpinene · linalool · geraniol · citral ← geranial, neral · citronellal · alpha-bisabolol ← α-bisabolol, bisabolol · chamazulene · beta-caryophyllene ← β-caryophyllene, caryophyllene · alpha-thujone ← α-thujone, thujone · rosmarinic acid · caffeic acid · chlorogenic acid · carnosic acid · carnosol · ursolic acid · apigenin · apigenin 7-glucoside ← apigenin-7-O-glucoside · luteolin · luteolin 7-glucoside ← luteolin-7-O-glucoside · eriocitrin · hesperidin · rutin · quercetin

### Preparation list → model preparation

| Terms in text | Model preparation |
|---|---|
| essential oil, hydrodistill*, steam distill* | distilled water |
| infusion, herbal tea, tea | hot water infusion (tea) |
| decoction | decoction in water |
| aqueous extract, water extract | hot water infusion (tea) |
| tincture, ethanolic extract, ethanol extract, hydroethanolic, hydroalcoholic | modern 70% ethanol extract |
| methanolic extract, methanol extract | modern methanol extract |

### Plant names (for the title test)

chamomile / Matricaria chamomilla / Matricaria recutita · peppermint / Mentha piperita / Mentha × piperita · thyme / Thymus vulgaris · rosemary / Salvia rosmarinus / Rosmarinus officinalis · sage / Salvia officinalis · lemon balm / Melissa officinalis

## Agreement rule and analysis

- **Agreement** (thresholds unchanged, `config/prep_model.toml [literature_check]`): `present` → predicted median ≥ 0.40; `low` → predicted median < 0.30.
- **Reported:**
  - the number of rows found;
  - the agreement rate with a Wilson 95% CI;
  - the agreement broken down by preparation type and by label.
- **Basis:** `ai_curated_literature_reference`, *provisional*. The rule and the code were written by an AI. It is reported separately from the exploratory set and is never presented as human-curated validation.

## Deviations

None so far.
