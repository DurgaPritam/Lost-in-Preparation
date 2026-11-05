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
| World Flora Online (WFO) Plant List, name-matching API | Accepted names, WFO IDs | CC BY 4.0, attribution required | see Phase 3 notes |
| Kew POWO API | — | — | refused automated access (HTTP 403); not used |
| GBIF species API | Vernacular → scientific name candidates | GBIF data licences per dataset (CC0 / CC BY) | see Phase 3 notes |
| Wikidata (hosts LOTUS natural-product occurrences) | Compounds per taxon, with references | CC0 | see Phase 3 notes |
| COCONUT | Additional compound coverage | to be confirmed | see Phase 3 notes |
| PubMed / PMC OA | Modern preparation methods | abstracts for mining; per-article licence for full text | later phase |
