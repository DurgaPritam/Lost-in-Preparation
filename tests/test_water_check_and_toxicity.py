"""v2 water-preparation check, water-window diagnostic, curated toxicity, per-source reporting, paraphrase rule."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from contract import models as C
from lip.m3 import toxicity
from lip.m4 import literature
from lip.m4 import model as M


# --- curated toxicity ---------------------------------------------------------------------------

def _proposed() -> list[str]:
    ss = pd.read_csv("data/interim/m3/study_set_proposal.csv")
    return list(ss[ss.proposed].acceptedName)


def test_toxicity_entries_cover_study_set_and_are_unverified():
    t = toxicity.table()
    assert sorted(t.acceptedName) == sorted(_proposed())
    assert set(t.basis) == {"ai_drafted_unverified"} and (t.verified_by == "").all()
    assert set(t.toxicity) <= set(toxicity.CATEGORIES)
    assert not t.toxicity.isin(["none_known", "known_toxic", "safe"]).any()
    sourced = t[t.toxicity != "unknown"]
    assert (sourced.sourceUrl != "").all() and (sourced.quote != "").all() and (sourced.licence != "").all()
    assert not sourced.licence.str.startswith(("none", "unknown")).any()
    assert not t.sourceUrl.str.contains("wikipedia", case=False).any()


def test_toxicity_quotes_reverify_against_sources():
    from _cache import needs_cache
    with needs_cache("data/cache/ema and data/cache/sources (EMA and PMC toxicity sources)", "python -m lip m3 studyset"):
        toxicity.build(_proposed())  # raises ToxicityError on any quote not found in the fetched source


def test_toxicity_rejects_unsourced_category(monkeypatch, tmp_path):
    monkeypatch.setattr(toxicity, "OUT", tmp_path / "t.csv")
    monkeypatch.setattr(toxicity, "ENTRIES", [("X y", "toxic_reported", "s", None, None, None, None)])
    with pytest.raises(toxicity.ToxicityError):
        toxicity.build(["X y"])


def test_profile_index_uses_curated_flags_with_evidence():
    idx = json.load(open("site-data/profiles/index.json"))
    t = toxicity.table().set_index("acceptedName")
    for e in idx:
        x = C.ProfileIndexEntry.model_validate(e)
        assert e["toxicityFlag"] == t.loc[x.acceptedName, "toxicity"]
        assert e["toxicityFlag"] not in ("none_known", "known_toxic")
        if e["toxicityFlag"] != "unknown":
            assert x.toxicityEvidence and x.toxicityEvidence.basis == "ai_drafted_unverified" and x.toxicityEvidence.verifiedBy == ""


# --- unlicensed article: paraphrase, never quote -------------------------------------------------

def test_unlicensed_article_is_paraphrased_not_quoted():
    df = pd.read_csv(literature.REF_CSV, dtype=str).fillna("")
    nl = df[df.pmcid.isin(literature.NO_LICENCE)]
    assert len(nl) == 3 and (nl.quote == "").all() and (nl.paraphrase != "").all() and (nl.citation != "").all()
    assert set(nl.evidenceType) == {"paraphrase"}
    assert (df[~df.pmcid.isin(literature.NO_LICENCE)].quote != "").all()


def test_quote_for_unlicensed_article_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(literature, "REF_CSV", tmp_path / "x.csv")
    monkeypatch.setattr(literature, "ROWS", [("Matricaria chamomilla", "apigenin", "tea", "hot water infusion (tea)", "low",
                                              "PMC2995283", "Aqueous extracts")])
    from _cache import needs_cache
    with needs_cache("data/cache/sources (PMC article pages and licences)", "python -m lip m4 run"):
        with pytest.raises(ValueError, match="no stated licence"):
            literature.build_table()


# --- v2 registered check ----------------------------------------------------------------------------

def test_v2_check_follows_registration():
    o = json.load(open("data/interim/m4/literature_prereg_v2.json"))
    assert o["registration"].endswith("(commit 9c36f68)") and o["modelVersion"] == M.config_version(M.load_config())
    assert o["found"]["present"] <= 15 and o["found"]["low"] <= 15
    df = pd.read_csv("data/reference/prep_literature_prereg_v2.csv")
    assert set(df.modelPreparation) <= {"cold water infusion", "hot water infusion (tea)", "decoction in water", "fresh juice"}
    assert not df.duplicated(["plant", "compound", "modelPreparation"]).any()
    assert (df.groupby("pmcid").size() <= 2).all()
    assert (df.groupby(["plant", "reported"]).size() <= 2).all()
    assert o["secondaryVariant"]["evaluatedOn"] == "v2 rows only"
    assert o["postHocAudit"]["basis"] == "ai_post_hoc_audit_unverified"
    assert o["primary"]["overall"]["n"] == len(df)


def test_variant_parameters_do_not_change_primary_model():
    cfg = M.load_config()
    c = M.Compound("x", 2.395, False, ["heat:endoperoxide"], False, 282.3)
    prep = M.BY_LABEL["cold water infusion"]
    assert M.simulate(c, prep, cfg) == M.simulate(c, prep, cfg, k_fixed=None, h_sd=0.0)
    assert M.simulate(c, prep, cfg)["likelihood"] == json.load(open("data/interim/m4/artemisinin_check.json"))[
        "predictions"]["cold water infusion"]["likelihood"]


def test_water_diagnostic_written():
    w = json.load(open("data/interim/m4/water_calibration.json"))
    assert w["modelVersion"] == M.config_version(M.load_config())
    assert w["crossings"]["median_eq_present_min"] < w["crossings"]["median_eq_absent_max"]
    assert w["studySetCompounds"]["spearmanLogPvsLikelihood"] < -0.9
    svg = open("docs/figures/water_likelihood_vs_logp.svg").read()
    assert svg.startswith("<svg") and "not a measurement" in svg


# --- per-source reporting -----------------------------------------------------------------------------

def test_results_report_per_source_with_pliny_lower_confidence():
    r = open("RESULTS.md").read()
    assert "## Headline metrics by source" in r and "| Metric | Culpeper | Pliny (lower confidence) | Overall |" in r
    assert "Pliny results are lower confidence" in open("README.md").read()
    src = json.load(open("site-data/sources.json"))
    assert all("LOWER CONFIDENCE" in s["editorialNote"] for s in src if s["id"].startswith("pliny"))
    assert not any("LOWER CONFIDENCE" in (s["editorialNote"] or "") for s in src if s["id"].startswith("culpeper"))


# --- complete-chemical-name matcher (v3 onwards) ---------------------------------------------------

from lip.m4.chemnames import Matcher  # noqa: E402

NAMES = {"phenol": "phenol", "apigenin": "apigenin", "apigenin 7-glucoside": "apigenin 7-glucoside", "quercetin": "quercetin",
         "rosmarinic acid": "rosmarinic acid", "α-pinene": "alpha-pinene", "naringenin": "naringenin", "gallic acid": "gallic acid"}


@pytest.mark.parametrize("text,expected", [
    ("the total phenol content was high", []),                         # v2 misread: class measure, not phenol
    ("phenol was detected", []),                                       # class noun never counts
    ("Apigenin 7-O-glucoside represented 7.6%", ["apigenin 7-glucoside"]),  # v2 misread: spaced glycoside spelling
    ("apigenin 7-O-rutinoside was found", []),                         # aglycone + locant = a different compound
    ("free apigenin was low", ["apigenin"]),
    ("quercetin 3-O-rutinoside and quercetin were found", ["quercetin"]),
    ("quercetin glycosides dominated", []),
    ("8-prenylnaringenin was detected", []),
    ("α-pinene (12%) was the major compound", ["alpha-pinene"]),
    ("total quercetin was 3 mg", []),
    ("rosmarinic acid derivatives were found", []),
    ("results in gallic acid equivalents (GAE)", []),
])
def test_complete_name_rule(text, expected):
    assert Matcher(NAMES).hits(text) == expected


@pytest.mark.parametrize("label,expected", [
    ("Rosmarinic acid", "rosmarinic acid"), ("Rosmarinic acid (RA)", "rosmarinic acid"),
    ("12 Apigenin-7-O-glucoside", "apigenin 7-glucoside"), ("α-Pinene *", "alpha-pinene"),
    ("Quercetin derivative", None), ("Total phenols", None), ("Phenol", None), ("Rosmarinic acid hexoside", None),
])
def test_exact_table_label(label, expected):
    assert Matcher(NAMES).exact_label(label) == expected


def test_v1_v2_collectors_unchanged_by_new_matcher():
    import inspect
    from lip.m4 import prereg_literature, prereg_v2
    assert "chemnames" not in inspect.getsource(prereg_literature) and "chemnames" not in inspect.getsource(prereg_v2)


# --- descriptor error in ranges (reporting only) ----------------------------------------------------

def test_descriptor_error_widens_range_not_median():
    cfg = M.load_config()
    sd = M.descriptor_sd("rdkit")
    v = json.load(open("data/interim/m4/logp_validation.json"))
    assert sd["mae"] == v["rdkit_all"]["mae"]["value"] and abs(sd["sd"] - sd["mae"] * 1.2533) < 1e-3
    c = M.Compound("x", 2.395, False, ["heat:endoperoxide"], False, 282.3)
    for lab in ("cold water infusion", "decoction in water", "infused oil"):
        a, b = M.simulate(c, M.BY_LABEL[lab], cfg), M.estimate(c, M.BY_LABEL[lab], cfg, sd=sd["sd"])
        assert a["likelihood"] == b["likelihood"] and a["drivers"] == b["drivers"]
        assert b["low"] <= b["likelihood"] <= b["high"] and b["rangeModelOnly"] == [a["low"], a["high"]]


def test_registered_scores_unaffected_by_range_change():
    s = json.load(open("data/interim/m4/m4_summary.json"))
    assert (s["literatureAgreementExploratory"], s["literatureAgreementPreregistered"], s["literatureAgreementPreregisteredV2"]) == \
        ("9/9", "19/19", "13/17")
    for f in ("data/reference/prep_literature_prereg_v1.csv", "data/reference/prep_literature_prereg_v2.csv"):
        d = pd.read_csv(f)
        assert ((d.low <= d.predicted) & (d.predicted <= d.high)).all()


# --- genus-signal audit -------------------------------------------------------------------------------

def test_genus_audit_marks_false_friends_disputed():
    from lip.m2 import genus_audit
    c = pd.read_parquet("data/interim/m2/name_candidates.parquet")
    top = c[c["rank"] == 1].set_index("nameId")
    for nid in genus_audit.ids():
        assert top.loc[nid, "disputed"] and top.loc[nid, "genusSignalAudit"]
    assert top.loc["pliny-nh:b22:c049:n0", "acceptedName"] == "Laser trilobum"
    newly = top[top.disputed & ~top.disputedBeforeGenusAudit]
    assert set(newly.index) <= genus_audit.ids()  # the audit is the only thing that changed
    ss = pd.read_csv("data/interim/m3/study_set_proposal.csv")
    assert not ss[ss.proposed].acceptedName.isin(["Laser trilobum", "Cotinus coggygria"]).any()
    assert "Moricandia arvensis" in json.load(open("data/interim/m2/flagged_for_review.json"))
    assert "Laser" in open("docs/GENUS_SIGNAL_AUDIT.md").read()
