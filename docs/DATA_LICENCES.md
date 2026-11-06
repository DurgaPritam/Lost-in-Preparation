# Data licences

A source is ingested **only** when its status here is `confirmed`. Each status was checked by reading the catalogue record, TEI header or title page directly. Last checked: 2026-11-05.

## Historical texts — ingested

| Source id | Text | Copy | Licence | Evidence |
|---|---|---|---|---|
| `culpeper-1652` | Culpeper, *The English Physitian* | EEBO-TCP **A35365**: London, Peter Cole, 1652; Wing C7501; ESTC R24897; Huntington Library copy | **CC0 1.0** (EEBO-TCP Phase I) | TEI header `<availability>`, quoted below |
| `culpeper-1850` | Culpeper, *The Complete Herbal*, "A New Edition" | Project Gutenberg #49513: London, Thomas Kelly, 1850 | **Public domain in the USA** | Gutenberg catalogue rights field |
| `pliny-nh-bohn-v4` | Pliny, *Natural History*, tr. Bostock & Riley, vol. 4 (books XVIII–XXIII) | Project Gutenberg #61113: Bohn, 1856 | **Public domain in the USA** | Gutenberg catalogue rights field |
| `pliny-nh-bohn-v5` | Same work, vol. 5 (books XXIV–XXXI) | Project Gutenberg #60688: Bohn, title page 1856 | **Public domain in the USA** | Gutenberg catalogue rights field |

EEBO-TCP availability statement (A35365), verbatim:

> "This keyboarded and encoded edition of the work described above is co-owned by the institutions providing financial support to the Early English Books Online Text Creation Partnership. This Phase I text is available for reuse, according to the terms of Creative Commons 0 1.0 Universal. The text can be copied, modified, distributed and performed, even for commercial purposes, all without asking permission."

## Historical texts — checked, not used

| Text | Finding | Decision |
|---|---|---|
| Gerard, *Herball*, 1633 Johnson edition | EEBO-TCP **A01622** (STC 11751; ESTC S122165), CC0 1.0 (same Phase I statement). It is Johnson's "very much enlarged and amended" revision, largely based on Dodoens; the TEI has 13,883 `<gap>` markers. | Not used. The 1633 text is Johnson's, not Gerard's 1597 original. |
| Gerard, *Herball*, 1597 first edition (STC 11750) | No TCP transcription found in the Phase I mirror. The Michigan catalogue refused automated access (HTTP 403), so Phase II was not checked. | Not used. |
| Dioscorides, *De materia medica* (Wellmann Greek ed.) | Not checked. | Out of scope. |
| Dioscorides, Osbaldeston English translation (2000) | In copyright. | Never used. |

## Caveats

- **Gutenberg texts:** Project Gutenberg certifies US status only. The authors and translators died long ago (Culpeper 1654, Bostock 1846, Riley 1878), but the 1850 edition's later editors are unnamed. Worldwide status has not been independently verified.
- **The 1850 Culpeper is not the 1652 text.** It adds herbs and receipts by later editors. Its herbal entries carry a crosswalk status against 1652 (see [METHODS.md](../METHODS.md) §2).
- **Pliny:** the footnotes are Bostock & Riley's 19th-century commentary, not Pliny. The vol. 5 printer imprint suggests a later reprint of the 1856 edition; this is unverified.
- **Redistribution:** passages contain only the text between the Gutenberg START/END markers, without the Project Gutenberg header or licence. Re-check the PG licence on use of the PG name before releasing the dataset.

## Databases and services

| Service | Use | Licence / terms | Status |
|---|---|---|---|
| World Flora Online (WFO) Plant List, name-matching API | Accepted names, WFO IDs, synonymy | Taxonomic backbone: **CC0** (WFO FAQ, checked 2026-11-05). We cite WFO and the classification version, which is recorded in each cached response. | **used** (M2) |
| GBIF Backbone Taxonomy and species/occurrence APIs | Vernacular → species candidates, scientific-name matching, regional occurrence counts | Backbone: **CC BY 4.0**, doi:10.15468/39omei (GBIF dataset API, checked 2026-11-05); occurrence data carry per-dataset licences, but only counts are used | **used** (M2) |
| Wikidata (hosts LOTUS natural-product occurrences) | Compounds per taxon, structures, LOTUS references | CC0 | **used** (M3) |
| Kew POWO API | — | — | refused automated access (HTTP 403); not used |
| COCONUT 2.0 | Additional compound coverage | Curated dataset released under CC0 (official about page); contributing sources carry their own licences, so check them | licence permits use; **not integrated yet** (bulk dump required) |
| PubMed / PMC OA | Modern preparation methods (Phase 5 audit) and short quoted lines for the literature checks | Per-article licence, listed in the tables below. PubMed abstracts are publisher copyright in general, so only PMID, title, MeSH and a SHA-256 of the abstract are committed. | **used**: short attributed quotes only; abstract and article text stay in the git-ignored `data/cache/` |
| PubChem PUG REST | Structures (SMILES, InChIKey) for the literature-check compounds | NCBI public data | **used** (M4) |
| SangsterLogP dataset (Zenodo 19387552) | Experimental logP reference for validating the solvent descriptor | **CC BY 4.0** (Zenodo record, checked 2026-11-05); SHA-256 `a5f998a6…`. Attribution: see below | **used** (M4) |
| Wikipedia, *List of poisonous plants* (rev 1383132551) | Known-toxicity screen for M2's toxic-confusion check only (no longer used for the study-set column) | CC BY-SA 4.0; the page is tagged by its editors as needing expert review | **used** (screen only; not a safety rating) |
| European Medicines Agency (HMPC herbal monographs, public summaries, public statements) | Study-set toxicity entries (one quoted sentence per species) | Each PDF states: "Reproduction is authorised provided the source is acknowledged." (checked in every fetched document) | **used** (attributed short quotes) |
| Crossref REST API | Publication years of logP sources (training-overlap proxy) | Crossref metadata: CC0 | **used** (M4) |
| Lewis & Short, *A Latin Dictionary* (1879), PerseusDL lexica TEI | Drafted Pliny name identifications and the genus-signal audit (short quoted definitions; provisional) | **CC BY-SA 4.0** (repository licence) | **used** (provisional drafts) |
| English Wikipedia (article wikitext) | Drafted Culpeper name identifications (provisional) | CC BY-SA 4.0 | **used** (provisional drafts) |
| xtb 6.7.1 (Grimme group, conda-forge) | GFN2-xTB solvation free energies | LGPL-3.0 (software) | **used** (M4), installed locally in `.tools/` |

Every API response is cached with its request and retrieval time under `data/cache/`. Requests identify the project in the User-Agent, as Wikimedia's policy requires.

## Attribution

**SangsterLogP:** Cirino, T., Sangster, J., Charochkina, L., & Tetko, I. (2026). *SangsterLogP dataset* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.19387552. Licensed under CC BY 4.0. We use a 150-compound neutral subset (seed and selection rule in METHODS.md §9) and redistribute only derived values in `data/interim/m4/logp_validation.csv`; the original workbook is downloaded at run time and checksum-verified.

## PMC articles quoted

Articles licensed CC BY-NC or CC BY-NC-ND are used only for one short attributed sentence each, in a non-commercial research project, and are not redistributed.

Only short quotations (one sentence each) from openly licensed articles are stored; an article with no stated licence is paraphrased and cited instead, never quoted. Each row keeps the PMCID, the URL and a SHA-256 of the fetched page. The licence is as stated on each article page (checked 2026-11-05).

| PMCID | Used in | Licence stated on the page |
|---|---|---|
| PMC2995283 | exploratory literature table | **none stated** on the page (in PMC). **Not quoted:** the 3 rows carry our own paraphrase plus a full citation (Srivastava, Shankar & Gupta 2010, *Mol Med Rep* 3(6):895–901, doi:10.3892/mmr.2010.377), checked against the article by short anchor terms |
| PMC13074686 | exploratory | CC BY 4.0 |
| PMC7587570 | exploratory | CC BY 4.0 |
| PMC10217939 | exploratory | CC BY 4.0 |
| PMC11944828 | exploratory | CC BY 4.0 |
| PMC13290042 | pre-registered check | **CC BY-NC-ND 4.0** (short attributed quote only; not redistributed) |
| PMC6843575 | pre-registered | CC BY 4.0 |
| PMC9099978 | pre-registered | CC BY 4.0 |
| PMC10707927 | pre-registered | CC BY 4.0 |
| PMC10819686 | pre-registered | CC BY 4.0 |
| PMC5622382 | pre-registered | CC BY 4.0 |
| PMC8398316 | pre-registered | CC BY 4.0 |
| PMC12309076 | pre-registered | **CC BY-NC-ND 4.0** (short attributed excerpt only; not redistributed). On 2026-11-07 the excerpt was trimmed to the table caption and the one row the check matched (it had been the first 600 characters of the table). **That row is linalool acetate, not linalool**: the v1 rule matched the substring, so this row counted linalool as present. The pre-registered result is frozen and unchanged; the misread is reported here and in the Phase 9 report. |
| PMC10180401 | pre-registered | CC BY 4.0 |
| PMC11171837 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC11504252 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC11819889 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC11988581 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC12715987 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC13306179 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC13468080 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC13471599 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC5603879 | pre-registered v2 (water preparations) | CC BY 3.0 |
| PMC6696252 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC7587196 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC8073307 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC8124543 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC9027103 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC9032859 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC9966964 | pre-registered v2 (water preparations) | CC BY 4.0 |
| PMC12729493 | study-set toxicity (*Crocus sativus*) | CC BY 4.0 |
| PMC11085171 | study-set toxicity (*Ajuga chamaepitys*) | CC BY 4.0 |
| PMC4342611 | study-set toxicity (*Ranunculus ficaria*) | CC BY-NC 4.0 |
| PMC7956842 | study-set toxicity (*Hyssopus officinalis*) | CC BY 4.0 |
| PMC8010426 | study-set toxicity (*Pastinaca sativa*) | CC BY-NC 4.0 |
| PMC11267910 | study-set toxicity (*Galium aparine*) | CC BY 4.0 |
| PMC4224707 | study-set toxicity (*Hyoscyamus niger*) | CC BY 3.0 |
| PMC11012840 | study-set toxicity (*Raphanus sativus*) | CC BY 4.0 |
| PMC13075098 | study-set toxicity (*Salvia sclarea*) | CC BY 4.0 |
| PMC4665026 | study-set toxicity (*Euphorbia antiquorum*) | CC BY-NC 3.0 |
| PMC6513924 | study-set toxicity (*Papaver somniferum*) | CC BY-NC 4.0 |
| PMC9495094 | study-set toxicity (*Allium cepa*) | CC BY 4.0 |
| PMC9314633 | study-set toxicity (*Coriandrum sativum*) | CC BY 4.0 |
| PMC12522648 | study-set toxicity (*Citrullus colocynthis*) | CC BY-NC-ND 4.0 |
| PMC4890191 | study-set toxicity (*Cotinus coggygria*) | CC BY-NC-ND 4.0 |
| PMC8949886 | study-set toxicity (*Dioscorea communis*) | CC BY 4.0 |
| PMC11717056 | pre-registered v3 (paired tables; numeric values only, no text quoted) | CC BY 4.0 |
| PMC5578075 | pre-registered v3 (paired tables; numeric values only, no text quoted) | CC BY 4.0 |
| PMC8746171 | pre-registered v3 (paired tables; numeric values only, no text quoted) | CC BY 4.0 |
| PMC9000270 | pre-registered v3 (paired tables; numeric values only, no text quoted) | CC BY 4.0 |
| PMC9218236 | pre-registered v3 (paired tables; numeric values only, no text quoted) | CC BY-NC-ND 4.0 |
| PMC9504179 | pre-registered v3 (paired tables; numeric values only, no text quoted) | CC BY 4.0 |

## Audit methods snippets (Phase 5)

The site's Audit drawer, and `site-data/audit.json`, show one methods snippet per coded study:
- **Length:** 259 characters at most.
- **Content:** the open-access methods sentence that the solvent was coded from.
- **Attribution:** each snippet is shown with its PMID, and its PMCID is kept in `data/interim/m5/audit_studies.json`.
- **Eligibility:** a snippet is kept only for PMC open-access articles. Studies coded from a PubMed abstract get no snippet.
- **Abstract and article text:** never committed. They stay in the git-ignored `data/cache/m5_abstracts/` and `data/cache/m5_audit_text/`, and the committed records keep a SHA-256 of the text.

Licences come from the `license` field of Europe PMC, which gives no licence version. There are 34 articles:

| PMCID | PMID | Licence |
|---|---|---|
| PMC3472325 | 22958433 | CC BY |
| PMC3523417 | 23248676 | **CC BY-NC-SA** |
| PMC3559656 | 23382823 | CC BY |
| PMC3804841 | 24175050 | CC BY |
| PMC3851199 | 24283263 | CC BY |
| PMC4075712 | 25050284 | CC BY |
| PMC4075723 | 25050293 | CC BY |
| PMC5101707 | 27825341 | CC BY |
| PMC5111204 | 27846856 | CC BY |
| PMC5292954 | 28165501 | CC BY |
| PMC5412219 | 28480425 | **CC BY-NC-ND 4.0** (stated on the article page, checked 2026-11-06; Europe PMC gives no licence) |
| PMC5454855 | 28468251 | CC BY |
| PMC7690613 | 33105854 | CC BY |
| PMC7813598 | 33505935 | **CC BY-NC** |
| PMC8000521 | 33801280 | CC BY |
| PMC8614688 | 34829526 | CC BY |
| PMC8705906 | 34959999 | CC BY |
| PMC9265937 | 35804727 | CC BY |
| PMC9409487 | 36012505 | CC BY |
| PMC9504179 | 36145820 | CC BY |
| PMC9737327 | 36501112 | CC BY |
| PMC10229614 | 37253812 | CC BY |
| PMC10478434 | 37670294 | CC BY |
| PMC10743429 | 38139137 | CC BY |
| PMC10749724 | 38146392 | CC BY |
| PMC10927832 | 38347254 | CC BY |
| PMC10964079 | 37046199 | CC BY |
| PMC10974632 | 38543055 | CC BY |
| PMC11282636 | 39061083 | CC BY |
| PMC11354801 | 39201676 | CC BY |
| PMC11650409 | 39344827 | CC BY |
| PMC12472807 | 41011216 | CC BY |
| PMC12653370 | 41302134 | CC BY |
| PMC12933199 | 41756116 | CC BY |
