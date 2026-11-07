"""Where a human reviewer should start: the 10 sample passages most likely to hold extraction errors.

Basis "ai_assisted_check". The reasons below were written by an AI agent (Claude, claude-opus-5-5, Claude Code,
2026-11-07) after reading each passage and the session extraction. This is NOT an evaluation: the extraction is never
compared with the silver set here (the same AI wrote both, so the comparison would be circular), and no field is
marked right or wrong. It only orders the human review. Counts and list positions are computed from the files.

No sampled passage contains an illegible-gap marker: the sampling frame excludes them (METHODS §4), so that signal
does not apply to this sample.

Writes data/reference/m1_review_priority_v1.csv.
"""
import csv
import json
import subprocess

from ..paths import INTERIM, ROOT

OUT = ROOT / "data" / "reference" / "m1_review_priority_v1.csv"
BASIS = "ai_assisted_check"

# (passageId, signals, reason): AI-written judgement, in priority order.
REASONS = [
    ("culpeper-1652:herbal:pellitory-of-the-wall:009", "compound recipes; ambiguous solvent; unclear referent",
     "The poultice 'boyled in Wine ... and some Oyl put thereto' is recorded with a wine + oil solvent, although the oil is added after "
     "boiling. 'Oyl of Roses' in the liniment is itself a rose preparation, recorded only as the solvent oil. 'being mixed with Goats "
     "Tallow' refers back to 'the said Oyntment, or the Herb', so what is mixed is unclear."),
    ("culpeper-1652:herbal:sanicle:008", "ambiguous solvent (alternatives); recipe boundaries",
     "'boyled in Wine or Water' is recorded as one recipe with a wine + water mixture, though 'or' gives two alternatives (likely two "
     "recipes). A run of alternatives ('the Decoction or Juyce ... or the Pouder in drink, and the Juyce used outwardly') is split into "
     "four recipes sharing one indication, and 'gargling or washing' into two near-identical recipes."),
    ("culpeper-1652:herbal:sorrel:003", "possible missed recipe; disputed name",
     "The closing 'The Distilled water of the Herb is of much good use for all the purposes aforesaid' has no recipe. Its indication is "
     "only by reference, so it is either a miss or a justified exclusion. The name is disputed. 'roasted under the Embers' is coded "
     "heat 'warm', and roasting fits the heat categories poorly."),
    ("pliny-nh:b20:c013:003", "ambiguous solvents; translation",
     "'Taken with vinegar or honey' is recorded as a vinegar + honey mixture, though these are alternatives. 'a decoction ... boiled down "
     "to one-third, taken in wine' is recorded with the solvent wine, although the decoction's liquid is unstated and wine is what it is "
     "taken in. 'boiled in earth and water' lists earth as an ingredient; the translation's sense is unclear."),
    ("pliny-nh:b24:c080:002", "unclear plant name; unclear referents",
     "Four names for one plant (chamædrys, trixago, chamædrops, teucria), and the identification is disputed. 'a wine too is prepared from "
     "it' leaves the process open. In 'taken also, in vinegar', whether the juice or the plant is meant is unclear. 'sprigs' is not "
     "mapped to a part."),
    ("culpeper-1850:dispensatory:s009-herbs-and-their-leaves:070", "two plants under one name; cross-reference; ambiguous solvent",
     "'Centaury the greater and less' are two different plants under one name. 'will do wonders in curing wounds: see the root' is a "
     "cross-reference, yet it is recorded as a recipe. 'boiled in posset-drink' (milk curdled with wine or ale) is coded solvent "
     "'other', which is ambiguous."),
    ("pliny-nh:b22:c071:001", "unclear plant name; ambiguous solvent",
     "Disputed identification: the translation calls the plant 'a species of wild lentil', while the chapter title says salvia. In "
     "'employed with wine ... a decoction of it', whether the decoction is made in wine is unclear (recorded as solvent unknown). The "
     "wormwood co-ingredient is 'taken in drink' with no vehicle named."),
    ("culpeper-1850:dispensatory:s045-species-or-powders:099", "possible missed recipe (indication by reference)",
     "The passage gives a preparation (powders beaten separately, then mixed; 'a dram of it taken in Muskadel'), but its only indication "
     "is 'the infirmities specified in the title'. The extraction records no recipe. A reviewer should decide whether an indication by "
     "reference counts. This passage is also in the 15-passage re-annotation subset."),
    ("culpeper-1652:herbal:cudweed-or-cottonweed:009", "several species under one name; ambiguous solvent",
     "'The Plants are all astringent' covers several species under one disputed name. 'The juyce ... taken in Wine and Milk' is recorded "
     "as wine + other, with milk coded 'other'. The Tenasmus use ('being either drunk or injected') leaves the form open."),
    ("pliny-nh:b24:c056:001", "unclear plant name; parts; vehicle mapping",
     "Three names for one plant (erythrodanus, ereuthodanus, rubia), and the identification is disputed. 'employed with hydromel' is "
     "coded water + honey, a mapping convention a reviewer should confirm. 'The root of it and the seed' and 'The branches, together "
     "with the leaves' are coded part 'other'. An amulet use is recorded as a recipe."),
]


def run() -> dict:
    pred = json.loads((INTERIM / "m1" / "predictions_sample.json").read_text())
    passages = json.loads(subprocess.check_output(
        ["node", "-e", "global.window={};require('./annotation/data.js');"
         "console.log(JSON.stringify(window.LIP.sample.passages.map(p=>({id:p.passageId,stratum:p.stratum,heading:p.heading}))))"],
        cwd=ROOT))
    pos = {p["id"]: (i + 1, p) for i, p in enumerate(passages)}
    subset = set(json.loads((ROOT / "data" / "gold" / "reannotation_subset_v1.json").read_text())["passageIds"])
    rows = []
    for rank, (pid, signals, reason) in enumerate(REASONS, 1):
        if pid not in pos:
            raise SystemExit(f"{pid} is not in the annotation sample")
        i, p = pos[pid]
        rows.append({"rank": rank, "passageId": pid, "annotationListPosition": i, "stratum": p["stratum"], "heading": p["heading"],
                     "recipesExtracted": sum(r["passage"]["passageId"] == pid for r in pred),
                     "inReannotationSubset": pid in subset, "signals": signals, "reason": reason, "basis": BASIS,
                     "writtenBy": "AI agent (Claude, claude-opus-5-5, Claude Code), 2026-11-07; not an evaluation"})
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return {"passages": len(rows), "out": str(OUT.relative_to(ROOT))}
