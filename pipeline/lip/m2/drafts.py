"""AI-drafted, UNVERIFIED candidate identifications for the 30-name evaluation list.

basis = "ai_drafted_unverified". For each name, a candidate is drafted ONLY from a source fetched
in the pipeline run, and the quoted line is re-checked against the fetched text every time this
module runs. Bostock & Riley's footnotes are excluded (they are an M2 input).
Sources used:
  - Lewis & Short, A Latin Dictionary (1879), TEI XML from the PerseusDL lexica repository
    (CC BY-SA 4.0): lat.ls.perseus-eng1.xml
  - English Wikipedia article wikitext (CC BY-SA 4.0), fetched with action=raw
NOT INDEPENDENT MODERN SCHOLARSHIP: Lewis & Short (1879) is a 19th-century dictionary whose plant
identifications partly rest on the same older commentators (e.g. Fée, Sprengel) that informed the
system's Bostock & Riley footnotes, and Wikipedia is a tertiary, editable source. The drafts therefore
stay `ai_drafted_unverified` until a person checks them against modern scholarly identifications.
Drafts are written to separate `draft*` columns of data/gold/name_identifications.csv. The human
columns (scholarlyAcceptedName, citation, annotator) and `verified_by` stay empty for a person.
`lip m2 eval` reports draft agreement only as PROVISIONAL (metrics.provisional), never as gold.
"""
from __future__ import annotations

import re

import pandas as pd

from ..http import get_text
from .services import wfo_resolve

BASIS = "ai_drafted_unverified"
CAVEAT = ("Lewis & Short (1879) and Wikipedia are not independent modern scholarly sources (L&S may share older commentators "
          "with the system's inputs; Wikipedia is tertiary); this draft stays unverified until checked by a person.")
LS_URL = "https://raw.githubusercontent.com/PerseusDL/lexica/master/CTS_XML_TEI/perseus/pdllex/lat/ls/lat.ls.perseus-eng1.xml"
WP_RAW = "https://en.wikipedia.org/w/index.php?title={t}&action=raw"
WP_PAGE = "https://en.wikipedia.org/wiki/{t}"

# (nameAsWritten, source, locator, quote, binomial in source or None, note)
DRAFTS = [
    ("Dovesfoot, or Cranesbill", "wp", "Geranium_molle", "Nicholas Culpeper in his herbal of 1652 suggested a variety of uses for G. molle", "Geranium molle", ""),
    ("Flixweed", "wp", "Descurainia_sophia", "Common names include flixweed, herb-Sophia and tansy mustard.", "Descurainia sophia", ""),
    ("The Melancholly Thistle", "wp", "Cirsium_heterophyllum", "Cirsium heterophyllum, the melancholy thistle, is an erect spineless herbaceous perennial", "Cirsium heterophyllum", ""),
    ("Henbane", "wp", "Hyoscyamus_niger", "Henbane (Hyoscyamus niger, also black henbane and stinking nightshade) is a poisonous plant", "Hyoscyamus niger", ""),
    ("Maidenhair", None, None, None, None, "Not drafted: the sources read do not tie Culpeper's 'Maidenhair' to one species (maidenhair spleenwort, Asplenium trichomanes, vs maidenhair fern, Adiantum)."),
    ("Vipers Buglofs", "wp", "Echium_vulgare", "Echium vulgare, known as viper's bugloss and blueweed, is a species of flowering plant", "Echium vulgare", ""),
    ("Calamint, or Mountain Mint", None, None, None, None, "Not drafted: the sources read name several calamints (lesser, wood) but none as 'mountain mint'."),
    ("Dill", "wp", "Dill", "Dill (Anethum graveolens) is an annual herb in the celery family Apiaceae.", "Anethum graveolens", ""),
    ("Garden Bazil, OR Sweet Bazil", "wp", "Basil", "Basil (Ocimum basilicum), also called great basil, is a culinary herb", "Ocimum basilicum", ""),
    ("Bishops-weed", None, None, None, None, "Not drafted: the source read calls Ammi majus 'false bishop's weed', which implies a different 'true' bishop's weed."),
    ("Woodbind, or Honeysuckles", "wp", "Lonicera_periclymenum", "Lonicera periclymenum, common names honeysuckle, common honeysuckle, European honeysuckle, or woodbine,", "Lonicera periclymenum", ""),
    ("Ground Pine, or Chamepitys", "wp", "Ajuga_chamaepitys", "Popularly known as yellow bugle, Chian bugle or ground-pine,", "Ajuga chamaepitys", ""),
    ("Wheat", "wp", "Common_wheat", "Common wheat (Triticum aestivum), also known as bread wheat, is a cultivated wheat species.", "Triticum aestivum",
     "Culpeper's 'Wheat' may refer to several Triticum species; drafted as common wheat."),
    ("Beans", "wp", "Vicia_faba", "Vicia faba, commonly known as the broad bean, fava bean, or faba bean,", "Vicia faba", "Assumes Culpeper's garden 'Beans' are broad beans."),
    ("Houndstongue", "wp", "Cynoglossum_officinale", "Cynoglossum officinale (houndstongue, houndstooth, dog's tongue, gypsy flower,", "Cynoglossum officinale", ""),
    ("GREAT HONOUR IN WHICH CHAPLETS WERE HELD BY THE ANCIENTS", None, None, None, None, "Not a plant name (chapter title)."),
    ("SARCOCOLLA", "wp", "Astragalus_sarcocolla", "also known as Persian gum, is a shrub or tree from Persia historically famed for its balsam", "Astragalus sarcocolla",
     "Lewis & Short gives only 'a Persian gum'; the species comes from the Wikipedia article."),
    ("PHALARIS", "ls", "phalaris", "The plant canarygrass (Phalaris canariensis, Linn.), Plin. 27, 12, 102", "Phalaris canariensis", ""),
    ("ACORNS", None, None, None, None, "Not drafted: genus-level (Quercus); Lewis & Short 'glans' gives no species."),
    ("HORMINUM", "ls", "horminum", "the herb clary, a kind of sage, Salvia horminum, Linn.", "Salvia horminum", ""),
    ("APARINE, OMPHALOCARPOS, OR PHILANTHROPOS", "ls", "aparine", "a plant, cleavers: Galium aparine, Linn.", "Galium aparine", ""),
    ("PLANT CALLED IMPIA", "ls", "impius", "impia herba, a plant, perh. the French everlasting, Gnaphalium Gallicum", "Gnaphalium gallicum", "Hedged in the source ('perh.')."),
    ("BECHION, OTHERWISE KNOWN AS ARCION, CHAMÆLEUCE OR TUSSILAGO", "ls", "bechion", "a plant good for a cough, colt'sfoot: Tussilago farfara, Linn.", "Tussilago farfara", ""),
    ("NYMA", "ls", "nyma", "nyma, ae, f., a plant, otherwise unknown", None, "Source states the plant is otherwise unknown; not scorable."),
    ("INGUINALIS OR ARGEMO", None, None, None, None, "Not drafted: Lewis & Short 'inguinalis' and 'argemon' give no species."),
    ("BALLOTES, MELAMPRASION, OR BLACK LEEK", "ls", "ballote", "a plant, also called porrum nigrum, black horehound: Ballota nigra, Linn.", "Ballota nigra", ""),
    ("LIMONION, OR NEUROIDES", "ls", "limonion", "the wild beet, Plin. 20, 8, 28", None, "Source gives 'the wild beet' with no species; not drafted to species."),
    ("OATS", "ls", "avena", "Oats; and specif., common oats, Gr. bro/mos: Avena sativa, Linn.", "Avena sativa", ""),
    ("MELILOTE, OTHERWISE KNOWN AS CAMPANIAN GARLAND", "ls", "melilotos", "a kind of clover, melilot, also called sertula Campana", None, "Genus-level only (Melilotus); no species in source."),
    ("BULBS", None, None, None, None, "Not drafted: generic term (bulbs / onions) in Lewis & Short."),
]


def _wp_plain(w: str) -> str:
    w = re.sub(r"<ref[^>]*/>", "", w)
    w = re.sub(r"<ref[^>]*>.*?</ref>", "", w, flags=re.S)
    for _ in range(3):
        w = re.sub(r"\{\{[^{}]*\}\}", "", w)
    w = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", w).replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", w))


def _ls_entries() -> tuple[dict[str, str], str]:
    xml, sha, _ = get_text("sources", LS_URL)
    out = {}
    for e in re.split(r"(?=<entryFree )", xml):
        m = re.match(r'<entryFree[^>]*key="([^"]+)"', e)
        if m:
            key = re.sub(r"\d", "", m.group(1)).lower()
            out.setdefault(key, "")
            out[key] += " " + re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", e))
    return out, sha


def build(eval_path) -> pd.DataFrame:
    df = pd.read_csv(eval_path, dtype=str).fillna("")
    by_name = {d[0]: d for d in DRAFTS}
    missing = set(df.nameAsWritten) - set(by_name)
    if missing:
        raise ValueError(f"no draft decision for: {sorted(missing)}")
    ls, ls_sha = _ls_entries()
    cols = {c: [] for c in ("draftSourceName", "draftAcceptedName", "draftWfoId", "draftSource", "draftSourceUrl",
                            "draftSourceSection", "draftQuote", "draftSourceSha256", "draftNote", "draftCaveat", "draftBasis", "verified_by")}
    for r in df.itertuples():
        _, src, loc, quote, binom, note = by_name[r.nameAsWritten]
        url = section = sha = ""
        if src == "wp":
            text, sha, _ = get_text("sources", WP_RAW.format(t=loc))
            url, section, hay = WP_PAGE.format(t=loc), f"Wikipedia article '{loc.replace('_', ' ')}' (wikitext, action=raw)", _wp_plain(text)
            srcname = "English Wikipedia (CC BY-SA 4.0)"
        elif src == "ls":
            url, section, hay, sha = LS_URL, f"Lewis & Short, entry '{loc}'", ls.get(loc, ""), ls_sha
            srcname = "Lewis & Short, A Latin Dictionary (1879), PerseusDL TEI (CC BY-SA 4.0)"
        else:
            srcname, hay = "", ""
        if quote and quote not in hay:
            raise ValueError(f"quote not found in fetched source for {r.nameAsWritten!r}: {quote!r}")
        acc = wfo_resolve(binom) if binom else None
        for k, v in (("draftSourceName", binom or ""), ("draftAcceptedName", (acc or {}).get("acceptedName", "")),
                     ("draftWfoId", (acc or {}).get("wfoId", "")), ("draftSource", srcname), ("draftSourceUrl", url),
                     ("draftSourceSection", section), ("draftQuote", quote or ""), ("draftSourceSha256", sha),
                     ("draftNote", note), ("draftCaveat", CAVEAT if src else ""), ("draftBasis", BASIS), ("verified_by", "")):
            cols[k].append(v)
    for k, v in cols.items():
        df[k] = v
    df.to_csv(eval_path, index=False)
    return df
