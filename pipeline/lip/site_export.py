"""Phase 7 preparation: write the remaining contract files, prune stale ones, validate every site-data file against
the contract (contract/models.py, v1.5), and generate docs/SITE_DATA_STATUS.md.

  recipes.json     the M1 session extraction (gold sample + Phase 5 species), as validated (one attempt, verbatim
                   quotes). Logged corrections (config/m1_corrections.csv) are in `corrections` (v1.6, P37a); the
                   fields themselves stay as extracted.
  audit_v2.json    audit v2 reshaped into contract records (v1.6, P37c); case_studies.json: the liquorice case (P37d).
  metrics.json     also reportingGap (P37b), auditV2 (P37c), per-source disputed shares in nameResolution.
  species.json     per recipe: the M2 candidates (rank 1–3) of the name entry the recipe's plant name is attributable to
                   (same attribution rule as the Phase 5 pairs); name entries a reviewer removed from a species are dropped.
  profiles/        only species in the current headline set; others are moved to data/interim/m4/profiles_not_headline/.
  metrics.json     headlineMatchRate filled from the frozen audit v1 (share faithful), with its note.
Run: python -m lip site
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone

import pandas as pd

from contract import models as C

from .m5.pairs import attributable
from .paths import INTERIM, ROOT, SITE_DATA

STATUS_DOC = ROOT / "docs" / "SITE_DATA_STATUS.md"
VALIDATION = INTERIM / "site_validation.json"


def recipes() -> list[dict]:
    out, seen = [], {}
    for scope in ("sample", "approved"):
        for r in json.loads((INTERIM / "m1" / f"predictions_{scope}.json").read_text()):
            if r["id"] in seen:
                a, b = (dict(x, provenance=None) for x in (seen[r["id"]], r))
                if a != b:
                    raise ValueError(f"recipe {r['id']} differs between scopes")
                continue
            seen[r["id"]] = r
            out.append(r)
    return out


def _entries(row, inv: pd.DataFrame) -> list[str]:
    if row.source_id == "culpeper-1652":
        return [f"culpeper-1652:{row.entry_slug}"]
    if row.source_id == "culpeper-1850" and isinstance(row.crosswalk_1652, str):
        return [f"culpeper-1652:{row.crosswalk_1652}"]
    if row.source_id.startswith("pliny") and not pd.isna(row.book):
        pre = f"pliny-nh:b{int(row.book):02d}:{row.entry_slug}:"
        return list(inv.index[inv.index.str.startswith(pre)])
    return []


def species(recs: list[dict]) -> tuple[list[dict], dict]:
    from .m1.prompt import load_passages
    pas = load_passages().set_index("passage_id")
    inv = pd.read_parquet(INTERIM / "m2" / "name_inventory.parquet").set_index("nameId")
    cand = pd.read_parquet(INTERIM / "m2" / "name_candidates.parquet")
    cand = cand[cand.acceptedName.notna() & (cand["rank"] >= 1)]
    nx = pd.read_csv(ROOT / "config" / "name_entry_exclusions.csv")
    drop = set(zip(nx.nameId, nx.species))
    tox = pd.read_csv(ROOT / "data" / "reference" / "toxicity_curated.csv").set_index("acceptedName")
    by_name = {k: g.sort_values("rank") for k, g in cand.groupby("nameId")}
    out, counts = [], {"recipes": len(recs), "withCandidates": 0, "noNameEntry": 0, "notAttributable": 0, "nameUnresolved": 0, "droppedByReviewer": 0}
    for r in recs:
        row = pas.loc[r["passage"]["passageId"]]
        ids = [n for n in _entries(row, inv) if n in inv.index]
        if not ids:
            counts["noNameEntry"] += 1
            continue
        hit = [n for n in ids if attributable(r["plantNameAsWritten"],
                                              (json.loads(inv.loc[n, "queries"]) if isinstance(inv.loc[n, "queries"], str) else list(inv.loc[n, "queries"])))]
        if not hit:
            counts["notAttributable"] += 1
            continue
        n_before = len(out)
        for n in hit:
            for c in (by_name.get(n, pd.DataFrame()).itertuples()):
                if (n, c.acceptedName) in drop:
                    counts["droppedByReviewer"] += 1
                    continue
                t = tox.loc[c.acceptedName] if c.acceptedName in tox.index else None
                out.append(C.SpeciesCandidate(
                    id=f"{r['id']}|{n}|r{int(c.rank)}", recipeId=r["id"], speciesId=c.wfoId if c.inWFO else None,
                    nameAsWritten=inv.loc[n, "nameAsWritten"], acceptedName=c.acceptedName, wfoId=c.wfoId if c.inWFO else None,
                    confidence=round(float(c.confidence), 4), basis=c.basis,
                    basisRef=c.basisRef if isinstance(c.basisRef, str) else None, disputed=bool(c.disputed),
                    toxicityFlag=t["toxicity"] if t is not None else "unknown",
                    toxicityNote=(f"{t['summary']} (AI-drafted, unverified)" if t is not None else None)).model_dump(mode="json"))
        if len(out) > n_before:
            counts["withCandidates"] += 1
        else:
            counts["nameUnresolved"] += 1
    return out, counts


def prune_profiles() -> list[str]:
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    keep = set(ss[ss.headline].wfoId)
    idx_path = SITE_DATA / "profiles" / "index.json"
    idx = json.loads(idx_path.read_text())
    moved = []
    dest = INTERIM / "m4" / "profiles_not_headline"
    for e in idx:
        if e["speciesId"] not in keep:
            dest.mkdir(parents=True, exist_ok=True)
            src = SITE_DATA / e["file"]
            if src.exists():
                shutil.move(str(src), dest / src.name)
            moved.append(e["acceptedName"])
    idx_path.write_text(json.dumps([e for e in idx if e["speciesId"] in keep], ensure_ascii=False, indent=1))
    names = dict(zip(ss.wfoId, ss.acceptedName))
    return sorted(names.get(f.stem, f.stem) for f in dest.glob("*.json")) if dest.exists() else moved


def headline_match_rate() -> None:
    a = json.loads((INTERIM / "m5" / "audit_summary.json").read_text())["headline"]
    p = SITE_DATA / "metrics.json"
    m = json.loads(p.read_text())
    m["headlineMatchRate"] = C.Metric(
        status="computed", value=round(1 - a["value"], 4), low=round(1 - a["high"], 4), high=round(1 - a["low"], 4), n=a["nKnown"],
        sourceFile="data/interim/m5/audit_summary.json",
        note=(f"audit v1 as pre-registered (docs/AUDIT_PROTOCOL_v1.md): share of (pair, study) units faithful to a historical preparation, "
              f"among {a['nKnown']} with a known status ({a['nUnknown']} unknown); 95% CI bootstrap over pairs. v1's solvent rule makes "
              "non-water recipes unmatchable, so this mostly reflects the protocol; audit v2 and the reporting-gap headline are in RESULTS.md "
              "(metrics.reportingGap and metrics.auditV2)")).model_dump(mode="json")
    p.write_text(json.dumps(C.Metrics.model_validate(m).model_dump(mode="json"), ensure_ascii=False, indent=1))


def validate() -> dict:
    res = {}
    files = {"sources.json": "sources.json", "recipes.json": "recipes.json", "species.json": "species.json",
             "profiles/index.json": "profiles.index.json", "audit.json": "audit.json", "audit_v2.json": "audit_v2.json",
             "case_studies.json": "case_studies.json", "hypotheses.json": "hypotheses.json", "metrics.json": "metrics.json"}
    for path, key in files.items():
        data = json.loads((SITE_DATA / path).read_text())
        model = C.FILE_MODELS[key]
        if key in C.ARRAY_FILES:
            recs = [model.model_validate(x) for x in data]
            res[path] = {"records": len(recs), "mock": sum(r.mock for r in recs), "valid": True}
        else:
            model.model_validate(data)
            res[path] = {"records": 1, "mock": int(data.get("mock", False)), "valid": True}
    idx = json.loads((SITE_DATA / "profiles" / "index.json").read_text())
    n = 0
    for e in idx:
        n += len([C.Profile.model_validate(x) for x in json.loads((SITE_DATA / e["file"]).read_text())])
    res["profiles/<speciesId>.json"] = {"files": len(idx), "records": n, "valid": True}
    stray = sorted(p.name for p in (SITE_DATA / "profiles").glob("wfo-*.json") if f"profiles/{p.name}" not in {e["file"] for e in idx})
    res["strayProfileFiles"] = stray
    eng = SITE_DATA / "engine"  # v1.7 (P38): Preparation Lab inputs, written by `python -m lip m4 engine-export`
    if eng.exists():
        model = C.EngineModel.model_validate(json.loads((eng / "model.json").read_text()))
        sp = [C.EngineSpecies.model_validate(json.loads((eng / f"{e['speciesId']}.json").read_text())) for e in idx]
        par = [C.EngineParityCase.model_validate(x) for x in json.loads((eng / "parity.json").read_text())]
        if any(x.modelVersion != model.modelVersion for x in sp):
            raise ValueError("site-data/engine: species files and model.json have different model versions")
        res["engine/"] = {"files": 2 + len(sp), "species": len(sp), "compounds": sum(len(x.compounds) for x in sp),
                          "parityCases": len(par), "modelVersion": model.modelVersion, "valid": True}
        res["strayEngineFiles"] = sorted(p.name for p in eng.glob("*.json")
                                         if p.name not in {"model.json", "parity.json", *(f"{e['speciesId']}.json" for e in idx)})
    return res


def corrections_by_recipe() -> dict[str, list[dict]]:
    t = pd.read_csv(ROOT / "config" / "m1_corrections.csv", dtype=str).fillna("")
    out: dict[str, list[dict]] = {}
    for c in t.to_dict("records"):
        out.setdefault(c["recipeId"], []).append({k: c[k] for k in ("field", "from", "to", "reason", "evidence", "requestedBy", "appliedBy", "date")})
    return out


def _metric(x: dict, note: str, source: str) -> dict:
    return C.Metric(status="computed" if x.get("value") is not None else "not_computed", value=x.get("value"), low=x.get("low"),
                    high=x.get("high"), n=x.get("n") if "n" in x else x.get("nKnown"), sourceFile=source, note=note).model_dump(mode="json")


def reporting_gap_metrics() -> dict:
    g = json.loads((INTERIM / "m5" / "reporting_gap.json").read_text())
    src = "data/interim/m5/reporting_gap.json"
    out = {}
    for setname, blocks in g["sets"].items():
        for part, b in blocks.items():
            if part == "extractor":
                continue
            for var, x in b.items():
                out[f"{setname}:{part}:{var}"] = _metric(
                    x, f"{x['k']}/{x['n']} studies ({setname}, coded from {'all texts' if part == 'all' else part}) state "
                       f"{'none of the five variables' if var == 'none' else 'all five variables' if var == 'all five' else var}; Wilson 95% CI; "
                       "stated = coded by the rule-based extractor (heuristic, hand-check pending)"
                       + ("; eligibility partly selects on a stated solvent, so this share is inflated by construction" if setname == "prepared" and var == "solvent" else ""), src)
    v3 = g["v3Screening"]
    out["v3:screening"] = _metric(v3["share"], f"{v3['eligibleScreenings']} of {v3['screeningsWithTablesExamined']} article screenings whose tables "
                                                f"were examined ({v3['distinctArticlesWithTablesExamined']} distinct articles) compared two preparations of "
                                                "the same plant material in a usable table; pre-registered v3 screening; Wilson 95% CI", src)
    return out


def audit_v2() -> tuple[list[dict], dict]:
    """Reshape the frozen audit v2 outputs into contract records (no re-analysis)."""
    from .m1.corrections import apply
    from .m5 import audit as A
    from .m5 import audit_v2 as V
    from .m5.rules import Prep
    a = json.loads((INTERIM / "m5" / "v2" / "audit_summary.json").read_text())
    pairs = json.loads((INTERIM / "m5" / "v2" / "pairs.json").read_text())
    st = json.loads((INTERIM / "m5" / "v2" / "audit_studies.json").read_text())
    studies = {s["pmid"]: s for s in st["studies"]}
    meta = {}
    for f in (INTERIM / "m5" / "literature").glob("*.json"):
        for r in json.loads(f.read_text())["records"]:
            meta[r["pmid"]] = r
    recipes = {r["id"]: r for r in apply(json.loads((INTERIM / "m1" / "predictions_approved.json").read_text()))}
    recs = []
    for p in pairs["pairs"]:
        k = f"{p['speciesId']}|{p['indication']['meshId']}"
        ids = [i for i in st["pairPmids"].get(k, []) if i in studies]
        for hk, rids in p["preparations"].items():
            h = A.parse_key(hk)
            classes = sorted({V.hist_class(recipes[r]) for r in rids})
            rows, stat = [], []
            for pmid in ids:
                s = studies[pmid]
                per = []
                for x in s["preparations"]:
                    pr = Prep(**{f: x[f] for f in ("solvent", "solventClass", "solventText", "ethanolFraction", "heat", "part", "freshOrDried", "filtered")})
                    ms = [V.compare(h, c, pr) for c in classes]
                    m = next((m for m in ms if m["overall"] == "match"), None) or next((m for m in ms if m["overall"] == "mismatch"), None) or ms[0]
                    per.append(m["overall"])
                    snippet = None
                    sev = next((e for e in x["evidence"] if e["field"] == "solvent"), None)
                    if sev and sev.get("quote"):
                        snippet = sev["quote"]
                    rows.append(C.Study(pmid=pmid, doi=meta.get(pmid, {}).get("doi"), title=s["title"], year=meta.get(pmid, {}).get("year"),
                                        solvent=x["solvent"], solventText=x["solventText"], ethanolFraction=x["ethanolFraction"], heat=x["heat"],
                                        part=x["part"], freshOrDried=x["freshOrDried"], filtered=x["filtered"], match=C.StudyMatch(**m),
                                        unknownFields=[f for f in ("solvent", "heat", "part", "freshOrDried", "filtered") if x[f] == "unknown"],
                                        evidenceSource=s["evidenceSource"], methodsSnippet=snippet))
                u = V.unit_status(per)
                stat.append({"match": "faithful", "mismatch": "not_faithful"}.get(u, u))
            nk = sum(x in ("faithful", "not_faithful") for x in stat)
            recs.append(C.AuditRecord(speciesId=p["speciesId"], indication=C.MeshTerm(**p["indication"]),
                                      indicationAsWritten=p["indicationsAsWritten"][0], historicalPreparation=hk, historicalRecipeIds=rids,
                                      studies=rows, matchRate=C.Rate(value=round(sum(x == "faithful" for x in stat) / nk, 4) if nk else None,
                                                                     nKnown=nk, nUnknown=sum(x == "unknown" for x in stat))).model_dump(mode="json", by_alias=True))
    src = "data/interim/m5/v2/audit_summary.json"
    of = a["overallFidelity"]
    sec = C.AuditV2Section(
        label=a["label"], protocol=a["protocol"],
        overallFidelity=_metric(of, f"share of (pair, eligible study) units faithful to a historical preparation; {of['nKnown']} known, "
                                    f"{of['nUnknown']} unknown, {of['nNoAnalogue']} with no modern analogue; bootstrap 95% CI over pairs", src),
        overallNotFaithfulShare=_metric({"value": a["overallNotFaithfulShare"], "nKnown": of["nKnown"],
                                         "low": None if of["high"] is None else round(1 - of["high"], 4),
                                         "high": None if of["low"] is None else round(1 - of["low"], 4)},
                                        "share not faithful, for comparison with v1", src),
        perVariableFidelity={v: _metric(x, f"{v}: share of units matching; {x['nKnown']} known, {x['nUnknown']} unknown"
                                           + (f", {x['nNoAnalogue']} with no modern analogue" if x.get("nNoAnalogue") else "") + "; bootstrap 95% CI", src)
                             for v, x in a["perVariableFidelity"].items()},
        solventWineCutoffSensitivity={c: _metric(x, f"solvent match rate with the wine cut-off at {c} v/v ethanol", src)
                                      for c, x in a["solventWineCutoffSensitivity"].items()},
        units=a["units"]["n"], unknownUnits=a["units"]["overallStatus"].get("unknown", 0),
        noModernAnalogueUnits=a["units"]["overallStatus"].get("no_analogue", 0), eligibleStudies=a["retrieval"]["eligibleStudies"],
        pairsWithRecords=a["retrieval"]["pairsWithRecords"], pairs=a["retrieval"]["pairs"])
    return recs, sec.model_dump(mode="json")


def case_studies() -> list[dict]:
    c = json.loads((INTERIM / "m6" / "liquorice_case.json").read_text())
    from .m1.prompt import load_passages
    pas = load_passages().set_index("passage_id")
    titles = {s["id"]: s["title"] for s in json.loads((SITE_DATA / "sources.json").read_text())}
    ev = []
    for e in c["evidence"]:
        row = pas.loc[e["passageId"]]
        ev.append({"passageId": e["passageId"], "sourceId": row.source_id, "citation": titles.get(row.source_id, row.source_id), "text": e["text"]})
    gap = lambda x: {"value": x["gapP50"], "low": x["gapP5"], "high": x["gapP95"]}
    pairs = json.loads((INTERIM / "m5" / "pairs.json").read_text())
    ind = next(p["indication"] for p in pairs["pairs"] if p["species"] == c["species"] and p["indication"]["label"] == c["indication"])
    sid = next(p["speciesId"] for p in pairs["pairs"] if p["species"] == c["species"])
    rec = C.CaseStudy(id="liquorice", title="Liquorice “juice”", speciesId=sid, indication=ind, primaryRecipeId=c["recipeId"],
                      recipeQuote=c["recipeQuote"],
                      extractedAs={k: "+".join(v) if isinstance(v, list) else v for k, v in c["extractedAs"].items()},
                      correctedTo=c["correctedTo"], correctedRecipeIds=[c["recipeId"]] + c["otherLiquoriceRecipesCorrected"], evidence=ev,
                      before={**{k: c["before"][k] for k in ("faithful", "modern", "rank", "rankedOf")}, "gap": gap(c["before"])},
                      after={**{k: c["after"][k] for k in ("faithful", "modern", "rank", "rankedOf")}, "gap": gap(c["after"])},
                      label=c["label"])
    return [rec.model_dump(mode="json")]


def source_disputed_shares() -> dict:
    from .m2.evaluate import wilson
    s = json.loads((INTERIM / "m2" / "name_resolution_summary.json").read_text())
    out = {}
    for src, v in s.items():
        key = "culpeper" if src.startswith("culpeper") else "pliny" if src.startswith("pliny") else src
        cur = out.setdefault(key, {"resolved": 0, "disputed": 0})
        cur["resolved"] += v["resolved"]
        cur["disputed"] += v["disputed"]
    res = {}
    for key, v in out.items():
        lo, hi = wilson(v["disputed"], v["resolved"])
        res[f"disputedShare:{key}"] = C.Metric(status="computed", value=round(v["disputed"] / v["resolved"], 4), low=round(lo, 4), high=round(hi, 4),
                                                n=v["resolved"], sourceFile="data/interim/m2/name_resolution_summary.json",
                                                note=f"share of resolved names flagged disputed, {key} (Culpeper = the 1652 herbal; the 1850 edition "
                                                     "is resolved through its 1652 entry); descriptive").model_dump(mode="json")
    return res


def extend_metrics() -> None:
    p = SITE_DATA / "metrics.json"
    m = json.loads(p.read_text())
    m["contractVersion"] = C.CONTRACT_VERSION
    m["reportingGap"] = reporting_gap_metrics()
    m["nameResolution"] = {k: v for k, v in m["nameResolution"].items() if not k.startswith("disputedShare:")} | source_disputed_shares()
    recs, sec = audit_v2()
    m["auditV2"] = sec
    (SITE_DATA / "audit_v2.json").write_text(json.dumps(recs, ensure_ascii=False, indent=1))
    p.write_text(json.dumps(C.Metrics.model_validate(m).model_dump(mode="json"), ensure_ascii=False, indent=1))


def run() -> dict:
    recs = recipes()
    cor = corrections_by_recipe()
    for r in recs:
        r["corrections"] = cor.get(r["id"], [])
    for r in recs:
        C.Recipe.model_validate(r)
    (SITE_DATA / "recipes.json").write_text(json.dumps(recs, ensure_ascii=False, indent=1))
    sp, counts = species(recs)
    (SITE_DATA / "species.json").write_text(json.dumps(sp, ensure_ascii=False, indent=1))
    moved = prune_profiles()
    headline_match_rate()
    extend_metrics()
    (SITE_DATA / "case_studies.json").write_text(json.dumps(case_studies(), ensure_ascii=False, indent=1))
    val = validate()
    out = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "contractVersion": C.CONTRACT_VERSION,
           "files": val, "speciesCounts": counts, "profilesMovedOut": moved,
           "correctionsInRecipes": sorted(cor)}
    VALIDATION.write_text(json.dumps(out, indent=2))
    write_status(out)
    return out


def write_status(v: dict) -> None:
    f = v["files"]
    g = lambda k: f[k]["records"]
    h = json.loads((INTERIM / "m6" / "hypotheses_summary.json").read_text())
    L = ["# site-data status (Phase 7 preparation)", "",
         f"Generated by `python -m lip site` on {v['generatedAt'][:10]} (`data/interim/site_validation.json`). Do not edit by hand.", "",
         f"Every file below **validates against contract v{v['contractVersion']}** (`contract/models.py`). No record is mock "
         f"({sum(x.get('mock', 0) for x in f.values() if isinstance(x, dict))} mock records). The website (`site/`) reads these files at build time.", "",
         "Status words: **validated** = checked against an independent, non-AI reference; *provisional* = AI-made or checked only against "
         "AI-made references; pending = waiting on human work.", "",
         "| File | Records | Content status | What is pending |", "|---|---|---|---|",
         f"| `sources.json` | {g('sources.json')} | **validated**: checksums and licences of the digitised sources; ingestion tested against the source files | — |",
         f"| `recipes.json` | {g('recipes.json')} | *provisional*: written by Claude in a Claude Code session (prompt v3); every quote passed the verbatim check | human gold annotation (50 passages) and 15-passage re-annotation; {len(v['correctionsInRecipes'])} recipes carry logged corrections in `corrections` (P37a) |",
         f"| `species.json` | {g('species.json')} | *provisional*: M2 candidates (GBIF/WFO evidence, heuristic weights) for {v['speciesCounts']['withCandidates']} recipes; "
         f"{v['speciesCounts']['notAttributable']} recipes name a plant other than their entry's, {v['speciesCounts']['noNameEntry']} have no name entry and {v['speciesCounts']['nameUnresolved']} have an entry name M2 did not resolve, so they get no candidate | 30-name scholarly identification check |",
         f"| `profiles/index.json` + {f['profiles/<speciesId>.json']['files']} species files | {g('profiles/index.json')} species, {f['profiles/<speciesId>.json']['records']} profiles | "
         "logP descriptor **validated** against experiment; preparation factors *heuristic*; aqueous preparations unvalidated; toxicity entries *provisional* (AI-drafted) | toxicity review |",
         f"| `audit.json` | {g('audit.json')} | audit **v1 as pre-registered**, rule-based coding (frozen) | 40-study hand-check of the coding |",
         f"| `audit_v2.json` | {g('audit_v2.json')} | audit **v2**, pre-registered re-analysis after v1's design flaw (frozen; P37c) | 40-study hand-check; small n |",
         f"| `case_studies.json` | {g('case_studies.json')} | the liquorice extraction correction and its effect on Phase 6 (P37d) | — |",
         f"| `hypotheses.json` | {g('hypotheses.json')} | Phase 6 on audit v1 with logged corrections ({h['ranked']} hypotheses worth re-testing) | depends on the hand-check and the unvalidated aqueous model |",
         *([f"| `engine/` (model.json + {f['engine/']['species']} species files + parity.json) | {f['engine/']['compounds']} compounds, "
            f"{f['engine/']['parityCases']} parity cases | inputs of the preparation model for the in-browser Preparation Lab (P38, approved); "
            "the same model inputs as the profiles, self-checked against them; heuristic factors labelled | — |"] if 'engine/' in f else []),
         "| `metrics.json` | 1 | extraction run, name resolution, logP error, artemisinin check, `headlineMatchRate` (audit v1); AI-reference results only under `provisional` | gold-set F1 and annotator self-consistency (not computed until annotation exists) |",
         "", "## Added in contract v1.6 (P37, approved by the project lead; P37d added for the case-study page)", "",
         "- `recipes.json` `corrections` (P37a), `metrics.json` `reportingGap` (P37b) and `auditV2` (P37c), `audit_v2.json` (P37c), "
         "`case_studies.json` (P37d); `MatchCode` gains `no_analogue` (audit v2 only).",
         "", "## Changes made for Phase 7", "",
         f"- `recipes.json` and `species.json` written (they were missing).",
         f"- Profiles moved out of `site-data/` because the species is no longer in the headline set: {', '.join(v['profilesMovedOut']) or 'none'} "
         "(kept in `data/interim/m4/profiles_not_headline/`).",
         "- `metrics.json`: `headlineMatchRate` filled from audit v1, with a note on its design flaw."]
    STATUS_DOC.write_text("\n".join(L) + "\n")
