"""M1 session extraction (written in a Claude Code session) and single-annotator evaluation."""
from __future__ import annotations

import json

import pytest

from lip.m1 import evaluate as ev
from lip.m1 import session as S

PID = "pliny-nh:b24:c027:001"   # "A decoction in vinegar of the wood of the torch-tree makes a most efficacious gargle for tooth-ache."
GOOD = {"recipeQuote": "A decoction in vinegar of the wood of the torch-tree makes a most efficacious gargle for tooth-ache.",
        "recipeType": "single_plant", "ingredients": [{"plantNameAsWritten": "torch-tree", "part": "stem", "role": "principal", "kind": "plant"}],
        "plantNameAsWritten": "torch-tree", "part": "stem", "freshOrDried": "unknown", "solvent": ["vinegar"], "heat": "boiled",
        "heatText": "unknown", "durationText": "unknown", "filtered": "unknown", "process": "decoction", "form": "gargle",
        "indicationAsWritten": "tooth-ache",
        "evidence": [{"field": "part", "quote": "the wood of the torch-tree"}, {"field": "solvent", "quote": "A decoction in vinegar"},
                     {"field": "heat", "quote": "A decoction in vinegar"}, {"field": "process", "quote": "A decoction in vinegar"},
                     {"field": "form", "quote": "makes a most efficacious gargle"}],
        "quotesFromHeading": [], "fieldConfidence": []}


def _batch(tmp_path, recipes, version=None):
    d = tmp_path / "sess" / "t"
    d.mkdir(parents=True, exist_ok=True)
    v = version or S.Extractor(S._SessionProvider("x"), cache=False, prompt_version=S.PROMPT).prompt.version
    (d / "batch_01.json").write_text(json.dumps({"batch": 1, "scope": "t", "promptVersion": v, "writtenOn": "2026-11-06",
                                                 "passages": {PID: {"recipes": recipes}}}))


def test_ingest_accepts_valid_and_rejects_without_repair(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "SESSION_DIR", tmp_path / "sess")
    monkeypatch.setattr(S, "OUT", tmp_path / "out")
    bad = json.loads(json.dumps(GOOD))
    bad["recipeQuote"] = "A decoction in wine of the wood"          # not in the passage
    _batch(tmp_path, [GOOD, bad])
    out = S.ingest("t")
    assert out["recipesAccepted"] == 1 and out["recipesRejected"] == 1 and out["passagesFailedWhole"] == 0
    rej = [json.loads(x) for x in (tmp_path / "out" / "rejections_t.jsonl").read_text().splitlines()]
    assert rej[0]["recipe"]["recipeQuote"] == "A decoction in wine of the wood"   # logged as written, not repaired
    pred = json.loads((tmp_path / "out" / "predictions_t.json").read_text())
    prov = pred[0]["provenance"]
    assert prov["provider"] == "Claude via Claude Code session" and prov["model"] == "claude-opus-5-5"
    assert prov["promptVersion"].startswith("m1_extract/v3:") and prov["decoding"]["writtenOn"] == "2026-11-06"


def test_ingest_refuses_a_batch_written_for_another_prompt(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "SESSION_DIR", tmp_path / "sess")
    monkeypatch.setattr(S, "OUT", tmp_path / "out")
    _batch(tmp_path, [GOOD], version="m1_extract/v2:deadbeef00")
    with pytest.raises(ValueError, match="written for"):
        S.ingest("t")


def test_schema_failure_rejects_the_whole_passage(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "SESSION_DIR", tmp_path / "sess")
    monkeypatch.setattr(S, "OUT", tmp_path / "out")
    _batch(tmp_path, [{"nonsense": 1}])
    out = S.ingest("t")
    assert out["passagesFailedWhole"] == 1 and out["recipesAccepted"] == 0


def test_committed_outputs_carry_session_provenance():
    for scope in ("sample", "approved"):
        run = json.loads((S.OUT / f"run_{scope}.json").read_text())
        pred = json.loads((S.OUT / f"predictions_{scope}.json").read_text())
        rej = (S.OUT / f"rejections_{scope}.jsonl").read_text().splitlines()
        assert run["recipesAccepted"] == len(pred) and run["recipesRejected"] + run["passagesFailedWhole"] == len(rej)
        assert {r["provenance"]["provider"] for r in pred} == {"Claude via Claude Code session"}
        assert {r["provenance"]["promptVersion"] for r in pred} == {run["promptVersion"]}
        for b in S.batches(scope):   # every batch was written for prompt v3 and says it did not consult the silver set
            assert b["promptVersion"].startswith("m1_extract/v3:") and "without consulting the silver" in b["note"]


def test_approved_scope_covers_phase5_species_only():
    from lip.m5.literature import held_species, species_list
    a = S.approved_passages()
    assert set(a.species) <= set(species_list().acceptedName)
    assert not set(a.species) & set(held_species().species)
    assert len(S.passages_for("approved")) == a.passageId.nunique()
    sample = set(S.passages_for("sample"))
    assert not set(S.to_write("approved")) & sample          # overlapping passages reuse their sample extraction
    covered = {pid for b in S.batches("approved") for pid in b["passages"]}
    assert covered == set(S.passages_for("approved"))


# --- evaluation: single annotator gold, self-consistency, no silver for the session extractor --------------------

def _patch(monkeypatch, tmp_path, sp):
    (tmp_path / "s.json").write_text(json.dumps({"passages": sp}))
    for k, v in {"SAMPLE_PATH": tmp_path / "s.json", "ANN_DIR": tmp_path / "ann", "GOLD_PATH": tmp_path / "ann" / "gold.json",
                 "PRED_PATH": tmp_path / "pred.json", "RUN_PATH": tmp_path / "run.json", "DETAIL_PATH": tmp_path / "d.json",
                 "TALLY_PATH": tmp_path / "t.json", "SITE_DATA": tmp_path / "site", "SILVER_PATH": tmp_path / "silver.json"}.items():
        monkeypatch.setattr(ev, k, v)


def _ann(sp, heat, ids=None):
    return {"annotator": "x", "passages": {p["passageId"]: {"done": True, "recipes": [
        {"recipeSpan": {"quote": "x", "start": 0, "end": 10}, "part": "root", "heat": heat(i), "solvent": ["wine"],
         "ingredients": [{"plantNameAsWritten": "Fennel"}], "plantNameAsWritten": "Fennel"}]}
        for i, p in enumerate(sp) if ids is None or p["passageId"] in ids}}


def _pred(sp, provider=None):
    return [{"passage": {"passageId": p["passageId"]}, "recipeType": "unknown", "part": "root", "heat": "boiled", "solvent": ["wine"],
             "ingredients": [{"plantNameAsWritten": "Fennel"}], "plantNameAsWritten": "Fennel",
             "evidence": {"recipe": [{"quote": "x", "start": 0, "end": 8}]}, "provenance": {"provider": provider}} for p in sp]


def test_single_annotator_is_gold_and_reannotation_gives_self_consistency(monkeypatch, tmp_path):
    sp = [{"passageId": f"p{i}", "stratum": s} for i, s in enumerate(["culpeper1652_virtues", "culpeper1850_dispensatory", "pliny"] * 10)]
    _patch(monkeypatch, tmp_path, sp)
    (tmp_path / "ann").mkdir()
    (tmp_path / "ann" / "lead.json").write_text(json.dumps(_ann(sp, lambda i: "boiled")))
    (tmp_path / "pred.json").write_text(json.dumps(_pred(sp, S.PROVIDER)))
    m = ev.evaluate()
    assert m.extraction.overall["heat"].f1.value == 1.0                         # the single annotation is the gold set
    assert "re-annotation" in m.interAnnotatorAgreement["heat"].note
    d = json.loads((tmp_path / "d.json").read_text())
    assert d["goldBasis"] == "single annotator (no adjudication)"
    ids = {p["passageId"] for p in sp[:15]}
    (tmp_path / "ann" / "lead_reannotation.json").write_text(json.dumps(_ann(sp, lambda i: "boiled" if i % 3 else "cold", ids)))
    (tmp_path / "ann" / "lead.json").write_text(json.dumps(_ann(sp, lambda i: "boiled" if i % 2 else "cold")))
    m = ev.evaluate()
    k = m.interAnnotatorAgreement["heat"]
    assert k.status == "computed" and "self-consistency" in k.note and "in 15 passages" in k.note
    assert json.loads((tmp_path / "d.json").read_text())["agreement"] == "intra-annotator (self-consistency)"


def test_silver_comparison_is_refused_for_the_session_extractor(monkeypatch, tmp_path):
    sp = [{"passageId": "p0", "stratum": "pliny"}]
    _patch(monkeypatch, tmp_path, sp)
    (tmp_path / "silver.json").write_text(json.dumps({"basis": "silver_ai_reference", "passages": _ann(sp, lambda i: "boiled")["passages"]}))
    (tmp_path / "pred.json").write_text(json.dumps(_pred(sp, S.PROVIDER)))
    m = ev.evaluate("silver")
    f1 = m.provisional["extractionVsSilver"].extraction.overall["part"].f1
    assert f1.status == "not_computed" and "circular" in f1.note
