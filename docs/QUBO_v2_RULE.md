# Panel v2: pre-registered rule (2026-11-07)

**Status: pre-registered.** This file and [config/m8_qubo_v2.toml](../config/m8_qubo_v2.toml) were committed before
any v2 solver run. The rule was decided by the project lead on 2026-11-07, after reading the v1 result. It is written
down here by the AI (Claude, in Claude Code), and nothing in the v2 outcome may change it.
config/m8_qubo_v2.toml is identical to config/m8_qubo.toml (v1) apart from its `[rule]` section and header comment.

## Why

The v1 panel's slot 8 (*Raphanus sativus*, decoction in wine vs decoction in water) entered on coverage alone. It has
a robust gap of 0.003 and no compound likely to differ, so a lab would learn nothing from it
(docs/QUANTUM_RESULTS.md, "Selected on coverage, not value"). v1 also placed two entries from the same species in
several slots. That spends the panel on one plant.

## The rule

1. **Hard eligibility, applied to the pool before optimisation.** A candidate is eligible only if its robust gap is
   positive (gapP5 > 0) and at least one compound is likely to differ (|D_i| ≥ 1, the v1 definition with
   differ_delta = 0.10). Ineligible candidates are listed, never silently dropped.
2. **Diversity, as a hard constraint.** At most one entry per species: Σ_{i ∈ species s} x_i ≤ 1 for every s.
   - **Sensitivity:** the same run with at most two per species, solved exactly by the ILP only. "At most two" is
     not quadratic, so it has no QUBO form here.
3. **Weights unchanged from v1:** α = 1.0, β_class = β_indication = β_prep = 0.2, γ = 0.5, penalty_margin = 1.25.
4. **The displayed panel:** the exact optimum (ILP) for k = 4, 6 and 8, with toxic-reported species excluded. The
   default shown is k = 8.
5. **Stability:** each weight ×0.5 and ×2, others fixed, reporting the Jaccard overlap with the default v2 panel (as
   in v1).
6. **QUBO form of the species constraint:** P_sp · Σ_{i<j, same species} x_i x_j, with P_sp = 2 · margin · B.
   Repairing a selection with two entries from one species takes two bit flips (swap one out for another candidate),
   so the toxic-rule argument in docs/QUBO.md §3 applies unchanged.

## Benchmark

The v2 pool and constraints change the instances, so the benchmark is re-run under v2, with everything else as in v1:
- **Instances:** sampled from the v2-eligible pool, with toxic-reported candidates included, using v1's seed formula
  (20261107 + 1000·n + i, three per size) at n = 8, 12, 16 and 20, plus the full v2-eligible pool.
- **Constraints:** at most one entry per species, and at most one toxic (as in v1), so both quadratic penalty kinds
  are exercised.
- **Feasibility:** an instance on which no k-panel satisfies the constraints is recorded as infeasible and skipped.
- **Solvers, depths, restarts, shots, noise sweep and figures:** as in v1.

## Reporting

- **Side by side:** v1 and v2 are reported together. v2 is the displayed panel. v1 stays visible as the original
  result, with its slot-8 note.
- **Excluded toxic candidates:** the toxic-reported candidates excluded from the displayed panel are listed plainly.
- **v1 files kept:** the v1 benchmark and panel are kept, as `data/interim/m8/benchmark_v1.json` and
  `data/interim/m8/panel_v1.json`.
