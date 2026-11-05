# Annotator quickstart

You will label recipes in 50 historical passages. Two people do this **independently**. Afterwards one person adjudicates the two sets into the gold standard.

## Setup (2 minutes)

1. Open `annotation/index.html` in Chrome, Firefox or Safari. No server or install is needed.
2. Type your name in **Annotator**. Leave **Mode** on **Annotate**.
3. Click **Guidelines** and read them once (about 10 minutes). They are the same rules the extraction model follows.

**Do not** open **Review** mode or any file in `data/silver/` before you finish. They contain AI labels and would bias you.

## For each passage

1. Read the passage, the heading above it and the context line.
2. If there is **no** recipe (description, place, astrology, household use), tick **done — no recipe** and go to the next passage.
3. For each recipe:
   1. Click **+ recipe**.
   2. Select the shortest stretch of text that covers the preparation and the indication, then click **Recipe span**.
   3. Select the plant name, then click **Plant name**. If the passage only says "the herb", select the name in the heading. Do the same with **Indication**, plus **Heat text** and **Duration** if they appear.
   4. Select each named material and click **Ingredient**. Set its part, role and kind.
   5. Set each dropdown. For any value other than `unknown`, select the words that justify it, choose the field under **evidence for**, and click **Add**.
4. Start a **new recipe** when part, solvent, heat, process, form or filtration changes. The juice and the distilled water are two recipes.
5. When in doubt, choose `unknown`.
6. Fix any ⚠ warnings, then tick **done**.

## Time

Estimated **3–6 minutes per passage**. About a quarter of the passages have no recipe, and those take under a minute. Recipe-dense Culpeper passages can take 10 minutes. **Plan 3–4 hours for all 50**, in two or three sittings. This is an estimate, not a measurement; please note your real time in the passage notes.

Your work saves automatically in this browser. Use the same browser and the same name to resume.

## Export

Click **Export JSON**. You get `<your name>.json`. Put it in `data/gold/annotations/`. Both annotators' files go there; there must be exactly two.

## Adjudication (one person, after both are done)

- **Adjudicate** mode: load file A and file B. For each passage, click **start gold from A** or **start gold from B**, resolve the differences using the guidelines, then export. The output is `gold.json`.
- **Review** mode (optional, after adjudication or for spot checks only): shows a human file beside the AI reference file (`data/silver/silver_v1.json`). The AI labels are provisional and are not ground truth. A gold file exported from Review mode records that the AI reference was visible.

Then run `python -m lip m1 eval` to compute accuracy against the gold set and agreement between the two annotators.
