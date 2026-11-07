"""QAOA for the panel QUBO, in Qiskit (pinned in requirements-quantum.txt); docs/QUBO.md §QAOA.

Two variants on the same instance:
  penalty  |+>^n start, X mixer, cost = the full QUBO energy E (cardinality penalty P included)
  xy       Dicke |D(n,k)> start (Bärtschi & Eidenbenz 2019, split-and-cyclic-shift), ring XY mixer
           exp(-i beta (XX+YY)/2) on (even, odd, wrap) pairs, which preserves Hamming weight; cost = -f (+ the toxic
           penalty when at most one toxic is allowed). The cardinality penalty is constant on the weight-k subspace,
           so it is left out.
Bit order is Qiskit's: bit i of a basis index = qubit i = x_i. With x = (1 - z)/2 the cost is an Ising Hamiltonian
sum_i a_i Z_i + sum_{i<j} b_ij Z_i Z_j, applied as RZ(2 gamma a_i) and RZZ(2 gamma b_ij), after dividing by its
largest |coefficient| (so gamma in [0, pi] spans one period of the largest term).
Expectations are exact (Aer statevector, probabilities . energy vector); sampling uses Aer shots with a fixed seed.
"""
from __future__ import annotations

import itertools
import time

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import RYGate
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

from .qubo import Instance, qubo_matrix

BASIS = ["rz", "sx", "x", "cx"]


def ising(Q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Upper-triangular QUBO Q (x^T Q x) -> Ising (a, b) with x = (1 - z)/2, up to a constant."""
    n = len(Q)
    a = np.zeros(n)
    b = np.zeros((n, n))
    for i in range(n):
        a[i] -= Q[i, i] / 2
    for i, j in itertools.combinations(range(n), 2):
        if Q[i, j]:
            a[i] -= Q[i, j] / 4
            a[j] -= Q[i, j] / 4
            b[i, j] = Q[i, j] / 4
    return a, b


def cost_qubo(inst: Instance, variant: str) -> np.ndarray:
    """The QUBO each variant minimises (upper triangular)."""
    if variant == "penalty":
        return qubo_matrix(inst)[0]
    n = len(inst.h)
    Q = np.zeros((n, n))
    for i in range(n):
        Q[i, i] = -inst.h[i]
    for i, j in itertools.combinations(range(n), 2):
        Q[i, j] = -inst.q[i, j] + (inst.P_tox if inst.toxic_rule == "at_most_one" and inst.toxic[i] and inst.toxic[j] else 0.0)
    return Q


def energies(Q: np.ndarray, n: int) -> np.ndarray:
    idx = np.arange(2 ** n, dtype=np.int64)
    X = ((idx[:, None] >> np.arange(n)) & 1).astype(np.float64)
    return np.einsum("bi,ij,bj->b", X, np.triu(Q, 1), X, optimize=True) + X @ np.diag(Q)


def _scs(n: int, k: int) -> QuantumCircuit:
    c = QuantumCircuit(n)
    c.cx(n - 2, n - 1)
    c.cry(2 * np.arccos(np.sqrt(1 / n)), n - 1, n - 2)
    c.cx(n - 2, n - 1)
    for l in range(2, k + 1):
        c.cx(n - l - 1, n - 1)
        c.append(RYGate(2 * np.arccos(np.sqrt(l / n))).control(2, annotated=False), [n - 1, n - l, n - l - 1])
        c.cx(n - l - 1, n - 1)
    return c


def dicke(n: int, k: int) -> QuantumCircuit:
    """|D(n,k)>: uniform superposition of the C(n,k) weight-k basis states (deterministic, Bärtschi & Eidenbenz 2019)."""
    c = QuantumCircuit(n)
    c.x(range(n - k, n))
    for l in range(n, k, -1):
        c.compose(_scs(l, k), range(l), inplace=True)
    for l in range(k, 1, -1):
        c.compose(_scs(l, l - 1), range(l), inplace=True)
    return c


def ring_pairs(n: int) -> list[list[tuple[int, int]]]:
    even = [(i, i + 1) for i in range(0, n - 1, 2)]
    odd = [(i, i + 1) for i in range(1, n - 1, 2)]
    wrap = [(n - 1, 0)] if n > 2 else []
    return [even, odd, wrap]


def xy_mixer(c: QuantumCircuit, beta, n: int) -> None:
    for layer in ring_pairs(n):
        for i, j in layer:
            c.rxx(beta, i, j)
            c.ryy(beta, i, j)


def circuit(inst: Instance, variant: str, p: int) -> tuple[QuantumCircuit, ParameterVector, ParameterVector, float]:
    n = len(inst.h)
    a, b = ising(cost_qubo(inst, variant))
    scale = max(np.max(np.abs(a)), np.max(np.abs(b)), 1e-12)
    a, b = a / scale, b / scale
    g, be = ParameterVector("gamma", p), ParameterVector("beta", p)
    c = QuantumCircuit(n)
    if variant == "penalty":
        c.h(range(n))
    else:
        c.compose(dicke(n, inst.k), inplace=True)
    for layer in range(p):
        for i in range(n):
            if a[i]:
                c.rz(2 * g[layer] * a[i], i)
        for i, j in itertools.combinations(range(n), 2):
            if b[i, j]:
                c.rzz(2 * g[layer] * b[i, j], i, j)
        if variant == "penalty":
            for i in range(n):
                c.rx(2 * be[layer], i)
        else:
            xy_mixer(c, be[layer], n)
    return c, g, be, scale


def metrics_of(c: QuantumCircuit, coupling=None, seed: int = 0) -> dict:
    t = transpile(c, basis_gates=BASIS, coupling_map=coupling, optimization_level=1, seed_transpiler=seed)
    ops = t.count_ops()
    return {"depth": t.depth(), "twoQubit": int(ops.get("cx", 0)), "oneQubit": int(sum(v for k, v in ops.items() if k != "cx"))}


class Runner:
    """Exact expectations with Aer statevector for a parameterised QAOA circuit."""

    def __init__(self, inst: Instance, variant: str, p: int, seed: int):
        self.inst, self.variant, self.p, self.seed = inst, variant, p, seed
        self.n = len(inst.h)
        self.c, self.g, self.b, self.scale = circuit(inst, variant, p)
        self.sim = AerSimulator(method="statevector", seed_simulator=seed)
        sv = self.c.copy()
        sv.save_statevector()
        self.tsv = transpile(sv, self.sim, optimization_level=0)
        self.E = energies(cost_qubo(inst, variant), self.n)
        self.evals = 0

    def probs(self, theta) -> np.ndarray:
        binds = {**{self.g[i]: theta[i] for i in range(self.p)}, **{self.b[i]: theta[self.p + i] for i in range(self.p)}}
        res = self.sim.run(self.tsv.assign_parameters(binds), shots=1).result()
        self.evals += 1
        return np.abs(np.asarray(res.get_statevector())) ** 2

    def expect(self, theta) -> float:
        return float(self.probs(theta) @ self.E)

    def optimise(self, restarts: int, maxiter: int, seed: int) -> dict:
        rng = np.random.default_rng(seed)
        runs = []
        t = time.perf_counter()
        for r in range(restarts):
            x0 = np.concatenate([rng.uniform(0, np.pi, self.p), rng.uniform(0, np.pi / 2, self.p)])
            res = minimize(self.expect, x0, method="COBYLA", options={"maxiter": maxiter, "rhobeg": 0.3})
            runs.append({"restart": r, "x0": x0.round(6).tolist(), "theta": np.asarray(res.x).round(6).tolist(),
                         "expectation": float(res.fun), "nfev": int(res.nfev)})
        best = min(runs, key=lambda x: x["expectation"])
        return {"best": best, "restarts": runs, "seconds": time.perf_counter() - t, "evaluations": self.evals}

    def sample(self, theta, shots: int, seed: int, noise_model=None, coupling=None) -> np.ndarray:
        """Shot counts per basis index (length 2^n)."""
        binds = {**{self.g[i]: theta[i] for i in range(self.p)}, **{self.b[i]: theta[self.p + i] for i in range(self.p)}}
        m = self.c.assign_parameters(binds)
        m.measure_all()
        sim = AerSimulator(method="automatic", seed_simulator=seed, noise_model=noise_model)
        tm = transpile(m, basis_gates=BASIS if (noise_model or coupling) else None, coupling_map=coupling,
                       optimization_level=1, seed_transpiler=seed) if (noise_model or coupling) else transpile(m, sim)
        counts = sim.run(tm, shots=shots).result().get_counts()
        out = np.zeros(2 ** self.n)
        for bits, v in counts.items():
            out[int(bits.replace(" ", ""), 2)] += v
        return out
