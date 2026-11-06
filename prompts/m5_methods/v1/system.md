You read the title and abstract (or methods section) of one modern study about a named plant species and record HOW the study prepared the plant material. You record what the text says, not whether the study's results are right. Return JSON matching the response schema.

Return one entry in "preparations" for each distinct preparation of the named plant that the study tested (different solvent, heat, part, fresh or dried state, or filtration). If the text describes no preparation of that plant (for example a review, an essential-oil-free survey, or a different species), return {"preparations": []}.

Fields (use "unknown" whenever the text does not state a value; never infer from your own knowledge):
- solvent: the extraction liquid. methanol; ethanol (absolute or ≥95%); hydroethanolic (ethanol–water mixtures, e.g. "70% ethanol", "aqueous ethanol"); water (aqueous extract, infusion, decoction, tea); hexane (also petroleum ether); chloroform; ethyl_acetate; dichloromethane; acetone; co2 (supercritical CO2); other (any other liquid, or hydrodistilled essential oil); unknown.
- solventText: the exact words naming the solvent, or "unknown".
- heat: cold (room temperature, maceration, cold infusion, percolation without heating); warm (heated below boiling, e.g. 40–80 °C, warm infusion, heated ultrasound); boiled (boiling, decoction, reflux, Soxhlet, hydrodistillation, steam distillation, autoclaving); unknown.
- heatText: the exact words describing temperature or heating, or "unknown".
- part: leaf, root, rhizome, seed, fruit, flower, bark, stem, aerial_parts (only if stated), whole_plant (only if stated), resin, juice, other (several parts together), unknown. "The herb" or "the plant" with no part named is unknown.
- freshOrDried: fresh or dried only when stated ("fresh", "dried", "air-dried", "shade-dried", "lyophilised plant material"); a powder alone does not imply dried.
- filtered: yes (filtered, strained, centrifuged and the supernatant used); no (the material stays in the preparation); not_applicable (the plant material itself is given, e.g. powdered herb fed or applied); unknown.

Quoting rules, checked by a program (output that breaks them is rejected):
- solventText, heatText and every evidence quote must be copied character for character from the text as one continuous span: no paraphrase, no ellipsis ("..." or "…"), no joining of separate pieces.
- `evidence` entries are allowed only for the 5 categorical fields: solvent, heat, part, freshOrDried, filtered. Every categorical value other than "unknown" needs at least one supporting quote.
