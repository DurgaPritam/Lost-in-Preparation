"""M1 extraction written directly by Claude in a Claude Code session (no API calls).

Each batch file data/m1_session/<scope>/batch_NN.json holds the extractions exactly as written, one LLMResponse
({"recipes": [...]}) per passage, following prompt v3 and the response schema. This module:
  - validates every passage against the response schema (a passage that fails is rejected whole, logged);
  - runs the unchanged M1 verbatim-quote validator (m1/spans.py) on every recipe, ONE attempt only: there are no
    retries, because a retry that reads the validator's message and edits the output would be repair.
    A recipe that fails is rejected and logged, never repaired;
  - converts accepted recipes to the recipes.json contract shape with the same code as the API extractor;
  - records provenance: provider "Claude via Claude Code session", the model, the prompt version and the date.
The batch files are committed, so the outputs are reproducible and inspectable.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from pydantic import ValidationError

from ..paths import INTERIM, ROOT
from .extract import Extractor
from .prompt import heading_of, load_passages
from .providers import RunInfo
from .schema import LLMResponse
from .spans import check_recipe

SESSION_DIR = ROOT / "data" / "m1_session"
OUT = INTERIM / "m1"
PROVIDER = "Claude via Claude Code session"
MODEL = "claude-opus-5-5"
PROMPT = "v3"


class _SessionProvider:
    """Carries provenance only; never called."""

    def __init__(self, written_on: str):
        self.written_on = written_on

    def info(self) -> RunInfo:
        return RunInfo(PROVIDER, MODEL, MODEL, {
            "mode": "written directly by the model in an interactive Claude Code session, following the prompt; "
                    "no API call, no sampling parameters; one attempt per passage, no retries",
            "writtenOn": self.written_on})

    def complete(self, *a, **k):
        raise RuntimeError("session extractions are written, not requested")


def batches(scope: str) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((SESSION_DIR / scope).glob("batch_*.json"))]


def ingest(scope: str) -> dict:
    df = load_passages().set_index("passage_id")
    bs = batches(scope)
    recipes, rejections, per_batch = [], [], []
    for b in bs:
        ex = Extractor(_SessionProvider(b["writtenOn"]), cache=False, prompt_version=PROMPT)
        if b["promptVersion"] != ex.prompt.version:
            raise ValueError(f"batch {b['batch']}: written for {b['promptVersion']}, prompt is now {ex.prompt.version}")
        n_acc = n_rej = 0
        for pid, out in b["passages"].items():
            row = df.loc[pid]
            r = type("Row", (), {"passage_id": pid, **row.to_dict()})()
            try:
                parsed = LLMResponse.model_validate(out)
            except ValidationError as e:
                rejections.append({"passageId": pid, "batch": b["batch"], "recipe": None, "errors": [f"schema: {e.errors()[:3]}"]})
                n_rej += 1
                continue
            accepted = []
            for rec in parsed.recipes:
                c = check_recipe(rec, row["text_clean"], heading_of(r))
                if c.ok:
                    accepted.append((rec, c))
                else:
                    rejections.append({"passageId": pid, "batch": b["batch"], "recipe": rec.model_dump(), "errors": c.errors})
                    n_rej += 1
            recipes += [ex.to_contract(r, rec, c, i) for i, (rec, c) in enumerate(accepted)]
            n_acc += len(accepted)
        per_batch.append({"batch": b["batch"], "passages": len(b["passages"]), "accepted": n_acc, "rejected": n_rej,
                          "writtenOn": b["writtenOn"]})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"predictions_{scope}.json").write_text(json.dumps(recipes, ensure_ascii=False, indent=1))
    with (OUT / f"rejections_{scope}.jsonl").open("w") as fh:
        for rj in rejections:
            fh.write(json.dumps(rj, ensure_ascii=False) + "\n")
    summary = {"scope": scope, "run": asdict(_SessionProvider("see batches").info()), "promptVersion": f"m1_extract/{PROMPT}",
               "passages": sum(x["passages"] for x in per_batch), "recipesAccepted": len(recipes),
               "recipesRejected": sum(1 for x in rejections if x["recipe"] is not None),
               "passagesFailedWhole": sum(1 for x in rejections if x["recipe"] is None), "batches": per_batch,
               "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (OUT / f"run_{scope}.json").write_text(json.dumps(summary, indent=2))
    return summary


def passages_for(scope: str) -> list[str]:
    """The passage IDs a scope covers: 'sample' = the 50-passage gold sample."""
    if scope == "sample":
        from .sample import SAMPLE_PATH
        return [p["passageId"] for p in json.loads(SAMPLE_PATH.read_text())["passages"]]
    raise ValueError(scope)


def show(scope: str, start: int, n: int) -> str:
    """Render passages for writing a batch: context exactly as the prompt's user message gives it."""
    from .extract import source_titles
    from .prompt import render_user
    titles = dict(source_titles())
    df = load_passages().set_index("passage_id")
    out = []
    for pid in passages_for(scope)[start:start + n]:
        row = df.loc[pid]
        r = type("Row", (), {"passage_id": pid, **row.to_dict()})()
        out.append(f"### {pid}\n" + render_user(r, titles.get(row["source_id"], "")))
    return "\n\n".join(out)
