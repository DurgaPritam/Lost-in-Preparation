# Preparation engine (`lib/engine`)

This is the preparation model (M4, `pipeline/lip/m4/model.py`) ported to TypeScript, for the planned Preparation Lab. Given the inputs in `site-data/engine/` (contract v1.7, P38, approved), it computes any combination of solvent, heat, filtration and acidity in the browser:
- the median likelihood;
- the 5th–95th percentile range, including descriptor error;
- the four separate factor medians (solvent, heat, filtration, acidity).

It has no UI yet; the Lab's design will come from Claude Design.

Its outputs are **model estimates of what a preparation would carry, not measurements**. Acidity, the heat alerts, volatility, filtration carry-over and the size penalty are heuristics.

## How it reproduces the pipeline

The engine reproduces the pipeline's Monte Carlo draws exactly, not just statistically:
- **The generator:** `numpy/random.ts` is a port of NumPy 2.4.6's `default_rng`. It covers:
  - SeedSequence seeding of PCG64 (XSL-RR 128/64);
  - `next_double`;
  - `uniform`;
  - `random`;
  - `choice`, via Lemire's bounded integers on `next_uint32` with numpy's half-word buffer;
  - the ziggurat `normal`, with numpy's own tables in `numpy/zigguratTables.ts` (BSD-3-Clause).
- **Fused multiply-add:** `numpy/fma.ts` emulates FMA using Boldo & Melquiond's round-to-odd algorithm. The macOS arm64 numpy build that produced the published profiles fuses `lo + range * u` in `uniform`. Without the emulation, about 4.5% of uniform draws differ in the last bit.
- **Statistics:** `numpy/stats.ts` reproduces numpy's `linear` percentile (`_lerp`), `np.median` and Python's `round(x, 4)`. It uses selection rather than sorting, and gets identical values.
- **The model:** `model.ts` follows `simulate()` / `estimate()` operation by operation, in the same draw order:
  - the steepness draws;
  - the solvent windows, then the acidity re-evaluation, then the size penalty;
  - both suspension draws;
  - the heat-level draws, then the heat alerts;
  - the descriptor-error pass, from the noise stream at `seed + seedOffset + 10000019`.

Every compound of one preparation reads the same random stream, because the pipeline reseeds per compound with `seed + seedOffset`. So a stream and its uniform values are generated once, and every compound reads them through a fresh cursor. The descriptor-error pass reuses the primary pass's filtration and heat factors, which don't depend on logP and come from the same stream positions.

**Platform note:** the published profiles come from numpy on macOS arm64 (with FMA). A numpy build without FMA contraction, which is typical on x86_64 Linux, can differ in the last bit of individual draws. That can change a 4th decimal in rare cases.

## Preparations and seeds

`preparationFor(model, {solvents, heat, filtered, process})` returns one of two things:
- **A grid combination:** the pipeline preparation with its own `seedOffset` (its grid index), so the result equals the published profile.
- **Any other combination:** a custom preparation whose `seedOffset` is `1000 + FNV-1a(key) mod 1,000,000` (`customSeedRule` in `model.json`). This is the rule the Python exporter used to produce `parity.json`.

## Parity gate (fails the build)

`npm run engine:parity` runs inside `prebuild`, so `npm run build` and CI fail if parity breaks. It compares 7 values per estimate: likelihood, 5th and 95th percentiles, and the four drivers. The parity cases also compare the model-only range.

| Set | Contents |
|---|---|
| Grid | 19 species × 13 preparations (247 profiles), against `site-data/profiles/` |
| Off-grid | 27 cases in `site-data/engine/parity.json`: 9 combinations × 3 species. The combinations cover unknown heat, unknown filtration, vinegar on basic nitrogen, vinegar + water, wine + honey, oil applied whole, boiled oil, pure ethanol, and powder with heat not stated. |

The stated tolerance is **1e-4 absolute**, one unit in the 4th decimal, the precision both sides round to. The current result is **312,337 of 312,337 values identical** (42,403 estimates, maximum difference 0).

`site-data/engine/` itself is checked on the Python side:
- `python -m lip m4 engine-export` refuses to write unless the exported inputs reproduce all 34,645 published estimates through `model.py`;
- `tests/test_engine_export.py` checks the files.

## Performance

Run `npm run engine:bench`, which writes [bench-report.json](bench-report.json). A "full profile" means one preparation for every compound of a species, including the descriptor-error pass. The benchmark uses the largest species, *Humulus lupulus* (484 compounds) at 400 draws, measured on an Apple M4. Median times in headless Chromium:

| CPU | Grid preparation, cached streams | Grid preparation, new streams | Off-grid, heaviest branches, new streams |
|---|---|---|---|
| 1× (M4) | 11.1 ms | 11.7 ms | 19.1 ms |
| 2× throttled | 23.0 ms | 24.4 ms | 38.5 ms |
| 4× throttled | 45.6 ms | 49.8 ms | 78.9 ms |

The heaviest off-grid case is vinegar + water with heat and filtration not stated: two solvent windows, acidity, and per-draw heat and filtration. Throttling uses Chrome DevTools' CPU emulation. 2× is the closer stand-in for a mid-range laptop's single-thread speed; 4× is Lighthouse's slow-device setting. Smaller species scale linearly with their compound count (median species: 78 compounds).

## Responsiveness in the Lab

Run `npm run lab:latency` (needs `npm run serve`). It writes [latency-report.json](latency-report.json): every sample, plus a summary per CPU rate, species and cache state. It clicks Lab settings for *Salvia sclarea* (the default, 136 compounds) and *Humulus lupulus* (the largest, 484), 3 repeats of 9 steps each. Five steps reach a preparation the page has not computed; four return to one it has.

- **Measured under the slowdown (main thread):** the click to the next frame, which is the UI's response, and the longest main-thread task. The previous profile stays visible, marked as updating, until the new one is ready.
- **Not throttled (the worker):** Chrome applies DevTools CPU throttling only to pages; `Emulation.setCPUThrottlingRate` is rejected for worker targets. The time until the new profile is ready is therefore measured with the engine's worker at full speed.
- **Estimate (heuristic):** `estReadyMs` adds (rate − 1) × the worker's own time for the request. This assumes the worker would slow down linearly.
- **Yields:** the worker yields between chunks of 24 compounds through a `MessageChannel` task, not `setTimeout`. Nested timeouts are clamped to 4 ms, which had made the yields most of a large species' time.

The numbers are in `latency-report.json`; this file does not repeat them.

## Files

| File | Contents |
|---|---|
| `model.ts` | `simulate`, `estimate`, `Streams` (the per-model stream cache) |
| `prep.ts` | `preparationFor`, `customSeedOffset`, `fnv1a32` |
| `index.ts` | `computeProfile(species, prep, model, streams?)` |
| `numpy/random.ts` | `numpy/stats.ts`, `numpy/fma.ts`, `numpy/zigguratTables.ts` |
| `../../scripts/engine-parity.ts` | the build gate |
| `../../scripts/engine-bench.ts` | the benchmark |
| `worker.ts` | the Web Worker: per-(species, preparation) cache, per-channel cancellation, chunked compute |
| `../../scripts/lab-latency.ts` | the Lab latency measurement |
| `../../tests/unit/engine.test.ts` | unit tests: generator, FMA, percentiles, seeds, one-species parity |
