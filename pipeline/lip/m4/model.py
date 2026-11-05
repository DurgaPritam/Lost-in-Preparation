"""Preparation model (M4): how likely is each compound to reach a given preparation?

likelihood = solvent factor (with acidity) -> filtration -> heat, each a separate, inspectable factor,
with uncertainty propagated by Monte Carlo over the ranges in config/prep_model.toml.
Outputs per compound × preparation: median likelihood, 5th–95th percentile range, and the median of
each factor (drivers). Heuristic factors (acidity, heat alerts, volatility, filtration, size) are
labelled heuristic in the output.

These are MODEL ESTIMATES of what a preparation would carry, not chemical measurements.
"""
from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass, field

import numpy as np

from ..paths import ROOT

CONFIG = ROOT / "config" / "prep_model.toml"
AQUEOUS = {"water", "wine", "vinegar", "honey", "other"}


def load_config() -> dict:
    with CONFIG.open("rb") as fh:
        return tomllib.load(fh)


def config_version(cfg: dict) -> str:
    return "prep-model:" + hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:10]


@dataclass(frozen=True)
class Prep:
    key: str            # contract preparationKey
    label: str
    solvent: tuple      # one or more solvents (historical or modern)
    heat: str           # cold | warm | boiled | unknown
    filtered: str       # yes | no | not_applicable | unknown
    process: str | None = None   # distillation | powder | expression | None
    part: str = "unknown"
    fresh: str = "unknown"


def _key(solvent, heat, filtered, part="unknown", fresh="unknown") -> str:
    return f"{part}|{fresh}|{'+'.join(sorted(solvent))}|{heat}|{filtered}"


GRID = [
    Prep(_key(("water",), "cold", "yes"), "cold water infusion", ("water",), "cold", "yes", "infusion"),
    Prep(_key(("water",), "warm", "yes"), "hot water infusion (tea)", ("water",), "warm", "yes", "infusion"),
    Prep(_key(("water",), "boiled", "yes"), "decoction in water", ("water",), "boiled", "yes", "decoction"),
    Prep(_key(("wine",), "cold", "yes"), "steeped in wine", ("wine",), "cold", "yes", "maceration"),
    Prep(_key(("wine",), "boiled", "yes"), "decoction in wine", ("wine",), "boiled", "yes", "decoction"),
    Prep(_key(("vinegar",), "cold", "yes"), "steeped in vinegar", ("vinegar",), "cold", "yes", "maceration"),
    Prep(_key(("oil",), "warm", "yes"), "infused oil", ("oil",), "warm", "yes", "maceration"),
    Prep(_key(("none",), "cold", "no"), "fresh juice", ("none",), "cold", "no", "expression"),
    Prep(_key(("none",), "cold", "no") + "#powder", "powder taken whole", ("none",), "cold", "no", "powder"),
    Prep(_key(("water",), "boiled", "unknown") + "#distillation", "distilled water", ("water",), "boiled", "unknown", "distillation"),
    Prep(_key(("methanol",), "cold", "yes"), "modern methanol extract", ("methanol",), "cold", "yes", "maceration"),
    Prep(_key(("hydroethanolic",), "cold", "yes"), "modern 70% ethanol extract", ("hydroethanolic",), "cold", "yes", "maceration"),
    Prep(_key(("hexane",), "cold", "yes"), "low-temperature nonpolar extract (hexane)", ("hexane",), "cold", "yes", "maceration"),
]
BY_LABEL = {p.label: p for p in GRID}


def _u(rng, lohi, n):
    lo, hi = lohi
    return rng.uniform(lo, hi, n)


def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def solvent_fraction(rng, cfg, solvent: str, h: np.ndarray, k: np.ndarray) -> np.ndarray:
    n = len(k)
    s = cfg["solvent"]
    if solvent == "none":
        return np.ones(n)
    if solvent == "wine":
        w = s["wine"]
        shift = _u(rng, w["ethanol_fraction"], n) * _u(rng, w["ethanol_shift"], n)
        return _sig(k * (_u(rng, w["upper"], n) + shift - h))
    p = s[solvent]
    f = np.ones(n)
    if "upper" in p:
        f = f * _sig(k * (_u(rng, p["upper"], n) - h))
    if "lower" in p:
        f = f * _sig(k * (h - _u(rng, p["lower"], n)))
    return f


@dataclass
class Compound:
    inchikey: str
    h: float                 # lipophilicity descriptor (logP)
    basicN: bool
    heatFlags: list
    volatile: bool
    mw: float
    meta: dict = field(default_factory=dict)


LOGP_VALIDATION = ROOT / "data" / "interim" / "m4" / "logp_validation.json"


def descriptor_sd(descriptor: str = "rdkit") -> dict:
    """Descriptor error used for UNCERTAINTY REPORTING (not scoring): the SD of a Normal error whose mean
    absolute deviation equals the descriptor's MAE against experimental logP (sigma = MAE * sqrt(pi/2))."""
    v = json.loads(LOGP_VALIDATION.read_text())
    block = {"rdkit": "rdkit_all", "xtb": "xtb_paired"}[descriptor]
    mae = float(v[block]["mae"]["value"])
    return {"descriptor": descriptor, "mae": mae, "sd": round(mae * (np.pi / 2) ** 0.5, 4), "source": f"{LOGP_VALIDATION.name} {block}.mae"}


def estimate(c: Compound, prep: Prep, cfg: dict, seed_offset: int = 0, sd: float | None = None) -> dict:
    """The reported estimate. Median and drivers are the primary model's (`simulate`, unchanged), so every
    score that uses the median is unaffected. The 5th–95th range additionally includes descriptor error:
    it comes from the same draws with Normal(0, sd) added to logP, widened if needed to contain the median.
    `rangeModelOnly` keeps the range without descriptor error."""
    s = simulate(c, prep, cfg, seed_offset)
    if not sd:
        return s
    n = simulate(c, prep, cfg, seed_offset, h_sd=sd)
    out = dict(s)
    out["rangeModelOnly"] = [s["low"], s["high"]]
    out["low"] = round(min(n["low"], s["likelihood"]), 4)
    out["high"] = round(max(n["high"], s["likelihood"]), 4)
    return out


def simulate(c: Compound, prep: Prep, cfg: dict, seed_offset: int = 0,
             k_fixed: float | None = None, h_sd: float = 0.0, noise_seed: int | None = None,
             return_draws: bool = False):
    """Primary model with the defaults. `k_fixed` / `h_sd` exist only for the secondary
    `water-partition-slope` variant pre-registered in docs/PREREGISTRATION_v2.md (fixed window
    slope; Normal descriptor noise drawn from a separate stream so the primary draws are unchanged)."""
    n = int(cfg["mc"]["draws"])
    rng = np.random.default_rng(cfg["mc"]["seed"] + seed_offset)
    k = _u(rng, cfg["mc"]["steepness"], n)
    if k_fixed is not None:
        k = np.full(n, float(k_fixed))
    h = np.full(n, c.h)
    if h_sd > 0:
        ns = noise_seed if noise_seed is not None else cfg["mc"]["seed"] + seed_offset + 10_000_019
        h = h + np.random.default_rng(ns).normal(0.0, h_sd, n)  # noise_seed: couple one compound's error across preparations

    # solvent (+ acidity), mixtures take the best-extracting component
    if prep.process == "distillation":
        f_solvent = (_u(rng, cfg["distillation"]["volatile_carried"], n) if c.volatile
                     else _u(rng, cfg["distillation"]["nonvolatile_carried"], n))
        f_noacid = f_solvent
    elif prep.process == "powder":
        f_solvent = f_noacid = np.ones(n)
    else:
        sol = prep.solvent
        if prep.process == "expression":
            sol = ("water",)  # juice = aqueous cell sap
        f_noacid = np.max([solvent_fraction(rng, cfg, s, h, k) for s in sol], axis=0)
        if "vinegar" in prep.solvent and c.basicN:
            h_acid = h - _u(rng, cfg["acidity"]["logd_shift"], n)
            f_solvent = np.max([solvent_fraction(rng, cfg, s, h_acid if s == "vinegar" else h, k) for s in sol], axis=0)
        else:
            f_solvent = f_noacid
        if c.mw > cfg["size"]["mw_penalty_above"]:
            f_solvent = f_solvent * _u(rng, cfg["size"]["mw_penalty"], n)
            f_noacid = f_noacid * 1.0

    # filtration
    filt = prep.filtered
    if filt == "unknown" and prep.process != "distillation":
        filt_draw = rng.random(n) < 0.5
    else:
        filt_draw = np.full(n, filt == "yes" or prep.process == "distillation")
    susp = np.where(prep.filtered == "not_applicable", _u(rng, cfg["filtration"]["applied_whole_suspended"], n),
                    _u(rng, cfg["filtration"]["unfiltered_suspended"], n))
    f_carried = np.where(filt_draw, f_solvent, f_solvent + susp * (1.0 - f_solvent))

    # heat
    heat_level = prep.heat
    heat_factor = np.ones(n)
    levels = np.full(n, heat_level) if heat_level != "unknown" else rng.choice(["cold", "warm", "boiled"], n)
    alerts = list(c.heatFlags) + (["volatile"] if c.volatile and prep.process != "distillation" else [])
    for a in alerts:
        rngs = cfg["heat"][a]
        d = np.zeros(n)
        for lvl in ("warm", "boiled"):
            m = levels == lvl
            if m.any():
                d[m] = _u(rng, rngs[lvl], int(m.sum()))
        heat_factor = heat_factor * (1.0 - d)

    total = np.clip(f_carried * heat_factor, 0, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        filt_factor = np.where(f_solvent > 0, f_carried / f_solvent, 1.0)
        acid_factor = np.where(f_noacid > 0, f_solvent / f_noacid, 1.0)
    q = np.percentile(total, [5, 50, 95])
    out = {
        "likelihood": round(float(q[1]), 4), "low": round(float(q[0]), 4), "high": round(float(q[2]), 4),
        "drivers": {"solvent": round(float(np.median(f_noacid)), 4), "heat": round(float(np.median(heat_factor)), 4),
                    "filtration": round(float(np.median(filt_factor)), 4), "acidity": round(float(np.median(acid_factor)), 4)},
        "heuristicFlags": sorted(set(c.heatFlags + (["volatile"] if c.volatile else []) + (["basic_nitrogen"] if c.basicN else []))),
    }
    return (out, total) if return_draws else out
