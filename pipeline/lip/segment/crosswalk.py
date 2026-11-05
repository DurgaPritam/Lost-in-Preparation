"""Heading crosswalk: Culpeper 1850 herbal entries -> 1652 herb entries (HEURISTIC).

The 1850 Kelly edition adds herbs to the 1652 text. An 1850 herbal entry with no 1652
counterpart is a *later-addition candidate*. Matching is heuristic and is reported with its
score so a person can review borderline cases (data/interim/culpeper_1850_1652_crosswalk.csv).

Normalisation: lower case, drop "the" and possessive 's, map early-modern spellings
(vv→w, v→u, j→i, y→i, ph→f), drop doubled letters and word-final e. Every alternative name in a heading
("ALEHOOF, OR GROUND-IVY") is compared; score = max over alternative pairs of
max(sequence ratio, token-sorted sequence ratio).
Status: in_1652 (score >= 0.90), probable_1652 (0.75–0.90), later_addition_candidate (< 0.75).
Only herbal entries are crosswalked; other 1850 parts have no 1652 counterpart by construction.

Reviewer decisions in config/crosswalk_overrides.csv (entry_1850, entry_1652 or "none",
reviewer, note) always win over the heuristic; such rows get status `reviewed_*`.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

import pandas as pd

MATCHED, PROBABLE = 0.90, 0.75
_SPLIT = re.compile(r",|;|\bor\b|\botherwise\b|\bcalled\b|\(|\)|\band\b")


def _word(w: str) -> str:
    w = w.replace("vv", "w").replace("ph", "f").replace("v", "u").replace("j", "i").replace("y", "i")
    w = re.sub(r"(.)\1+", r"\1", w)
    return w[:-1] if len(w) > 3 and w.endswith("e") else w


def key(s: str) -> str:
    s = s.lower().replace("&amp;", " ")
    s = re.sub(r"[’']s\b", "s", s)
    words = [w for w in re.findall(r"[a-z]+", s) if w not in ("the", "a")]
    return " ".join(_word(w) for w in words)


def alternatives(heading: str) -> list[str]:
    alts = {key(heading)}
    alts |= {key(p) for p in _SPLIT.split(heading.lower())}
    return sorted(a for a in alts if len(a) >= 3)


def _ratio(a: str, b: str) -> float:
    s1 = SequenceMatcher(None, a, b).ratio()
    s2 = SequenceMatcher(None, " ".join(sorted(a.split())), " ".join(sorted(b.split()))).ratio()
    return max(s1, s2)


def score(h1: str, h2: str) -> float:
    a1, a2 = alternatives(h1), alternatives(h2)
    return max((_ratio(x, y) for x in a1 for y in a2), default=0.0)


def status(s: float) -> str:
    return "in_1652" if s >= MATCHED else ("probable_1652" if s >= PROBABLE else "later_addition_candidate")


def crosswalk(entries_1850: pd.DataFrame, entries_1652: pd.DataFrame) -> pd.DataFrame:
    """entries_*: columns entry_slug, heading. Greedy one-to-one assignment by descending score."""
    named_1652 = entries_1652[entries_1652.heading.str.contains(r"[A-Za-z]", regex=True)]
    cands = []
    for a in entries_1850.itertuples():
        for b in named_1652.itertuples():
            cands.append((score(a.heading, b.heading), a.entry_slug, b.entry_slug))
    cands.sort(key=lambda t: (-t[0], t[1], t[2]))
    best_any = {}
    for s, a, b in cands:
        best_any.setdefault(a, (s, b))
    used_a, used_b, pair = set(), set(), {}
    for s, a, b in cands:
        if a in used_a or b in used_b or s < PROBABLE:
            continue
        pair[a] = (s, b)
        used_a.add(a)
        used_b.add(b)
    h52 = dict(zip(entries_1652.entry_slug, entries_1652.heading))
    rows = []
    for a in entries_1850.itertuples():
        s, b = pair.get(a.entry_slug, (best_any.get(a.entry_slug, (0.0, None))[0], None))
        nearest = best_any.get(a.entry_slug, (0.0, None))[1]
        rows.append({
            "entry_1850": a.entry_slug, "heading_1850": a.heading,
            "entry_1652": b, "heading_1652": h52.get(b) if b else None,
            "score": round(s, 3), "status": status(s) if b else "later_addition_candidate",
            "nearest_1652": nearest, "nearest_heading_1652": h52.get(nearest) if nearest else None,
        })
    out = pd.DataFrame(rows)
    return apply_overrides(out, h52)


def apply_overrides(cw: pd.DataFrame, h52: dict) -> pd.DataFrame:
    from ..paths import ROOT
    path = ROOT / "config" / "crosswalk_overrides.csv"
    if not path.exists():
        return cw
    ov = pd.read_csv(path, dtype=str).fillna("")
    for r in ov.itertuples():
        m = cw.entry_1850 == r.entry_1850
        if not m.any():
            raise ValueError(f"override for unknown 1850 entry: {r.entry_1850}")
        if r.entry_1652 == "none":
            cw.loc[m, ["entry_1652", "heading_1652", "status"]] = [None, None, "reviewed_later_addition"]
        else:
            if r.entry_1652 not in h52:
                raise ValueError(f"override to unknown 1652 entry: {r.entry_1652}")
            cw.loc[m, ["entry_1652", "heading_1652", "status"]] = [r.entry_1652, h52[r.entry_1652], "reviewed_in_1652"]
    return cw
