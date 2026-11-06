"""Gold-set sample v2 for M1 evaluation: 50 passages, stratified by source, fixed seed.

Strata and allocation:
  culpeper1652_virtues       20  Culpeper 1652 herbal, "Vertues and use" sections (body paragraphs)
  culpeper1850_dispensatory  10  Culpeper 1850 Family Dispensatory (body paragraphs)
  pliny                      20  Pliny, Natural History, books 20–27 (body paragraphs)
Frame rules: recipe-scope body passages only; few-shot example passages excluded (they are in the
prompt); passages containing an illegible-gap marker (⟦…⟧) excluded. Recipe spans are not known
before annotation, so any passage with a gap is skipped (a conservative superset of "a gap inside
recipe text"). Sampling is without replacement within each stratum, seed below.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from ..paths import ROOT
from .prompt import fewshot_ids, heading_of, load_passages

SEED = 20261106
VERSION = "v2"
ALLOCATION = {"culpeper1652_virtues": 20, "culpeper1850_dispensatory": 10, "pliny": 20}
SAMPLE_PATH = ROOT / "data" / "gold" / f"sample_{VERSION}.json"


def stratum(row) -> str | None:
    if row.source_id == "culpeper-1652" and row.part == "herbal" and row.subsection == "vertues and use":
        return "culpeper1652_virtues"
    if row.source_id == "culpeper-1850" and row.part == "dispensatory":
        return "culpeper1850_dispensatory"
    if row.source_id.startswith("pliny-nh") and not pd.isna(row.book) and 20 <= int(row.book) <= 27:
        return "pliny"
    return None


def _base(df: pd.DataFrame | None) -> pd.DataFrame:
    df = load_passages() if df is None else df
    d = df[df.recipe_scope & (df.passage_type == "body")].copy()
    d["stratum"] = [stratum(r) for r in d.itertuples()]
    return d[d.stratum.notna() & ~d.passage_id.isin(fewshot_ids())]


def frame(df: pd.DataFrame | None = None) -> pd.DataFrame:
    d = _base(df)
    return d[d.gap_count == 0].sort_values("passage_id").reset_index(drop=True)


def draw(df: pd.DataFrame | None = None, seed: int = SEED) -> pd.DataFrame:
    f = frame(df)
    parts = [f[f.stratum == s].sample(n=n, random_state=seed) for s, n in ALLOCATION.items()]
    return pd.concat(parts).sort_values(["stratum", "passage_id"]).reset_index(drop=True)


def write(df: pd.DataFrame | None = None) -> dict:
    base, f, s = _base(df), frame(df), draw(df)
    out = {
        "version": VERSION,
        "seed": SEED,
        "allocation": ALLOCATION,
        "frameSize": {k: int((f.stratum == k).sum()) for k in ALLOCATION},
        "excludedForGap": {k: int(((base.stratum == k) & (base.gap_count > 0)).sum()) for k in ALLOCATION},
        "excludedFewShot": sorted(fewshot_ids()),
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "passages": [
            {
                "passageId": r.passage_id, "stratum": r.stratum, "sourceId": r.source_id, "part": r.part,
                "heading": heading_of(r), "subsection": r.subsection if isinstance(r.subsection, str) else None,
                "book": None if pd.isna(r.book) else int(r.book),
                "chapter": None if pd.isna(r.chapter) else r.chapter,
                "page": None if pd.isna(r.page) else r.page,
                "text": r.text_clean,
            }
            for r in s.itertuples()
        ],
    }
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return out


# --- self-consistency re-annotation subset (single annotator) -------------------------------
# The gold set is annotated by ONE person (the project lead). To measure self-consistency, the same
# person re-annotates 15 of the 50 passages later, blind to the first pass, in a separate file
# data/gold/annotations/<name>_reannotation.json. The 15 are drawn here, stratified in proportion
# to the sample (6 / 3 / 6), with a fixed seed different from the sample's.
REANNOT_SEED = 20261108
REANNOT_ALLOCATION = {"culpeper1652_virtues": 6, "culpeper1850_dispensatory": 3, "pliny": 6}
REANNOT_PATH = ROOT / "data" / "gold" / "reannotation_subset_v1.json"


def write_reannotation_subset() -> dict:
    s = pd.DataFrame(json.loads(SAMPLE_PATH.read_text())["passages"])
    parts = [s[s.stratum == k].sort_values("passageId").sample(n=n, random_state=REANNOT_SEED)
             for k, n in REANNOT_ALLOCATION.items()]
    sub = pd.concat(parts).sort_values(["stratum", "passageId"])
    out = {"sampleVersion": VERSION, "seed": REANNOT_SEED, "allocation": REANNOT_ALLOCATION,
           "purpose": "intra-annotator self-consistency: the single gold annotator re-annotates these passages "
                      "later, without looking at the first annotation, saving <name>_reannotation.json",
           "passageIds": list(sub.passageId)}
    REANNOT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return out
