"""Export the M4 preparation model's inputs for the in-browser engine (contract v1.7, P38: Preparation Lab).

    python -m lip m4 engine-export

Writes, for the species in site-data/profiles/index.json:
  site-data/engine/model.json          model parameters, uncertainty settings, the 13 preparations and their seeds
  site-data/engine/<speciesId>.json    per-compound model inputs (descriptor, flags, MW), in profile order
  site-data/engine/parity.json         Python reference estimates for preparations OUTSIDE the 13-preparation grid
                                        (unknown heat, unknown filtration, vinegar on basic nitrogen, mixtures, applied
                                        whole, pure ethanol, boiled oil, ...), so the port is tested on every branch
  data/interim/m4/engine_export.json   summary, including the self-check below

Self-check before anything is written: the exported inputs must reproduce, through this module's own model
(model.estimate), EXACTLY the committed profiles in site-data/profiles/. Otherwise the export fails.

The inputs are built exactly as run.profiles() builds them (same occurrence order, same descriptor rule).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from contract import models as C

from ..paths import INTERIM, SITE_DATA
from . import chem
from . import model as M
from .run import choose_descriptor, lipophilicity

OUT = SITE_DATA / "engine"
NOISE_SEED_OFFSET = 10_000_019  # model.simulate: noise_seed = seed + seed_offset + 10_000_019
CUSTOM_SEED_RULE = ("seedOffset = 1000 + (FNV-1a 32-bit hash of the UTF-8 string "
                    "'<solvents sorted, joined by +>|<heat>|<filtered>|<process or empty>') mod 1000000")
RNG = ("numpy.random.default_rng(seed) = PCG64 (XSL-RR 128/64) seeded through SeedSequence(seed), pool size 4. "
       "Uniform(lo, hi) = lo + (hi - lo) * next_double, next_double = (next_uint64 >> 11) * 2^-53. "
       "Descriptor noise: Generator.normal (ziggurat, numpy tables). Unknown heat: Generator.choice over "
       "[cold, warm, boiled] (integers via Lemire's method on next_uint32). Percentiles: numpy 'linear'; medians: numpy median.")
HEURISTICS = ["acidity (basic nitrogen in vinegar)", "heat alerts (SMARTS)", "volatile loss on open heating",
              "filtration carry-over (suspended material)", "size penalty (MW > 1000)", "compound class"]


def fnv1a32(s: str) -> int:
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def custom_seed_offset(solvents, heat: str, filtered: str, process: str | None) -> int:
    return 1000 + fnv1a32(f"{'+'.join(sorted(solvents))}|{heat}|{filtered}|{process or ''}") % 1_000_000


def params(cfg: dict) -> C.EngineParams:
    s = cfg["solvent"]
    sol = {k: C.EngineSolventWindow(upper=v.get("upper"), lower=v.get("lower"), ethanolFraction=v.get("ethanol_fraction"),
                                    ethanolShift=v.get("ethanol_shift")) for k, v in s.items()}
    return C.EngineParams(
        draws=int(cfg["mc"]["draws"]), seed=int(cfg["mc"]["seed"]), steepness=cfg["mc"]["steepness"], solvents=sol,
        acidityLogdShift=cfg["acidity"]["logd_shift"],
        heat={k: C.EngineHeatRange(warm=v["warm"], boiled=v["boiled"]) for k, v in cfg["heat"].items()},
        distillationVolatileCarried=cfg["distillation"]["volatile_carried"],
        distillationNonvolatileCarried=cfg["distillation"]["nonvolatile_carried"],
        unfilteredSuspended=cfg["filtration"]["unfiltered_suspended"],
        appliedWholeSuspended=cfg["filtration"]["applied_whole_suspended"],
        mwPenaltyAbove=float(cfg["size"]["mw_penalty_above"]), mwPenalty=cfg["size"]["mw_penalty"])


def prep_model(j: int, p: M.Prep) -> C.EnginePreparation:
    return C.EnginePreparation(seedOffset=j, key=p.key, label=p.label, solvents=list(p.solvent), heat=p.heat,
                               filtered=p.filtered, process=p.process)


def species_inputs(acceptedName: str, descriptor: str, occ, comp) -> list[tuple]:
    """(inchikey, name, class, Compound, descriptor used, smiles) in run.profiles() order."""
    out = []
    for r in occ[occ.acceptedName == acceptedName].itertuples():
        if r.inchikey not in comp.index:
            continue
        cr = comp.loc[r.inchikey]
        d = chem.describe(cr.smiles)
        if d is None:
            continue
        h, used = lipophilicity(cr.smiles, r.inchikey, descriptor)
        out.append((r.inchikey, cr.label if isinstance(cr.label, str) else r.inchikey, f"{d['class']} (heuristic)",
                    M.Compound(r.inchikey, h, d["basicN"], d["heatFlags"], d["volatile"], d["mw"]), used))
    return out


# Preparations outside the grid, chosen so every branch of model.simulate is exercised (see module docstring).
CUSTOM = [
    ("water, heat not stated, filtered", ("water",), "unknown", "yes", "infusion"),
    ("water, warm, filtration not stated", ("water",), "warm", "unknown", "infusion"),
    ("vinegar, warm, unfiltered", ("vinegar",), "warm", "no", "maceration"),
    ("vinegar + water, boiled, filtered", ("vinegar", "water"), "boiled", "yes", "decoction"),
    ("wine + honey, boiled, unfiltered", ("wine", "honey"), "boiled", "no", "decoction"),
    ("oil, warm, applied whole", ("oil",), "warm", "not_applicable", "other"),
    ("oil, boiled, filtered", ("oil",), "boiled", "yes", "decoction"),
    ("pure ethanol, cold, filtered", ("ethanol",), "cold", "yes", "maceration"),
    ("powder, heat not stated", ("none",), "unknown", "no", "powder"),
]


def run() -> dict:
    cfg = M.load_config()
    descriptor, _ = choose_descriptor(cfg)
    errs = {d: M.descriptor_sd(d) for d in ("rdkit", "xtb")}
    sd = {d: e["sd"] for d, e in errs.items()}
    version = M.config_version(cfg)
    idx = json.loads((SITE_DATA / "profiles" / "index.json").read_text())
    occ = pd.read_parquet(INTERIM / "m3" / "occurrences.parquet")
    comp = pd.read_parquet(INTERIM / "m3" / "compounds.parquet").drop_duplicates("inchikey").set_index("inchikey")

    species, mismatches, checked = {}, [], 0
    for e in idx:
        inputs = species_inputs(e["acceptedName"], descriptor, occ, comp)
        committed = json.loads((SITE_DATA / e["file"]).read_text())
        order = [c["compoundId"] for c in committed[0]["compounds"]]
        if [x[0] for x in inputs] != order:
            raise RuntimeError(f"{e['acceptedName']}: exported compound order differs from {e['file']}")
        for j, prep in enumerate(M.GRID):
            prof = committed[j]
            if prof["preparationLabel"] != prep.label:
                raise RuntimeError(f"{e['file']}: profile {j} is {prof['preparationLabel']!r}, grid has {prep.label!r}")
            for (ik, _, _, c, used), want in zip(inputs, prof["compounds"]):
                got = M.estimate(c, prep, cfg, seed_offset=j, sd=sd[used])
                checked += 1
                if (got["likelihood"], got["low"], got["high"], got["drivers"]) != (want["likelihood"], want["low"], want["high"], want["drivers"]):
                    mismatches.append({"species": e["speciesId"], "prep": prep.label, "compound": ik})
        species[e["speciesId"]] = (e, inputs)
    if mismatches:
        raise RuntimeError(f"self-check failed: {len(mismatches)} of {checked} estimates differ from site-data/profiles "
                           f"(first: {mismatches[0]}); re-run `python -m lip m4 run` before exporting")

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    model = C.EngineModel(
        modelVersion=version, rng=RNG, noiseSeedOffset=NOISE_SEED_OFFSET, customSeedRule=CUSTOM_SEED_RULE, params=params(cfg),
        descriptorError=[C.EngineDescriptorError(descriptor=d, mae=x["mae"], sd=x["sd"], source=x["source"]) for d, x in errs.items()],
        preparations=[prep_model(j, p) for j, p in enumerate(M.GRID)], heuristics=HEURISTICS,
        note=("Inputs to the preparation model (M4) for the in-browser engine. Model estimates of what a preparation would "
              "carry, not measurements; the 5th–95th range includes descriptor error."))
    (OUT / "model.json").write_text(json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=1) + "\n")
    for sid, (e, inputs) in species.items():
        rec = C.EngineSpecies(speciesId=sid, acceptedName=e["acceptedName"], modelVersion=version, compounds=[
            C.EngineCompound(compoundId=ik, name=name, compoundClass=cls, descriptor=used, lipophilicity=c.h, basicN=c.basicN,
                             heatFlags=list(c.heatFlags), volatile=c.volatile, mw=c.mw) for ik, name, cls, c, used in inputs])
        (OUT / f"{sid}.json").write_text(json.dumps(rec.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")) + "\n")

    # Parity cases: species chosen to cover basic nitrogen, MW > 1000, volatiles and every heat alert.
    def feats(inputs) -> set[str]:
        f: set[str] = set()
        for _, _, _, c, _ in inputs:
            f |= set(c.heatFlags) | ({"basicN"} if c.basicN else set()) | ({"volatile"} if c.volatile else set()) \
                | ({"mw>1000"} if c.mw > 1000 else set())
        return f
    present = set().union(*(feats(v[1]) for v in species.values()))
    chosen, covered = [], set()
    # greedy: the species adding most uncovered features first (smaller species on ties), until every feature present
    # in the headline set is covered
    while covered != present:
        sid = max((s for s in species if s not in chosen),
                  key=lambda s: (len(feats(species[s][1]) - covered), -len(species[s][1])))
        chosen.append(sid)
        covered |= feats(species[sid][1])
    cases = []
    for sid in chosen:
        e, inputs = species[sid]
        for label, sol, heat, filt, proc in CUSTOM:
            off = custom_seed_offset(sol, heat, filt, proc)
            prep = M.Prep(f"unknown|unknown|{'+'.join(sorted(sol))}|{heat}|{filt}", label, sol, heat, filt, proc)
            exp = []
            for ik, _, _, c, used in inputs:
                s = M.estimate(c, prep, cfg, seed_offset=off, sd=sd[used])
                exp.append(C.EngineEstimate(compoundId=ik, likelihood=s["likelihood"], low=s["low"], high=s["high"],
                                            rangeModelOnly=s["rangeModelOnly"], drivers=C.Drivers(**s["drivers"])))
            cases.append(C.EngineParityCase(speciesId=sid, preparation=C.EnginePreparation(
                seedOffset=off, key=prep.key, label=label, solvents=list(sol), heat=heat, filtered=filt, process=proc), expected=exp))
    (OUT / "parity.json").write_text(json.dumps([c.model_dump(mode="json") for c in cases], ensure_ascii=False, separators=(",", ":")) + "\n")

    summary = {"modelVersion": version, "descriptor": descriptor, "species": len(species),
               "compounds": sum(len(v[1]) for v in species.values()), "gridPreparations": len(M.GRID),
               "selfCheck": {"estimatesChecked": checked, "mismatches": 0,
                             "note": "exported inputs reproduce site-data/profiles exactly through pipeline/lip/m4/model.py"},
               "parity": {"species": chosen, "featuresCovered": sorted(covered), "customPreparations": len(CUSTOM),
                          "cases": len(cases), "estimates": sum(len(c.expected) for c in cases)},
               "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (INTERIM / "m4" / "engine_export.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
