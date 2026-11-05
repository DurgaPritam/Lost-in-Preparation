"""LLM providers for M1. Both receive the same system prompt, messages and JSON schema.

- OllamaProvider: local open-weight model via the Ollama REST API (POST /api/chat) with
  `format` = the JSON schema (structured outputs), temperature 0 and a fixed seed. The exact
  model digest and quantisation are read from /api/tags and recorded in every output.
- AnthropicProvider: Claude via the Anthropic SDK (`output_config.format`), kept for later use.

The provider is chosen in config/pipeline.toml ([m1] provider = "ollama" | "anthropic").
"""
from __future__ import annotations

import json
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from ..paths import ROOT

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
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read())
        except urllib.error.URLError as e:
            raise ProviderError(f"Ollama not reachable at {self.host} ({e}). Start it with `ollama serve`.") from e

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


def from_config(provider: str | None = None, **overrides):
    cfg = load_config()
    name = provider or cfg["provider"]
    opts = {**cfg.get(name, {}), **overrides}
    if name == "ollama":
        return OllamaProvider(**opts)
    if name == "anthropic":
        return AnthropicProvider(**opts)
    raise ValueError(f"unknown provider {name!r}")
