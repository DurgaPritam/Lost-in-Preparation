"""Pre-registered water-preparation check, v2 (docs/PREREGISTRATION_v2.md, registered in commit 9c36f68).

Implements the registered rule mechanically. Implementation clarifications (not deviations):
  - LOTUS labels for the 30 study-set species come from the M3 output (data/interim/m3, produced by
    the `found in taxon` query); for the 6 well-studied plants the same query is run here on every
    Latin name listed for the plant;
  - when a LOTUS label names several Wikidata items, the item with the lowest QID is used;
  - "a shorter aglycone name inside a longer matched name does not count" is applied generally:
    a compound match whose span lies inside a longer compound match is dropped.
basis = ai_curated_literature_reference (provisional). Never pooled with v1 or the exploratory table.
"""
from __future__ import annotations

import html
import json
import math
import re

import pandas as pd

from ..http import get_json, get_text
from ..paths import INTERIM, ROOT
from . import chem
from . import model as M
from .prereg_literature import COMPOUNDS as V1_COMPOUNDS

OUT = INTERIM / "m4"
CSV = ROOT / "data" / "reference" / "prep_literature_prereg_v2.csv"
JSON = OUT / "literature_prereg_v2.json"
REGISTRATION = "docs/PREREGISTRATION_v2.md (commit 9c36f68)"
SEARCH = "https://pmc.ncbi.nlm.nih.gov/search/?term={}"
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/{}/"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/property/IsomericSMILES,InChIKey/JSON"
BASIS = "ai_curated_literature_reference"
LABEL = "PRE-REGISTERED v2 (aqueous preparations) literature check, provisional; AI-written rule and code, not human-curated"

PLANTS = [  # (Latin name, other names for the title test)
    ("Artemisia absinthium", ["wormwood", "absinthe"]), ("Agrimonia eupatoria", ["agrimony"]),
    ("Crocus sativus", ["saffron"]), ("Symphytum officinale", ["comfrey"]),
    ("Lavandula angustifolia", ["lavender", "Lavandula officinalis"]), ("Ajuga chamaepitys", ["ground pine", "yellow bugle"]),
    ("Ranunculus ficaria", ["lesser celandine", "Ficaria verna"]), ("Glycyrrhiza glabra", ["licorice", "liquorice"]),
    ("Melissa officinalis", ["lemon balm"]), ("Hyssopus officinalis", ["hyssop"]), ("Pastinaca sativa", ["parsnip"]),
    ("Galium aparine", ["cleavers"]), ("Centaurium erythraea", ["centaury", "Centaurium umbellatum"]),
    ("Chelidonium majus", ["greater celandine"]), ("Hyoscyamus niger", ["henbane"]), ("Raphanus sativus", ["radish"]),
    ("Laser trilobum", []), ("Salvia sclarea", ["clary sage"]), ("Euphorbia antiquorum", []),
    ("Papaver somniferum", ["opium poppy"]), ("Humulus lupulus", ["hop", "hops"]), ("Allium cepa", ["onion"]),
    ("Coriandrum sativum", ["coriander", "cilantro"]), ("Carum carvi", ["caraway"]), ("Citrullus colocynthis", ["colocynth"]),
    ("Cotinus coggygria", ["smoke tree", "smoketree"]), ("Dioscorea communis", ["black bryony", "Tamus communis"]),
    ("Filipendula ulmaria", ["meadowsweet"]), ("Betonica officinalis", ["betony", "Stachys officinalis"]),
    ("Moricandia arvensis", []),
    ("Artemisia annua", ["sweet wormwood"]),
    ("Matricaria chamomilla", ["chamomile", "Matricaria recutita", "Chamomilla recutita"]),
    ("Mentha × piperita", ["peppermint", "Mentha piperita"]), ("Thymus vulgaris", ["thyme"]),
    ("Salvia officinalis", ["sage"]), ("Salvia rosmarinus", ["rosemary", "Rosmarinus officinalis"]),
]
STUDY_SET_N = 30
EXCLUDED = {"PMC2995283", "PMC13074686", "PMC7587570", "PMC10217939", "PMC11944828",
            "PMC10180401", "PMC10707927", "PMC10819686", "PMC12309076", "PMC13290042", "PMC5622382",
            "PMC6843575", "PMC8398316", "PMC9099978"}
AQ = '(infusion OR decoction OR tea OR "aqueous extract" OR juice)'
ANALYTICAL = re.compile(r"\bU?HPLC\b|\bUPLC\b|LC[-–]MS|GC[-–]MS|chromatograph|mass spectromet|\bNMR\b", re.I)
SOLVENT_LABELS = {"water", "ethanol", "methanol", "acetone", "hexane", "chloroform", "ethyl acetate", "acetonitrile",
                  "acetic acid", "formic acid", "dimethyl sulfoxide"}
COLD = re.compile(r"cold[- ]water|cold infusions?|cold[- ]brew\w*|cold macerat\w*", re.I)
PREPS = [
    (re.compile(r"\binfusions?\b|herbal teas?|\bteas?\b|aqueous extracts?|water extracts?|hot water", re.I), "hot water infusion (tea)"),
    (re.compile(r"\bdecoctions?\b", re.I), "decoction in water"),
    (re.compile(r"\bjuices?\b", re.I), "fresh juice"),
]
ABSENT = re.compile(r"not detected|n\.d\.|not found|not present|undetect\w*|below the (?:limit|detection)|\babsent\b|\btraces?\b|"
                    r"low (?:concentration|amount|level|content)s?|lacking|free of|did not contain|(?:was|were) not extracted|"
                    r"poorly extracted|negligible", re.I)
PRESENT = re.compile(r"\bmain\b|\bmajor\b|predominant|principal|dominant|rich in|contain|identified|detected|\bfound\b|%|\bmg\b|"
                     r"quantified|abundant|highest", re.I)
EXCLUDE = re.compile(r"essential oil|volatile oil|\boil\b|distill|tincture|ethanol|methanol|hydroalcoholic|hydroethanolic|acetone|"
                     r"hexane|supercritical|\bCO2\b|chloroform|ethyl acetate|dichloromethane|petroleum ether|butanol|"
                     r"fraction|partition|commercial|synthetic|derivative|total phenolic|activity|inhibit|IC50|\bMIC\b|"
                     r"standard|calibration|spiked|recovery", re.I)
MAX_PER_ARTICLE, MAX_PER_PLANT_LABEL, QUOTA = 2, 2, 15
VARIANT = {"name": "water-partition-slope", "k_fixed": math.log(10), "h_sd": 0.8374}

# POST-HOC row audit (NOT part of the registered analysis): the AI's reading of each collected row,
# keyed by (pmcid, plant, compound). basis = ai_post_hoc_audit_unverified. Reported beside, never instead of,
# the registered result. "misread" = the mechanical rule picked the wrong compound, plant or context.
AUDIT_BASIS = "ai_post_hoc_audit_unverified"
AUDIT = {
    ("PMC11819889", "Agrimonia eupatoria", "apigenin"): ("misread", "sentence reports apigenin 7-O-glucoside; the v1 synonym list lacks the spaced spelling, so the aglycone matched"),
    ("PMC5603879", "Glycyrrhiza glabra", "phenol"): ("misread", "'total phenol content' of rose-petal teas; not a compound report and not about licorice"),
    ("PMC11171837", "Raphanus sativus", "sucrose"): ("misread", "sucrose added in a kombucha recipe; not a constituent extracted from the plant"),
    ("PMC12715987", "Carum carvi", "rutin"): ("misread", "sentence is about chamomile aqueous extracts, cited inside a caraway article"),
}


# --- compounds ------------------------------------------------------------------------------

def _lotus_for(names: list[str]) -> pd.DataFrame:
    """-> label, smiles, inchikey for every LOTUS compound with an English label (same query as M3)."""
    from ..m3.compounds import fetch, standardise
    rows = []
    for b in fetch(names):
        if b.get("label") and (b.get("iso") or b.get("smiles")):
            smi, key, status = standardise(b.get("iso") or b["smiles"])
            if status == "ok":
                rows.append({"label": b["label"], "smiles": smi, "inchikey": key, "qid": b["compound"].rsplit("/", 1)[-1]})
    return pd.DataFrame(rows, columns=["label", "smiles", "inchikey", "qid"])


def lotus_tables() -> dict[str, pd.DataFrame]:
    comp = pd.read_parquet(INTERIM / "m3" / "compounds.parquet")
    occ = pd.read_parquet(INTERIM / "m3" / "occurrences.parquet")
    comp = comp[comp.status == "ok"].dropna(subset=["label", "smiles"])
    out = {}
    for i, (latin, others) in enumerate(PLANTS):
        if i < STUDY_SET_N:
            keys = set(occ[occ.acceptedName == latin].inchikey)
            t = comp[comp.inchikey.isin(keys)][["label", "smiles", "inchikey", "wikidataId"]].rename(columns={"wikidataId": "qid"})
        else:
            latin_names = [latin] + [o for o in others if o[:1].isupper()]
            t = _lotus_for(latin_names)
        t = t[(t.label.str.len() >= 5) & (~t.label.str.lower().isin(SOLVENT_LABELS))].copy()
        t["qnum"] = t.qid.astype(str).str.extract(r"(\d+)$")[0].astype(int)
        t["key"] = t.label.str.lower()
        out[latin] = t.sort_values("qnum").drop_duplicates("key")[["key", "label", "smiles", "inchikey"]]
    return out


def compound_matcher(lotus: pd.DataFrame):
    names: dict[str, tuple[str, str | None]] = {}  # synonym (lower) -> (compound name, source)
    for name, syns in V1_COMPOUNDS.items():
        for s in syns:
            names.setdefault(s.lower(), (name, "v1"))
    for r in lotus.itertuples():
        names.setdefault(r.key, (r.label, "lotus"))
    pats = sorted(names, key=len, reverse=True)
    rx = re.compile("|".join(r"(?<![\w-])" + re.escape(p) + r"(?![\w-])" for p in pats), re.I) if pats else None

    def hits(sentence: str) -> list[tuple[str, str]]:
        if rx is None:
            return []
        spans = []
        for p in pats:  # all matches of every name, then drop spans inside a longer match
            for m in re.finditer(r"(?<![\w-])" + re.escape(p) + r"(?![\w-])", sentence, re.I):
                spans.append((m.start(), m.end(), p))
        if not spans:
            return []
        keep = [s for s in spans if not any(o[0] <= s[0] and s[1] <= o[1] and (o[1] - o[0]) > (s[1] - s[0]) for o in spans)]
        out = []
        for _, _, p in sorted(keep):
            if names[p] not in out:
                out.append(names[p])
        return out

    def fast_reject(sentence: str) -> bool:
        return rx is None or rx.search(sentence) is None

    return hits, fast_reject


# --- articles ---------------------------------------------------------------------------------

def _article(pmcid: str):
    raw, sha, when = get_text("sources", PMC.format(pmcid))
    m = re.search(r"<title>(.*?)</title>", raw, re.S)
    title = html.unescape(m.group(1)).replace(" - PMC", "").strip() if m else ""
    cc = "creativecommons.org/licenses" in raw
    lm = re.search(r"creativecommons\.org/licenses/([a-z-]+)/(\d\.\d)", raw)
    licence = f"CC {lm.group(1).upper()} {lm.group(2)}" if lm else ("Creative Commons (version not parsed)" if cc else "none stated")
    cut = min([i for i in (raw.find('class="ref-list'), raw.find('id="ref-list')) if i > 0] or [len(raw)])
    body = re.sub(r"<table\b.*?</table>", " ", raw[:cut], flags=re.S | re.I)
    body = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)))
    return title, body, cc, sha, when, licence


def _title_names(latin: str, others: list[str]) -> list[str]:
    names = [latin, latin.replace("× ", "").replace("×", "")] + others
    return [n.lower() for n in names]


def _prep_of(s: str) -> str | None:
    types = set()
    rest = s
    if COLD.search(rest):
        types.add("cold water infusion")
        rest = COLD.sub(" ", rest)
    for rx, label in PREPS:
        if rx.search(rest):
            types.add(label)
    return types.pop() if len(types) == 1 else None


def collect() -> tuple[pd.DataFrame, dict]:
    lotus = lotus_tables()
    per_plant: dict[str, dict[str, list[dict]]] = {p[0]: {"present": [], "low": []} for p in PLANTS}
    log = {}
    for latin, others in PLANTS:
        q_latin = latin.replace("× ", "").replace("×", "")
        q2 = f'{q_latin} {AQ} ("not detected" OR "below the limit")'
        q1 = f"{q_latin} {AQ}"
        ids2 = list(dict.fromkeys(re.findall(r"PMC\d{6,8}", get_text("sources", SEARCH.format(_q(q2)))[0])))
        ids1 = list(dict.fromkeys(re.findall(r"PMC\d{6,8}", get_text("sources", SEARCH.format(_q(q1)))[0])))
        order = ids2 + [i for i in ids1 if i not in ids2]
        hits, fast_reject = compound_matcher(lotus[latin])
        tnames = _title_names(latin, others)
        log[latin] = {"queries": [q2, q1], "results": order, "lotusLabels": int(len(lotus[latin])), "screened": []}
        seen = set()
        bucket = per_plant[latin]
        for pid in order:
            if all(len(bucket[k]) >= MAX_PER_PLANT_LABEL for k in bucket):
                break
            if pid in EXCLUDED:
                log[latin]["screened"].append((pid, "excluded: exploratory or v1 set"))
                continue
            try:
                title, body, cc, sha, when, licence = _article(pid)
            except Exception as e:  # noqa: BLE001
                log[latin]["screened"].append((pid, f"fetch failed: {type(e).__name__}"))
                continue
            tl = title.lower()
            if not cc:
                log[latin]["screened"].append((pid, "ineligible: no CC licence"))
                continue
            if not any(re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", tl) for n in tnames):
                log[latin]["screened"].append((pid, "ineligible: title does not name the plant"))
                continue
            if not ANALYTICAL.search(body):
                log[latin]["screened"].append((pid, "ineligible: no analytical-chemistry term"))
                continue
            n_art = 0
            for s in re.split(r"(?<=[.!?])\s+", body):
                if n_art >= MAX_PER_ARTICLE:
                    break
                if len(s) > 600 or EXCLUDE.search(s) or fast_reject(s):
                    continue
                if not (PRESENT.search(s) or ABSENT.search(s)):
                    continue
                prep = _prep_of(s)
                if prep is None:
                    continue
                label = "low" if ABSENT.search(s) else "present"
                for cname, csrc in hits(s):
                    key = (cname.lower(), prep)
                    if key in seen or n_art >= MAX_PER_ARTICLE or len(bucket[label]) >= MAX_PER_PLANT_LABEL:
                        continue
                    seen.add(key)
                    n_art += 1
                    bucket[label].append({"plant": latin, "compound": cname, "compoundSource": csrc, "modelPreparation": prep,
                                          "reported": label, "pmcid": pid, "url": PMC.format(pid), "articleTitle": title[:200], "licence": licence,
                                          "quote": s.strip(), "articleSha256": sha, "retrievedAt": when})
            log[latin]["screened"].append((pid, f"eligible: {n_art} rows"))
    rows = []
    for label in ("present", "low"):
        got, i = 0, 0
        while got < QUOTA and any(per_plant[p][label] for p in per_plant):
            plant = PLANTS[i % len(PLANTS)][0]
            if per_plant[plant][label]:
                rows.append(per_plant[plant][label].pop(0))
                got += 1
            i += 1
    return pd.DataFrame(rows), {"screening": log, "lotus": lotus}


def _q(q: str) -> str:
    from urllib.parse import quote_plus
    return quote_plus(q)


# --- evaluation ------------------------------------------------------------------------------

def _structure(r, lotus: dict[str, pd.DataFrame]) -> tuple[str, str, int | None]:
    if r.compoundSource == "lotus":
        t = lotus[r.plant]
        m = t[t.key == r.compound.lower()].iloc[0]
        return m.smiles, m.inchikey, None
    p = get_json("pubchem", PUBCHEM.format(r.compound.replace(" ", "%20")))["PropertyTable"]["Properties"][0]
    return p.get("IsomericSMILES") or p.get("SMILES"), p["InChIKey"], p["CID"]


def _agree(reported: str, x: float, thr: dict) -> bool:
    return x >= thr["present_min"] if reported == "present" else x < thr["absent_max"]


def _summ(df: pd.DataFrame, col: str) -> dict:
    from ..m2.evaluate import wilson
    out = {}
    n, k = len(df), int(df[col].sum()) if len(df) else 0
    lo, hi = wilson(k, n) if n else (None, None)
    out["overall"] = {"agree": k, "n": n, "rate": round(k / n, 4) if n else None, "ci": [round(lo, 4), round(hi, 4)] if n else None}
    for lab in ("present", "low"):
        d = df[df.reported == lab]
        n2, k2 = len(d), int(d[col].sum()) if len(d) else 0
        lo2, hi2 = wilson(k2, n2) if n2 else (None, None)
        out[lab] = {"agree": k2, "n": n2, "rate": round(k2 / n2, 4) if n2 else None,
                    "ci": [round(lo2, 4), round(hi2, 4)] if n2 else None}
    out["byPreparation"] = {p: {"agree": int(g[col].sum()), "n": len(g)} for p, g in df.groupby("modelPreparation")} if n else {}
    return out


def _audit(res: pd.DataFrame) -> dict:
    if not len(res):
        return {}
    labels = [AUDIT.get((r.pmcid, r.plant, r.compound), ("valid", ""))[0] for r in res.itertuples()]
    a = res.assign(audit=labels)
    valid = a[a.audit == "valid"]
    return {"basis": AUDIT_BASIS, "label": "POST-HOC row audit by the AI (not registered; not human-verified)",
            "counts": a.audit.value_counts().to_dict(),
            "misread": [{"plant": p, "compound": c, "pmcid": i, "reason": AUDIT[(i, p, c)][1]} for (i, p, c) in AUDIT
                        if ((a.pmcid == i) & (a.plant == p) & (a.compound == c)).any()],
            "validRowsPrimary": _summ(valid, "agree"), "validRowsVariant": _summ(valid, "variantAgree")}


def evaluate(cfg: dict) -> dict:
    df, extra = collect()
    lotus = extra["lotus"]
    thr = cfg["literature_check"]
    rows = []
    for j, r in enumerate(df.itertuples()):
        smi, key, cid = _structure(r, lotus)
        d = chem.describe(smi)
        c = M.Compound(key, d["logP"], d["basicN"], d["heatFlags"], d["volatile"], d["mw"])
        prep = M.BY_LABEL[r.modelPreparation]
        s = M.estimate(c, prep, cfg, seed_offset=300 + j, sd=M.descriptor_sd()["sd"])
        v = M.simulate(c, prep, cfg, seed_offset=300 + j, k_fixed=VARIANT["k_fixed"], h_sd=VARIANT["h_sd"])
        rows.append({**{k2: v2 for k2, v2 in r._asdict().items() if k2 != "Index"}, "pubchemCid": cid, "inchikey": key, "smiles": smi,
                     "logP": d["logP"], "predicted": s["likelihood"], "low": s["low"], "high": s["high"],
                     "agree": bool(_agree(r.reported, s["likelihood"], thr)), "drivers": json.dumps(s["drivers"]),
                     "variantPredicted": v["likelihood"], "variantLow": v["low"], "variantHigh": v["high"],
                     "variantAgree": bool(_agree(r.reported, v["likelihood"], thr)), "basis": BASIS})
    res = pd.DataFrame(rows)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(CSV, index=False)
    out = {"registration": REGISTRATION, "label": LABEL, "basis": BASIS, "modelVersion": M.config_version(cfg),
           "thresholds": thr, "quota": {"present": QUOTA, "low": QUOTA},
           "found": {lab: int((res.reported == lab).sum()) if len(res) else 0 for lab in ("present", "low")},
           "primary": _summ(res, "agree") if len(res) else {},
           "secondaryVariant": {**{k2: VARIANT[k2] for k2 in VARIANT}, "evaluatedOn": "v2 rows only",
                                **(_summ(res, "variantAgree") if len(res) else {})},
           "postHocAudit": _audit(res),
           "screening": extra["screening"]}
    OUT.mkdir(parents=True, exist_ok=True)
    JSON.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False))
    return out
