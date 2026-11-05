"""Versioned M1 prompt: system text + guidelines + Culpeper few-shot examples + response schema.

promptVersion = "<dir>:<sha256 of rendered system prompt + schema>[:10]", so any edit to the
guidelines, examples or schema yields a new version string recorded in provenance.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from ..paths import INTERIM, ROOT
from .schema import response_schema

PROMPT_DIR = ROOT / "prompts" / "m1_extract" / "v1"
PROMPT_NAME = "m1_extract/v1"


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


def fewshot() -> list[dict]:
    return json.loads((PROMPT_DIR / "fewshot.json").read_text())


def fewshot_ids() -> set[str]:
    return {ex["passageId"] for ex in fewshot()}


@dataclass(frozen=True)
class Prompt:
    system: str
    schema: dict
    version: str


@lru_cache(maxsize=1)
def build(source_titles: tuple[tuple[str, str], ...]) -> Prompt:
    titles = dict(source_titles)
    passages = load_passages().set_index("passage_id")
    blocks = []
    for i, ex in enumerate(fewshot(), 1):
        row = passages.loc[ex["passageId"]]
        user = render_user(_Row(ex["passageId"], row), titles.get(row["source_id"], ""))
        blocks.append(
            f"<example index=\"{i}\">\n{user}\n<output>\n"
            + json.dumps(ex["output"], ensure_ascii=False, indent=1)
            + "\n</output>\n</example>"
        )
    system = (
        (PROMPT_DIR / "system.md").read_text()
        .replace("{{GUIDELINES}}", (PROMPT_DIR / "guidelines.md").read_text().strip())
        .replace("{{EXAMPLES}}", "\n\n".join(blocks))
    )
    schema = response_schema()
    digest = hashlib.sha256((system + json.dumps(schema, sort_keys=True)).encode()).hexdigest()[:10]
    return Prompt(system=system, schema=schema, version=f"{PROMPT_NAME}:{digest}")


class _Row:
    """Adapter so a Series indexed by passage_id renders like an itertuples() row."""

    def __init__(self, pid: str, s: pd.Series):
        self.passage_id = pid
        for k, v in s.items():
            setattr(self, k, v)
