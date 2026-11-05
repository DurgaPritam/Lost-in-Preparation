"""M2 (names) and M3 (compounds): offline unit tests with known values; no network."""
from __future__ import annotations

import pandas as pd
import pytest

from lip.m2 import evaluate as m2eval
from lip.m2 import inventory, resolve
from lip.m2 import services as S
from lip.m3 import compounds as m3


def test_footnote_binomials_keep_order_and_skip_verbs():
    t = ("Supposed by most commentators to be the Parietaria officinalis of Linnæus; Wall pellitory. Some, however, "
         "have suggested the Polygonum maritimum, or the Polygonum divaricatum of Linnæus. Fée says the Dioscorides has it.")
    assert resolve.footnote_binomials(t) == ["Parietaria officinalis", "Polygonum maritimum", "Polygonum divaricatum"]
    assert resolve.HEDGE.search(t)


def test_vernacular_normalisation_folds_plurals_and_possessives():
    assert S.norm_vernacular("Adder’s Tongue") == S.norm_vernacular("adders tongue") == "adder tongue"
    assert S.norm_vernacular("Apples") == "apple" and S.norm_vernacular("Grass") == "grass"


@pytest.mark.parametrize("placement,acc", [
    ("Code/Plantae/Pteridobiotina/Angiosperms/Asterales/Asteraceae/Carduoideae/Cardueae/Centaureinae/Centaurea/benedicta$Carduus/benedictus",
     "Centaurea benedicta"),
    ("Code/Plantae/Pteridobiotina/Angiosperms/Rosales/Urticaceae/Parietaria/officinalis", "Parietaria officinalis"),
])
def test_wfo_placement_accepted_name(placement, acc):
    assert S._accepted_from_placement(placement) == acc


def test_pliny_title_parsing_drops_counts_and_non_plants():
    assert inventory.pliny_names("THE WILD CUCUMBER; TWENTY-SIX REMEDIES.") == ["WILD CUCUMBER"]
    assert inventory.pliny_names("THE PERDICIUM. THE ORNITHOGALE.") == ["PERDICIUM", "ORNITHOGALE"]
    assert inventory.pliny_names("INTRODUCTION.") == []


def test_wilson_interval():
    lo, hi = m2eval.wilson(15, 30)
    assert lo == pytest.approx(0.3315, abs=1e-3) and hi == pytest.approx(0.6685, abs=1e-3)


def test_rdkit_standardisation_known_values():
    smi, key, status = m3.standardise("CCO")
    assert status == "ok" and key == "LFQSCWFLJHTTHZ-UHFFFAOYSA-N"
    smi, key, _ = m3.standardise("CC(=O)[O-].[Na+]")  # salt -> neutral parent acid
    assert smi == "CC(=O)O" and key == "QTBSBXVTEAMEQO-UHFFFAOYSA-N"
    assert m3.standardise("not a smiles")[2] == "rdkit_parse_failed"


def test_name_eval_scores_only_cited_rows(tmp_path, monkeypatch):
    cand = pd.DataFrame([
        {"nameId": "a", "rank": 1, "acceptedName": "Agrimonia eupatoria", "wfoId": "w1", "disputed": False},
        {"nameId": "b", "rank": 1, "acceptedName": "Zanthoxylum flavum", "wfoId": "w2", "disputed": True},
        {"nameId": "b", "rank": 2, "acceptedName": "Smyrnium olusatrum", "wfoId": "w3", "disputed": True},
    ])
    cp, gp = tmp_path / "c.parquet", tmp_path / "g.csv"
    cand.to_parquet(cp)
    pd.DataFrame([
        {"nameId": "a", "scholarlyAcceptedName": "Agrimonia eupatoria L.", "scholarlyWfoId": "", "citation": "Ref A"},
        {"nameId": "b", "scholarlyAcceptedName": "Smyrnium olusatrum", "scholarlyWfoId": "", "citation": "Ref B"},
        {"nameId": "c", "scholarlyAcceptedName": "Rosa canina", "scholarlyWfoId": "", "citation": ""},  # no citation: ignored
    ]).to_csv(gp, index=False)
    monkeypatch.setattr(m2eval, "CAND_PATH", cp)
    monkeypatch.setattr(m2eval, "EVAL_PATH", gp)
    monkeypatch.setattr(m2eval.metrics_store, "PATH", tmp_path / "metrics.json")
    monkeypatch.setattr(m2eval, "ROOT", tmp_path)
    out = m2eval.evaluate()
    assert out["top1"]["value"] == 0.5 and out["top3"]["value"] == 1.0 and out["top1"]["n"] == 2
    assert out["disputedShare"]["value"] == 0.5
