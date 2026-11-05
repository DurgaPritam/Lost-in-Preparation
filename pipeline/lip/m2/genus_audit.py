"""Audit of the classical-genus signal (M2 v2): false friends between a classical word and a modern genus.

The signal boosts candidates in a modern genus whose name matches a word of the historical name.
That fails when the word means something else in classical usage (Pliny's *laser* is the juice of
silphium, not the modern genus *Laser*), when an English word happens to spell-match a genus
(Culpeper's "Cotton Thistle" -> *Cotinus*), or when the "name" is a chapter title.

Screen (mechanical, every run): all top-1 resolutions whose evidence includes a classical-genus match,
each checked against the Lewis & Short entry for the token (PerseusDL TEI, CC BY-SA 4.0).
Findings (reviewed by an AI, basis ai_drafted_unverified): listed in FINDINGS with the Lewis & Short
sentence that shows the classical meaning, re-checked verbatim against the fetched dictionary.
Every listed resolution is marked `disputed` by m2/resolve.py (reason `genus_signal_false_friend`);
nothing is deleted, so a person can overturn a finding.
"""
from __future__ import annotations

import json
import re
import unicodedata

import pandas as pd

from ..paths import INTERIM, ROOT

OUT_CSV = INTERIM / "m2" / "genus_signal_audit.csv"
OUT_MD = ROOT / "docs" / "GENUS_SIGNAL_AUDIT.md"
BASIS = "ai_drafted_unverified"

# (nameId, finding, reason in our words, Lewis & Short key or None, verbatim L&S fragment or None)
FINDINGS: list[tuple] = [
    ("culpeper-1652:down-or-cottonthistle", "english_word_spelling_match",
     "the English word 'cotton' was spelling-matched to Cotinus (smoke tree); a cotton thistle is not a Cotinus", None, None),
    ("culpeper-1652:the-woolley-or-cotton-thistle", "english_word_spelling_match",
     "the English word 'cotton' was spelling-matched to Cotinus (smoke tree); a cotton thistle is not a Cotinus", None, None),
    ("pliny-nh:b22:c049:n0", "classical_meaning_differs",
     "classical laser is the juice of silphium/laserpitium, not the modern genus Laser", "laser",
     "the juice of the plant laserpitium, assafœtida"),
    ("pliny-nh:b22:c048:n0", "classical_meaning_differs",
     "classical silphium is the plant also called laserpitium, not the modern genus Silphium", "silphium",
     "a plant, called in pure Latin laserpitium"),
    ("pliny-nh:b22:c020:n0", "classical_meaning_differs",
     "classical parthenium names several plants; the modern genus Parthenium is not among those Lewis & Short gives", "parthenium",
     "the name of several plants"),
    ("pliny-nh:b24:c053:n0", "classical_meaning_differs",
     "classical rhododendron is the oleander (rosebay), not the modern genus Rhododendron", "rhododendros",
     "the rosebay, oleander"),
    ("pliny-nh:b25:c101:n0", "classical_meaning_differs",
     "classical cotyledon is navelwort (Linnaeus' Cotyledon umbilicus), not the modern genus Cotyledon (here C. orbiculata)",
     "cotyledon", "a plant, navelwort: Cotyledon umbilicus, Linn."),
    ("pliny-nh:b24:c049:n3", "classical_meaning_differs",
     "classical clematis names various climbing plants, e.g. Vinca minor; not specifically the modern genus Clematis", "clematis",
     "the name of various climbing plants, as Vinca minor, Linn., etc."),
    ("pliny-nh:b25:c008:n0", "classical_meaning_differs",
     "classical moly is a legendary or unidentified plant; not specifically Allium", "moly",
     "A plant with a white flower and a black root"),
    ("pliny-nh:b20:c066:n0", "classical_meaning_differs",
     "classical siliquastrum is a pepperwort (also called piperitis), not the Judas tree Cercis siliquastrum", "siliquastrum",
     "a plant, also called piperitis, pepperwort"),
    ("pliny-nh:b24:c101:n0", "classical_meaning_differs",
     "classical aproxis is an unidentified plant; the match to Muhlenbergia is a spelling coincidence", "aproxis",
     "a plant whose root, acc. to Pythagoras, takes fire at a distance"),
    ("pliny-nh:b20:c059:n0", "english_word_spelling_match",
     "the English word 'caper' was spelling-matched to Cyperus; classical capparis is the caper-bush", "capparis",
     "the caper-bush"),
    ("pliny-nh:b23:c046:n0", "spelling_match",
     "'Cyprus' was spelling-matched to Cyperus; in Lewis & Short, Cyprus is the island, and the plant meaning was not verified",
     "cyprus", "an island in the Mediterranean Sea"),
    ("pliny-nh:b21:c038:n5", "spelling_match",
     "'Melanion' was spelling-matched to the epithet of Cuphea melanium; no Lewis & Short entry, classical meaning not verified", None, None),
    ("pliny-nh:b21:c009:n0", "not_a_plant_name", "chapter title (an anecdote about Cleopatra), not a plant name", None, None),
    ("pliny-nh:b22:c006:n0", "not_a_plant_name", "chapter title ('centurion'), not a plant name", None, None),
    ("pliny-nh:b21:c050:n0", "english_word_spelling_match",
     "the English word 'broom' (butcher's broom) was spelling-matched to Bromus (a grass)", None, None),
    ("pliny-nh:b26:c017:n0", "classical_meaning_differs",
     "Pliny says bechion is also called salvia; Lewis & Short identifies bechion as coltsfoot, so the boost to Salvia is unsupported",
     "bechion", "a plant good for a cough, colt'sfoot: Tussilago farfara, Linn."),
    # already disputed for other reasons; listed so the reason is recorded
    ("pliny-nh:b22:c027:n0", "classical_meaning_differs", "classical lotos names several plants (water-lily, lotus-tree); not specifically the modern genus Lotus", "lotos", "The name of several plants"),
    ("pliny-nh:b24:c002:n0", "classical_meaning_differs", "classical lotos names several plants (water-lily, lotus-tree); not specifically the modern genus Lotus", "lotos", "The name of several plants"),
    ("pliny-nh:b24:c041:n0", "classical_meaning_differs", "classical myrice is the tamarisk, not the modern genus Myrica (bog myrtle)", "myrice", "the tamarisk, a kind of shrub"),
    ("pliny-nh:b21:c029:n1", "classical_meaning_differs", "classical casia is a cinnamon-like bark, not the modern legume genus Cassia", "casia", "A tree with an aromatic bark, similar to cinnamon"),
    ("pliny-nh:b26:c019:n1", "classical_meaning_differs", "Lewis & Short identifies classical amomum with a different plant (Linnaeus' Cissus vitiginea), not the modern genus Amomum", "amomum", "an aromatic shrub, from which the Romans prepared a costly, fragrant balsam"),
    ("pliny-nh:b24:c013:n0", "classical_meaning_differs", "galbanum is the resin of a Syrian umbellifer; the match to Laser trilobum is not supported", "galbanum", "the resinous sap of an umbelliferous plant in Syria"),
    ("pliny-nh:b27:c018:n0", "classical_meaning_differs", "classical asclepias is the swallowwort (Linnaeus' Asclepias vincetoxicum), not the American milkweed Asclepias syriaca", "asclepias", "the common swallowwort: Asclepias vincetoxicum, Linn."),
    ("pliny-nh:b21:c033:n2", "classical_meaning_differs", "classical helenium is perhaps elecampane, not the modern genus Helenium", "helenium", "a plant, perh. the elecampane"),
    ("pliny-nh:b20:c061:n0", "classical_meaning_differs", "classical cunila is a kind of origanum, not the modern genus Cunila", "cunila", "a plant, a species of origanum"),
    ("pliny-nh:b20:c062:n0", "classical_meaning_differs", "classical cunila is a kind of origanum, not the modern genus Cunila", "cunila", "a plant, a species of origanum"),
    ("pliny-nh:b20:c064:n0", "classical_meaning_differs", "classical cunila is a kind of origanum, not the modern genus Cunila", "cunila", "a plant, a species of origanum"),
    ("pliny-nh:b20:c065:n0", "classical_meaning_differs", "classical cunila is a kind of origanum, not the modern genus Cunila", "cunila", "a plant, a species of origanum"),
    ("pliny-nh:b20:c065:n1", "classical_meaning_differs", "classical cunila is a kind of origanum, not the modern genus Cunila", "cunila", "a plant, a species of origanum"),
    ("pliny-nh:b21:c016:n1", "classical_meaning_differs", "classical combretum is a kind of rush, not the modern genus Combretum", "combretum", "a kind of rush"),
]
FLAGGED_FOR_REVIEW = {
    "Moricandia arvensis": ("pliny-nh:b20:c036:n0", "pliny-nh-bohn-v4:fn1487",
                            "Resolved from Pliny's WILD CABBAGE (20.36) only, via a Bostock & Riley footnote naming 'Brassica arvensis' "
                            "(a synonym of Moricandia arvensis in GBIF). The same footnote reports Fée's view that Pliny merged the "
                            "descriptions of two different plants. DECISION (project lead, 2026-11-05): removed from the study set "
                            "(config/study_set_exclusions.csv); the name resolution itself is unchanged."),
}


class AuditError(ValueError):
    pass


def ids() -> set[str]:
    return {f[0] for f in FINDINGS}


def finding_of() -> dict[str, str]:
    return {f[0]: f[1] for f in FINDINGS}


def _plain(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def screen(cand: pd.DataFrame) -> pd.DataFrame:
    """Every top-1 resolution that used the classical-genus signal, with the Lewis & Short check."""
    from .drafts import _ls_entries
    ls, _ = _ls_entries()
    rows = []
    for r in cand[cand["rank"] == 1].itertuples():
        ev = json.loads(r.evidence)
        g = [x for x in ev if "classical genus match" in x["how"]]
        if not g:
            continue
        m = re.search(r"'([^']+)' -> (\w+)", g[0]["how"])
        tok, genus = m.group(1), m.group(2)
        key = "".join(c for c in unicodedata.normalize("NFD", tok.lower().replace("æ", "ae").replace("œ", "oe"))
                      if unicodedata.category(c) != "Mn")
        keys = [key] + ([key[:-2] + "um", key[:-2] + "os", key[:-2] + "e"] if key.endswith("on") else []) + \
               ([key[:-2] + "us"] if key.endswith("os") else [])
        ent = next((ls[k] for k in keys if k in ls), None)
        rows.append({"nameId": r.nameId, "source": r.source, "nameAsWritten": r.nameAsWritten, "token": tok, "matchedGenus": genus,
                     "acceptedName": r.acceptedName, "confidence": r.confidence, "exactWord": tok.lower() == genus.lower(),
                     "lewisShort": "no entry" if ent is None else ("mentions genus" if genus.lower() in ent.lower() else "does not mention genus")})
    return pd.DataFrame(rows)


def build(cand: pd.DataFrame) -> dict:
    from .drafts import _ls_entries
    ls, _ = _ls_entries()
    if len(ids()) != len(FINDINGS):
        raise AuditError("duplicate nameId in FINDINGS")
    known = set(cand.nameId)
    for nid, finding, reason, key, frag in FINDINGS:
        if nid not in known:
            raise AuditError(f"{nid} not in the name candidates")
        if key and _plain(frag) not in _plain(ls.get(key, "")):
            raise AuditError(f"Lewis & Short '{key}' does not contain {frag!r}")
    sc = screen(cand)
    top = cand[cand["rank"] == 1].set_index("nameId")
    f = pd.DataFrame([{"nameId": n, "nameAsWritten": top.loc[n, "nameAsWritten"], "source": top.loc[n, "source"],
                       "matchedSpecies": top.loc[n, "acceptedName"] or top.loc[n, "gbifSpecies"], "finding": fd, "reason": rs,
                       "lewisShortEntry": k or "", "lewisShortQuote": q or "", "basis": BASIS} for n, fd, rs, k, q in FINDINGS])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    f.to_csv(OUT_CSV, index=False)
    return {"screened": int(len(sc)), "screen": sc, "findings": f}


def write_md(res: dict, before_disputed: dict[str, bool]) -> str:
    sc, f = res["screen"], res["findings"]
    f = f.assign(wasDisputed=f.nameId.map(before_disputed).fillna(False))
    new = f[~f.wasDisputed]
    L = ["# Classical-genus signal audit", "",
         "Generated by `python -m lip m2 resolve` (`pipeline/lip/m2/genus_audit.py`); do not edit by hand. "
         f"Findings are AI-reviewed (`{BASIS}`) and await the project lead's check.", "",
         "## Why", "",
         "Name resolution v2 boosts candidates in a modern genus whose name matches a word of the historical name "
         "(e.g. 'MANDRAGORA' → *Mandragora*). That goes wrong when:",
         "- the word has a different classical meaning (Pliny's *laser* is the juice of silphium, not the modern genus *Laser*);",
         "- an English word spell-matches a genus (Culpeper's 'Cotton Thistle' → *Cotinus*);",
         "- the 'name' is a chapter title.", "",
         "## Screen", "",
         f"Every top-1 resolution whose evidence includes a classical-genus match was screened: **{len(sc)}** resolutions "
         f"({(sc.source == 'pliny').sum()} Pliny, {(sc.source != 'pliny').sum()} Culpeper). "
         f"In {int(sc.exactWord.sum())} of them the word equals the genus name; in the rest it is a variant or spelling match. "
         "Each word was looked up in Lewis & Short (PerseusDL TEI, CC BY-SA 4.0): "
         + ", ".join(f"{k} {v}" for k, v in sc.lewisShort.value_counts().items())
         + ". A dictionary entry that does not name the genus is only a prompt for review, since many entries give no Linnaean name.", "",
         f"## Findings ({len(f)} resolutions)", "",
         f"**{len(new)}** were previously undisputed and are now marked `disputed` (reason `genus_signal_false_friend`). "
         f"The other {len(f) - len(new)} were already disputed for other reasons; they are listed so the reason is on record. "
         "Nothing is deleted, so a reviewer can overturn a finding.", "",
         "| Name as written | Source | Matched species | Finding | Reason | Lewis & Short | Was disputed |", "|---|---|---|---|---|---|---|"]
    for r in f.sort_values(["wasDisputed", "source", "nameAsWritten"]).itertuples():
        q = f"*{r.lewisShortEntry}*: “{r.lewisShortQuote}”" if r.lewisShortQuote else "—"
        L.append(f"| {r.nameAsWritten} | {r.source} | *{r.matchedSpecies}* | `{r.finding}` | {r.reason} | {q} | {'yes' if r.wasDisputed else '**no → now disputed**'} |")
    L += ["", "## Flagged for review (not changed automatically)", ""]
    for sp, (nid, fn, note) in FLAGGED_FOR_REVIEW.items():
        L += [f"### *{sp}*", "", note, "", f"- Name entry: `{nid}`; footnote `{fn}`.",
              "- Passages: see `data/interim/m2/flagged_for_review.json` (verbatim text of the chapter and its footnotes).", ""]
    L += ["## Limits", "",
          "- Lewis & Short (1879) is a 19th-century dictionary and may share older commentators with the system's inputs.",
          "- The review covered every undisputed resolution in the screen, and the already-disputed ones whose dictionary entry "
          "showed a clear different meaning. Other disputed resolutions may contain further false friends; they are already excluded from attestation counts."]
    OUT_MD.write_text("\n".join(L) + "\n")
    return OUT_MD.read_text()


def flagged_passages() -> dict:
    p = pd.read_parquet(INTERIM / "passages.parquet")
    inv = pd.read_parquet(INTERIM / "m2" / "name_inventory.parquet")
    out = {}
    for sp, (nid, _, note) in FLAGGED_FOR_REVIEW.items():
        e = inv[inv.nameId == nid].iloc[0]
        book, chap = (x[1:] for x in e.entry.split(":"))
        ch = p[p.source_id.str.startswith("pliny") & (p.book.astype(str) == str(int(book))) & (p.chapter.astype(str) == str(int(chap)))]
        fns = [f["id"] for f in json.loads(e.footnotes)]
        out[sp] = {"nameId": nid, "nameAsWritten": e.nameAsWritten, "note": note,
                   "passages": [{"passageId": r.passage_id, "type": r.passage_type, "text": r.text_clean} for r in ch.itertuples()],
                   "footnotes": [{"passageId": r.passage_id, "text": r.text_clean} for r in p[p.passage_id.isin(fns)].itertuples()]}
    (INTERIM / "m2" / "flagged_for_review.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out
