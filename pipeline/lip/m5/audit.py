"""Phase 5 audit, following docs/AUDIT_PROTOCOL_v1.md (fixed before retrieval). No LLM.

Per species–indication pair (data/interim/m5/pairs.json):
  retrieve   PubMed esearch (species names [tiab]) AND (MeSH descriptor [MeSH Terms] or [tiab]), relevance, first 30;
             efetch; publication-type exclusions; Europe PMC licence for PMCIDs
  text       open access: methods sections of the Europe PMC fullTextXML + title (pmc_fulltext); else title + abstract
  code       rule-based extractor m5/rules.py (lexicon config/m5_lexicon/v1.toml)
  match      protocol §4 (unknown is never a mismatch)
  report     protocol §5 headline with a bootstrap CI over pairs; per-field mismatch rates; coverage
Texts stay in the git-ignored cache; committed outputs carry a methods snippet only for open-access records.
Outputs: site-data/audit.json (contract), data/interim/m5/audit_studies.json, data/interim/m5/audit_summary.json,
data/reference/m5_handcheck_v1.csv (+ a local reading copy with the texts in data/cache/m5_handcheck/).
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from lxml import etree

from contract import models as C

from ..http import CACHE, SSL_CONTEXT, USER_AGENT, get_json
from ..paths import INTERIM, ROOT, SITE_DATA
from . import literature as L
from . import rules

OUT = INTERIM / "m5"
METHODS_CACHE = CACHE / "m5_methods"
TEXT_CACHE = CACHE / "m5_audit_text"
HANDCHECK = ROOT / "data" / "reference" / "m5_handcheck_v1.csv"
HANDCHECK_LOCAL = CACHE / "m5_handcheck" / "handcheck_v1_texts.md"
RETMAX = 30
SEED = 20261106
B = 2000
EXCLUDED_TYPES = {"Review", "Systematic Review", "Meta-Analysis", "Editorial", "Comment", "Letter", "News",
                  "Published Erratum", "Retracted Publication"}
METHOD_TITLE = re.compile(r"materials?|methods?|experimental|extraction|preparation|plant", re.I)
FIELDS = ["solvent", "heat", "filtered", "part", "freshOrDried"]
MATCH_FIELD = {"filtered": "filtration"}


# --- retrieval ------------------------------------------------------------------------------------

def pair_term(names: list[str], label: str) -> str:
    return f'({L.search_term(names)}) AND ("{label}"[MeSH Terms] OR "{label}"[tiab])'


def species_names() -> dict[str, list[str]]:
    out = {}
    for f in (OUT / "literature").glob("*.json"):
        d = json.loads(f.read_text())
        out[d["species"]] = d["names"]
    return out


def esearch(term: str) -> dict:
    r = get_json("ncbi", f"{L.EUTILS}/esearch.fcgi", data={"db": "pubmed", "term": term, "retmode": "json", "retmax": RETMAX,
                                                           "sort": "relevance", **L.TOOL})
    e = r["esearchresult"]
    return {"count": int(e.get("count", 0)), "ids": e.get("idlist", [])}


def fetch_records(pmids: list[str]) -> dict[str, dict]:
    recs = {}
    for r in L.efetch(sorted(set(pmids))):
        recs[r["pmid"]] = r
    lic = L.oa_status_batch([r["pmcid"] for r in recs.values() if r["pmcid"]])
    for r in recs.values():
        r["licenceStatus"] = lic[r["pmcid"]] if r["pmcid"] else {"status": "no_pmc", "licence": None}
    return recs


def _get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120, context=SSL_CONTEXT) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (404, 400):
                return e.code, ""
            time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(2 * (attempt + 1))
    return 0, ""


def methods_text(pmcid: str) -> str | None:
    """Methods sections of an open-access article (Europe PMC fullTextXML), cached; None if unavailable."""
    METHODS_CACHE.mkdir(parents=True, exist_ok=True)
    cp = METHODS_CACHE / f"{pmcid}.json"
    if cp.exists():
        return json.loads(cp.read_text())["methods"]
    status, xml = _get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML")
    methods = None
    if status == 200 and xml:
        try:
            root = etree.fromstring(xml.encode(), parser=etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))
            parts = []
            for sec in root.iter("sec"):
                title = "".join(sec.findtext("title") or "")
                if (sec.get("sec-type") or "").lower().find("method") >= 0 or METHOD_TITLE.search(title):
                    if any(a.tag == "sec" and (METHOD_TITLE.search(a.findtext("title") or "") or "method" in (a.get("sec-type") or ""))
                           for a in sec.iterancestors()):
                        continue                      # counted with its parent section
                    parts.append(re.sub(r"\s+", " ", " ".join(sec.itertext())).strip())
            methods = "\n\n".join(parts) or None
        except etree.XMLSyntaxError:
            methods = None
    if status in (200, 404, 400):                       # cache definite answers only
        cp.write_text(json.dumps({"pmcid": pmcid, "status": status, "methods": methods,
                                  "retrievedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}, ensure_ascii=False))
    return methods


# --- matching (protocol §4) -----------------------------------------------------------------------

def parse_key(k: str) -> dict:
    part, fod, sol, heat, filt = k.split("|")
    return {"part": part, "freshOrDried": fod, "solvent": sol.split("+"), "heat": heat, "filtered": filt}


def compare(hist: dict, prep) -> dict:
    out = {}
    hs, ms = [s for s in hist["solvent"] if s != "unknown"], prep.solvent
    out["solvent"] = "unknown" if not hs or ms == "unknown" else ("match" if hs == ["water"] and ms == "water" else "mismatch")
    for f in ("heat", "filtered", "part", "freshOrDried"):
        h, m = hist[f], getattr(prep, f)
        out[MATCH_FIELD.get(f, f)] = "unknown" if "unknown" in (h, m) else ("match" if h == m else "mismatch")
    vals = list(out.values())
    out["overall"] = ("mismatch" if "mismatch" in vals else
                      "match" if out["solvent"] == "match" and out["heat"] == "match" else "unknown")
    return out


def study_status(matches: list[dict]) -> str:
    ov = [m["overall"] for m in matches]
    if "match" in ov:
        return "faithful"
    if ov and all(o == "mismatch" for o in ov):
        return "not_faithful"
    return "unknown"


# --- run ------------------------------------------------------------------------------------------

def _source_group(sources: list[str]) -> str:
    return "pliny_only" if all(s.startswith("pliny") for s in sources) else "culpeper"


def _boot(units: pd.DataFrame, rng: np.random.Generator) -> tuple[float | None, float | None]:
    pairs = units.pairKey.unique()
    if len(pairs) < 2:
        return None, None
    by = {p: g for p, g in units.groupby("pairKey")}
    vals = []
    for _ in range(B):
        s = pd.concat([by[p] for p in rng.choice(pairs, len(pairs))])
        vals.append((s.status == "not_faithful").mean())
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def _metric(units: pd.DataFrame, note: str, boot=True, seed=SEED) -> dict:
    known = units[units.status != "unknown"]
    nk, nu = len(known), int((units.status == "unknown").sum())
    if not nk:
        return {"status": "not_computed", "value": None, "low": None, "high": None, "nKnown": 0, "nUnknown": nu, "note": note}
    lo, hi = _boot(known, np.random.default_rng(seed)) if boot else (None, None)
    return {"status": "computed", "value": round(float((known.status == "not_faithful").mean()), 4),
            "low": None if lo is None else round(lo, 4), "high": None if hi is None else round(hi, 4),
            "nKnown": nk, "nUnknown": nu, "note": note}


def run() -> dict:
    pairs = json.loads((OUT / "pairs.json").read_text())
    names = species_names()
    lex_version = rules.lexicon().version
    # 1. retrieval
    hits, pair_ids = {}, {}
    for p in pairs["pairs"]:
        k = f"{p['speciesId']}|{p['indication']['meshId']}"
        s = esearch(pair_term(names[p["species"]], p["indication"]["label"]))
        hits[k], pair_ids[k] = s["count"], s["ids"]
    recs = fetch_records([i for ids in pair_ids.values() for i in ids])
    # 2. text and coding (per unique study)
    TEXT_CACHE.mkdir(parents=True, exist_ok=True)
    coded, excluded = {}, Counter()
    for pmid, r in recs.items():
        types = set(r["publicationTypes"])
        if types & EXCLUDED_TYPES:
            excluded["publication type"] += 1
            continue
        lic = r["licenceStatus"]
        mt = methods_text(r["pmcid"]) if lic["status"] == "pmc_oa" else None
        if mt:
            text, src = r["title"] + "\n\n" + mt, "pmc_fulltext"
        elif r["abstract"]:
            text, src = r["title"] + "\n\n" + r["abstract"], "abstract"
        else:
            excluded["no abstract and no open-access methods"] += 1
            continue
        (TEXT_CACHE / f"{pmid}.txt").write_text(text)
        preps = rules.extract(text)
        coded[pmid] = {"pmid": pmid, "doi": r["doi"], "title": r["title"], "year": r["year"], "pmcid": r["pmcid"],
                       "licenceStatus": lic, "evidenceSource": src, "textSha256": hashlib.sha256(text.encode()).hexdigest(),
                       "extractor": lex_version,
                       "preparations": [{**{f: getattr(x, f) for f in ("solvent", "solventText", "ethanolFraction", "heat", "heatText",
                                                                         "part", "freshOrDried", "filtered")},
                                         "unknownFields": x.unknownFields, "flags": x.flags,
                                         "evidence": [{**e, "quote": e["quote"] if lic["status"] == "pmc_oa" else None} for e in x.evidence]}
                                        for x in preps],
                       "_preps": preps, "_text": text}
    # 3. matching and contract audit records
    audit, units, field_rows = [], [], []
    for p in pairs["pairs"]:
        k = f"{p['speciesId']}|{p['indication']['meshId']}"
        studies = [coded[i] for i in pair_ids[k] if i in coded]
        hist = {hk: parse_key(hk) for hk in p["preparations"]}
        per_study = {}
        for s in studies:
            ms = [(hk, i, compare(h, x)) for hk, h in hist.items() for i, x in enumerate(s["_preps"])]
            per_study[s["pmid"]] = ms
            st = study_status([m for _, _, m in ms])
            units.append({"pairKey": k, "species": p["species"], "mesh": p["indication"]["label"], "pmid": s["pmid"], "status": st,
                          "group": _source_group(p["sources"]), "evidenceSource": s["evidenceSource"],
                          "solventStated": any(x.solvent != "unknown" for x in s["_preps"])})
            for _, _, m in ms:
                field_rows.append({"pairKey": k, **{f: m[f] for f in ("solvent", "heat", "filtration", "part", "freshOrDried")}})
        for hk in hist:
            rows = []
            for s in studies:
                for hk2, i, m in per_study[s["pmid"]]:
                    if hk2 != hk:
                        continue
                    x = s["_preps"][i]
                    snippet = None
                    sol_ev = next((e for e in x.evidence if e["field"] == "solvent"), None)
                    if sol_ev and s["licenceStatus"]["status"] == "pmc_oa":
                        t = s["_text"]
                        snippet = t[max(0, sol_ev["start"] - 120):sol_ev["end"] + 120]
                    rows.append(C.Study(pmid=s["pmid"], doi=s["doi"], title=s["title"], year=s["year"], solvent=x.solvent,
                                        solventText=x.solventText, ethanolFraction=x.ethanolFraction, heat=x.heat, part=x.part,
                                        freshOrDried=x.freshOrDried, filtered=x.filtered, match=C.StudyMatch(**m),
                                        unknownFields=x.unknownFields, evidenceSource=s["evidenceSource"], methodsSnippet=snippet))
            by_pmid = defaultdict(list)
            for st in rows:
                by_pmid[st.pmid].append(st.match.overall.value if hasattr(st.match.overall, "value") else st.match.overall)
            stat = [("faithful" if "match" in v else "not_faithful" if all(o == "mismatch" for o in v) else "unknown") for v in by_pmid.values()]
            nk = sum(s != "unknown" for s in stat)
            audit.append(C.AuditRecord(speciesId=p["speciesId"], indication=C.MeshTerm(**p["indication"]),
                                       indicationAsWritten=p["indicationsAsWritten"][0], historicalPreparation=hk,
                                       historicalRecipeIds=p["preparations"][hk], studies=rows,
                                       matchRate=C.Rate(value=round(sum(s == "faithful" for s in stat) / nk, 4) if nk else None,
                                                        nKnown=nk, nUnknown=len(stat) - nk)))
    part_only = {}
    for x in units:
        if x["status"] == "not_faithful" and not x["solventStated"]:
            part_only[(x["pairKey"], x["pmid"])] = True
    U = pd.DataFrame(units, columns=["pairKey", "species", "mesh", "pmid", "status", "group", "evidenceSource", "solventStated"])
    F = pd.DataFrame(field_rows)
    head = _metric(U, "share of (pair, study) units with no historical-preparation match, among units whose status is known; "
                      "95% CI: bootstrap over pairs (B=2000)")
    uniq = U.sort_values("status").groupby("pmid").status.apply(
        lambda s: "faithful" if (s == "faithful").any() else "not_faithful" if (s == "not_faithful").all() else "unknown").reset_index()
    uniq["pairKey"] = uniq.pmid
    summary = {
        "protocol": "docs/AUDIT_PROTOCOL_v1.md", "extractor": lex_version, "indicationLexicon": pairs["indicationLexicon"],
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "retrieval": {"pairs": len(pairs["pairs"]), "retmaxPerPair": RETMAX, "pairsWithHits": sum(1 for v in hits.values() if v),
                      "totalHits": int(sum(hits.values())), "uniqueRecords": len(recs), "excluded": dict(excluded),
                      "studiesCoded": len(coded),
                      "byEvidenceSource": dict(Counter(s["evidenceSource"] for s in coded.values())),
                      "studiesAllUnknown": sum(all(len(x["unknownFields"]) == 5 for x in s["preparations"]) for s in coded.values())},
        "units": {"pairStudyUnits": len(U), "byStatus": U.status.value_counts().to_dict(),
                  "pairsWithAnyStudy": int(U.pairKey.nunique()), "pairsWithKnownStatus": int(U[U.status != "unknown"].pairKey.nunique())},
        "headline": head,
        "headlineUniqueStudies": _metric(uniq, "each study counted once (not faithful to any pair it was retrieved for)", boot=False),
        "bySourceGroup": {g: _metric(U[U.group == g], f"pairs attested {'only by Pliny (lower confidence)' if g == 'pliny_only' else 'by Culpeper'}")
                          for g in ("culpeper", "pliny_only")},
        "byEvidenceSource": {g: _metric(U[U.evidenceSource == g], f"studies coded from {g}", boot=False) for g in ("pmc_fulltext", "abstract")},
        "postHocSensitivity": {
            "label": "POST-HOC, NOT PRE-REGISTERED (added after inspecting results): only studies with a stated solvent, i.e. "
                     "studies that describe preparing the plant. Under protocol v1 a study can be 'not faithful' on a part "
                     "mismatch alone even if it never prepared the plant (e.g. a pure-compound study).",
            "solventStatedOnly": _metric(U[U.solventStated.astype(bool)], "units whose study states a solvent"),
            "notFaithfulOnPartAlone": int(sum(1 for k, v in part_only.items() if v))},
        "fieldMismatchRate": {f: ({"mismatch": int((F[f] == "mismatch").sum()), "known": int((F[f] != "unknown").sum()),
                                   "rate": round(float((F[f] == "mismatch").sum() / max(1, (F[f] != "unknown").sum())), 4)}
                                  if len(F) else None) for f in ("solvent", "heat", "filtration", "part", "freshOrDried")},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit_studies.json").write_text(json.dumps(
        {"extractor": lex_version, "pairHits": hits, "pairPmids": pair_ids,
         "studies": [{k: v for k, v in s.items() if not k.startswith("_")} for s in coded.values()]}, ensure_ascii=False, indent=1))
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    U.to_csv(OUT / "audit_units.csv", index=False)
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "audit.json").write_text(json.dumps([a.model_dump(mode="json") for a in audit], ensure_ascii=False, indent=1))
    handcheck(coded)
    return summary


# --- hand-check sheet (protocol §6) ---------------------------------------------------------------

def handcheck(coded: dict, n: int = 40) -> pd.DataFrame:
    rng = random.Random(SEED)
    by = defaultdict(list)
    for pmid in sorted(coded):
        by[coded[pmid]["evidenceSource"]].append(pmid)
    want = {"pmc_fulltext": min(20, len(by["pmc_fulltext"])), "abstract": min(20, len(by["abstract"]))}
    short = n - sum(want.values())
    for g in want:                                  # top up from the other stratum if one is short
        extra = min(short, len(by[g]) - want[g])
        want[g] += extra
        short -= extra
    pick = [p for g in ("pmc_fulltext", "abstract") for p in sorted(rng.sample(by[g], want[g]))]
    rows, local = [], ["# M5 hand-check v1 — texts (LOCAL ONLY, not committed: publisher-copyright text)\n"]
    for pmid in pick:
        s = coded[pmid]
        local.append(f"\n## PMID {pmid} — {s['title']}\n\nhttps://pubmed.ncbi.nlm.nih.gov/{pmid}/ · source: {s['evidenceSource']} · "
                     f"licence: {s['licenceStatus']}\n\n{s['_text']}\n")
        for i, x in enumerate(s["preparations"]):
            ev = {e["field"]: e for e in x["evidence"]}
            rows.append({"pmid": pmid, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "title": s["title"],
                         "evidenceSource": s["evidenceSource"], "licence": s["licenceStatus"]["licence"] or s["licenceStatus"]["status"],
                         "preparation": i + 1, "extractor": s["extractor"],
                         **{f"rule_{f}": x[f] for f in ("solvent", "heat", "part", "freshOrDried", "filtered")},
                         "rule_solventText": x["solventText"],
                         **{f"rule_{f}_quote": (ev[f]["quote"] if f in ev and ev[f]["quote"] else
                                                (f"chars {ev[f]['start']}-{ev[f]['end']}" if f in ev else ""))
                            for f in ("solvent", "heat", "part", "freshOrDried", "filtered")},
                         "rule_flags": "; ".join(x["flags"]),
                         **{f"human_{f}": "" for f in ("solvent", "heat", "part", "freshOrDried", "filtered")},
                         "human_missed_preparation": "", "human_notes": ""})
    df = pd.DataFrame(rows)
    HANDCHECK.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(HANDCHECK, index=False)
    HANDCHECK_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    HANDCHECK_LOCAL.write_text("\n".join(local))
    return df


# --- hand-check evaluation (only from the filled sheet) -------------------------------------------

def handcheck_eval() -> dict:
    """Per-field accuracy of the rule-based extractor against the human hand-check sheet. Rows whose human column is
    empty are not scored; nothing is written as a placeholder. Wilson 95% intervals."""
    from ..m2.evaluate import wilson
    df = pd.read_csv(HANDCHECK, dtype=str).fillna("")
    out = {"sheet": str(HANDCHECK.relative_to(ROOT)), "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fields": {}}
    for f in ("solvent", "heat", "part", "freshOrDried", "filtered"):
        d = df[df[f"human_{f}"].str.strip() != ""]
        if not len(d):
            out["fields"][f] = {"status": "not_computed", "note": "no filled rows"}
            continue
        ok = (d[f"rule_{f}"].str.strip() == d[f"human_{f}"].str.strip())
        lo, hi = wilson(int(ok.sum()), len(d))
        stated_missed = int(((d[f"rule_{f}"] == "unknown") & (d[f"human_{f}"] != "unknown")).sum())
        wrong_value = int(((d[f"rule_{f}"] != "unknown") & (d[f"human_{f}"] != d[f"rule_{f}"])).sum())
        out["fields"][f] = {"status": "computed", "accuracy": round(float(ok.mean()), 4), "low": round(lo, 4), "high": round(hi, 4),
                            "n": int(len(d)), "missedStatedValue": stated_missed, "wrongValue": wrong_value}
    out["missedPreparations"] = int((df.human_missed_preparation.str.strip() != "").sum())
    (OUT / "handcheck_eval.json").write_text(json.dumps(out, indent=2))
    return out
