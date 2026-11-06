"""M5 study-method extraction: how a modern study prepared the plant (solvent, heat, part, fresh/dried, filtration).

Same rules as M1 recipes:
- every free-text value (solventText, heatText) and every evidence quote must be found verbatim and continuous in
  the study text (typography-only normalisation, m1/spans.py); ellipses are rejected;
- `evidence` only for the 5 categorical fields, and every categorical value other than "unknown" needs a quote;
- unstated = "unknown" (later counted as unknown, never as a mismatch);
- failures get compact retries (the text, the errors and only the failed preparations), then are REJECTED and
  logged, never repaired;
- every result is cached per (provider, model, model version, decoding, prompt version, study id, text hash).
`ethanolFraction` is parsed by code from the verbatim solventText (HEURISTIC regex; null when not stated).
No provider is called here except through `MethodExtractor.extract`, which tests drive with a fake client.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from contract import models as C

from ..m1.spans import find
from ..paths import INTERIM, ROOT

PROMPT_DIR = ROOT / "prompts" / "m5_methods" / "v1"
OUT = INTERIM / "m5" / "methods_raw"
MAX_RETRIES = 2
CATEGORICAL = ["solvent", "heat", "part", "freshOrDried", "filtered"]
ENUMS = {"solvent": C.ModernSolvent, "heat": C.Heat, "part": C.Part, "freshOrDried": C.FreshOrDried, "filtered": C.Filtered}
ELLIPSIS = re.compile(r"\.\.\.|…")


def _vals(e) -> list[str]:
    return [x.value for x in e]


def response_schema() -> dict:
    ev = {"type": "object", "properties": {"field": {"type": "string", "enum": CATEGORICAL}, "quote": {"type": "string"}},
          "required": ["field", "quote"], "additionalProperties": False}
    props = {"solvent": {"type": "string", "enum": _vals(C.ModernSolvent)}, "solventText": {"type": "string"},
             "heat": {"type": "string", "enum": _vals(C.Heat)}, "heatText": {"type": "string"},
             "part": {"type": "string", "enum": _vals(C.Part)}, "freshOrDried": {"type": "string", "enum": _vals(C.FreshOrDried)},
             "filtered": {"type": "string", "enum": _vals(C.Filtered)}, "evidence": {"type": "array", "items": ev}}
    prep = {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
    return {"type": "object", "properties": {"preparations": {"type": "array", "items": prep}},
            "required": ["preparations"], "additionalProperties": False}


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LLMEvidence(_M):
    field: Literal["solvent", "heat", "part", "freshOrDried", "filtered"]
    quote: str


class LLMPreparation(_M):
    solvent: Literal[tuple(_vals(C.ModernSolvent))]  # type: ignore[valid-type]
    solventText: str
    heat: Literal[tuple(_vals(C.Heat))]  # type: ignore[valid-type]
    heatText: str
    part: Literal[tuple(_vals(C.Part))]  # type: ignore[valid-type]
    freshOrDried: Literal[tuple(_vals(C.FreshOrDried))]  # type: ignore[valid-type]
    filtered: Literal[tuple(_vals(C.Filtered))]  # type: ignore[valid-type]
    evidence: list[LLMEvidence]


class LLMMethods(_M):
    preparations: list[LLMPreparation]


def check(p: LLMPreparation, text: str) -> list[str]:
    """Verbatim and evidence rules; [] = ok."""
    errs = []
    for f in ("solventText", "heatText"):
        v = getattr(p, f)
        if v != C.UNKNOWN:
            if ELLIPSIS.search(v):
                errs.append(f"{f}: ellipsis not allowed")
            elif find(v, text) is None:
                errs.append(f"{f}: quote not found verbatim in text: {v[:80]!r}")
    for e in p.evidence:
        if ELLIPSIS.search(e.quote):
            errs.append(f"evidence[{e.field}]: ellipsis not allowed")
        elif find(e.quote, text) is None:
            errs.append(f"evidence[{e.field}]: quote not found verbatim in text: {e.quote[:80]!r}")
    have = {e.field for e in p.evidence}
    for f in CATEGORICAL:
        if getattr(p, f) != C.UNKNOWN and f not in have:
            errs.append(f"{f}={getattr(p, f)}: no evidence quote given")
    return errs


FRACTION = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*%\s*(?:\(\s*v\s*/\s*v\s*\)\s*)?(?:aqueous\s+)?(?:ethanol|EtOH)"
                      r"|(?:ethanol|EtOH)\s*(?:\(\s*)?(\d{1,3}(?:[.,]\d+)?)\s*%", re.I)


def ethanol_fraction(solvent: str, solvent_text: str) -> float | None:
    """HEURISTIC: '70% ethanol' / 'ethanol 80%' -> 0.7 / 0.8; absolute ethanol -> None unless a number is given."""
    if solvent not in ("ethanol", "hydroethanolic") or solvent_text == C.UNKNOWN:
        return None
    m = FRACTION.search(solvent_text)
    if not m:
        return None
    v = float((m.group(1) or m.group(2)).replace(",", "."))
    return round(v / 100, 3) if 0 < v <= 100 else None


@dataclass
class Study:
    studyId: str      # e.g. "pmid:12345678"
    title: str
    text: str
    source: str       # abstract | pmc_fulltext


def prompt_version() -> str:
    sysm = (PROMPT_DIR / "system.md").read_text()
    retry = (PROMPT_DIR / "retry.md").read_text()
    return "m5_methods/v1:" + hashlib.sha256((sysm + json.dumps(response_schema(), sort_keys=True) + retry).encode()).hexdigest()[:10]


class MethodExtractor:
    def __init__(self, provider, cache: bool = True):
        self.provider, self.cache = provider, cache
        self.system = (PROMPT_DIR / "system.md").read_text()
        self.retry = (PROMPT_DIR / "retry.md").read_text()
        self.schema = response_schema()
        self.version = prompt_version()
        self.run = provider.info()

    def _cache_path(self, s: Study):
        k = json.dumps([self.run.provider, self.run.model, self.run.modelVersion, self.run.decoding, self.version,
                        s.studyId, hashlib.sha256(s.text.encode()).hexdigest()], sort_keys=True, default=str)
        return OUT / f"{hashlib.sha256(k.encode()).hexdigest()[:24]}.json"

    def _user(self, s: Study, species: str) -> dict:
        return {"role": "user", "content": f"<species>{species}</species>\n<title>{s.title}</title>\n<text source=\"{s.source}\">\n{s.text}\n</text>"}

    def _retry_msg(self, errors: list[str], failed: list[dict] | None) -> dict:
        if failed:
            fj = "The preparation(s) that failed:\n" + json.dumps({"preparations": failed}, ensure_ascii=False, separators=(",", ":"))
            ask = 'Return JSON whose "preparations" list contains only the corrected version of each failed preparation.'
        else:
            fj = "(The output did not validate against the schema, so nothing could be read.)"
            ask = "Return the full JSON for the whole text."
        return {"role": "user", "content": self.retry.replace("{{ERRORS}}", "\n".join(f"- {e}" for e in errors))
                .replace("{{FAILED}}", fj).replace("{{ASK}}", ask)}

    def extract(self, s: Study, species: str) -> dict:
        cp = self._cache_path(s)
        if self.cache and cp.exists():
            return json.loads(cp.read_text())
        original = self._user(s, species)
        accepted: list[LLMPreparation] = []
        failures: list[dict] = []
        mode, retry, attempts, stop, usage = "full", None, 0, None, {}
        for attempt in range(MAX_RETRIES + 1):
            attempts = attempt + 1
            comp = self.provider.complete(self.system, [original] if retry is None else [original, retry], self.schema)
            for k, v in comp.usage.items():
                usage[k] = usage.get(k, 0) + v
            stop = comp.stop
            if stop in ("refusal", "max_tokens"):
                failures = (failures if mode == "fix" else []) + [{"preparation": None, "errors": [f"stop={stop}"]}]
                break
            try:
                parsed = LLMMethods.model_validate_json(comp.text)
            except ValidationError as e:
                err = f"schema: {e.errors()[:3]}"
                if mode == "full":
                    failures, retry = [{"preparation": None, "errors": [err]}], self._retry_msg([err], None)
                else:
                    retry = self._retry_msg([err], [f["preparation"] for f in failures if f["preparation"]])
                continue
            res = [(p, check(p, s.text)) for p in parsed.preparations]
            ok = [p for p, e in res if not e]
            bad = [{"preparation": p.model_dump(), "errors": e} for p, e in res if e]
            if mode == "full":
                accepted, failures = ok, bad
            else:
                accepted += ok
                failures = bad if (ok or bad) else failures
            if not failures:
                break
            mode = "fix"
            retry = self._retry_msg([f"preparation {i + 1}: " + "; ".join(f["errors"]) for i, f in enumerate(failures)],
                                    [f["preparation"] for f in failures])
        preps = []
        for p in accepted:
            d = p.model_dump()
            d["ethanolFraction"] = ethanol_fraction(p.solvent, p.solventText)
            d["unknownFields"] = [f for f in CATEGORICAL if d[f] == C.UNKNOWN]
            d["evidenceSource"] = s.source
            preps.append(d)
        result = {"studyId": s.studyId, "species": species, "preparations": preps, "rejections": failures,
                  "attempts": attempts, "stop": stop, "usage": usage, "run": asdict(self.run), "promptVersion": self.version}
        if self.cache:
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str))
        return result
