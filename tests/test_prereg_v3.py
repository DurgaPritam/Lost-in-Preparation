"""v3 paired within-plant check: table reading, value rules, double-ratio scoring, analysis."""
from __future__ import annotations

import json
import math

import pandas as pd
import pytest
from lxml import html as H

from lip.m4 import model as M
from lip.m4 import prereg_v3 as P
from lip.m4.chemnames import Matcher

MATCH = Matcher({s: n for n, syns in P.V1_COMPOUNDS.items() for s in syns})
NO_LOTUS = pd.DataFrame(columns=["label", "smiles", "inchikey"])


@pytest.mark.parametrize("label,prep,cond", [
    ("Infusion", "hot water infusion (tea)", ""), ("Methanol extract", "modern methanol extract", ""),
    ("70% aqueous ethanol", "modern 70% ethanol extract", ""), ("MeOH:H2O (80:20)", "modern methanol extract", ""),
    ("Leaves Decoction (mg/g DW)", "decoction in water", "leaves"), ("Essential oil (%)", "distilled water", ""),
    ("Flowers EO", "distilled water", "flowers"), ("Infusion and decoction", None, "and"), ("Retention time (min)", None, "retention time min"),
])
def test_preparation_labels(label, prep, cond):
    assert P.prep_of(label) == (prep, cond)


@pytest.mark.parametrize("cell,value", [("12.3 ± 0.4", 12.3), ("n.d.", 0.0), ("ND", 0.0), ("<LOD", 0.0), ("–", 0.0), ("tr", 0.0),
                                        ("10,5", 10.5), ("", None), ("see text", None), ("2.1e-3", 0.0021),
                                        # registered rule = "first number in the cell": thousands separators are NOT handled
                                        # (a known limitation of v3, reported; not changed after registration)
                                        ("1,234.5", 1.0)])
def test_cell_values(cell, value):
    assert P.value_of(cell) == (pytest.approx(value) if value is not None else None)


TABLE = """<table><thead><tr><th rowspan="2">Compound</th><th colspan="2">Leaves</th><th>Flowers</th></tr>
<tr><th>Infusion</th><th>Essential oil (%)</th><th>Infusion</th></tr></thead><tbody>
<tr><td>Thymol</td><td>0.5 ± 0.1</td><td>45.2</td><td>1</td></tr><tr><td>Rosmarinic acid</td><td>30.1</td><td>n.d.</td><td>9</td></tr>
<tr><td>Total phenols</td><td>99</td><td>1</td><td>5</td></tr><tr><td>Carvacrol a</td><td>0.2</td><td>10.5</td><td>2</td></tr></tbody></table>"""


def test_table_reading_pairs_only_same_material():
    t = P.read_table(H.fromstring(TABLE), MATCH)
    assert t["orientation"] == "A" and set(t["values"]) == {"thymol", "rosmarinic acid", "carvacrol"}  # not "Total phenols"
    assert P.comparable_pairs(t) == [(0, 1)]  # leaves infusion vs leaves EO; flowers column has no partner


def test_double_ratio_sign_and_rules():
    from _cache import needs_cache, require_dir
    require_dir("data/cache/pubchem", "PubChem compound structures", "python -m lip m4 run")  # misses are tolerated quietly
    t = P.read_table(H.fromstring(TABLE), MATCH)
    with needs_cache("data/cache/pubchem (compound structures)", "python -m lip m4 run"):
        rows, st = P.score_table(t, P.Model(M.load_config()), NO_LOTUS, {"pmcid": "X", "plant": "T"})
    r = {(x["compoundX"], x["compoundY"]): x for x in rows}
    ra = r[("rosmarinic acid", "thymol")]
    # rosmarinic acid: 30.1 in infusion, n.d. -> half the smallest positive EO value (10.5/2) ; thymol 0.5 vs 45.2
    assert math.isclose(ra["deltaObs"], math.log(30.1 / 0.5) - math.log(5.25 / 45.2), rel_tol=1e-3)
    assert ra["deltaObs"] > 0 and ra["deltaPred"] > 0 and ra["agree"] is True  # polar acid enriched in the infusion
    assert r[("carvacrol", "thymol")]["abstain"]  # same descriptors class: model cannot rank -> abstains, not scored
    assert st["pairsConsidered"] == 3


def test_analysis_is_per_article_with_cluster_bootstrap():
    pairs = pd.DataFrame({"pmcid": ["a"] * 9 + ["b"], "plant": "p", "contrast": "aqueous vs distillation",
                          "abstain": False, "agree": [True] * 9 + [False]})
    res = P.analyse(pairs)
    assert res["primary"]["meanPerArticleAgreement"] == 0.5  # each article weighs the same, not each pair
    assert res["pooledPairAgreement"]["rate"] == 0.9 and res["primary"]["verdict"] == "not distinguishable from chance"


def test_v3_output_follows_registration():
    o = json.load(open("data/interim/m4/literature_prereg_v3.json"))
    assert "7bc28ab" in o["registration"] and "99e120e" in o["registration"]
    assert o["modelVersion"] == M.config_version(M.load_config())
    assert all(sum(1 for _, why in v["screened"] if why.startswith("eligible")) <= P.MAX_ARTICLES_PER_PLANT for v in o["screening"].values())
    excluded = P._excluded()
    if o.get("articles"):
        d = pd.read_csv(P.CSV)
        assert not d.pmcid.isin(excluded).any()
        assert ((d.prep1 != d.prep2)).all()
        assert d[~d.abstain].agree.notna().all() and d[d.abstain].agree.isna().all()


# --- number parsing for FUTURE registered checks (v3 keeps its registered parser) -------------------

from lip.m4.values import parse_cell  # noqa: E402


@pytest.mark.parametrize("cell,value", [
    ("1,234.5", 1234.5), ("12,345.67", 12345.67), ("1,234,567", 1234567.0), ("1.234,5", 1234.5), ("1 234.5", 1234.5),
    ("1 234,5", 1234.5), ("10,5", 10.5), ("0,25", 0.25), ("1.234", 1.234), ("12.3 ± 0.4", 12.3), ("45.2a", 45.2),
    ("2.1e-3", 0.0021), ("2.1 × 10−3", 0.0021), ("3.5 x 10^2", 350.0),
    ("n.d.", 0.0), ("<LOQ", 0.0), ("–", 0.0),
    ("1,234", None),            # ambiguous: thousands (English) or decimal comma -> missing, never guessed
    ("1,23,4", None), ("", None), ("see text", None),
])
def test_future_parser_handles_thousands_separators(cell, value):
    got = parse_cell(cell)
    assert got == (pytest.approx(value) if value is not None else None)


def test_v3_parser_is_unchanged():
    assert P.value_of("1,234.5") == 1.0  # registered behaviour kept; v3 is not re-scored
    import inspect
    assert "from .values" not in inspect.getsource(P) and "parse_cell" not in inspect.getsource(P)
