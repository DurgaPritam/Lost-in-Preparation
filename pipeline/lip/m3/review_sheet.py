"""Study-set review sheet for the project lead: docs/STUDY_SET_REVIEW.csv + docs/STUDY_SET_REVIEW.md.

One row per proposed species. Every field is read from pipeline outputs; nothing is typed by hand:
  - names as written, per source, with the passage IDs of each name entry (M2 inventory + passages);
  - a description excerpt: Culpeper 1652's "Description" paragraphs (or, for Pliny-only species, the first body
    paragraph of the chapter), cut MECHANICALLY to its first sentences (no selection or paraphrase);
  - resolution basis, confidence, disputed and genus-level status of every name entry that resolves to the species
    (entries that count towards attestation and entries that do not);
  - links: Wikipedia article (checked to exist; redirects followed), GBIF species page (GBIF backbone match), WFO page;
  - recipes: recipe extraction (M1) has NOT been run on the corpus, so no recipe counts exist. Shown instead, as a
    labelled HEURISTIC proxy: the recipe-scope passages of the counted entries and how many of them mention each
    vehicle word (water / wine / vinegar / oil / honey);
  - compounds and coverage flag (M3); toxicity category and source (AI-drafted, unverified);
  - empty `decision` (approve / reject / unsure) and `reason` columns for the reviewer.
Rows most likely to be wrong come first: species with disputed name entries, then genus-level resolutions, then
the lowest confidence among counted entries, then the fewest counted entries.
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote

import pandas as pd

from ..http import get_text
from ..m2.services import gbif_match
from ..paths import INTERIM, ROOT

OUT_CSV = ROOT / "docs" / "STUDY_SET_REVIEW.csv"
OUT_MD = ROOT / "docs" / "STUDY_SET_REVIEW.md"
WP_RAW = "https://en.wikipedia.org/w/index.php?title={}&action=raw"
EXCERPT_CHARS = 320
VEHICLES = {"water": r"\bwater", "wine": r"\bwine", "vinegar": r"\bvinegar|\bvineger|\bacetum", "oil": r"\boyl|\boil\b|\boils\b",
            "honey": r"\bhon[ie]y|\bhoney|\bmel\b"}
PREP_WORDS = {"decoction": r"\bdecoct\w*|\bboil(?:ed|ing)?\b", "distilled_water": r"\bdistill?ed water|\bdistilled\b|\bdistil\w*",
              "juice": r"\bjuyce|\bjuice", "ale_beer": r"\bale\b|\bbeer\b|\bposset", "syrup": r"\bsyrr?up|\bsirr?up|\bsyrop",
              "ointment": r"\boyntment|\bointment|\bunguent|\bsalve"}
MIN_CONF = 0.6


def _sentences_excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    out = ""
    for s in re.split(r"(?<=[.;:!?])\s+", text):
        if len(out) + len(s) + 1 > limit:
            break
        out = (out + " " + s).strip()
    return (out or text[:limit].rsplit(" ", 1)[0]) + " …"


def _wikipedia(name: str) -> str:
    title = name.replace(" ", "_")
    for _ in range(3):
        try:
            text, _, _ = get_text("sources", WP_RAW.format(quote(title)))
        except Exception:  # noqa: BLE001 - missing article
            return ""
        m = re.match(r"\s*#REDIRECT\s*\[\[([^\]|#]+)", text, re.I)
        if not m:
            return f"https://en.wikipedia.org/wiki/{quote(title)}" if text.strip() else ""
        title = m.group(1).strip().replace(" ", "_")
    return ""


def _gbif(name: str) -> str:
    r = gbif_match(name)
    if not r:
        return ""
    key = r.get("acceptedUsageKey") or r.get("usageKey")
    return f"https://www.gbif.org/species/{key}" if key else ""


def _passages(p: pd.DataFrame, e) -> pd.DataFrame:
    if e.source == "culpeper-1652":
        return p[(p.source_id == "culpeper-1652") & (p.entry_slug == e.entry)]
    return p[p.passage_id.str.startswith(f"pliny-nh:{e.entry}:")]


def _fold(t: str) -> str:
    return t.lower().replace("æ", "ae").replace("œ", "oe")


def _description(ps: pd.DataFrame, e) -> tuple[pd.DataFrame, str]:
    """Culpeper: the Description paragraphs, else the entry's opening paragraphs. Pliny: the first body paragraph
    of the chapter that names the plant as written, else the first body paragraph."""
    body = ps[ps.passage_type == "body"]
    if e.source == "culpeper-1652":
        d = body[body.subsection == "description"]
        if len(d):
            return d, "Culpeper 1652, Description"
        d = body[body.subsection == "intro"]
        return (d, "Culpeper 1652, opening paragraph (no Description section)") if len(d) else (body.head(1), "Culpeper 1652, first paragraph")
    words = [w for w in re.findall(r"[a-zæœ]{5,}", _fold(e.nameAsWritten)) if w not in {"called", "known", "otherwise", "plant"}]
    hit = body[body.text_clean.map(lambda t: any(w in _fold(t) for w in words))] if words else body.iloc[0:0]
    if len(hit):
        return hit.head(1), "Pliny (Bostock & Riley), first paragraph naming the plant"
    return body.head(1), "Pliny (Bostock & Riley), first paragraph of the chapter"


def _n(k: int, one: str, many: str) -> str:
    return f"{k} {one if k == 1 else many}"


def build() -> pd.DataFrame:
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    ss = ss[ss.proposed]
    cand = pd.read_parquet(INTERIM / "m2" / "name_candidates.parquet")
    top = cand[cand["rank"] == 1]
    inv = pd.read_parquet(INTERIM / "m2" / "name_inventory.parquet").set_index("nameId")
    p = pd.read_parquet(INTERIM / "passages.parquet")
    tox = pd.read_csv(ROOT / "data" / "reference" / "toxicity_curated.csv", dtype=str).fillna("").set_index("acceptedName")
    from .study_set import DECISIONS, NAME_EXCLUSIONS
    dec = pd.read_csv(DECISIONS).set_index("species") if DECISIONS.exists() else pd.DataFrame()
    nx = pd.read_csv(NAME_EXCLUSIONS) if NAME_EXCLUSIONS.exists() else pd.DataFrame(columns=["nameId", "species", "reviewerNote"])
    removed = {(r.nameId, r.species): r.reviewerNote for r in nx.itertuples()}
    full = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    extra = full[full.acceptedName.isin(set(dec.index) - set(ss.acceptedName))] if len(dec) else full.iloc[0:0]
    ss = pd.concat([ss, extra])  # reviewed species that are no longer proposed keep their row
    rows = []
    for sp in ss.itertuples():
        ents = top[top.acceptedName == sp.acceptedName].copy()
        ents["removedByReviewer"] = [removed.get((n, sp.acceptedName), "") for n in ents.nameId]
        ents["counted"] = (~ents.disputed) & (ents.confidence >= MIN_CONF) & (ents.removedByReviewer == "")
        names, pids, desc, desc_src, recipe_pids = {"culpeper-1652": [], "pliny": []}, {"culpeper-1652": [], "pliny": []}, "", "", []
        bases, how = [], []
        ents["_culp"] = ents.source == "culpeper-1652"  # Culpeper's morphological Description is preferred
        for e in ents.sort_values(["counted", "_culp", "confidence"], ascending=False).itertuples():
            ie = inv.loc[e.nameId]
            ps = _passages(p, ie)
            flag = ("" if e.counted else f" [removed by reviewer: {e.removedByReviewer}]" if e.removedByReviewer
                    else " [disputed]" if e.disputed else " [confidence < 0.6]")
            names[e.source].append(f"{e.nameAsWritten} ({e.confidence:.2f}{', genus-level' if e.genusLevelOnly else ''}){flag}")
            pids[e.source] += list(ps.passage_id)
            ev = json.loads(e.evidence)
            how += sorted({x["how"].split(" (")[0] for x in ev})
            bases.append(e.basis)
            if e.counted:
                recipe_pids += list(ps[ps.recipe_scope.fillna(False).astype(bool) & (ps.passage_type == "body")].passage_id)
            if not desc and e.counted:
                d, label = _description(ps, e)
                if len(d):
                    desc = _sentences_excerpt(" ".join(d.text_clean))
                    desc_src = f"{label}: {d.passage_id.iloc[0]}"
        recipe_pids = list(dict.fromkeys(recipe_pids))  # several name entries can share one chapter
        pids = {k: list(dict.fromkeys(v)) for k, v in pids.items()}
        rtext = p[p.passage_id.isin(recipe_pids)].text_clean.str.lower()
        vehicle = {k: int(rtext.str.contains(rx, regex=True).sum()) for k, rx in VEHICLES.items()}
        prepw = {k: int(rtext.str.contains(rx, regex=True).sum()) for k, rx in PREP_WORDS.items()}
        counted = ents[ents.counted]
        n_disp = int((~ents.counted & ents.disputed & (ents.removedByReviewer == "")).sum())
        n_rem = int((ents.removedByReviewer != "").sum())
        genus_level = bool(ents.genusLevelOnly.any())
        genus_signal = int(sum("classical genus match" in x for x in ents[ents.counted].evidence))
        flags = []
        if n_disp:
            flags.append(_n(n_disp, "disputed name entry also resolves here", "disputed name entries also resolve here") + " (excluded from counts)")
        if n_rem:
            flags.append(_n(n_rem, "name entry removed by the reviewer", "name entries removed by the reviewer"))
        if genus_level:
            flags.append("a disputed entry is resolved only to genus level")
        if len(counted) and counted.confidence.min() < 0.8:
            flags.append(f"lowest counted confidence {counted.confidence.min():.2f}")
        if len(counted) == 1:
            flags.append("one counted name entry")
        if sp.sources == 1:
            flags.append(f"one source only ({sp.sourceList})")
        if genus_signal:
            flags.append(_n(genus_signal, "counted entry relies", "counted entries rely") + " on the classical-genus signal")
        if set(counted.basis) == {"commentary_19c"}:
            flags.append("resolved only via 19th-century footnotes")
        t = tox.loc[sp.acceptedName] if sp.acceptedName in tox.index else None
        rows.append({
            "species": sp.acceptedName, "family": sp.family, "wfoId": sp.wfoId, "sources": sp.sourceList,
            "riskFlags": "; ".join(flags) or "none",
            "culpeperNames": "; ".join(names["culpeper-1652"]), "culpeperPassageIds": " ".join(pids["culpeper-1652"]),
            "plinyNames": "; ".join(names["pliny"]), "plinyPassageIds": " ".join(pids["pliny"]),
            "descriptionExcerpt": desc, "descriptionSource": desc_src,
            "resolutionBasis": "; ".join(sorted(set(bases))), "resolutionEvidence": "; ".join(sorted(set(how))),
            "countedEntries": int(len(counted)), "minCountedConfidence": round(float(counted.confidence.min()), 2) if len(counted) else None,
            "disputedEntries": n_disp, "genusLevel": genus_level, "attestationProxy": sp.attestations,
            "wikipediaUrl": _wikipedia(sp.acceptedName), "gbifUrl": _gbif(sp.acceptedName),
            "wfoUrl": f"https://www.worldfloraonline.org/taxon/{sp.wfoId}",
            "recipeScopePassages": len(recipe_pids),
            **{f"mentions_{k}": v for k, v in vehicle.items()},
            **{f"prep_{k}": v for k, v in prepw.items()},
            "compounds": int(sp.nCompounds), "coverage": "poor (heuristic)" if sp.poorCoverage else "adequate (heuristic)",
            "toxicity": t.toxicity if t is not None else "not curated (not proposed)",
            "toxicityScope": (t.evidenceScope if t is not None and "evidenceScope" in t.index else ""),
            "toxicitySource": t.sourceName if t is not None else "",
            "toxicityUrl": t.sourceUrl if t is not None else "", "toxicityBasis": t.basis if t is not None else "",
            "proposedNow": bool(sp.proposed), "eligibleNow": bool(sp.eligible),
            "decision": dec.loc[sp.acceptedName, "decision"] if sp.acceptedName in dec.index else "",
            "reason": dec.loc[sp.acceptedName, "reason"] if sp.acceptedName in dec.index else "",
            "reReviewRequested": bool(n_rem) and (dec.loc[sp.acceptedName, "decision"] in ("unsure", "reject") if sp.acceptedName in dec.index else False),
        })
    df = pd.DataFrame(rows)
    df["_s"] = df.minCountedConfidence.fillna(0)
    df = df.sort_values(["disputedEntries", "genusLevel", "_s", "countedEntries"], ascending=[False, False, True, True]).drop(columns="_s")
    df.insert(0, "reviewOrder", range(1, len(df) + 1))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    _md(df)
    return df


def _md(df: pd.DataFrame) -> None:
    L = ["# Study-set review sheet", "",
         f"Generated by `python -m lip m3 review` from pipeline outputs; do not edit by hand. **{len(df)} species reviewed.** "
         "Decisions are read from `config/study_set_review_decisions.csv`; to change one, edit that file and re-run. "
         "Machine-readable version: [STUDY_SET_REVIEW.csv](STUDY_SET_REVIEW.csv).", "",
         "**Order.** Rows most likely to be wrong come first:",
         "1. species with disputed name entries;",
         "2. then genus-level resolutions;",
         "3. then the lowest confidence among counted entries;",
         "4. then the fewest counted entries.", "",
         "**Read with care:**",
         "- **Description excerpts** are the first sentences of Culpeper's Description, or of Pliny's chapter, cut mechanically, not selected.",
         "- **Recipes.** Recipe extraction (M1) has not been run on the corpus, so there are no recipe counts. The *vehicle mentions* "
         "are a **heuristic proxy**: how many recipe-scope passages mention each word, not how many recipes use it.",
         "- **Toxicity** entries are AI-drafted and unverified.",
         "- **Name entries** marked [disputed] resolve to the species but do not count towards attestation.", "",
         ]
    dec = df[df.decision.fillna("") != ""]
    if len(dec):
        head = df[df.decision == "approve"]
        L += ["## Review decisions (project lead, `config/study_set_review_decisions.csv`)", "",
              f"**{(df.decision == 'approve').sum()} approve · {(df.decision == 'unsure').sum()} unsure · {(df.decision == 'reject').sum()} reject.** "
              f"Unsure counts as reject, so **{len(head)} species form the headline set.**", ""]
        rr = df[df.reReviewRequested]
        if len(rr):
            L += ["**Re-review requested.** For these rows the reviewer removed a wrongly merged name entry (`config/name_entry_exclusions.csv`). "
                  "The rows below are recomputed without it; the decision stands until re-reviewed:", ""]
            L += [f"- *{r.species}* ({r.decision}): now {r.countedEntries} counted entr{'y' if r.countedEntries == 1 else 'ies'}, attestation proxy "
                  f"{r.attestationProxy}, {'still eligible' if r.eligibleNow else '**no longer eligible** (attestation proxy below 3)'}." for r in rr.itertuples()]
            L += [""]
        cols = ["water", "wine", "vinegar", "oil", "honey"]
        pcols = ["decoction", "distilled_water", "juice", "ale_beer", "syrup", "ointment"]
        L += [f"**Vehicle and preparation words across the {len(head)} headline species** (heuristic: recipe-scope passages mentioning the word, "
              "after de-duplicating passages shared by several name entries; not recipe counts):", "",
              "| Word | Passages mentioning it | Species with ≥ 1 |", "|---|---|---|"]
        L += [f"| {c} | {int(head[f'mentions_{c}'].sum())} | {int((head[f'mentions_{c}'] > 0).sum())} |" for c in cols]
        L += [f"| {c.replace('_', ' ')} | {int(head[f'prep_{c}'].sum())} | {int((head[f'prep_{c}'] > 0).sum())} |" for c in pcols]
        none = head[(head[[f"mentions_{c}" for c in cols] + [f"prep_{c}" for c in pcols]].sum(axis=1) == 0)]
        L += ["", "Headline species with no vehicle or preparation word in their recipe-scope passages: "
              + (", ".join(f"*{x}*" for x in none.species) if len(none) else "none") + ".", ""]
    L += ["## All reviewed species", "",
          "| # | Species | Sources | Risk flags | Counted entries | Min. conf. | Compounds | Toxicity | Decision |", "|---|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        tx = r.toxicity + (f" ({r.toxicityScope})" if isinstance(r.toxicityScope, str) and r.toxicityScope not in ("", "species") else "")
        L.append(f"| {r.reviewOrder} | [*{r.species}*](#{r.reviewOrder}-{r.species.lower().replace(' ', '-').replace('×', '')}) | {r.sources} | "
                 f"{r.riskFlags} | {r.countedEntries} | {r.minCountedConfidence} | {r.compounds} | {tx} | "
                 f"{(r.decision or 'pending') + (' — re-review requested' if r.reReviewRequested else '')} |")
    for r in df.itertuples():
        links = " · ".join(x for x in (f"[Wikipedia]({r.wikipediaUrl})" if r.wikipediaUrl else "Wikipedia: no article found",
                                        f"[GBIF]({r.gbifUrl})" if r.gbifUrl else "GBIF: no match", f"[WFO]({r.wfoUrl})"))
        L += ["", f"## {r.reviewOrder}. {r.species}", "",
              f"*{r.family}* · {r.sources} · {links}", "",
              f"- **Risk flags:** {r.riskFlags}",
              f"- **Culpeper names:** {r.culpeperNames or '—'}",
              f"- **Pliny names:** {r.plinyNames or '—'}",
              f"- **Resolution:** basis {r.resolutionBasis}; evidence: {r.resolutionEvidence}. Counted entries {r.countedEntries}, "
              f"lowest counted confidence {r.minCountedConfidence}, disputed entries {r.disputedEntries}, genus-level {'yes' if r.genusLevel else 'no'}. "
              f"Attestation proxy {r.attestationProxy}.",
              f"- **Description** ({r.descriptionSource or 'none found'}): {r.descriptionExcerpt or '—'}",
              f"- **Recipe-scope passages (counted entries):** {r.recipeScopePassages}. Vehicle mentions (heuristic): "
              f"water {r.mentions_water}, wine {r.mentions_wine}, vinegar {r.mentions_vinegar}, oil {r.mentions_oil}, honey {r.mentions_honey}; "
              f"preparation words: decoction {r.prep_decoction}, distilled water {r.prep_distilled_water}, juice {r.prep_juice}, "
              f"ale/beer {r.prep_ale_beer}, syrup {r.prep_syrup}, ointment {r.prep_ointment}.",
              f"- **Compounds (LOTUS):** {r.compounds}, coverage {r.coverage}.",
              f"- **Toxicity (AI-drafted, unverified):** `{r.toxicity}`"
              + (f" — evidence: {r.toxicityScope}" if isinstance(r.toxicityScope, str) and r.toxicityScope not in ("", "species") else "")
              + (f", [{r.toxicitySource}]({r.toxicityUrl})" if isinstance(r.toxicityUrl, str) and r.toxicityUrl else ""),
              f"- **Passage IDs:** Culpeper: {r.culpeperPassageIds or '—'}; Pliny: {r.plinyPassageIds or '—'}",
              (f"- **Decision:** {r.decision}" + (" — **re-review requested** (a name entry was removed)" if r.reReviewRequested else "")
               + f" · **Reason:** {r.reason}" if isinstance(r.decision, str) and r.decision else
               "- **Decision:** ______ (approve / reject / unsure) · **Reason:** ______")]
        if not r.proposedNow:
            L.insert(len(L) - 1, "- **Status now:** no longer proposed (not eligible after the reviewer's fix).")
    OUT_MD.write_text("\n".join(L) + "\n")
