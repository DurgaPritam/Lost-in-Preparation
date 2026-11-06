"""Logged corrections to M1 extraction fields (config/m1_corrections.csv), applied as an overlay.

The extraction outputs (data/interim/m1/predictions_*.json) are never edited. Each correction names the recipe, the
field, the old and new value, the reason, the evidence, who requested it and who applied it. `apply` checks that the
recorded old value matches the extraction (so a stale correction fails loudly) and marks every corrected record with
`corrections`. Solvent values are lists in the extraction; a correction "a+b" sets ["a", "b"].
"""
from __future__ import annotations

import copy

import pandas as pd

from ..paths import ROOT

PATH = ROOT / "config" / "m1_corrections.csv"


def table() -> pd.DataFrame:
    return pd.read_csv(PATH, dtype=str).fillna("") if PATH.exists() else pd.DataFrame(columns=["recipeId", "field", "from", "to"])


def _val(field, v):
    return v.split("+") if field == "solvent" else v


def apply(recipes: list[dict]) -> list[dict]:
    t = table()
    by = {r["id"]: r for r in recipes}
    out = {rid: r for rid, r in by.items()}
    for c in t.to_dict("records"):
        rid, f = c["recipeId"], c["field"]
        if rid not in by:
            continue
        r = out[rid] = copy.deepcopy(out[rid]) if "corrections" not in out[rid] else out[rid]
        if r[f] != _val(f, c["from"]):
            raise ValueError(f"correction for {rid}.{f}: recorded old value {c['from']!r} != extraction {r[f]!r}")
        r[f] = _val(f, c["to"])
        r.setdefault("corrections", []).append({k: c[k] for k in ("field", "from", "to", "reason", "evidence", "requestedBy",
                                                                    "appliedBy", "date")})
    return [out[r["id"]] for r in recipes]
