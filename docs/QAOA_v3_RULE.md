# QAOA v3: improved QAOA on the v2 benchmark instances (pre-registered)

Written and committed **before any v3 run**. The v2 benchmark ([QUBO_v2_RULE.md](QUBO_v2_RULE.md),
[QUANTUM_RESULTS.md](QUANTUM_RESULTS.md)) is unchanged and stays the primary, pre-registered result. v3 is an
addition, reported beside it, never instead of it.

## Why v3 exists (disclosed)

v3 was designed **after** the v2 results were known. The v2 QAOA was close to a uniformly random feasible panel. An
exploratory diagnostic on the three n = 8 instances (not committed as a result; its numbers are not reported anywhere)
showed two causes:

1. **Cost scaling.** v2 divides the Ising cost by its largest coefficient. Under v2 that coefficient is a constraint
   penalty (species or toxic), so the objective terms span a small fraction of one gamma period and the landscape the
   optimiser sees is nearly flat.
2. **Depth and initialisation.** v2 stops at p = 3 and starts every depth from random parameters.

v3 changes only these two things and adds one objective variant. Everything else is as in v2.

## Protocol

- **Instances:** exactly the v2 benchmark instances with n in {8, 12, 16} and k = 4 (same seeds, same rule: toxic
  plants at most one, at most one entry per species, weights unchanged). Instances where no 4-panel is feasible are
  skipped, as in v2.
- **Ansatz:** XY ring mixer from the Dicke state |D(n, 4)> (as v2's `xy` variant). The penalty-mixer ansatz is not
  run in v3 (it was the weaker v2 variant on every size).
- **Cost scaling (HEURISTIC):** the Ising cost is divided by s = 2 · sd(E) / sqrt(n), where sd(E) is the standard
  deviation of the cost over the weight-4 subspace the ansatz explores. Gamma starts are drawn from [0, 2].
- **Depths:** p = 1, 2, 3, 4, 5.
- **Initialisation:** p = 1 from 8 random starts. For p >= 2, one start is INTERP (Zhou et al., *Phys. Rev. X* 10,
  021067, 2020) from the best p - 1 parameters, plus 3 random starts (4 in total).
- **Optimiser:** COBYLA, maxiter 300, rhobeg 0.3, seed 20261107 (+ 17 · p + variant offset).
- **Objectives (two variants, both reported):**
  - `xy-v3`: expected energy (as v2).
  - `xy-v3-cvar`: CVaR at alpha = 0.1 (Barkoutsos et al., *Quantum* 4, 256, 2020), the mean energy of the best 10% of
    the output distribution.
- **Measured (exact statevector, as v2):** P(optimum), its ratio to the uniform probability over feasible panels,
  feasibility, expected approximation ratio over feasible outcomes, optimiser seconds, and circuit 2-qubit gate counts
  (all-to-all and heavy-hex). Also 4096 seeded shots, as v2.

## Reporting rules (fixed now)

1. Every variant, depth and instance is reported. No selection of the best depth or variant for the headline.
2. The comparison with classical methods uses the v2 classical results on the same instances (exact ILP, greedy,
   simulated annealing), unchanged.
3. "Best of N shots" is not used as a success measure: on these sizes a uniformly random sampler with the same shot
   budget also finds the optimum, so it does not distinguish methods.
4. No quantum advantage is claimed. v3 measures whether standard QAOA improvements narrow the gap to classical
   methods on a noise-free simulator; noise is not modelled in v3.
5. Results go to `data/interim/m8/qaoa_v3.json` and `docs/QAOA_v3_RESULTS.md` only. Nothing is shown on the website
   until the project lead decides the wording.
