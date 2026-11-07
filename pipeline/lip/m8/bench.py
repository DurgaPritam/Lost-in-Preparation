"""Phase 8 benchmark: exact ILP vs greedy vs simulated annealing vs QAOA (penalty and XY mixer), on the same instances.

Every setting comes from config/m8_qubo.toml (weights fixed before any comparison). Outputs:
  data/interim/m8/benchmark.json   every instance, solver, seed and metric
  data/interim/m8/panel.json       the recommended panel (exact solver, full pool) and the weight sensitivity
  docs/figures/m8/*.png            scaling and noise figures
Metrics:
  approximation ratio  AR = (f(x) - f_min) / (f_opt - f_min) over feasible x (f_min, f_opt exact)
  P(optimum)           probability of sampling an optimal selection (exact from the statevector; also from shots)
  feasibility          share of probability / samples with exactly k selected (and at most one toxic, when that rule is on)
  runtime              wall clock; circuit depth and two-qubit gates after transpiling to {rz, sx, x, cx}, all-to-all
                       and on a heavy-hex coupling map (Qiskit core; no device)
"""
from __future__ import annotations

import json
import math
import platform
import random
import time
from datetime import datetime, timezone

import numpy as np

from ..paths import INTERIM, ROOT
from . import pool as Pm
from . import qaoa as A
from . import qubo as Q

OUT = INTERIM / "m8"
FIG = ROOT / "docs" / "figures" / "m8"


def _versions() -> dict:
    import pulp
    import qiskit
    import qiskit_aer
    import scipy
    return {"python": platform.python_version(), "qiskit": qiskit.__version__, "qiskit-aer": qiskit_aer.__version__,
            "pulp": pulp.__version__, "numpy": np.__version__, "scipy": scipy.__version__}


def _ar(f: float, fo: float, fm: float) -> float:
    return 1.0 if fo == fm else (f - fm) / (fo - fm)


def instances(cands: list[dict], cfg: dict) -> list[dict]:
    out = []
    for n in cfg["instances"]["sizes"]:
        reps = 1 if n >= len(cands) else cfg["instances"]["per_size"]
        for i in range(reps):
            seed = cfg["instances"]["seed"] + 1000 * n + i
            sub = cands if n >= len(cands) else random.Random(seed).sample(cands, n)
            out.append({"name": f"n{n}-{i}" if n < len(cands) else f"full-pool-n{len(cands)}", "n": len(sub), "seed": seed if n < len(cands) else None,
                        "ids": [c["id"] for c in sub], "cands": sub})
    return out


def classical(inst: Q.Instance, cfg: dict) -> dict:
    ex, mn = Q.ilp(inst, "max"), Q.ilp(inst, "min")
    fo, fm = ex["f"], mn["f"]
    res = {"exact": {"f": fo, "seconds": ex["seconds"], "status": ex["status"], "x": ex["x"].astype(int).tolist()}, "fMin": fm}
    if len(inst.h) <= 16:
        bf = Q.brute_force(inst)
        res["bruteForceAgrees"] = bool(abs(bf["f"] - fo) < 1e-9 and abs(bf["fMin"] - fm) < 1e-9)
    g = Q.greedy(inst)
    res["greedy"] = {"f": g["f"], "ar": _ar(g["f"], fo, fm), "optimal": abs(g["f"] - fo) < 1e-9, "seconds": g["seconds"]}
    sa = [Q.anneal(inst, s, cfg["classical"]["sa_sweeps"], cfg["classical"]["sa_t0"], cfg["classical"]["sa_t1"]) for s in cfg["classical"]["sa_seeds"]]
    res["anneal"] = {"runs": [{"seed": r["seed"], "f": r["f"], "ar": _ar(r["f"], fo, fm), "optimal": abs(r["f"] - fo) < 1e-9, "seconds": r["seconds"]} for r in sa],
                     "meanAr": float(np.mean([_ar(r["f"], fo, fm) for r in sa])), "successRate": float(np.mean([abs(r["f"] - fo) < 1e-9 for r in sa])),
                     "meanSeconds": float(np.mean([r["seconds"] for r in sa]))}
    return res


def _feas_vec(inst: Q.Instance, n: int) -> tuple[np.ndarray, np.ndarray]:
    return Q.all_objectives(inst, n)


def qaoa_run(inst: Q.Instance, variant: str, p: int, cfg: dict, fo: float, fm: float, f: np.ndarray, feas: np.ndarray, heavy) -> dict:
    qc = cfg["qaoa"]
    r = A.Runner(inst, variant, p, qc["seed"])
    opt = r.optimise(qc["restarts"], qc["maxiter"], qc["seed"] + 17 * p + (0 if variant == "penalty" else 1))
    th = opt["best"]["theta"]
    pr = r.probs(th)
    optimal = feas & (np.abs(f - fo) < 1e-9)
    arv = np.where(feas, (f - fm) / (fo - fm) if fo != fm else 1.0, 0.0)
    pf = float(pr[feas].sum())
    counts = r.sample(th, qc["shots"], qc["seed"])
    shots = counts.sum()
    cf = counts[feas].sum()
    samp_ar = arv[(counts > 0) & feas]
    return {
        "variant": variant, "p": p, "optimiser": qc["optimizer"], "maxiter": qc["maxiter"], "restarts": qc["restarts"],
        "restartRuns": opt["restarts"], "bestTheta": th, "expectedEnergy": opt["best"]["expectation"], "evaluations": opt["evaluations"],
        "seconds": opt["seconds"],
        "exact": {"pOptimum": float(pr[optimal].sum()), "feasibility": pf,
                  "expectedArFeasible": float((pr[feas] * arv[feas]).sum() / pf) if pf > 0 else None},
        "shots": {"n": int(shots), "seed": qc["seed"], "pOptimum": float(counts[optimal].sum() / shots), "feasibility": float(cf / shots),
                  "bestAr": float(samp_ar.max()) if len(samp_ar) else None,
                  "meanArFeasible": float((counts[feas] * arv[feas]).sum() / cf) if cf else None},
        "circuit": {"allToAll": A.metrics_of(r.c), "heavyHex": A.metrics_of(r.c, heavy, qc["seed"])},
    }


def noise_study(inst: Q.Instance, cfg: dict, best: dict, fo: float, fm: float, f: np.ndarray, feas: np.ndarray, heavy) -> dict:
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error
    nc = cfg["noise"]
    optimal = feas & (np.abs(f - fo) < 1e-9)
    arv = np.where(feas, (f - fm) / (fo - fm) if fo != fm else 1.0, 0.0)
    rows = []
    for variant, run in best.items():
        r = A.Runner(inst, variant, run["p"], cfg["qaoa"]["seed"])
        for e2 in nc["two_qubit_errors"]:
            nm = None
            if e2 > 0:
                nm = NoiseModel()
                nm.add_all_qubit_quantum_error(depolarizing_error(e2, 2), ["cx"])
                nm.add_all_qubit_quantum_error(depolarizing_error(e2 * nc["one_qubit_ratio"], 1), ["sx", "x"])
                ro = nc["readout_error"]
                nm.add_all_qubit_readout_error(ReadoutError([[1 - ro, ro], [ro, 1 - ro]]))
            counts = r.sample(run["bestTheta"], nc["shots"], cfg["qaoa"]["seed"], noise_model=nm, coupling=heavy)
            s = counts.sum()
            cf = counts[feas].sum()
            rows.append({"variant": variant, "p": run["p"], "twoQubitError": e2, "oneQubitError": e2 * nc["one_qubit_ratio"],
                         "readoutError": nc["readout_error"] if e2 > 0 else 0.0,
                         "pOptimum": float(counts[optimal].sum() / s), "feasibility": float(cf / s),
                         "meanArFeasible": float((counts[feas] * arv[feas]).sum() / cf) if cf else None})
    return {"model": "parametric depolarising noise (Qiskit Aer) on a heavy-hex coupling map; not a device calibration",
            "instance": inst.ids, "rows": rows, "randomFeasibleAr": float(arv[feas].mean()),
            "uniformPOptimum": float(optimal.sum() / feas.sum())}


def caveats(c: dict) -> list[str]:
    out = ["hypothesis worth re-testing, not a claim that the preparation works or is safe",
           "profile gap from predicted compound likelihoods (model), equal weights: LOTUS has no abundance data",
           "historical indication mapped to MeSH by a heuristic lexicon; the historical term is not a modern diagnosis"]
    if c["modernBasis"] == "default":
        out.append("no retrieved study used a modelled modern preparation for these pairs; comparator is the most frequent modern preparation across all coded studies")
    if all(s.startswith("pliny") for s in c["sources"]):
        out.append("attested only by Pliny (lower confidence)")
    if c["toxic"]:
        out.append("toxicity reported for this species (curated entry, AI-drafted, unverified): not offered for planning")
    return out


def panel_entry(c: dict, rank: int, inst: Q.Instance, vmax: float) -> dict:
    return {"position": rank, "candidateId": c["id"], "speciesId": c["speciesId"], "species": c["species"],
            "historicalPreparation": c["historical"], "modernComparator": c["modern"], "modernComparatorBasis": c["modernBasis"],
            "indication": c["indication"], "indications": c["indications"],
            "gap": {"p5": c["gapP5"], "p50": c["gapP50"], "p95": c["gapP95"]}, "value": round(c["gapP5"] / vmax, 4),
            "compoundsLikelyToDiffer": len(c["differs"]), "compoundClasses": c["classes"], "toxicity": c["toxicity"],
            "caveats": caveats(c),
            "evidenceTrail": [*({"kind": "recipe", "ref": r} for r in c["recipes"][:10]),
                              *({"kind": "study", "ref": f"pmid:{p}"} for p in c["pmids"][:10]),
                              {"kind": "profile", "ref": f"{c['speciesId']}:{c['historical']} vs {c['modern']}"},
                              {"kind": "species", "ref": c["speciesId"]}]}


def panel(cands: list[dict], cfg: dict, vmax: float) -> dict:
    """The recommended panel from the exact solver on the real pool, for both toxic rules and k = 4, 6, 8, plus the
    weight sensitivity (each weight x0.5 and x2, others fixed) for the default configuration."""
    w0 = {k: cfg["objective"][k] for k in ("alpha", "beta_class", "beta_indication", "beta_prep", "gamma")}
    margin = cfg["objective"]["penalty_margin"]
    out = {"weights": w0, "panels": {}, "sensitivity": []}
    for rule in ("exclude", "at_most_one"):
        pool = [c for c in cands if not (rule == "exclude" and c["toxic"])]
        for k in cfg["instances"]["ks"]:
            inst = Q.build(pool, k, w0, vmax, rule, margin)
            ex = Q.ilp(inst, "max")
            sel = [pool[i] for i in np.flatnonzero(ex["x"])]
            sel.sort(key=lambda c: -c["gapP5"])
            out["panels"][f"{rule}:k{k}"] = {"toxicRule": rule, "k": k, "poolSize": len(pool), "objective": ex["f"], "status": ex["status"],
                                              "coverage": Q.coverage_counts(pool, ex["x"]),
                                              "candidates": [panel_entry(c, i + 1, inst, vmax) for i, c in enumerate(sel)]}
    default = f"{cfg['pool']['toxic']}:k{cfg['objective']['k']}"
    base_ids = {c["candidateId"] for c in out["panels"][default]["candidates"]}
    pool = [c for c in cands if not (cfg["pool"]["toxic"] == "exclude" and c["toxic"])]
    for wname in w0:
        for fct in cfg["sensitivity"]["factors"]:
            w = {**w0, wname: w0[wname] * fct}
            inst = Q.build(pool, cfg["objective"]["k"], w, vmax, cfg["pool"]["toxic"], margin)
            ex = Q.ilp(inst, "max")
            ids = {pool[i]["id"] for i in np.flatnonzero(ex["x"])}
            out["sensitivity"].append({"weight": wname, "factor": fct, "value": w[wname], "jaccardWithDefault": round(len(ids & base_ids) / len(ids | base_ids), 4),
                                       "added": sorted(ids - base_ids), "removed": sorted(base_ids - ids)})
    out["default"] = default
    return out


def figures(bench: dict) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    files = []
    rows = [r for r in bench["results"] if "classical" in r]
    ns = sorted({r["n"] for r in rows})

    def by(solver_fn, k):
        xs, ys = [], []
        for n in ns:
            v = [solver_fn(r) for r in rows if r["n"] == n and r["k"] == k]
            v = [x for x in v if x is not None]
            if v:
                xs.append(n), ys.append(float(np.mean(v)))
        return xs, ys
    k = 4
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for lab, fn in (("Exact (ILP)", lambda r: 1.0), ("Greedy", lambda r: r["classical"]["greedy"]["ar"]),
                    ("Simulated annealing (mean of 5 seeds)", lambda r: r["classical"]["anneal"]["meanAr"])):
        ax.plot(*by(fn, k), marker="o", label=lab)
    for variant, ls in (("penalty", "--"), ("xy", "-")):
        for p in (1, 2, 3):
            ax.plot(*by(lambda r, v=variant, pp=p: next((q["exact"]["expectedArFeasible"] for q in r.get("qaoa", []) if q["variant"] == v and q["p"] == pp), None), k),
                    ls=ls, marker="s", label=f"QAOA {variant} p={p} (expected AR, feasible mass)")
    ax.set_xlabel("candidates n"), ax.set_ylabel("approximation ratio"), ax.set_title(f"Approximation ratio by size (k = {k})")
    ax.legend(fontsize=6), ax.grid(alpha=0.3)
    f1 = FIG / "approximation_ratio.png"; fig.tight_layout(); fig.savefig(f1, dpi=150); plt.close(fig); files.append(f1)

    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
    for variant, ls in (("penalty", "--"), ("xy", "-")):
        for p in (1, 2, 3):
            for ax, key in ((axs[0], "pOptimum"), (axs[1], "feasibility")):
                ax.plot(*by(lambda r, v=variant, pp=p, kk=key: next((q["exact"][kk] for q in r.get("qaoa", []) if q["variant"] == v and q["p"] == pp), None), k),
                        ls=ls, marker="s", label=f"{variant} p={p}")
    axs[0].plot(*by(lambda r: r.get("uniformPOptimum"), k), color="black", lw=1, label="uniform over feasible")
    axs[0].set_title("P(sample the optimum)"), axs[1].set_title("Feasibility (k selected, at most one toxic)")
    for ax in axs:
        ax.set_xlabel("candidates n"), ax.grid(alpha=0.3), ax.set_yscale("log")
    axs[0].legend(fontsize=6)
    f2 = FIG / "qaoa_success_feasibility.png"; fig.tight_layout(); fig.savefig(f2, dpi=150); plt.close(fig); files.append(f2)

    fig, ax = plt.subplots(figsize=(6.4, 4))
    ax.plot(*by(lambda r: r["classical"]["exact"]["seconds"], k), marker="o", label="Exact (ILP, CBC)")
    ax.plot(*by(lambda r: r["classical"]["anneal"]["meanSeconds"], k), marker="o", label="Simulated annealing (per run)")
    for variant in ("penalty", "xy"):
        ax.plot(*by(lambda r, v=variant: next((q["seconds"] for q in r.get("qaoa", []) if q["variant"] == v and q["p"] == 1), None), k), marker="s", label=f"QAOA {variant} p=1 (simulated, all restarts)")
    ax.set_yscale("log"), ax.set_xlabel("candidates n"), ax.set_ylabel("wall-clock seconds"), ax.set_title("Runtime (laptop; QAOA is a classical simulation)")
    ax.legend(fontsize=7), ax.grid(alpha=0.3)
    f3 = FIG / "runtime.png"; fig.tight_layout(); fig.savefig(f3, dpi=150); plt.close(fig); files.append(f3)

    fig, ax = plt.subplots(figsize=(6.4, 4))
    for variant, ls in (("penalty", "--"), ("xy", "-")):
        for p in (1, 3):
            ax.plot(*by(lambda r, v=variant, pp=p: next((q["circuit"]["allToAll"]["twoQubit"] for q in r.get("qaoa", []) if q["variant"] == v and q["p"] == pp), None), k), ls=ls, marker="s", label=f"{variant} p={p}, all-to-all")
            ax.plot(*by(lambda r, v=variant, pp=p: next((q["circuit"]["heavyHex"]["twoQubit"] for q in r.get("qaoa", []) if q["variant"] == v and q["p"] == pp), None), k), ls=ls, marker="^", label=f"{variant} p={p}, heavy-hex")
    ax.set_xlabel("candidates n (qubits)"), ax.set_ylabel("two-qubit (CX) gates"), ax.set_title("Circuit cost after transpiling")
    ax.legend(fontsize=6), ax.grid(alpha=0.3)
    f4 = FIG / "two_qubit_gates.png"; fig.tight_layout(); fig.savefig(f4, dpi=150); plt.close(fig); files.append(f4)

    nz = bench.get("noise")
    if nz:
        fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
        for variant in sorted({r["variant"] for r in nz["rows"]}):
            rr = [r for r in nz["rows"] if r["variant"] == variant]
            axs[0].plot([r["twoQubitError"] for r in rr], [r["pOptimum"] for r in rr], marker="o", label=f"{variant} p={rr[0]['p']}")
            axs[1].plot([r["twoQubitError"] for r in rr], [r["feasibility"] for r in rr], marker="o", label=f"{variant} p={rr[0]['p']}")
        axs[0].axhline(nz["uniformPOptimum"], color="black", lw=1, label="uniform over feasible")
        axs[0].set_title("P(optimum) under noise"), axs[1].set_title("Feasibility under noise (k selected, at most one toxic)")
        for ax in axs:
            ax.set_xlabel("two-qubit depolarising error"), ax.grid(alpha=0.3)
        axs[0].legend(fontsize=7)
        f5 = FIG / "noise.png"; fig.tight_layout(); fig.savefig(f5, dpi=150); plt.close(fig); files.append(f5)
    return [str(f.relative_to(ROOT)) for f in files]


def run(qaoa_on: bool = True) -> dict:
    from qiskit.transpiler import CouplingMap
    cfg = Pm.config()
    data = json.loads(Pm.OUT.read_text())
    cands = data["candidates"]
    vmax = max(c["gapP5"] for c in cands)
    w = {k: cfg["objective"][k] for k in ("alpha", "beta_class", "beta_indication", "beta_prep", "gamma")}
    margin = cfg["objective"]["penalty_margin"]
    heavy = CouplingMap.from_heavy_hex(5)
    t0 = time.perf_counter()
    results = []
    for I in instances(cands, cfg):
        for k in cfg["instances"]["ks"]:
            if k >= I["n"]:
                continue
            inst = Q.build(I["cands"], k, w, vmax, "at_most_one", margin)
            nontox = int((~inst.toxic).sum())
            if nontox + min(1, int(inst.toxic.sum())) < k:   # no selection can satisfy "at most one toxic"
                results.append({"instance": I["name"], "n": I["n"], "k": k, "seed": I["seed"], "ids": I["ids"], "toxicRule": "at_most_one",
                                "toxicInInstance": int(inst.toxic.sum()), "infeasible": f"only {nontox} non-toxic candidates: no {k}-panel has at most one toxic"})
                continue
            row = {"instance": I["name"], "n": I["n"], "k": k, "seed": I["seed"], "ids": I["ids"], "toxicRule": "at_most_one",
                   "toxicInInstance": int(inst.toxic.sum()), "P": inst.P, "P_tox": inst.P_tox, "classical": classical(inst, cfg)}
            fo, fm = row["classical"]["exact"]["f"], row["classical"]["fMin"]
            if I["n"] <= 20:
                f, feas = Q.all_objectives(inst)
                optimal = feas & (np.abs(f - fo) < 1e-9)
                row["feasibleSelections"] = int(feas.sum())
                row["uniformPOptimum"] = float(optimal.sum() / feas.sum())
                row["randomFeasibleAr"] = float(((f[feas] - fm) / (fo - fm)).mean()) if fo != fm else 1.0
            else:  # too large to enumerate: random feasible baseline by sampling (seeded)
                rng = random.Random(cfg["instances"]["seed"])
                vals = []
                n_, idx = I["n"], list(range(I["n"]))
                tox, non = [i for i in idx if inst.toxic[i]], [i for i in idx if not inst.toxic[i]]
                while len(vals) < 20000:
                    S = rng.sample(idx, k)
                    if sum(inst.toxic[i] for i in S) <= 1:
                        x = np.zeros(n_); x[S] = 1
                        vals.append(Q.objective(inst, x))
                row["randomFeasibleAr"] = float(np.mean([(v - fm) / (fo - fm) for v in vals])) if fo != fm else 1.0
                row["randomFeasibleSamples"] = len(vals)
            if qaoa_on and I["n"] in cfg["qaoa"]["sizes"] and k == cfg["qaoa"]["k"]:
                row["qaoa"] = [qaoa_run(inst, v, p, cfg, fo, fm, f, feas, heavy) for v in ("penalty", "xy") for p in cfg["qaoa"]["depths"]]
            results.append(row)
            print(row["instance"], k, "done", round(time.perf_counter() - t0, 1), "s", flush=True)
    bench = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "config": cfg, "versions": _versions(),
             "poolSize": len(cands), "vmax": vmax, "results": results,
             "seeds": {"instances": f"{cfg['instances']['seed']} + 1000*n + i", "anneal": cfg["classical"]["sa_seeds"],
                       "qaoa": cfg["qaoa"]["seed"], "restartInit": "qaoa.seed + 17*p + (0 penalty | 1 xy)", "shots": cfg["qaoa"]["seed"]},
             "hardware": {"ibmQuantum": "not used: no IBM Quantum account or token on this machine, and none was created",
                          "ionqQollab": "not used: needs the project lead's own account",
                          "substitute": "parametric noise-model simulation (Qiskit Aer)"}}
    if qaoa_on:
        small = [r for r in results if r["n"] <= 12 and "qaoa" in r]
        if small:
            def score(r):  # best noise-free XY result at the smallest depth reaching it
                return max(q["exact"]["pOptimum"] for q in r["qaoa"])
            pick = max(small, key=score)
            best = {}
            for v in ("penalty", "xy"):
                qs = [q for q in pick["qaoa"] if q["variant"] == v]
                b = max(qs, key=lambda q: (q["exact"]["pOptimum"], -q["p"]))
                best[v] = {"p": b["p"], "bestTheta": b["bestTheta"]}
            cmap = {c["id"]: c for c in cands}
            inst = Q.build([cmap[i] for i in pick["ids"]], pick["k"], w, vmax, "at_most_one", margin)
            f, feas = Q.all_objectives(inst)
            bench["noise"] = {**noise_study(inst, cfg, best, pick["classical"]["exact"]["f"], pick["classical"]["fMin"], f, feas, heavy),
                              "instanceName": pick["instance"], "k": pick["k"]}
    bench["seconds"] = time.perf_counter() - t0
    bench["figures"] = figures(bench)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "benchmark.json").write_text(json.dumps(bench, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)) + "\n")
    pn = panel(cands, cfg, vmax)
    (OUT / "panel.json").write_text(json.dumps(pn, indent=1, ensure_ascii=False) + "\n")
    return {"instances": len(results), "seconds": round(bench["seconds"], 1), "figures": bench["figures"], "defaultPanel": pn["default"]}
