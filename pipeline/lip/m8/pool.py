"""Phase 8 candidate pool: (species, historical preparation, modern comparator) for the 19 approved species.

A candidate is a re-test that a lab could run: prepare the plant as the historical recipe did, and as the modern
comparator does, and compare the profiles. It is kept only when the M6 robust gap is usable (m6/ranking.py rules:
at least MIN_COMPOUNDS compounds whose reported 5th–95th range is narrower than WIDTH_MAX in both preparations).

  historical preparation  every M4-representable historical preparation attested for the species in the single-plant
                          recipes with a mapped indication (m5/pairs.json, logged M1 corrections applied; HEURISTIC map
                          m6.hypotheses.hist_to_grid)
  modern comparator       the most frequent M4-representable modern preparation among the studies retrieved for the
                          candidate's pairs; when none was retrieved, the most frequent one across all coded studies
                          (recorded as basis "default")
  indication              the most-attested MeSH indication among the candidate's recipes; all attested indications
                          are kept for the coverage term
  value                   gapP5, the 5th percentile of the profile gap over coupled Monte Carlo draws (M6, unchanged)
  differs                 compounds "likely to differ" between the two preparations (HEURISTIC, config differ_delta):
                          the 5th–95th range of the coupled draw difference excludes 0 and |median| >= differ_delta
  classes                 compound classes (heuristic, site-data/engine) among `differs`

Toxic-reported species stay in the pool with `toxic: true`; the objective's config decides (exclude / at most one).
Writes data/interim/m8/pool.json. Candidates are hypotheses worth re-testing, never claims that a preparation works.
"""
from __future__ import annotations

import json
import tomllib
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from ..m4 import model as M
from ..m6 import ranking as R
from ..m6.hypotheses import compounds_for, hist_to_grid, modern_to_grid
from ..paths import INTERIM, ROOT, SITE_DATA

OUT = INTERIM / "m8" / "pool.json"
CONFIG = ROOT / "config" / "m8_qubo.toml"
CONFIGS = {"v1": CONFIG, "v2": ROOT / "config" / "m8_qubo_v2.toml"}   # v2: docs/QUBO_v2_RULE.md (pre-registered)


def config(version: str = "v1") -> dict:
    return tomllib.loads(CONFIGS[version].read_text())


def eligibility(c: dict, cfg: dict) -> str | None:
    """v2 hard eligibility (docs/QUBO_v2_RULE.md); None = eligible, else the reason. v1 has no rule."""
    r = cfg.get("rule")
    if not r:
        return None
    if not c["gapP5"] > r["min_gap_p5"]:
        return f"robust gap {c['gapP5']} is not positive"
    if len(c["differs"]) < r["min_differs"]:
        return f"{len(c['differs'])} compounds likely to differ (needs at least {r['min_differs']})"
    return None


def build() -> dict:
    from ..m1.corrections import apply
    cfg = config()
    delta = cfg["pool"]["differ_delta"]
    pairs = json.loads((INTERIM / "m5" / "pairs.json").read_text())["pairs"]
    studies = {s["pmid"]: s for s in json.loads((INTERIM / "m5" / "audit_studies.json").read_text())["studies"]}
    pair_pmids = json.loads((INTERIM / "m5" / "audit_studies.json").read_text())["pairPmids"]
    recipes = {r["id"]: r for r in apply(json.loads((INTERIM / "m1" / "predictions_approved.json").read_text()))}
    index = {e["acceptedName"]: e for e in json.loads((SITE_DATA / "profiles" / "index.json").read_text())}
    prop = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    approved = sorted(prop[prop.headline].acceptedName)

    global_modern = Counter(lab for s in studies.values() for x in s["preparations"] for lab in [modern_to_grid(x)[0]] if lab)
    default_modern = sorted(global_modern.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

    groups: dict[tuple, dict] = {}
    for p in pairs:
        if p["species"] not in approved:
            continue
        key = f"{p['speciesId']}|{p['indication']['meshId']}"
        for rid in p["recipes"]:
            lab = hist_to_grid(recipes[rid])
            if not lab:
                continue
            g = groups.setdefault((p["species"], lab), {"species": p["species"], "speciesId": p["speciesId"], "historical": lab,
                                                         "recipes": set(), "indications": Counter(), "indicationLabels": {},
                                                         "pairKeys": set(), "sources": set()})
            g["recipes"].add(rid)
            g["indications"][p["indication"]["meshId"]] += 1
            g["indicationLabels"][p["indication"]["meshId"]] = p["indication"]["label"]
            g["pairKeys"].add(key)
            g["sources"].add(recipes[rid]["sourceId"])

    cfg_m4 = M.load_config()
    draws = R.Draws(cfg_m4, M.descriptor_sd("rdkit")["sd"])
    comps = compounds_for(sorted({g["species"] for g in groups.values()}))
    classes = {}
    for e in index.values():
        f = SITE_DATA / "engine" / f"{e['speciesId']}.json"
        if f.exists():
            classes.update({c["compoundId"]: c["compoundClass"] for c in json.loads(f.read_text())["compounds"]})

    pool, dropped = [], Counter()
    for (species, hist), g in sorted(groups.items()):
        mc = Counter()
        pmids = sorted({pm for k in g["pairKeys"] for pm in pair_pmids.get(k, [])})
        for pm in pmids:
            for x in (studies[pm]["preparations"] if pm in studies else []):
                lab, _ = modern_to_grid(x)
                if lab:
                    mc[lab] += 1
        if mc:
            modern, basis = sorted(mc.items(), key=lambda kv: (-kv[1], kv[0]))[0][0], "studies"
        else:
            modern, basis = default_modern, "default"
        if modern == hist:
            dropped["same modelled preparation"] += 1
            continue
        cand = R.Candidate(g["speciesId"], species, hist, modern)
        s = R.score(cand, comps[species], draws)
        if s["notRanked"]:
            dropped["no usable robust gap: " + s["notRanked"]] += 1
            continue
        differs = []
        for c in comps[species]:
            sf, df = draws.get(c, hist)
            sm, dm = draws.get(c, modern)
            if (sf["high"] - sf["low"]) > R.WIDTH_MAX or (sm["high"] - sm["low"]) > R.WIDTH_MAX:
                continue
            d = df - dm
            lo, med, hi = np.percentile(d, [5, 50, 95])
            if (lo > 0 or hi < 0) and abs(med) >= delta:
                differs.append(c.inchikey)
        e = index[species]
        top = sorted(g["indications"].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        pool.append({
            "id": f"{g['speciesId']}|{hist}|{modern}", "speciesId": g["speciesId"], "species": species,
            "historical": hist, "modern": modern, "modernBasis": basis, "modernStudyPreps": int(mc[modern]) if mc else 0,
            "indication": {"meshId": top, "label": g["indicationLabels"][top]},
            "indications": sorted(g["indications"]), "indicationLabels": g["indicationLabels"],
            "recipes": sorted(g["recipes"]), "sources": sorted(g["sources"]), "pmids": pmids,
            "gapP5": s["gapP5"], "gapP50": s["gapP50"], "gapP95": s["gapP95"], "pGapAboveTau": s["pGapAboveTau"],
            "compoundsUsed": s["compoundsUsed"], "compoundsExcludedWide": s["compoundsExcludedWide"],
            "differs": sorted(differs), "classes": sorted({classes.get(k, "other (heuristic)") for k in differs}),
            "toxicity": e["toxicityFlag"], "toxic": e["toxicityFlag"] == "toxic_reported",
            "toxicityNote": e.get("toxicityNote"),
        })
    out = {"species": len(approved), "speciesWithCandidates": len({c["species"] for c in pool}), "pool": len(pool),
           "toxicInPool": sum(c["toxic"] for c in pool), "defaultModern": default_modern, "dropped": dict(dropped),
           "rule": R.RULE, "differDelta": delta, "candidates": pool,
           "label": "candidates are hypotheses worth re-testing, never claims that a preparation works or is safe"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return {k: v for k, v in out.items() if k != "candidates"}
