"""Phase 1: segment raw texts into passages.

Outputs
  data/interim/passages.parquet   one row per passage (original + cleaned text, stable ID, location)
  site-data/sources.json          contract v0.1 shape, validated with contract.models.Source
  data/interim/ingest_report.json counts per source (the only source for any reported count)
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone

import pandas as pd

from contract.models import CONTRACT_VERSION, Source, SourceFile

from . import PIPELINE_VERSION
from .fetch import load_manifest, verify
from .paths import INTERIM, ROOT, SITE_DATA, load_sources
from .segment import PROFILES, crosswalk, tei
from .segment.common import clean_text, sha256_text

def source_record(s: dict) -> Source:
    """Map a config/sources.toml entry (+ raw manifest checksums) onto contract Source."""
    manifest = {f["source_id"]: f for f in load_manifest()["files"]}
    files = [SourceFile(url=manifest[s["id"]]["url"], sha256=manifest[s["id"]]["sha256"])] if s["id"] in manifest else []
    return Source(
        id=s["id"], workId=s["work_id"], title=s["title"], author=s["author"],
        translator=s.get("translator"), originalYear=s.get("original_year"),
        originalYearApprox=s.get("original_year_approx", False), editionYear=s["edition_year"],
        language=s["language"], edition=s["edition"], licence=s["licence"],
        licenceVerified=s["licence_verified"], licenceNote=s.get("licence_note"),
        editorialNote=s.get("editorial_note"), url=s["url"], files=files,
    )


def read_lines(path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("﻿"):
        text = text[1:]
    return text.split("\n")


def build(sources: list[dict] | None = None, verify_checksums: bool = True) -> pd.DataFrame:
    sources = sources or load_sources()
    rows = []
    for src in sources:
        if verify_checksums:
            verify(src)
        if src["profile"] == "tei":
            passages = tei.segment(src, ROOT / src["raw_path"])  # renders text_clean itself
        else:
            passages = PROFILES[src["profile"]](src, read_lines(ROOT / src["raw_path"]))

        cited_by: dict[str, list[str]] = {}
        for p in passages:
            for ref in p.footnote_refs:
                cited_by.setdefault(ref, []).append(p.passage_id)
        for p in passages:
            if p.passage_type == "footnote":
                p.footnote_of = cited_by.get(p.passage_id, [])
            if src["profile"] != "tei":
                p.text_clean, p.cleaning_ops = clean_text(
                    p.text_original, strip_footnote_anchors=src["profile"] == "pliny"
                )
            row = asdict(p)
            row["gap_count"] = p.text_clean.count("⟦")
            row["sha256_original"] = sha256_text(p.text_original)
            row["word_count"] = len(p.text_clean.split())
            rows.append(row)

    df = pd.DataFrame(rows)
    for col in ("book", "entry_ordinal"):
        df[col] = df[col].astype("Int64")
    for col in ("section", "chapter", "chapter_alt", "page", "entry_title", "entry_slug", "subsection"):
        df[col] = df[col].astype("string")
    dupes = df["passage_id"][df["passage_id"].duplicated()]
    if len(dupes):
        raise RuntimeError(f"duplicate passage IDs: {dupes.head().tolist()}")
    return add_crosswalk(df)


def herbal_entries(df: pd.DataFrame, source_id: str) -> pd.DataFrame:
    h = df[(df.source_id == source_id) & (df.part == "herbal") & (df.passage_type == "heading") & (df.block_index == 0)
           & df.entry_slug.notna()]
    return pd.DataFrame({"entry_slug": h.entry_slug.astype(str), "heading": h.text_clean})


def add_crosswalk(df: pd.DataFrame) -> pd.DataFrame:
    """1850 herbal entries -> 1652 entries; later-addition flag applies to 1850 herbal entries only."""
    df["addition_status"] = pd.Series(pd.NA, index=df.index, dtype="string")
    df["crosswalk_1652"] = pd.Series(pd.NA, index=df.index, dtype="string")
    df["crosswalk_score"] = pd.Series(pd.NA, index=df.index, dtype="Float64")
    if not {"culpeper-1850", "culpeper-1652"} <= set(df.source_id):
        return df
    cw = crosswalk.crosswalk(herbal_entries(df, "culpeper-1850"), herbal_entries(df, "culpeper-1652"))
    INTERIM.mkdir(parents=True, exist_ok=True)
    cw.to_csv(INTERIM / "culpeper_1850_1652_crosswalk.csv", index=False)
    m = (df.source_id == "culpeper-1850") & (df.part == "herbal") & df.entry_slug.notna()
    by = cw.set_index("entry_1850")
    slugs = df.loc[m, "entry_slug"].astype(str)
    df.loc[m, "addition_status"] = slugs.map(by.status).values
    df.loc[m, "crosswalk_1652"] = slugs.map(by.entry_1652).values
    df.loc[m, "crosswalk_score"] = slugs.map(by.score).values
    return df


def report(df: pd.DataFrame, sources: list[dict]) -> dict:
    out = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pipelineVersion": PIPELINE_VERSION, "contractVersion": CONTRACT_VERSION, "sources": {}}
    all_ids = set(df["passage_id"])
    for src in sources:
        d = df[df.source_id == src["id"]]
        body = d[d.passage_type == "body"]
        refs = [r for lst in d.footnote_refs for r in lst]
        fn = d[d.passage_type == "footnote"]
        if src["profile"] in ("culpeper", "tei"):
            entries = {
                part: int(d[(d.part == part) & d.entry_slug.notna()].entry_slug.nunique())
                for part in sorted(d.part.unique())
            }
        else:
            ch = d[(d.part == "body") & d.chapter.notna()]
            entries = {f"book_{int(b)}": int(g.entry_slug.nunique()) for b, g in ch.groupby("book")}
        out["sources"][src["id"]] = {
            "passages_total": int(len(d)),
            "by_part": {k: int(v) for k, v in Counter(d.part).items()},
            "by_type": {k: int(v) for k, v in Counter(d.passage_type).items()},
            "entries": entries,
            "recipe_scope_passages": int(d.recipe_scope.sum()),
            "recipe_scope_words": int(d[d.recipe_scope].word_count.sum()),
            "body_words": int(body.word_count.sum()),
            "footnotes": int(len(fn)),
            "footnote_refs": len(refs),
            "footnote_refs_unresolved": sorted({r for r in refs if r not in all_ids}),
            "footnotes_uncited": int((fn.footnote_of.map(len) == 0).sum()),
            "cleaning_ops": dict(Counter(op for ops in d.cleaning_ops for op in ops)),
            "passages_with_gap_marker": int((d.gap_count > 0).sum()),
            "gap_markers": int(d.gap_count.sum()),
        }
        if src["id"] == "culpeper-1850":
            st = d[(d.part == "herbal") & d.addition_status.notna()].drop_duplicates("entry_slug")
            out["sources"][src["id"]]["crosswalk_1652"] = {k: int(v) for k, v in Counter(st.addition_status).items()}
    return out


def run() -> dict:
    sources = load_sources()
    df = build(sources)
    INTERIM.mkdir(parents=True, exist_ok=True)
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    df.to_parquet(INTERIM / "passages.parquet", index=False)

    records = [source_record(s).model_dump() for s in sources]
    (SITE_DATA / "sources.json").write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")

    rep = report(df, sources)
    (INTERIM / "ingest_report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n")
    return rep
