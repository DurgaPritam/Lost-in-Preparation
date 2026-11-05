"""Phase 1 ingest tests.

Expected values for the hand-picked entries were read by eye from the raw Gutenberg files
(line numbers refer to the files whose SHA-256 is pinned in data/raw/manifest.json),
not copied from the segmenter's output.
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd
import pytest

from contract.models import Source
from lip.ingest import build, read_lines
from lip.paths import ROOT, SITE_DATA, load_sources
from lip.segment.common import gutenberg_bounds


@pytest.fixture(scope="session")
def sources():
    return load_sources()


@pytest.fixture(scope="session")
def df(sources):
    return build(sources)


def entry(df, prefix):
    rows = df[df.passage_id.str.startswith(prefix + ":")].sort_values("block_index")
    assert len(rows), f"no passages for {prefix}"
    return rows


# --- 10 hand-picked entries ---------------------------------------------------------------

CULPEPER = [
    # (entry prefix, heading, n body paragraphs, subsection sequence, first words of last body)
    ("culpeper-1850:herbal:amara-dulcis", "AMARA DULCIS.", 7,
     ["intro", "descript", "place", "time", "government and virtues", "government and virtues",
      "government and virtues"], "They that think"),
    ("culpeper-1850:herbal:all-heal", "ALL-HEAL.", 5,
     ["intro", "descript", "place", "time", "government and virtues"], "_Government and virtues._]"),
    ("culpeper-1850:herbal:kidneywort-or-wall-pennyroyal-or-wall-pennywort",
     "KIDNEYWORT, OR WALL PENNYROYAL, OR WALL PENNYWORT.", 4,
     ["descript", "place", "time", "government and virtues"], "_Government and virtues._] Venus"),
    ("culpeper-1850:herbal:henbane", "HENBANE.", 5,
     ["descript", "place", "time", "government and virtues", "government and virtues"],
     "Take notice, that this herb must never be taken inwardly"),
    # ONE BLADE is printed twice in the 1850 edition (lines 2345 and 9184): second gets ~2
    ("culpeper-1850:herbal:one-blade~2", "ONE BLADE.", 4,
     ["descript", "place", "time", "government and virtues"], "_Government and virtues._] It is a precious herb"),
]


@pytest.mark.parametrize("prefix,heading,n_body,subs,last_start", CULPEPER, ids=[c[0].rsplit(":", 1)[1] for c in CULPEPER])
def test_culpeper_entries(df, prefix, heading, n_body, subs, last_start):
    rows = entry(df, prefix)
    head = rows.iloc[0]
    assert head.passage_type == "heading" and head.block_index == 0
    assert re.sub(r"\s+", " ", head.text_original.strip()) == heading
    body = rows[rows.passage_type == "body"]
    assert len(body) == n_body
    assert body.subsection.tolist() == subs
    assert body.iloc[-1].text_original.startswith(last_start)
    assert body.recipe_scope.all()


def test_culpeper_two_line_heading_location(df):
    head = df[df.passage_id == "culpeper-1850:herbal:parsley-piert-or-parsley-break-stone:000"].iloc[0]
    assert (head.line_start, head.line_end) == (9353, 9354)
    nxt = df[df.passage_id == "culpeper-1850:herbal:parsley-piert-or-parsley-break-stone:001"].iloc[0]
    assert nxt.subsection == "descript" and nxt.line_start == 9356


PLINY = [
    # (entry prefix, source, book, chapter, chapter_alt, title, n body, first words of first body, footnote refs)
    ("pliny-nh:b20:c002", "pliny-nh-bohn-v4", 20, "2", "1", "THE WILD CUCUMBER; TWENTY-SIX REMEDIES.", 2,
     "We have already stated", [f"pliny-nh-bohn-v4:fn{n}" for n in range(1296, 1305)]),
    # irregular heading "CHAP 75." (no period after CHAP); paragraph starts with an anchor
    ("pliny-nh:b20:c075", "pliny-nh-bohn-v4", 20, "75", None, "SACOPENIUM, OR SAGAPENON: THIRTEEN REMEDIES.", 2,
     "The sacopenium which grows in Italy", ["pliny-nh-bohn-v4:fn1639", "pliny-nh-bohn-v4:fn1640"]),
    # irregular heading "CHAP. 62—" (no period before the dash)
    ("pliny-nh:b21:c062", "pliny-nh-bohn-v4", 21, "62", None, "THE PERDICIUM. THE ORNITHOGALE.", 1,
     "It is not in Egypt only", [f"pliny-nh-bohn-v4:fn{n}" for n in range(2243, 2247)]),
    # heading wrapped over two lines; book XXIV is the first book in volume 5
    ("pliny-nh:b24:c001", "pliny-nh-bohn-v5", 24, "1", "1",
     "THE ANTIPATHIES AND SYMPATHIES WHICH EXIST AMONG TREES AND PLANTS.", None,
     "Not even are the forests", None),
]


@pytest.mark.parametrize("prefix,sid,book,chap,alt,title,n_body,first,refs", PLINY, ids=[p[0] for p in PLINY])
def test_pliny_chapters(df, prefix, sid, book, chap, alt, title, n_body, first, refs):
    rows = entry(df, prefix)
    head = rows.iloc[0]
    assert head.passage_type == "heading" and head.source_id == sid
    got = tuple(None if pd.isna(v) else v for v in (head.book, head.chapter, head.chapter_alt, head.entry_title))
    assert got == (book, chap, alt, title)
    body = rows[rows.passage_type == "body"]
    if n_body is not None:
        assert len(body) == n_body
    assert body.iloc[0].text_clean.startswith(first)
    if refs is not None:
        assert [r for lst in body.footnote_refs for r in lst] == refs
    assert body.recipe_scope.all()


def test_footnote_links_back(df):
    fn = df[df.passage_id == "pliny-nh-bohn-v4:fn1291"].iloc[0]
    assert fn.passage_type == "footnote" and not fn.recipe_scope
    assert fn.text_original.startswith("[1291] Fée remarks")
    assert list(fn.footnote_of) == ["pliny-nh:b20:c001:001"]


# --- no passage lost ----------------------------------------------------------------------

GUTENBERG = ["culpeper-1850", "pliny-nh-bohn-v4", "pliny-nh-bohn-v5"]


def by_id(sources, sid):
    return next(s for s in sources if s["id"] == sid)


@pytest.mark.parametrize("sid", GUTENBERG)
def test_no_passage_lost(df, sources, sid):
    src = by_id(sources, sid)
    lines = read_lines(ROOT / src["raw_path"])
    lo, hi = gutenberg_bounds(lines)
    expected = {i + 1 for i in range(lo + 1, hi) if lines[i].strip()}
    d = df[df.source_id == src["id"]]
    covered: list[int] = []
    for p in d.itertuples():
        span = [n for n in range(p.line_start, p.line_end + 1) if lines[n - 1].strip()]
        covered.extend(span)
        assert p.text_original == "\n".join(lines[p.line_start - 1 : p.line_end])
    assert len(covered) == len(set(covered)), "a line belongs to two passages"
    assert set(covered) == expected, "lines lost or invented"


def test_cleaning_never_changes_content(df):
    """Cleaned text == original minus whitespace, italics markers and footnote anchors."""
    def norm(s, anchors):
        s = unicodedata.normalize("NFC", s)
        if anchors:
            s = re.sub(r"\[\d+\]", "", s)
        return re.sub(r"\s+|_", "", s)

    for p in df[df.source_id.isin(GUTENBERG)].itertuples():  # TEI rendering is tested in test_tei.py
        anchors = p.source_id.startswith("pliny")
        assert re.sub(r"\s", "", p.text_clean) == norm(p.text_original, anchors), p.passage_id


# --- stability ----------------------------------------------------------------------------

def test_ids_stable_across_runs(df, sources):
    again = build(sources)
    pd.testing.assert_series_equal(df.passage_id, again.passage_id)
    pd.testing.assert_series_equal(df.sha256_original, again.sha256_original)


def test_ids_unique_and_well_formed(df):
    assert df.passage_id.is_unique
    assert df.passage_id.str.match(r"^[a-z0-9-]+:[A-Za-z0-9:~_-]+$").all()


# --- structure checks against independent evidence ------------------------------------------

@pytest.mark.parametrize("sid", ["pliny-nh-bohn-v4", "pliny-nh-bohn-v5"])
def test_pliny_chapter_counts_match_printed_contents(df, sources, sid):
    src = by_id(sources, sid)
    lines = read_lines(ROOT / src["raw_path"])
    s = lines.index("CONTENTS")
    e = next(i for i, l in enumerate(lines) if re.match(r"^NATURAL HISTORY OF PLINY\.?$", l))
    roman, last = None, {}
    for line in lines[s:e]:
        if m := re.match(r"^\s*BOOK ([XVIL]+)\.$", line):
            roman = m.group(1)
        elif (m := re.match(r"^\s{1,4}(\d+)\.\s", line)) and roman:
            last[roman] = int(m.group(1))
    from lip.segment.pliny import roman_to_int
    d = df[(df.source_id == src["id"]) & (df.part == "body") & df.chapter.notna()]
    got = d.groupby("book").chapter.apply(lambda c: sorted({int(x) for x in c}))
    for r, n in last.items():
        assert got[roman_to_int(r)] == list(range(1, n + 1)), r


def test_footnotes_resolve(df):
    ids = set(df.passage_id)
    refs = {r for lst in df.footnote_refs for r in lst}
    assert refs <= ids
    fn = df[df.passage_type == "footnote"]
    assert (fn.footnote_of.map(len) > 0).all()


def test_recipe_scope_rules(df):
    pl = df[df.source_id.str.startswith("pliny")]
    assert not pl[pl.recipe_scope & ~pl.book.isin(range(20, 28))].shape[0]
    assert not df[df.recipe_scope & (df.passage_type != "body")].shape[0]
    assert (df[~df.recipe_scope].scope_reason != "").all()


def test_sources_json_matches_contract(sources):
    import json
    data = json.loads((SITE_DATA / "sources.json").read_text())
    assert [Source(**r).id for r in data] == [s["id"] for s in sources]
