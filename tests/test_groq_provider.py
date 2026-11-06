"""Groq provider: rate limiting, caching, offline reproduction, model selection, and key hygiene (no network)."""
from __future__ import annotations

import json
import subprocess

import pytest

from lip.m1 import providers as P

FAKE_KEY = "gsk_" + "T" * 24  # built at run time so no key-like literal sits in the repository
SCHEMA = {"type": "object", "properties": {"recipes": {"type": "array", "items": {"type": "string"}}},
          "required": ["recipes"], "additionalProperties": False}
MODELS = {"object": "list", "data": [{"id": "llama-3.1-8b-instant", "created": 1, "active": True},
                                     {"id": "openai/gpt-oss-120b", "created": 1754408224, "owned_by": "OpenAI", "active": True,
                                      "context_window": 131072}]}
OK = {"choices": [{"message": {"content": '{"recipes": []}'}, "finish_reason": "stop"}],
      "usage": {"prompt_tokens": 100, "completion_tokens": 10, "prompt_tokens_details": {"cached_tokens": 64}}}


class Fake:
    def __init__(self, script):
        self.script, self.calls = list(script), []

    def __call__(self, method, path, body):
        self.calls.append((method, path, body))
        return self.script.pop(0)


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(P, "GROQ_SELECTION", tmp_path / "sel.json")
    monkeypatch.setattr(P, "GROQ_RESPONSES", tmp_path / "responses")
    monkeypatch.setattr(P, "ROOT", tmp_path)
    monkeypatch.setenv("GROQ_API_KEY", FAKE_KEY)
    return tmp_path


def _prov(script, **kw):
    sleeps = []
    t = Fake(script)
    p = P.GroqProvider(candidates=["openai/gpt-oss-120b", "openai/gpt-oss-20b"], min_interval_s=0, transport=t,
                       sleep=sleeps.append, **kw)
    return p, t, sleeps


def test_selects_first_live_candidate_and_records_it(env):
    p, t, _ = _prov([(200, {}, json.dumps(MODELS))])
    p.check()
    info = p.info()
    assert info.provider == "groq" and info.model == "openai/gpt-oss-120b"
    assert info.modelVersion == "openai/gpt-oss-120b@created=1754408224" and info.decoding["selectedOn"]
    assert info.decoding["temperature"] == 0.0 and info.decoding["responseFormat"] == "json_schema (strict)"
    sel = json.loads((env / "sel.json").read_text())
    assert sel["model"] == "openai/gpt-oss-120b" and "liveModels" in sel and FAKE_KEY not in json.dumps(sel)


def test_backoff_on_429_then_success_and_strict_schema_body(env):
    p, t, sleeps = _prov([(200, {}, json.dumps(MODELS)), (429, {"retry-after": "3"}, '{"error":{"message":"slow down"}}'),
                          (200, {"x-ratelimit-remaining-tokens": "7000", "x-ratelimit-reset-tokens": "7.66s"}, json.dumps(OK))])
    p.check()
    c = p.complete("sys", [{"role": "user", "content": "x"}], SCHEMA)
    assert c.text == '{"recipes": []}' and c.stop == "end" and c.usage["cache_read_input_tokens"] == 64
    assert 3.0 in sleeps
    body = t.calls[-1][2]
    assert body["temperature"] == 0.0 and body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True and body["response_format"]["json_schema"]["schema"] == SCHEMA
    assert body["reasoning_effort"] == "low"


def test_long_rate_limit_wait_stops_with_resume_message(env):
    p, _, _ = _prov([(200, {}, json.dumps(MODELS)), (429, {"retry-after": "3600"}, "{}")])
    p.check()
    with pytest.raises(P.ProviderError, match="re-run later"):
        p.complete("sys", [{"role": "user", "content": "x"}], SCHEMA)


def test_every_response_is_cached_and_never_resent(env):
    p, t, _ = _prov([(200, {}, json.dumps(MODELS)), (200, {}, json.dumps(OK))])
    p.check()
    a = p.complete("sys", [{"role": "user", "content": "x"}], SCHEMA)
    b = p.complete("sys", [{"role": "user", "content": "x"}], SCHEMA)  # served from the cache
    assert a.text == b.text and len(t.calls) == 2
    stored = next((env / "responses").glob("*.json")).read_text()
    assert FAKE_KEY not in stored and "Authorization" not in stored


def test_offline_reproduction_without_a_key(env, monkeypatch):
    p, _, _ = _prov([(200, {}, json.dumps(MODELS)), (200, {}, json.dumps(OK))])
    p.check()
    p.complete("sys", [{"role": "user", "content": "x"}], SCHEMA)
    monkeypatch.delenv("GROQ_API_KEY")
    q = P.GroqProvider(candidates=["openai/gpt-oss-120b"], min_interval_s=0)  # real transport: would need a key
    q.check()  # uses the recorded selection
    assert q.info().modelVersion == "openai/gpt-oss-120b@created=1754408224"
    assert q.complete("sys", [{"role": "user", "content": "x"}], SCHEMA).text == '{"recipes": []}'  # cached
    with pytest.raises(P.ProviderError, match="GROQ_API_KEY is not set"):
        q.complete("sys", [{"role": "user", "content": "new"}], SCHEMA)


def test_errors_never_contain_the_key(env):
    p, _, _ = _prov([(200, {}, json.dumps(MODELS)), (401, {}, json.dumps({"error": {"message": f"Invalid API Key {FAKE_KEY}"}}))])
    p.check()
    with pytest.raises(P.ProviderError) as e:
        p.complete("sys", [{"role": "user", "content": "x"}], SCHEMA)
    assert FAKE_KEY not in str(e.value) and "REDACTED" in str(e.value)
    assert FAKE_KEY not in repr(p)


def test_key_from_dotenv(env, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    (env / ".env").write_text(f'# local\nGROQ_API_KEY="{FAKE_KEY}"\n')
    assert P.groq_api_key() == FAKE_KEY


def test_duration_headers():
    assert P._duration_s("7.66s") == pytest.approx(7.66) and P._duration_s("2m59.56s") == pytest.approx(179.56)
    assert P._duration_s("350ms") == pytest.approx(0.35) and P._duration_s("2") == 2.0


def test_groq_is_default_and_env_is_ignored():
    assert P.load_config()["provider"] == "groq"
    assert subprocess.run(["git", "check-ignore", "-q", ".env"]).returncode == 0


def test_no_key_like_string_in_tracked_files():
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
    for f in files:
        try:
            text = open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        assert not P.KEY_PATTERN.search(text), f
