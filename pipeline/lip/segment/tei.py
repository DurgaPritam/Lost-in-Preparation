"""Segmenter for EEBO-TCP TEI P5 texts (Culpeper, The English Physitian, 1652 — TCP A35365).

Passages are TEI block elements: head, p, list item, lg, q, signed, opener, closer, salute.
Rendering (text_clean):
  - <g ref="char:EOLhyphen"/> and EOLunhyphen: line-end word breaks are joined ("un-|to" -> "unto")
  - <gap reason="illegible" extent="N letters"/> -> visible marker ⟦?…?⟧ (one ? per letter);
    <gap reason="foreign"/> -> ⟦foreign⟧. Markers are never removed downstream.
  - <note place="margin"> (printed marginal notes) are removed from the running text and emitted
    as separate `marginal_note` passages linked to their block (footnote_refs / footnote_of).
  - <pb/> sets the page; other markup (hi, expan, …) is reduced to its text.
Parts: front_matter (front + letters) · herbal (div[@type=herb]) · directions (sections/chapters)
· index. Only herbal and directions body blocks are recipe scope.
"""
from __future__ import annotations

import re

from lxml import etree

from .common import Passage, SlugRegistry, slugify

TEI = "{http://www.tei-c.org/ns/1.0}"
BLOCKS = {"head", "p", "item", "lg", "q", "signed", "opener", "closer", "salute", "trailer", "byline",
          "label", "argument", "epigraph", "dateline"}
GAP_MARK = "⟦{}⟧"
GLYPHS = re.compile(r"[^\w\s,.'’()&-]")


def local(el) -> str:
    return el.tag.replace(TEI, "") if isinstance(el.tag, str) else ""


def gap_marker(el) -> str:
    if el.get("reason") == "foreign":
        return GAP_MARK.format("foreign")
    m = re.match(r"(\d+)", el.get("extent", ""))
    return GAP_MARK.format("?" * int(m.group(1)) if m else "?")


def render(el, notes: list | None = None) -> str:
    """Text of el with TEI rules applied. Marginal notes are skipped and collected into `notes`."""
    if local(el) == "gap":
        return gap_marker(el)
    out: list[str] = []
    join_next = [False]

    def emit(s: str | None):
        if not s:
            return
        if join_next[0]:
            s = s.lstrip()
            join_next[0] = False
        out.append(s)

    def walk(e, top=False):
        tag = local(e)
        if not top:
            if tag == "note":
                if notes is not None:
                    notes.append(e)
                emit(e.tail)
                return
            if tag == "g" and e.get("ref") in ("char:EOLhyphen", "char:EOLunhyphen"):
                join_next[0] = True
                if out:
                    out[-1] = out[-1].rstrip()
                emit(e.tail)
                return
            if tag == "gap":
                emit(gap_marker(e))
                emit(e.tail)
                return
            if tag == "pb":
                emit(e.tail)
                return
        emit(e.text)
        for c in e:
            if isinstance(c.tag, str):
                walk(c)
            else:
                emit(c.tail)  # comments / PIs
        if not top:
            emit(e.tail)

    walk(el, top=True)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def source_xml(el) -> str:
    s = etree.tostring(el, encoding="unicode", with_tail=False)
    return s.replace(' xmlns="http://www.tei-c.org/ns/1.0"', "")


def herb_name(head_text: str) -> str:
    return re.sub(r"\s+", " ", GLYPHS.sub(" ", head_text)).strip(" .")


def canonical_part(head_text: str) -> str:
    """Map 1652 part headings ('Vertues and Vse.', '♄ Discription.') to canonical labels."""
    s = herb_name(head_text).lower().replace("vse", "use")
    s = re.sub(r"\s+", " ", s).strip(" .")
    s = re.sub(r"^the ", "", s)
    if s.startswith(("vert", "virt")):
        return "vertues and use"
    if s.startswith(("descr", "discr")):
        return "description"
    if "place" in s and "time" in s:
        return "place and time"
    if s.startswith("place"):
        return "place"
    if s.startswith("time"):
        return "time"
    return s or "other"


def segment_tree(source: dict, root) -> list[tuple[Passage, object]]:
    """Returns (Passage, element) pairs; elements are kept for coverage tests."""
    sid = source["id"]
    text = root.find(f".//{TEI}text")
    out: list[tuple[Passage, object]] = []
    state = {"page": None}
    herb_slugs = SlugRegistry()
    counters: dict[str, int] = {}
    herb_ordinal = [0]

    def nxt(prefix: str) -> int:
        counters[prefix] = counters.get(prefix, 0) + 1
        return counters[prefix] - 1

    def emit_block(el, ctx: dict):
        notes: list = []
        clean = render(el, notes)
        btype = "heading" if local(el) == "head" else ("front_matter" if ctx["part"] == "front_matter" else
                                                        "index" if ctx["part"] == "index" else "body")
        prefix = f"{sid}:{ctx['part']}:{ctx.get('slug') or '_'}"
        k = nxt(prefix)
        pid = f"{prefix}:{k:03d}"
        scope = ctx["part"] in ("herbal", "directions") and btype == "body"
        p = Passage(
            passage_id=pid, source_id=sid, part=ctx["part"], passage_type=btype,
            line_start=el.sourceline or 0, line_end=(el.sourceline or 0) + source_xml(el).count("\n"),
            text_original=source_xml(el), section=ctx.get("section"), page=state["page"],
            entry_title=ctx.get("entry"), entry_slug=ctx.get("slug"), entry_ordinal=ctx.get("ordinal"),
            subsection=ctx.get("subsection") if btype == "body" else None, block_index=k,
            recipe_scope=scope, scope_reason="" if scope else f"{ctx['part']} {btype}",
            text_clean=clean, cleaning_ops=_ops(el, notes),
        )
        out.append((p, el))
        for n in notes:
            nk = nxt(prefix + ":note")
            npid = f"{prefix}:note{nk:02d}"
            nclean = render(n)
            out.append((Passage(
                passage_id=npid, source_id=sid, part=ctx["part"], passage_type="marginal_note",
                line_start=n.sourceline or 0, line_end=(n.sourceline or 0) + source_xml(n).count("\n"),
                text_original=source_xml(n), page=state["page"], entry_title=ctx.get("entry"),
                entry_slug=ctx.get("slug"), entry_ordinal=ctx.get("ordinal"), block_index=nk,
                recipe_scope=False, scope_reason="printed marginal note (index gloss)", footnote_of=[pid],
                text_clean=nclean, cleaning_ops=_ops(n, []),
            ), n))
            p.footnote_refs.append(npid)

    def walk(el, ctx: dict):
        for c in el:
            if not isinstance(c.tag, str):
                continue
            tag = local(c)
            if tag == "pb":
                state["page"] = c.get("n") or c.get("facs")
            elif tag == "teiHeader":
                continue
            elif tag in ("front",):
                walk(c, {**ctx, "part": "front_matter"})
            elif tag == "floatingText":
                walk(c, {**ctx, "part": "front_matter", "slug": f"letter{nxt('letters')}"})
            elif tag == "div":
                walk(c, div_ctx(c, ctx))
            elif tag == "list":
                walk(c, ctx)
            elif tag in BLOCKS or tag == "gap":  # a gap outside any block is kept as its own passage
                emit_block(c, ctx)
            elif tag == "note":  # a note outside any block: its own passage, unlinked
                prefix = f"{sid}:{ctx['part']}:{ctx.get('slug') or '_'}"
                nk = nxt(prefix + ":note")
                out.append((Passage(
                    passage_id=f"{prefix}:note{nk:02d}", source_id=sid, part=ctx["part"], passage_type="marginal_note",
                    line_start=c.sourceline or 0, line_end=(c.sourceline or 0) + source_xml(c).count("\n"),
                    text_original=source_xml(c), page=state["page"], entry_title=ctx.get("entry"),
                    entry_slug=ctx.get("slug"), entry_ordinal=ctx.get("ordinal"), block_index=nk, recipe_scope=False,
                    scope_reason="printed marginal note (index gloss)", text_clean=render(c), cleaning_ops=_ops(c, []),
                ), c))
            elif c.text and c.text.strip():  # unknown element carrying text: keep it as its own block
                emit_block(c, ctx)
            else:
                walk(c, ctx)

    def div_ctx(d, ctx: dict) -> dict:
        typ = d.get("type")
        head = d.find(f"{TEI}head")
        head_text = render(head) if head is not None else ""
        if typ == "herb":
            herb_ordinal[0] += 1
            name = herb_name(head_text)
            slug = herb_slugs.claim(slugify(name) if re.search(r"[A-Za-z]", name) else f"herb{herb_ordinal[0]:03d}")
            return {**ctx, "part": "herbal", "entry": head_text, "slug": slug, "ordinal": herb_ordinal[0],
                    "subsection": "intro"}
        if typ == "part" and ctx.get("part") == "herbal":
            return {**ctx, "subsection": canonical_part(head_text)}
        if typ in ("section", "chapter", "table_of_contents"):
            slug = f"{typ}{nxt('dir-' + typ):02d}"
            return {**ctx, "part": "directions", "entry": head_text, "slug": slug, "section": head_text[:80],
                    "subsection": None}
        if typ == "index":
            return {**ctx, "part": "index", "slug": "index", "entry": head_text}
        return ctx

    walk(text, {"part": "front_matter"})
    return out


def _ops(el, notes) -> list[str]:
    ops = ["tei_render", "unwrap"]
    if el.find(f".//{TEI}g[@ref='char:EOLhyphen']") is not None or el.find(f".//{TEI}g[@ref='char:EOLunhyphen']") is not None:
        ops.append("eol_join")
    if el.find(f".//{TEI}gap") is not None:
        ops.append("gap_marker")
    if notes:
        ops.append("note_extracted")
    return ops


def parse(path):
    return etree.parse(str(path), etree.XMLParser(remove_blank_text=False, huge_tree=True, resolve_entities=False, no_network=True, load_dtd=False)).getroot()


def segment(source: dict, path) -> list[Passage]:
    return [p for p, _ in segment_tree(source, parse(path))]
