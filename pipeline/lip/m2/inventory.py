"""Name inventory for M2: the historical plant names to resolve, before recipe extraction exists.

Entries
- Culpeper 1652: one entry per herb (heading). Query strings = alternatives in the heading
  ("Alehoof, or Ground-Ivy") + alternatives of the crosswalked 1850 heading (modern spelling).
- Pliny books XX–XXVII: one entry per plant named in a chapter title
  ("THE PERDICIUM. THE ORNITHOGALE." -> two entries). Count words ("TWENTY-SIX REMEDIES") and
  non-plant chapter titles (INTRODUCTION, …) are dropped.

`passages` = number of recipe-scope body passages in the entry (1652: "Vertues and use"
paragraphs; Pliny: chapter body paragraphs, shared by every name in a multi-name chapter). It is an
ATTESTATION PROXY used only to help choose a study set; it is not a count of extracted recipes.
"""
from __future__ import annotations

import re
import string

import pandas as pd

from ..paths import INTERIM
from ..segment.common import FOOTNOTE_ANCHOR
from ..segment.crosswalk import alternatives as heading_alternatives
from ..segment.tei import herb_name

NON_PLANT = re.compile(
    r"\b(REMED(Y|IES)|OBSERVATIONS?|PRESCRIPTIONS?|INTRODUCTION|SUMMARY|REMARKS?|HISTORY|NATURE|PROPERTIES|"
    r"VARIETIES|KINDS|SPECIES|PLANTS? WHICH|HOW|WHAT|WHEN|IN WHAT|OF THE|AUTHORS)\b")
NUMBER_WORDS = re.compile(r"\b(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|TWENTY|THIRTY|FORTY|"
                          r"FIFTY|SIXTY|SEVENTY|EIGHTY|NINETY|HUNDRED|[A-Z]+TEEN)\b")


def _with_folded(qs: list[str]) -> list[str]:
    """Add the plural/possessive-folded form of each query ('Our Ladies Thistle' -> 'our lady thistle'):
    GBIF matches tokens, so 'Ladies' would never hit "Our Lady's thistle"."""
    from .services import norm_vernacular
    out = list(qs)
    for q in qs:
        f = norm_vernacular(q)
        if f and f not in (x.lower() for x in out):
            out.append(f)
    return out


def _queries(heading: str) -> list[str]:
    parts = re.split(r",|;|\bor\b|\bOR\b|\(|\)|&|\bvulgarly called\b|\bcalled\b", herb_name(heading), flags=re.I)
    out = []
    for p in [herb_name(heading), *parts]:
        p = re.sub(r"^\s*the\s+", "", p.strip(" .,"), flags=re.I).strip()
        if len(p) >= 3 and p.lower() not in (q.lower() for q in out):
            out.append(p)
    return out


def pliny_names(title: str) -> list[str]:
    names = []
    for seg in re.split(r"[.;:]", title or ""):
        seg = re.sub(r"\[\d+\]", "", seg).strip(" ,—-")
        if not seg or NUMBER_WORDS.search(seg) or NON_PLANT.search(seg):
            continue
        seg = re.sub(r"^(THE|A|AN)\s+", "", seg)
        if 3 <= len(seg) <= 60:
            names.append(seg)
    return names


def build(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Culpeper 1652
    c = df[df.source_id == "culpeper-1652"]
    heads = c[(c.part == "herbal") & (c.passage_type == "heading") & (c.block_index == 0)]
    virt = c[(c.part == "herbal") & (c.passage_type == "body") & (c.subsection == "vertues and use")]
    n_virt = virt.groupby("entry_slug").size()
    cw = pd.read_csv(INTERIM / "culpeper_1850_1652_crosswalk.csv")
    h1850 = cw[cw.entry_1652.notna()].groupby("entry_1652").heading_1850.first()
    for h in heads.itertuples():
        name = herb_name(h.text_clean)
        if not re.search(r"[A-Za-z]", name):
            continue  # glyph-only heading: no name to resolve
        q = _queries(h.text_clean)
        modern = h1850.get(h.entry_slug)
        if isinstance(modern, str):
            q += [x for x in _queries(string.capwords(modern.lower())) if x.lower() not in (y.lower() for y in q)]
        rows.append({"nameId": f"culpeper-1652:{h.entry_slug}", "source": "culpeper-1652", "entry": h.entry_slug,
                     "nameAsWritten": name, "queries": _with_folded(q), "passages": int(n_virt.get(h.entry_slug, 0)),
                     "footnotes": [], "namesInEntry": 1})
    # Pliny books 20–27
    p = df[df.source_id.str.startswith("pliny") & (df.part == "body") & df.book.between(20, 27)]
    fn_text = df[df.passage_type == "footnote"].set_index("passage_id").text_clean
    for (book, key), g in p.groupby(["book", "entry_slug"]):
        head = g[g.passage_type == "heading"].sort_values("block_index")
        names = pliny_names(head.iloc[0].entry_title if len(head) and isinstance(head.iloc[0].entry_title, str) else "")
        if not names:
            continue
        body = g[g.passage_type == "body"]
        for i, n in enumerate(names):
            rows.append({"nameId": f"pliny-nh:b{int(book):02d}:{key}:n{i}", "source": "pliny", "entry": f"b{int(book):02d}:{key}",
                         "nameAsWritten": n, "queries": _queries(string.capwords(n.lower())), "passages": int(len(body)),
                         "footnotes": _linked_footnotes(n, g, names, fn_text), "namesInEntry": len(names)})
    return pd.DataFrame(rows)


def _linked_footnotes(name: str, chapter: pd.DataFrame, names: list[str], fn_text: pd.Series) -> list[dict]:
    """Footnotes tied to this name: an anchor right after a word of the name (strong), else, for
    single-name chapters, footnotes of the heading and first paragraph (weak)."""
    tokens = [w.lower() for w in re.findall(r"[A-Za-zæœ]{4,}", name)]
    out, seen = [], set()
    for r in chapter.sort_values("block_index").itertuples():
        raw = r.text_original
        for m in FOOTNOTE_ANCHOR.finditer(raw):
            fid = f"{r.source_id}:fn{m.group(1)}"
            if fid in seen or fid not in fn_text.index:
                continue
            window = re.sub(r"\s+", " ", raw[max(0, m.start() - 80):m.start()]).lower()
            if tokens and any(t in window[-40:] for t in tokens):
                out.append({"id": fid, "strength": "strong"})
                seen.add(fid)
    if not out and len(names) == 1:
        early = chapter[chapter.block_index <= 1]
        for r in early.sort_values("block_index").itertuples():
            for m in FOOTNOTE_ANCHOR.finditer(r.text_original):
                fid = f"{r.source_id}:fn{m.group(1)}"
                if fid not in seen and fid in fn_text.index:
                    out.append({"id": fid, "strength": "weak"})
                    seen.add(fid)
    return out
