"""Pre-registered literature check (docs/PREREGISTRATION.md, registered in commit 35b7c0d).

Implements the registered rule mechanically. Implementation clarifications (not deviations):
  - the reference list at the end of a PMC article page is excluded (cited titles are not the
    article's own sentences);
  - "exactly one preparation term" is applied to preparation TYPES after mapping, so a sentence
    saying "essential oil ... hydrodistillation" counts once.
basis = ai_curated_literature_reference (provisional).
"""
from __future__ import annotations

import html
import json
import re

import pandas as pd

from ..http import get_json, get_text
from ..paths import INTERIM, ROOT
from . import chem
from . import model as M

OUT = INTERIM / "m4"
CSV = ROOT / "data" / "reference" / "prep_literature_prereg_v1.csv"
SEARCH = "https://pmc.ncbi.nlm.nih.gov/search/?term={}"
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/{}/"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/property/IsomericSMILES,InChIKey/JSON"
EXCLUDED_PMCIDS = {"PMC2995283", "PMC13074686", "PMC7587570", "PMC10217939", "PMC11944828"}
PLANTS = [
    ("Matricaria chamomilla", "chamomile", ["chamomile", "matricaria chamomilla", "matricaria recutita"]),
    ("Mentha × piperita", "peppermint", ["peppermint", "mentha piperita", "mentha × piperita", "mentha x piperita"]),
    ("Thymus vulgaris", "thyme", ["thyme", "thymus vulgaris"]),
    ("Salvia rosmarinus", "rosemary", ["rosemary", "salvia rosmarinus", "rosmarinus officinalis"]),
    ("Salvia officinalis", "sage", ["sage", "salvia officinalis"]),
    ("Melissa officinalis", "lemon balm", ["lemon balm", "melissa officinalis"]),
]
COMPOUNDS = {  # PubChem name -> synonyms matched in text (registered list)
    "menthol": ["menthol"], "menthone": ["menthone"], "pulegone": ["pulegone"], "carvone": ["carvone"],
    "limonene": ["limonene"], "1,8-cineole": ["1,8-cineole", "eucalyptol", "cineole"], "camphor": ["camphor"],
    "alpha-pinene": ["alpha-pinene", "α-pinene"], "borneol": ["borneol"], "thymol": ["thymol"], "carvacrol": ["carvacrol"],
    "p-cymene": ["p-cymene"], "gamma-terpinene": ["gamma-terpinene", "γ-terpinene"], "linalool": ["linalool"],
    "geraniol": ["geraniol"], "citral": ["citral", "geranial", "neral"], "citronellal": ["citronellal"],
    "alpha-bisabolol": ["alpha-bisabolol", "α-bisabolol", "bisabolol"], "chamazulene": ["chamazulene"],
    "beta-caryophyllene": ["beta-caryophyllene", "β-caryophyllene", "caryophyllene"],
    "alpha-thujone": ["alpha-thujone", "α-thujone", "thujone"], "rosmarinic acid": ["rosmarinic acid"],
    "caffeic acid": ["caffeic acid"], "chlorogenic acid": ["chlorogenic acid"], "carnosic acid": ["carnosic acid"],
    "carnosol": ["carnosol"], "ursolic acid": ["ursolic acid"], "apigenin": ["apigenin"],
    "apigenin 7-glucoside": ["apigenin 7-glucoside", "apigenin-7-o-glucoside", "apigenin-7-glucoside"],
    "luteolin": ["luteolin"], "luteolin 7-glucoside": ["luteolin 7-glucoside", "luteolin-7-o-glucoside", "luteolin-7-glucoside"],
    "eriocitrin": ["eriocitrin"], "hesperidin": ["hesperidin"], "rutin": ["rutin"], "quercetin": ["quercetin"],
}
PREPS = [
    (r"essential oil|hydrodistill\w*|steam distill\w*", "distilled water"),
    (r"\binfusions?\b|herbal teas?|\bteas?\b", "hot water infusion (tea)"),
    (r"\bdecoctions?\b", "decoction in water"),
    (r"aqueous extracts?|water extracts?", "hot water infusion (tea)"),
    (r"tinctures?|ethanolic extracts?|ethanol extracts?|hydroethanolic|hydroalcoholic", "modern 70% ethanol extract"),
    (r"methanolic extracts?|methanol extracts?", "modern methanol extract"),
]
PRESENT = re.compile(r"\bmain\b|\bmajor\b|predominant|principal|dominant|rich in|contain|identified|detected|\bfound\b|%|\bmg\b", re.I)
ABSENT = re.compile(r"not detected|\babsent\b|\btraces?\b|low concentrations?|low amounts?|lacking|free of|did not contain", re.I)
EXCLUDE = re.compile(r"supercritical|\bCO2\b|fraction|partition|hexane|chloroform|ethyl acetate|commercial|synthetic|derivative|"
                     r"total phenolic|activity|inhibit|IC50|\bMIC\b", re.I)
MAX_PER_ARTICLE, MAX_PER_PLANT, TARGET = 3, 6, 30


def _compound_hits(s: str) -> list[str]:
    low = s.lower()
    gly = {"apigenin 7-glucoside": "apigenin", "luteolin 7-glucoside": "luteolin"}
    hits = []
    for name, syns in COMPOUNDS.items():
        text = low
        if name in gly.values():  # do not count an aglycone inside its glycoside's name
            for g, a in gly.items():
                if a == name:
                    for x in COMPOUNDS[g]:
                        text = text.replace(x, " ")
        if any(re.search(r"(?<![\w-])" + re.escape(x) + r"(?![\w-])", text) for x in syns):
            hits.append(name)
    return hits


def _article(pmcid: str) -> tuple[str, str, bool, str, str]:
    raw, sha, when = get_text("sources", PMC.format(pmcid))
    title = html.unescape(re.search(r"<title>(.*?)</title>", raw, re.S).group(1)).replace(" - PMC", "").strip()
    cc = "creativecommons.org/licenses" in raw
    cut = min([i for i in (raw.find('class="ref-list'), raw.find('id="ref-list')) if i > 0] or [len(raw)])
    body = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw[:cut])))
    return title, body, cc, sha, when


def collect() -> tuple[pd.DataFrame, dict]:
    per_plant: dict[str, list[dict]] = {p[0]: [] for p in PLANTS}
    log = {}
    for latin, common, names in PLANTS:
        q = f"{common} {latin} composition".replace("×", "").replace("  ", " ")
        page, _, _ = get_text("sources", SEARCH.format(q.replace(" ", "+")))
        ids = list(dict.fromkeys(re.findall(r"PMC\d{6,8}", page)))
        log[latin] = {"query": q, "results": ids, "screened": []}
        seen = set()
        for pid in ids:
            if len(per_plant[latin]) >= MAX_PER_PLANT:
                break
            if pid in EXCLUDED_PMCIDS:
                log[latin]["screened"].append((pid, "excluded: exploratory set"))
                continue
            try:
                title, body, cc, sha, when = _article(pid)
            except Exception as e:  # noqa: BLE001
                log[latin]["screened"].append((pid, f"fetch failed: {e}"))
                continue
            if not cc or not any(n in title.lower() for n in names):
                log[latin]["screened"].append((pid, "ineligible: " + ("no CC licence" if not cc else "title does not name the plant")))
                continue
            n_art = 0
            for s in re.split(r"(?<=[.!?])\s+", body):
                if n_art >= MAX_PER_ARTICLE or len(per_plant[latin]) >= MAX_PER_PLANT:
                    break
                if EXCLUDE.search(s) or not (PRESENT.search(s) or ABSENT.search(s)):
                    continue
                preps = {m for pat, m in PREPS if re.search(pat, s, re.I)}
                if len(preps) != 1:
                    continue
                prep = preps.pop()
                for cpd in _compound_hits(s):
                    key = (cpd, prep)
                    if key in seen or n_art >= MAX_PER_ARTICLE or len(per_plant[latin]) >= MAX_PER_PLANT:
                        continue
                    seen.add(key)
                    n_art += 1
                    per_plant[latin].append({"plant": latin, "compound": cpd, "modelPreparation": prep,
                                             "reported": "low" if ABSENT.search(s) else "present", "pmcid": pid,
                                             "url": PMC.format(pid), "articleTitle": title[:200], "quote": s.strip()[:600],
                                             "articleSha256": sha, "retrievedAt": when})
            log[latin]["screened"].append((pid, f"eligible: {n_art} rows"))
    rows, i = [], 0
    while len(rows) < TARGET and any(per_plant.values()):
        plant = PLANTS[i % len(PLANTS)][0]
        if per_plant[plant]:
            rows.append(per_plant[plant].pop(0))
        i += 1
        if i > 1000:
            break
    df = pd.DataFrame(rows)
    return df, log


def evaluate(cfg: dict) -> dict:
    df, log = collect()
    thr = cfg["literature_check"]
    out_rows = []
    for j, r in enumerate(df.itertuples()):
        p = get_json("pubchem", PUBCHEM.format(r.compound.replace(" ", "%20")))["PropertyTable"]["Properties"][0]
        smi = p.get("IsomericSMILES") or p.get("SMILES")
        d = chem.describe(smi)
        c = M.Compound(p["InChIKey"], d["logP"], d["basicN"], d["heatFlags"], d["volatile"], d["mw"])
        s = M.estimate(c, M.BY_LABEL[r.modelPreparation], cfg, seed_offset=200 + j, sd=M.descriptor_sd()["sd"])
        agree = s["likelihood"] >= thr["present_min"] if r.reported == "present" else s["likelihood"] < thr["absent_max"]
        out_rows.append({**r._asdict(), "pubchemCid": p["CID"], "inchikey": p["InChIKey"], "smiles": smi,
                         "predicted": s["likelihood"], "low": s["low"], "high": s["high"], "agree": bool(agree),
                         "drivers": json.dumps(s["drivers"]), "basis": "ai_curated_literature_reference"})
    res = pd.DataFrame(out_rows).drop(columns=["Index"], errors="ignore")
    CSV.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(CSV, index=False)
    n, k = len(res), int(res.agree.sum()) if len(res) else 0
    out = {"registration": "docs/PREREGISTRATION.md (commit 35b7c0d)", "modelVersion": M.config_version(cfg),
           "rowsFound": n, "agree": k, "byPreparation": res.groupby("modelPreparation").agree.agg(["sum", "count"]).to_dict("index") if n else {},
           "byLabel": res.groupby("reported").agree.agg(["sum", "count"]).to_dict("index") if n else {},
           "screening": log}
    (OUT / "literature_prereg.json").write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False))
    return out
