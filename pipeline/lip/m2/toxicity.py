"""Known-toxicity flags from an openly licensed, cited source (HEURISTIC screen, not a safety rating).

Source: English Wikipedia, "List of poisonous plants" (CC BY-SA 4.0), wikitext fetched with action=raw;
the revision id and retrieval time are recorded with every output. The page itself is tagged by its
editors as needing expert review. Absence from the list does NOT mean a plant is safe: unlisted
species are "unknown", never "none_known".
"""
from __future__ import annotations

import re
from functools import lru_cache

from ..http import get_json, get_text

TITLE = "List_of_poisonous_plants"
RAW = f"https://en.wikipedia.org/w/index.php?title={TITLE}&action=raw"
PAGE = f"https://en.wikipedia.org/wiki/{TITLE}"
API = "https://en.wikipedia.org/w/api.php"


@lru_cache(maxsize=1)
def load() -> dict:
    text, sha, when = get_text("sources", RAW)
    rev = get_json("sources", API, {"action": "query", "prop": "revisions", "titles": TITLE, "rvprop": "ids|timestamp", "format": "json"})
    page = next(iter(rev["query"]["pages"].values()))["revisions"][0]
    species = set(re.findall(r"''\[\[([A-Z][a-z]+ [a-z][a-z\-]+)(?:\|[^\]]*)?\]\]''", text))
    species |= set(re.findall(r"''([A-Z][a-z]+ [a-z][a-z\-]+)''", text))
    genera = {m for m in re.findall(r"''\[\[([A-Z][a-z]+)(?:\|[^\]]*)?\]\]''", text)}
    genera |= {m for m in re.findall(r"''([A-Z][a-z]{3,})''(?!\s*[a-z])", text)}
    return {"species": species, "genera": genera - {s.split()[0] for s in []}, "sha256": sha, "retrievedAt": when,
            "revid": page["revid"], "revTimestamp": page["timestamp"], "url": PAGE}


def flag(binomial: str | None) -> tuple[str, str]:
    """-> (known_toxic | unknown, note)."""
    if not isinstance(binomial, str) or not binomial.strip():
        return "unknown", ""
    src = load()
    cite = f"Wikipedia 'List of poisonous plants', rev {src['revid']}"
    if binomial in src["species"]:
        return "known_toxic", f"species listed in {cite}"
    if binomial.split()[0] in src["genera"]:
        return "known_toxic", f"genus {binomial.split()[0]} listed in {cite} (genus-level listing)"
    return "unknown", f"not listed in {cite}; absence is not evidence of safety"
