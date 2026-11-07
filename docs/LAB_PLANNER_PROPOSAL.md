# Proposal: the Lab Planner panel and "Where quantum helps, and where it doesn't"

**Status: proposal, not built.** It awaits the project lead's approval. The data is ready in `site-data/lab_panel.json`
(contract v1.9, P40, proposed); the site validates the file at build time but no page reads it yet. Every number on
these screens would come from that file, or from `metrics.json` for the logP comparison. The wireframes below show the
layout only; the placeholders in angle brackets are filled from data.

Everything uses design v2 components and tokens only. No new components are needed. Two existing components get
small, data-driven additions, listed in §3.

## 1. Lab Planner (`/planner/`)

The "Coming in this release" state becomes the recommended panel. The page keeps its v2 structure: PageHeader,
feature card, ordered list, Drawer for the evidence trail, ChartTable fallback.

```
┌ PageHeader ────────────────────────────────────────────────────────────────────────────┐
│ LAB PLANNER                                                                            │
│ Which re-tests should a lab run first?                                                 │
│ A panel of <k> re-tests chosen by exact optimisation of the model's predictions:       │
│ the clearest robust profile gaps, spread across compound classes, uses and preparations, │
│ with little overlap. Hypotheses worth re-testing, never claims.                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
┌ Feature card ──────────────────────────────────────────────────────────────────────────┐
│ [Human validation pending]  Panel optimiser                                            │
│ Panel size  ( 4 | 6 | 8* )            ← SegmentedControl; alternatives[] already hold 4/6/8 │
│ [ ] Show the analysis-only panel that allows one plant with toxicity reported          │
│     (Switch; off by default. When on, the toxic entry shows ToxicityNotice and never   │
│      a plan action, as acceptance check 5 requires)                                    │
│ How it was chosen →  (link to "How the panel was chosen" below)                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
┌ Coverage strip (three stat cells) ─────────────────────────────────────────────────────┐
│ Compound classes <c>/5 · Indications <i> · Preparation types <p>   (ChartTable below)   │
└────────────────────────────────────────────────────────────────────────────────────────┘
 1  Ajuga chamaepitys · decoction in water vs modern methanol extract     [Evidence trail]
    ● Historical: decoction in water   ○ Modern: modern methanol extract (default comparator)
    Robust gap  [====|=====-----]  5th–95th <p5>–<p95>   (LikelihoodBar, neutral family)
    <n> compounds likely to differ [Heuristic]  · classes: phenolic, terpenoid-like
    For <indication label>   · No toxicity reported   · caveats: <first caveat> (+n more)
 …
 8  Raphanus sativus · decoction in wine vs decoction in water
    ⚑ Entered on coverage, not gap: no compound likely to differ (robust gap <p5>)
```

- **Entry order:** by robust gap, as in the data. Each entry reuses today's list-item layout: rank, title, MarkHist / MarkMod lines, LikelihoodBar, a `dl` of status and toxicity.
- **The "Quantum priority" cell** is replaced by "Selected by exact optimisation". The QAOA result is a benchmark of the method, not a priority for any single experiment, so it moves to its own section.
- **The ⚑ note** appears for any entry with zero compounds likely to differ, whichever entry that is.
- **Toxicity:** every entry keeps `ToxicityBadge`. Plants with toxicity reported are excluded under the default rule. The analysis-only panel shows one, with `ToxicityNotice` and no "Plan an experiment" link.
- **"How stable is this panel?":** a compact DataTable built from `sensitivity[]`, giving each weight ×0.5 and ×2, the Jaccard overlap with the default panel, and the entries added or removed. A short lead sentence states the smallest overlap.
- **"How the panel was chosen"** (collapsible, closed by default):
  - the objective in words, value + coverage − redundancy;
  - the weights, from data;
  - links to docs/QUBO.md and docs/QUANTUM_RESULTS.md.
- **Quantum benchmark (a sub-section, from `benchmark[]` and `winnerBySize`):**
  - **Size selector:** a SegmentedControl for n = 8 / 12 / 16 / 20 / 24.
  - **Bars:** one horizontal bar per method (exact, simulated annealing, greedy, random, QAOA penalty p = 1–3, QAOA XY p = 1–3), drawn the way the evidence-gap rows are (token fills, whiskers only where an interval exists). There is a column of bars for approximation ratio and one for P(optimum); P(optimum) shows a uniform-random reference line.
  - **Winner sentence:** "Which method wins at n = <n>" prints `winnerBySize[n]` as written.
  - **Fallback:** a ChartTable with every column (feasibility, seconds, two-qubit gates all-to-all and heavy-hex, depth).
  - **Noise card:** the `noise[]` sweep as rows (two-qubit error → P(optimum), feasibility), with the note "parametric noise model, not a device; no quantum hardware was used" taken from `hardware` and `noiseModel`.
- **Evidence trail Drawer:** unchanged component; the items come from `panel[].evidenceTrail` (recipes link to recipe pages, studies to PubMed, the profile to the Lab URL for that species and preparation).
- **Phone (390 px):** the entries stack, the bars become one column, and the size selector wraps (the SegmentedControl already does).

## 2. Methods & data: "Where quantum helps, and where it doesn't" (new section `#quantum`)

It is placed after "Findings", with a table-of-contents entry. There are two cards side by side on desktop, stacked on
phones, and a closing paragraph.

```
Where quantum helps, and where it doesn't
Two places in this project could use quantum methods. In both, a classical method did better at our scale.

┌ Quantum chemistry for the descriptor ──────────┐ ┌ Quantum optimisation for the panel ─────────────┐
│ [Validated against external data]             │ │ Status: <decision needed: see §4>              │
│ GFN2-xTB (semi-empirical quantum chemistry)    │ │ QAOA (penalty and XY mixers, p = 1–3),         │
│ vs RDKit Crippen logP, against measured logP   │ │ simulated, vs the exact ILP on the same        │
│ (SangsterLogP, n = <n>)                         │ │ instances                                     │
│ MAE  RDKit <a> [CI]  ·  xTB <b> [CI]           │ │ Approximation ratio: exact 1.00; QAOA <x>–<y>, │
│ (MethodComparison chart, existing)             │ │ about the same as a random panel (<r>)        │
│ Decision: the model uses Crippen logP; xTB is  │ │ P(optimum) vs uniform random: <winnerBySize>   │
│ kept as a comparison.                          │ │ Noise: drops below uniform by <e>% two-qubit   │
│                                                │ │ error (parametric model)                       │
└────────────────────────────────────────────────┘ └────────────────────────────────────────────────┘
What would have to change for quantum to help here:
• problems far beyond exact classical solvers (ours solve in seconds);
• ansätze that respect both constraints natively, or better parameter training;
• two-qubit error rates well below those in the sweep, at depths of hundreds of gates.
The contribution is the formulation, the penalty-vs-XY comparison, the noise analysis and a reproducible pipeline.
```

- **xTB card:** the existing logP MethodComparison is reused (values from `metrics.logPError`).
- **QAOA card:** its numbers come from `lab_panel.json`. The sentences stay generic and fill in from data; none is typed by hand.
- **Noise threshold:** the "drops below uniform" level is computed from `noise[]`, as the smallest error level at which P(optimum) falls below the uniform value.
- **Charts:** none new. Each card links to the Planner benchmark for detail.

## 3. Changes to existing components (recorded in site/CHANGES.md when built)

- **`LabPlanner`:** the screen is rewritten from the design's own Planner layout, keeping its sections and components.
- **`Docs`:** one new Section, using existing components.
- **`EvidenceStatusBadge`:** no change; the four validation statuses already exist.
- **Possibly a new evidence word, "Computed benchmark":** for the QAOA card. See §4; it would need the project lead's approval and a contract or type change.

## 4. Decisions needed from the project lead

1. **Which status the QAOA benchmark gets.** It is a deterministic comparison against the exact optimum computed by
   the ILP, not a check against people or external data. Options:
   - (a) show it with no status badge, as a method benchmark;
   - (b) use "validated against external data", which I think overstates it;
   - (c) add a fifth word, "computed benchmark".

   I recommend (a).
2. **The toxic option.** Should the Planner offer the analysis-only "allow one plant with toxicity reported" switch at
   all, or show only the default (exclude) panel?
3. **The coverage-only entry (slot 8).** Keep it under the fixed weights and show the ⚑ note, as proposed. Or adopt a
   pre-registered v2 rule before rebuilding, such as requiring at least one compound likely to differ, or capping the
   indications counted per candidate. A v2 rule would be a new configuration, rerun and reported beside v1.
4. **P40.** Approve `site-data/lab_panel.json` (contract v1.9).
