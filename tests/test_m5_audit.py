"""Phase 5 pairs and audit matching rules, and the Phase 6 preparation maps (protocol docs/AUDIT_PROTOCOL_v1.md)."""
from __future__ import annotations

import json

import pytest

from lip.m5 import audit as A
from lip.m5 import pairs as P
from lip.m5.rules import Prep
from lip.m6 import hypotheses as H


@pytest.mark.parametrize("name,queries,ok", [
    ("Wormwood", ["Wormwood"], True), ("common Wormwood", ["Wormwood"], True), ("Sea Wormwood", ["Wormwood"], False),
    ("Seriphium", ["Wormwood"], False), ("radish-seed", ["Cultivated Radish"], True), ("radishes", ["Cultivated Radish"], True),
    ("long radish", ["Cultivated Radish"], False), ("Leeks", ["Onions"], False), ("Onion", ["Onions"], True),
    ("Betony", ["Wood-Betony", "Wood Betony"], True), ("MEADOW SWEET", ["Meadow-sweet"], True), ("gourd", ["Colocynthis"], False),
])
def test_attribution_is_never_more_specific_than_the_entry(name, queries, ok):
    assert P.attributable(name, queries) is ok


def test_indication_lexicon_maps_historical_wording():
    assert set(P.map_indication("helpeth the yellow Jaundice")) == {"Jaundice"}
    assert "Fever" in P.map_indication("the Tertian or Quartan Agues")
    assert "Skin Ulcer" in P.map_indication("old sores, Cancers, and inveterate Ulcers")   # historical "cancers" are not Neoplasms
    assert "Neoplasms" not in P.map_indication("old sores, Cancers")
    assert P.map_indication("doth the same") == []                                         # back-references are not forced


def test_committed_pairs_have_verified_mesh_and_single_plant_recipes():
    d = json.loads(P.OUT.read_text())
    assert d["meshLookup"]["notFound"] == [] and d["counts"]["pairs"] == len(d["pairs"])
    recipes = {r["id"]: r for r in json.loads((P.INTERIM / "m1" / "predictions_approved.json").read_text())}
    for p in d["pairs"]:
        assert p["indication"]["meshId"].startswith("D")
        assert all(not recipes[r]["excludedFromHeadline"] for r in p["recipes"])


def _prep(**kw):
    p = Prep()
    for k, v in kw.items():
        setattr(p, k, v)
    return p


HIST_DECOCTION = A.parse_key("unknown|unknown|water|boiled|unknown")


def test_unknown_is_never_a_mismatch():
    m = A.compare(HIST_DECOCTION, _prep())
    assert set(m.values()) == {"unknown"} and A.study_status([m]) == "unknown"


def test_faithful_needs_solvent_and_heat_to_match():
    assert A.compare(HIST_DECOCTION, _prep(solvent="water", heat="boiled"))["overall"] == "match"
    assert A.compare(HIST_DECOCTION, _prep(solvent="water"))["overall"] == "unknown"   # heat unstated
    m = A.compare(HIST_DECOCTION, _prep(solvent="methanol", heat="unknown"))
    assert m["solvent"] == "mismatch" and m["overall"] == "mismatch"


def test_only_water_matches_a_modern_solvent():
    wine = A.parse_key("leaf|unknown|wine|boiled|unknown")
    assert A.compare(wine, _prep(solvent="hydroethanolic", heat="boiled"))["solvent"] == "mismatch"
    mixed = A.parse_key("unknown|unknown|honey+water|boiled|unknown")
    assert A.compare(mixed, _prep(solvent="water", heat="boiled"))["solvent"] == "mismatch"


def test_study_status():
    assert A.study_status([{"overall": "mismatch"}, {"overall": "match"}]) == "faithful"
    assert A.study_status([{"overall": "mismatch"}, {"overall": "mismatch"}]) == "not_faithful"
    assert A.study_status([{"overall": "mismatch"}, {"overall": "unknown"}]) == "unknown"


def test_phase6_preparation_maps():
    r = {"solvent": ["water"], "heat": "boiled", "process": "decoction", "part": "leaf"}
    assert H.hist_to_grid(r) == "decoction in water"
    assert H.hist_to_grid({**r, "process": "distillation"}) == "distilled water"
    assert H.hist_to_grid({**r, "solvent": ["wine", "honey"]}) is None              # mixed vehicles are not modelled
    assert H.hist_to_grid({"solvent": ["unknown"], "heat": "cold", "process": "unknown", "part": "juice"}) == "fresh juice"
    assert H.modern_to_grid({"solvent": "methanol", "heat": "unknown"}) == ("modern methanol extract", True)
    assert H.modern_to_grid({"solvent": "water", "heat": "unknown"}) == (None, False)   # water needs a stated heat
