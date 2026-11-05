"""M2 name resolution: historical plant name -> up to 3 accepted species with confidence (HEURISTIC).

Evidence (each adds weight to a GBIF-backbone species; weights are heuristic and documented here):
  database        the name as written is itself a scientific binomial (GBIF strict match)   2.0
  database        GBIF backbone species with an EXACT English vernacular match (plurals and
                  possessives folded): each query contributes 1.0, split by `support` (the number
                  of independent vernacular-name records matching); ×0.3 for Pliny names, whose
                  English renderings of Greek/Latin names are unreliable
                  Regional prior: vernacular weights are multiplied by 0.1 + 0.9 × log10(1+n) / max over
                  the query's candidates, n = GBIF occurrences in Great Britain (Culpeper, "the vulgar
                  herbs of this nation") or in Europe (Pliny)
  commentary_19c  binomial named in a Bostock & Riley footnote linked to the name:
                  strong link 2.0 / weak 1.0, divided by (order in footnote); ×0.5 if hedged
Scores per species are normalised to sum to 1 -> `confidence`. Each species is then mapped to its
accepted WFO name and id. `disputed` = top confidence < 0.6, or the deciding footnote hedges
("probably", "supposed", "some", "doubt"…), or the top two are within 0.15, or the total evidence
weight for the name is below 0.5 (weak evidence even if unopposed).
No scholarly identifications are used as candidates (they are reserved for evaluation), and no
LLM ("model" basis) is used in this version.
"""
from __future__ import annotations

import json
import math
import re
import string
from collections import defaultdict

import pandas as pd

from ..http import pmap
from ..paths import INTERIM
from . import services as S

OUT = INTERIM / "m2"
HEDGE = re.compile(r"\b(probabl[ey]|perhaps|suppos|uncertain|doubt|not known|unknown|conjectur|some (?:have|think|say|suppose)|"
                   r"others|it is thought|identity|identif(?:y|ied) it|it is not|may be|possibly|apparently)\w*", re.I)
BINOMIAL = re.compile(r"(?:\b(?:the|a|an|of|or|and)\s+)([A-Z][a-zæœëïé]+)\s+([a-zæœëïé]{3,})\b")
NOT_EPITHET = {"says", "has", "is", "was", "and", "the", "which", "this", "that", "with", "from", "seems", "thinks",
               "remarks", "states", "observes", "were", "are", "had", "also", "being", "says", "tells", "gives",
               "calls", "mentions", "speaks", "makes", "would", "will", "could", "should", "have", "does", "did"}


def footnote_binomials(text: str) -> list[str]:
    out = []
    for g, s in BINOMIAL.findall(text):
        if s in NOT_EPITHET:
            continue
        b = f"{g} {s}"
        if b not in out:
            out.append(b)
    return out


def capwords(s: str) -> str:
    return string.capwords(s.lower())


def run(inv: pd.DataFrame, fn_text: pd.Series, workers: int = 6) -> pd.DataFrame:
    # -- fetch phase (cached, parallel) ----------------------------------------------------
    latin_q = sorted({q for qs in inv.queries for q in qs if len(q.split()) == 2 and q.replace(" ", "").isalpha()})
    vern_q = sorted({q for qs in inv.queries for q in qs})
    fn_ids = sorted({f["id"] for fl in inv.footnotes for f in fl})
    bin_by_fn = {fid: footnote_binomials(fn_text.get(fid, "")) for fid in fn_ids}
    binoms = sorted({b for bl in bin_by_fn.values() for b in bl} | set(latin_q))
    match = dict(zip(binoms, pmap(S.gbif_match, binoms, workers)))
    vern = dict(zip(vern_q, pmap(S.gbif_vernacular, vern_q, workers)))

    def accepted(r):
        return S.gbif_accepted_species(r) if r else (None, None)
    usages = [r for r in match.values() if r] + [x for v in vern.values() for x in v]
    acc_map = {id(r): a for r, a in zip(usages, pmap(accepted, usages, workers))}
    region_of = {"culpeper-1652": "GB", "pliny": "EUROPE"}
    occ_keys = sorted({(acc_map[id(x)][1], region_of[e.source]) for e in inv.itertuples() for q in e.queries
                       for x in vern.get(q, []) if acc_map[id(x)][1]})
    occ = dict(zip(occ_keys, pmap(lambda kr: S.gbif_occurrences(*kr), occ_keys, workers)))

    # -- scoring ----------------------------------------------------------------------------
    rows = []
    for e in inv.itertuples():
        score: dict[str, float] = defaultdict(float)
        ev: dict[str, list] = defaultdict(list)
        hedged_top: dict[str, bool] = defaultdict(bool)
        for q in e.queries:
            if q in match and match[q]:
                sp, _ = acc_map[id(match[q])]
                if sp:
                    score[sp] += 2.0
                    ev[sp].append({"basis": "database", "how": "name as written is a scientific name", "query": q,
                                   "weight": 2.0})
            factor = 0.3 if e.source == "pliny" else 1.0
            hits = [x for x in vern.get(q, []) if acc_map[id(x)][0]]
            total_support = sum(x["support"] for x in hits)
            logs = {id(x): math.log10(1 + occ.get((acc_map[id(x)][1], region_of[e.source]), 0)) for x in hits}
            top_log = max(logs.values(), default=0) or 1.0
            for x in hits:
                sp, _ = acc_map[id(x)]
                prior = 0.1 + 0.9 * logs[id(x)] / top_log
                w = x["support"] / total_support * factor * prior
                score[sp] += w
                ev[sp].append({"basis": "database", "how": f"GBIF exact English vernacular (support {x['support']}, "
                               f"regional prior {prior:.2f})", "query": q, "weight": round(w, 3)})
        for f in e.footnotes:
            text = fn_text.get(f["id"], "")
            hedge = bool(HEDGE.search(text))
            for j, b in enumerate(bin_by_fn.get(f["id"], [])):
                r = match.get(b)
                if not r:
                    continue
                sp, _ = acc_map[id(r)]
                if not sp:
                    continue
                w = (2.0 if f["strength"] == "strong" else 1.0) / (j + 1) * (0.5 if hedge else 1.0)
                score[sp] += w
                hedged_top[sp] |= hedge
                ev[sp].append({"basis": "commentary_19c", "how": f"{f['strength']} footnote link" + (", hedged" if hedge else ""),
                               "footnote": f["id"], "binomial": b, "weight": round(w, 3)})
        total = sum(score.values())
        ranked = sorted(score.items(), key=lambda kv: -kv[1])[:3]
        for rank, (sp, s) in enumerate(ranked, 1):
            conf = s / total
            bases = defaultdict(float)
            for x in ev[sp]:
                bases[x["basis"]] += x["weight"]
            basis = max(bases, key=bases.get)
            ref = next((x.get("footnote") for x in ev[sp] if x["basis"] == basis and x.get("footnote")), None)
            rows.append({"nameId": e.nameId, "source": e.source, "nameAsWritten": e.nameAsWritten, "rank": rank,
                         "gbifSpecies": sp, "confidence": round(conf, 4), "evidenceTotal": round(total, 3), "basis": basis, "basisRef": ref,
                         "hedged": hedged_top[sp], "evidence": json.dumps(ev[sp], ensure_ascii=False)})
        if not ranked:
            rows.append({"nameId": e.nameId, "source": e.source, "nameAsWritten": e.nameAsWritten, "rank": 0,
                         "gbifSpecies": None, "confidence": None, "basis": None, "basisRef": None, "hedged": False,
                         "evidence": "[]"})
    cand = pd.DataFrame(rows)

    # -- WFO accepted names -------------------------------------------------------------------
    species = sorted(cand.gbifSpecies.dropna().unique())
    wfo = dict(zip(species, pmap(S.wfo_resolve, species, 4)))
    cand["acceptedName"] = cand.gbifSpecies.map(lambda s: (wfo.get(s) or {}).get("acceptedName") if s else None)
    cand["wfoId"] = cand.gbifSpecies.map(lambda s: (wfo.get(s) or {}).get("wfoId") if s else None)
    cand["family"] = cand.gbifSpecies.map(lambda s: (wfo.get(s) or {}).get("family") if s else None)
    cand["inWFO"] = cand.wfoId.notna()

    # -- disputed -------------------------------------------------------------------------------
    disputed = {}
    for nid, g in cand[cand["rank"] > 0].groupby("nameId"):
        g = g.sort_values("rank")
        top = g.iloc[0]
        close = len(g) > 1 and (top.confidence - g.iloc[1].confidence) < 0.15
        disputed[nid] = bool(top.confidence < 0.6 or (top.basis == "commentary_19c" and top.hedged) or close
                             or top.evidenceTotal < 0.5)
    cand["disputed"] = cand.nameId.map(disputed).fillna(False).astype(bool)
    return cand


def summary(inv: pd.DataFrame, cand: pd.DataFrame) -> dict:
    top = cand[cand["rank"] == 1]
    out = {}
    for src, g in inv.groupby("source"):
        t = top[top.source == src]
        out[src] = {"names": int(len(g)), "resolved": int(t.nameId.nunique()),
                    "resolvedInWFO": int(t[t.inWFO].nameId.nunique()),
                    "disputed": int(t[t.disputed].nameId.nunique()),
                    "topBasis": {k: int(v) for k, v in t.basis.value_counts().items()}}
    return out


def main(limit: int | None = None) -> dict:
    df = pd.read_parquet(INTERIM / "passages.parquet")
    from .inventory import build
    inv = build(df)
    if limit:
        inv = pd.concat([inv[inv.source == "culpeper-1652"].head(limit), inv[inv.source == "pliny"].head(limit)])
    fn_text = df[df.passage_type == "footnote"].set_index("passage_id").text_clean
    cand = run(inv, fn_text)
    OUT.mkdir(parents=True, exist_ok=True)
    inv.assign(queries=inv.queries.map(json.dumps), footnotes=inv.footnotes.map(json.dumps)).to_parquet(OUT / "name_inventory.parquet", index=False)
    cand.to_parquet(OUT / "name_candidates.parquet", index=False)
    s = summary(inv, cand)
    (OUT / "name_resolution_summary.json").write_text(json.dumps(s, indent=2))
    return s
