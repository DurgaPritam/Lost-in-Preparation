"""M2 name resolution: historical plant name -> up to 3 accepted species with confidence (HEURISTIC).

Evidence (each adds weight to a GBIF-backbone species; weights are heuristic and documented here):
  database        the name as written is itself a scientific binomial (GBIF strict match)   2.0
  database        GBIF backbone species with an EXACT English vernacular match (plurals and
                  possessives folded): each query contributes 1.0, split by `support` (the number
                  of independent vernacular-name records matching); ×0.3 for Pliny names, whose
                  English renderings of Greek/Latin names are unreliable
                  Regional prior (v2: milder, so cultivated and traded plants stay plausible): vernacular
                  weights are multiplied by 0.5 + 0.5 × log10(1+n) / max over
                  the query's candidates, n = GBIF occurrences in Great Britain (Culpeper, "the vulgar
                  herbs of this nation") or in Europe (Pliny)
  commentary_19c  binomial named in a Bostock & Riley footnote linked to the name:
                  strong link 2.0 / weak 1.0, divided by (order in footnote); ×0.5 if hedged.
                  v3: if the binomial's own sentence hedges or contradicts it ("probably", "takes this to be",
                  "thinks", "is right", "a totally different plant", …) or the footnote sets named authorities
                  against each other, the binomial is NOT used as the identification: weight ×0.2 (a
                  low-confidence candidate), the name is disputed, and the trigger is logged (footnoteTriggers)
  database        CLASSICAL GENUS (v2): a word of the name, or a Latinised/transliterated variant of it
                  ('Mandragora', 'Cummin'->Cuminum, 'Aron'->Arum), is an accepted plant genus (GBIF): candidates
                  in that genus get ×3 (ranking within the genus kept); if none exists, the genus's most-recorded
                  species in the region is added (2.0, genus-level, disputed). Pliny: every word is eligible;
                  Culpeper (an English herbal): only Latin-looking words, never English words
  database        BINOMIAL FROM NAME TOKENS (v2): genus + another word of the name matches a species
                  ('Dodder ... Epithimum' -> Cuscuta epithymum): 3.0
Scores per species are normalised to sum to 1 -> `confidence`. Each species is then mapped to its
accepted WFO name and id. `disputed` = top confidence < 0.6, or the deciding footnote hedges
("probably", "supposed", "some", "doubt"…), or the top two are within 0.15, or the total evidence
weight for the name is below 0.5 (weak evidence even if unopposed), or the name is resolved only to genus level,
or the TOXIC-CONFUSION check fires: candidates with confidence >= 0.15 differ in known toxicity (one listed
as poisonous, one not) — see m2/toxicity.py — or the GENUS-SIGNAL AUDIT lists the name as a false friend
(classical word with a different meaning, English spelling match, or chapter title; m2/genus_audit.py).
No scholarly identifications are used as candidates (they are reserved for evaluation), and no
LLM ("model" basis) is used in this version.
"""
from __future__ import annotations

import json
import math
import re
import string
from collections import defaultdict

import pandas as pd

from ..http import pmap
from ..paths import INTERIM
from . import services as S

OUT = INTERIM / "m2"
HEDGE = re.compile(r"\b(probabl[ey]|perhaps|suppos|uncertain|doubt|not known|unknown|conjectur|some (?:have|think|say|suppose)|"
                   r"others|it is thought|identity|identif(?:y|ied) it|it is not|may be|may not be|possibly|apparently|quer(?:y|ies)|"
                   r"inclined|impossible|cannot be|questionable|whether|difficult to)\w*", re.I)
STOP = set("wild garden common great greater lesser less small water black white sweet mountain tree herb herbs sea golden "
           "ladies lady english french roman greek red yellow blue green called other others kind kinds sort the and known "
           "otherwise plant plants true bastard field marsh wood stinking prickly double single female male broad narrow "
           "leaved flowered cultivated thistle grass root apples poppy leek those also some various".split())


LATINISH = re.compile(r"(um|us|a|is|on|os|es|ion|ia|ium|ae|ys|ix|ex)$", re.I)

# v3 footnote rule: a binomial is NOT used as the identification when its own sentence hedges or contradicts it,
# or when the footnote sets named authorities against each other. It stays a low-confidence candidate
# (weight x FOOTNOTE_TRIGGER_WEIGHT), the name is disputed, and the trigger phrase is logged.
FN_HEDGE = re.compile(r"\bprobabl[ey]\b|\bperhaps\b|\bpossibly\b|\btakes? (?:this|it|them|these) (?:to be|for)\b|\bthinks?\b|"
                      r"\bthought\b|\bsuppos\w*|\bconjectur\w*|\bis (?:probably )?right\b|\bconsiders?\b|\bis of opinion\b|"
                      r"\bseems?\b|\bappears? to\b|\bdoubt\w*|\buncertain\w*|\bmay be\b|\binclined\b|\bquer(?:y|ies)\b", re.I)
FN_CONTRA = re.compile(r"totally different|different plant|distinct plant|not the same|confound\w*|confus\w*|mistak\w*|"
                       r"erroneous\w*|wrongly", re.I)
AUTHORITIES = re.compile(r"\b(F[ée]e|Sprengel|Littr[ée]|Desfontaines|Brotier|Lobel|C(?:æ|ae)salpinus|Sibthorp|Dalechamps|"
                         r"Hardouin|Bauhin|Matthiolus|Anguillara|Dodon(?:æ|ae)us|Clusius|Tournefort|Fraas|Billerbeck|Sillig|Schneider)\b")
FOOTNOTE_TRIGGER_WEIGHT = 0.2


def footnote_trigger(text: str, binomial: str, n_binomials: int) -> str | None:
    """-> the trigger phrase that disqualifies `binomial` as an identification, or None."""
    sents = re.split(r"(?<=[.;])\s+", text)
    g, *rest = binomial.split()
    pat = re.compile(re.escape(g[:5]) + r"\w*\s+" + (re.escape(rest[0][:4]) if rest else ""), re.I)
    own = [x for x in sents if pat.search(x)] or [text]
    for x in own:
        m = FN_CONTRA.search(x) or FN_HEDGE.search(x)
        if m:
            return m.group(0)
    auth = sorted({a.replace("Fee", "Fée").replace("Littre", "Littré") for a in AUTHORITIES.findall(text)})
    if len(auth) >= 2 and n_binomials >= 2:
        return "competing authorities: " + ", ".join(auth)
    return None


def latin_tokens(ws: list[str]) -> list[str]:
    return [w for w in ws if len(w) >= 6 and LATINISH.search(w)]


def name_tokens(e) -> list[str]:
    words = {w for q in [e.nameAsWritten, *e.queries] for w in re.findall(r"[A-Za-zÆæŒœ]{4,}", q)}
    return sorted(w for w in words if w.lower() not in STOP)
BINOMIAL = re.compile(r"(?:\b(?:the|a|an|of|or|and)\s+)([A-Z][a-zæœëïé]+)\s+([a-zæœëïé]{3,})\b")
NOT_EPITHET = {"says", "has", "is", "was", "and", "the", "which", "this", "that", "with", "from", "seems", "thinks",
               "remarks", "states", "observes", "were", "are", "had", "also", "being", "says", "tells", "gives",
               "calls", "mentions", "speaks", "makes", "would", "will", "could", "should", "have", "does", "did"}


def footnote_binomials(text: str) -> list[str]:
    out = []
    for g, s in BINOMIAL.findall(text):
        if s in NOT_EPITHET:
            continue
        b = f"{g} {s}"
        if b not in out:
            out.append(b)
    return out


def capwords(s: str) -> str:
    return string.capwords(s.lower())


def run(inv: pd.DataFrame, fn_text: pd.Series, workers: int = 6) -> pd.DataFrame:
    # -- fetch phase (cached, parallel) ----------------------------------------------------
    latin_q = sorted({q for qs in inv.queries for q in qs if len(q.split()) == 2 and q.replace(" ", "").isalpha()})
    vern_q = sorted({q for qs in inv.queries for q in qs})
    fn_ids = sorted({f["id"] for fl in inv.footnotes for f in fl})
    bin_by_fn = {fid: footnote_binomials(fn_text.get(fid, "")) for fid in fn_ids}
    binoms = sorted({b for bl in bin_by_fn.values() for b in bl} | set(latin_q))
    match = dict(zip(binoms, pmap(S.gbif_match, binoms, workers)))
    vern = dict(zip(vern_q, pmap(S.gbif_vernacular, vern_q, workers)))

    def accepted(r):
        return S.gbif_accepted_species(r) if r else (None, None)
    usages = [r for r in match.values() if r] + [x for v in vern.values() for x in v]
    acc_map = {id(r): a for r, a in zip(usages, pmap(accepted, usages, workers))}
    region_of = {"culpeper-1652": "GB", "pliny": "EUROPE"}
    occ_keys = sorted({(acc_map[id(x)][1], region_of[e.source]) for e in inv.itertuples() for q in e.queries
                       for x in vern.get(q, []) if acc_map[id(x)][1]})
    occ = dict(zip(occ_keys, pmap(lambda kr: S.gbif_occurrences(*kr), occ_keys, workers)))

    # -- classical-genus signal: fetch ---------------------------------------------------------
    # Pliny names are Latin/Greek transliterations: every word is eligible. Culpeper is an English herbal:
    # only Latin-looking words (Chamepitys, Filipendula, Angelica) are eligible, never English words
    # such as 'Agrimony', 'Bugloss' or 'tongue'.
    toks = {e.nameId: (name_tokens(e) if e.source == "pliny" else [w for w in name_tokens(e) if LATINISH.search(w)])
            for e in inv.itertuples()}
    all_toks = sorted({w for ws in toks.values() for w in ws})
    genus_of = dict(zip(all_toks, pmap(S.gbif_genus, all_toks, workers)))

    # -- scoring ----------------------------------------------------------------------------
    rows = []
    base = {}
    triggers: dict[str, list] = {}
    for e in inv.itertuples():
        score: dict[str, float] = defaultdict(float)
        ev: dict[str, list] = defaultdict(list)
        hedged_top: dict[str, bool] = defaultdict(bool)
        for q in e.queries:
            if q in match and match[q]:
                sp, _ = acc_map[id(match[q])]
                if sp:
                    score[sp] += 2.0
                    ev[sp].append({"basis": "database", "how": "name as written is a scientific name", "query": q,
                                   "weight": 2.0})
            factor = 0.3 if e.source == "pliny" else 1.0
            hits = [x for x in vern.get(q, []) if acc_map[id(x)][0]]
            total_support = sum(x["support"] for x in hits)
            logs = {id(x): math.log10(1 + occ.get((acc_map[id(x)][1], region_of[e.source]), 0)) for x in hits}
            top_log = max(logs.values(), default=0) or 1.0
            for x in hits:
                sp, _ = acc_map[id(x)]
                prior = 0.5 + 0.5 * logs[id(x)] / top_log
                w = x["support"] / total_support * factor * prior
                score[sp] += w
                ev[sp].append({"basis": "database", "how": f"GBIF exact English vernacular (support {x['support']}, "
                               f"regional prior {prior:.2f})", "query": q, "weight": round(w, 3)})
        trig_log = []
        for f in e.footnotes:
            text = fn_text.get(f["id"], "")
            hedge = bool(HEDGE.search(text))
            bl = bin_by_fn.get(f["id"], [])
            for j, b in enumerate(bl):
                trig = footnote_trigger(text, b, len(bl))
                r = match.get(b)
                sp = acc_map[id(r)][0] if r else None
                if not sp:
                    if trig:  # an unmatched binomial still shows the footnote contests the name's identity
                        trig_log.append({"footnote": f["id"], "binomial": b, "species": None, "trigger": trig})
                    continue
                w = (2.0 if f["strength"] == "strong" else 1.0) / (j + 1)
                w *= FOOTNOTE_TRIGGER_WEIGHT if trig else (0.5 if hedge else 1.0)
                score[sp] += w
                hedged_top[sp] |= hedge or bool(trig)
                if trig:
                    trig_log.append({"footnote": f["id"], "binomial": b, "species": sp, "trigger": trig})
                ev[sp].append({"basis": "commentary_19c", "how": f"{f['strength']} footnote link"
                               + (f", not used as identification (trigger: '{trig}')" if trig else ", hedged" if hedge else ""),
                               "footnote": f["id"], "binomial": b, "weight": round(w, 3)})
        triggers[e.nameId] = trig_log
        base[e.nameId] = (score, ev, hedged_top)

    # -- genus boost, genus fallback, binomials from tokens (fetch then apply) --------------------
    combos, fallback_req = set(), set()
    for e in inv.itertuples():
        score = base[e.nameId][0]
        genera = {g["genus"] for w in toks[e.nameId] if (g := genus_of.get(w))}
        top_genera = {sp.split()[0] for sp, _ in sorted(score.items(), key=lambda kv: -kv[1])[:1]}
        for g in genera | top_genera:
            for w in latin_tokens(toks[e.nameId]):
                if w.lower() != g.lower():
                    for v in S.latin_variants(w)[:2]:
                        combos.add(f"{g} {v.lower()}")
        for w in toks[e.nameId]:
            gm = genus_of.get(w)
            if gm and not any(sp.split()[0] == gm["genus"] for sp in score):
                fallback_req.add((gm["genusKey"], region_of[e.source]))
    combos = sorted(combos)
    loose = dict(zip(combos, pmap(S.gbif_match_loose, combos, workers)))
    fb = dict(zip(sorted(fallback_req), pmap(lambda kr: S.gbif_top_species_in_genus(*kr), sorted(fallback_req), workers)))
    genus_level: dict[str, bool] = {}
    for e in inv.itertuples():
        score, ev, hedged_top = base[e.nameId]
        genus_level[e.nameId] = False
        top_genera = {sp.split()[0] for sp, _ in sorted(score.items(), key=lambda kv: -kv[1])[:1]}
        genera = {}
        for w in toks[e.nameId]:
            if (gm := genus_of.get(w)):
                genera[gm["genus"]] = gm
        for c in [k for k in loose if loose[k] and k.split()[0] in (set(genera) | top_genera)]:
            r = loose[c]
            g, v = c.split(" ", 1)
            if not any(w for w in latin_tokens(toks[e.nameId]) if v in [x.lower() for x in S.latin_variants(w)[:2]]):
                continue
            sp = S._species_of(r)
            if sp and sp.split()[0] == g and r.get("rank") in S.SPECIES_RANKS:
                score[sp] += 3.0
                ev[sp].append({"basis": "database", "how": f"binomial rebuilt from name tokens ({c} -> {sp}, {r.get('matchType')})",
                               "weight": 3.0})
        for g, gm in genera.items():
            inside = [sp for sp in score if sp.split()[0] == g]
            if inside:
                for sp in inside:  # ×3 keeps the ranking within the genus
                    add = score[sp] * 2
                    score[sp] += add
                    ev[sp].append({"basis": "database", "how": f"classical genus match ('{gm['token']}' -> {g}), ×3", "weight": round(add, 3)})
            else:
                for sp in fb.get((gm["genusKey"], region_of[e.source]), [])[:1]:
                    score[sp] += 2.0
                    ev[sp].append({"basis": "database", "how": f"classical genus match ('{gm['token']}' -> {g}); species = most "
                                   f"recorded in region (heuristic, genus-level)", "weight": 2.0})
                    genus_level[e.nameId] = True
        total = sum(score.values())
        ranked = sorted(score.items(), key=lambda kv: -kv[1])[:3]
        for rank, (sp, s) in enumerate(ranked, 1):
            conf = s / total
            bases = defaultdict(float)
            for x in ev[sp]:
                bases[x["basis"]] += x["weight"]
            basis = max(bases, key=bases.get)
            ref = next((x.get("footnote") for x in ev[sp] if x["basis"] == basis and x.get("footnote")), None)
            rows.append({"nameId": e.nameId, "source": e.source, "nameAsWritten": e.nameAsWritten, "rank": rank,
                         "gbifSpecies": sp, "confidence": round(conf, 4), "evidenceTotal": round(total, 3), "basis": basis, "basisRef": ref,
                         "hedged": hedged_top[sp], "evidence": json.dumps(ev[sp], ensure_ascii=False)})
        if ranked and genus_level[e.nameId]:
            rows[-len(ranked)]["genusLevelOnly"] = True
        if not ranked:
            rows.append({"nameId": e.nameId, "source": e.source, "nameAsWritten": e.nameAsWritten, "rank": 0,
                         "gbifSpecies": None, "confidence": None, "basis": None, "basisRef": None, "hedged": False,
                         "evidence": "[]"})
    cand = pd.DataFrame(rows)

    # -- WFO accepted names -------------------------------------------------------------------
    species = sorted(cand.gbifSpecies.dropna().unique())
    wfo = dict(zip(species, pmap(S.wfo_resolve, species, 4)))
    cand["acceptedName"] = cand.gbifSpecies.map(lambda s: (wfo.get(s) or {}).get("acceptedName") if s else None)
    cand["wfoId"] = cand.gbifSpecies.map(lambda s: (wfo.get(s) or {}).get("wfoId") if s else None)
    cand["family"] = cand.gbifSpecies.map(lambda s: (wfo.get(s) or {}).get("family") if s else None)
    cand["inWFO"] = cand.wfoId.notna()
    from . import toxicity
    tox = [toxicity.flag(a if isinstance(a, str) else g) for a, g in zip(cand.acceptedName, cand.gbifSpecies)]
    cand["toxicity"] = [x[0] for x in tox]
    cand["toxicityNote"] = [x[1] for x in tox]
    if "genusLevelOnly" not in cand:
        cand["genusLevelOnly"] = False
    cand["genusLevelOnly"] = cand.genusLevelOnly.fillna(False).astype(bool)

    # -- disputed -------------------------------------------------------------------------------
    disputed, toxic_confusion = {}, {}
    for nid, g in cand[cand["rank"] > 0].groupby("nameId"):
        g = g.sort_values("rank")
        top = g.iloc[0]
        close = len(g) > 1 and (top.confidence - g.iloc[1].confidence) < 0.15
        live = g[g.confidence >= 0.15]
        toxic_conf = bool((live.toxicity == "known_toxic").any() and (live.toxicity != "known_toxic").any())
        toxic_confusion[nid] = toxic_conf
        disputed[nid] = bool(top.confidence < 0.6 or (top.basis == "commentary_19c" and top.hedged) or close
                             or top.evidenceTotal < 0.5 or g.genusLevelOnly.any() or toxic_conf or bool(triggers.get(nid)))
    cand["disputed"] = cand.nameId.map(disputed).fillna(False).astype(bool)
    cand["footnoteTriggers"] = cand.nameId.map(lambda n: json.dumps(triggers.get(n, []), ensure_ascii=False))
    cand["toxicConfusion"] = cand.nameId.map(toxic_confusion).fillna(False).astype(bool)
    # genus-signal audit (docs/GENUS_SIGNAL_AUDIT.md): false friends are disputed, never deleted
    from . import genus_audit
    cand["disputedBeforeGenusAudit"] = cand.disputed
    ff = genus_audit.finding_of()
    cand["genusSignalAudit"] = cand.nameId.map(ff).fillna("")
    cand.loc[cand.nameId.isin(ff), "disputed"] = True
    return cand


def summary(inv: pd.DataFrame, cand: pd.DataFrame) -> dict:
    top = cand[cand["rank"] == 1]
    out = {}
    for src, g in inv.groupby("source"):
        t = top[top.source == src]
        out[src] = {"names": int(len(g)), "resolved": int(t.nameId.nunique()),
                    "resolvedInWFO": int(t[t.inWFO].nameId.nunique()),
                    "disputed": int(t[t.disputed].nameId.nunique()),
                    "topBasis": {k: int(v) for k, v in t.basis.value_counts().items()}}
    return out


def main(limit: int | None = None) -> dict:
    df = pd.read_parquet(INTERIM / "passages.parquet")
    from .inventory import build
    inv = build(df)
    if limit:
        inv = pd.concat([inv[inv.source == "culpeper-1652"].head(limit), inv[inv.source == "pliny"].head(limit)])
    fn_text = df[df.passage_type == "footnote"].set_index("passage_id").text_clean
    cand = run(inv, fn_text)
    OUT.mkdir(parents=True, exist_ok=True)
    inv.assign(queries=inv.queries.map(json.dumps), footnotes=inv.footnotes.map(json.dumps)).to_parquet(OUT / "name_inventory.parquet", index=False)
    cand.to_parquet(OUT / "name_candidates.parquet", index=False)
    s = summary(inv, cand)
    (OUT / "name_resolution_summary.json").write_text(json.dumps(s, indent=2))
    from . import genus_audit
    res = genus_audit.build(cand)
    top = cand[cand["rank"] == 1]
    genus_audit.write_md(res, dict(zip(top.nameId, top.disputedBeforeGenusAudit)))
    genus_audit.flagged_passages()
    return s
