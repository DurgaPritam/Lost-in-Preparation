# M5 AI-assisted check, prompt v1 (2026-11-07)

Basis: `ai_assisted_check`. Used by Claude agents (model `claude-opus-5-5`, Claude Code) to code the 40 hand-check studies
**blind to the rule-based extractor's output**. Output is never human validation and is stored apart from the human
hand-check sheet (`data/reference/m5_handcheck_v1.csv`, which stays empty for people).

---

You are coding how modern studies prepared plant material, as an independent check on a keyword-based extractor.
You see only the study texts below (title, and the abstract or the open-access methods excerpts that were retrieved).
Do not use any other source, prior knowledge of the paper, or assumptions about usual practice.

For each row in the row list, code four fields for that preparation. A row is one plant-material preparation of the
study. When a study has several rows, each row carries a `label` (the solvent wording that identifies it); code the
preparation that label refers to. When a study has one row, code the study's main extraction of the plant material.

Fields and the only allowed values:

- `solvent`: methanol, ethanol, hydroethanolic, hexane, chloroform, ethyl_acetate, dichloromethane, acetone, co2, water, other, unknown
  - hydroethanolic = ethanol with a stated water share (e.g. "70% ethanol", "hydroalcoholic", "ethanol/water"); a stated
    ethanol share of 95% or more is `ethanol`.
  - `other` = a solvent that is named but not in the list (e.g. butanol, petroleum ether, oil).
- `heat` (of the extraction step only; ignore drying, evaporation, concentration, storage, incubation):
  cold, warm, boiled, unknown
  - cold = no heat applied, room or ambient temperature, up to 30 °C;
  - warm = heat applied but not boiling, 31–94 °C, including infusion in hot or boiling water poured over the material;
  - boiled = 95 °C or more, decoction, boiling, reflux, Soxhlet, steam or hydro-distillation, Clevenger.
- `part`: leaf, root, rhizome, seed, fruit, flower, bark, stem, aerial_parts, whole_plant, resin, juice, other, unknown
  (the plant part that was extracted; if several parts are extracted together, use `other` and say so in the note)
- `freshOrDried`: fresh, dried, unknown (about the plant material before extraction, never the extract)

Rules:

1. A value other than `unknown` needs an **exact quote**: a short span copied character for character from the text
   (keep spacing and punctuation exactly; 3–150 characters), which states that value. The quotes are checked by a
   program against the text; a quote that is not an exact substring invalidates the value.
2. If the text does not state it, the value is `unknown` with an empty quote. Don't infer from the study type, the
   plant, or what is usual. "Extract" alone does not state a solvent; "dried extract" does not state dried material.
3. If the text states nothing about any preparation of plant material (e.g. a survey or a genetics paper), every field
   is `unknown` and the note says so.
4. Add a short `note` only when something is ambiguous (two candidate values, a mixture, unclear part).

Output: a JSON array, one object per row, in the row order given:
`{"pmid": "...", "preparation": 1, "solvent": "...", "solvent_quote": "...", "heat": "...", "heat_quote": "...",
"part": "...", "part_quote": "...", "freshOrDried": "...", "freshOrDried_quote": "...", "note": "..."}`
