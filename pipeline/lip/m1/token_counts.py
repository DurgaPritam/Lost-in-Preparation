"""Prompt size per version, for METHODS.md and prompts/m1_extract/CHANGELOG.md (never typed by hand).

- local counts: tiktoken o200k_base (the public encoding closest to gpt-oss's tokenizer) of the system prompt and
  of the response schema (Groq counts the schema in the prompt);
- reported counts: the input tokens Groq reported for FIRST-ATTEMPT requests (one request per passage), read from
  the committed extraction cache (data/interim/m1/raw), grouped by prompt version.
Writes data/interim/m1/prompt_token_counts.json.
"""
from __future__ import annotations

import glob
import json

from ..paths import INTERIM, ROOT
from .extract import source_titles
from .prompt import PROMPTS, build

OUT = INTERIM / "m1" / "prompt_token_counts.json"


def run() -> dict:
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    out = {"encoding": "o200k_base (approximation of gpt-oss's tokenizer)", "versions": {}}
    reported: dict[str, list[int]] = {}
    for f in glob.glob(str(INTERIM / "m1" / "raw" / "*.json")):
        d = json.loads(open(f).read())
        if d.get("attempts") == 1 and d.get("run", {}).get("provider") == "groq" and d.get("usage", {}).get("input_tokens"):
            reported.setdefault(d["promptVersion"], []).append(int(d["usage"]["input_tokens"]))
    for vdir in sorted(p for p in PROMPTS.iterdir() if (p / "system.md").exists()):
        p = build(source_titles(), vdir.name)
        sys_t, sch_t = len(enc.encode(p.system)), len(enc.encode(json.dumps(p.schema)))
        r = sorted(reported.get(p.version, []))
        out["versions"][vdir.name] = {
            "promptVersion": p.version, "systemTokens": sys_t, "schemaTokens": sch_t, "fixedTokens": sys_t + sch_t,
            "workedExamples": len(json.loads((vdir / "fewshot.json").read_text())),
            "groqReportedFirstAttemptInputTokens": {"n": len(r), "min": r[0] if r else None, "max": r[-1] if r else None,
                                                    "median": r[len(r) // 2] if r else None}}
    OUT.write_text(json.dumps(out, indent=2))
    return out
