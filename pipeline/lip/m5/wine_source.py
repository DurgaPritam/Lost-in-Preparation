"""Cited source for the audit v2 wine cut-off (docs/AUDIT_PROTOCOL_v2.md §5): typical wine alcohol content.

Fetches the open-access article from Europe PMC (fullTextXML), records its metadata and licence, and checks that the
quoted sentences occur verbatim in the fetched text (re-checked on every run). Output: data/reference/wine_alcohol_source.json.
"""
from __future__ import annotations

import hashlib
import json
import re

from lxml import etree

from ..http import get_json, get_text
from ..paths import ROOT

OUT = ROOT / "data" / "reference" / "wine_alcohol_source.json"
PMCID = "PMC12155356"
QUOTES = ["In standard fermentation conditions, ethanol can accumulate to about 14–15%, even if its concentration generally ranges between 10 and 13%",
          "This amount can slightly vary in other countries, but alcohol content in wine is generally above 7.5%."]


def run() -> dict:
    xml, sha, at = get_text("europepmc", f"https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML")
    root = etree.fromstring(xml.encode(), parser=etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))
    body = re.sub(r"\s+", " ", " ".join(root.find(".//body").itertext()))
    for q in QUOTES:
        if q not in body:
            raise ValueError(f"quote not found in {PMCID}: {q[:60]}")
    meta = get_json("europepmc", "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                    {"query": f"PMCID:{PMCID}", "format": "json", "resultType": "core"})["resultList"]["result"][0]
    lic = root.find(".//license")
    out = {"pmcid": PMCID, "pmid": meta.get("pmid"), "doi": meta.get("doi"), "title": meta.get("title"),
           "authors": meta.get("authorString"), "journal": (meta.get("journalInfo") or {}).get("journal", {}).get("title"),
           "year": meta.get("pubYear"), "licence": meta.get("license"),
           "licenceText": re.sub(r"\s+", " ", etree.tostring(lic, method="text", encoding=str)).strip() if lic is not None else None,
           "url": f"https://europepmc.org/article/PMC/{PMCID}", "quotes": QUOTES, "fullTextSha256": sha, "retrievedAt": at,
           "usedFor": "audit v2 wine cut-off (<= 20% v/v ethanol): typical wine is 10-13%, fermentation reaches about 14-15%",
           "basis": "ai_curated_literature_reference", "verified_by": ""}
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out
