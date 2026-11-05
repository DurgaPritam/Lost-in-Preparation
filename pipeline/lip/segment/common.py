"""Shared segmentation primitives.

A *block* is a run of non-blank lines. Every non-blank line between the Gutenberg START and
END markers belongs to exactly one block, and every block becomes exactly one passage, so
nothing is lost. Line numbers are 1-based and refer to the raw file as downloaded.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field

GUTENBERG_START = re.compile(r"^\*\*\* START OF TH(E|IS) PROJECT GUTENBERG EBOOK")
GUTENBERG_END = re.compile(r"^\*\*\* END OF TH(E|IS) PROJECT GUTENBERG EBOOK")
FOOTNOTE_ANCHOR = re.compile(r"\[(\d+)\]")


@dataclass
class Block:
    line_start: int
    line_end: int
    lines: list[str]

    @property
    def raw(self) -> str:
        return "\n".join(self.lines)

    @property
    def joined(self) -> str:
        return " ".join(line.strip() for line in self.lines)

    @property
    def indent(self) -> int:
        first = self.lines[0]
        return len(first) - len(first.lstrip(" "))


@dataclass
class Passage:
    passage_id: str
    source_id: str
    part: str
    passage_type: str  # heading | body | footnote | illustration | editorial | contents | index | front_matter | back_matter
    line_start: int
    line_end: int
    text_original: str
    book: int | None = None
    section: str | None = None
    chapter: str | None = None
    chapter_alt: str | None = None
    page: str | None = None
    entry_title: str | None = None
    entry_slug: str | None = None
    entry_ordinal: int | None = None
    subsection: str | None = None
    block_index: int = 0
    recipe_scope: bool = False
    scope_reason: str = ""
    footnote_refs: list[str] = field(default_factory=list)
    footnote_of: list[str] = field(default_factory=list)
    text_clean: str = ""
    cleaning_ops: list[str] = field(default_factory=list)


def gutenberg_bounds(lines: list[str]) -> tuple[int, int]:
    """Return 0-based indices (start_marker, end_marker); content lies strictly between them."""
    starts = [i for i, l in enumerate(lines) if GUTENBERG_START.match(l)]
    ends = [i for i, l in enumerate(lines) if GUTENBERG_END.match(l)]
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError(f"expected one START and one END marker, got {len(starts)}/{len(ends)}")
    return starts[0], ends[0]


def split_blocks(lines: list[str], lo: int, hi: int) -> list[Block]:
    """Blocks from 0-based line range [lo, hi)."""
    blocks: list[Block] = []
    cur: list[str] = []
    cur_start = None
    for i in range(lo, hi):
        line = lines[i].rstrip("\r")
        if line.strip():
            if cur_start is None:
                cur_start = i
            cur.append(line)
        elif cur:
            blocks.append(Block(cur_start + 1, i, cur))
            cur, cur_start = [], None
    if cur:
        blocks.append(Block(cur_start + 1, hi, cur))
    return blocks


def is_caps_heading(block: Block, max_lines: int = 3) -> bool:
    """A heading has letters, no lowercase letters, and is short."""
    text = block.joined
    if len(block.lines) > max_lines or len(text) > 200:
        return False
    if text.startswith("["):
        return False
    return any(c.isalpha() for c in text) and not any(c.islower() for c in text)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("’", "").replace("'", "")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:60].rstrip("-") or "untitled"


def clean_text(raw: str, strip_footnote_anchors: bool) -> tuple[str, list[str]]:
    """Conservative cleaning. Never changes spelling, hyphenation or punctuation.

    Ops (recorded per passage):
      - nfc:            Unicode NFC normalisation
      - unwrap:         join wrapped lines with a single space, collapse runs of whitespace
      - italics:        remove Gutenberg `_italic_` markers
      - footnote_anchor: remove `[123]` anchors (kept in footnote_refs)
    Smudge markers (`*`, per the Culpeper transcriber) are kept as printed.
    """
    ops: list[str] = []
    text = unicodedata.normalize("NFC", raw)
    if text != raw:
        ops.append("nfc")
    if strip_footnote_anchors and FOOTNOTE_ANCHOR.search(text):
        text = FOOTNOTE_ANCHOR.sub("", text)
        ops.append("footnote_anchor")
    if "_" in text:
        text = text.replace("_", "")
        ops.append("italics")
    unwrapped = re.sub(r"\s+", " ", text).strip()
    if unwrapped != text:
        ops.append("unwrap")
    return unwrapped, ops


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SlugRegistry:
    """Deterministic de-duplication of slugs within a scope (first wins, then ~2, ~3…)."""

    def __init__(self) -> None:
        self.seen: dict[str, int] = {}

    def claim(self, slug: str) -> str:
        n = self.seen.get(slug, 0) + 1
        self.seen[slug] = n
        return slug if n == 1 else f"{slug}~{n}"
