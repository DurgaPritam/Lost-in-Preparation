"""QAOA v3 (pre-registered in docs/QAOA_v3_RULE.md, committed before any v3 run): improved QAOA on the v2 instances.

Changes from v2, and nothing else: cost scaled by the objective's spread (HEURISTIC, qaoa.spread_scale) instead of
the largest coefficient; depths 1-5; INTERP initialisation from the best p-1 parameters; a CVaR(0.1) variant. The XY
ansatz (Dicke start, ring XY mixer) is v2's. The v2 benchmark (benchmark_v2.json) is unchanged and stays primary;
the classical results compared against are read from it, not recomputed.

Writes data/interim/m8/qaoa_v3.json and docs/QAOA_v3_RESULTS.md. Nothing goes to site-data/.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np
from qiskit.transpiler import CouplingMap

from ..paths import ROOT
from . import bench as B
from . import pool as Pm
from . import qaoa as A
from . import qubo as Q

OUT = B.OUT / "qaoa_v3.json"
DOC = ROOT / "docs" / "QAOA_v3_RESULTS.md"
RULE = "docs/QAOA_v3_RULE.md"
SIZES, K, DEPTHS = (8, 12, 16), 4, (1, 2, 3, 4, 5)
VARIANTS = {"xy-v3": 1.0, "xy-v3-cvar": 0.1}          # name -> CVaR alpha (1.0 = expected energy)
RESTARTS_P1, RESTARTS, MAXITER, GAMMA_MAX, SHOTS = 8, 4, 300, 2.0, 4096


def _one(inst, variant: str, cvar: float, p: int, seed: int, prev, f, feas, fo, fm, heavy) -> dict:
    r = A.Runner(inst, "xy", p, seed, scale_mode="spread", cvar=cvar)
    starts = [A.interp(prev, p)] if prev is not None else []
    opt = r.optimise(RESTARTS_P1 if p == 1 else RESTARTS, MAXITER, seed + 17 * p + (1 if cvar >= 1 else 2), starts=starts, gamma_max=GAMMA_MAX)
    th = opt["best"]["theta"]
    pr = r.probs(th)
    optimal = feas & (np.abs(f - fo) < 1e-9)
    arv = np.where(feas, (f - fm) / (fo - fm) if fo != fm else 1.0, 0.0)
    pf = float(pr[feas].sum())
    counts = r.sample(th, SHOTS, seed)
    cf = counts[feas].sum()
    return {"variant": variant, "cvarAlpha": cvar, "p": p, "scale": r.scale, "interpStart": prev is not None,
            "restarts": len(opt["restarts"]), "restartRuns": opt["restarts"], "bestTheta": th, "objective": opt["best"]["expectation"],
            "evaluations": opt["evaluations"], "seconds": opt["seconds"],
            "exact": {"pOptimum": float(pr[optimal].sum()), "feasibility": pf,
                      "expectedArFeasible": float((pr[feas] * arv[feas]).sum() / pf) if pf > 0 else None},
            "shots": {"n": int(counts.sum()), "seed": seed, "pOptimum": float(counts[optimal].sum() / counts.sum()),
                      "feasibility": float(cf / counts.sum())},
            "circuit": {"allToAll": A.metrics_of(r.c), "heavyHex": A.metrics_of(r.c, heavy, seed)}}


def run() -> dict:
    cfg = Pm.config("v2")
    v2 = json.loads((B.OUT / "benchmark_v2.json").read_text())
    allc = json.loads(Pm.OUT.read_text())["candidates"]
    cmap = {c["id"]: c for c in allc}
    w = {k: cfg["objective"][k] for k in ("alpha", "beta_class", "beta_indication", "beta_prep", "gamma")}
    heavy = CouplingMap.from_heavy_hex(5)
    seed = cfg["qaoa"]["seed"]
    rows, t0 = [], time.perf_counter()
    for row in v2["results"]:
        if row["n"] not in SIZES or row["k"] != K or "infeasible" in row:
            continue
        inst = Q.build([cmap[i] for i in row["ids"]], K, w, v2["vmax"], row["toxicRule"], cfg["objective"]["penalty_margin"], row["perSpecies"])
        f, feas = Q.all_objectives(inst)
        fo, fm = row["classical"]["exact"]["f"], row["classical"]["fMin"]
        if abs(Q.ilp(inst, "max")["f"] - fo) > 1e-9:
            raise RuntimeError(f"{row['instance']}: rebuilt instance does not match benchmark_v2")
        out = []
        for name, cvar in VARIANTS.items():
            prev = None
            for p in DEPTHS:
                res = _one(inst, name, cvar, p, seed, prev, f, feas, fo, fm, heavy)
                prev = res["bestTheta"]
                out.append(res)
                print(row["instance"], name, "p", p, "P(opt)", round(res["exact"]["pOptimum"], 4), round(time.perf_counter() - t0), "s", flush=True)
        v2x = [q for q in row.get("qaoa", []) if q["variant"] == "xy"]
        rows.append({"instance": row["instance"], "n": row["n"], "k": K, "ids": row["ids"], "uniformPOptimum": row["uniformPOptimum"],
                     "classical": {"exactSeconds": row["classical"]["exact"]["seconds"], "greedyOptimal": row["classical"]["greedy"]["optimal"],
                                   "annealSuccessRate": row["classical"]["anneal"]["successRate"], "annealMeanSeconds": row["classical"]["anneal"]["meanSeconds"]},
                     "v2xy": [{"p": q["p"], "pOptimum": q["exact"]["pOptimum"], "feasibility": q["exact"]["feasibility"]} for q in v2x],
                     "v3": out})
    res = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "rule": RULE, "primary": "benchmark_v2.json (unchanged)",
           "protocol": {"sizes": SIZES, "k": K, "depths": DEPTHS, "variants": VARIANTS, "restartsP1": RESTARTS_P1, "restarts": RESTARTS,
                        "maxiter": MAXITER, "optimizer": "COBYLA", "gammaStartMax": GAMMA_MAX, "shots": SHOTS, "seed": seed,
                        "scale": "2 * sd(E over weight-k states) / sqrt(n) (heuristic)", "init": "INTERP from best p-1 (p >= 2) + random"},
           "versions": B._versions(), "noise": "not modelled in v3 (noise-free statevector)", "results": rows, "seconds": time.perf_counter() - t0}
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)) + "\n")
    DOC.write_text("\n".join(report(res)) + "\n")
    return {"instances": len(rows), "seconds": round(res["seconds"], 1), "out": str(OUT.relative_to(ROOT)), "doc": str(DOC.relative_to(ROOT))}


def report(res: dict) -> list[str]:
    R = res["results"]
    L = ["# QAOA v3 results (generated)", "",
         f"Generated by `python -m lip m8 qaoa-v3` from `data/interim/m8/qaoa_v3.json`. Do not edit by hand. Protocol "
         f"pre-registered in [QAOA_v3_RULE.md](QAOA_v3_RULE.md) before any run. The v2 benchmark ([QUANTUM_RESULTS.md](QUANTUM_RESULTS.md)) "
         "is unchanged and stays the primary result. No quantum advantage is claimed. Noise-free statevector simulation.", "",
         "## Mean P(optimum) as a multiple of a uniformly random feasible panel (k = 4)", "",
         "Every variant and depth is shown (rule 1). v2 xy is the original benchmark's XY variant on the same instances.", "",
         "| n | Instances | v2 xy (best p ≤ 3) | " + " | ".join(f"{v} p={p}" for v in VARIANTS for p in res["protocol"]["depths"]) + " | Classical (annealing success) |",
         "|---|---|---|" + "---|" * (len(VARIANTS) * len(res["protocol"]["depths"])) + "---|"]
    for n in res["protocol"]["sizes"]:
        rs = [r for r in R if r["n"] == n]
        if not rs:
            continue
        ratio = lambda r, po: po / r["uniformPOptimum"]
        v2b = np.mean([max(ratio(r, q["pOptimum"]) for q in r["v2xy"]) for r in rs]) if all(r["v2xy"] for r in rs) else None
        cells = []
        for v in VARIANTS:
            for p in res["protocol"]["depths"]:
                cells.append(f"{np.mean([ratio(r, next(q for q in r['v3'] if q['variant'] == v and q['p'] == p)['exact']['pOptimum']) for r in rs]):.1f}×")
        sa = np.mean([r["classical"]["annealSuccessRate"] for r in rs])
        L.append(f"| {n} | {len(rs)} | {'—' if v2b is None else f'{v2b:.1f}×'} | " + " | ".join(cells) + f" | {sa:.0%} |")
    L += ["", "## Per instance (exact statevector)", "",
          "| Instance | Uniform P(opt) | Variant | p | P(optimum) | × uniform | Feasibility | Expected AR (feasible) | Seconds | CX heavy-hex |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in R:
        for q in r["v3"]:
            e = q["exact"]
            L.append(f"| {r['instance']} | {r['uniformPOptimum']:.4f} | {q['variant']} | {q['p']} | {e['pOptimum']:.4f} | {e['pOptimum'] / r['uniformPOptimum']:.1f}× | "
                     f"{e['feasibility']:.3f} | {'—' if e['expectedArFeasible'] is None else f'{e['expectedArFeasible']:.3f}'} | {q['seconds']:.1f} | {q['circuit']['heavyHex']['twoQubit']} |")
    L += ["", "## Classical methods on the same instances (from benchmark_v2.json)", "",
          "| Instance | Exact ILP seconds | Greedy optimal | Annealing success | Annealing mean seconds |", "|---|---|---|---|---|"]
    for r in R:
        c = r["classical"]
        L.append(f"| {r['instance']} | {c['exactSeconds']:.3f} | {'yes' if c['greedyOptimal'] else 'no'} | {c['annealSuccessRate']:.0%} | {c['annealMeanSeconds']:.3f} |")
    L += ["", f"Versions: {', '.join(f'{k} {v}' for k, v in res['versions'].items())}. Total optimiser time {res['seconds']:.0f} s."]
    return L
