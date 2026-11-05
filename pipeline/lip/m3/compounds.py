"""M3 compound retrieval: known natural products per species from LOTUS (hosted on Wikidata, CC0).

For each resolved species (top-1 candidate in WFO) we query Wikidata for compounds with a
"found in taxon" (P703) statement on the taxon whose scientific name (P225) is the accepted WFO
name or the GBIF name it came from. Each occurrence keeps its LOTUS reference (the "stated in"
item, P248). LOTUS records organism-level occurrences, so `part` is "unknown" throughout.

Structures (isomeric SMILES P2017, else canonical SMILES P233) are standardised with RDKit:
sanitise -> Cleanup -> largest organic fragment (FragmentParent) -> neutralise (Uncharger).
No tautomer canonicalisation is applied. Compounds are deduplicated by the InChIKey of the
standardised structure; disagreement with the InChIKey stored in Wikidata (first block) is flagged.

Coverage per species = number of distinct standardised compounds; species with fewer than
`poor_coverage_below` compounds (config/pipeline.toml, default 10; a HEURISTIC threshold) are
flagged as poor coverage.
"""
from __future__ import annotations

import json
import tomllib
from collections import defaultdict

import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.MolStandardize import rdMolStandardize

from ..http import get_json, pmap
from ..paths import INTERIM, ROOT

RDLogger.DisableLog("rdApp.*")
OUT = INTERIM / "m3"
SPARQL = "https://query.wikidata.org/sparql"
BATCH = 12
QUERY = """SELECT ?name ?compound ?label ?inchikey ?smiles ?iso ?ref WHERE {
  VALUES ?name { %s }
  ?taxon wdt:P225 ?name .
  ?compound p:P703 ?st . ?st ps:P703 ?taxon .
  OPTIONAL { ?st prov:wasDerivedFrom/pr:P248 ?ref }
  OPTIONAL { ?compound wdt:P235 ?inchikey }
  OPTIONAL { ?compound wdt:P233 ?smiles }
  OPTIONAL { ?compound wdt:P2017 ?iso }
  OPTIONAL { ?compound rdfs:label ?label FILTER(lang(?label) = "en") }
}"""


def threshold() -> int:
    with (ROOT / "config" / "pipeline.toml").open("rb") as fh:
        return int(tomllib.load(fh).get("m3", {}).get("poor_coverage_below", 10))


def _qid(uri: str | None) -> str | None:
    return uri.rsplit("/", 1)[-1] if uri else None


def fetch(names: list[str]) -> list[dict]:
    values = " ".join(json.dumps(n) for n in names)
    r = get_json("wikidata", SPARQL, data={"query": QUERY % values, "format": "json"},
                 headers={"Accept": "application/sparql-results+json"})
    return [{k: v["value"] for k, v in b.items()} for b in r["results"]["bindings"]]


_cleanup = rdMolStandardize.CleanupParameters()
_uncharger = rdMolStandardize.Uncharger()
_chooser = rdMolStandardize.LargestFragmentChooser(preferOrganic=True)


def standardise(smiles: str) -> tuple[str | None, str | None, str]:
    """-> (standardised isomeric SMILES, InChIKey, status)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None, "rdkit_parse_failed"
    try:
        mol = rdMolStandardize.Cleanup(mol, _cleanup)
        mol = _chooser.choose(mol)
        mol = _uncharger.uncharge(mol)
        Chem.SanitizeMol(mol)
    except Exception as e:  # noqa: BLE001 - record and continue; never invent a structure
        return None, None, f"standardise_failed: {type(e).__name__}"
    key = Chem.MolToInchiKey(mol)
    return Chem.MolToSmiles(mol), key or None, "ok" if key else "inchikey_failed"


def main() -> dict:
    cand = pd.read_parquet(INTERIM / "m2" / "name_candidates.parquet")
    top = cand[(cand["rank"] == 1) & cand.inWFO]
    species = (top.groupby("acceptedName").agg(wfoId=("wfoId", "first"), gbifNames=("gbifSpecies", lambda s: sorted(set(s))))
               .reset_index())
    lookup: dict[str, str] = {}
    for r in species.itertuples():
        for n in {r.acceptedName, *r.gbifNames}:
            lookup.setdefault(n, r.acceptedName)
    names = sorted(lookup)
    batches = [names[i:i + BATCH] for i in range(0, len(names), BATCH)]
    rows = [x for b in pmap(fetch, batches, 2) for x in b]

    # standardise each distinct Wikidata compound once
    comp = {}
    for x in rows:
        q = _qid(x["compound"])
        if q not in comp:
            src = x.get("iso") or x.get("smiles")
            smi, key, status = standardise(src) if src else (None, None, "no_smiles")
            wd_key = x.get("inchikey")
            comp[q] = {"wikidataId": q, "label": x.get("label"), "smilesSource": src, "smiles": smi, "inchikey": key,
                       "wikidataInchikey": wd_key, "status": status,
                       "inchikeyMismatch": bool(key and wd_key and key.split("-")[0] != wd_key.split("-")[0])}
    compounds = pd.DataFrame(comp.values())

    occ = defaultdict(lambda: {"refs": set(), "wikidataIds": set(), "names": set()})
    for x in rows:
        c = comp[_qid(x["compound"])]
        if not c["inchikey"]:
            continue
        o = occ[(lookup[x["name"]], c["inchikey"])]
        o["wikidataIds"].add(c["wikidataId"])
        o["names"].add(x["name"])
        if x.get("ref"):
            o["refs"].add(_qid(x["ref"]))
    occurrences = pd.DataFrame([{"acceptedName": sp, "inchikey": k, "wikidataIds": sorted(v["wikidataIds"]),
                                 "queriedNames": sorted(v["names"]), "references": sorted(v["refs"]),
                                 "part": "unknown", "source": "LOTUS via Wikidata"} for (sp, k), v in occ.items()])

    thr = threshold()
    cov = []
    for r in species.itertuples():
        o = occurrences[occurrences.acceptedName == r.acceptedName] if len(occurrences) else occurrences
        refs = {ref for lst in o.references for ref in lst} if len(o) else set()
        n = int(len(o))
        cov.append({"acceptedName": r.acceptedName, "wfoId": r.wfoId, "nCompounds": n, "nReferences": len(refs),
                    "poorCoverage": n < thr, "coverageNote": f"{n} compounds from {len(refs)} LOTUS references; "
                    f"organism-level (plant part not recorded)" + ("; POOR COVERAGE" if n < thr else "")})
    coverage = pd.DataFrame(cov).sort_values("nCompounds", ascending=False)

    OUT.mkdir(parents=True, exist_ok=True)
    compounds.to_parquet(OUT / "compounds.parquet", index=False)
    occurrences.to_parquet(OUT / "occurrences.parquet", index=False)
    coverage.to_csv(OUT / "coverage.csv", index=False)
    summary = {
        "species": int(len(species)), "queriedNames": len(names), "wikidataRows": len(rows),
        "distinctWikidataCompounds": int(len(compounds)),
        "standardised": int((compounds.status == "ok").sum()) if len(compounds) else 0,
        "standardisationFailures": compounds[compounds.status != "ok"].status.value_counts().to_dict() if len(compounds) else {},
        "inchikeyConnectivityMismatches": int(compounds.inchikeyMismatch.sum()) if len(compounds) else 0,
        "distinctStandardisedInchikeys": int(compounds.inchikey.nunique()) if len(compounds) else 0,
        "speciesWithAnyCompound": int((coverage.nCompounds > 0).sum()),
        "speciesPoorCoverage": int(coverage.poorCoverage.sum()), "poorCoverageThreshold": thr,
        "medianCompoundsPerSpecies": float(coverage.nCompounds.median()) if len(coverage) else 0.0,
    }
    (OUT / "compounds_summary.json").write_text(json.dumps(summary, indent=2))
    return summary
