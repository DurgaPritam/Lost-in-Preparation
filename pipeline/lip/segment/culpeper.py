"""Segmenter for Culpeper, The Complete Herbal (Kelly, 1850; Gutenberg #49513).

Parts are located by text markers (not line numbers), searched in order:
  front_matter → herbal → directions → dispensatory → last_legacies → index → disease_list
  → transcriber_notes.
Herbal: one entry per plant heading (indented, all caps, may wrap over two lines). Subsections
come from the `_Descript._]`, `_Place._]`, `_Time._]`, `_Government and virtues._]` tags; text
before the first tag is the naming paragraph (`intro`), later untagged paragraphs inherit the
previous tag.
Other parts: one entry per caps heading; SECTION/CHAPTER headings set `section`/`chapter`.
"""
from __future__ import annotations

import re

from .common import (
    Block,
    Passage,
    SlugRegistry,
    gutenberg_bounds,
    is_caps_heading,
    slugify,
    split_blocks,
)

# (part, multiline regex for the first line of the part, recipe_scope, scope_reason)
PARTS = [
    ("front_matter", None, False, "title page, prefaces and epistles"),
    ("herbal", r"^THE\n\nENGLISH PHYSICIAN\n\nENLARGED\.$", True, ""),
    ("directions", r"^DIRECTIONS FOR MAKING SYRUPS, CONSERVES,$", True, ""),
    ("dispensatory", r"^THE\n\nENGLISH PHYSICIAN\n\nAND\n\nFAMILY DISPENSATORY\.$", True, ""),
    ("last_legacies", r"^ +_CULPEPER’S LAST LEGACIES\._$", True, ""),
    ("index", r"^GENERAL INDEX$", False, "index"),
    ("disease_list", r"^A LIST OF THE PRINCIPAL DISEASES\.$", False, "index of diseases"),
    ("transcriber_notes", r"^Transcriber’s Notes:$", False, "modern transcriber notes, not historical text"),
]

SUBSECTION_TAG = re.compile(r"^\s*_([A-Z][A-Za-z ,&’']{1,40}?)\._?\]")
SECTION_HEAD = re.compile(r"^SECTION [IVXLC]+\.?$")
CHAPTER_HEAD = re.compile(r"^CHAPTER [IVXLC]+\.?$")


def _part_starts(lines: list[str], lo: int, hi: int) -> list[tuple[int, tuple]]:
    """0-based start line of each part, searched sequentially."""
    text = "\n".join(lines)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line) + 1)
    starts = [(lo + 1, PARTS[0])]
    cursor = offsets[lo + 1]
    for spec in PARTS[1:]:
        m = re.compile(spec[1], re.M).search(text, cursor, offsets[hi])
        if m is None:
            raise ValueError(f"part marker not found: {spec[0]}")
        line_idx = text.count("\n", 0, m.start())
        starts.append((line_idx, spec))
        cursor = m.end()
    return starts


def _block_type(block: Block, part: str) -> str:
    t = block.joined
    if t.startswith("[Illustration"):
        return "illustration"
    if t.startswith("[Transcriber"):
        return "editorial"
    if part == "transcriber_notes":
        return "editorial"
    if part in ("index", "disease_list"):
        return "heading" if is_caps_heading(block) else "index"
    if is_caps_heading(block):
        return "heading"
    if part == "front_matter":
        return "front_matter"
    return "body"


def segment(source: dict, lines: list[str]) -> list[Passage]:
    sid = source["id"]
    lo, hi = gutenberg_bounds(lines)
    starts = _part_starts(lines, lo, hi)
    bounds = [(s, (starts[i + 1][0] if i + 1 < len(starts) else hi), spec) for i, (s, spec) in enumerate(starts)]

    passages: list[Passage] = []
    for p_lo, p_hi, (part, _rx, in_scope, reason) in bounds:
        entry_slugs = SlugRegistry()
        entry_title = entry_slug = section = chapter = subsection = None
        entry_ordinal = 0
        k = 0
        generic_k = 0
        for block in split_blocks(lines, p_lo, p_hi):
            btype = _block_type(block, part)
            heading_text = block.joined.strip()

            if part == "herbal":
                if btype == "heading" and block.indent >= 2:
                    entry_ordinal += 1
                    entry_title = heading_text
                    entry_slug = entry_slugs.claim(slugify(heading_text))
                    subsection, k = None, 0
                elif btype == "body":
                    m = SUBSECTION_TAG.match(block.lines[0])
                    if m:
                        subsection = m.group(1).strip().lower()
                    elif subsection is None and entry_slug is not None:
                        subsection = "intro"
                if entry_slug is None:
                    pid = f"{sid}:herbal:_title:{generic_k:03d}"
                    generic_k += 1
                else:
                    pid = f"{sid}:herbal:{entry_slug}:{k:03d}"
                    k += 1
            else:
                if btype == "heading":
                    if SECTION_HEAD.match(heading_text):
                        section, chapter = heading_text.rstrip("."), None
                    elif CHAPTER_HEAD.match(heading_text):
                        chapter = heading_text.rstrip(".")
                    entry_ordinal += 1
                    entry_title = heading_text
                    entry_slug = f"s{entry_ordinal:03d}-" + entry_slugs.claim(slugify(heading_text))
                    k = 0
                prefix = entry_slug or "_"
                pid = f"{sid}:{part}:{prefix}:{k:03d}"
                k += 1

            scope = in_scope and btype == "body"
            passages.append(
                Passage(
                    passage_id=pid,
                    source_id=sid,
                    part=part,
                    passage_type=btype,
                    line_start=block.line_start,
                    line_end=block.line_end,
                    text_original=block.raw,
                    section=section,
                    chapter=chapter,
                    entry_title=entry_title,
                    entry_slug=entry_slug,
                    entry_ordinal=entry_ordinal or None,
                    subsection=subsection if part == "herbal" and btype == "body" else None,
                    block_index=int(pid.rsplit(":", 1)[1]),
                    recipe_scope=scope,
                    scope_reason="" if scope else (reason or f"{btype} block"),
                )
            )
    return passages
