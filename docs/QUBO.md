# Choosing a re-test panel: the objective, its QUBO and the QAOA variants

Phase 8 picks a small panel of re-tests for a lab: candidates where the historical preparation and a modern
comparator are predicted to extract different compound profiles. It is an optimisation over **model outputs**, so the
panel is a list of hypotheses worth re-testing, never a claim that a preparation works or is safe.

This file defines the problem (rule v1). The displayed panel uses **rule v2**, pre-registered in
[QUBO_v2_RULE.md](QUBO_v2_RULE.md): eligibility (positive robust gap, at least one compound likely to differ) and at
most one entry per species, with the weights unchanged. The numbers (pool size, optima, solver metrics) are written by scripts to
[QUANTUM_RESULTS.md](QUANTUM_RESULTS.md) and `data/interim/m8/`. Settings are in
[config/m8_qubo.toml](../config/m8_qubo.toml); every weight there was fixed before any solver was compared.

## 1. Candidates

A candidate *i* is a triple (species, historical preparation, modern comparator). `pipeline/lip/m8/pool.py` builds it
for the approved headline species:

- **Historical preparation:** every M4-representable preparation attested for the species in the single-plant recipes
  that have a mapped indication (the M6 heuristic map `hist_to_grid`, with the logged M1 corrections applied).
- **Modern comparator:** the most frequent M4-representable modern preparation among the studies retrieved for the
  candidate's species–indication pairs. When no such study exists, it is the most frequent one across all coded
  studies, recorded as basis `default`.
- **Indication:** the most-attested MeSH indication of the candidate's recipes. All attested indications are kept, for
  coverage.
- **Usable robust gap:** the candidate is kept only if the M6 rule can score it (at least 5 compounds whose reported
  5th–95th range is narrower than 0.8 in both preparations). Its value is the gap's 5th percentile, `gapP5`.
- **Compounds likely to differ, D_i (heuristic):** a compound is in D_i when the 5th–95th range of its coupled draw
  difference (historical − modern) excludes 0 and the median difference is at least `differ_delta` (0.10).
- **Compound classes of D_i:** the heuristic classes from `site-data/engine`.
- **Toxicity:** toxic-reported species stay in the pool with a flag. The config chooses `exclude` (drop them) or
  `at_most_one`.

## 2. The objective (maximise)

Variables x_i ∈ {0, 1} (1 = in the panel), with the constraint Σ x_i = k (default k = 8; also k = 4 and 6).

f(x) = **value** + **coverage** − **redundancy**:

| Term | Formula | Why |
|---|---|---|
| Robust value | (α / k) · Σ_i v_i x_i, where v_i = gapP5_i / max_j gapP5_j over the pool | Prefer re-tests whose profile difference holds in 95% of the Monte Carlo draws. Normalising by the pool maximum and by k puts the term on a 0–1 scale for any k. |
| Coverage, per family F ∈ {compound class, indication, preparation type} | (β_F / k) · Σ_{a∈F} [ Σ_i A_ia x_i − Σ_{i<j} A_ia A_ja x_i x_j ] | A_ia = 1 when candidate i has attribute a. The bracket is the second-order (Bonferroni) surrogate of "attribute a is covered": 1 when one or two selected candidates share it, 0 for three, negative beyond. It is quadratic, so it fits a QUBO. The true number of distinct attributes covered is reported beside it. |
| Redundancy | (γ / C(k,2)) · Σ_{i<j} J_ij x_i x_j, where J_ij = \|D_i ∩ D_j\| / \|D_i ∪ D_j\| (0 when both are empty) | Two re-tests that would measure the same differing compounds teach the lab little more than one. Dividing by the number of pairs puts the term on a 0–1 scale. |

**Weights (fixed 2026-11-07, before any comparison):** α = 1.0, β_class = β_indication = β_prep = 0.2, γ = 0.5.
- **Rationale:** value is the primary goal, coverage as a whole (0.6) is a secondary goal, and overlap is penalised moderately.
- **Sensitivity:** each weight is multiplied by 0.5 and by 2 in turn, and the change in the exact panel is reported (Jaccard overlap with the default panel).

**A property to keep in mind:** the coverage terms count attributes without a cap. A candidate with many attested
indications can therefore enter on coverage alone, even with a small gap. RESULTS reports when that happens. It is a
consequence of the fixed weights, not something tuned away afterwards.

## 3. The QUBO (minimise)

f is linear plus quadratic: f(x) = Σ_i h_i x_i + Σ_{i<j} q_ij x_i x_j, with h_i ≥ 0 and q_ij ≤ 0. The QUBO is

E(x) = −f(x) + P · (Σ_i x_i − k)² [ + P_tox · Σ_{i<j, both toxic} x_i x_j  when at most one toxic is allowed ].

In matrix form E(x) = xᵀQx + c, with c = P k² and Q upper triangular:
- Q_ii = −h_i + P(1 − 2k);
- Q_ij = −q_ij + 2P (+ P_tox for a toxic pair).

### Penalty

Let B = max_i ( |h_i| + Σ_j |q_ij| ). That is the most that −f can change when one bit flips.

- **Cardinality.** Take any infeasible x with Σ x = k + d (d ≠ 0). Flipping |d| bits reaches a feasible y, and −f(y) ≤ −f(x) + |d|·B. The penalty at x is P·d² ≥ P·|d|. So P > B makes E(y) < E(x), and every minimiser of E is feasible.
- **Toxic rule.** Repairing m ≥ 2 selected toxic candidates swaps one toxic candidate for a non-toxic one: two flips, so up to 2B. The penalty drops by (m − 1)·P_tox ≥ P_tox, so P_tox > 2B suffices.
- **Choice:** P = 1.25 B and P_tox = 2.5 B (config `penalty_margin` = 1.25). They are derived from the instance, never tuned.

A test enumerates every bitstring of a small instance and checks that the minimiser of E is feasible and equals the
ILP optimum (`tests/test_m8_qubo.py`).

## 4. Solvers (same instances, fixed seeds)

| Solver | What it does |
|---|---|
| **Exact (ground truth)** | ILP with PuLP / CBC. Products x_i x_j become y_ij ≥ x_i + x_j − 1, y_ij ≥ 0, which is exact when maximising because every q_ij ≤ 0. The constraints are Σx = k and, when used, Σ_{toxic} x ≤ 1. The minimum f_min (for the approximation ratio) uses the full linearisation. It is cross-checked against brute force for n ≤ 16. |
| Greedy | Adds the best marginal candidate k times. |
| Simulated annealing | Searches the feasible set with swap moves and geometric cooling from T0 = 0.5 to T1 = 0.001, over 2000·n moves. Seeds 1–5. |
| QAOA, penalty | Starts from \|+⟩ⁿ. Cost layer exp(−iγ H_E), the full E including P. Mixer exp(−iβ Σ X_i). |
| QAOA, XY | Starts from the Dicke state \|D(n,k)⟩: the uniform superposition of all weight-k strings, prepared deterministically with split-and-cyclic-shift gates (Bärtschi & Eidenbenz, 2019). Mixer exp(−iβ (XX + YY)/2) on the ring of qubit pairs (even, odd and wrap layers), which preserves Hamming weight, so every sample has exactly k selected. Cost layer: −f, plus the toxic term when at most one toxic is allowed. The cardinality penalty is constant on the weight-k subspace, so it is omitted. |

**QAOA details:**
- **Mapping:** x = (1 − z)/2 maps E to an Ising Hamiltonian Σ a_i Z_i + Σ b_ij Z_i Z_j. It is applied as RZ(2γ a_i) and RZZ(2γ b_ij) after dividing by max |coefficient|, so γ ∈ [0, π] spans one period of the largest term.
- **Depths:** p = 1, 2 and 3.
- **Optimiser:** COBYLA (SciPy), at most 300 iterations, from 8 random starts with γ ∈ [0, π] and β ∈ [0, π/2]. The seed is fixed per depth and variant. Every restart is recorded.
- **Simulation:** expectations are exact (Qiskit Aer statevector). The final parameters are also sampled with 4096 shots at a fixed seed.
- **Sizes:** statevector QAOA runs at n = 8, 12 and 16 with k = 4. Larger n is beyond this budget: each evaluation at n = 20 is about 16 times the cost at n = 16.

## 5. Metrics

| Metric | Definition |
|---|---|
| Approximation ratio | AR(x) = (f(x) − f_min) / (f_opt − f_min) over feasible x. Classical solvers: their returned panel. QAOA: the expected AR over the feasible probability mass, and the best and mean AR among sampled feasible panels. |
| P(optimum) | The probability of sampling an optimal panel: exact from the statevector, and estimated from shots. A uniform random feasible panel is the baseline. |
| Feasibility | The share of probability or samples with exactly k selected (and at most one toxic, under that rule). |
| Runtime | Wall clock on the development laptop. QAOA time is a classical simulation, including all restarts. |
| Circuit cost | Depth and two-qubit (CX) gate count after transpiling to {rz, sx, x, cx}, both all-to-all and on a heavy-hex coupling map (Qiskit core, distance 5). No device is involved. |

## 6. Noise and hardware

- **Hardware:** no free quantum hardware was used. There is no IBM Quantum account or token on this machine, none was created, and IonQ access needs the project lead's own account.
- **Instead:** a parametric noise-model simulation. The best small instance (n ≤ 12) runs on a heavy-hex coupling map with depolarising two-qubit errors of 0, 0.1, 0.5, 1 and 2%. One-qubit errors are 10% of the two-qubit error, and the readout error is 2%.
- **What this is:** a noise sweep, not a device calibration.

## 7. What to expect, and what not to claim

At these sizes, exact classical optimisation is instantaneous, so no quantum advantage is expected or claimed. The
contribution is:
- the formulation;
- the penalty-versus-XY-mixer comparison, including feasibility;
- the noise analysis;
- a reproducible pipeline (`python -m lip m8 pool`, `python -m lip m8 bench`).

The results file states plainly which method wins at each size.
