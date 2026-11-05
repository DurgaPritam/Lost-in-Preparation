# Recipe annotation guidelines — v1

These rules apply to human annotators and to the extraction model alike. You record **what the historical text says**, not whether it works or is safe. When you are unsure about a value, write `unknown`.

## 1. What counts as a recipe

A **recipe** is a statement in the passage that one or more named materials (usually a plant or part of a plant) are, or should be, used for a health indication, internal or external, in people or animals.

- **Include** uses that give no preparation details ("Borage flowers strengthen the brain"). Their preparation fields are all `unknown`.
- **Include** amulets and other non-chemical uses that name an indication ("being tied about the neck … for the vertigo").
- **Include** uses as an antidote ("the remedy to help those that have taken Henbane is to drink goat's milk").
- **Exclude** botanical description, habitat, flowering time, astrology with no use, and household or culinary uses with no health indication (keeping moths from clothes, keeping birds from grapes).
- **Exclude** the editor's commentary and cross-references.

## 2. One recipe per distinct preparation

- Start a **new recipe** whenever part, solvent, heat, process, form or filtration changes. "The juice or the distilled water being drunk" is two recipes: one by expression, one by distillation.
- When one preparation serves **several indications**, it is still **one recipe**. Its indication span covers the list.
- Indications stated with **no preparation** at all become **one recipe per plant**, with every preparation field `unknown`.
- If the same preparation is mentioned twice, record **one** recipe.

## 3. Quotes (spans)

Every value other than `unknown` must be supported by text you can point to.

- **Recipe span:** the shortest contiguous stretch of the passage that covers the preparation and the indication. It is used to match recipes between annotators and the model.
- **Free-text fields** (`plantNameAsWritten`, `heatText`, `durationText`, `indicationAsWritten`, ingredient names) are copied **exactly** from the passage: one contiguous span, no ellipses, no edits, original spelling.
- If the plant is named only in the **entry heading** (the passage says "the herb" or "it"), copy the name from the heading.
- **Enum fields:** quote the words that justify the value.

## 4. Fields

| Field | Values and rules |
|---|---|
| `recipeType` | **single_plant**: exactly one ingredient besides the vehicle. Wine, water, vinegar, oil and honey used as vehicles are not ingredients. **compound**: two or more ingredients besides the vehicle, or the text says the material is mixed with other things ("in many compound balms"). Otherwise **unknown**. |
| `ingredients` | Each named material other than the vehicle. Give the name as written and the part. **role**: `principal` for the plant the entry or sentence is about, `co_ingredient` for everything else. **kind**: `plant`, `animal`, `mineral`, `other` or `unknown`. |
| `plantNameAsWritten` | The principal plant, verbatim. |
| `part` | `leaf`, `root`, `rhizome`, `seed`, `fruit` (includes berries), `flower`, `bark`, `stem` (includes wood and stalks), `aerial_parts` (only if the text says so explicitly), `whole_plant` (only if explicit), `resin` (gums, tears, rosins), `juice` (when the material is the plant's juice), `other` (several parts together, such as "the wood and leaves", or anything else). **"The herb" with no part named is `unknown`.** |
| `freshOrDried` | Only when stated: "green" or "fresh" → `fresh`; "dried" or "dry" → `dried`. A powder alone does **not** imply `dried`. |
| `solvent` (list) | The liquid vehicles the material is prepared in or taken with. `water` (includes the plant's own distilled water); `wine` (white or red wine, sack, claret); `vinegar`; `oil`; `honey`; `none` (explicitly taken or applied without a vehicle: fresh juice drunk, powder strewn, leaves applied, worn, smelled); `other` (milk, ale, beer, broth, rose-water, another plant's distilled water, hog's grease); `unknown`. Oxymel → `[vinegar, honey]`. |
| `heat` | `cold`: a preparation whose wording involves no heating (juice, fresh herb bruised and applied, powder, steeped cold). `warm`: warmed, infused hot, "over a gentle fire", applied warm. `boiled`: boiled, decoction, seethed, distilled. Otherwise `unknown`. |
| `heatText` | The words describing heat, verbatim ("over a gentle fire"); otherwise `unknown`. |
| `durationText` | The verbatim duration of a preparation step ("twelve hours", "till a third part be consumed"). How often to take it ("every morning") is **not** a duration. Otherwise `unknown`. |
| `filtered` | `yes`: strained, pressed out (of a liquid), clarified. `no`: a liquid taken or applied with the plant material still in it (a powder in a drink). `not_applicable`: ointments, plasters, poultices, balms, fumes, amulets. Otherwise `unknown`. |
| `process` | `infusion` (steeped in liquid, hot or cold, without boiling); `decoction` (boiled in liquid); `maceration` (steeped for a long time, for example oil set in the sun); `distillation`; `expression` (juice pressed out); `powder`; `other` (burned for fumes, bruised and applied, conserve, syrup, electuary); `unknown`. |
| `form` | `drink` (any liquid taken by mouth); `poultice` (bruised herb or cataplasm applied); `ointment` (ointment, salve, balm, oil applied to the body); `plaster`; `gargle` (includes mouthwash); `inhalation` (smoke, fume, smell, snuff); `other` (bath, fomentation, clyster, pessary, amulet, eaten as food, pills, conserve, electuary); `unknown`. |
| `indicationAsWritten` | A verbatim span naming the condition(s) or effect(s). If there are several, use the contiguous span that covers them. Otherwise `unknown`. |

## 5. Unknown policy

When the text does not state a value, or two readings are equally possible, the value is `unknown`. A missing value is better than a guessed one.

## 6. Adjudication (human gold set only)

The adjudicator resolves each disagreement between the two annotators using these guidelines, not their own reading. Any guideline gap they find goes into the notes and into the error analysis.
