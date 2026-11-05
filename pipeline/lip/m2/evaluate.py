"""M2 evaluation against hand-made scholarly identifications.

`lip m2 evalset` writes data/gold/name_identifications.csv: 30 names (15 Culpeper 1652, 15 Pliny),
drawn with a fixed seed. It is NEVER overwritten once it exists. A person fills, for each row,
`scholarlyAcceptedName` (and `scholarlyWfoId` if known) and the `citation` they took it from.
Rows without both a name and a citation are not scored.

`lip m2 eval` scores top-1 / top-3 accuracy (Wilson 95% CI) and the share of resolved names
flagged disputed, and writes them to metrics.json (nameResolution).
"""
from __future__ import annotations

import math
import re

import pandas as pd

from contract import models as C

from .. import metrics_store
from ..paths import INTERIM, ROOT
from .services import ascii_latin

EVAL_PATH = ROOT / "data" / "gold" / "name_identifications.csv"
CAND_PATH = INTERIM / "m2" / "name_candidates.parquet"
INV_PATH = INTERIM / "m2" / "name_inventory.parquet"
SEED = 20261107
N_PER_SOURCE = 15
COLUMNS = ["nameId", "source", "entry", "nameAsWritten", "context", "scholarlyAcceptedName", "scholarlyWfoId",
           "citation", "annotator", "notes"]


def _context(df: pd.DataFrame, row) -> str:
    if row.source == "culpeper-1652":
        d = df[(df.source_id == "culpeper-1652") & (df.entry_slug == row.entry).fillna(False).astype(bool)
               & (df.passage_type == "body")]
    else:
        book, key = row.entry.split(":")
        m = (df.source_id.str.startswith("pliny").fillna(False).astype(bool)
             & (df.book == int(book[1:])).fillna(False).astype(bool)
             & (df.entry_slug == key).fillna(False).astype(bool) & (df.passage_type == "body"))
        d = df[m]
    return (d.sort_values("block_index").text_clean.iloc[0][:300] if len(d) else "")


def write_template() -> str:
    if EVAL_PATH.exists():
        return f"{EVAL_PATH.relative_to(ROOT)} already exists; not overwritten."
    inv = pd.read_parquet(INV_PATH)
    df = pd.read_parquet(INTERIM / "passages.parquet")
    picks = pd.concat([inv[inv.source == s].sample(n=N_PER_SOURCE, random_state=SEED) for s in ("culpeper-1652", "pliny")])
    out = pd.DataFrame({
        "nameId": picks.nameId, "source": picks.source, "entry": picks.entry, "nameAsWritten": picks.nameAsWritten,
        "context": [_context(df, r) for r in picks.itertuples()],
    })
    for c in COLUMNS[5:]:
        out[c] = ""
    EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    out[COLUMNS].to_csv(EVAL_PATH, index=False)
    return f"wrote {EVAL_PATH.relative_to(ROOT)} ({len(out)} names)"


def _binomial(s: str) -> str:
    words = re.findall(r"[A-Za-z]+", ascii_latin(str(s)))
    return " ".join(words[:2]).lower()


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def evaluate() -> dict:
    cand = pd.read_parquet(CAND_PATH)
    top = cand[cand["rank"] == 1]
    resolved = top[top.acceptedName.notna()]
    disputed = C.Metric(status="computed", value=round(float(resolved.disputed.mean()), 4), n=int(len(resolved)),
                        sourceFile=str(CAND_PATH.relative_to(ROOT)),
                        note="share of resolved names whose top candidate is flagged disputed (descriptive)")
    out = {"disputedShare": disputed}
    gold = pd.read_csv(EVAL_PATH, dtype=str).fillna("") if EVAL_PATH.exists() else pd.DataFrame(columns=COLUMNS)
    # GOLD = human-filled columns only; the draft* columns are never read here
    gold = gold[(gold.scholarlyAcceptedName.str.strip() != "") & (gold.citation.str.strip() != "")]
    if gold.empty:
        note = f"awaiting scholarly identifications in {EVAL_PATH.relative_to(ROOT)} (name + citation per row)"
        out["top1"], out["top3"] = C.not_computed(note), C.not_computed(note)
    else:
        hits1 = hits3 = 0
        for g in gold.itertuples():
            c = cand[(cand.nameId == g.nameId) & (cand["rank"] > 0)].sort_values("rank")
            ok = [(_binomial(r.acceptedName) == _binomial(g.scholarlyAcceptedName))
                  or (bool(g.scholarlyWfoId) and r.wfoId == g.scholarlyWfoId) for r in c.itertuples()]
            hits1 += bool(ok[:1] and ok[0])
            hits3 += any(ok[:3])
        n = len(gold)
        for key, k in (("top1", hits1), ("top3", hits3)):
            lo, hi = wilson(k, n)
            out[key] = C.Metric(status="computed", value=round(k / n, 4), low=round(lo, 4), high=round(hi, 4), n=n,
                                sourceFile=str(EVAL_PATH.relative_to(ROOT)), note="Wilson 95% CI")
    metrics_store.update(nameResolution=out)
    prov = _draft_agreement(cand)
    return {**{k: v.model_dump() for k, v in out.items()},
            "provisional_vs_ai_drafts": {k: v.model_dump() for k, v in prov.items()}}


DRAFT_LABEL = "M2 vs AI-drafted identifications, provisional; not human-verified"


def _score(cand: pd.DataFrame, rows: pd.DataFrame, name_col: str, id_col: str) -> tuple[int, int, int]:
    hits1 = hits3 = 0
    for g in rows.itertuples():
        c = cand[(cand.nameId == g.nameId) & (cand["rank"] > 0)].sort_values("rank")
        ok = [(_binomial(r.acceptedName) == _binomial(getattr(g, name_col)))
              or (bool(getattr(g, id_col)) and r.wfoId == getattr(g, id_col)) for r in c.itertuples()]
        hits1 += bool(ok[:1] and ok[0])
        hits3 += any(ok[:3])
    return hits1, hits3, len(rows)


def _draft_agreement(cand: pd.DataFrame) -> dict:
    """Agreement with AI-drafted identifications -> metrics.provisional['nameResolutionVsDraft'] only."""
    out = {}
    d = pd.read_csv(EVAL_PATH, dtype=str).fillna("") if EVAL_PATH.exists() else pd.DataFrame()
    if "draftAcceptedName" in d:
        d = d[d.draftAcceptedName.str.strip() != ""]
    if len(d) == 0 or "draftAcceptedName" not in d:
        out["top1"] = out["top3"] = C.not_computed("no AI-drafted identifications (run `python -m lip m2 drafts`)")
    else:
        h1, h3, n = _score(cand, d, "draftAcceptedName", "draftWfoId")
        for key, k in (("top1", h1), ("top3", h3)):
            lo, hi = wilson(k, n)
            out[key] = C.Metric(status="computed", value=round(k / n, 4), low=round(lo, 4), high=round(hi, 4), n=n,
                                sourceFile=str(EVAL_PATH.relative_to(ROOT)), note=f"{DRAFT_LABEL}; Wilson 95% CI")
    metrics_store.update_provisional("nameResolutionVsDraft", C.ProvisionalSection(
        basis="ai_drafted_unverified", label=DRAFT_LABEL, metrics=out))
    return out


BEFORE = INTERIM / "m2" / "before" / "name_candidates.parquet"
WATCH = ["MANDRAGORA", "CUMMIN", "WILD CUMMIN", "Dodder", "ARON", "SCORDOTIS", "BECHION", "HORMINUM", "Wormwood", "Agrimony"]


def before_after() -> dict:
    """Compare M2 v1 (data/interim/m2/before/) with the current run, per source; drafts are provisional."""
    import json as _json
    b, a = pd.read_parquet(BEFORE), pd.read_parquet(CAND_PATH)
    d = pd.read_csv(EVAL_PATH, dtype=str).fillna("")
    d = d[d.draftAcceptedName.str.strip() != ""]
    out = {"bySource": {}, "names": {}, "note": "draftTop1 = agreement with AI-drafted identifications (provisional, not gold)"}
    for src in ("culpeper-1652", "pliny"):
        x = {}
        for tag, c in (("before", b), ("after", a)):
            t = c[(c["rank"] == 1) & (c.source == src)]
            dd = d[d.source == src]
            h1, _, n = _score(c, dd, "draftAcceptedName", "draftWfoId")
            x[tag] = {"resolved": int(t[t.acceptedName.notna()].nameId.nunique()), "disputed": int(t[t.disputed].nameId.nunique()),
                      "draftTop1": f"{h1}/{n}"}
        out["bySource"][src] = {k: [x["before"][k], x["after"][k]] for k in ("resolved", "disputed", "draftTop1")}
    for nm in WATCH:
        row = {}
        for tag, c in (("before", b), ("after", a)):
            t = c[(c["rank"] == 1) & c.nameAsWritten.str.upper().str.startswith(nm.upper())]
            if len(t):
                r = t.iloc[0]
                extra = " (genus-level)" if bool(r.get("genusLevelOnly", False)) else ""
                tox = f"; toxic-confusion" if bool(r.get("toxicConfusion", False)) else ""
                row[tag] = f"{r.acceptedName} ({r.confidence:.2f}{', disputed' if r.disputed else ''}{extra}{tox})"
            else:
                row[tag] = "—"
        out["names"][nm] = row
    (INTERIM / "m2" / "before_after.json").write_text(_json.dumps(out, indent=2, ensure_ascii=False))
    return out
