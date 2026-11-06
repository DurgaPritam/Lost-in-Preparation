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
    """The scope's batch files. For 'approved', passages already extracted in the sample are taken from the sample
    batches (same extractor, same prompt, one extraction per passage) and appended as batch "sample:NN"."""
    bs = [json.loads(p.read_text()) for p in sorted((SESSION_DIR / scope).glob("batch_*.json"))]
    if scope == "approved":
        want = set(passages_for("approved"))
        for b in batches("sample"):
            keep = {pid: out for pid, out in b["passages"].items() if pid in want}
            if keep:
                bs.append({**b, "batch": f"sample:{b['batch']:02d}", "passages": keep})
    return bs


def to_write(scope: str) -> list[str]:
    """Passages still to be written for a scope (approved: those not already extracted in the sample)."""
    ids = passages_for(scope)
    if scope == "approved":
        done = {pid for b in batches("sample") for pid in b["passages"]}
        ids = [p for p in ids if p not in done]
    return ids


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
    versions = sorted({b["promptVersion"] for b in bs})
    summary = {"scope": scope, "run": asdict(_SessionProvider("see batches").info()),
               "promptVersion": versions[0] if len(versions) == 1 else ",".join(versions),
               "passages": sum(x["passages"] for x in per_batch), "recipesAccepted": len(recipes),
               "recipesRejected": sum(1 for x in rejections if x["recipe"] is not None),
               "passagesFailedWhole": sum(1 for x in rejections if x["recipe"] is None), "batches": per_batch,
               "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (OUT / f"run_{scope}.json").write_text(json.dumps(summary, indent=2))
    return summary


def approved_passages() -> "pd.DataFrame":
    """Recipe-scope passages of the Phase 5 species (lip.m5.literature.species_list: the approved headline set plus
    approved species pending re-review that are still eligible; held and fallback-added species are NOT included).

    A species' passages come from the name entries that count towards its attestations in the study set
    (m3/study_set.py): rank-1 candidate in WFO, undisputed, confidence >= 0.6, not removed in
    config/name_entry_exclusions.csv. For each such entry:
      Culpeper 1652  recipe-scope passages of the entry, plus the recipe-scope passages of the Culpeper 1850 entry
                     crosswalked to it (data/interim/culpeper_1850_1652_crosswalk.csv, column crosswalk_1652)
      Pliny          recipe-scope passages of the chapter (shared by every name in a multi-name chapter)
    minus config/passage_exclusions.csv for that species. A passage linked to two species is listed once per species
    but extracted once (passages_for de-duplicates)."""
    import pandas as pd
    from ..m3.study_set import MIN_CONF, NAME_EXCLUSIONS, PASSAGE_EXCLUSIONS
    from ..m5.literature import species_list
    sp = set(species_list().acceptedName)
    cand = pd.read_parquet(INTERIM / "m2" / "name_candidates.parquet")
    top = cand[(cand["rank"] == 1) & cand.inWFO & ~cand.disputed & (cand.confidence >= MIN_CONF) & cand.acceptedName.isin(sp)]
    nx = pd.read_csv(NAME_EXCLUSIONS)
    drop = set(zip(nx.nameId, nx.species))
    top = top[[(n, a) not in drop for n, a in zip(top.nameId, top.acceptedName)]]
    df = load_passages()
    rs = df[df.recipe_scope.astype(bool)]
    rows = []
    for t in top.itertuples():
        if t.nameId.startswith("culpeper-1652:"):
            slug = t.nameId.split(":", 1)[1]
            m = ((rs.source_id == "culpeper-1652") & (rs.entry_slug == slug)) | ((rs.source_id == "culpeper-1850") & (rs.crosswalk_1652 == slug))
        else:
            book, key = t.nameId.split(":")[1:3]
            m = rs.source_id.str.startswith("pliny") & (rs.book == int(book[1:])) & (rs.entry_slug == key)
        rows += [{"passageId": p, "species": t.acceptedName, "nameId": t.nameId} for p in rs[m].passage_id]
    out = pd.DataFrame(rows, columns=["passageId", "species", "nameId"]).drop_duplicates(["passageId", "species"])
    px = pd.read_csv(PASSAGE_EXCLUSIONS)
    out = out[[(p, s) not in set(zip(px.passageId, px.species)) for p, s in zip(out.passageId, out.species)]]
    order = {p: i for i, p in enumerate(df.passage_id)}
    return out.sort_values("passageId", key=lambda s: s.map(order)).reset_index(drop=True)


def passages_for(scope: str) -> list[str]:
    """The passage IDs a scope covers: 'sample' = the 50-passage gold sample; 'approved' = recipe-scope passages of
    the Phase 5 species (approved_passages), in corpus order, de-duplicated."""
    if scope == "sample":
        from .sample import SAMPLE_PATH
        return [p["passageId"] for p in json.loads(SAMPLE_PATH.read_text())["passages"]]
    if scope == "approved":
        return list(dict.fromkeys(approved_passages().passageId))
    raise ValueError(scope)


def show(scope: str, start: int, n: int) -> str:
    """Render passages for writing a batch: context exactly as the prompt's user message gives it."""
    from .extract import source_titles
    from .prompt import render_user
    titles = dict(source_titles())
    df = load_passages().set_index("passage_id")
    out = []
    for pid in to_write(scope)[start:start + n]:
        row = df.loc[pid]
        r = type("Row", (), {"passage_id": pid, **row.to_dict()})()
        out.append(f"### {pid}\n" + render_user(r, titles.get(row["source_id"], "")))
    return "\n\n".join(out)
