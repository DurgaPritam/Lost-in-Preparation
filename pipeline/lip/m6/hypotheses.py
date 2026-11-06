"""Phase 6: rank species–indication pairs that modern studies never tested faithfully (docs/AUDIT_PROTOCOL_v1.md §7).

Candidates: pairs with at least one study whose status is known and NO faithful study (neverTestedFaithfully).
  faithful preparation  the pair's historical preparation with most recipes that maps to an M4 preparation
                        (HEURISTIC map, HIST_MAP below)
  modern preparation    the most frequent M4-mappable modern solvent among the pair's studies (water keeps its stated
                        heat; methanol, hydroethanolic and hexane use the M4 maceration presets; when a study's heat is
                        unstated the preset is used and a caveat is recorded)
Scored and ranked by the M6 rule (m6/ranking.py, contract P35). Outputs are HYPOTHESES WORTH RE-TESTING, never claims
that a preparation works or is safe. Toxicity: the curated, AI-drafted, unverified entries (data/reference/
toxicity_curated.csv); a species without one is "unknown" (not evidence of safety).
Outputs: site-data/hypotheses.json (contract), data/interim/m6/hypotheses.csv, data/interim/m6/hypotheses_summary.json.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone

import pandas as pd

from contract import models as C

from ..m4 import chem
from ..m4 import model as M
from ..paths import INTERIM, ROOT, SITE_DATA
from . import ranking as R

OUT = INTERIM / "m6"


def hist_to_grid(p: dict) -> str | None:
    """Historical preparation (fields of a recipe) -> M4 preparation label (HEURISTIC; protocol §7)."""
    sol = sorted(set(p["solvent"]) - {"unknown"})
    heat, proc, part = p["heat"], p["process"], p["part"]
    if sol == ["water"]:
        if heat == "boiled":
            return "distilled water" if proc == "distillation" else "decoction in water"
        return {"cold": "cold water infusion", "warm": "hot water infusion (tea)"}.get(heat)
    if sol == ["wine"]:
        return {"cold": "steeped in wine", "boiled": "decoction in wine"}.get(heat)
    if sol == ["vinegar"] and heat == "cold":
        return "steeped in vinegar"
    if sol == ["oil"] and heat == "warm":
        return "infused oil"
    if sol in ([], ["none"]):
        if part == "juice" and heat in ("cold", "unknown"):
            return "fresh juice"
        if proc == "powder":
            return "powder taken whole"
    return None


def modern_to_grid(prep: dict) -> tuple[str | None, bool]:
    """Study preparation -> (M4 preparation label, heat-unstated caveat)."""
    s, h = prep["solvent"], prep["heat"]
    if s == "water":
        return {"cold": "cold water infusion", "warm": "hot water infusion (tea)", "boiled": "decoction in water"}.get(h), False
    lab = {"methanol": "modern methanol extract", "hydroethanolic": "modern 70% ethanol extract",
           "hexane": "low-temperature nonpolar extract (hexane)"}.get(s)
    return lab, (lab is not None and h == "unknown")


def compounds_for(species: list[str]) -> dict[str, list[M.Compound]]:
    occ = pd.read_parquet(INTERIM / "m3" / "occurrences.parquet")
    comp = pd.read_parquet(INTERIM / "m3" / "compounds.parquet").drop_duplicates("inchikey").set_index("inchikey")
    out = {}
    for name in species:
        cs = []
        for k in sorted(set(occ[occ.acceptedName == name].inchikey)):
            if k in comp.index and isinstance(comp.loc[k].smiles, str):
                d = chem.describe(comp.loc[k].smiles)
                if d is not None:
                    cs.append(M.Compound(k, d["logP"], d["basicN"], d["heatFlags"], d["volatile"], d["mw"]))
        out[name] = cs
    return out


def run() -> dict:
    pairs = json.loads((INTERIM / "m5" / "pairs.json").read_text())
    units = pd.read_csv(INTERIM / "m5" / "audit_units.csv", dtype={"pmid": str})
    studies = {s["pmid"]: s for s in json.loads((INTERIM / "m5" / "audit_studies.json").read_text())["studies"]}
    pair_pmids = json.loads((INTERIM / "m5" / "audit_studies.json").read_text())["pairPmids"]
    recipes = {r["id"]: r for r in json.loads((INTERIM / "m1" / "predictions_approved.json").read_text())}
    tox = pd.read_csv(ROOT / "data" / "reference" / "toxicity_curated.csv").set_index("acceptedName")
    cfg = M.load_config()
    sd = M.descriptor_sd("rdkit")["sd"]
    draws = R.Draws(cfg, sd)
    skipped = Counter()
    rows, meta = [], []
    cands = []
    for p in pairs["pairs"]:
        key = f"{p['speciesId']}|{p['indication']['meshId']}"
        u = units[units.pairKey == key]
        if not len(u) or (u.status != "unknown").sum() == 0:
            skipped["no study with a known status"] += 1
            continue
        if (u.status == "faithful").any():
            skipped["tested faithfully at least once"] += 1
            continue
        # faithful preparation: most recipes among grid-mappable historical preparations
        fc = Counter()
        fkey = {}
        for hk, rids in p["preparations"].items():
            for rid in rids:
                lab = hist_to_grid(recipes[rid])
                if lab:
                    fc[lab] += 1
                    fkey.setdefault(lab, hk)
        if not fc:
            skipped["no historical preparation the model represents"] += 1
            continue
        faithful = sorted(fc.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        mc, caveat_heat = Counter(), Counter()
        for pmid in pair_pmids.get(key, []):
            for x in (studies[pmid]["preparations"] if pmid in studies else []):
                lab, cav = modern_to_grid(x)
                if lab:
                    mc[lab] += 1
                    caveat_heat[lab] += int(cav)
        if not mc:
            skipped["no modern preparation the model represents"] += 1
            continue
        modern = sorted(mc.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        if modern == faithful:
            skipped["same modelled preparation (mismatch only on fields the model does not represent)"] += 1
            continue
        cands.append((p, key, faithful, fkey[faithful], fc[faithful], modern, mc[modern], caveat_heat[modern], u))
    comps = compounds_for(sorted({c[0]["species"] for c in cands}))
    for p, key, faithful, fk, fn, modern, mn, mcav, u in cands:
        s = R.score(R.Candidate(p["speciesId"], p["species"], faithful, modern), comps[p["species"]], draws)
        rows.append({**s, "pairKey": key, "mesh": p["indication"]["label"], "meshId": p["indication"]["meshId"],
                     "faithfulKey": fk, "faithfulRecipes": fn, "modernStudyPreps": mn, "modernHeatUnstated": mcav,
                     "studiesKnown": int((u.status != "unknown").sum()), "studiesUnknown": int((u.status == "unknown").sum()),
                     "attestationCount": p["attestationCount"], "sources": ";".join(p["sources"])})
        meta.append(p)
    df = R.rank(pd.DataFrame(rows)) if rows else pd.DataFrame(rows)
    hyps = []
    pm = {p["speciesId"] + "|" + p["indication"]["meshId"]: p for p in meta}
    for r in df[df["rank"].notna()].itertuples() if len(df) else []:
        p = pm[r.pairKey]
        gap, gr = R.to_contract(df.loc[r.Index])
        t = tox.loc[p["species"]] if p["species"] in tox.index else None
        caveats = ["hypothesis worth re-testing, not a claim that the preparation works or is safe",
                   "profile gap from predicted compound likelihoods (model), equal weights: LOTUS has no abundance data",
                   "historical indication mapped to MeSH by a heuristic lexicon; the historical term is not a modern diagnosis"]
        if r.modernHeatUnstated:
            caveats.append(f"modern preparation modelled with the M4 maceration preset: heat unstated in {r.modernHeatUnstated} of "
                           f"{r.modernStudyPreps} study preparations")
        if all(s.startswith("pliny") for s in p["sources"]):
            caveats.append("attested only by Pliny (lower confidence)")
        if r.studiesUnknown:
            caveats.append(f"{r.studiesUnknown} retrieved studies could not be coded as faithful or not (unknown fields)")
        hyps.append(C.Hypothesis(
            rank=int(r.rank), speciesId=p["speciesId"], indication=C.MeshTerm(**p["indication"]),
            indicationAsWritten=p["indicationsAsWritten"][0], faithfulPreparation=r.faithfulKey,
            faithfulPreparationText=r.faithful, attestationCount=int(r.attestationCount), profileGap=gap, gapRanking=gr,
            neverTestedFaithfully=True,
            toxicityFlag=t["toxicity"] if t is not None else "unknown",
            toxicityNote=(f"{t['summary']} (source: {t['sourceName']}; AI-drafted, unverified)" if t is not None else
                          "no curated toxicity entry; unknown is not evidence of safety"),
            caveats=caveats,
            evidenceTrail=[*(C.EvidenceItem(kind="recipe", ref=rid) for rid in p["recipes"][:10]),
                           *(C.EvidenceItem(kind="study", ref=f"pmid:{x}") for x in units[units.pairKey == r.pairKey].pmid[:10]),
                           C.EvidenceItem(kind="profile", ref=f"{p['speciesId']}:{r.faithful} vs {r.modern}"),
                           C.EvidenceItem(kind="species", ref=p["speciesId"])]))
    OUT.mkdir(parents=True, exist_ok=True)
    if len(df):
        df.to_csv(OUT / "hypotheses.csv", index=False)
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "hypotheses.json").write_text(json.dumps([h.model_dump(mode="json") for h in sorted(hyps, key=lambda h: h.rank)],
                                                          ensure_ascii=False, indent=1))
    summary = {"protocol": "docs/AUDIT_PROTOCOL_v1.md §7", "rule": R.RULE, "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "pairs": len(pairs["pairs"]), "candidates": len(rows), "ranked": len(hyps),
               "notRanked": int((df.notRanked != "").sum()) if len(df) else 0, "skipped": dict(skipped),
               "label": "hypotheses worth re-testing; ranks never claim efficacy or safety"}
    (OUT / "hypotheses_summary.json").write_text(json.dumps(summary, indent=2))
    return summary
