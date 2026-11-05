"""Thin wrappers over GBIF and World Flora Online (all responses cached by lip.http)."""
from __future__ import annotations

import re
import unicodedata

from ..http import HTTPError, get_json

GBIF = "https://api.gbif.org/v1"
GBIF_BACKBONE = "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"
WFO = "https://list.worldfloraonline.org/matching_rest.php"
SPECIES_RANKS = {"SPECIES", "SUBSPECIES", "VARIETY", "FORM"}
FAMILY_ALIASES = {"Compositae", "Gramineae", "Leguminosae", "Palmae", "Umbelliferae", "Cruciferae", "Labiatae", "Guttiferae"}


def ascii_latin(s: str) -> str:
    s = s.replace("æ", "ae").replace("œ", "oe").replace("Æ", "Ae").replace("Œ", "Oe")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_vernacular(s: str) -> str:
    """Lower case, ASCII, possessives and plurals folded ('Adder's Tongue' == 'adders tongue' == 'adder tongue')."""
    s = ascii_latin(s).lower().replace("’", "'")
    s = re.sub(r"'s\b", "", s)
    def fold(w: str) -> str:
        if len(w) > 4 and w.endswith("ies"):
            return w[:-3] + "y"
        return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
    return " ".join(fold(w) for w in re.findall(r"[a-z]+", s))


def _species_of(r: dict) -> str | None:
    """Canonical species binomial for a GBIF usage (infraspecific names roll up to the species)."""
    sp = r.get("species")
    if sp and not sp.strip().endswith("×"):
        return sp
    name = r.get("canonicalName") or ""
    parts = name.split()
    if len(parts) >= 3 and parts[1] == "×":  # nothospecies: keep the hybrid epithet
        return " ".join(parts[:3])
    return " ".join(parts[:2]) if len(parts) >= 2 and parts[1] != "×" else None


def gbif_usage(key: int) -> dict:
    return get_json("gbif", f"{GBIF}/species/{key}")


def gbif_accepted_species(r: dict) -> tuple[str | None, int | None]:
    status = (r.get("taxonomicStatus") or r.get("status") or "").upper()
    if status in ("ACCEPTED", "DOUBTFUL", ""):
        return _species_of(r), r.get("speciesKey") or r.get("usageKey") or r.get("key")
    acc = r.get("acceptedKey") or r.get("acceptedUsageKey")
    if not acc:
        return None, None
    u = gbif_usage(acc)
    return _species_of(u), u.get("speciesKey") or u.get("key")


def gbif_match(name: str) -> dict | None:
    r = get_json("gbif", f"{GBIF}/species/match", {"name": ascii_latin(name), "kingdom": "Plantae", "strict": "true"})
    if r.get("matchType") in (None, "NONE") or r.get("kingdom") != "Plantae" or r.get("rank") not in SPECIES_RANKS:
        return None
    return r


ENGLISH = {"eng", "en", None, ""}


def gbif_match_loose(name: str) -> dict | None:
    """Non-strict (fuzzy) GBIF match, plants only, species rank or below."""
    r = get_json("gbif", f"{GBIF}/species/match", {"name": ascii_latin(name), "kingdom": "Plantae"})
    if r.get("matchType") not in ("EXACT", "FUZZY") or r.get("kingdom") != "Plantae" or r.get("rank") not in SPECIES_RANKS:
        return None
    return r


def gbif_vernacular_names(key: int) -> list[dict]:
    out, offset = [], 0
    while True:
        r = get_json("gbif", f"{GBIF}/species/{key}/vernacularNames", {"limit": 1000, "offset": offset})
        out += r.get("results", [])
        if r.get("endOfRecords", True) or offset > 5000:
            return out
        offset += 1000


def gbif_vernacular(q: str, limit: int = 300) -> list[dict]:
    """Backbone plant species whose English vernacular names include q exactly (after folding).
    `support` = number of vernacular-name records (from independent checklists) that match."""
    r = get_json("gbif", f"{GBIF}/species/search",
                 {"q": q, "qField": "VERNACULAR", "datasetKey": GBIF_BACKBONE, "limit": limit})
    target, out = norm_vernacular(q), []
    for x in r.get("results", []):
        if x.get("kingdom") != "Plantae" or x.get("rank") not in SPECIES_RANKS:
            continue
        names = x.get("vernacularNames", [])
        if len(names) >= 100:  # search results truncate the list at 100: fetch the species' full list
            names = gbif_vernacular_names(x["key"])
        support = sum(1 for v in names
                      if v.get("language") in ENGLISH and norm_vernacular(v.get("vernacularName", "")) == target)
        if support:
            out.append({**x, "support": support})
    return out


def _accepted_from_placement(placement: str) -> str | None:
    """'…/Asteraceae/…/Centaurea/benedicta$Carduus/benedictus' -> 'Centaurea benedicta'."""
    parts = [p for p in placement.split("$")[0].split("/") if p]
    upper = [i for i, p in enumerate(parts) if p[0].isupper()]
    if not upper or upper[-1] + 1 >= len(parts):
        return None
    g = upper[-1]
    return f"{parts[g]} {parts[g + 1]}"


def _family(placement: str) -> str | None:
    return next((p for p in placement.split("/") if p.endswith("aceae") or p in FAMILY_ALIASES), None)


def wfo_resolve(binomial: str) -> dict | None:
    """Accepted WFO name + id for a species binomial, following synonymy once."""
    try:
        r = get_json("wfo", WFO, {"input_string": ascii_latin(binomial), "acceptSingleCandidate": "true"})
    except HTTPError:
        return None
    cands = [r["match"]] if r.get("match") else r.get("candidates", [])
    cands = [c for c in cands if c.get("placement")]
    if not cands:
        return None
    exact = [c for c in cands if c["full_name_plain"].startswith(ascii_latin(binomial) + " ")
             or c["full_name_plain"] == ascii_latin(binomial)] or cands
    accepted_here = [c for c in exact if "$" not in c["placement"]]
    if accepted_here:
        c = accepted_here[0]
        toks = c["full_name_plain"].split()
        name = " ".join(toks[:3]) if len(toks) >= 3 and toks[1] == "×" else " ".join(toks[:2])
        return {"acceptedName": name, "wfoId": c["wfo_id"],
                "family": _family(c["placement"]), "wfoFullName": c["full_name_plain"], "viaSynonym": None}
    acc = _accepted_from_placement(exact[0]["placement"])
    if not acc or acc == binomial:
        return None
    a = wfo_resolve(acc)
    if a:
        a["viaSynonym"] = exact[0]["full_name_plain"]
    return a


def gbif_occurrences(species_key: int, region: str) -> int:
    """Occurrence count for a species in a region: region = 'GB' (country) or 'EUROPE' (continent)."""
    params = {"taxonKey": species_key, "limit": 0}
    params["country" if len(region) == 2 else "continent"] = region
    try:
        return int(get_json("gbif", f"{GBIF}/occurrence/search", params).get("count", 0))
    except HTTPError:
        return 0


# --- classical-genus signal ------------------------------------------------------------------

def latin_variants(token: str) -> list[str]:
    """Latinised / transliterated forms of a historical name token (HEURISTIC):
    Greek -on/-ion -> -um/-ium, -os -> -us, -e -> -a, doubled consonants collapsed, Latin endings
    added to bare stems ('Cummin' -> 'Cuminum')."""
    t = ascii_latin(token).lower()
    out = [t]
    for a, b in (("ion", "ium"), ("on", "um"), ("os", "us"), ("e", "a"), ("es", "is")):
        if t.endswith(a):
            out.append(t[: -len(a)] + b)
    collapsed = re.sub(r"([bcdfgklmnprst])\1", r"\1", t)
    out.append(collapsed)
    if re.search(r"[^aeiou]$", collapsed):
        out += [collapsed + "um", collapsed + "us", collapsed + "a"]
    seen, res = set(), []
    for v in out:
        if v not in seen and len(v) >= 4:
            seen.add(v)
            res.append(v.capitalize())
    return res


def gbif_genus(token: str) -> dict | None:
    """Accepted plant genus matching a token or one of its Latin variants (EXACT, or FUZZY with
    near-identical spelling). Synonym genera are followed to the accepted genus."""
    from difflib import SequenceMatcher
    for v in latin_variants(token):
        r = get_json("gbif", f"{GBIF}/species/match", {"name": v, "rank": "GENUS", "kingdom": "Plantae"})
        if r.get("rank") != "GENUS" or r.get("kingdom") != "Plantae":
            continue
        name = r.get("canonicalName") or ""
        mt, status = r.get("matchType"), r.get("status")
        if mt == "FUZZY" and SequenceMatcher(None, v.lower(), name.lower()).ratio() < 0.85:
            continue
        if mt not in ("EXACT", "FUZZY") or status == "DOUBTFUL":
            continue
        if status == "SYNONYM" and r.get("acceptedUsageKey"):
            u = gbif_usage(r["acceptedUsageKey"])
            acc = u.get("genus") or (u.get("canonicalName") or "").split(" ")[0]
            key = u.get("genusKey") or u.get("key")
        else:
            acc, key = name, r.get("usageKey")
        if acc:
            return {"token": token, "variant": v, "genus": acc, "genusKey": key, "matchType": mt, "via": name}
    return None


def gbif_top_species_in_genus(genus_key: int, region: str, n: int = 2) -> list[str]:
    """Most-recorded species of a genus in a region (GBIF occurrence facet)."""
    params = {"genusKey": genus_key, "limit": 0, "facet": "speciesKey", "facetLimit": n}
    params["country" if len(region) == 2 else "continent"] = region
    try:
        r = get_json("gbif", f"{GBIF}/occurrence/search", params)
    except HTTPError:
        return []
    keys = [int(c["name"]) for f in r.get("facets", []) for c in f.get("counts", [])]
    return [s for s in (_species_of(gbif_usage(k)) for k in keys) if s]
