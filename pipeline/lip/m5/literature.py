"""M5 (prep): species-level literature retrieval for the approved study-set species. No LLM calls.

API: NCBI E-utilities (checked working on 2026-11-06; Europe PMC REST is the recorded fallback, unused).
Per species:
  names   accepted WFO name + WFO synonyms (WFO Plant List GraphQL, taxonNameById -> currentPreferredUsage ->
          hasSynonym), reduced to the Latin name without authors; de-duplicated
  search  PubMed esearch: ("name1"[tiab] OR "name2"[tiab] ...), sort=relevance, up to RETMAX records
          (the total hit count is recorded, so the cap is visible)
  fetch   PubMed efetch XML in batches: PMID, title, year, journal, DOI, PMCID, MeSH headings, publication
          types, abstract
  licence for records with a PMCID: Europe PMC REST search by PMCID (batches of 100), giving isOpenAccess and
          the licence: "pmc_oa" + licence, "pmc_not_oa", or "no_pmc" (abstract only). NCBI's PMC OA web service
          (oa.fcgi) returned HTTP 404 at both its old and new addresses on 2026-11-06, so Europe PMC is used here.
Every request is cached (data/cache/). Abstracts are publisher-copyright in general, so their TEXT stays in the
git-ignored cache (data/cache/m5_abstracts/); the committed records keep PMID, title, year, identifiers, MeSH,
licence status and the abstract's SHA-256. Outputs: data/interim/m5/literature/<wfoId>.json and summary.json.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import pandas as pd
from lxml import etree

from ..http import CACHE, get_json, get_text
from ..paths import INTERIM

OUT = INTERIM / "m5" / "literature"
ABSTRACTS = CACHE / "m5_abstracts"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
WFO_GQL = "https://list.worldfloraonline.org/gql.php"
TOOL = {"tool": "LostInPreparation"}
RETMAX = 300
BATCH = 100
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
API = {"search": "NCBI E-utilities (esearch, efetch)", "licence": "Europe PMC REST (search by PMCID: isOpenAccess, license)",
       "checkedOn": "2026-11-06",
       "status": "E-utilities and Europe PMC returned HTTP 200; NCBI's PMC OA web service (oa.fcgi) returned 404, so licence "
                 "status comes from Europe PMC"}


def latin_name(full: str) -> str | None:
    """'Mutelia officinalis (L.) Gren. ex Mutel' -> 'Mutelia officinalis'; keeps 'subsp.'/'var.' + epithet."""
    toks = full.split()
    if len(toks) >= 3 and toks[1] == "×":            # nothogenus-level hybrid sign: "Mentha × piperita L."
        toks = [toks[0], "×" + toks[2]] + toks[3:]
    if len(toks) < 2 or not toks[0][:1].isupper() or not (toks[1][:1].islower() or toks[1].startswith("×")):
        return None
    out = toks[:2]
    for i in range(2, len(toks) - 1):
        if toks[i] in ("subsp.", "var.", "f.", "subvar.") and toks[i + 1][:1].islower():
            out += toks[i:i + 2]
            break
    return " ".join(out).replace(" ×", " × ")


def wfo_synonyms(wfo_id: str) -> list[str]:
    q = ('{ taxonNameById(nameId: "%s") { currentPreferredUsage { hasName { fullNameStringPlain } '
         'hasSynonym { fullNameStringPlain } } } }' % wfo_id)
    r = get_json("wfo_gql", WFO_GQL, json_body={"query": q})
    u = ((r.get("data") or {}).get("taxonNameById") or {}).get("currentPreferredUsage") or {}
    names = [latin_name(s["fullNameStringPlain"]) for s in u.get("hasSynonym") or []]
    return sorted({n for n in names if n})


def search_term(names: list[str]) -> str:
    return " OR ".join(f'"{n}"[tiab]' for n in names)


def esearch(term: str) -> dict:
    r = get_json("ncbi", f"{EUTILS}/esearch.fcgi", data={"db": "pubmed", "term": term, "retmode": "json", "retmax": RETMAX,
                                                         "sort": "relevance", **TOOL})
    e = r["esearchresult"]
    return {"count": int(e.get("count", 0)), "ids": e.get("idlist", []), "queryTranslation": e.get("querytranslation")}


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def parse_pubmed(xml: str) -> list[dict]:
    root = etree.fromstring(xml.encode(), parser=etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))
    out = []
    for art in root.findall(".//PubmedArticle"):
        mc = art.find("MedlineCitation")
        pmid = mc.findtext("PMID")
        a = mc.find("Article")
        parts = []
        for at in a.findall("Abstract/AbstractText"):
            label = at.get("Label")
            parts.append((f"{label}: " if label else "") + _text(at))
        year = a.findtext("Journal/JournalIssue/PubDate/Year") or (a.findtext("Journal/JournalIssue/PubDate/MedlineDate") or "")[:4]
        ids = {i.get("IdType"): (i.text or "").strip() for i in art.findall("PubmedData/ArticleIdList/ArticleId")}
        out.append({"pmid": pmid, "title": _text(a.find("ArticleTitle")), "year": int(year) if year[:4].isdigit() else None,
                    "journal": a.findtext("Journal/Title"), "doi": ids.get("doi"), "pmcid": ids.get("pmc"),
                    "mesh": [_text(m.find("DescriptorName")) for m in mc.findall("MeshHeadingList/MeshHeading")],
                    "publicationTypes": [_text(p) for p in a.findall("PublicationTypeList/PublicationType")],
                    "abstract": " ".join(parts)})
    return out


def efetch(ids: list[str]) -> list[dict]:
    recs = []
    for i in range(0, len(ids), BATCH):
        chunk = ",".join(ids[i:i + BATCH])
        xml, _, _ = get_text("ncbi", f"{EUTILS}/efetch.fcgi?db=pubmed&retmode=xml&id={chunk}&tool=LostInPreparation")
        recs += parse_pubmed(xml)
    return recs


def oa_status_batch(pmcids: list[str]) -> dict[str, dict]:
    """PMCID -> {status, licence} from Europe PMC (100 per query, cached). Unseen PMCIDs are 'pmc_unknown'."""
    out: dict[str, dict] = {}
    ids = sorted(set(pmcids))
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        r = get_json("europepmc", EPMC, {"query": " OR ".join(f"PMCID:{x}" for x in chunk), "format": "json",
                                         "pageSize": 1000, "resultType": "core"})
        for x in (r.get("resultList") or {}).get("result", []):
            if x.get("pmcid"):
                oa = x.get("isOpenAccess") == "Y"
                out[x["pmcid"]] = {"status": "pmc_oa" if oa else "pmc_not_oa", "licence": x.get("license") if oa else None}
    return {p: out.get(p, {"status": "pmc_unknown", "licence": None}) for p in pmcids}


HELD = INTERIM / "m5" / "literature_held"   # retrieved earlier for species now outside the Phase 5 set; not used


def species_list() -> pd.DataFrame:
    """Phase 5 inputs: the headline set (approved, eligible, unchanged since review) plus approved species that are
    pending re-review but still ELIGIBLE. An "approve" decision alone is not enough: species whose attestation
    proxy fell below the threshold, or whose conditional approval was not met, are held until the project lead
    decides."""
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    ss = ss[(ss.approved == "yes") & (ss.headline | (ss.pendingReReview & ss.eligible))].copy()
    return ss[["acceptedName", "wfoId", "headline", "pendingReReview", "eligible"]]


def held_species() -> pd.DataFrame:
    """Approved species NOT in the Phase 5 set, with the reason."""
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    dec = pd.read_csv(INTERIM.parent.parent / "config" / "study_set_review_decisions.csv").set_index("species")
    a = ss[(ss.approved == "yes") & ~(ss.headline | (ss.pendingReReview & ss.eligible))]
    def why(r):
        if r.pendingReReview:
            return "pending re-review after the footnote rule; attestation proxy below 3"
        if dec.loc[r.acceptedName, "headline"] == "conditional":
            return "conditional approval not met (attestation proxy below 3)"
        return "approved, but attestation proxy below 3 after the reviewer's removals: needs a decision"
    return pd.DataFrame([{"species": r.acceptedName, "wfoId": r.wfoId, "attestations": r.attestations, "reason": why(r)}
                         for r in a.itertuples()], columns=["species", "wfoId", "attestations", "reason"])


def run(species: list[str] | None = None) -> dict:
    sp = species_list()
    if species:
        sp = sp[sp.acceptedName.isin(species)]
    OUT.mkdir(parents=True, exist_ok=True)
    ABSTRACTS.mkdir(parents=True, exist_ok=True)
    summary = {**API, "retmax": RETMAX, "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "species": {}}
    for r in sp.itertuples():
        names = [r.acceptedName] + [n for n in wfo_synonyms(r.wfoId) if n != r.acceptedName]
        s = esearch(search_term(names))
        recs = efetch(s["ids"])
        abstracts = {}
        lic = oa_status_batch([x["pmcid"] for x in recs if x["pmcid"]])
        for x in recs:
            ab = x.pop("abstract")
            x["hasAbstract"] = bool(ab)
            x["abstractSha256"] = hashlib.sha256(ab.encode()).hexdigest() if ab else None
            x["licenceStatus"] = lic[x["pmcid"]] if x["pmcid"] else {"status": "no_pmc", "licence": None}
            abstracts[x["pmid"]] = ab
        (OUT / f"{r.wfoId}.json").write_text(json.dumps(
            {"species": r.acceptedName, "wfoId": r.wfoId, "names": names, "term": search_term(names), **{k: s[k] for k in ("count", "queryTranslation")},
             "retrieved": len(recs), "records": recs}, ensure_ascii=False, indent=1))
        (ABSTRACTS / f"{r.wfoId}.json").write_text(json.dumps(abstracts, ensure_ascii=False))
        lic_counts = pd.Series([x["licenceStatus"]["status"] for x in recs]).value_counts().to_dict() if recs else {}
        oal = pd.Series([x["licenceStatus"]["licence"] for x in recs if x["licenceStatus"]["status"] == "pmc_oa"]).value_counts().to_dict()
        summary["species"][r.acceptedName] = {"wfoId": r.wfoId, "headline": bool(r.headline), "pendingReReview": bool(r.pendingReReview),
                                              "eligible": bool(r.eligible), "names": len(names), "hits": s["count"],
                                              "retrieved": len(recs), "withAbstract": sum(x["hasAbstract"] for x in recs),
                                              "licenceStatus": lic_counts, "oaLicences": oal}
    summary["held"] = held_species().to_dict("records")
    HELD.mkdir(parents=True, exist_ok=True)
    keep = set(sp.wfoId)
    for f in OUT.glob("*.json"):
        if f.stem not in keep:
            f.rename(HELD / f.name)   # kept for later, not deleted; not a Phase 5 input
    (OUT.parent / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary
