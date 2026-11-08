"""Phase 8 tests (docs/QUBO.md): the QUBO energy equals the objective; the penalty makes every minimiser feasible;
the XY mixer preserves Hamming weight; the Dicke state is uniform on weight k; feasibility counting is correct; the
Ising form reproduces the QUBO. Uses a small synthetic pool, so it needs neither the data cache nor network."""
import itertools

import numpy as np
import pytest

from lip.m8 import qubo as Q

qiskit = pytest.importorskip("qiskit", reason="Phase 8 needs requirements-quantum.txt (pip install -r requirements-quantum.txt)")
pytest.importorskip("qiskit_aer", reason="Phase 8 needs requirements-quantum.txt")

W = {"alpha": 1.0, "beta_class": 0.2, "beta_indication": 0.2, "beta_prep": 0.2, "gamma": 0.5}


def _pool(n=7, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        out.append({"id": f"c{i}", "speciesId": f"s{i // 2}", "gapP5": float(rng.uniform(0.01, 0.3)), "toxic": bool(i % 3 == 0),
                    "classes": sorted(rng.choice(["a", "b", "c", "d"], rng.integers(1, 4), replace=False).tolist()),
                    "indications": sorted(rng.choice(["m1", "m2", "m3", "m4", "m5"], rng.integers(1, 3), replace=False).tolist()),
                    "historical": str(rng.choice(["decoction", "juice", "wine"])),
                    "differs": sorted(rng.choice([f"k{j}" for j in range(12)], rng.integers(0, 8), replace=False).tolist())})
    return out


def _inst(rule="at_most_one", k=3, n=7):
    c = _pool(n)
    return Q.build(c, k, W, max(x["gapP5"] for x in c), rule), c


def test_energy_of_a_known_selection_equals_the_objective():
    inst, c = _inst()
    x = np.zeros(len(c)); x[[1, 2, 4]] = 1          # feasible: k = 3, no toxic (0, 3, 6 are toxic)
    # the objective by hand, term by term, from the definitions in docs/QUBO.md
    k, vmax = 3, max(y["gapP5"] for y in c)
    S = [c[i] for i in (1, 2, 4)]
    value = W["alpha"] / k * sum(s["gapP5"] / vmax for s in S)
    cov = 0.0
    for fam, key in (("beta_class", "classes"), ("beta_indication", "indications"), ("beta_prep", "historical")):
        sets = [set(s[key]) if key != "historical" else {s[key]} for s in S]
        for a in set().union(*sets):
            na = sum(a in z for z in sets)
            cov += W[fam] / k * (na - na * (na - 1) / 2)
    red = sum(Q.jaccard(set(a["differs"]), set(b["differs"])) for a, b in itertools.combinations(S, 2)) * W["gamma"] / (k * (k - 1) / 2)
    f = value + cov - red
    assert Q.objective(inst, x) == pytest.approx(f, abs=1e-12)
    assert Q.energy(inst, x) == pytest.approx(-f, abs=1e-12)
    Qm, const = Q.qubo_matrix(inst)
    assert float(x @ Qm @ x + const) == pytest.approx(-f, abs=1e-12)


def test_qubo_matrix_equals_energy_everywhere_and_minimisers_are_feasible():
    for rule in ("at_most_one", "exclude"):
        inst, c = _inst(rule)
        Qm, const = Q.qubo_matrix(inst)
        n = len(c)
        E = []
        for bits in itertools.product([0, 1], repeat=n):
            x = np.array(bits, float)
            e = Q.energy(inst, x)
            assert float(x @ Qm @ x + const) == pytest.approx(e, abs=1e-9)
            E.append((e, bits))
        e_min, best = min(E)
        assert Q.feasible(inst, np.array(best))             # the penalty argument in docs/QUBO.md
        assert -e_min == pytest.approx(Q.ilp(inst)["f"], abs=1e-9)


def test_feasibility_counting():
    inst, c = _inst("at_most_one", k=3)
    f, feas = Q.all_objectives(inst)
    n, tox = len(c), [i for i in range(len(c)) if c[i]["toxic"]]
    expected = sum(1 for S in itertools.combinations(range(n), 3) if sum(i in tox for i in S) <= 1)
    assert int(feas.sum()) == expected
    inst2, _ = _inst("exclude", k=3)
    assert int(Q.all_objectives(inst2)[1].sum()) == len(list(itertools.combinations(range(n), 3)))
    # every enumerated objective matches the direct evaluation (Qiskit bit order: bit i of the index = x_i)
    for b in (0b0010110, 0b1000011, 0b0111000):
        x = np.array([(b >> i) & 1 for i in range(n)], float)
        assert f[b] == pytest.approx(Q.objective(inst, x), abs=1e-12)


def test_xy_mixer_preserves_hamming_weight():
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from lip.m8.qaoa import xy_mixer
    n, k = 6, 2
    rng = np.random.default_rng(3)
    w = np.array([bin(i).count("1") for i in range(2 ** n)])
    amp = np.where(w == k, rng.normal(size=2 ** n) + 1j * rng.normal(size=2 ** n), 0)
    amp /= np.linalg.norm(amp)
    for beta in (0.3, 1.1, 2.7):
        c = QuantumCircuit(n)
        xy_mixer(c, beta, n)
        out = Statevector(amp).evolve(c).data
        assert np.abs(out[w != k]).max() < 1e-12
        assert np.linalg.norm(out) == pytest.approx(1.0, abs=1e-12)


def test_dicke_state_is_uniform_on_weight_k():
    from qiskit.quantum_info import Statevector
    from lip.m8.qaoa import dicke
    for n, k in ((5, 2), (6, 3), (8, 4)):
        p = np.abs(Statevector(dicke(n, k)).data) ** 2
        w = np.array([bin(i).count("1") for i in range(2 ** n)])
        assert p[w != k].sum() < 1e-12
        assert np.allclose(p[w == k], 1 / len(list(itertools.combinations(range(n), k))), atol=1e-12)


def test_ising_reproduces_the_qubo_up_to_a_constant():
    from lip.m8.qaoa import cost_qubo, energies, ising
    inst, c = _inst()
    for variant in ("penalty", "xy"):
        Qm = cost_qubo(inst, variant)
        a, b = ising(Qm)
        n = len(c)
        E = energies(Qm, n)
        z = 1 - 2 * ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1)
        H = z @ a + np.einsum("bi,ij,bj->b", z, b, z)
        assert np.allclose(E - H, (E - H)[0], atol=1e-9)


def test_v2_species_limit_in_qubo_ilp_and_feasibility():
    """docs/QUBO_v2_RULE.md: at most one entry per species (QUBO penalty P_sp) and at most two (ILP only)."""
    c = _pool(8)
    vmax = max(x["gapP5"] for x in c)
    inst = Q.build(c, 3, W, vmax, "at_most_one", per_species=1)
    n = len(c)
    Qm, const = Q.qubo_matrix(inst)
    E = []
    for bits in itertools.product([0, 1], repeat=n):
        x = np.array(bits, float)
        assert float(x @ Qm @ x + const) == pytest.approx(Q.energy(inst, x), abs=1e-9)
        E.append((Q.energy(inst, x), bits))
    best = np.array(min(E)[1])
    assert Q.feasible(inst, best)
    sp = [x["speciesId"] for x in c]
    assert all(sum(best[i] for i in range(n) if sp[i] == s) <= 1 for s in set(sp))
    ex = Q.ilp(inst)
    assert -min(E)[0] == pytest.approx(ex["f"], abs=1e-9)
    f, feas = Q.all_objectives(inst)
    tox = [i for i in range(n) if c[i]["toxic"]]
    expected = sum(1 for S in itertools.combinations(range(n), 3)
                   if sum(i in tox for i in S) <= 1 and all(sum(sp[i] == s for i in S) <= 1 for s in set(sp)))
    assert int(feas.sum()) == expected
    two = Q.ilp(Q.build(c, 3, W, vmax, "at_most_one", per_species=2))
    assert two["f"] >= ex["f"] - 1e-12                     # relaxing the limit can only help the objective


def test_v3_options_leave_v2_unchanged_and_interp_matches_zhou():
    from lip.m8 import qaoa as A
    inst = _inst()[0]
    a, b = A.ising(A.cost_qubo(inst, "xy"))
    assert A.circuit(inst, "xy", 1)[3] == max(abs(a).max(), abs(b).max())          # v2 default: largest coefficient
    assert A.circuit(inst, "xy", 1, "spread")[3] == A.spread_scale(inst, "xy") > 0  # v3 only when asked
    assert A.interp([0.1, 0.2, 0.3, 1.0, 2.0, 3.0], 4).round(6).tolist() == [0.1, 0.166667, 0.233333, 0.3, 1.0, 1.666667, 2.333333, 3.0]
    assert A.interp([0.5, 0.3], 2).tolist() == [0.5, 0.5, 0.3, 0.3]
    import numpy as np
    assert A.cvar_of(np.array([0.05, 0.95]), np.array([1.0, 3.0]), 0.1) == 2.0
    assert A.cvar_of(np.array([0.5, 0.5]), np.array([1.0, 3.0]), 1.0) == 2.0
