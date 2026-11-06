"""Phase 2 (M1) tests.

All annotation / prediction data below is SYNTHETIC test fixture data, constructed by hand to
check the metric arithmetic. It is never written to site-data/.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from contract import models as C
from lip.m1 import evaluate as ev
from lip.m1 import extract as ex
from lip.m1 import providers
from lip.m1 import sample as smp
from lip.m1.prompt import fewshot, fewshot_ids
from lip.m1.schema import LLMRecipe, LLMResponse, response_schema
from lip.m1.spans import check_recipe, find


@pytest.fixture(scope="module")
def passages():
    return pd.read_parquet("data/interim/passages.parquet").set_index("passage_id")


# --- spans --------------------------------------------------------------------------------

def test_find_normalises_typography_only():
    text = "Venus’s herb — boiled in white wine, then strained."
    s, e = find("Venus's herb - boiled", text)
    assert text[s:e] == "Venus’s herb — boiled"  # offsets index the original text
    assert find("boiled in white wine.", text) is not None  # trailing punctuation trimmed
    assert find("Boiled in white wine", text) is None  # case must match
    assert find("boiled in wine", text) is None  # no paraphrase


def _recipe(**kw) -> LLMRecipe:
    base = dict(recipeQuote="boiled in white wine", recipeType="unknown", ingredients=[], plantNameAsWritten="unknown",
                part="unknown", freshOrDried="unknown", solvent=["unknown"], heat="unknown", heatText="unknown",
                durationText="unknown", filtered="unknown", process="unknown", form="unknown",
                indicationAsWritten="unknown", evidence=[], quotesFromHeading=[], fieldConfidence=[])
    base.update(kw)
    return LLMRecipe.model_validate(base)


def test_check_rejects_missing_evidence_and_bad_quotes():
    text = "The leaves boiled in white wine help the cough."
    ok = _recipe(solvent=["wine"], evidence=[{"field": "solvent", "quote": "white wine"}])
    assert check_recipe(ok, text, "").ok
    no_ev = _recipe(solvent=["wine"])
    assert any("no evidence" in e for e in check_recipe(no_ev, text, "").errors)
    bad = _recipe(indicationAsWritten="helps coughs")
    assert any("not found" in e for e in check_recipe(bad, text, "").errors)
    mixed = _recipe(solvent=["unknown", "wine"], evidence=[{"field": "solvent", "quote": "white wine"}])
    assert not check_recipe(mixed, text, "").ok


def test_heading_quotes_only_for_names():
    text = "It helps the cough."
    r = _recipe(recipeQuote="It helps the cough", plantNameAsWritten="HYSSOP", quotesFromHeading=["plantNameAsWritten"])
    assert check_recipe(r, text, "HYSSOP.").ok
    r2 = _recipe(recipeQuote="It helps the cough", indicationAsWritten="HYSSOP", quotesFromHeading=["plantNameAsWritten"])
    assert not check_recipe(r2, text, "HYSSOP.").ok


def test_recipe_type_consistency():
    text = "Fennel and Rue boiled together."
    two = [{"plantNameAsWritten": "Fennel", "part": "unknown", "role": "principal", "kind": "plant"},
           {"plantNameAsWritten": "Rue", "part": "unknown", "role": "co_ingredient", "kind": "plant"}]
    assert not check_recipe(_recipe(recipeQuote="Fennel and Rue", recipeType="single_plant", ingredients=two), text, "").ok
    assert check_recipe(_recipe(recipeQuote="Fennel and Rue", recipeType="compound", ingredients=two), text, "").ok


def test_fewshot_examples_pass_the_validator(passages):
    for exm in fewshot("v1"):
        row = passages.loc[exm["passageId"]]
        for r in LLMResponse.model_validate(exm["output"]).recipes:
            c = check_recipe(r, row.text_clean, row.entry_title)
            assert c.ok, (exm["passageId"], c.errors)


def test_response_schema_is_strict():
    def walk(s):
        if s.get("type") == "object":
            assert s["additionalProperties"] is False
            assert set(s["required"]) == set(s["properties"])
            for v in s["properties"].values():
                walk(v)
        if s.get("type") == "array":
            walk(s["items"])
    walk(response_schema())


# --- extraction loop with a fake client -----------------------------------------------------

class FakeOllama:
    """Stands in for the Ollama HTTP API (transport injection); records every request."""

    def __init__(self, outputs, model="qwen2.5:7b-instruct"):
        self.outputs, self.calls, self.model = list(outputs), [], model

    def __call__(self, path, payload, method="POST"):
        if path == "/api/tags":
            return {"models": [{"name": self.model, "digest": "sha256:test", "details": {"quantization_level": "Q4_K_M",
                                                                                          "parameter_size": "7.6B"}}]}
        self.calls.append(payload)
        return {"message": {"role": "assistant", "content": json.dumps(self.outputs.pop(0))}, "done_reason": "stop",
                "prompt_eval_count": 10, "eval_count": 5}


def ollama(outputs):
    fake = FakeOllama(outputs)
    return providers.OllamaProvider(model=fake.model, transport=fake), fake


class FakeAnthropic:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        text = json.dumps(self.outputs.pop(0))
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0,
                                                     cache_creation_input_tokens=0))


def _row(passages, pid):
    r = passages.loc[pid]
    return SimpleNamespace(passage_id=pid, **{k: r[k] for k in r.index})


def test_retry_then_accept(passages):
    pid = "culpeper-1850:herbal:amara-dulcis:006"
    good = next(e for e in fewshot("v1") if e["passageId"] == pid)["output"]
    bad = json.loads(json.dumps(good))
    bad["recipes"][0]["indicationAsWritten"] = "to open the liver"  # not verbatim
    prov, fake = ollama([bad, good])
    out = ex.Extractor(prov, cache=False, prompt_version="v1").extract(_row(passages, pid))
    assert out["attempts"] == 2 and len(out["recipes"]) == 1 and out["rejections"] == []
    assert fake.calls[1]["messages"][-1]["role"] == "user" and "quoting rules" in fake.calls[1]["messages"][-1]["content"]
    rec = C.Recipe.model_validate(out["recipes"][0])
    assert rec.attributionCaveat and rec.excludedFromHeadline is False
    q = rec.evidence["solvent"][0]
    assert rec.passage.text[q.start:q.end] == q.quote == "three pints of white wine"
    assert rec.evidence["plantNameAsWritten"][0].inHeading
    # same schema, temperature 0, fixed seed, provider + digest recorded
    req = fake.calls[0]
    assert req["format"] == response_schema() and req["options"]["temperature"] == 0 and req["options"]["seed"] == 0
    assert req["options"]["num_ctx"] >= 16384 and req["messages"][0]["role"] == "system"
    assert (rec.provenance.provider, rec.provenance.modelVersion) == ("ollama", "sha256:test")
    assert rec.provenance.decoding["quantization"] == "Q4_K_M"


def test_anthropic_provider_uses_same_schema_and_fallbacks(passages):
    pid = "culpeper-1850:herbal:amara-dulcis:006"
    good = next(e for e in fewshot("v1") if e["passageId"] == pid)["output"]
    client = FakeAnthropic([good])
    prov = providers.AnthropicProvider(client=client)
    out = ex.Extractor(prov, cache=False, prompt_version="v1").extract(_row(passages, pid))
    assert len(out["recipes"]) == 1 and out["run"]["provider"] == "anthropic"
    call = client.calls[0]
    assert call["output_config"]["format"]["schema"] == response_schema()
    assert call["betas"] == ["server-side-fallback-2026-07-01"] and call["fallbacks"] == "default"


def test_same_prompt_for_both_providers(passages):
    pid = "culpeper-1850:herbal:one-blade~2:002"
    po, fo = ollama([{"recipes": []}])
    ex.Extractor(po, cache=False, prompt_version="v1").extract(_row(passages, pid))
    ca = FakeAnthropic([{"recipes": []}])
    ex.Extractor(providers.AnthropicProvider(client=ca), cache=False, prompt_version="v1").extract(_row(passages, pid))
    assert fo.calls[0]["messages"][0]["content"] == ca.calls[0]["system"][0]["text"]
    assert fo.calls[0]["messages"][1:] == ca.calls[0]["messages"]


def test_cache_key_depends_on_provider_model_and_digest(passages):
    a, _ = ollama([])
    b = providers.OllamaProvider(model="qwen3:8b", transport=FakeOllama([], model="qwen3:8b"))
    row = _row(passages, "culpeper-1850:herbal:one-blade~2:002")
    assert ex.Extractor(a)._cache_path(row.passage_id) != ex.Extractor(b)._cache_path(row.passage_id)


def test_persistent_bad_span_is_rejected_not_repaired(passages):
    pid = "culpeper-1850:herbal:amara-dulcis:006"
    bad = json.loads(json.dumps(next(e for e in fewshot("v1") if e["passageId"] == pid)["output"]))
    bad["recipes"][0]["durationText"] = "12 hours"
    out = ex.Extractor(ollama([bad] * (ex.MAX_RETRIES + 1))[0], cache=False, prompt_version="v1").extract(_row(passages, pid))
    assert out["recipes"] == [] and out["attempts"] == ex.MAX_RETRIES + 1
    assert "durationText" in out["rejections"][0]["errors"][0]


def test_compound_recipes_excluded_from_headline(passages):
    pid = "culpeper-1850:herbal:one-blade~2:004"
    good = next(e for e in fewshot("v1") if e["passageId"] == pid)["output"]
    out = ex.Extractor(ollama([good])[0], cache=False, prompt_version="v1").extract(_row(passages, pid))
    flags = [(r["recipeType"], r["excludedFromHeadline"]) for r in out["recipes"]]
    assert flags == [("single_plant", False), ("compound", True)]


# --- sample -------------------------------------------------------------------------------

def test_sample_is_deterministic_stratified_and_leak_free(passages):
    a, b = smp.draw(), smp.draw()
    assert a.passage_id.tolist() == b.passage_id.tolist()
    assert a.stratum.value_counts().to_dict() == smp.ALLOCATION
    assert not set(a.passage_id) & fewshot_ids()
    assert a.recipe_scope.all() and (a.passage_type == "body").all() and (a.gap_count == 0).all()
    v = a[a.stratum == "culpeper1652_virtues"]
    assert (v.source_id == "culpeper-1652").all() and (v.subsection == "vertues and use").all()
    assert a[a.stratum == "pliny"].book.between(20, 27).all()
    on_disk = [p["passageId"] for p in json.loads(smp.SAMPLE_PATH.read_text())["passages"]]
    assert on_disk == a.passage_id.tolist()


# --- metrics arithmetic (synthetic fixtures) --------------------------------------------------

def _flat(span, **kw):
    r = {f: "unknown" for f in ev.CATEGORICAL_FIELDS + ev.TEXT_FIELDS}
    r.update(solvent=[], ingredients=[], span=span, spanText="")
    r.update(kw)
    return r


def test_field_counts_hand_computed():
    gold_x = [_flat((0, 50), part="root", solvent=["wine"], heat="boiled", form="drink",
                    plantNameAsWritten="Fennel", indicationAsWritten="the stone", ingredients=["Fennel"])]
    pred_x = [_flat((0, 48), part="root", solvent=["water", "wine"], form="ointment",
                    plantNameAsWritten="Fennel", indicationAsWritten="stone", ingredients=["Fennel"]),
              _flat((100, 140), part="leaf", plantNameAsWritten="Rue")]
    gold_y = [_flat((0, 30), part="seed", plantNameAsWritten="Anise")]
    cx, _ = ev.passage_counts(gold_x, pred_x)
    cy, _ = ev.passage_counts(gold_y, [])
    tot = lambda f: tuple(cx[f][i] + cy[f][i] for i in range(3))  # noqa: E731
    assert tot("part") == (1, 1, 1)
    assert tot("solvent") == (1, 1, 0)
    assert tot("heat") == (0, 0, 1)
    assert tot("form") == (0, 1, 1)
    assert tot("plantNameAsWritten") == (1, 1, 1)
    assert tot("indicationAsWritten") == (1, 0, 0)
    assert tot("_recipe") == (1, 1, 1)
    assert ev.prf(*tot("part")) == (0.5, 0.5, 0.5)
    assert ev.prf(*tot("heat"))[0] is None and ev.prf(*tot("heat"))[1] == 0.0


def test_alignment_breaks_span_ties_by_agreement():
    g = [_flat((0, 40), form="other"), _flat((0, 40), form="drink")]
    p = [_flat((0, 40), form="drink"), _flat((0, 40), form="other")]
    pairs, ug, up = ev.align(g, p)
    assert sorted(pairs) == [(0, 1), (1, 0)] and not ug and not up


def test_cohen_kappa_textbook_value():
    pairs = [("a", "a")] * 20 + [("a", "b")] * 5 + [("b", "a")] * 10 + [("b", "b")] * 15
    assert ev.cohen_kappa(pairs) == pytest.approx(0.4)
    assert ev.cohen_kappa([("x", "x")] * 5) is None  # undefined, not 1.0


def _patch_paths(monkeypatch, tmp_path, sample_passages):
    sp = tmp_path / "sample.json"
    sp.write_text(json.dumps({"passages": sample_passages}))
    monkeypatch.setattr(ev, "SAMPLE_PATH", sp)
    monkeypatch.setattr(ev, "ANN_DIR", tmp_path / "ann")
    monkeypatch.setattr(ev, "GOLD_PATH", tmp_path / "ann" / "gold.json")
    monkeypatch.setattr(ev, "PRED_PATH", tmp_path / "pred.json")
    monkeypatch.setattr(ev, "RUN_PATH", tmp_path / "run.json")
    monkeypatch.setattr(ev, "DETAIL_PATH", tmp_path / "detail.json")
    monkeypatch.setattr(ev, "TALLY_PATH", tmp_path / "tally.json")
    monkeypatch.setattr(ev, "SITE_DATA", tmp_path / "site")


def test_metrics_not_computed_without_inputs(monkeypatch, tmp_path):
    _patch_paths(monkeypatch, tmp_path, [{"passageId": "p1", "stratum": "pliny"}])
    m = ev.evaluate()
    assert m.extraction.overall["part"].f1.status == "not_computed"
    assert "awaiting" in m.extraction.overall["part"].f1.note
    assert m.interAnnotatorAgreement["heat"].status == "not_computed"
    assert m.headlineMatchRate.status == "not_computed" and m.headlineMatchRate.value is None
    C.Metrics.model_validate_json((tmp_path / "site" / "metrics.json").read_text())


def test_metrics_end_to_end_on_synthetic_annotations(monkeypatch, tmp_path):
    sp = [{"passageId": f"p{i}", "stratum": s} for i, s in enumerate(["culpeper1652_virtues", "culpeper1850_dispensatory", "pliny"] * 10)]
    _patch_paths(monkeypatch, tmp_path, sp)
    (tmp_path / "ann").mkdir()

    def ann(name, heat):
        return {"annotator": name, "passages": {p["passageId"]: {"done": True, "recipes": [
            {"recipeSpan": {"quote": "x", "start": 0, "end": 10}, "part": "root", "heat": heat(i), "solvent": ["wine"],
             "ingredients": [{"plantNameAsWritten": "Fennel"}], "plantNameAsWritten": "Fennel"}]} for i, p in enumerate(sp)}}
    (tmp_path / "ann" / "a.json").write_text(json.dumps(ann("a", lambda i: "boiled" if i % 2 else "cold")))
    (tmp_path / "ann" / "b.json").write_text(json.dumps(ann("b", lambda i: "boiled" if i % 3 else "cold")))
    (tmp_path / "ann" / "gold.json").write_text(json.dumps(ann("gold", lambda i: "boiled")))
    preds = [{"passage": {"passageId": p["passageId"]}, "recipeType": "unknown", "part": "root", "heat": "boiled",
              "solvent": ["wine"], "ingredients": [{"plantNameAsWritten": "Fennel"}], "plantNameAsWritten": "Fennel",
              "evidence": {"recipe": [{"quote": "x", "start": 0, "end": 8}]}} for p in sp]
    (tmp_path / "pred.json").write_text(json.dumps(preds))
    m = ev.evaluate()
    assert m.extraction.overall["part"].f1.value == 1.0 and m.extraction.overall["part"].f1.n == 30
    assert m.extraction.bySource["pliny"]["heat"].precision.value == 1.0
    assert m.interAnnotatorAgreement["part"].status == "not_computed"  # single category -> undefined
    assert m.interAnnotatorAgreement["heat"].status == "computed"
    assert m.extraction.recipeDetection["overall"].recall.value == 1.0
