"""Verbatim-span checks (the rule: every field must be supported by a quote from the passage).

Matching normalises only typography that the model may legitimately re-encode: curly vs straight
quotes, dash variants, and runs of whitespace. Spelling, case and punctuation must match exactly.
Every normalisation maps one character to one character, so offsets found in the normalised text
are valid offsets into the passage's cleaned text.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from contract.models import UNKNOWN

from .schema import EVIDENCE_FIELDS, HEADING_ALLOWED, TEXT_FIELDS, LLMRecipe

_TRANS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "—": "-", "–": "-"})


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).translate(_TRANS)
    return re.sub(r"\s+", " ", s)


def _trim(q: str) -> str:
    return norm(q).strip().rstrip(".,;:")


def find(quote: str, text: str) -> tuple[int, int] | None:
    q = _trim(quote)
    if not q:
        return None
    i = norm(text).find(q)
    return (i, i + len(q)) if i >= 0 else None


@dataclass
class SpanCheck:
    ok: bool
    errors: list[str] = field(default_factory=list)
    offsets: dict[str, list[tuple[int, int, bool]]] = field(default_factory=dict)  # field -> [(start, end, inHeading)]


def check_recipe(r: LLMRecipe, passage: str, heading: str) -> SpanCheck:
    res = SpanCheck(ok=True)

    def locate(fieldname: str, quote: str, heading_ok: bool) -> None:
        hit = find(quote, passage)
        if hit:
            res.offsets.setdefault(fieldname, []).append((hit[0], hit[1], False))
            return
        if heading_ok and heading and find(quote, heading):
            res.offsets.setdefault(fieldname, []).append((-1, -1, True))
            return
        res.errors.append(f"{fieldname}: quote not found verbatim in passage: {quote!r}")

    locate("recipe", r.recipeQuote, heading_ok=False)

    for f in TEXT_FIELDS:
        v = getattr(r, f)
        if v != UNKNOWN:
            locate(f, v, heading_ok=f in r.quotesFromHeading and f in HEADING_ALLOWED)

    for ing in r.ingredients:
        locate("ingredients", ing.plantNameAsWritten, heading_ok="ingredients" in r.quotesFromHeading)

    by_field: dict[str, list[str]] = {}
    for ev in r.evidence:
        by_field.setdefault(ev.field, []).append(ev.quote)
    for f in EVIDENCE_FIELDS:
        value = getattr(r, f)
        filled = [v for v in value if v != UNKNOWN] if isinstance(value, list) else ([value] if value != UNKNOWN else [])
        if f != "recipeType" and filled and not by_field.get(f):  # recipeType: own rules below
            res.errors.append(f"{f}={value}: no evidence quote given")
        for q in by_field.get(f, []):
            locate(f, q, heading_ok=False)

    if r.recipeType == "single_plant" and len(r.ingredients) != 1:
        res.errors.append(f"recipeType=single_plant but {len(r.ingredients)} ingredients listed")
    if r.recipeType == "compound" and len(r.ingredients) < 2 and not by_field.get("recipeType"):
        res.errors.append("recipeType=compound with <2 ingredients needs an evidence quote")
    if not r.solvent:
        res.errors.append("solvent list is empty (use ['unknown'])")
    if "unknown" in r.solvent and len(r.solvent) > 1:
        res.errors.append("solvent mixes 'unknown' with known values")

    res.ok = not res.errors
    return res
