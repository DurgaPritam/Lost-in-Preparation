"""Phase 5 species–indication pairs from the M1 session extraction of the 19 Phase 5 species.

1. Attribution (HEURISTIC, conservative). A recipe from passage P counts for species S only if P is one of S's
   passages (m1.session.approved_passages) AND the recipe's principal plant name is not more specific than one of S's
   entry names: after lower-casing, folding plurals and dropping part words ("seed", "juice" ...) and determiners,
   every remaining token of the name must occur in one query string of S's name entries (data/interim/m2/
   name_inventory.parquet) or in S's accepted Latin name. "Sea Wormwood", "Leeks", "gourd" or "Pine Kernels" in a
   Wormwood / Onion / Colocynth / Henbane entry are therefore NOT attributed. Unattributed recipes are counted.
2. Indications -> MeSH descriptors with the versioned lexicon config/m5_indications/v1.toml (HEURISTIC). Descriptor
   IDs are looked up live in NCBI MeSH (E-utilities) and cached; a name not found exactly is dropped and reported.
3. Pairs = (species, MeSH descriptor) with at least one attributed SINGLE-PLANT recipe (compound recipes are
   excluded from the headline, as everywhere). Each pair lists its recipes and its distinct historical preparations
   (contract preparationKey part|freshOrDried|solvent|heat|filtered).
Output: data/interim/m5/pairs.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache

import pandas as pd

from ..http import get_json
from ..paths import INTERIM, ROOT

IND_PATH = ROOT / "config" / "m5_indications" / "v1.toml"
OUT = INTERIM / "m5" / "pairs.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PART_WORDS = {"seed", "seeds", "juice", "root", "roots", "leaf", "leaves", "flower", "flowers", "kernel", "kernels", "herb", "the",
              "this", "these", "of", "a", "an", "common", "our"}


def _fold(t: str) -> str:
    for suf, rep in (("ies", "y"), ("es", ""), ("s", "")):
        if len(t) > 4 and t.endswith(suf):
            return t[: -len(suf)] + rep
    return t


def tokens(s: str) -> set[str]:
    return {_fold(t) for t in re.findall(r"[a-zæœ]+", (s or "").lower().replace("-", " ")) if t not in PART_WORDS}


def attributable(name: str, queries: list[str]) -> bool:
    nt = tokens(name)
    return bool(nt) and any(nt <= tokens(q) for q in queries)


@lru_cache(maxsize=2)
def indication_lexicon(path=IND_PATH) -> tuple[str, dict[str, list[re.Pattern]]]:
    raw = path.read_bytes()
    d = tomllib.loads(raw.decode())
    return (f"m5_indications/{d['version']}:{hashlib.sha256(raw).hexdigest()[:10]}",
            {k: [re.compile(p, re.I) for p in v] for k, v in d["descriptors"].items()})


def map_indication(text: str) -> list[str]:
    _, lex = indication_lexicon()
    return [k for k, ps in lex.items() if any(p.search(text or "") for p in ps)]


def mesh_lookup(label: str) -> dict | None:
    """MeSH descriptor UI for an exact descriptor name, from NCBI MeSH (cached). None if not found exactly."""
    r = get_json("ncbi", f"{EUTILS}/esearch.fcgi", {"db": "mesh", "term": f'"{label}"[MeSH Terms]', "retmode": "json",
                                                    "tool": "LostInPreparation"})
    for uid in r["esearchresult"].get("idlist", [])[:5]:
        s = get_json("ncbi", f"{EUTILS}/esummary.fcgi", {"db": "mesh", "id": uid, "retmode": "json", "tool": "LostInPreparation"})
        doc = s.get("result", {}).get(uid, {})
        terms = doc.get("ds_meshterms") or []
        if terms and terms[0] == label and doc.get("ds_meshui", "").startswith("D"):
            return {"meshId": doc["ds_meshui"], "label": label}
    return None


def species_queries() -> dict[str, list[str]]:
    from ..m1.session import approved_passages
    a = approved_passages()
    inv = pd.read_parquet(INTERIM / "m2" / "name_inventory.parquet").set_index("nameId")
    q: dict[str, list[str]] = defaultdict(list)
    for sp, nid in set(zip(a.species, a.nameId)):
        qs = inv.loc[nid, "queries"]
        q[sp] += json.loads(qs) if isinstance(qs, str) else list(qs)
        q[sp].append(sp)
    return dict(q)


def build() -> dict:
    from ..m1.session import approved_passages
    from ..m5.literature import species_list
    sp = species_list().set_index("acceptedName")
    a = approved_passages()
    by_passage = a.groupby("passageId").species.apply(lambda s: sorted(set(s))).to_dict()
    queries = species_queries()
    recipes = json.loads((INTERIM / "m1" / "predictions_approved.json").read_text())
    version, lex = indication_lexicon()
    mesh = {k: mesh_lookup(k) for k in lex}
    missing = sorted(k for k, v in mesh.items() if v is None)
    attributed, unattributed, unmapped = [], [], []
    for r in recipes:
        pid = r["passage"]["passageId"]
        hits = [s for s in by_passage.get(pid, []) if attributable(r["plantNameAsWritten"], queries[s])]
        if not hits:
            unattributed.append({"recipeId": r["id"], "plantNameAsWritten": r["plantNameAsWritten"], "passageId": pid,
                                 "passageSpecies": by_passage.get(pid, [])})
            continue
        descs = [d for d in map_indication(r["indicationAsWritten"]) if mesh.get(d)]
        if not descs:
            unmapped.append({"recipeId": r["id"], "indicationAsWritten": r["indicationAsWritten"]})
        for s in hits:
            attributed.append({"recipeId": r["id"], "species": s, "speciesId": sp.loc[s, "wfoId"], "sourceId": r["sourceId"],
                               "passageId": pid, "plantNameAsWritten": r["plantNameAsWritten"], "recipeType": r["recipeType"],
                               "excludedFromHeadline": r["excludedFromHeadline"], "indicationAsWritten": r["indicationAsWritten"],
                               "mesh": [mesh[d] for d in descs],
                               "prep": {k: r[k] for k in ("part", "freshOrDried", "solvent", "heat", "filtered", "process", "form")}})
    pairs: dict[tuple, dict] = {}
    for x in attributed:
        if x["excludedFromHeadline"]:
            continue
        for m in x["mesh"]:
            k = (x["species"], m["meshId"])
            p = pairs.setdefault(k, {"species": x["species"], "speciesId": x["speciesId"], "indication": m, "recipes": [],
                                     "indicationsAsWritten": [], "preparations": defaultdict(list), "sources": set()})
            p["recipes"].append(x["recipeId"])
            p["indicationsAsWritten"].append(x["indicationAsWritten"])
            p["sources"].add(x["sourceId"])
            p["preparations"][preparation_key(x["prep"])].append(x["recipeId"])
    out_pairs = sorted(({**p, "sources": sorted(p["sources"]), "preparations": dict(p["preparations"]),
                         "attestationCount": len(p["recipes"])} for p in pairs.values()),
                       key=lambda p: (p["species"], p["indication"]["label"]))
    out = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "indicationLexicon": version,
           "attribution": "recipe name not more specific than an entry name of a species linked to the passage (HEURISTIC)",
           "meshLookup": {"source": "NCBI MeSH via E-utilities (esearch + esummary, db=mesh)", "notFound": missing},
           "counts": {"recipes": len(recipes), "attributedRecipes": len({x["recipeId"] for x in attributed}),
                      "unattributedRecipes": len(unattributed),
                      "attributedSinglePlant": len({x["recipeId"] for x in attributed if not x["excludedFromHeadline"]}),
                      "attributedCompound": len({x["recipeId"] for x in attributed if x["excludedFromHeadline"]}),
                      "attributedWithoutMappedIndication": len(unmapped), "pairs": len(out_pairs),
                      "speciesWithPairs": len({p["species"] for p in out_pairs})},
           "pairs": out_pairs, "unattributed": unattributed, "unmappedIndications": unmapped}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def preparation_key(p: dict) -> str:
    """Contract preparationKey (P4): part|freshOrDried|solvent(+joined, sorted)|heat|filtered."""
    sol = sorted(set(p["solvent"]) - {"unknown"}) or ["unknown"]
    return f"{p['part']}|{p['freshOrDried']}|{'+'.join(sol)}|{p['heat']}|{p['filtered']}"
