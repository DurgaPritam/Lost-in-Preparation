"""Liquorice case study: an extraction misclassification, the corpus evidence that corrected it, and how the hypothesis
changed. Every number is computed here from pipeline outputs: M6 (audit v1) is run with and without the logged
corrections (config/m1_corrections.csv). Output: data/interim/m6/liquorice_case.json.
"""
from __future__ import annotations

import json

import pandas as pd

from ..m1.corrections import table
from ..m1.prompt import load_passages
from ..paths import INTERIM
from . import hypotheses as H

OUT = INTERIM / "m6" / "liquorice_case.json"
RECIPE = "pliny-nh:b22:c011:001#r01"
EVIDENCE_PASSAGES = ["pliny-nh-bohn-v4:fn2511", "culpeper-1850:dispensatory:s040-rob-or-sapa-and-juices:026",
                     "culpeper-1850:dispensatory:s040-rob-or-sapa-and-juices:027"]


def run() -> dict:
    tmp = INTERIM / "m6" / "uncorrected_v1"
    before = H.run("v1", corrections=False, out_override=tmp)
    after = json.loads((INTERIM / "m6" / "hypotheses_summary.json").read_text())
    b = pd.read_csv(tmp / "hypotheses.csv")
    a = pd.read_csv(INTERIM / "m6" / "hypotheses.csv")
    pick = lambda d: d[(d.acceptedName == "Glycyrrhiza glabra") & (d.mesh == "Liver Diseases")].iloc[0]
    rb, ra = pick(b), pick(a)
    rec = {r["id"]: r for r in json.loads((INTERIM / "m1" / "predictions_approved.json").read_text())}[RECIPE]
    pas = load_passages().set_index("passage_id")
    t = table()
    out = {
        "species": "Glycyrrhiza glabra", "indication": "Liver Diseases", "recipeId": RECIPE,
        "recipeQuote": rec["evidence"]["recipe"][0]["quote"],
        "extractedAs": {k: rec[k] for k in ("part", "solvent", "heat", "process", "filtered")},
        "correctedTo": {c["field"]: c["to"] for c in t[t.recipeId == RECIPE].to_dict("records")},
        "evidence": [{"passageId": p, "text": pas.loc[p, "text_clean"]} for p in EVIDENCE_PASSAGES],
        "otherLiquoriceRecipesCorrected": sorted(set(t.recipeId) - {RECIPE}),
        "before": {"faithful": rb.faithful, "modern": rb.modern, "rank": int(rb["rank"]), "gapP5": rb.gapP5, "gapP50": rb.gapP50,
                   "gapP95": rb.gapP95, "rankedOf": int(before["ranked"])},
        "after": {"faithful": ra.faithful, "modern": ra.modern, "rank": int(ra["rank"]), "gapP5": ra.gapP5, "gapP50": ra.gapP50,
                  "gapP95": ra.gapP95, "rankedOf": int(after["ranked"])},
        "label": "case study of an extraction correction; the hypothesis is worth re-testing, not a claim that liquorice works or is safe",
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out
