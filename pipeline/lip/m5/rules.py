"""M5 rule-based study-method extractor (no LLM): solvent, heat, part, fresh or dried, and filtration.

Driven entirely by the versioned keyword lexicon config/m5_lexicon/v1.toml (HEURISTIC; read its header). Rules:
- Text is split into sentences. A solvent mention counts only in a sentence with an extraction cue, and not when the
  lexicon's exclusion context says it is a fraction, a disease model ("ethanol-induced"), a beverage ("green tea") etc.
- One preparation per distinct solvent category found. No solvent found -> one preparation with solvent "unknown".
- heat: the cues in that preparation's sentences (warm, then boiled, then cold, each masking the next; plus a stated
  extraction temperature in HEURISTIC bands). Exactly one category -> that value; several -> "unknown" (flagged); none ->
  the study-wide value only if the study has a single preparation and exactly one heat category overall.
- part: one part category in the preparation's sentences, else exactly one in the whole text; several -> "unknown".
- freshOrDried and filtered: study-wide, exactly one category, else "unknown".
- Unstated = "unknown"; nothing is inferred. Every non-unknown value keeps the verbatim matched text and its offsets.
Version string: "m5_rules/v1:<sha256 of the lexicon file, 10 hex>", recorded on every output.
"""
from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache

from ..paths import ROOT
from .methods import ethanol_fraction

LEX_PATH = ROOT / "config" / "m5_lexicon" / "v1.toml"
FIELDS = ["solvent", "heat", "part", "freshOrDried", "filtered"]
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


@dataclass
class Lexicon:
    version: str
    cues: list[re.Pattern]
    solvent: list[tuple[str, list[re.Pattern]]]
    excl_after: list[re.Pattern]
    excl_before: list[re.Pattern]
    before_window: int
    heat: list[tuple[str, list[re.Pattern]]]
    temp: re.Pattern
    temp_ignore: list[str]
    cold_max: int
    boiled_min: int
    part: list[tuple[str, list[re.Pattern]]]
    dried: list[re.Pattern]
    fresh: list[re.Pattern]
    dried_excl_before: list[str]
    dried_excl_after: list[re.Pattern]
    filtered: list[tuple[str, list[re.Pattern]]]


def _c(ps):
    return [re.compile(p, re.I) for p in ps]


@lru_cache(maxsize=4)
def lexicon(path=LEX_PATH) -> Lexicon:
    raw = path.read_bytes()
    d = tomllib.loads(raw.decode())
    order = lambda sec, keys: [(k, _c(d[sec][k])) for k in keys]
    return Lexicon(
        version=f"m5_rules/{d['version']}:{hashlib.sha256(raw).hexdigest()[:10]}",
        cues=_c(d["sentences"]["extraction_cues"]),
        solvent=order("solvent", ["hydroethanolic", "methanol", "ethanol", "hexane", "chloroform", "ethyl_acetate", "dichloromethane",
                                  "acetone", "co2", "water", "other"]),
        excl_after=_c(d["solvent_exclude"]["after"]), excl_before=_c(d["solvent_exclude"]["before"]),
        before_window=d["solvent_exclude"]["before_window"],
        heat=order("heat", ["warm", "boiled", "cold"]),
        temp=re.compile(d["heat_temperature"]["pattern"], re.I), temp_ignore=d["heat_temperature"]["ignore_if_near"],
        cold_max=d["heat_temperature"]["cold_max"], boiled_min=d["heat_temperature"]["boiled_min"],
        part=order("part", ["leaf", "root", "rhizome", "seed", "fruit", "flower", "bark", "stem", "aerial_parts", "whole_plant",
                            "resin", "juice", "other"]),
        dried=_c(d["fresh_or_dried"]["dried"]), fresh=_c(d["fresh_or_dried"]["fresh"]),
        dried_excl_before=d["fresh_or_dried"]["dried_exclude_before"], dried_excl_after=_c(d["fresh_or_dried"]["dried_exclude_after"]),
        filtered=order("filtered", ["yes", "no"]),
    )


@dataclass
class Hit:
    category: str
    start: int
    end: int
    text: str


def sentences(text: str) -> list[tuple[int, int]]:
    out, i = [], 0
    for m in SENT.finditer(text):
        out.append((i, m.start()))
        i = m.end()
    out.append((i, len(text)))
    return [(a, b) for a, b in out if b > a]


def _ordered_hits(text, a, b, groups, mask=None) -> list[Hit]:
    """Matches in text[a:b], category by category; a span already taken masks overlapping later matches."""
    taken = list(mask or [])
    hits = []
    for cat, pats in groups:
        for p in pats:
            for m in p.finditer(text, a, b):
                s, e = m.start(), m.end()
                if any(s < te and ts < e for ts, te in taken):
                    continue
                taken.append((s, e))
                hits.append(Hit(cat, s, e, m.group(0)))
    return sorted(hits, key=lambda h: h.start)


def _solvent_hits(text, a, b, L: Lexicon) -> list[Hit]:
    out = []
    for h in _ordered_hits(text, a, b, L.solvent):
        after, before = text[h.end:h.end + 25], text[max(a, h.start - L.before_window):h.start]
        if any(p.search(after) for p in L.excl_after) or any(p.search(before) for p in L.excl_before):
            continue
        if h.category == "hydroethanolic":
            pct = re.search(r"(\d{1,3}(?:[.,]\d+)?)\s?%", h.text)
            if pct and float(pct.group(1).replace(",", ".")) >= 95:
                h = Hit("ethanol", h.start, h.end, h.text)   # HEURISTIC: 95% or more is coded as ethanol
        out.append(h)
    return out


def _heat_hits(text, a, b, L: Lexicon) -> list[Hit]:
    hits = _ordered_hits(text, a, b, L.heat)
    for m in L.temp.finditer(text, a, b):
        near = text[max(a, m.start() - 60):m.start()].lower()
        if any(w in near for w in L.temp_ignore):
            continue
        t = int(m.group(1))
        cat = "cold" if t <= L.cold_max else "boiled" if t >= L.boiled_min else "warm"
        hits.append(Hit(cat, m.start(), m.end(), m.group(0)))
    return hits


def _dried_hits(text, L: Lexicon) -> list[Hit]:
    hits = []
    for p in L.dried:
        for m in p.finditer(text):
            before = text[max(0, m.start() - 30):m.start()].lower()
            if any(w in before for w in L.dried_excl_before) or any(q.search(text[m.end():m.end() + 25]) for q in L.dried_excl_after):
                continue
            hits.append(Hit("dried", m.start(), m.end(), m.group(0)))
    for p in L.fresh:
        hits += [Hit("fresh", m.start(), m.end(), m.group(0)) for m in p.finditer(text)]
    return hits


def _one(hits: list[Hit]) -> tuple[str, Hit | None, bool]:
    """(value, evidence hit, conflict)."""
    cats = {h.category for h in hits}
    if len(cats) == 1:
        return cats.pop(), hits[0], False
    return "unknown", None, len(cats) > 1


@dataclass
class Prep:
    solvent: str = "unknown"
    solventText: str = "unknown"
    ethanolFraction: float | None = None
    heat: str = "unknown"
    heatText: str = "unknown"
    part: str = "unknown"
    freshOrDried: str = "unknown"
    filtered: str = "unknown"
    evidence: list[dict] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    @property
    def unknownFields(self) -> list[str]:
        return [f for f in FIELDS if getattr(self, f) == "unknown"]


def _ev(f: str, h: Hit) -> dict:
    return {"field": f, "quote": h.text, "start": h.start, "end": h.end}


def extract(text: str, L: Lexicon | None = None) -> list[Prep]:
    """Code every preparation a study text describes. Always returns at least one preparation (all unknown when the
    text describes none, flagged)."""
    L = L or lexicon()
    sents = sentences(text)
    cue_sents = [(a, b) for a, b in sents if any(p.search(text, a, b) for p in L.cues)]
    by_cat: dict[str, list[tuple[Hit, tuple[int, int]]]] = {}
    for a, b in cue_sents:
        for h in _solvent_hits(text, a, b, L):
            by_cat.setdefault(h.category, []).append((h, (a, b)))
    preps: list[tuple[Prep, list[tuple[int, int]]]] = []
    for cat, hs in by_cat.items():
        p = Prep(solvent=cat, solventText=hs[0][0].text)
        p.evidence.append(_ev("solvent", hs[0][0]))
        p.ethanolFraction = ethanol_fraction(cat, p.solventText)
        preps.append((p, sorted({s for _, s in hs})))
    if not preps:
        p = Prep(flags=["no solvent stated" if cue_sents else "no preparation described"])
        preps.append((p, cue_sents))
    # heat
    all_heat = [h for a, b in cue_sents for h in _heat_hits(text, a, b, L)]
    for p, ss in preps:
        hv, hh, conflict = _one([h for a, b in ss for h in _heat_hits(text, a, b, L)])
        if hh is None and not conflict and len(preps) == 1:
            hv, hh, conflict = _one(all_heat)
        if conflict:
            p.flags.append("conflicting heat cues")
        if hh:
            p.heat, p.heatText = hv, hh.text
            p.evidence.append(_ev("heat", hh))
    # part
    all_part = _ordered_hits(text, 0, len(text), L.part)
    for p, ss in preps:
        pv, ph, conflict = _one([h for a, b in ss for h in _ordered_hits(text, a, b, L.part)])
        if ph is None and not conflict:
            pv, ph, conflict = _one(all_part)
        if conflict:
            p.flags.append("several plant parts named")
        if ph:
            p.part = pv
            p.evidence.append(_ev("part", ph))
    # study-wide: fresh or dried, filtration
    fv, fh, fconf = _one(_dried_hits(text, L))
    tv, th, tconf = _one(_ordered_hits(text, 0, len(text), L.filtered))
    for p, _ in preps:
        if fh:
            p.freshOrDried = fv
            p.evidence.append(_ev("freshOrDried", fh))
        elif fconf:
            p.flags.append("both fresh and dried material named")
        if th:
            p.filtered = tv
            p.evidence.append(_ev("filtered", th))
        elif tconf:
            p.flags.append("conflicting filtration cues")
    return [p for p, _ in preps]
