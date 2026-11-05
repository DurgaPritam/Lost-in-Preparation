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
    assert sorted(t.acceptedName) == sorted(_proposed()) and len(t) == 30
    assert set(t.basis) == {"ai_drafted_unverified"} and (t.verified_by == "").all()
    assert set(t.toxicity) <= set(toxicity.CATEGORIES)
    assert not t.toxicity.isin(["none_known", "known_toxic", "safe"]).any()
    sourced = t[t.toxicity != "unknown"]
    assert (sourced.sourceUrl != "").all() and (sourced.quote != "").all() and (sourced.licence != "").all()
    assert not sourced.licence.str.startswith(("none", "unknown")).any()
    assert not t.sourceUrl.str.contains("wikipedia", case=False).any()


def test_toxicity_quotes_reverify_against_sources():
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
