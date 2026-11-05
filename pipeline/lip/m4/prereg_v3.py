"""Pre-registered paired within-plant check, v3 (docs/PREREGISTRATION_v3.md, registered in commit 7bc28ab).

For two compounds X, Y measured in two preparations P1, P2 of the same plant material in one table, the
double ratio (X1/Y1)/(X2/Y2) cancels plant content, preparation yield and units; the model predicts it
from extraction fractions alone. Outcome: does the model get the sign of ln(double ratio) right?

Implementation clarifications (not deviations):
  - model medians use seed_offset = the preparation's index in the grid (as for the published profiles);
  - LOTUS labels: study-set species from the M3 output; other plants by the same `found in taxon` query on
    every Latin name listed for the plant (as in v2); a label naming several items uses the lowest QID.
basis = ai_curated_literature_reference (provisional). Never pooled with v1, v2 or the exploratory table.
"""
from __future__ import annotations

import html as htmlmod
import itertools
import json
import math
import re
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
from lxml import html as lxml_html

from ..http import get_json, get_text
from ..paths import INTERIM, ROOT
from . import chem
from . import model as M
from .chemnames import Matcher
from .prereg_literature import COMPOUNDS as V1_COMPOUNDS
from .prereg_v2 import EXCLUDED as V2_EXCLUDED
from .prereg_v2 import SOLVENT_LABELS, _lotus_for

OUT = INTERIM / "m4"
CSV = ROOT / "data" / "reference" / "prep_literature_prereg_v3_pairs.csv"
TABLES_CSV = ROOT / "data" / "reference" / "prep_literature_prereg_v3_tables.csv"
JSON = OUT / "literature_prereg_v3.json"
REGISTRATION = "docs/PREREGISTRATION_v3.md (commit 7bc28ab; Amendment 1 in 99e120e)"
BASIS = "ai_curated_literature_reference"
LABEL = "PRE-REGISTERED v3 (paired, within plant) literature check, provisional; AI-written rule and code, not human-curated"
SEARCH = "https://pmc.ncbi.nlm.nih.gov/search/?term={}"
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/{}/"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/property/IsomericSMILES,InChIKey/JSON"

STUDY_SET = ["Artemisia absinthium", "Agrimonia eupatoria", "Crocus sativus", "Symphytum officinale", "Lavandula angustifolia",
             "Ajuga chamaepitys", "Ranunculus ficaria", "Glycyrrhiza glabra", "Melissa officinalis", "Hyssopus officinalis",
             "Pastinaca sativa", "Galium aparine", "Centaurium erythraea", "Chelidonium majus", "Hyoscyamus niger",
             "Raphanus sativus", "Salvia sclarea", "Euphorbia antiquorum", "Papaver somniferum", "Humulus lupulus", "Allium cepa",
             "Coriandrum sativum", "Carum carvi", "Citrullus colocynthis", "Dioscorea communis", "Filipendula ulmaria",
             "Betonica officinalis", "Moricandia arvensis"]
COMMON = {  # v2 title names for the study set
    "Artemisia absinthium": ["wormwood", "absinthe"], "Agrimonia eupatoria": ["agrimony"], "Crocus sativus": ["saffron"],
    "Symphytum officinale": ["comfrey"], "Lavandula angustifolia": ["lavender", "Lavandula officinalis"],
    "Ajuga chamaepitys": ["ground pine", "yellow bugle"], "Ranunculus ficaria": ["lesser celandine", "Ficaria verna"],
    "Glycyrrhiza glabra": ["licorice", "liquorice"], "Melissa officinalis": ["lemon balm"], "Hyssopus officinalis": ["hyssop"],
    "Pastinaca sativa": ["parsnip"], "Galium aparine": ["cleavers"], "Centaurium erythraea": ["centaury", "Centaurium umbellatum"],
    "Chelidonium majus": ["greater celandine"], "Hyoscyamus niger": ["henbane"], "Raphanus sativus": ["radish"],
    "Salvia sclarea": ["clary sage"], "Euphorbia antiquorum": [], "Papaver somniferum": ["opium poppy"],
    "Humulus lupulus": ["hop", "hops"], "Allium cepa": ["onion"], "Coriandrum sativum": ["coriander", "cilantro"],
    "Carum carvi": ["caraway"], "Citrullus colocynthis": ["colocynth"], "Dioscorea communis": ["black bryony", "Tamus communis"],
    "Filipendula ulmaria": ["meadowsweet"], "Betonica officinalis": ["betony", "Stachys officinalis"], "Moricandia arvensis": [],
}
WELL_STUDIED = [
    ("Artemisia annua", ["sweet wormwood"]), ("Matricaria chamomilla", ["chamomile", "Matricaria recutita", "Chamomilla recutita"]),
    ("Mentha × piperita", ["peppermint", "Mentha piperita"]), ("Thymus vulgaris", ["thyme"]), ("Salvia officinalis", ["sage"]),
    ("Salvia rosmarinus", ["rosemary", "Rosmarinus officinalis"]), ("Foeniculum vulgare", ["fennel"]), ("Origanum vulgare", ["oregano"]),
    ("Hypericum perforatum", ["St John's wort"]), ("Calendula officinalis", ["calendula", "marigold"]),
    ("Achillea millefolium", ["yarrow"]), ("Mentha spicata", ["spearmint"]),
]
PLANTS = [(p, COMMON[p]) for p in STUDY_SET] + WELL_STUDIED
Q1 = ('{} (infusion OR decoction OR tea OR "aqueous extract") ("essential oil" OR hydrodistillation OR ethanolic OR methanolic '
      'OR hydroethanolic OR hydroalcoholic) (HPLC OR "LC-MS" OR "GC-MS")')
Q2 = '{} ("essential oil" OR hydrolate OR ethanolic OR methanolic) (infusion OR decoction) composition'
MAX_ARTICLES_PER_PLANT = 3
TIE = math.log(1.25)
FLOOR = 1e-4
B, SEED = 2000, 20261106

# POST-HOC row audit (NOT part of the registered analysis; AI reading, basis ai_post_hoc_audit_unverified)
AUDIT_BASIS = "ai_post_hoc_audit_unverified"
AUDIT = {  # (pmcid, column1 contains) -> note
    ("PMC9504179", "A. glutinosa"): "material is Alnus glutinosa cones, a second species in the same table, not the target plant "
                                    "(still a valid within-material comparison of extraction, but not of Filipendula ulmaria)",
}

COLD = re.compile(r"cold[- ]water|cold infusions?|cold macerat\w*", re.I)
PREPS = [
    (re.compile(r"\binfusions?\b|herbal teas?|\bteas?\b|aqueous|water extracts?|hot water|\bH2O\b", re.I), "hot water infusion (tea)"),
    (re.compile(r"\bdecoctions?\b", re.I), "decoction in water"),
    (re.compile(r"essential oils?|\bEO\b|hydrodistill\w*|steam distill\w*|hydrolates?|hydrosols?", re.I), "distilled water"),
    (re.compile(r"\bethanol\w*|\bEtOH\b|hydroethanolic|hydroalcoholic|tinctures?", re.I), "modern 70% ethanol extract"),
    (re.compile(r"\bmethanol\w*|\bMeOH\b", re.I), "modern methanol extract"),
    (re.compile(r"hexane|petroleum ether", re.I), "low-temperature nonpolar extract (hexane)"),
    (re.compile(r"\bjuices?\b", re.I), "fresh juice"),
]
ND = re.compile(r"^\s*(?:n\.?\s?d\.?|ND|<\s*LO[DQ]|bdl|BDL|tr\.?|traces?|[-–−])\s*[a-z*†‡]{0,2}\s*$", re.I)
AQUEOUS_P = {"cold water infusion", "hot water infusion (tea)", "decoction in water", "fresh juice"}
ALCOHOL_P = {"modern 70% ethanol extract", "modern methanol extract"}


# --- preparation and value parsing ------------------------------------------------------------------

GENERIC = re.compile(r"\b(?:extracts?|samples?|mean|sd|se|rsd|area|relative|content|concentrations?|amounts?|"
                     r"mg|g|kg|µg|μg|ug|ng|ml|l|dw|fw|d\s?w|f\s?w|dry|fresh weight|weight|ppm|ppb|per|of|in|the)\b", re.I)
ALCOHOL = re.compile(r"\bethanol\w*|\bEtOH\b|\bmethanol\w*|\bMeOH\b", re.I)
AQ_WORD = re.compile(r"aqueous|\bwater\b|\bH2O\b", re.I)


def prep_of(label: str) -> tuple[str | None, str]:
    """-> (model preparation or None, label with preparation terms removed).

    Amendment 1 (registered before collection): an alcohol term together with 'aqueous'/'water' is an
    aqueous-alcohol (hydroalcoholic) extract, so the aqueous term is dropped; generic words and units are
    removed from the condition."""
    types, rest = set(), label
    if ALCOHOL.search(rest) and AQ_WORD.search(rest):
        rest = AQ_WORD.sub(" ", rest)
    if COLD.search(rest):
        types.add("cold water infusion")
        rest = COLD.sub(" ", rest)
    for rx, lab in PREPS:
        if rx.search(rest):
            types.add(lab)
            rest = rx.sub(" ", rest)
    rest = re.sub(r"\d+(?:[.,]\d+)?\s*%|\b\d+\s*:\s*\d+\b|\(\s*v\s*/\s*v\s*\)", " ", rest)  # solvent strength, ratios
    cond = re.sub(r"[^a-z0-9µμ]+", " ", rest.lower())
    cond = re.sub(r"\s+", " ", GENERIC.sub(" ", cond)).strip()
    return (types.pop() if len(types) == 1 else None), cond


def value_of(cell: str) -> float | None:
    s = htmlmod.unescape(cell).strip()
    if not s:
        return None
    if ND.match(s):
        return 0.0
    if re.search(r"\d+,\d{1,2}\b", s) and "." not in s:
        s = re.sub(r"(\d+),(\d{1,2})\b", r"\1.\2", s)
    m = re.search(r"(?<![\w.])(\d+(?:\.\d+)?)(?:\s*[eE]([-+]?\d+))?", s)
    if not m:
        return None
    v = float(m.group(1)) * (10 ** int(m.group(2)) if m.group(2) else 1)
    return v


# --- tables --------------------------------------------------------------------------------------------

def _text(el) -> str:
    return re.sub(r"\s+", " ", el.text_content()).strip()


def grid(table) -> tuple[list[list[str]], int]:
    """Expand rowspan/colspan. -> (rows of cell text, number of header rows)."""
    trs = table.xpath(".//tr")
    head = table.xpath(".//thead//tr")
    n_head = len(head) if head else 1
    out: list[list[str]] = []
    pending: dict[tuple[int, int], str] = {}
    for i, tr in enumerate(trs):
        row: list[str] = []
        j = 0
        cells = tr.xpath("./th|./td")
        for c in cells:
            while (i, j) in pending:
                row.append(pending.pop((i, j)))
                j += 1
            t = _text(c)
            cs, rs = int(c.get("colspan", 1) or 1), int(c.get("rowspan", 1) or 1)
            for dc in range(cs):
                row.append(t)
                for dr in range(1, rs):
                    pending[(i + dr, j + dc)] = t
            j += cs
        while (i, j) in pending:
            row.append(pending.pop((i, j)))
            j += 1
        out.append(row)
    w = max((len(r) for r in out), default=0)
    return [r + [""] * (w - len(r)) for r in out], n_head


def read_table(table, matcher: Matcher) -> dict | None:
    """-> {'orientation', 'columns': [(prep, cond, label)], 'values': {compound: [v per column]}} or None."""
    g, nh = grid(table)
    if len(g) <= nh or not g or len(g[0]) < 3:
        return None

    def orient(rows, n_head):
        width = len(rows[0])
        cols = []
        for j in range(1, width):
            label = " ".join(dict.fromkeys(r[j] for r in rows[:n_head] if r[j]))
            p, cond = prep_of(label)
            cols.append((p, cond, label))
        vals = {}
        for r in rows[n_head:]:
            name = matcher.exact_label(r[0]) if r[0] else None
            if name is None or name in vals:
                continue
            vals[name] = [value_of(r[j]) if cols[j - 1][0] else None for j in range(1, width)]
        n_cells = sum(v is not None for vs in vals.values() for v in vs)
        return {"columns": cols, "values": vals, "cells": n_cells}

    a = orient(g, nh)
    a["orientation"] = "A"
    t = [list(x) for x in zip(*g)]  # transpose: header row = first column of g
    b = orient(t, 1) if len(t) > 1 else {"cells": -1}
    b["orientation"] = "B"
    best = a if a["cells"] >= b["cells"] else b
    return best if best["cells"] > 0 else None


def comparable_pairs(t: dict) -> list[tuple[int, int]]:
    cols = t["columns"]
    out = []
    for i, j in itertools.combinations(range(len(cols)), 2):
        (p1, c1, _), (p2, c2, _) = cols[i], cols[j]
        if p1 and p2 and p1 != p2 and c1 == c2:
            n = sum(1 for vs in t["values"].values() if vs[i] is not None and vs[j] is not None)
            if n >= 2:
                out.append((i, j))
    return out


def article_tables(raw: str) -> list:
    cut = min([k for k in (raw.find('class="ref-list'), raw.find('id="ref-list')) if k > 0] or [len(raw)])
    doc = lxml_html.fromstring(raw[:cut])
    return doc.xpath("//table")


# --- compounds and model ---------------------------------------------------------------------------------

def lotus(latin: str, others: list[str], comp: pd.DataFrame, occ: pd.DataFrame) -> pd.DataFrame:
    if latin in STUDY_SET:
        keys = set(occ[occ.acceptedName == latin].inchikey)
        t = comp[comp.inchikey.isin(keys)][["label", "smiles", "inchikey", "wikidataId"]].rename(columns={"wikidataId": "qid"})
    else:
        t = _lotus_for([latin] + [o for o in others if o[:1].isupper()])
    t = t[(t.label.str.len() >= 5) & (~t.label.str.lower().isin(SOLVENT_LABELS))].copy()
    t["qnum"] = t.qid.astype(str).str.extract(r"(\d+)$")[0].astype(int)
    return t.sort_values("qnum").drop_duplicates("label")


class Model:
    def __init__(self, cfg: dict):
        self.cfg, self.cache, self.struct = cfg, {}, {}
        self.idx = {p.label: i for i, p in enumerate(M.GRID)}

    def structure(self, name: str, lot: pd.DataFrame) -> tuple[str, str] | None:
        if name in self.struct:
            return self.struct[name]
        row = lot[lot.label == name]
        if len(row):
            s = (row.iloc[0].smiles, row.iloc[0].inchikey)
        else:
            try:
                p = get_json("pubchem", PUBCHEM.format(quote_plus(name).replace("+", "%20")))["PropertyTable"]["Properties"][0]
                s = (p.get("IsomericSMILES") or p.get("SMILES"), p["InChIKey"])
            except Exception:  # noqa: BLE001 - no structure: dropped and counted
                s = None
        self.struct[name] = s
        return s

    def median(self, name: str, lot: pd.DataFrame, prep: str) -> float | None:
        st = self.structure(name, lot)
        if st is None:
            return None
        key = (st[1], prep)
        if key not in self.cache:
            d = chem.describe(st[0])
            if d is None:
                self.cache[key] = None
            else:
                c = M.Compound(st[1], d["logP"], d["basicN"], d["heatFlags"], d["volatile"], d["mw"])
                self.cache[key] = M.simulate(c, M.BY_LABEL[prep], self.cfg, seed_offset=self.idx[prep])["likelihood"]
        return self.cache[key]


def contrast(p1: str, p2: str) -> str:
    s = {p1, p2}
    if s <= AQUEOUS_P:
        return "aqueous vs aqueous"
    if s & AQUEOUS_P and "distilled water" in s:
        return "aqueous vs distillation"
    if s & AQUEOUS_P and s & ALCOHOL_P:
        return "aqueous vs alcohol"
    if s & ALCOHOL_P and "distilled water" in s:
        return "alcohol vs distillation"
    return "other"


def score_table(t: dict, model: Model, lot: pd.DataFrame, meta: dict) -> tuple[list[dict], dict]:
    rows, stats = [], {"pairsConsidered": 0, "skippedUninformative": 0, "noClearDifference": 0, "noStructure": 0}
    for i, j in comparable_pairs(t):
        p1, p2 = t["columns"][i][0], t["columns"][j][0]
        v = {n: (vs[i], vs[j]) for n, vs in t["values"].items() if vs[i] is not None and vs[j] is not None}
        pos1 = [a for a, _ in v.values() if a > 0]
        pos2 = [b for _, b in v.values() if b > 0]
        if not pos1 or not pos2:
            continue
        s1, s2 = min(pos1) / 2, min(pos2) / 2
        for x, y in itertools.combinations(sorted(v), 2):
            stats["pairsConsidered"] += 1
            (x1, x2), (y1, y2) = v[x], v[y]
            if (x1 == 0 and y1 == 0) or (x2 == 0 and y2 == 0) or (x1 == 0 and x2 == 0) or (y1 == 0 and y2 == 0):
                stats["skippedUninformative"] += 1
                continue
            x1, y1 = x1 or s1, y1 or s1
            x2, y2 = x2 or s2, y2 or s2
            d_obs = math.log(x1 / y1) - math.log(x2 / y2)
            if abs(d_obs) < TIE:
                stats["noClearDifference"] += 1
                continue
            L = [model.median(n, lot, p) for n, p in ((x, p1), (y, p1), (x, p2), (y, p2))]
            if any(m is None for m in L):
                stats["noStructure"] += 1
                continue
            lx1, ly1, lx2, ly2 = (max(m, FLOOR) for m in L)
            d_pred = math.log(lx1 / ly1) - math.log(lx2 / ly2)
            abstain = abs(d_pred) < TIE
            rows.append({**meta, "prep1": p1, "prep2": p2, "contrast": contrast(p1, p2), "compoundX": x, "compoundY": y,
                         "x1": v[x][0], "y1": v[y][0], "x2": v[x][1], "y2": v[y][1], "deltaObs": round(d_obs, 4),
                         "predX1": L[0], "predY1": L[1], "predX2": L[2], "predY2": L[3], "deltaPred": round(d_pred, 4),
                         "abstain": abstain, "agree": (None if abstain else bool(np.sign(d_obs) == np.sign(d_pred))),
                         "column1": t["columns"][i][2], "column2": t["columns"][j][2]})
    return rows, stats


# --- collection --------------------------------------------------------------------------------------------

def _title_hit(title: str, names: list[str]) -> bool:
    tl = title.lower()
    return any(re.search(r"(?<![\w-])" + re.escape(n.lower()) + r"(?![\w-])", tl) for n in names)


def _excluded() -> set[str]:
    v2 = pd.read_csv(ROOT / "data" / "reference" / "prep_literature_prereg_v2.csv")
    return set(V2_EXCLUDED) | set(v2.pmcid)


def collect(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    comp = pd.read_parquet(INTERIM / "m3" / "compounds.parquet")
    comp = comp[comp.status == "ok"].dropna(subset=["label", "smiles"])
    occ = pd.read_parquet(INTERIM / "m3" / "occurrences.parquet")
    excl = _excluded()
    model = Model(cfg)
    pair_rows, table_rows, log = [], [], {}
    for latin, others in PLANTS:
        ql = latin.replace("× ", "").replace("×", "")
        ids = []
        for q in (Q1.format(ql), Q2.format(ql)):
            page, _, _ = get_text("sources", SEARCH.format(quote_plus(q)))
            ids += [i for i in dict.fromkeys(re.findall(r"PMC\d{6,8}", page)) if i not in ids]
        lot = lotus(latin, others, comp, occ)
        names = {s: n for n, syns in V1_COMPOUNDS.items() for s in syns}
        names.update({lab: lab for lab in lot.label})
        matcher = Matcher(names)
        tnames = [latin, ql] + others
        log[latin] = {"results": ids, "lotusLabels": int(len(lot)), "screened": []}
        n_ok = 0
        for pid in ids:
            if n_ok >= MAX_ARTICLES_PER_PLANT:
                break
            if pid in excl:
                log[latin]["screened"].append((pid, "excluded: used in an earlier check"))
                continue
            try:
                raw, sha, when = get_text("sources", PMC.format(pid))
            except Exception as e:  # noqa: BLE001
                log[latin]["screened"].append((pid, f"fetch failed: {type(e).__name__}"))
                continue
            m = re.search(r"<title>(.*?)</title>", raw, re.S)
            title = htmlmod.unescape(m.group(1)).replace(" - PMC", "").strip() if m else ""
            lm = re.search(r"creativecommons\.org/licenses/([a-z-]+)/(\d\.\d)", raw)
            if not lm:
                log[latin]["screened"].append((pid, "ineligible: no CC licence"))
                continue
            if not _title_hit(title, tnames):
                log[latin]["screened"].append((pid, "ineligible: title does not name the plant"))
                continue
            eligible = []
            for k, tab in enumerate(article_tables(raw)):
                t = read_table(tab, matcher)
                if t and comparable_pairs(t):
                    eligible.append((k, t))
            if not eligible:
                log[latin]["screened"].append((pid, "ineligible: no eligible table"))
                continue
            n_ok += 1
            meta0 = {"plant": latin, "pmcid": pid, "url": PMC.format(pid), "articleTitle": title[:200],
                     "licence": f"CC {lm.group(1).upper()} {lm.group(2)}", "articleSha256": sha, "retrievedAt": when}
            art_pairs = 0
            for k, t in eligible:
                rows, st = score_table(t, model, lot, {**meta0, "table": k})
                pair_rows += rows
                art_pairs += len(rows)
                table_rows.append({**meta0, "table": k, "orientation": t["orientation"], "compounds": len(t["values"]),
                                   "preparationColumns": "; ".join(f"{c[2]} -> {c[0]}" for c in t["columns"] if c[0]),
                                   "pairsScoredOrAbstained": len(rows), **st})
            log[latin]["screened"].append((pid, f"eligible: {len(eligible)} tables, {art_pairs} pairs"))
    return pd.DataFrame(pair_rows), pd.DataFrame(table_rows), log


# --- analysis ------------------------------------------------------------------------------------------------

def analyse(pairs: pd.DataFrame) -> dict:
    if not len(pairs):
        return {"articles": 0, "note": "no eligible pairs"}
    sc = pairs[~pairs.abstain]
    per = sc.groupby("pmcid").agree.mean()
    rng = np.random.default_rng(SEED)
    arts = per.index.to_numpy()
    boots = [per.loc[rng.choice(arts, len(arts), replace=True)].mean() for _ in range(B)] if len(arts) else []
    lo, hi = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))) if boots else (None, None)
    mean = float(per.mean()) if len(per) else None
    verdict = ("not computed" if mean is None else "better than chance" if lo > 0.5 else
               "worse than chance" if hi < 0.5 else "not distinguishable from chance")
    by_c = {c: {"agree": int(g.agree.sum()), "scored": int(len(g)), "articles": int(g.pmcid.nunique()),
                "rate": round(float(g.agree.mean()), 4)} for c, g in sc.groupby("contrast")}
    return {"articles": int(pairs.pmcid.nunique()), "articlesScored": int(len(per)), "pairs": int(len(pairs)),
            "scored": int(len(sc)), "abstained": int(pairs.abstain.sum()),
            "primary": {"meanPerArticleAgreement": round(mean, 4) if mean is not None else None,
                        "ci95": [round(lo, 4), round(hi, 4)] if lo is not None else None, "bootstrap": {"B": B, "seed": SEED},
                        "verdict": verdict},
            "pooledPairAgreement": {"agree": int(sc.agree.sum()), "scored": int(len(sc)),
                                    "rate": round(float(sc.agree.mean()), 4) if len(sc) else None},
            "perArticle": {k: round(float(v), 4) for k, v in per.items()},
            "byContrast": by_c, "plants": int(pairs.plant.nunique())}


def evaluate(cfg: dict) -> dict:
    pairs, tables, log = collect(cfg)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(CSV, index=False)
    tables.to_csv(TABLES_CSV, index=False)
    res = analyse(pairs)
    notes = []
    for (pid, frag), note in AUDIT.items():
        hit = pairs[(pairs.pmcid == pid) & pairs.column1.str.contains(frag, regex=False)] if len(pairs) else pairs
        if len(hit):
            notes.append({"pmcid": pid, "pairs": int(len(hit)), "note": note})
    res["postHocAudit"] = {"basis": AUDIT_BASIS, "label": "POST-HOC note by the AI (not registered; not human-verified)", "notes": notes,
                           "largestArticleShareOfScoredPairs": (round(float(pairs[~pairs.abstain].pmcid.value_counts(normalize=True).iloc[0]), 4)
                                                                if len(pairs) and (~pairs.abstain).any() else None)}
    excluded = {k: int(tables[k].sum()) for k in ("pairsConsidered", "skippedUninformative", "noClearDifference", "noStructure")} if len(tables) else {}
    out = {"registration": REGISTRATION, "label": LABEL, "basis": BASIS, "modelVersion": M.config_version(cfg),
           "rule": {"tie": "ln 1.25", "floor": FLOOR, "maxArticlesPerPlant": MAX_ARTICLES_PER_PLANT},
           "tables": int(len(tables)), "pairCounts": excluded, **res, "screening": log}
    OUT.mkdir(parents=True, exist_ok=True)
    JSON.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False))
    return out
