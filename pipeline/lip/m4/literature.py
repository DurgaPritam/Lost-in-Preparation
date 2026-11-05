"""Literature check for the preparation model — EXPLORATORY set (selected after model build).

These 9 rows were chosen by the same AI that built the model, after the model existed. They are kept
as an exploratory check only; the confirmatory check follows the selection rule pre-registered in
docs/PREREGISTRATION.md (see prereg_literature.py) and is reported separately, never pooled.

basis = "ai_curated_literature_reference": a small hand-built table of what published papers report
in teas / aqueous extracts vs essential oils vs alcoholic extracts, built by an AI (Claude Code) from
open-access PMC articles fetched in the pipeline run. Every quote is re-checked against the fetched
article text each run. Articles whose page states no reuse licence (PMC2995283) are not quoted: the row
carries our own paraphrase plus a full citation, checked against the article by short anchor terms.
Not a human-curated gold standard.

Agreement rule (pre-registered in config/prep_model.toml [literature_check]):
  reported major / high / present -> predicted median >= present_min
  reported low / not carried      -> predicted median <  absent_max
"""
from __future__ import annotations

import html
import json
import re
from typing import NamedTuple

import pandas as pd

from ..http import get_json, get_text
from ..paths import INTERIM, ROOT
from . import chem
from . import model as M

OUT = INTERIM / "m4"
REF_CSV = ROOT / "data" / "reference" / "prep_literature_v1.csv"
BASIS = "ai_curated_literature_reference"
LABEL = ("EXPLORATORY (rows selected after model build): preparation model vs AI-curated literature table, "
         "provisional; not human-curated")
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/{}/"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/property/IsomericSMILES,InChIKey/JSON"

class Paraphrase(NamedTuple):
    """Evidence for an article with NO stated reuse licence: our own paraphrase plus a citation, never its text.

    `anchors` are short technical terms (not sentences) that must all occur within one ANCHOR_WINDOW-character
    window of the fetched article, so the paraphrase is still checked against the source on every run.
    """
    text: str
    anchors: tuple


ANCHOR_WINDOW = 400
NO_LICENCE = {"PMC2995283"}  # article pages with no Creative Commons or other reuse licence stated
CITATIONS = {
    "PMC2995283": "Srivastava JK, Shankar E, Gupta S. Chamomile: a herbal medicine of the past with bright future. "
                  "Mol Med Rep. 2010;3(6):895-901. doi:10.3892/mmr.2010.377",
}

# plant, compound (PubChem name), preparation as reported, model preparation, expectation, PMCID,
# evidence: a verbatim quote (str) for openly licensed articles, or a Paraphrase for unlicensed ones
ROWS = [
    ("Matricaria chamomilla", "alpha-bisabolol", "essential oil", "distilled water", "present", "PMC2995283",
     Paraphrase("The review lists α-bisabolol among the principal terpenoid components of German chamomile flower essential oil.",
                ("principal components", "essential oil", "α-bisabolol"))),
    ("Matricaria chamomilla", "apigenin 7-glucoside", "tea (aqueous extract)", "hot water infusion (tea)", "present", "PMC2995283",
     Paraphrase("The review reports that chamomile tea and other aqueous extracts are high in apigenin 7-O-glucoside.",
                ("Aqueous extracts", "tea", "high levels", "apigenin-7- O -glucoside"))),
    ("Matricaria chamomilla", "apigenin", "tea (aqueous extract)", "hot water infusion (tea)", "low", "PMC2995283",
     Paraphrase("The review reports that chamomile tea and other aqueous extracts contain little free (aglycone) apigenin.",
                ("Aqueous extracts", "tea", "low concentrations", "free apigenin"))),
    ("Mentha × piperita", "menthol", "essential oil", "distilled water", "present", "PMC13074686",
     "as well as essential oil, whose main constituents are menthol and menthone"),
    ("Mentha × piperita", "rosmarinic acid", "hot water extract", "hot water infusion (tea)", "present", "PMC13074686",
     "This outcome reflects a polarity mismatch with the main peppermint phenolics (rosmarinic acid and derivatives) and the fact that short extraction times in hydroalcoholic systems do not allow sufficient tissue swelling compared with water."),
    ("Satureja montana", "thymol", "essential oil", "distilled water", "present", "PMC7587570",
     "Thymol (81.79%) revealed by gas chromatography-mass spectrometry (GC-MS) was the predominant compound of the essential oil of this plant."),
    ("Satureja montana", "rosmarinic acid", "ethanolic tincture", "modern 70% ethanol extract", "present", "PMC7587570",
     "Caffeic, rosmarinic, and chlorogenic acids, (–)-catechin and rutin were identified in the tinctures using the HPTLC method."),
    ("Thymus vulgaris", "thymol", "essential oil", "distilled water", "present", "PMC10217939",
     "the essential oil of common thyme is extracted by the distillation of the fresh leaves and flowering tops, and it contains 20–54% thymol"),
    ("Salvia rosmarinus", "carnosic acid", "essential oil (distillation)", "distilled water", "low", "PMC11944828",
     "obtained fractions enriched in carnosol and carnosic acids through extraction from the residue of rosemary plants obtained after essential oil production"),
]


def _article_text(pmcid: str) -> tuple[str, str, str]:
    raw, sha, when = get_text("sources", PMC.format(pmcid))
    body = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)))
    return body, sha, when


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("p -Thymol", "Thymol")).strip()


def _anchored(body: str, anchors: tuple) -> bool:
    first = anchors[0]
    start = body.find(first)
    while start >= 0:
        lo, hi = max(0, start - ANCHOR_WINDOW), start + ANCHOR_WINDOW
        if all(a in body[lo:hi] for a in anchors):
            return True
        start = body.find(first, start + 1)
    return False


def build_table() -> pd.DataFrame:
    rows = []
    for plant, cpd, rep_prep, model_prep, expect, pmcid, ev in ROWS:
        body, sha, when = _article_text(pmcid)
        if isinstance(ev, Paraphrase):
            if pmcid not in NO_LICENCE:
                raise ValueError(f"{pmcid}: paraphrase used for an article not listed as unlicensed")
            if not _anchored(_norm(body), ev.anchors):
                raise ValueError(f"paraphrase anchors not found together in {pmcid}: {ev.anchors}")
            quote, paraphrase, evidence = "", ev.text, "paraphrase"
        else:
            if pmcid in NO_LICENCE:
                raise ValueError(f"{pmcid} has no stated licence: use a Paraphrase, not a quote")
            if _norm(ev) not in _norm(body):
                raise ValueError(f"quote not found in {pmcid}: {ev[:80]!r}")
            quote, paraphrase, evidence = ev, "", "verbatim quote"
        title = re.search(r"^\s*(.*?)\s*-\s*PMC", body)
        p = get_json("pubchem", PUBCHEM.format(cpd.replace(" ", "%20")))["PropertyTable"]["Properties"][0]
        rows.append({"plant": plant, "compound": cpd, "reportedPreparation": rep_prep, "modelPreparation": model_prep,
                     "reported": expect, "pmcid": pmcid, "url": PMC.format(pmcid), "evidenceType": evidence, "quote": quote,
                     "paraphrase": paraphrase, "citation": CITATIONS.get(pmcid, ""),
                     "articleSha256": sha, "retrievedAt": when, "pubchemCid": p["CID"], "inchikey": p["InChIKey"],
                     "smiles": p.get("IsomericSMILES") or p.get("SMILES"), "basis": BASIS,
                     "articleTitle": title.group(1)[:160] if title else ""})
    df = pd.DataFrame(rows)
    REF_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(REF_CSV, index=False)
    return df


def evaluate(cfg: dict) -> dict:
    df = build_table()
    thr = cfg["literature_check"]
    res = []
    for i, r in enumerate(df.itertuples()):
        d = chem.describe(r.smiles)
        c = M.Compound(r.inchikey, d["logP"], d["basicN"], d["heatFlags"], d["volatile"], d["mw"])
        s = M.simulate(c, M.BY_LABEL[r.modelPreparation], cfg, seed_offset=100 + i)
        agree = s["likelihood"] >= thr["present_min"] if r.reported == "present" else s["likelihood"] < thr["absent_max"]
        res.append({"plant": r.plant, "compound": r.compound, "preparation": r.modelPreparation, "reported": r.reported,
                    "predicted": s["likelihood"], "low": s["low"], "high": s["high"], "agree": bool(agree),
                    "drivers": s["drivers"], "flags": s["heuristicFlags"], "pmcid": r.pmcid})
    n, k = len(res), sum(x["agree"] for x in res)
    out = {"basis": BASIS, "label": LABEL, "n": n, "agree": k, "rows": res, "thresholds": thr}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "literature_check.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out
