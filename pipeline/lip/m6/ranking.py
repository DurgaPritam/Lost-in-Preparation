"""M6 hypothesis ranking rule: rank only on profile gaps that hold across the uncertainty range.

A hypothesis compares a species' FAITHFUL preparation (as the recipe made it) with the MODERN preparation
a study used. Its profile gap = 1 - cosine similarity of the two predicted compound profiles (equal
weights: LOTUS has no abundance data). A gap computed from medians alone can be driven by compounds whose
likelihood is barely constrained. The ranking therefore uses the gap's DISTRIBUTION:

  1. Coupled draws. For each compound, the Monte Carlo draws in the faithful and the modern preparation
     share one descriptor-error draw (a compound's logP error is the same in both); descriptor error is
     Normal with SD from the Crippen MAE (m4.model.descriptor_sd). Draw d gives gap_d.
  2. Wide compounds cannot drive the gap (HEURISTIC): a compound whose reported 5th–95th range is wider
     than WIDTH_MAX (0.8 of the 0–1 scale) in either preparation is left out of both profile vectors.
  3. Ranking key: the gap's 5th percentile (the gap that holds in 95% of draws), descending; ties broken by
     P(gap > TAU) (TAU = 0.2, HEURISTIC), then by the median gap. The median-gap ranking is reported only
     for comparison.
  4. A candidate with fewer than MIN_COMPOUNDS usable compounds is not ranked (`rank` empty, reason given).

Ranks are hypotheses worth re-testing, never claims that a preparation works.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..m4 import chem
from ..m4 import model as M
from ..paths import INTERIM

OUT = INTERIM / "m6"
WIDTH_MAX = 0.8
TAU = 0.2
MIN_COMPOUNDS = 5
RULE = (f"rank by the 5th percentile of the profile gap over coupled Monte Carlo draws (descriptor error included); "
        f"ties: P(gap > {TAU}), then median gap; compounds with a 5th–95th range wider than {WIDTH_MAX} in either "
        f"preparation are excluded (heuristic); at least {MIN_COMPOUNDS} usable compounds")


@dataclass(frozen=True)
class Candidate:
    speciesId: str
    acceptedName: str
    faithful: str     # model preparation label
    modern: str       # model preparation label


def _noise_seed(inchikey: str) -> int:
    return int(hashlib.sha256(inchikey.encode()).hexdigest()[:8], 16)


class Draws:
    """Per-compound draw cache: (inchikey, prep) -> (summary, draws)."""

    def __init__(self, cfg: dict, sd: float):
        self.cfg, self.sd, self.cache = cfg, sd, {}
        self.idx = {p.label: i for i, p in enumerate(M.GRID)}

    def get(self, c: M.Compound, prep: str):
        key = (c.inchikey, prep)
        if key not in self.cache:
            p = M.BY_LABEL[prep]
            s = M.estimate(c, p, self.cfg, seed_offset=self.idx[prep], sd=self.sd)  # reported range (for the width rule)
            _, d = M.simulate(c, p, self.cfg, seed_offset=self.idx[prep], h_sd=self.sd,
                              noise_seed=_noise_seed(c.inchikey), return_draws=True)
            self.cache[key] = (s, d)
        return self.cache[key]


def _gap(f: np.ndarray, m: np.ndarray) -> np.ndarray:
    """1 - cosine similarity per draw; f, m: (compounds, draws)."""
    num = (f * m).sum(0)
    den = np.sqrt((f * f).sum(0) * (m * m).sum(0))
    with np.errstate(invalid="ignore", divide="ignore"):
        cos = np.where(den > 0, num / den, 1.0)
    return 1.0 - np.clip(cos, -1, 1)


def score(cand: Candidate, compounds: list[M.Compound], draws: Draws) -> dict:
    keep, wide = [], 0
    for c in compounds:
        sf, df = draws.get(c, cand.faithful)
        sm, dm = draws.get(c, cand.modern)
        if (sf["high"] - sf["low"]) > WIDTH_MAX or (sm["high"] - sm["low"]) > WIDTH_MAX:
            wide += 1
            continue
        keep.append((c, sf, sm, df, dm))
    base = {**cand.__dict__, "compounds": len(compounds), "compoundsUsed": len(keep), "compoundsExcludedWide": wide}
    if len(keep) < MIN_COMPOUNDS:
        return {**base, "gapMedianOfMedians": None, "gapP5": None, "gapP50": None, "gapP95": None, "pGapAboveTau": None,
                "notRanked": f"fewer than {MIN_COMPOUNDS} compounds with a range narrower than {WIDTH_MAX}"}
    F = np.vstack([k[3] for k in keep])
    Mm = np.vstack([k[4] for k in keep])
    g = _gap(F, Mm)
    fm = np.array([k[1]["likelihood"] for k in keep])
    mm = np.array([k[2]["likelihood"] for k in keep])
    naive = float(_gap(fm[:, None], mm[:, None])[0])
    q5, q50, q95 = np.percentile(g, [5, 50, 95])
    return {**base, "gapMedianOfMedians": round(naive, 4), "gapP5": round(float(q5), 4), "gapP50": round(float(q50), 4),
            "gapP95": round(float(q95), 4), "pGapAboveTau": round(float((g > TAU).mean()), 4), "notRanked": ""}


def rank(scores: pd.DataFrame) -> pd.DataFrame:
    s = scores.copy()
    ok = s.notRanked == ""
    order = s[ok].sort_values(["gapP5", "pGapAboveTau", "gapP50"], ascending=False).index
    s["rank"] = pd.Series(range(1, len(order) + 1), index=order)
    naive = s[ok].sort_values("gapMedianOfMedians", ascending=False).index
    s["rankMedianGap"] = pd.Series(range(1, len(naive) + 1), index=naive)
    return s.sort_values("rank", na_position="last")


# --- demonstration and stability test (no audit data yet: NOT hypotheses) ---------------------------------

HISTORICAL = ["cold water infusion", "hot water infusion (tea)", "decoction in water", "steeped in wine", "decoction in wine",
              "steeped in vinegar", "infused oil", "fresh juice", "distilled water"]
MODERN = ["modern 70% ethanol extract", "modern methanol extract"]


def species_compounds(descriptor: str = "rdkit") -> dict[str, tuple[str, list[M.Compound]]]:
    prop = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    prop = prop[prop.proposed]
    occ = pd.read_parquet(INTERIM / "m3" / "occurrences.parquet")
    comp = pd.read_parquet(INTERIM / "m3" / "compounds.parquet").drop_duplicates("inchikey").set_index("inchikey")
    out = {}
    for sp in prop.itertuples():
        cs = []
        for k in sorted(set(occ[occ.acceptedName == sp.acceptedName].inchikey)):
            if k in comp.index and isinstance(comp.loc[k].smiles, str):
                d = chem.describe(comp.loc[k].smiles)
                if d is not None:
                    cs.append(M.Compound(k, d["logP"], d["basicN"], d["heatFlags"], d["volatile"], d["mw"]))
        out[sp.acceptedName] = (sp.wfoId, cs)
    return out


def _run(cfg: dict, spc: dict, sd: float, subset: dict | None = None) -> pd.DataFrame:
    draws = Draws(cfg, sd)
    rows = []
    for name, (wid, cs) in spc.items():
        use = subset[name] if subset else cs
        for f in HISTORICAL:
            for m in MODERN:
                rows.append(score(Candidate(wid, name, f, m), use, draws))
    return rank(pd.DataFrame(rows))


def _overlap(a: pd.DataFrame, b: pd.DataFrame, col: str, k: int) -> float:
    key = ["acceptedName", "faithful", "modern"]
    ta = set(map(tuple, a.dropna(subset=[col]).nsmallest(k, col)[key].values))
    tb = set(map(tuple, b.dropna(subset=[col]).nsmallest(k, col)[key].values))
    return len(ta & tb) / k


def _spearman(a: pd.DataFrame, b: pd.DataFrame, col: str) -> float:
    key = ["acceptedName", "faithful", "modern"]
    j = a[key + [col]].merge(b[key + [col]], on=key, suffixes=("_a", "_b")).dropna()
    return round(float(j[f"{col}_a"].corr(j[f"{col}_b"], method="spearman")), 4) if len(j) > 2 else float("nan")


def stability(n_boot: int = 20, top_k: int = 20, seed: int = 20261108) -> dict:
    cfg = M.load_config()
    sd = M.descriptor_sd("rdkit")["sd"]
    spc = species_compounds()
    base = _run(cfg, spc, sd)
    cfg2 = json.loads(json.dumps(cfg))
    cfg2["mc"]["seed"] = cfg["mc"]["seed"] + 1
    reseed = _run(cfg2, spc, sd)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        sub = {n: [cs[i] for i in rng.integers(0, len(cs), len(cs))] if cs else [] for n, (_, cs) in spc.items()}
        boots.append(_run(cfg, spc, sd, sub))
    res = {}
    for col, name in (("rank", "robust (5th percentile of gap)"), ("rankMedianGap", "median gap only (comparison)")):
        res[name] = {
            "monteCarloReseed": {"spearman": _spearman(base, reseed, col), f"top{top_k}Overlap": _overlap(base, reseed, col, top_k)},
            "compoundBootstrap": {"spearmanMean": round(float(np.nanmean([_spearman(base, b, col) for b in boots])), 4),
                                  f"top{top_k}OverlapMean": round(float(np.mean([_overlap(base, b, col, top_k) for b in boots])), 4),
                                  "replicates": n_boot},
        }
    used = base[base.notRanked == ""]
    out = {"label": "DEMONSTRATION on model profiles only: candidate pairs = every study-set species × historical preparation "
                    "× modern extract. No modern-methods audit has been run, so these are NOT hypotheses.",
           "rule": RULE, "widthMax": WIDTH_MAX, "tau": TAU, "minCompounds": MIN_COMPOUNDS, "descriptorErrorSd": sd,
           "modelVersion": M.config_version(cfg), "candidates": int(len(base)), "ranked": int(len(used)),
           "notRanked": int((base.notRanked != "").sum()),
           "compoundsExcludedWideShare": round(float(base.compoundsExcludedWide.sum() / max(base.compounds.sum(), 1)), 4),
           "stability": res,
           "rankDisagreement": {"spearmanRobustVsMedian": round(float(used["rank"].corr(used["rankMedianGap"], method="spearman")), 4),
                                f"top{top_k}Shared": int(len(set(used.nsmallest(top_k, "rank").index) & set(used.nsmallest(top_k, "rankMedianGap").index)))},
           "top": base.head(top_k)[["acceptedName", "faithful", "modern", "rank", "rankMedianGap", "gapP5", "gapP50", "gapP95",
                                    "pGapAboveTau", "compoundsUsed", "compoundsExcludedWide"]].to_dict("records")}
    OUT.mkdir(parents=True, exist_ok=True)
    base.to_csv(OUT / "ranking_demo.csv", index=False)
    (OUT / "ranking_stability.json").write_text(json.dumps(out, indent=2, default=str))
    return out


def to_contract(row) -> tuple:
    """A scored, ranked row -> (contract Interval for profileGap, contract GapRanking)."""
    from contract import models as C
    gap = C.Interval(value=row["gapP50"], low=row["gapP5"], high=row["gapP95"])
    gr = C.GapRanking(rule=RULE, gapP5=row["gapP5"], gapThreshold=TAU, pGapAboveThreshold=row["pGapAboveTau"],
                      compoundsUsed=int(row["compoundsUsed"]), compoundsExcludedWide=int(row["compoundsExcludedWide"]),
                      rankByMedianGap=int(row["rankMedianGap"]) if pd.notna(row.get("rankMedianGap")) else None)
    return gap, gr
