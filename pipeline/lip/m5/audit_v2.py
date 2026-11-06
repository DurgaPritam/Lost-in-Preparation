"""Phase 5 audit v2: pre-registered re-analysis after v1's design flaw (docs/AUDIT_PROTOCOL_v2.md). No LLM.

Differences from v1 (m5/audit.py): logged M1 corrections applied to the pairs; species-level literature (Phase 5 prep)
filtered by MeSH descriptor or descendant; eligibility (the study prepared the plant material; no reviews, case reports,
surveys or pure-compound papers); lexicon v2; solvent equivalence classes with "no modern analogue" kept apart;
per-variable fidelity rates with bootstrap CIs. Outputs in data/interim/m5/v2/.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from ..http import CACHE, get_json
from ..paths import INTERIM
from . import audit as A
from . import pairs as P
from . import rules

OUT = INTERIM / "m5" / "v2"
LEX = rules.LEX_PATH.with_name("v2.toml")
SPARQL = "https://id.nlm.nih.gov/mesh/sparql"
EXCLUDED_TYPES = A.EXCLUDED_TYPES | {"Case Reports"}
SEED, B = 20261106, 2000
WINE_MAX = 0.20
VARS = ["solvent", "heat", "part", "freshOrDried", "filtration"]
NA = "no_analogue"


# --- MeSH descendants ---------------------------------------------------------------------------

def descendants(mesh_id: str) -> set[str]:
    q = ("PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#> PREFIX mesh: <http://id.nlm.nih.gov/mesh/> "
         "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
         f"SELECT DISTINCT ?label WHERE {{ ?d meshv:broaderDescriptor* mesh:{mesh_id} . ?d rdfs:label ?label }}")
    r = get_json("mesh_sparql", SPARQL, {"query": q, "format": "JSON", "limit": 10000, "year": "current"})
    return {b["label"]["value"] for b in r["results"]["bindings"]}


# --- equivalence classes (protocol §5) ----------------------------------------------------------

def hist_class(r: dict) -> str:
    v = sorted(set(r["solvent"]) - {"unknown"})
    if not v:
        return "unknown"
    if "honey" in v or "other" in v:
        return NA
    if v == ["water"]:
        return "aqueous"
    if v in (["vinegar"], ["vinegar", "water"]):
        return "acidified_aqueous"
    if v in (["wine"], ["water", "wine"]):
        return "low_ethanol"
    if v == ["oil"]:
        return "oil"
    if v == ["none"]:
        if r["part"] == "juice" or r["process"] == "expression":
            return "fresh_juice"
        if r["process"] == "powder":
            return "powder"
        return NA
    return NA


def modern_class(p, wine_max: float = WINE_MAX) -> str:
    c = p.solventClass
    if c == "unknown":
        return "unknown"
    if c == "water":
        return "aqueous"
    if c == "hydroethanolic":
        if p.ethanolFraction is None:
            return "hydroalcoholic_unstated"
        return "low_ethanol" if p.ethanolFraction <= wine_max else "high_ethanol"
    return {"acidified_aqueous": "acidified_aqueous", "wine": "low_ethanol", "juice": "fresh_juice", "powder": "powder",
            "oil": "oil"}.get(c, c)


def compare(h: dict, hcls: str, p, wine_max: float = WINE_MAX) -> dict:
    mc = modern_class(p, wine_max)
    if hcls == NA:
        sol = NA
    elif "unknown" in (hcls, mc) or (hcls == "low_ethanol" and mc == "hydroalcoholic_unstated"):
        sol = "unknown"
    else:
        sol = "match" if hcls == mc else "mismatch"
    out = {"solvent": sol}
    for f, g in (("heat", "heat"), ("part", "part"), ("freshOrDried", "freshOrDried"), ("filtered", "filtration")):
        a, b = h[f], getattr(p, f)
        out[g] = "unknown" if "unknown" in (a, b) else ("match" if a == b else "mismatch")
    if sol == NA:
        out["overall"] = NA
    elif "mismatch" in out.values():
        out["overall"] = "mismatch"
    elif sol == "match" and out["heat"] == "match":
        out["overall"] = "match"
    else:
        out["overall"] = "unknown"
    return out


def unit_status(vals: list[str]) -> str:
    """faithful / not_faithful / no_analogue / unknown over a unit's comparisons (overall, or one variable)."""
    if "match" in vals:
        return "match"
    real = [v for v in vals if v != NA]
    known = [v for v in real if v != "unknown"]
    if known and len(known) == len(real) and all(v == "mismatch" for v in known):
        return "mismatch"
    if vals and not real:
        return NA
    return "unknown"


def _rate(U: pd.DataFrame, col: str, rng_seed: int = SEED, boot: bool = True) -> dict:
    k = U[U[col].isin(["match", "mismatch"])]
    out = {"nKnown": int(len(k)), "nUnknown": int((U[col] == "unknown").sum()), "nNoAnalogue": int((U[col] == NA).sum())}
    if not len(k):
        return {"status": "not_computed", "value": None, "low": None, "high": None, **out}
    val = float((k[col] == "match").mean())
    lo = hi = None
    pairs = k.pairKey.unique()
    if boot and len(pairs) > 1:
        rng = np.random.default_rng(rng_seed)
        by = {p: g[col].values for p, g in k.groupby("pairKey")}
        vals = []
        for _ in range(B):
            s = np.concatenate([by[p] for p in rng.choice(pairs, len(pairs))])
            vals.append((s == "match").mean())
        lo, hi = (round(float(x), 4) for x in np.percentile(vals, [2.5, 97.5]))
    return {"status": "computed", "value": round(val, 4), "low": lo, "high": hi, **out}


# --- run ----------------------------------------------------------------------------------------

def run() -> dict:
    L = rules.lexicon(LEX)
    pairs = P.build(out_path=OUT / "pairs.json", corrections=True)
    recipes = {r["id"]: r for r in __import__("lip.m1.corrections", fromlist=["apply"]).apply(
        json.loads((INTERIM / "m1" / "predictions_approved.json").read_text()))}
    desc = {d: descendants(d) for d in sorted({p["indication"]["meshId"] for p in pairs["pairs"]})}
    lit = {}
    for f in (INTERIM / "m5" / "literature").glob("*.json"):
        d = json.loads(f.read_text())
        abstracts = json.loads((CACHE / "m5_abstracts" / f.name).read_text())
        lit[d["species"]] = [{**r, "abstract": abstracts.get(r["pmid"], "")} for r in d["records"]]
    excluded, coded = Counter(), {}
    pair_pmids, no_mesh = {}, Counter()
    for p in pairs["pairs"]:
        k = f"{p['speciesId']}|{p['indication']['meshId']}"
        d = desc[p["indication"]["meshId"]]
        pair_pmids[k] = [r["pmid"] for r in lit[p["species"]] if set(r["mesh"]) & d]
        no_mesh[p["species"]] = sum(1 for r in lit[p["species"]] if not r["mesh"])
    wanted = {i for ids in pair_pmids.values() for i in ids}
    recs = {r["pmid"]: r for rs in lit.values() for r in rs if r["pmid"] in wanted}
    for pmid, r in recs.items():
        if set(r["publicationTypes"]) & EXCLUDED_TYPES:
            excluded["publication type"] += 1
            continue
        if any(q.search(r["title"] + " " + (r["abstract"] or "")) for q in L.survey):
            excluded["survey"] += 1
            continue
        lic = r["licenceStatus"]
        mt = A.methods_text(r["pmcid"]) if lic["status"] == "pmc_oa" else None
        if mt:
            text, src = r["title"] + "\n\n" + mt, "pmc_fulltext"
        elif r["abstract"]:
            text, src = r["title"] + "\n\n" + r["abstract"], "abstract"
        else:
            excluded["no abstract and no open-access methods"] += 1
            continue
        preps = rules.extract(text, L)
        if not (any(x.solventClass != "unknown" for x in preps) or any(q.search(text) for q in L.plant_prep)):
            excluded["no prepared plant material stated"] += 1
            continue
        coded[pmid] = {"pmid": pmid, "title": r["title"], "pmcid": r["pmcid"], "licenceStatus": lic, "evidenceSource": src,
                       "extractor": L.version, "_preps": preps,
                       "preparations": [{"solvent": x.solvent, "solventClass": x.solventClass, "modernClass": modern_class(x),
                                         "solventText": x.solventText, "ethanolFraction": x.ethanolFraction, "heat": x.heat,
                                         "part": x.part, "freshOrDried": x.freshOrDried, "filtered": x.filtered, "flags": x.flags,
                                         "evidence": [{**e, "quote": e["quote"] if lic["status"] == "pmc_oa" else None} for e in x.evidence]}
                                        for x in preps]}
    units = []
    for p in pairs["pairs"]:
        k = f"{p['speciesId']}|{p['indication']['meshId']}"
        hist = []
        for hk, rids in p["preparations"].items():
            h = A.parse_key(hk)
            classes = {hist_class(recipes[r]) for r in rids}
            for c in classes:
                hist.append((hk, h, c))
        for pmid in pair_pmids[k]:
            if pmid not in coded:
                continue
            s = coded[pmid]
            row = {"pairKey": k, "species": p["species"], "mesh": p["indication"]["label"], "pmid": pmid,
                   "group": A._source_group(p["sources"]), "evidenceSource": s["evidenceSource"]}
            for wm, tag in ((WINE_MAX, ""), (0.15, "_w15"), (0.25, "_w25")):
                cmp = [compare(h, c, x, wm) for _, h, c in hist for x in s["_preps"]]
                if tag:
                    row["solvent" + tag] = unit_status([m["solvent"] for m in cmp])
                    continue
                row["overall"] = {"match": "faithful", "mismatch": "not_faithful"}.get(u := unit_status([m["overall"] for m in cmp]), u)
                for v in VARS:
                    row[v] = unit_status([m[v] for m in cmp])
                row["historicalClasses"] = ";".join(sorted({c for _, _, c in hist}))
            units.append(row)
    U = pd.DataFrame(units)
    ov = U.assign(o=U.overall.map({"faithful": "match", "not_faithful": "mismatch"}).fillna(U.overall))
    summary = {
        "label": "pre-registered re-analysis after v1's design flaw", "protocol": "docs/AUDIT_PROTOCOL_v2.md",
        "extractor": L.version, "indicationLexicon": pairs["indicationLexicon"], "m1CorrectionsApplied": pairs["m1CorrectionsApplied"],
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "retrieval": {"pairs": len(pairs["pairs"]), "source": "species-level literature (data/interim/m5/literature/), MeSH descriptor or descendant",
                      "pairsWithRecords": sum(1 for v in pair_pmids.values() if v), "recordsMatched": len(recs),
                      "recordsWithoutMeshInSpeciesLiterature": int(sum(no_mesh.values())), "excluded": dict(excluded),
                      "eligibleStudies": len(coded), "byEvidenceSource": dict(Counter(s["evidenceSource"] for s in coded.values()))},
        "units": {"n": int(len(U)), "pairsWithUnits": int(U.pairKey.nunique()) if len(U) else 0,
                  "overallStatus": U.overall.value_counts().to_dict() if len(U) else {}},
        "overallFidelity": _rate(ov, "o"),
        "perVariableFidelity": {v: _rate(U, v) for v in VARS},
        "solventWineCutoffSensitivity": {"0.15": _rate(U, "solvent_w15", boot=False), "0.20": _rate(U, "solvent", boot=False),
                                         "0.25": _rate(U, "solvent_w25", boot=False)},
        "bySourceGroup": {g: _rate(ov[ov.group == g], "o") for g in ("culpeper", "pliny_only")},
        "byEvidenceSource": {g: _rate(ov[ov.evidenceSource == g], "o", boot=False) for g in ("pmc_fulltext", "abstract")},
    }
    of = summary["overallFidelity"]
    summary["overallNotFaithfulShare"] = (None if of["value"] is None else round(1 - of["value"], 4))
    OUT.mkdir(parents=True, exist_ok=True)
    U.to_csv(OUT / "audit_units.csv", index=False)
    (OUT / "audit_studies.json").write_text(json.dumps({"extractor": L.version, "pairPmids": pair_pmids,
                                                         "studies": [{k: v for k, v in s.items() if not k.startswith("_")} for s in coded.values()]},
                                                        ensure_ascii=False, indent=1))
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary
