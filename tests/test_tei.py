"""Culpeper 1652 (EEBO-TCP A35365) ingest and the 1850↔1652 crosswalk."""
from __future__ import annotations

import pandas as pd
import pytest

from lip.paths import INTERIM, ROOT
from lip.segment import crosswalk, tei

SRC = {"id": "culpeper-1652"}


@pytest.fixture(scope="module")
def tree():
    root = tei.parse(ROOT / "data/raw/tcp/A35365.xml")
    return root, tei.segment_tree(SRC, root)


@pytest.fixture(scope="module")
def df():
    d = pd.read_parquet(INTERIM / "passages.parquet")
    return d[d.source_id == "culpeper-1652"].set_index("passage_id")


def test_no_text_lost(tree):
    """Every non-whitespace text node inside <text> belongs to exactly one passage."""
    root, pairs = tree
    roots = {id(e) for _, e in pairs}
    assert len(roots) == len(pairs)

    def owner(e):
        while e is not None and id(e) not in roots:
            e = e.getparent()
        return e

    text = root.find(f".//{tei.TEI}text")
    for e in text.iter():
        if not isinstance(e.tag, str):
            continue
        if e.text and e.text.strip() and tei.local(e) not in ("desc",):
            assert owner(e) is not None, (e.tag, e.text[:60])
        if e.tail and e.tail.strip() and e is not text:
            assert owner(e.getparent()) is not None, (e.tag, e.tail[:60])


def test_every_gap_has_a_visible_marker(tree, df):
    root, _ = tree
    n_gaps = len(root.findall(f".//{tei.TEI}text//{tei.TEI}gap"))
    assert n_gaps == 301
    assert int(df.gap_count.sum()) == n_gaps


def test_eol_hyphens_joined_and_notes_extracted(df):
    v = df.loc["culpeper-1652:herbal:adders-tongue:008"]
    assert v.subsection == "vertues and use"
    assert "given with good success unto those who are troubled with Casting, Vomiting," in v.text_clean
    assert "Inflamations in Wounds" not in v.text_clean  # marginal note removed from running text
    note = df.loc[v.footnote_refs[0]]
    assert note.passage_type == "marginal_note" and list(note.footnote_of) == ["culpeper-1652:herbal:adders-tongue:008"]
    assert note.text_clean.startswith("Wounds in the Breast")


def test_structure_counts(df):
    heads = df[(df.part == "herbal") & (df.passage_type == "heading") & (df.block_index == 0)]
    assert heads.entry_slug.nunique() == 282
    assert "herb045" in set(heads.entry_slug)  # glyph-only heading gets an ordinal slug
    virt = df[(df.part == "herbal") & (df.subsection == "vertues and use") & (df.passage_type == "body")]
    assert len(virt) > 500
    assert not df[(df.part == "herbal") & (df.passage_type == "body")].subsection.str.contains("♄|♀|discr").any()


@pytest.mark.parametrize("raw,canon", [("Vertues and Vse.", "vertues and use"), ("The Vertues.", "vertues and use"),
                                       ("♄ Discription.", "description"), ("Place and Time.", "place and time")])
def test_canonical_part(raw, canon):
    assert tei.canonical_part(raw) == canon


def test_gap_marker_format():
    assert tei.GAP_MARK.format("??") == "⟦??⟧"


# --- crosswalk ----------------------------------------------------------------------------

def test_key_normalises_early_modern_spelling():
    assert crosswalk.key("VVood-Sage.") == crosswalk.key("WOOD-SAGE.")
    assert crosswalk.key("Lettice") == crosswalk.key("LETTUCE") or crosswalk.score("LETTUCE.", "☽ ♋ Lettice.") >= 0.75


@pytest.fixture(scope="module")
def cw():
    return pd.read_csv(INTERIM / "culpeper_1850_1652_crosswalk.csv").set_index("heading_1850")


@pytest.mark.parametrize("h1850,h1652", [
    ("ALEHOOF, OR GROUND-IVY.", "Alehoof, or Ground-Ivy."),
    ("AGRIMONY.", "Agrimony. ♃"),
    ("BORAGE AND BUGLOSS.", "♃ ♌ Borrage & Bugloss."),
    ("CAMOMILE.", "☉ Chamomel."),
    ("THE WILLOW TREE.", "The VVillow-tree."),
    ("SAUCE-ALONE, OR JACK-BY-THE-HEDGE-SIDE.", "Sawce alone, or Jack by the Hedg."),
])
def test_known_pairs_match(cw, h1850, h1652):
    row = cw.loc[h1850]
    assert row.heading_1652 == h1652 and row.status in ("in_1652", "probable_1652")


@pytest.mark.parametrize("h1850", ["AMARA DULCIS.", "ALKANET.", "CARDUUS BENEDICTUS.", "ALL-HEAL."])
def test_headings_absent_from_1652_are_flagged(cw, h1850):
    assert cw.loc[h1850].status == "later_addition_candidate"


def test_flag_only_on_1850_herbal(cw):
    d = pd.read_parquet(INTERIM / "passages.parquet")
    flagged = d[d.addition_status.notna()]
    assert set(flagged.source_id) == {"culpeper-1850"} and set(flagged.part) == {"herbal"}
