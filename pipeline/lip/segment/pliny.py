"""Segmenter for Pliny, Natural History, Bostock & Riley translation (Bohn, Gutenberg #61113 / #60688).

Parts (located by text markers): front_matter (title, transcriber notes, contents) → body
(BOOK → CHAP. → paragraphs) → footnotes (Bostock & Riley's editorial notes) → back_matter.

IDs
  body:      pliny-nh:b{book:02d}:c{chapter:03d}:{k:03d}   (c000 = book-level blocks before CHAP. 1)
  footnotes: {source_id}:fn{n}                             (numbering is per volume)
Only body paragraphs in the configured `scope_books` are recipe_scope. Footnotes are editorial
(19th-century), never recipe_scope, but are kept and linked: they carry plant identifications
useful for M2.
"""
from __future__ import annotations

import re

from .common import (
    FOOTNOTE_ANCHOR,
    Block,
    Passage,
    SlugRegistry,
    gutenberg_bounds,
    is_caps_heading,
    split_blocks,
)

BOOK_HEAD = re.compile(r"^BOOK ([XVILC]+)\.$")
CHAP_HEAD = re.compile(r"^CHAP\.?\s*(\d+)\.?\s*(?:\((\d+)\.?\))?\s*[—–-]*\s*(.*)$")
BOOK_APPARATUS = re.compile(r"^(SUMMARY|(ROMAN|FOREIGN|MEDICAL) AUTHORS QUOTED)\.?—")
FOOTNOTE_START = re.compile(r"^\[(\d+)\]")

MARKERS = [
    ("body", re.compile(r"^NATURAL HISTORY OF PLINY\.?$")),
    ("footnotes", re.compile(r"^FOOTNOTES:$")),
    ("back_matter", re.compile(r"^\s*END OF VOL\.")),
]

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(s: str) -> int:
    total = 0
    for a, b in zip(s, s[1:] + " "):
        v = ROMAN[a]
        total += -v if b != " " and ROMAN[b] > v else v
    return total


def _part_bounds(lines: list[str], lo: int, hi: int) -> list[tuple[str, int, int]]:
    starts = [("front_matter", lo + 1)]
    cursor = lo + 1
    for name, rx in MARKERS:
        hits = [i for i in range(cursor, hi) if rx.match(lines[i])]
        if not hits:
            raise ValueError(f"part marker not found: {name}")
        starts.append((name, hits[0]))
        cursor = hits[0] + 1
    return [(n, s, starts[i + 1][1] if i + 1 < len(starts) else hi) for i, (n, s) in enumerate(starts)]


def segment(source: dict, lines: list[str]) -> list[Passage]:
    sid = source["id"]
    scope_books = set(source.get("scope_books", []))
    lo, hi = gutenberg_bounds(lines)
    out: list[Passage] = []

    for part, p_lo, p_hi in _part_bounds(lines, lo, hi):
        blocks = split_blocks(lines, p_lo, p_hi)
        if part == "front_matter":
            seen_contents = False
            for k, b in enumerate(blocks):
                if b.joined == "CONTENTS":
                    seen_contents = True
                if b.joined.startswith("Transcriber"):
                    btype = "editorial"
                else:
                    btype = "contents" if seen_contents else "front_matter"
                out.append(_p(sid, f"{sid}:front_matter:{k:04d}", part, btype, b, reason="front matter / contents"))
        elif part == "body":
            out.extend(_body(sid, blocks, scope_books))
        elif part == "footnotes":
            out.extend(_footnotes(sid, blocks, lines))
        else:
            for k, b in enumerate(blocks):
                out.append(_p(sid, f"{sid}:back_matter:{k:04d}", part, "editorial", b, reason="back matter / transcriber notes"))
    return out


def _p(sid, pid, part, btype, b: Block, reason="", **kw) -> Passage:
    return Passage(
        passage_id=pid, source_id=sid, part=part, passage_type=btype,
        line_start=b.line_start, line_end=b.line_end, text_original=b.raw,
        block_index=int(pid.rsplit(":", 1)[1]) if pid.rsplit(":", 1)[1].isdigit() else 0,
        scope_reason=reason, **kw,
    )


def _body(sid: str, blocks: list[Block], scope_books: set[int]) -> list[Passage]:
    out: list[Passage] = []
    book: int | None = None
    chap_key = chapter = chapter_alt = title = None
    chap_reg = SlugRegistry()
    k = 0
    pre_k = 0
    for b in blocks:
        text = b.joined.strip()
        bm = BOOK_HEAD.match(text)
        cm = CHAP_HEAD.match(text) if is_caps_heading(b) or text.startswith("CHAP") else None
        if bm:
            book = roman_to_int(bm.group(1))
            chap_reg = SlugRegistry()
            chap_key, chapter, chapter_alt, title, k = "c000", None, None, None, 0
            btype = "heading"
        elif cm and book is not None:
            chapter, chapter_alt, title = cm.group(1), cm.group(2), cm.group(3).strip() or None
            chap_key = chap_reg.claim(f"c{int(chapter):03d}")
            k = 0
            btype = "heading"
        elif is_caps_heading(b):
            btype = "heading"
        elif BOOK_APPARATUS.match(text):
            btype = "book_apparatus"
        else:
            btype = "body"

        if book is None:
            pid = f"{sid}:body:_:{pre_k:03d}"
            pre_k += 1
        else:
            pid = f"pliny-nh:b{book:02d}:{chap_key}:{k:03d}"
            k += 1
        in_scope = btype == "body" and book in scope_books and chapter is not None
        if in_scope:
            reason = ""
        elif btype == "book_apparatus":
            reason = "end-of-book summary / list of authors quoted"
        elif btype == "body" and book not in scope_books:
            reason = f"book {book} outside configured scope (books {sorted(scope_books)})"
        else:
            reason = f"{btype} block"
        out.append(
            Passage(
                passage_id=pid, source_id=sid, part="body", passage_type=btype,
                line_start=b.line_start, line_end=b.line_end, text_original=b.raw,
                book=book, chapter=chapter, chapter_alt=chapter_alt, entry_title=title,
                entry_slug=chap_key, block_index=int(pid.rsplit(":", 1)[1]),
                recipe_scope=in_scope, scope_reason=reason,
                footnote_refs=[f"{sid}:fn{n}" for n in FOOTNOTE_ANCHOR.findall(b.raw)],
            )
        )
    return out


def _footnotes(sid: str, blocks: list[Block], lines: list[str]) -> list[Passage]:
    """One passage per footnote; continuation paragraphs (no leading [n]) join the previous note."""
    out: list[Passage] = []
    reg = SlugRegistry()
    for k, b in enumerate(blocks):
        m = FOOTNOTE_START.match(b.joined)
        if m:
            pid = f"{sid}:" + reg.claim(f"fn{m.group(1)}")
            out.append(_p(sid, pid, "footnotes", "footnote", b, reason="editorial footnote (Bostock & Riley)"))
        elif out and out[-1].passage_type == "footnote":
            prev = out[-1]
            prev.line_end = b.line_end
            prev.text_original = "\n".join(lines[prev.line_start - 1 : prev.line_end])
        else:
            out.append(_p(sid, f"{sid}:footnotes:{k:04d}", "footnotes", "heading", b, reason="footnotes heading"))
    return out
