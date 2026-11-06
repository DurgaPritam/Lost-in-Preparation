"""Prompt v2 (Groq free tier): size, unchanged v1, compact retries, and pacing to the per-minute token window."""
from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

import pytest

from lip.m1 import extract as ex
from lip.m1 import providers
from lip.m1.prompt import ANNOTATION_GUIDELINES, build, fewshot, load_passages
from lip.m1.schema import LLMResponse
from lip.m1.spans import check_recipe

PID = "culpeper-1850:herbal:one-blade~2:004"   # v2 worked example: two recipes (single plant + compound)


@pytest.fixture(scope="module")
def passages():
    return load_passages().set_index("passage_id")


def _row(passages, pid):
    r = passages.loc[pid]
    return SimpleNamespace(passage_id=pid, **{k: r[k] for k in r.index})


class FakeOllama:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def __call__(self, path, payload, method="POST"):
        if path == "/api/tags":
            return {"models": [{"name": "m", "digest": "d", "details": {}}]}
        self.calls.append(payload)
        return {"message": {"role": "assistant", "content": json.dumps(self.outputs.pop(0))}, "done_reason": "stop",
                "prompt_eval_count": 10, "eval_count": 5}


def _extractor(outputs):
    fake = FakeOllama(outputs)
    return ex.Extractor(providers.OllamaProvider(model="m", transport=fake), cache=False, prompt_version="v2"), fake


def test_v2_is_small_and_v1_is_unchanged():
    import tiktoken
    from lip.m1.extract import source_titles
    enc = tiktoken.get_encoding("o200k_base")
    v1, v2 = build(source_titles(), "v1"), build(source_titles(), "v2")
    assert len(enc.encode(v2.system)) <= 2500 < len(enc.encode(v1.system))
    assert v2.schema == v1.schema and v2.retry_template and v1.retry_template is None
    assert v2.version.startswith("m1_extract/v2:") and v1.version.startswith("m1_extract/v1:")
    assert subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "prompts/m1_extract/v1"]).returncode == 0
    assert ANNOTATION_GUIDELINES.parent.name == "v1"   # human annotators keep the full guidelines
    g1 = (ANNOTATION_GUIDELINES.parent / "guidelines.md").read_text()
    g2 = open("prompts/m1_extract/v2/guidelines.md").read()
    table = g1[g1.index("## 4. Fields"):g1.index("## 5. Unknown policy")].strip()
    assert table in g2   # field definitions are unchanged, word for word


def test_v2_examples_pass_the_validator(passages):
    assert 1 <= len([e for e in fewshot("v2") if e["output"]["recipes"]]) <= 2
    for exm in fewshot("v2"):
        row = passages.loc[exm["passageId"]]
        for r in LLMResponse.model_validate(exm["output"]).recipes:
            assert check_recipe(r, row.text_clean, row.entry_title).ok


def _good():
    return json.loads(json.dumps(next(e for e in fewshot("v2") if e["passageId"] == PID)["output"]))


def test_compact_retry_sends_only_the_failed_recipe(passages):
    good = _good()
    bad = json.loads(json.dumps(good))
    bad["recipes"][1]["recipeQuote"] = "an ointment made of it"   # not in the passage: breaks the quote rule
    e, fake = _extractor([bad, {"recipes": [good["recipes"][1]]}])
    out = e.extract(_row(passages, PID))
    assert out["attempts"] == 2 and len(out["recipes"]) == 2 and out["rejections"] == []
    second = fake.calls[1]["messages"]
    assert [m["role"] for m in second] == ["system", "user", "user"]          # no previous answer resent
    assert second[1] == fake.calls[0]["messages"][1]                           # the passage, as first sent
    failed = json.loads(second[2]["content"].split("The recipe(s) that failed:\n", 1)[1].split("\n", 1)[0])
    assert len(failed["recipes"]) == 1 and failed["recipes"][0]["recipeQuote"] == "an ointment made of it"
    assert "recipeQuote" in second[2]["content"] or "recipe 1" in second[2]["content"]


def test_schema_failure_retries_the_whole_passage(passages):
    e, fake = _extractor([{"recipes": [{"nonsense": 1}]}, _good()])
    out = e.extract(_row(passages, PID))
    assert out["attempts"] == 2 and len(out["recipes"]) == 2
    retry = fake.calls[1]["messages"][2]["content"]
    assert "did not validate" in retry and "full JSON for the whole passage" in retry


def test_persistent_failure_is_rejected_not_repaired(passages):
    good = _good()
    bad = json.loads(json.dumps(good))
    bad["recipes"][1]["recipeQuote"] = "an ointment made of it"
    e, _ = _extractor([bad] + [{"recipes": [bad["recipes"][1]]}] * ex.MAX_RETRIES)
    out = e.extract(_row(passages, PID))
    assert len(out["recipes"]) == 1 and len(out["rejections"]) == 1 and out["attempts"] == ex.MAX_RETRIES + 1


def test_groq_waits_for_the_next_window_instead_of_sending(monkeypatch, tmp_path):
    monkeypatch.setattr(providers, "GROQ_SELECTION", tmp_path / "sel.json")
    monkeypatch.setattr(providers, "GROQ_RESPONSES", tmp_path / "r")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "Z" * 24)
    hdr = {"x-ratelimit-limit-tokens": "8000", "x-ratelimit-remaining-tokens": "500", "x-ratelimit-reset-tokens": "41.2s"}
    models = {"data": [{"id": "openai/gpt-oss-120b", "created": 1, "active": True}]}
    ok = {"choices": [{"message": {"content": '{"recipes": []}'}, "finish_reason": "stop"}], "usage": {}}
    script = [(200, hdr, json.dumps(models)), (200, hdr, json.dumps(ok))]
    events = []

    def transport(m, p, b):
        events.append(("send", p))
        return script.pop(0)

    prov = providers.GroqProvider(candidates=["openai/gpt-oss-120b"], min_interval_s=0, transport=transport,
                                  sleep=lambda s: events.append(("sleep", s)))
    prov.check()
    prov.complete("system " * 500, [{"role": "user", "content": "passage"}], {"type": "object"})
    i_sleep = next(i for i, e in enumerate(events) if e[0] == "sleep")
    assert events[i_sleep][1] == pytest.approx(41.7) and events[i_sleep + 1] == ("send", "/chat/completions")
