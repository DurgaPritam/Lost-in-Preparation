"""M5 study-method extraction with a fake client (no network, no Groq)."""
from __future__ import annotations

import json

import pytest

from lip.m1.providers import Completion, RunInfo
from lip.m5 import methods as M

TEXT = ("Leaves were shade-dried, powdered and extracted with 70% ethanol at room temperature for 72 h; "
        "the extract was filtered and concentrated. A decoction of the roots was also prepared.")
STUDY = M.Study("pmid:1", "A test study", TEXT, "abstract")


class FakeProvider:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def info(self):
        return RunInfo("fake", "fake-model", "v0", {"temperature": 0.0})

    def complete(self, system, messages, schema):
        self.calls.append(messages)
        out = self.outputs.pop(0)
        return Completion(out if isinstance(out, str) else json.dumps(out), "end", {"input_tokens": 1, "output_tokens": 1},
                          {"role": "assistant", "content": ""})


def good_leaf():
    return {"solvent": "hydroethanolic", "solventText": "70% ethanol", "heat": "cold", "heatText": "room temperature",
            "part": "leaf", "freshOrDried": "dried", "filtered": "yes",
            "evidence": [{"field": "solvent", "quote": "extracted with 70% ethanol"}, {"field": "heat", "quote": "at room temperature"},
                         {"field": "part", "quote": "Leaves"}, {"field": "freshOrDried", "quote": "shade-dried"},
                         {"field": "filtered", "quote": "the extract was filtered"}]}


def root_decoction():
    return {"solvent": "water", "solventText": "unknown", "heat": "boiled", "heatText": "unknown", "part": "root",
            "freshOrDried": "unknown", "filtered": "unknown",
            "evidence": [{"field": "solvent", "quote": "A decoction"}, {"field": "heat", "quote": "decoction"},
                         {"field": "part", "quote": "the roots"}]}


def test_schema_is_strict_and_evidence_only_for_categoricals():
    s = M.response_schema()
    prep = s["properties"]["preparations"]["items"]
    assert prep["additionalProperties"] is False and set(prep["required"]) == set(prep["properties"])
    assert prep["properties"]["evidence"]["items"]["properties"]["field"]["enum"] == M.CATEGORICAL


def test_good_extraction_and_ethanol_fraction(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "OUT", tmp_path)
    f = FakeProvider([{"preparations": [good_leaf(), root_decoction()]}])
    out = M.MethodExtractor(f).extract(STUDY, "Melissa officinalis")
    assert out["attempts"] == 1 and len(out["preparations"]) == 2 and out["rejections"] == []
    leaf, root = out["preparations"]
    assert leaf["ethanolFraction"] == 0.7 and leaf["unknownFields"] == [] and leaf["evidenceSource"] == "abstract"
    assert set(root["unknownFields"]) == {"freshOrDried", "filtered"}   # unstated -> unknown, never guessed
    again = M.MethodExtractor(FakeProvider([])).extract(STUDY, "Melissa officinalis")  # served from the cache
    assert again["preparations"] == out["preparations"]


def test_ellipsis_and_missing_evidence_are_rejected_with_compact_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "OUT", tmp_path)
    bad = good_leaf()
    bad["evidence"][0]["quote"] = "extracted with … ethanol"            # ellipsis
    bad["evidence"] = [e for e in bad["evidence"] if e["field"] != "filtered"]  # filtered=yes without a quote
    f = FakeProvider([{"preparations": [bad, root_decoction()]}, {"preparations": [good_leaf()]}])
    out = M.MethodExtractor(f, cache=False).extract(STUDY, "X")
    assert out["attempts"] == 2 and len(out["preparations"]) == 2 and out["rejections"] == []
    retry = f.calls[1]
    assert len(retry) == 2 and retry[0] == f.calls[0][0]                # the text again, no previous answer
    body = retry[1]["content"]
    assert "ellipsis not allowed" in body and "filtered=yes: no evidence quote given" in body
    failed = json.loads(body.split("The preparation(s) that failed:\n", 1)[1].split("\n", 1)[0])
    assert len(failed["preparations"]) == 1                              # only the failed preparation is resent


def test_non_categorical_evidence_fails_schema_and_retries_whole_text(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "OUT", tmp_path)
    wrong = good_leaf()
    wrong["evidence"].append({"field": "solventText", "quote": "70% ethanol"})
    f = FakeProvider([{"preparations": [wrong]}, {"preparations": [good_leaf()]}])
    out = M.MethodExtractor(f, cache=False).extract(STUDY, "X")
    assert out["attempts"] == 2 and len(out["preparations"]) == 1
    assert "full JSON for the whole text" in f.calls[1][1]["content"]


def test_persistent_failure_is_rejected_not_repaired(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "OUT", tmp_path)
    bad = good_leaf()
    bad["solventText"] = "seventy percent ethanol"                       # not in the text
    f = FakeProvider([{"preparations": [bad]}] + [{"preparations": [bad]}] * M.MAX_RETRIES)
    out = M.MethodExtractor(f, cache=False).extract(STUDY, "X")
    assert out["preparations"] == [] and len(out["rejections"]) == 1 and out["attempts"] == M.MAX_RETRIES + 1


def test_no_preparation_described(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "OUT", tmp_path)
    out = M.MethodExtractor(FakeProvider([{"preparations": []}]), cache=False).extract(STUDY, "X")
    assert out["preparations"] == [] and out["rejections"] == []


@pytest.mark.parametrize("solvent,text,expected", [
    ("hydroethanolic", "70% ethanol", 0.7), ("hydroethanolic", "ethanol 80%", 0.8), ("hydroethanolic", "50 % (v/v) aqueous ethanol", 0.5),
    ("ethanol", "absolute ethanol", None), ("methanol", "80% methanol", None), ("hydroethanolic", "unknown", None),
])
def test_ethanol_fraction_heuristic(solvent, text, expected):
    assert M.ethanol_fraction(solvent, text) == expected


def test_prompt_has_the_quote_rules():
    sysm = (M.PROMPT_DIR / "system.md").read_text()
    assert "allowed only for the 5 categorical fields" in sysm and "no ellipsis" in sysm and "never infer" in sysm
    assert M.prompt_version().startswith("m5_methods/v1:")
