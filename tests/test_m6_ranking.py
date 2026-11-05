"""M6 ranking rule: only gaps that hold across the uncertainty range can drive a rank."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from contract import models as C
from lip.m4 import chem
from lip.m4 import model as M
from lip.m6 import ranking as R

SMILES = ["CC(C)C1CCC(C)CC1O", "OC(=O)/C=C/c1ccc(O)c(O)c1", "CC1=CCC(CC1)C(C)=C", "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O",
          "Cc1ccc(C(C)C)c(O)c1", "CCCCCCCCCCCCCCCC(=O)O", "O=C(O)c1cc(O)c(O)c(O)c1", "CC(=O)OC1CC2CCC1(C)C2(C)C"]


def _compounds():
    out = []
    for i, s in enumerate(SMILES):
        d = chem.describe(s)
        out.append(M.Compound(f"K{i}", d["logP"], d["basicN"], d["heatFlags"], d["volatile"], d["mw"]))
    return out


def _draws():
    return R.Draws(M.load_config(), M.descriptor_sd("rdkit")["sd"])


def test_same_preparation_has_no_gap_and_coupling_holds():
    d = _draws()
    s = R.score(R.Candidate("w", "X", "modern methanol extract", "modern methanol extract"), _compounds(), d)
    assert s["gapP95"] < 1e-9  # identical draws on both sides: coupled descriptor error, same seeds


def test_wide_compounds_are_excluded_and_counted():
    d = _draws()
    cs = _compounds()
    s = R.score(R.Candidate("w", "X", "cold water infusion", "modern methanol extract"), cs, d)
    wide = sum(1 for c in cs for p in ("cold water infusion", "modern methanol extract")
               if (lambda e: e["high"] - e["low"] > R.WIDTH_MAX)(d.get(c, p)[0]))
    assert s["compoundsUsed"] + s["compoundsExcludedWide"] == len(cs)
    assert (s["compoundsExcludedWide"] > 0) == (wide > 0)


def test_too_few_usable_compounds_are_not_ranked():
    s = R.score(R.Candidate("w", "X", "cold water infusion", "modern methanol extract"), _compounds()[:2], _draws())
    assert s["notRanked"] and s["gapP5"] is None
    r = R.rank(pd.DataFrame([s]))
    assert pd.isna(r.iloc[0]["rank"])


def test_rank_uses_lower_bound_not_median():
    rows = pd.DataFrame([
        {"acceptedName": "A", "faithful": "f", "modern": "m", "gapP5": 0.05, "gapP50": 0.60, "gapP95": 0.95, "pGapAboveTau": 0.7,
         "gapMedianOfMedians": 0.60, "notRanked": ""},   # large but uncertain gap
        {"acceptedName": "B", "faithful": "f", "modern": "m", "gapP5": 0.30, "gapP50": 0.35, "gapP95": 0.40, "pGapAboveTau": 1.0,
         "gapMedianOfMedians": 0.35, "notRanked": ""},   # smaller gap that holds across the range
    ])
    r = R.rank(rows).set_index("acceptedName")
    assert r.loc["B", "rank"] == 1 and r.loc["A", "rankMedianGap"] == 1


def test_contract_fields():
    row = {"gapP50": 0.5, "gapP5": 0.3, "gapP95": 0.7, "pGapAboveTau": 0.9, "compoundsUsed": 10, "compoundsExcludedWide": 2, "rankMedianGap": 3}
    gap, gr = R.to_contract(row)
    assert isinstance(gap, C.Interval) and gap.low == 0.3 and isinstance(gr, C.GapRanking) and gr.gapP5 == 0.3


def test_recorded_stability_and_labels():
    o = json.load(open("data/interim/m6/ranking_stability.json"))
    assert "NOT hypotheses" in o["label"] and o["modelVersion"] == M.config_version(M.load_config())
    rob = o["stability"]["robust (5th percentile of gap)"]
    assert rob["monteCarloReseed"]["top20Overlap"] >= 0.8 and rob["compoundBootstrap"]["top20OverlapMean"] >= 0.8
    ss = pd.read_csv("data/interim/m3/study_set_proposal.csv")
    demo = pd.read_csv("data/interim/m6/ranking_demo.csv")
    assert set(demo.acceptedName) == set(ss[ss.proposed].acceptedName)
