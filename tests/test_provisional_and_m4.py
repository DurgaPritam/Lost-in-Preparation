"""Silver/provisional separation, AI drafts, and the preparation model (M4)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from contract import models as C
from lip.m1 import evaluate as ev
from lip.m1 import silver
from lip.m4 import chem
from lip.m4 import model as M

ART = "C[C@@H]1CC[C@H]2[C@H](C(=O)O[C@H]3[C@@]24[C@H]1CC[C@](O3)(OO4)C)C"


# --- silver -------------------------------------------------------------------------------

def test_silver_builds_with_all_quotes_verbatim():
    out = silver.build()  # raises SilverError on any non-verbatim quote
    assert out["passages"] == 50 and out["recipes"] > 100
    data = json.loads(silver.OUT.read_text())
    assert data["basis"] == "silver_ai_reference" and "not human" in data["label"].lower()
    for pid, p in data["passages"].items():
        for r in p["recipes"]:
            assert r["basis"] == "silver_ai_reference"
            span = r["recipeSpan"]
            text = next(x["text"] for x in json.loads(ev.SAMPLE_PATH.read_text())["passages"] if x["passageId"] == pid)
            assert text[span["start"]:span["end"]] == span["quote"]


def test_silver_never_written_to_gold_fields(monkeypatch, tmp_path):
    sp = [{"passageId": "p0", "stratum": "pliny"}]
    (tmp_path / "s.json").write_text(json.dumps({"passages": sp}))
    sil = {"basis": "silver_ai_reference", "passages": {"p0": {"done": True, "recipes": [
        {"recipeSpan": {"quote": "x", "start": 0, "end": 5}, "part": "root", "solvent": ["wine"]}]}}}
    (tmp_path / "silver.json").write_text(json.dumps(sil))
    pred = [{"passage": {"passageId": "p0"}, "part": "root", "solvent": ["wine"],
             "evidence": {"recipe": [{"quote": "x", "start": 0, "end": 5}]}}]
    (tmp_path / "pred.json").write_text(json.dumps(pred))
    for k, v in {"SAMPLE_PATH": tmp_path / "s.json", "SILVER_PATH": tmp_path / "silver.json", "PRED_PATH": tmp_path / "pred.json",
                 "RUN_PATH": tmp_path / "run.json", "DETAIL_PATH": tmp_path / "d.json", "TALLY_PATH": tmp_path / "t.json",
                 "SITE_DATA": tmp_path / "site", "GOLD_PATH": tmp_path / "nogold.json", "ANN_DIR": tmp_path / "ann"}.items():
        monkeypatch.setattr(ev, k, v)
    m = ev.evaluate("silver")
    sec = m.provisional["extractionVsSilver"]
    assert sec.basis == "silver_ai_reference" and "not human-validated" in sec.label
    assert sec.extraction.overall["part"].f1.value == 1.0
    assert m.extraction.overall == {} or m.extraction.overall["part"].f1.status == "not_computed"


def test_annotation_tool_does_not_ship_silver():
    assert "silver" not in open("annotation/data.js").read()
    html = open("annotation/index.html").read()
    assert 'value="review"' in html and "NOT human-validated" in html


# --- AI drafts ------------------------------------------------------------------------------

def test_drafts_are_separate_and_unverified():
    d = pd.read_csv("data/gold/name_identifications.csv", dtype=str).fillna("")
    assert set(d.draftBasis) == {"ai_drafted_unverified"} and (d.verified_by == "").all()
    assert (d.scholarlyAcceptedName == "").all() and (d.citation == "").all()  # human columns untouched
    drafted = d[d.draftAcceptedName != ""]
    assert len(drafted) >= 10 and (drafted.draftQuote != "").all() and (drafted.draftSourceUrl != "").all()
    assert not drafted.draftSource.str.contains("Bostock", case=False).any()


# --- chemistry flags --------------------------------------------------------------------------

def test_flags_known_values():
    a = chem.describe(ART)
    assert a["heatFlags"] == ["heat:endoperoxide"] and not a["basicN"] and not a["volatile"]
    nicotine = chem.describe("CN1CCC[C@H]1c1cccnc1")
    assert nicotine["basicN"] and nicotine["class"] == "alkaloid-like"
    assert chem.describe("CC(C)C1CCC(C)CC1O")["volatile"]           # menthol
    assert not chem.describe("CC(=O)Nc1ccc(O)cc1")["basicN"]         # paracetamol: amide N is not basic
    sinigrin = "C=CC/C(=N/OS(=O)(=O)O)S[C@H]1O[C@H](CO)[C@@H](O)[C@H](O)[C@H]1O"
    assert "heat:glucosinolate" in chem.describe(sinigrin)["heatFlags"]


# --- model properties -------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cfg():
    return M.load_config()


def _c(smiles, h=None):
    d = chem.describe(smiles)
    return M.Compound("X", d["logP"] if h is None else h, d["basicN"], d["heatFlags"], d["volatile"], d["mw"])


def test_heat_lowers_heat_labile_only(cfg):
    art = _c(ART)
    cold, boiled = (M.simulate(art, M.BY_LABEL[l], cfg)["likelihood"] for l in ("cold water infusion", "decoction in water"))
    assert boiled < cold * 0.5
    glc = _c("OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O")  # glucose: no alert
    g = [M.simulate(glc, M.BY_LABEL[l], cfg)["drivers"]["heat"] for l in ("cold water infusion", "decoction in water")]
    assert g == [1.0, 1.0]


def test_vinegar_raises_basic_alkaloid_only(cfg):
    for smi, should_rise in (("CN1CCC[C@H]1c1ccccc1", True), ("CCCCCCCC(=O)C", False)):
        c = _c(smi, h=2.5)
        v = M.simulate(c, M.BY_LABEL["steeped in vinegar"], cfg)
        w = M.simulate(c, M.BY_LABEL["cold water infusion"], cfg)
        assert (v["likelihood"] > w["likelihood"] + 0.1) == should_rise
        assert (v["drivers"]["acidity"] > 1.0) == should_rise


def test_filtration_and_powder(cfg):
    c = _c("CCCCCCCCCCCCCCCC(=O)O")  # palmitic acid, lipophilic
    juice = M.simulate(c, M.BY_LABEL["fresh juice"], cfg)  # unfiltered aqueous
    assert juice["drivers"]["filtration"] > 1.0
    powder = M.simulate(c, M.BY_LABEL["powder taken whole"], cfg)
    assert powder["likelihood"] == 1.0
    oil = M.simulate(c, M.BY_LABEL["infused oil"], cfg)
    water = M.simulate(c, M.BY_LABEL["cold water infusion"], cfg)
    assert oil["likelihood"] > 0.8 > 0.2 > water["likelihood"]


def test_distillation_carries_volatiles_only(cfg):
    dist = M.BY_LABEL["distilled water"]
    assert M.simulate(_c("CC(C)C1CCC(C)CC1O"), dist, cfg)["likelihood"] > 0.5       # menthol
    assert M.simulate(_c("OC(=O)/C=C/c1ccc(O)c(O)c1"), dist, cfg)["likelihood"] < 0.05  # caffeic acid


def test_ranges_bracket_median_and_are_reproducible(cfg):
    c = _c(ART)
    a = M.simulate(c, M.BY_LABEL["steeped in wine"], cfg)
    b = M.simulate(c, M.BY_LABEL["steeped in wine"], cfg)
    assert a == b and a["low"] <= a["likelihood"] <= a["high"]


def test_artemisinin_known_case_recorded():
    m = C.Metrics.model_validate_json(open("site-data/metrics.json").read())
    assert m.artemisininCheck.status == "computed" and m.artemisininCheck.result in ("pass", "borderline pass")
    case = json.load(open("data/interim/m4/artemisinin_check.json"))
    assert all(case["checks"].values())
    cw = case["predictions"]["cold water infusion"]
    assert case["result"] == ("borderline pass" if cw["high"] >= 0.30 else "pass")
    assert cw["drivers"]["filtration"] == 1.0  # filtered: no suspension contribution
    assert case["predictions"]["cold water, unfiltered (soaked and wrung out)"]["drivers"]["filtration"] > 1.0
    assert case["predictions"]["decoction in water"]["likelihood"] < case["predictions"]["cold water infusion"]["likelihood"]


def test_profiles_split_per_species_with_index():
    import gzip
    from pathlib import Path
    idx = json.load(open("site-data/profiles/index.json"))
    assert idx and not Path("site-data/profiles.json").exists()
    total = 0
    for e in idx:
        C.ProfileIndexEntry.model_validate(e)
        data = json.load(open(Path("site-data") / e["file"]))
        assert len(data) == e["preparations"] == 13
        p = C.Profile.model_validate(data[0])
        assert p.speciesId == e["speciesId"] and all(0 <= x.low <= x.likelihood <= x.high <= 1 for x in p.compounds)
        total += len(data)
    full = json.load(gzip.open("data/release/profiles_full.json.gz", "rt"))   # every M4 profile, incl. species no longer headline
    keep = {e["speciesId"] for e in idx}
    assert sum(1 for r in full if r["speciesId"] in keep) == total


def test_toxicity_screen_is_cited_and_conservative():
    from _cache import needs_cache
    from lip.m2 import toxicity
    with needs_cache("data/cache/sources (Wikipedia, List of poisonous plants)", "python -m lip m2 resolve"):
        assert toxicity.flag("Atropa belladonna")[0] == "known_toxic"
        flag, note = toxicity.flag("Mentha spicata")
        assert flag == "unknown" and "not evidence of safety" in note  # never "none_known"
        assert toxicity.load()["revid"]
