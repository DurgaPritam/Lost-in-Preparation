"""Audit protocol v2: solvent equivalence classes, eligibility, per-variable status; logged M1 corrections."""
from __future__ import annotations

import json

import pytest

from lip.m1 import corrections as COR
from lip.m5 import audit as A
from lip.m5 import audit_v2 as V
from lip.m5 import rules as R

L2 = R.lexicon(V.LEX)


def rec(solvent, part="unknown", process="unknown"):
    return {"solvent": solvent, "part": part, "process": process}


@pytest.mark.parametrize("r,cls", [
    (rec(["water"]), "aqueous"), (rec(["vinegar"]), "acidified_aqueous"), (rec(["vinegar", "water"]), "acidified_aqueous"),
    (rec(["wine"]), "low_ethanol"), (rec(["wine", "water"]), "low_ethanol"), (rec(["oil"]), "oil"),
    (rec(["none"], part="juice"), "fresh_juice"), (rec(["none"], process="powder"), "powder"), (rec(["none"]), V.NA),
    (rec(["vinegar", "honey"]), V.NA), (rec(["water", "honey"]), V.NA), (rec(["other"]), V.NA), (rec(["unknown"]), "unknown"),
])
def test_historical_classes(r, cls):
    assert V.hist_class(r) == cls


def prep(text):
    ps = R.extract(text, L2)
    assert len(ps) == 1
    return ps[0]


def test_modern_classes_and_wine_cutoff():
    assert V.modern_class(prep("Leaves were extracted with 15% ethanol.")) == "low_ethanol"
    assert V.modern_class(prep("Leaves were extracted with 70% ethanol.")) == "high_ethanol"
    assert V.modern_class(prep("A hydroalcoholic extract of the leaves was prepared.")) == "hydroalcoholic_unstated"
    assert V.modern_class(prep("The roots were extracted in acidified water.")) == "acidified_aqueous"
    assert V.modern_class(prep("Fresh onion juice was administered orally.")) == "fresh_juice"
    assert V.modern_class(prep("Leaves were extracted with 22% ethanol."), wine_max=0.25) == "low_ethanol"


def test_no_analogue_is_never_unfaithful_and_unstated_strength_is_unknown():
    h = A.parse_key("unknown|unknown|honey+vinegar|unknown|unknown")
    m = V.compare(h, V.NA, prep("Leaves were extracted with methanol."))
    assert m["solvent"] == V.NA and m["overall"] == V.NA and V.unit_status([m["overall"]]) == V.NA
    w = A.parse_key("unknown|unknown|wine|boiled|unknown")
    assert V.compare(w, "low_ethanol", prep("A hydroalcoholic extract was prepared by reflux."))["solvent"] == "unknown"
    assert V.compare(w, "low_ethanol", prep("The leaves were boiled under reflux in 12% ethanol."))["overall"] == "match"


def test_unit_status():
    assert V.unit_status(["mismatch", "match"]) == "match"
    assert V.unit_status(["mismatch", V.NA]) == "mismatch"
    assert V.unit_status(["mismatch", "unknown"]) == "unknown"
    assert V.unit_status([V.NA, V.NA]) == V.NA


def test_eligibility_patterns():
    assert any(q.search("An ethnobotanical survey of 120 informants") for q in L2.survey)
    assert any(q.search("the methanolic extract of the leaves") for q in L2.plant_prep)
    assert not any(q.search("Glycyrrhizin attenuates liver injury in mice") for q in L2.plant_prep)   # pure compound


def test_v1_lexicon_is_unchanged_by_v2():
    assert R.lexicon().version == "m5_rules/v1:a058db8e4e"


def test_liquorice_corrections_are_logged_with_evidence_and_checked():
    t = COR.table()
    assert set(t.recipeId) >= {"pliny-nh:b22:c011:001#r01"} and (t.evidence != "").all() and (t.requestedBy == "project lead").all()
    recs = json.loads((COR.ROOT / "data" / "interim" / "m1" / "predictions_approved.json").read_text())
    out = {r["id"]: r for r in COR.apply(recs)}
    r = out["pliny-nh:b22:c011:001#r01"]
    assert (r["part"], r["solvent"], r["heat"], r["process"]) == ("root", ["water"], "boiled", "decoction") and len(r["corrections"]) == 5
    orig = {x["id"]: x for x in recs}["pliny-nh:b22:c011:001#r01"]
    assert orig["part"] == "juice" and "corrections" not in orig            # the extraction itself is never edited
    bad = [dict(orig, part="leaf")]
    with pytest.raises(ValueError, match="recorded old value"):
        COR.apply(bad)
