"""Phase 8 outputs from data/interim/m8/{benchmark,panel}.json:
  site-data/lab_panel.json   (contract v1.9, P40; v2 amendment)
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
from .pool import CONFIGS

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


def _cand(c: dict) -> C.PanelCandidate:
    return C.PanelCandidate(**{**c, "indication": C.MeshTerm(**c["indication"]), "gap": C.PanelGap(**c["gap"]),
                               "evidenceTrail": [C.EvidenceItem(**e) for e in c["evidenceTrail"]]})


def _alt(v: dict) -> C.PanelAlternative:
    return C.PanelAlternative(toxicRule=v["toxicRule"], k=v["k"], perSpecies=v.get("perSpecies"), poolSize=v["poolSize"],
                              objective=round(v["objective"], 6), candidateIds=[c["candidateId"] for c in v["candidates"]], coverage=v["coverage"],
                              panel=[_cand(c) for c in v["candidates"]])


def v1_notes(panel: list[dict]) -> list[str]:
    """Plain notes on the original v1 result, from its data."""
    out = []
    for c in panel:
        if c["compoundsLikelyToDiffer"] == 0:
            out.append(f"Slot {c['position']} ({c['species']}, {c['historicalPreparation']} vs {c['modernComparator']}) was selected on coverage, "
                       f"not value: robust gap {c['gap']['p5']:.3f} and no compound likely to differ.")
    sp = defaultdict(int)
    for c in panel:
        sp[c["species"]] += 1
    rep = sorted(k for k, v in sp.items() if v > 1)
    if rep:
        out.append(f"Several entries share a species: {', '.join(rep)}.")
    return out


def run(bench_version: str = "v2") -> dict:
    """bench_version: which benchmark file feeds the benchmark summary (v2 once `lip m8 bench` has run)."""
    bench = json.loads((INTERIM / "m8" / f"benchmark_{bench_version}.json").read_text())
    pn = json.loads((INTERIM / "m8" / "panel_v2.json").read_text())
    p1 = json.loads((INTERIM / "m8" / "panel_v1.json").read_text())
    cfg = bench["config"]
    d = pn["panels"][pn["default"]]
    d1 = p1["panels"][p1["default"]]
    lp = C.LabPanel(
        basis="exact_optimisation_of_model_outputs",
        label="recommended re-test panel: exact optimum of a fixed objective over model predictions; hypotheses worth re-testing, never claims that a preparation works or is safe",
        ruleVersion=pn["ruleVersion"], ruleDoc="docs/QUBO_v2_RULE.md",
        toxicRule=d["toxicRule"], perSpecies=d.get("perSpecies"), k=d["k"], weights=pn["weights"], penaltyMargin=cfg["objective"]["penalty_margin"],
        configSha256=hashlib.sha256(CONFIGS["v2"].read_bytes()).hexdigest(), poolSize=d["poolSize"],
        panel=[_cand(c) for c in d["candidates"]],
        alternatives=[_alt(v) for key, v in pn["panels"].items() if key != pn["default"] and not key.endswith("perSpecies2") and not v.get("infeasible")],
        perSpeciesSensitivity=[_alt(v) for key, v in pn["panels"].items() if key.endswith("perSpecies2") and not v.get("infeasible")],
        ineligible=[C.PanelExcluded(**x) for x in pn["ineligible"]],
        excludedToxic=[C.PanelExcluded(candidateId=x["candidateId"], species=x["species"], historicalPreparation=x["historicalPreparation"],
                                       modernComparator=x["modernComparator"], reason=f"toxicity reported ({x['toxicity']})") for x in pn["excludedToxic"]],
        original=C.PanelOriginal(ruleVersion="v1", k=d1["k"], toxicRule=d1["toxicRule"], objective=round(d1["objective"], 6),
                                 configSha256=hashlib.sha256(CONFIGS["v1"].read_bytes()).hexdigest(),
                                 panel=[_cand(c) for c in d1["candidates"]], notes=v1_notes(d1["candidates"])),
        sensitivity=[C.PanelSensitivity(**s) for s in pn["sensitivity"]],
        benchmark=[C.BenchmarkRow(**r) for r in summary_rows(bench)],
        winnerBySize=winners(bench),
        noise=[C.NoiseRow(**r) for r in bench.get("noise", {}).get("rows", [])],
        noiseModel=bench.get("noise", {}).get("model", "not run"),
        hardware=bench["hardware"], versions=bench["versions"], seeds={k: str(v) for k, v in bench["seeds"].items()},
        generatedAt=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    (SITE_DATA / "lab_panel.json").write_text(lp.model_dump_json(indent=1) + "\n")
    b1 = json.loads((INTERIM / "m8" / "benchmark_v1.json").read_text())
    DOC.write_text(report(bench, pn, lp, b1, p1))
    return {"panel": [c.candidateId for c in lp.panel], "winnerBySize": lp.winnerBySize, "benchmark": bench_version}


def _f(x, fmt="{:.3f}"):
    return "—" if x is None else fmt.format(x)


def _ptable(cands) -> list[str]:
    L = ["| # | Species | Historical preparation | Modern comparator | Indication | Robust gap (5th / 50th / 95th) | Compounds likely to differ | Toxicity |",
         "|---|---|---|---|---|---|---|---|"]
    for c in cands:
        L.append(f"| {c.position} | *{c.species}* | {c.historicalPreparation} | {c.modernComparator}{' (default)' if c.modernComparatorBasis == 'default' else ''} | "
                 f"{c.indication.label} | {c.gap.p5:.3f} / {c.gap.p50:.3f} / {c.gap.p95:.3f} | {c.compoundsLikelyToDiffer} | {c.toxicity} |")
    return L


def _bench_section(bench: dict, lp_rows: list, winners_: dict, title: str) -> list[str]:
    cfg = bench["config"]
    L = [f"## {title}", "",
         f"Instances: sizes {cfg['instances']['sizes']} ({cfg['instances']['per_size']} sampled per size, seed {cfg['instances']['seed']} + 1000·n + i), plus the full "
         f"{bench['ruleVersion']} pool ({bench['poolSize']} candidates). Constraints: at most one toxic"
         + (f", at most {cfg['rule']['per_species']} per species" if cfg.get("rule") else "") + f". Annealing seeds {cfg['classical']['sa_seeds']}. "
         f"QAOA: n ∈ {cfg['qaoa']['sizes']}, k = {cfg['qaoa']['k']}, p ∈ {cfg['qaoa']['depths']}, {cfg['qaoa']['optimizer']} (maxiter {cfg['qaoa']['maxiter']}) "
         f"from {cfg['qaoa']['restarts']} random restarts, seed {cfg['qaoa']['seed']}, {cfg['qaoa']['shots']} shots. Versions: "
         + ", ".join(f"{k} {v}" for k, v in bench["versions"].items()) + ".", ""]
    infeasible = [r for r in bench["results"] if "infeasible" in r]
    if infeasible:
        L += ["Skipped as infeasible: " + "; ".join(f"{r['instance']} k = {r['k']} ({r['infeasible']})" for r in infeasible) + ".", ""]
    L += ["| n | Solver | Depth | Instances | Mean AR | P(optimum) | Feasibility | Mean seconds | CX all-to-all | CX heavy-hex | Depth (all-to-all) |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in lp_rows:
        if r.k != 4:
            continue
        L.append(f"| {r.n} | {r.solver} | {r.p or '—'} | {r.instances} | {_f(r.meanApproximationRatio)} | {_f(r.pOptimum)} | {_f(r.feasibility)} | "
                 f"{_f(r.meanSeconds, '{:.3g}')} | {r.twoQubitGatesAllToAll or '—'} | {r.twoQubitGatesHeavyHex or '—'} | {r.depthAllToAll or '—'} |")
    L += ["", "Notes on the columns:",
          "- **P(optimum):** for greedy and annealing, the share of instances (greedy) or runs (annealing) that returned an optimal panel. For QAOA, the "
          "exact statevector probability of sampling one. For random, the uniform probability over feasible panels.",
          "- **Feasibility** counts every constraint. The XY ansatz keeps exactly k selected with probability 1 (Dicke start and Hamming-weight-preserving "
          "mixer, both tested), so its shortfall below 1 is panels that break the toxic or species limit, which only the cost penalises. The penalty "
          "ansatz can break any constraint.", "",
          "### Which method wins at each size (k = 4)", ""]
    L += [f"- n = {n}: {w}" for n, w in winners_.items()]
    nz = bench.get("noise")
    if nz:
        L += ["", f"### Noise ({nz['model']})", "",
              f"Instance {nz['instanceName']} (k = {nz['k']}). Each variant runs at the depth with its best noise-free P(optimum), with its noise-free optimal "
              f"parameters (not re-optimised under noise). Uniform P(optimum) over feasible panels: {nz['uniformPOptimum']:.3f}; random feasible AR {nz['randomFeasibleAr']:.3f}.", "",
              "| Variant | p | 2-qubit error | 1-qubit error | Readout | P(optimum) | Feasibility | Mean AR (feasible) |", "|---|---|---|---|---|---|---|---|"]
        for r in nz["rows"]:
            L.append(f"| {r['variant']} | {r['p']} | {r['twoQubitError']} | {r['oneQubitError']:.4f} | {r['readoutError']} | {r['pOptimum']:.3f} | {r['feasibility']:.3f} | {_f(r['meanArFeasible'])} |")
    L += ["", "Figures:", ""] + [f"![{f.rsplit('/', 1)[-1]}]({f.replace('docs/', '')})" for f in bench["figures"]]
    return L


def report(bench: dict, pn: dict, lp: C.LabPanel, b1: dict, p1: dict) -> str:
    pool = {c["id"]: c for c in json.loads((INTERIM / "m8" / "pool.json").read_text())["candidates"]}
    name = lambda i: f"*{pool[i]['species']}* {pool[i]['historical']}" if i in pool else i
    L = ["# Phase 8 results: choosing a re-test panel (generated)", "",
         "Generated by `python -m lip m8 bench` and `pipeline/lip/m8/export.py` from `data/interim/m8/` (benchmark_v2, panel_v2, and the v1 files). "
         "Do not edit by hand. The formulation is in [QUBO.md](QUBO.md); the v2 rule, pre-registered before any v2 run, is in [QUBO_v2_RULE.md](QUBO_v2_RULE.md).", "",
         "The panel optimises **model predictions**. Each entry is a hypothesis worth re-testing, never a claim that a preparation works or is safe.", "",
         f"## The displayed panel: v2 (exact solver, k = {lp.k}, toxic-reported species excluded, at most {lp.perSpecies} per species)", "",
         f"Eligible pool after the v2 rule: {lp.poolSize} candidates. Weights unchanged from v1: " + ", ".join(f"{k} = {v}" for k, v in lp.weights.items()) + ".", ""]
    L += _ptable(lp.panel)
    L += ["", "**Not eligible under v2:** " + ("; ".join(f"*{x.species}* {x.historicalPreparation} vs {x.modernComparator} ({x.reason})" for x in lp.ineligible) or "none") + ".",
          "", f"**Excluded because toxicity is reported ({len(lp.excludedToxic)}):** " + "; ".join(f"*{x.species}* {x.historicalPreparation} vs {x.modernComparator}" for x in lp.excludedToxic) + ".", ""]
    o = lp.original
    L += [f"## v1 and v2 side by side (k = {lp.k})", "",
          "| Slot | v1 (original result) | v2 (displayed) |", "|---|---|---|"]
    for i in range(max(len(o.panel), len(lp.panel))):
        a = o.panel[i] if i < len(o.panel) else None
        b = lp.panel[i] if i < len(lp.panel) else None
        L.append(f"| {i + 1} | {f'*{a.species}* {a.historicalPreparation} (gap {a.gap.p5:.3f})' if a else '—'} | {f'*{b.species}* {b.historicalPreparation} (gap {b.gap.p5:.3f})' if b else '—'} |")
    L += ["", f"Objective: v1 {o.objective:.4f}, v2 {pn['panels'][pn['default']]['objective']:.4f}. "
          "They are not directly comparable: v2 optimises over a smaller set under stricter constraints, so its optimum can only be lower or equal.", ""]
    L += [f"- **v1 note:** {n}" for n in o.notes]
    L += ["", "### Other panel sizes, and at most two per species (sensitivity)", "",
          "| Rule | k | Pool | Objective | Coverage (classes / indications / preparations) | Panel |", "|---|---|---|---|---|---|"]
    for a in [*lp.alternatives, *lp.perSpeciesSensitivity]:
        L.append(f"| v2, ≤{a.perSpecies}/species | {a.k} | {a.poolSize} | {a.objective:.4f} | {a.coverage['class']} / {a.coverage['indication']} / {a.coverage['prep']} | "
                 + "; ".join(name(i) for i in a.candidateIds) + " |")
    L += ["", "### Weight sensitivity of the v2 panel (each weight ×0.5 and ×2, others fixed)", "",
          "| Weight | Factor | Jaccard with the default panel | Added | Removed |", "|---|---|---|---|---|"]
    for s_ in lp.sensitivity:
        L.append(f"| {s_.weight} | {s_.factor} | {s_.jaccardWithDefault:.2f} | {'; '.join(name(i) for i in s_.added) or '—'} | {'; '.join(name(i) for i in s_.removed) or '—'} |")
    L += [""] + _bench_section(bench, lp.benchmark, lp.winnerBySize, f"Benchmark ({bench['ruleVersion']} instances)")
    if bench["ruleVersion"] != "v1":
        L += ["", "## The v1 benchmark (original instances, kept for comparison)", ""] + [f"- n = {n}: {w}" for n, w in winners(b1).items()]
        L += ["", "Full v1 tables: `data/interim/m8/benchmark_v1.json`; v1 figures in `docs/figures/m8/v1/`."]
    L += ["", "## Hardware", ""] + [f"- **{k}:** {v}" for k, v in lp.hardware.items()]
    return "\n".join(L) + "\n"
