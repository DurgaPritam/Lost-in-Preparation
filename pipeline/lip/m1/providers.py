"""LLM providers for M1. All receive the same system prompt, messages and JSON schema.

- GroqProvider (default): hosted open-weight model via Groq's OpenAI-compatible API, strict JSON-schema
  structured outputs, temperature 0, rate-limited, every response cached (committed) so results reproduce
  without a key. See the class docstring.
- OllamaProvider: local open-weight model via the Ollama REST API (POST /api/chat) with
  `format` = the JSON schema (structured outputs), temperature 0 and a fixed seed. The exact
  model digest and quantisation are read from /api/tags and recorded in every output.
- AnthropicProvider: Claude via the Anthropic SDK (`output_config.format`), kept for later use.

The provider is chosen in config/pipeline.toml ([m1] provider = "groq" | "ollama" | "anthropic").
Ollama was tried on 2026-11-06 and froze the 16 GB development machine; its code is kept but it is not the default.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import tomllib
import urllib.error
import urllib.request
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any

from ..paths import INTERIM, ROOT

CONFIG = ROOT / "config" / "pipeline.toml"


def load_config() -> dict:
    with CONFIG.open("rb") as fh:
        return tomllib.load(fh)["m1"]


@dataclass
class Completion:
    text: str
    stop: str  # end | max_tokens | refusal
    usage: dict[str, int]
    assistant_message: dict  # appended verbatim to history on a retry


@dataclass
class RunInfo:
    provider: str
    model: str
    modelVersion: str | None
    decoding: dict[str, Any] = field(default_factory=dict)


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    name = "ollama"

    def __init__(self, model: str, host: str = "http://localhost:11434", num_ctx: int = 16384,
                 num_predict: int = 4096, temperature: float = 0.0, seed: int = 0, think: bool | None = None,
                 timeout: int = 600, transport=None):
        self.model, self.host = model, host.rstrip("/")
        self.options = {"temperature": temperature, "seed": seed, "num_ctx": num_ctx, "num_predict": num_predict}
        self.think, self.timeout = think, timeout
        self._post = transport or self._http_post
        self._digest: str | None = None
        self._details: dict = {}

    def _http_post(self, path: str, payload: dict | None, method: str = "POST") -> dict:
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.host + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        import time
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:  # the server is up but the request failed: report its own message
                body = e.read().decode("utf-8", "replace")[:500]
                if e.code >= 500 and attempt == 0:
                    time.sleep(5)
                    continue
                raise ProviderError(f"Ollama returned HTTP {e.code} for {path}: {body or e.reason}") from e
            except urllib.error.URLError as e:
                raise ProviderError(f"Ollama not reachable at {self.host} ({e}). Start it with `ollama serve`.") from e
        raise ProviderError(f"Ollama request to {path} failed")

    def check(self) -> None:
        tags = self._post("/api/tags", None, "GET")
        for m in tags.get("models", []):
            if m.get("name") == self.model or m.get("model") == self.model:
                self._digest, self._details = m.get("digest"), m.get("details", {})
                return
        raise ProviderError(f"model {self.model!r} is not pulled. Run `ollama pull {self.model}`.")

    def info(self) -> RunInfo:
        if self._digest is None:
            self.check()
        dec = {**self.options, "quantization": self._details.get("quantization_level"),
               "parameterSize": self._details.get("parameter_size")}
        if self.think is not None:
            dec["think"] = self.think
        return RunInfo(self.name, self.model, self._digest, dec)

    def complete(self, system: str, messages: list[dict], schema: dict) -> Completion:
        payload = {"model": self.model, "messages": [{"role": "system", "content": system}, *messages],
                   "format": schema, "stream": False, "options": self.options}
        if self.think is not None:
            payload["think"] = self.think
        r = self._post("/api/chat", payload)
        text = r.get("message", {}).get("content", "")
        stop = "max_tokens" if r.get("done_reason") == "length" else "end"
        usage = {"input_tokens": r.get("prompt_eval_count", 0) or 0, "output_tokens": r.get("eval_count", 0) or 0}
        return Completion(text, stop, usage, {"role": "assistant", "content": text})


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "high", fallbacks: bool = True,
                 max_tokens: int = 16000, client=None):
        self.model, self.effort, self.fallbacks, self.max_tokens = model, effort, fallbacks, max_tokens
        if client is None:
            import anthropic
            client = anthropic.Anthropic()
        self.client = client

    def check(self) -> None:
        return None

    def info(self) -> RunInfo:
        return RunInfo(self.name, self.model, None, {"effort": self.effort, "thinking": "adaptive",
                                                     "fallbacks": "default" if self.fallbacks else None})

    def complete(self, system: str, messages: list[dict], schema: dict) -> Completion:
        kw = dict(model=self.model, max_tokens=self.max_tokens,
                  system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                  messages=messages,
                  output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}})
        if self.fallbacks:
            resp = self.client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kw)
        else:
            resp = self.client.messages.create(**kw)
        text = next((b.text for b in resp.content if b.type == "text"), "")
        stop = {"refusal": "refusal", "max_tokens": "max_tokens"}.get(resp.stop_reason, "end")
        usage = {k: getattr(resp.usage, k, 0) or 0 for k in
                 ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")}
        return Completion(text, stop, usage, {"role": "assistant", "content": resp.content})


# --- Groq --------------------------------------------------------------------------------------------

GROQ_BASE = "https://api.groq.com/openai/v1"
GROQ_SELECTION = INTERIM / "m1" / "groq_model_selection.json"   # committed: which model, when, from which list
GROQ_RESPONSES = INTERIM / "m1" / "groq_responses"              # committed: one file per request (no key, no headers)
KEY_PATTERN = re.compile(r"gsk_[A-Za-z0-9]{16,}")


def groq_api_key() -> str | None:
    """GROQ_API_KEY from the environment, else from a .env file at the repository root. Never logged."""
    k = os.environ.get("GROQ_API_KEY", "").strip()
    if k:
        return k
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?GROQ_API_KEY\s*=\s*(.*)\s*$", line)
            if m:
                return m.group(1).strip().strip('"').strip("'") or None
    return None


def _redact(s: str) -> str:
    return KEY_PATTERN.sub("gsk_[REDACTED]", s)


def _duration_s(v: str | None) -> float | None:
    """Groq reset headers: '7.66s', '2m59.56s', '350ms', '1h2m3s'."""
    if not v:
        return None
    total, found = 0.0, False
    for num, unit in re.findall(r"([\d.]+)(ms|h|m|s)", v):
        found = True
        total += float(num) * {"ms": 0.001, "s": 1, "m": 60, "h": 3600}[unit]
    if found:
        return total
    try:
        return float(v)
    except ValueError:
        return None


class GroqProvider:
    """Groq (OpenAI-compatible chat completions) with strict JSON-schema structured outputs.

    - Key: GROQ_API_KEY (environment or .env). It is sent only in the Authorization header and never
      written to code, config, logs, error messages, caches or outputs.
    - Model: `model` in config/pipeline.toml, or, when empty, the first of `candidates` present in the live
      GET /models list; the choice, the list snapshot and the date are written to GROQ_SELECTION. The model
      version recorded in every output is "<id>@created=<unix time>"; the selection date is in `decoding`.
    - Decoding: temperature 0, seed 0, response_format json_schema strict (the same schema as every provider).
    - Request size: Groq counts input + the full max_completion_tokens against tokens-per-minute (TPM), so each
      request's completion cap is lowered to fit the TPM limit reported in x-ratelimit-limit-tokens (never below
      MIN_COMPLETION); a 413 "Request too large" is retried once with the cap Groq's own numbers allow. The
      configured maximum stays in the cache key and `decoding`; the cap actually sent is stored with each response.
    - Rate limits (free tier): a minimum interval between requests; pacing from x-ratelimit-remaining-tokens /
      x-ratelimit-reset-tokens; on 429, wait `retry-after` (or the reset header) with exponential backoff,
      and stop with a clear message if the wait is longer than `max_wait_s` (e.g. a daily limit).
    - Cache: every request/response pair is stored in GROQ_RESPONSES keyed by a hash of the request body, so
      no request is ever sent twice and runs reproduce without a key (offline mode serves only cached responses).
    """
    name = "groq"

    def __init__(self, model: str = "", candidates: list[str] | None = None, temperature: float = 0.0, seed: int = 0,
                 max_completion_tokens: int = 8192, reasoning_effort: str | None = "low", min_interval_s: float = 2.0,
                 max_wait_s: float = 300.0, max_retries: int = 6, transport=None, sleep=time.sleep):
        self.model = model or ""
        self.candidates = candidates or []
        self.options = {"temperature": temperature, "seed": seed, "max_completion_tokens": max_completion_tokens}
        self.reasoning_effort = reasoning_effort
        self.min_interval_s, self.max_wait_s, self.max_retries = min_interval_s, max_wait_s, max_retries
        self._transport = transport or self._http
        self._sleep = sleep
        self._last = 0.0
        self._selection: dict | None = None
        self._remaining_tokens: int | None = None
        self._reset_tokens_s: float | None = None
        self._tpm_limit: int | None = None
        self._last_cap: int | None = None

    def __repr__(self) -> str:  # never shows the key
        return f"GroqProvider(model={self.model!r})"

    # -- transport -------------------------------------------------------------------------------------------
    def _http(self, method: str, path: str, body: dict | None) -> tuple[int, dict, str]:
        key = groq_api_key()
        if not key:
            raise ProviderError("GROQ_API_KEY is not set (environment or .env); only cached responses are available.")
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(GROQ_BASE + path, data=data, method=method,
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                              "User-Agent": "LostInPreparation/0.3 (+https://github.com/DurgaPritam/Lost-in-Preperation)"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read().decode("utf-8", "replace")
        except urllib.error.URLError as e:
            raise ProviderError(_redact(f"Groq not reachable ({e.reason})")) from None

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        backoff = 2.0
        for attempt in range(self.max_retries + 1):
            wait = self.min_interval_s - (time.monotonic() - self._last)
            if wait > 0:
                self._sleep(wait)
            if body is not None and self._remaining_tokens is not None and self._reset_tokens_s:
                # Groq counts the input AND the full max_completion_tokens against tokens-per-minute
                est = self._input_tokens(body) + int(body.get("max_completion_tokens", 0))
                if self._remaining_tokens < est:
                    self._sleep(min(self._reset_tokens_s, self.max_wait_s))
            status, headers, text = self._transport(method, path, body)
            self._last = time.monotonic()
            self._last_cap = (body or {}).get("max_completion_tokens")
            if "x-ratelimit-limit-tokens" in headers:
                try:
                    self._tpm_limit = int(float(headers["x-ratelimit-limit-tokens"]))
                except ValueError:
                    pass
            if "x-ratelimit-remaining-tokens" in headers:
                try:
                    self._remaining_tokens = int(float(headers["x-ratelimit-remaining-tokens"]))
                except ValueError:
                    self._remaining_tokens = None
                self._reset_tokens_s = _duration_s(headers.get("x-ratelimit-reset-tokens"))
            if status == 200:
                return json.loads(text)
            if status == 429 or status >= 500:
                ra = _duration_s(headers.get("retry-after")) or _duration_s(headers.get("x-ratelimit-reset-tokens")) or backoff
                if ra > self.max_wait_s:
                    raise ProviderError(f"Groq rate limit: retry after {ra:.0f} s (beyond max_wait_s={self.max_wait_s:.0f}; "
                                        "probably a daily limit). Completed passages are cached; re-run later to resume.")
                if attempt < self.max_retries:
                    self._sleep(max(ra, backoff))
                    backoff = min(backoff * 2, 60.0)
                    continue
            msg = text[:400]
            err = {}
            try:
                err = json.loads(text).get("error", {}) or {}
                msg = err.get("message", msg)
            except (ValueError, AttributeError):
                pass
            m413 = re.search(r"Limit (\d+), Requested (\d+)", str(msg)) if status == 413 else None
            if m413 and body is not None and attempt < self.max_retries:
                over = int(m413.group(2)) - int(m413.group(1))
                cap = int(body.get("max_completion_tokens", 0)) - over - 150
                if cap >= self.MIN_COMPLETION:
                    body = {**body, "max_completion_tokens": cap}
                    continue
                raise ProviderError(f"Groq: request too large for the tokens-per-minute limit even with {self.MIN_COMPLETION} "
                                    "completion tokens (prompt too long for this tier).")
            if status == 400 and "failed_generation" in err:
                # the model's output broke the schema: hand it back to the extractor's normal validation / retry path
                return {"_schemaError": _redact(str(msg))[:600], "choices": [{"message": {"content": err.get("failed_generation") or ""},
                                                                         "finish_reason": "schema_error"}]}
            raise ProviderError(_redact(f"Groq HTTP {status} for {path}: {msg}"))
        raise ProviderError(f"Groq request to {path} failed after {self.max_retries + 1} attempts")

    # -- model selection -------------------------------------------------------------------------------------
    def check(self) -> None:
        rec = json.loads(GROQ_SELECTION.read_text()) if GROQ_SELECTION.exists() else None
        if not groq_api_key():
            if not rec or (self.model and rec["model"] != self.model):
                raise ProviderError("GROQ_API_KEY is not set and no recorded model selection matches; set the key to select a model.")
            self._selection, self.model = rec, rec["model"]
            return
        live = self._request("GET", "/models")["data"]
        ids = {m["id"]: m for m in live}
        model = self.model or (rec["model"] if rec and rec["model"] in ids else None) or \
            next((c for c in self.candidates if c in ids and ids[c].get("active", True)), None)
        if not model:
            raise ProviderError("none of the configured Groq candidates is in the live model list: "
                                + ", ".join(self.candidates))
        if model not in ids:
            raise ProviderError(f"Groq model {model!r} is not in the live model list (retired?). Cached responses still reproduce.")
        if rec and rec["model"] == model and rec["created"] == ids[model].get("created"):
            self._selection = rec
        else:
            self._selection = {"model": model, "created": ids[model].get("created"), "ownedBy": ids[model].get("owned_by"),
                               "contextWindow": ids[model].get("context_window"),
                               "selectedOn": datetime.now(timezone.utc).date().isoformat(),
                               "rule": "config model if set, else the first configured candidate present and active in GET /models",
                               "candidates": self.candidates,
                               "liveModels": sorted({m["id"]: m.get("created") for m in live}.items())}
            GROQ_SELECTION.parent.mkdir(parents=True, exist_ok=True)
            GROQ_SELECTION.write_text(json.dumps(self._selection, indent=2))
        self.model = model

    def info(self) -> RunInfo:
        if self._selection is None:
            self.check()
        sel = self._selection
        dec = {**self.options, "responseFormat": "json_schema (strict)", "selectedOn": sel["selectedOn"]}
        if self._reasoning():
            dec["reasoningEffort"] = self.reasoning_effort
        return RunInfo(self.name, sel["model"], f"{sel['model']}@created={sel['created']}", dec)

    MIN_COMPLETION = 1024
    TPM_MARGIN = 250

    @staticmethod
    def _input_tokens(body: dict) -> int:
        """Conservative input-token estimate (~3.2 characters per token for this English/JSON mix)."""
        return int(len(json.dumps(body.get("messages", []), ensure_ascii=False)) / 3.2) + 50

    def _cap(self, body: dict) -> dict:
        """Keep requests small: cap max_completion_tokens so input + cap fits under the tokens-per-minute limit."""
        limit = self._tpm_limit
        if not limit:
            return body
        room = limit - self._input_tokens(body) - self.TPM_MARGIN
        cap = max(self.MIN_COMPLETION, min(int(body["max_completion_tokens"]), room))
        return {**body, "max_completion_tokens": cap}

    def _reasoning(self) -> bool:
        return bool(self.reasoning_effort) and self.model.startswith("openai/gpt-oss")

    # -- completion -------------------------------------------------------------------------------------------
    def complete(self, system: str, messages: list[dict], schema: dict) -> Completion:
        if self._selection is None:
            self.check()
        body = {"model": self.model, "messages": [{"role": "system", "content": system}, *messages], **self.options,
                "response_format": {"type": "json_schema", "json_schema": {"name": "m1_recipes", "strict": True, "schema": schema}}}
        if self._reasoning():
            body["reasoning_effort"] = self.reasoning_effort
        key = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]
        cp = GROQ_RESPONSES / f"{key}.json"
        if cp.exists():
            r = json.loads(cp.read_text())["response"]
        else:
            sent = self._cap(body)  # the TPM limit is learned from check()'s GET /models headers; a 413 retry covers the rest
            r = self._request("POST", "/chat/completions", sent)
            r = {**r, "_maxCompletionTokensSent": self._last_cap}
            GROQ_RESPONSES.mkdir(parents=True, exist_ok=True)
            cp.write_text(json.dumps({"model": self.model, "requestSha256": key,
                                      "retrievedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                      "response": r}, ensure_ascii=False, indent=1))
        ch = (r.get("choices") or [{}])[0]
        text = (ch.get("message") or {}).get("content") or ""
        stop = {"length": "max_tokens", "content_filter": "refusal"}.get(ch.get("finish_reason"), "end")
        if r.get("_schemaError") and not text.strip():
            text = "{}"  # nothing generated: fails validation and triggers the extractor's retry with feedback
        u = r.get("usage") or {}
        usage = {"input_tokens": u.get("prompt_tokens", 0) or 0, "output_tokens": u.get("completion_tokens", 0) or 0}
        cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens")
        if cached:
            usage["cache_read_input_tokens"] = cached
        reasoning = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
        if reasoning:
            usage["reasoning_tokens"] = reasoning
        return Completion(text, stop, usage, {"role": "assistant", "content": text})


def from_config(provider: str | None = None, **overrides):
    cfg = load_config()
    name = provider or cfg["provider"]
    opts = {**cfg.get(name, {}), **overrides}
    if name == "groq":
        return GroqProvider(**opts)
    if name == "ollama":
        return OllamaProvider(**opts)
    if name == "anthropic":
        return AnthropicProvider(**opts)
    raise ValueError(f"unknown provider {name!r}")
