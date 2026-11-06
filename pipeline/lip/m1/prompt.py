"""Versioned M1 prompt: system text + guidelines + Culpeper few-shot examples + response schema.

promptVersion = "<dir>:<sha256 of rendered system prompt + schema (+ retry template)>[:10]", so any edit to
the guidelines, examples, schema or retry template yields a new version string recorded in provenance.

The version in use is `[m1] prompt` in config/pipeline.toml ("v1" or "v2"). v1 is kept unchanged.
v2 (2026-11-06): the fixed prompt is cut to fit the Groq free tier's tokens-per-minute limit
(prompts/m1_extract/CHANGELOG.md), examples are rendered as compact JSON, and retries are COMPACT
(retry.md): a retry sends the passage, the validation errors and only the failed recipes, never the full
previous answer.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from ..paths import INTERIM, ROOT
from .schema import response_schema

PROMPTS = ROOT / "prompts" / "m1_extract"


def prompt_version_dir() -> str:
    import tomllib
    with (ROOT / "config" / "pipeline.toml").open("rb") as fh:
        return tomllib.load(fh).get("m1", {}).get("prompt", "v1")


PROMPT_DIR = PROMPTS / prompt_version_dir()        # the configured version (extraction)
PROMPT_NAME = f"m1_extract/{PROMPT_DIR.name}"
ANNOTATION_GUIDELINES = PROMPTS / "v1" / "guidelines.md"  # human annotators always use the full v1 guidelines


def prompt_dir(version: str | None = None):
    return PROMPTS / version if version else PROMPT_DIR


def load_passages() -> pd.DataFrame:
    return pd.read_parquet(INTERIM / "passages.parquet")


def heading_of(row) -> str:
    return row.entry_title if isinstance(row.entry_title, str) else ""


def render_user(row, source_title: str) -> str:
    loc = [f"source: {row.source_id} — {source_title}", f"part: {row.part}"]
    if pd.notna(row.book):
        loc.append(f"book: {int(row.book)}, chapter: {row.chapter}")
    loc.append(f"entry heading: {heading_of(row) or '(none)'}")
    if isinstance(row.subsection, str):
        loc.append(f"subsection: {row.subsection}")
    return "<context>\n" + "\n".join(loc) + "\n</context>\n<passage>\n" + row.text_clean + "\n</passage>"


def fewshot(version: str | None = None) -> list[dict]:
    return json.loads((prompt_dir(version) / "fewshot.json").read_text())


def fewshot_ids() -> set[str]:
    """Passages used as worked examples in ANY prompt version (all are excluded from samples)."""
    return {ex["passageId"] for d in sorted(PROMPTS.iterdir()) if (d / "fewshot.json").exists() for ex in fewshot(d.name)}


@dataclass(frozen=True)
class Prompt:
    system: str
    schema: dict
    version: str
    retry_template: str | None = None   # None: v1 behaviour (append the previous answer); else compact retries


@lru_cache(maxsize=4)
def build(source_titles: tuple[tuple[str, str], ...], version: str | None = None) -> Prompt:
    pdir = prompt_dir(version)
    titles = dict(source_titles)
    passages = load_passages().set_index("passage_id")
    blocks = []
    for i, ex in enumerate(fewshot(version), 1):
        row = passages.loc[ex["passageId"]]
        user = render_user(_Row(ex["passageId"], row), titles.get(row["source_id"], ""))
        out = (json.dumps(ex["output"], ensure_ascii=False, indent=1) if pdir.name == "v1"
               else json.dumps(ex["output"], ensure_ascii=False, separators=(",", ":")))
        blocks.append(f"<example index=\"{i}\">\n{user}\n<output>\n" + out + "\n</output>\n</example>")
    system = (
        (pdir / "system.md").read_text()
        .replace("{{GUIDELINES}}", (pdir / "guidelines.md").read_text().strip())
        .replace("{{EXAMPLES}}", "\n\n".join(blocks))
    )
    schema = response_schema()
    retry_p = pdir / "retry.md"
    retry = retry_p.read_text() if retry_p.exists() else None
    digest = hashlib.sha256((system + json.dumps(schema, sort_keys=True) + (retry or "")).encode()).hexdigest()[:10]
    return Prompt(system=system, schema=schema, version=f"m1_extract/{pdir.name}:{digest}", retry_template=retry)


class _Row:
    """Adapter so a Series indexed by passage_id renders like an itertuples() row."""

    def __init__(self, pid: str, s: pd.Series):
        self.passage_id = pid
        for k, v in s.items():
            setattr(self, k, v)
