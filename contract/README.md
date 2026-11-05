# Data contract — v1.3

Frozen since v1.0 (2026-11-05); v1.1–v1.3 are additive or layout-only changes. The source of truth is [models.py](models.py); the JSON Schemas in [schemas/](schemas/) are generated from it with `python -m lip contract`. A test fails if a schema and the models drift apart. Any change from here on starts as a proposal in [CHANGELOG.md](CHANGELOG.md).

The contract files live in `site-data/`; profiles are split per species (v1.3). The pipeline exports them, and the web frontend validates every file against these schemas. Mock data for design work uses exactly these shapes, with `"mock": true` on every record.

| File | Shape | One record per | Schema |
|---|---|---|---|
| `sources.json` | array | digitised source (volume or edition); `workId` groups the volumes of one work | [sources.schema.json](schemas/sources.schema.json) |
| `recipes.json` | array | extracted recipe | [recipes.schema.json](schemas/recipes.schema.json) |
| `species.json` | array | species candidate for a recipe | [species.schema.json](schemas/species.schema.json) |
| `profiles/index.json` | array | species with a profile file (loaded first by the site) | [profiles.index.schema.json](schemas/profiles.index.schema.json) |
| `profiles/<speciesId>.json` | array | preparation profile of one species (loaded on demand) | [profiles.species.schema.json](schemas/profiles.species.schema.json) |
| `audit.json` | array | plant–use pair | [audit.schema.json](schemas/audit.schema.json) |
| `hypotheses.json` | array | ranked lead | [hypotheses.schema.json](schemas/hypotheses.schema.json) |
| `metrics.json` | object | whole project | [metrics.schema.json](schemas/metrics.schema.json) |

## Shared enumerations

| Enum | Values |
|---|---|
| `solvent` (historical, a **list**) | water, wine, vinegar, oil, honey, none, other, unknown |
| `modernSolvent` (studies) | methanol, ethanol, hydroethanolic, hexane, chloroform, ethyl_acetate, dichloromethane, acetone, co2, water, other, unknown |
| `heat` | cold (no applied heat), warm, boiled, unknown |
| `filtered` | yes, no, not_applicable, unknown |
| `process` | infusion, decoction, maceration, distillation, expression, powder, other, unknown |
| `part` | leaf, root, rhizome, seed, fruit, flower, bark, stem, aerial_parts, whole_plant, resin, juice, other, unknown |
| `freshOrDried` | fresh, dried, unknown |
| `form` | drink, poultice, ointment, plaster, gargle, inhalation, other, unknown |
| `recipeType` | single_plant, compound, unknown |
| `species.basis` | scholarly, database, model, commentary_19c |
| `metric.status` | computed, not_computed |

## Key rules

- **`preparationKey`** = `part|freshOrDried|solvent|heat|filtered`. Multiple solvents are sorted and joined with `+`. Example: `leaf|dried|vinegar+wine|boiled|yes`.
- **`speciesId`** = the WFO ID. It is `null` when a name is unresolved.
- **Evidence:** every non-`unknown` recipe field has verbatim quotes in `evidence[field]`, with offsets into `passage.text`. `evidence.recipe` is the whole recipe span. A plant name taken from the entry heading is a quote with `inHeading: true`.
- **Compound recipes** (`recipeType != single_plant`) have `excludedFromHeadline: true`. They are stored, but left out of the core M4–M6 analysis and the headline numbers.
- **Metrics** are never placeholders. An absent metric has `status: "not_computed"` and a `note` saying why. A computed metric has a `sourceFile`.
- **Extraction provenance** (v1.1): every recipe records the provider, model, model digest, decoding settings and prompt version.
- **`commentary_19c`** species candidates (from Bostock & Riley's Pliny footnotes) are candidates only, never ground truth.
