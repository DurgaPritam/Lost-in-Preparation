"""Phase 8 outputs from data/interim/m8/{benchmark,panel}.json:
  site-data/lab_panel.json   (contract v1.9, P40 proposed)
  docs/QUANTUM_RESULTS.md    (generated; every number comes from the two files)
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from contract import models as C

from ..paths import INTERIM, ROOT, SITE_DATA
from .pool import CONFIG

DOC = ROOT / "docs" / "QUANTUM_RESULTS.md"


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return float(np.mean(xs)) if xs else None


def summary_rows(bench: dict) -> list[dict]:
    rows = [r for r in bench["results"] if "classical" in r]
    out = []
    for (n, k) in sorted({(r["n"], r["k"]) for r in rows}):
        rs = [r for r in rows if r["n"] == n and r["k"] == k]
        out.append({"n": n, "k": k, "solver": "exact", "instances": len(rs), "meanApproximationRatio": 1.0,
                    "meanSeconds": _mean([r["classical"]["exact"]["seconds"] for r in rs])})
        out.append({"n": n, "k": k, "solver": "greedy", "instances": len(rs), "meanApproximationRatio": _mean([r["classical"]["greedy"]["ar"] for r in rs]),
                    "pOptimum": _mean([float(r["classical"]["greedy"]["optimal"]) for r in rs]),
                    "meanSeconds": _mean([r["classical"]["greedy"]["seconds"] for r in rs])})
        out.append({"n": n, "k": k, "solver": "anneal", "instances": len(rs), "meanApproximationRatio": _mean([r["classical"]["anneal"]["meanAr"] for r in rs]),
                    "pOptimum": _mean([r["classical"]["anneal"]["successRate"] for r in rs]),
                    "meanSeconds": _mean([r["classical"]["anneal"]["meanSeconds"] for r in rs])})
        out.append({"n": n, "k": k, "solver": "random", "instances": len(rs), "meanApproximationRatio": _mean([r.get("randomFeasibleAr") for r in rs]),
                    "pOptimum": _mean([r.get("uniformPOptimum") for r in rs])})
        for variant in ("penalty", "xy"):
            for p in bench["config"]["qaoa"]["depths"]:
                qs = [q for r in rs for q in r.get("qaoa", []) if q["variant"] == variant and q["p"] == p]
                if not qs:
                    continue
                out.append({"n": n, "k": k, "solver": f"qaoa-{variant}", "p": p, "instances": len(qs),
                            "meanApproximationRatio": _mean([q["exact"]["expectedArFeasible"] for q in qs]),
                            "pOptimum": _mean([q["exact"]["pOptimum"] for q in qs]), "feasibility": _mean([q["exact"]["feasibility"] for q in qs]),
                            "meanSeconds": _mean([q["seconds"] for q in qs]),
                            "twoQubitGatesAllToAll": int(round(_mean([q["circuit"]["allToAll"]["twoQubit"] for q in qs]))),
                            "twoQubitGatesHeavyHex": int(round(_mean([q["circuit"]["heavyHex"]["twoQubit"] for q in qs]))),
                            "depthAllToAll": int(round(_mean([q["circuit"]["allToAll"]["depth"] for q in qs])))})
    return out


def winners(bench: dict, k: int = 4) -> dict[str, str]:
    """n -> which method wins at that size (k = 4).
    Classical: the fastest method whose returned panel was optimal on every instance; only the ILP also proves it.
    QAOA is reported against a uniform random feasible panel: an optimum among 4096 shots is no evidence on its own,
    because 4096 uniform samples would usually contain it too at these sizes."""
    rows = [r for r in bench["results"] if "classical" in r and r["k"] == k]
    out = {}
    for n in sorted({r["n"] for r in rows}):
        rs = [r for r in rows if r["n"] == n]
        cand = {"exact ILP": _mean([r["classical"]["exact"]["seconds"] for r in rs])}
        if all(r["classical"]["greedy"]["optimal"] for r in rs):
            cand["greedy"] = _mean([r["classical"]["greedy"]["seconds"] for r in rs])
        if all(r["classical"]["anneal"]["successRate"] == 1.0 for r in rs):
            cand["simulated annealing"] = _mean([r["classical"]["anneal"]["meanSeconds"] for r in rs])
        best = min(cand.items(), key=lambda kv: kv[1])
        text = (f"{best[0]} ({best[1]:.3g} s mean) is the fastest to return the optimum on every instance; "
                f"also optimal every time: {', '.join(sorted(k_ for k_ in cand if k_ != best[0])) or 'none'}; only the ILP proves optimality")
        qs = [(v, p, _mean([q["exact"]["pOptimum"] for r in rs for q in r.get("qaoa", []) if q["variant"] == v and q["p"] == p]))
              for v in ("penalty", "xy") for p in bench["config"]["qaoa"]["depths"]]
        qs = [x for x in qs if x[2] is not None]
        if qs:
            v, p, po = max(qs, key=lambda x: x[2])
            uni = _mean([r.get("uniformPOptimum") for r in rs])
            text += (f". QAOA (simulated): best mean P(optimum) {po:.3f} ({v} mixer, p = {p}) vs {uni:.3f} for a uniform random "
                     f"feasible panel, i.e. {po / uni:.2f}× uniform")
        out[str(n)] = text
    return out


def run() -> dict:
    bench = json.loads((INTERIM / "m8" / "benchmark.json").read_text())
    pn = json.loads((INTERIM / "m8" / "panel.json").read_text())
    cfg = bench["config"]
    d = pn["panels"][pn["default"]]
    lp = C.LabPanel(
        basis="exact_optimisation_of_model_outputs",
        label="recommended re-test panel: exact optimum of a fixed objective over model predictions; hypotheses worth re-testing, never claims that a preparation works or is safe",
        toxicRule=d["toxicRule"], k=d["k"], weights=pn["weights"], penaltyMargin=cfg["objective"]["penalty_margin"],
        configSha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(), poolSize=bench["poolSize"],
        panel=[C.PanelCandidate(**{**c, "indication": C.MeshTerm(**c["indication"]), "gap": C.PanelGap(**c["gap"]),
                                   "evidenceTrail": [C.EvidenceItem(**e) for e in c["evidenceTrail"]]}) for c in d["candidates"]],
        alternatives=[C.PanelAlternative(toxicRule=v["toxicRule"], k=v["k"], poolSize=v["poolSize"], objective=round(v["objective"], 6),
                                         candidateIds=[c["candidateId"] for c in v["candidates"]], coverage=v["coverage"])
                      for key, v in pn["panels"].items() if key != pn["default"]],
        sensitivity=[C.PanelSensitivity(**s) for s in pn["sensitivity"]],
        benchmark=[C.BenchmarkRow(**r) for r in summary_rows(bench)],
        winnerBySize=winners(bench),
        noise=[C.NoiseRow(**r) for r in bench.get("noise", {}).get("rows", [])],
        noiseModel=bench.get("noise", {}).get("model", "not run"),
        hardware=bench["hardware"], versions=bench["versions"], seeds={k: str(v) for k, v in bench["seeds"].items()},
        generatedAt=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    (SITE_DATA / "lab_panel.json").write_text(lp.model_dump_json(indent=1) + "\n")
    DOC.write_text(report(bench, pn, lp))
    return {"panel": [c.candidateId for c in lp.panel], "winnerBySize": lp.winnerBySize}


def _f(x, fmt="{:.3f}"):
    return "—" if x is None else fmt.format(x)


def report(bench: dict, pn: dict, lp: C.LabPanel) -> str:
    cfg = bench["config"]
    L = ["# Phase 8 results: choosing a re-test panel (generated)", "",
         "Generated by `python -m lip m8 bench` and `pipeline/lip/m8/export.py` from `data/interim/m8/benchmark.json` and "
         "`data/interim/m8/panel.json`. Do not edit by hand. The formulation is in [QUBO.md](QUBO.md).", "",
         "The panel optimises **model predictions**. Each entry is a hypothesis worth re-testing, never a claim that a "
         "preparation works or is safe.", "",
         f"## The recommended panel (exact solver, full pool, k = {lp.k}, toxic rule `{lp.toxicRule}`)", "",
         f"Pool: {lp.poolSize} candidates (see `data/interim/m8/pool.json`). Weights: "
         + ", ".join(f"{k} = {v}" for k, v in lp.weights.items()) + ".", "",
         "| # | Species | Historical preparation | Modern comparator | Indication | Robust gap (5th / 50th / 95th) | Compounds likely to differ | Toxicity |",
         "|---|---|---|---|---|---|---|---|"]
    for c in lp.panel:
        L.append(f"| {c.position} | *{c.species}* | {c.historicalPreparation} | {c.modernComparator}{' (default)' if c.modernComparatorBasis == 'default' else ''} | "
                 f"{c.indication.label} | {c.gap.p5:.3f} / {c.gap.p50:.3f} / {c.gap.p95:.3f} | {c.compoundsLikelyToDiffer} | {c.toxicity} |")
    low = [c for c in lp.panel if c.compoundsLikelyToDiffer == 0]
    if low:
        L += ["", "**Selected on coverage, not value:** " + "; ".join(f"*{c.species}* {c.historicalPreparation} vs {c.modernComparator} (robust gap "
              f"{c.gap.p5:.3f}, no compound likely to differ)" for c in low) + ". The coverage terms count attributes without a cap, so a "
              "candidate with several attested indications or a new preparation type can enter with a small gap (QUBO.md §2). The weights were "
              "fixed before the comparison and are not changed here."]
    L += ["", "Every panel entry carries its caveats and evidence trail in `site-data/lab_panel.json`.", "",
          "### Other panel sizes and the toxic rule", "", "| Toxic rule | k | Pool | Objective | Coverage (classes / indications / preparations) | Panel |", "|---|---|---|---|---|---|"]
    for a in lp.alternatives:
        L.append(f"| {a.toxicRule} | {a.k} | {a.poolSize} | {a.objective:.4f} | {a.coverage['class']} / {a.coverage['indication']} / {a.coverage['prep']} | "
                 + "; ".join(i.split('|', 1)[1] + f" ({next((c['species'] for c in json.loads((INTERIM / 'm8' / 'pool.json').read_text())['candidates'] if c['id'] == i), i)})" for i in a.candidateIds) + " |")
    L += ["", "### Weight sensitivity (each weight ×0.5 and ×2, others fixed)", "", "| Weight | Factor | Jaccard with the default panel | Added | Removed |", "|---|---|---|---|---|"]
    for s in lp.sensitivity:
        L.append(f"| {s.weight} | {s.factor} | {s.jaccardWithDefault:.2f} | {'; '.join(s.added) or '—'} | {'; '.join(s.removed) or '—'} |")
    L += ["", "## Benchmark", "",
          f"Instances: sizes {cfg['instances']['sizes']} ({cfg['instances']['per_size']} sampled per size, seed {cfg['instances']['seed']} + 1000·n + i), plus the full pool. "
          f"Benchmark instances use the `at_most_one` toxic rule, so that term is exercised. Annealing seeds {cfg['classical']['sa_seeds']}. "
          f"QAOA: n ∈ {cfg['qaoa']['sizes']}, k = {cfg['qaoa']['k']}, p ∈ {cfg['qaoa']['depths']}, {cfg['qaoa']['optimizer']} (maxiter {cfg['qaoa']['maxiter']}) "
          f"from {cfg['qaoa']['restarts']} random restarts, seed {cfg['qaoa']['seed']}, {cfg['qaoa']['shots']} shots. Versions: "
          + ", ".join(f"{k} {v}" for k, v in lp.versions.items()) + ".", ""]
    infeasible = [r for r in bench["results"] if "infeasible" in r]
    if infeasible:
        L += ["Skipped as infeasible: " + "; ".join(f"{r['instance']} k = {r['k']} ({r['infeasible']})" for r in infeasible) + ".", ""]
    L += ["### Approximation ratio, success and runtime (k = 4)", "",
          "| n | Solver | Depth | Instances | Mean AR | P(optimum) | Feasibility | Mean seconds | CX all-to-all | CX heavy-hex | Depth (all-to-all) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in lp.benchmark:
        if r.k != 4:
            continue
        L.append(f"| {r.n} | {r.solver} | {r.p or '—'} | {r.instances} | {_f(r.meanApproximationRatio)} | {_f(r.pOptimum)} | {_f(r.feasibility)} | "
                 f"{_f(r.meanSeconds, '{:.3g}')} | {r.twoQubitGatesAllToAll or '—'} | {r.twoQubitGatesHeavyHex or '—'} | {r.depthAllToAll or '—'} |")
    L += ["", "For greedy and annealing, P(optimum) is the share of instances (greedy) or of runs (annealing) that returned an optimal panel. "
          "For QAOA it is the exact statevector probability of sampling one, and for random it is the uniform probability over feasible panels.",
          "Feasibility counts both constraints: exactly k selected and at most one toxic. The XY ansatz keeps exactly k selected with probability 1 "
          "(Dicke start and Hamming-weight-preserving mixer, both tested), so its shortfall below 1 is panels with two or more toxic candidates, "
          "which only the cost penalises. The penalty ansatz misses both constraints.", "",
          "### Classical results at k = 6 and 8", "", "| n | k | Greedy mean AR | Annealing mean AR | Annealing success | Exact mean seconds |", "|---|---|---|---|---|---|"]
    by = defaultdict(dict)
    for r in lp.benchmark:
        by[(r.n, r.k)][r.solver] = r
    for (n, k), v in sorted(by.items()):
        if k == 4:
            continue
        L.append(f"| {n} | {k} | {_f(v['greedy'].meanApproximationRatio)} | {_f(v['anneal'].meanApproximationRatio)} | {_f(v['anneal'].pOptimum)} | {_f(v['exact'].meanSeconds, '{:.3g}')} |")
    L += ["", "### Which method wins at each size (k = 4)", ""]
    L += [f"- n = {n}: {w}" for n, w in lp.winnerBySize.items()]
    nz = bench.get("noise")
    if nz:
        L += ["", f"## Noise ({nz['model']})", "",
              f"Instance {nz['instanceName']} (k = {nz['k']}). Each variant runs at the depth with its best noise-free P(optimum), with its noise-free optimal parameters "
              f"(not re-optimised under noise). Uniform P(optimum) over feasible panels: {nz['uniformPOptimum']:.3f}; random feasible AR {nz['randomFeasibleAr']:.3f}.", "",
              "| Variant | p | 2-qubit error | 1-qubit error | Readout | P(optimum) | Feasibility | Mean AR (feasible) |", "|---|---|---|---|---|---|---|---|"]
        for r in lp.noise:
            L.append(f"| {r.variant} | {r.p} | {r.twoQubitError} | {r.oneQubitError:.4f} | {r.readoutError} | {r.pOptimum:.3f} | {r.feasibility:.3f} | {_f(r.meanArFeasible)} |")
    L += ["", "## Hardware", ""] + [f"- **{k}:** {v}" for k, v in lp.hardware.items()]
    L += ["", "## Figures", ""] + [f"![{f.rsplit('/', 1)[-1]}]({f.replace('docs/', '')})" for f in bench["figures"]]
    return "\n".join(L) + "\n"
