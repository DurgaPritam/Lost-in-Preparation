"""The re-test panel objective and its QUBO (docs/QUBO.md). Every symbol here is defined there.

Maximise over x in {0,1}^n with sum(x) = k:
    f(x) = (alpha/k) * sum_i v_i x_i                                         robust value
         + sum_F (beta_F/k) * sum_{a in F} [ sum_i A_ia x_i - sum_{i<j} A_ia A_ja x_i x_j ]   coverage (2nd-order surrogate)
         - (gamma / C(k,2)) * sum_{i<j} J_ij x_i x_j                          redundancy
v_i = gapP5_i / max gapP5 over the pool; F in {compound class, indication, preparation type}; J_ij = Jaccard overlap of
the compound sets likely to differ. As a QUBO (minimise):
    E(x) = -f(x) + P * (sum(x) - k)^2 [+ P_tox * sum_{i<j toxic} x_i x_j]
f is linear + quadratic: f(x) = h.x + sum_{i<j} q_ij x_i x_j, with h_i >= 0 and q_ij <= 0.
"""
from __future__ import annotations

import itertools
import math
import random
import time
from dataclasses import dataclass

import numpy as np

FAMILIES = ("class", "indication", "prep")


@dataclass
class Instance:
    ids: list[str]
    k: int
    h: np.ndarray            # linear coefficients of f
    q: np.ndarray            # symmetric, zero diagonal: f quadratic part = 0.5 * x^T q x  (= sum_{i<j} q_ij x_i x_j)
    toxic: np.ndarray        # bool
    toxic_rule: str          # "exclude" handled by the caller; "at_most_one" adds P_tox
    P: float
    P_tox: float
    weights: dict
    species: np.ndarray | None = None   # species label per candidate (v2)
    per_species: int | None = None      # at most this many per species (v2); 1 has a QUBO form, 2 is ILP-only
    P_sp: float = 0.0


def attributes(c: dict) -> dict[str, set[str]]:
    return {"class": set(c["classes"]), "indication": set(c["indications"]), "prep": {c["historical"]}}


def jaccard(a: set, b: set) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def build(cands: list[dict], k: int, w: dict, vmax: float, toxic_rule: str = "at_most_one", margin: float = 1.25,
          per_species: int | None = None) -> Instance:
    n = len(cands)
    attrs = [attributes(c) for c in cands]
    diff = [set(c["differs"]) for c in cands]
    pairs_k = k * (k - 1) / 2
    beta = {"class": w["beta_class"], "indication": w["beta_indication"], "prep": w["beta_prep"]}
    h = np.array([w["alpha"] / k * (c["gapP5"] / vmax) + sum(beta[F] / k * len(attrs[i][F]) for F in FAMILIES)
                  for i, c in enumerate(cands)])
    q = np.zeros((n, n))
    for i, j in itertools.combinations(range(n), 2):
        v = -sum(beta[F] / k * len(attrs[i][F] & attrs[j][F]) for F in FAMILIES) - w["gamma"] / pairs_k * jaccard(diff[i], diff[j])
        q[i, j] = q[j, i] = v
    # Penalty (docs/QUBO.md): one bit flip changes -f by at most B = max_i (|h_i| + sum_j |q_ij|); P > B makes every
    # minimiser of E feasible. The toxic swap argument needs two flips, so P_tox > 2B.
    B = float(np.max(np.abs(h) + np.abs(q).sum(1))) if n else 0.0
    toxic = np.array([c["toxic"] for c in cands], bool)
    species = np.array([c["speciesId"] for c in cands]) if cands else np.array([])
    # v2 (docs/QUBO_v2_RULE.md): at most one per species; repairing takes two flips, so P_sp = 2 * margin * B.
    return Instance([c["id"] for c in cands], k, h, q, toxic, toxic_rule, margin * B, 2 * margin * B, dict(w),
                    species, per_species, 2 * margin * B if per_species == 1 else 0.0)


def _same_species(inst: Instance, i: int, j: int) -> bool:
    return inst.per_species == 1 and inst.species is not None and inst.species[i] == inst.species[j]


def objective(inst: Instance, x: np.ndarray) -> float:
    x = np.asarray(x, float)
    return float(inst.h @ x + 0.5 * x @ inst.q @ x)


def energy(inst: Instance, x: np.ndarray) -> float:
    x = np.asarray(x, float)
    e = -objective(inst, x) + inst.P * (x.sum() - inst.k) ** 2
    if inst.toxic_rule == "at_most_one":
        t = x[inst.toxic].sum()
        e += inst.P_tox * t * (t - 1) / 2
    if inst.per_species == 1:
        for s in set(inst.species.tolist()):
            m = x[inst.species == s].sum()
            e += inst.P_sp * m * (m - 1) / 2
    elif inst.per_species is not None:
        raise ValueError("only 'at most one per species' has a QUBO form; use the ILP for other limits")
    return float(e)


def qubo_matrix(inst: Instance) -> tuple[np.ndarray, float]:
    """Upper-triangular Q and constant c with E(x) = x^T Q x + c for binary x (x_i^2 = x_i on the diagonal)."""
    n, k, P = len(inst.h), inst.k, inst.P
    Q = np.zeros((n, n))
    for i in range(n):
        Q[i, i] = -inst.h[i] + P * (1 - 2 * k)
    for i, j in itertools.combinations(range(n), 2):
        Q[i, j] = (-inst.q[i, j] + 2 * P + (inst.P_tox if inst.toxic_rule == "at_most_one" and inst.toxic[i] and inst.toxic[j] else 0.0)
                   + (inst.P_sp if _same_species(inst, i, j) else 0.0))
    return Q, P * k * k


def feasible(inst: Instance, x) -> bool:
    x = np.asarray(x)
    ok = int(x.sum()) == inst.k
    if inst.toxic_rule == "at_most_one":
        ok = ok and int(x[inst.toxic].sum()) <= 1
    if inst.per_species is not None:
        ok = ok and all(int(x[inst.species == s].sum()) <= inst.per_species for s in set(inst.species.tolist()))
    return ok


def all_objectives(inst: Instance, n: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Objective and feasibility of every bitstring, in Qiskit order (bit i of the index = qubit i). n <= 24."""
    n = n or len(inst.h)
    idx = np.arange(2 ** n, dtype=np.int64)
    X = ((idx[:, None] >> np.arange(n)) & 1).astype(np.float64)
    f = X @ inst.h + 0.5 * np.einsum("bi,ij,bj->b", X, inst.q, X, optimize=True)
    w = X.sum(1)
    feas = w == inst.k
    if inst.toxic_rule == "at_most_one":
        feas &= X[:, inst.toxic].sum(1) <= 1
    if inst.per_species is not None:
        for s in set(inst.species.tolist()):
            feas &= X[:, inst.species == s].sum(1) <= inst.per_species
    return f, feas


# --- classical solvers ---------------------------------------------------------------------------------------------

def brute_force(inst: Instance) -> dict:
    t = time.perf_counter()
    n, best, worst = len(inst.h), (-math.inf, None), (math.inf, None)
    for S in itertools.combinations(range(n), inst.k):
        x = np.zeros(n)
        x[list(S)] = 1
        if not feasible(inst, x):
            continue
        v = objective(inst, x)
        if v > best[0]:
            best = (v, x.copy())
        if v < worst[0]:
            worst = (v, x.copy())
    return {"x": best[1], "f": best[0], "fMin": worst[0], "seconds": time.perf_counter() - t}


def ilp(inst: Instance, sense: str = "max") -> dict:
    """Exact optimum with PuLP/CBC. All q_ij <= 0, so y_ij >= x_i + x_j - 1, y_ij >= 0 is exact when maximising;
    minimising (for f_min, the AR baseline) needs the full linearisation y <= x_i, y <= x_j as well."""
    import pulp
    n = len(inst.h)
    prob = pulp.LpProblem("panel", pulp.LpMaximize if sense == "max" else pulp.LpMinimize)
    x = [prob.add_variable(f"x{i}", cat="Binary") for i in range(n)]
    terms = [inst.h[i] * x[i] for i in range(n)]
    for i, j in itertools.combinations(range(n), 2):
        if inst.q[i, j] != 0:
            y = prob.add_variable(f"y{i}_{j}", lowBound=0, upBound=1)
            prob += y >= x[i] + x[j] - 1
            if sense == "min":
                prob += y <= x[i]
                prob += y <= x[j]
            terms.append(inst.q[i, j] * y)
    prob += pulp.lpSum(terms)
    prob += pulp.lpSum(x) == inst.k
    if inst.toxic_rule == "at_most_one" and inst.toxic.any():
        prob += pulp.lpSum(x[i] for i in range(n) if inst.toxic[i]) <= 1
    if inst.per_species is not None:
        for s in sorted(set(inst.species.tolist())):
            prob += pulp.lpSum(x[i] for i in range(n) if inst.species[i] == s) <= inst.per_species
    t = time.perf_counter()
    import warnings
    with warnings.catch_warnings():  # PuLP 3.3 warns that its bundled CBC goes away in 4.0; pinned to 3.3.2, so it stays
        warnings.filterwarnings("ignore", message="PULP_CBC_CMD is deprecated", category=DeprecationWarning)
        status = prob.solve(pulp.PULP_CBC_CMD(msg=False, gapRel=0, gapAbs=0, threads=1))
    xs = np.array([round(v.value()) for v in x], float)
    return {"x": xs, "f": objective(inst, xs), "status": pulp.LpStatus[status], "seconds": time.perf_counter() - t}


def _partial_ok(inst: Instance, x: np.ndarray) -> bool:
    """A partial selection (sum <= k) that can still be completed: the toxic and species limits hold."""
    if inst.toxic_rule == "at_most_one" and x[inst.toxic].sum() > 1:
        return False
    if inst.per_species is not None and any(x[inst.species == s].sum() > inst.per_species for s in set(inst.species.tolist())):
        return False
    return True


def _random_feasible(inst: Instance, rng: random.Random, tries: int = 2000) -> list[int] | None:
    n = len(inst.h)
    for _ in range(tries):
        order = rng.sample(range(n), n)
        x, S = np.zeros(n), []
        for i in order:
            x[i] = 1
            if _partial_ok(inst, x):
                S.append(i)
                if len(S) == inst.k:
                    return S
            else:
                x[i] = 0
    return None


def max_selectable(inst: Instance) -> int:
    """The largest panel the toxic and species limits allow (species are either toxic-reported or not)."""
    n = len(inst.h)
    if inst.per_species is None:
        non = int((~inst.toxic).sum())
        return non + (min(1, int(inst.toxic.sum())) if inst.toxic_rule == "at_most_one" else int(inst.toxic.sum()))
    sp_non = {s for s, t in zip(inst.species.tolist(), inst.toxic.tolist()) if not t}
    sp_tox = {s for s, t in zip(inst.species.tolist(), inst.toxic.tolist()) if t}
    cnt = lambda ss: sum(min(inst.per_species, int((inst.species == s).sum())) for s in ss)
    return cnt(sp_non) + (min(1, cnt(sp_tox)) if inst.toxic_rule == "at_most_one" else cnt(sp_tox))


def greedy(inst: Instance) -> dict:
    t = time.perf_counter()
    n, x = len(inst.h), np.zeros(len(inst.h))
    for _ in range(inst.k):
        best, bi = -math.inf, None
        for i in range(n):
            if x[i]:
                continue
            x[i] = 1
            if _partial_ok(inst, x):
                v = objective(inst, x)
                if v > best:
                    best, bi = v, i
            x[i] = 0
        if bi is None:
            break
        x[bi] = 1
    return {"x": x, "f": objective(inst, x), "seconds": time.perf_counter() - t}


def anneal(inst: Instance, seed: int, sweeps: int, t0: float, t1: float) -> dict:
    """Simulated annealing on the feasible set (swap one selected for one unselected; geometric cooling)."""
    t = time.perf_counter()
    rng = random.Random(seed)
    n, k = len(inst.h), inst.k
    if inst.per_species is None:   # v1's start, unchanged, so v1 runs reproduce exactly
        nontox = [i for i in range(n) if not inst.toxic[i]]
        tox = [i for i in range(n) if inst.toxic[i]]
        if inst.toxic_rule == "at_most_one":
            start = rng.sample(nontox, min(k, len(nontox)))
            if len(start) < k:
                start += rng.sample(tox, 1)
        else:
            start = rng.sample(range(n), k)
    else:
        start = _random_feasible(inst, rng)
        if start is None:
            raise ValueError("no feasible start: the instance has no feasible panel")
    x = np.zeros(n)
    x[start] = 1
    f = objective(inst, x)
    best = (f, x.copy())
    steps = sweeps * n
    for s in range(steps):
        T = t0 * (t1 / t0) ** (s / max(1, steps - 1))
        i = rng.choice(np.flatnonzero(x).tolist())
        j = rng.choice(np.flatnonzero(1 - x).tolist())
        x[i], x[j] = 0, 1
        if not feasible(inst, x):
            x[i], x[j] = 1, 0
            continue
        g = objective(inst, x)
        if g >= f or rng.random() < math.exp((g - f) / T):
            f = g
            if f > best[0]:
                best = (f, x.copy())
        else:
            x[i], x[j] = 1, 0
    return {"x": best[1], "f": best[0], "seconds": time.perf_counter() - t, "seed": seed}


def coverage_counts(cands: list[dict], x) -> dict:
    """True coverage (distinct attributes covered), reported beside the surrogate used in f."""
    sel = [c for c, xi in zip(cands, x) if xi]
    out = {}
    for F in FAMILIES:
        out[F] = len(set().union(*[attributes(c)[F] for c in sel])) if sel else 0
    return out
