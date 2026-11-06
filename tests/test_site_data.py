"""Phase 7 preparation: every site-data file validates against the contract; reporting gap, liquorice case, wine source."""
from __future__ import annotations

import json

from contract import models as C
from lip.paths import INTERIM, ROOT, SITE_DATA


def test_every_site_data_file_validates_and_none_is_mock():
    for path, key in {"sources.json": "sources.json", "recipes.json": "recipes.json", "species.json": "species.json",
                      "profiles/index.json": "profiles.index.json", "audit.json": "audit.json", "hypotheses.json": "hypotheses.json"}.items():
        recs = [C.FILE_MODELS[key].model_validate(x) for x in json.loads((SITE_DATA / path).read_text())]
        assert recs and not any(r.mock for r in recs), path
    m = C.Metrics.model_validate_json((SITE_DATA / "metrics.json").read_text())
    assert m.headlineMatchRate.status == "computed" and "v1" in m.headlineMatchRate.note
    idx = json.loads((SITE_DATA / "profiles" / "index.json").read_text())
    for e in idx:
        [C.Profile.model_validate(x) for x in json.loads((SITE_DATA / e["file"]).read_text())]


def test_profiles_cover_exactly_the_headline_set():
    import pandas as pd
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    idx = json.loads((SITE_DATA / "profiles" / "index.json").read_text())
    assert {e["speciesId"] for e in idx} == set(ss[ss.headline].wfoId)
    assert {p.name for p in (SITE_DATA / "profiles").glob("wfo-*.json")} == {e["file"].split("/")[1] for e in idx}


def test_recipes_are_the_session_extraction_and_species_link_to_them():
    recs = json.loads((SITE_DATA / "recipes.json").read_text())
    assert {r["provenance"]["provider"] for r in recs} == {"Claude via Claude Code session"}
    ids = {r["id"] for r in recs}
    assert len(ids) == len(recs)
    assert {s["recipeId"] for s in json.loads((SITE_DATA / "species.json").read_text())} <= ids


def test_reporting_gap_shares_have_n_and_ci():
    g = json.loads((INTERIM / "m5" / "reporting_gap.json").read_text())
    for s in g["sets"].values():
        for k, x in s["all"].items():
            assert x["n"] > 0 and x["low"] <= x["value"] <= x["high"], k
    v3 = g["v3Screening"]
    assert v3["eligibleScreenings"] == v3["share"]["k"] and v3["screeningsWithTablesExamined"] == v3["share"]["n"]


def test_liquorice_case_is_computed_and_logged():
    c = json.loads((INTERIM / "m6" / "liquorice_case.json").read_text())
    assert c["extractedAs"]["part"] == "juice" and c["correctedTo"]["part"] == "root"
    assert c["before"]["faithful"] == "fresh juice" and c["after"]["faithful"] == "decoction in water"
    assert "Spanish juice" in c["evidence"][0]["text"]


def test_wine_source_is_recorded_with_licence_and_quote():
    d = json.loads((ROOT / "data" / "reference" / "wine_alcohol_source.json").read_text())
    assert d["licence"] == "cc by" and d["doi"] == "10.3390/foods14111854" and d["verified_by"] == ""
    assert "generally ranges between 10 and 13%" in d["quotes"][0]
