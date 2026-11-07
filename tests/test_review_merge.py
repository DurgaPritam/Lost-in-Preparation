"""Review pass v1 (basis ai_assisted_check): provisional only, never human validation."""
import csv
import json

import pytest

from lip import review_merge as R
from lip.paths import ROOT


def test_review_merge_runs_and_stays_provisional():
    out = R.run()
    assert out["basis"] == "ai_assisted_check"
    assert "not human validation" in out["label"]
    assert out["toxicity"]["n"] == 20 and out["plates"]["n"] == 15 and out["genusAudit"]["n"] == 32 and out["studySetRationale"]["n"] == 9
    assert out["genusAudit"]["sourceReopened"] == 0


def test_no_verified_by_or_confirmed_status_is_written():
    tox = list(csv.DictReader(open(ROOT / "data" / "reference" / "toxicity_curated.csv", newline="")))
    assert all(not r["verified_by"] for r in tox)
    assert {p["status"] for p in json.loads((ROOT / "site-data" / "plates.json").read_text())} <= {"sourced", "to_source"}
    for f in (R.DIR).glob("*.csv"):
        cols = next(csv.reader(open(f, newline="")))
        assert not {"verified_by", "verifiedBy", "gold"} & set(cols), f.name


def test_licence_term_rule():
    assert R._term("PD-old", 1927) == (True, "PD-old: 1927 + 70 = 1997")
    assert R._term("PD-old-100", 1927)[0] is False          # 1927 + 100 = 2027: not yet expired in 2026
    assert R._term("PD-old-100", 1865)[0] is True
    assert R._term("PD-scan|PD-old-auto-expired|deathyear=1925", 1925)[0] is True
    assert R._term("CC-BY-SA-4.0", 1800)[0] is False


def test_study_set_rationale_is_never_presented_as_the_leads_words():
    for r in csv.DictReader(open(R.DIR / "study_set_rationale.csv", newline="")):
        assert "not the project lead's own words" in r["rationaleKind"]
    dec = list(csv.DictReader(open(ROOT / "config" / "study_set_review_decisions.csv", newline="")))
    assert not any("rationale from the proposal" in r["reason"] for r in dec)


def test_bad_basis_is_refused(tmp_path, monkeypatch):
    (tmp_path / "x.csv").write_text("a,basis\n1,human\n")
    monkeypatch.setattr(R, "DIR", tmp_path)
    with pytest.raises(R.ReviewError):
        R._rows("x.csv")
