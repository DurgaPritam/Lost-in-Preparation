/**
 * The preparation model (M4) in TypeScript: pipeline/lip/m4/model.py (`simulate`, `estimate`), ported operation by
 * operation, so the browser can compute any combination of solvent, heat, filtration and acidity, with the same
 * Monte Carlo draws as the pipeline (numpy/ is an exact port of NumPy's generator; see engine parity tests).
 *
 * likelihood = solvent window (with acidity) -> filtration carry-over -> heat, each a separate factor; the median and
 * the 5th-95th percentile over `draws` Monte Carlo samples of the uncertainty ranges in config/prep_model.toml.
 * The reported range also includes descriptor error (a second pass with Normal noise on logP).
 *
 * MODEL ESTIMATES of what a preparation would carry, not measurements. Acidity, heat alerts, volatility, filtration
 * carry-over and the size penalty are HEURISTICS.
 */
import { Cursor, RawStream, standardNormals } from './numpy/random';
import { median, percentiles, round4 } from './numpy/stats';
import type { EngineCompound, EngineEstimate, EngineModel, EnginePrep, Heat } from './types';

type Params = EngineModel['params'];

const LEVELS: readonly Heat[] = ['cold', 'warm', 'boiled'];

/** Caches the random streams of one model: the primary stream per seedOffset, the standard normals per noise seed. */
export class Streams {
  private primary = new Map<number, RawStream>();
  private normals = new Map<number, Float64Array>();
  constructor(readonly model: EngineModel) {}
  cursor(seedOffset: number): Cursor {
    const seed = this.model.params.seed + seedOffset;
    let s = this.primary.get(seed);
    if (!s) { s = new RawStream(seed); this.primary.set(seed, s); }
    return new Cursor(s);
  }
  standardNormals(seedOffset: number): Float64Array {
    const seed = this.model.params.seed + seedOffset + this.model.noiseSeedOffset;
    let z = this.normals.get(seed);
    if (!z) { z = standardNormals(seed, this.model.params.draws); this.normals.set(seed, z); }
    return z;
  }
}

const sig = (x: number) => 1.0 / (1.0 + Math.exp(-x));

/** solvent_fraction: the logistic solvent window for one solvent. */
function solventFraction(c: Cursor, P: Params, solvent: string, h: Float64Array, k: Float64Array, n: number): Float64Array {
  const f = new Float64Array(n);
  if (solvent === 'none') { f.fill(1); return f; }
  const w = P.solvents[solvent];
  if (!w) throw new Error(`no solvent window for ${solvent}`);
  if (solvent === 'wine') {
    const ef = c.uniform(w.ethanolFraction!, n);
    const es = c.uniform(w.ethanolShift!, n);
    const up = c.uniform(w.upper!, n);
    for (let i = 0; i < n; i++) f[i] = sig(k[i] * ((up[i] + ef[i] * es[i]) - h[i]));
    return f;
  }
  f.fill(1);
  if (w.upper) {
    const up = c.uniform(w.upper, n);
    for (let i = 0; i < n; i++) f[i] = f[i] * sig(k[i] * (up[i] - h[i]));
  }
  if (w.lower) {
    const lo = c.uniform(w.lower, n);
    for (let i = 0; i < n; i++) f[i] = f[i] * sig(k[i] * (h[i] - lo[i]));
  }
  return f;
}

function maxOf(arrays: Float64Array[], n: number): Float64Array {
  if (arrays.length === 1) return arrays[0]; // never mutated afterwards, so no copy is needed
  const out = arrays[0].slice();
  for (let j = 1; j < arrays.length; j++) for (let i = 0; i < n; i++) if (arrays[j][i] > out[i]) out[i] = arrays[j][i];
  return out;
}

export interface Simulation {
  likelihood: number;
  low: number;
  high: number;
  drivers: { solvent: number; heat: number; filtration: number; acidity: number };
}

/** Draws that do not depend on the compound's lipophilicity (filtration and heat), shared by the primary and the
 *  descriptor-error pass: both read the same stream from the start, and the solvent stage consumes the same number
 *  of draws whatever h is, so these come from the same positions. */
interface Shared { filtDraw: Uint8Array; allFiltered: boolean; susp: Float64Array; heatFactor: Float64Array; alerts: number }

/** Solvent stage (+ acidity, size penalty): f_solvent and f_noacid. Consumes the steepness draws first. */
function solventStage(comp: EngineCompound, prep: EnginePrep, P: Params, c: Cursor, noise: Float64Array | null) {
  const n = P.draws;
  const k = c.uniform(P.steepness, n);
  const h = new Float64Array(n);
  for (let i = 0; i < n; i++) h[i] = noise ? comp.lipophilicity + noise[i] : comp.lipophilicity;
  if (prep.process === 'distillation') {
    const f = c.uniform(comp.volatile ? P.distillationVolatileCarried : P.distillationNonvolatileCarried, n);
    return { fSolvent: f, fNoacid: f };
  }
  if (prep.process === 'powder') {
    const f = new Float64Array(n).fill(1);
    return { fSolvent: f, fNoacid: f };
  }
  // mixtures take the best-extracting component; juice (expression) is aqueous cell sap
  const sol = prep.process === 'expression' ? ['water'] : prep.solvents;
  const fNoacid = maxOf(sol.map((s) => solventFraction(c, P, s, h, k, n)), n);
  let fSolvent = fNoacid;
  if (prep.solvents.includes('vinegar') && comp.basicN) {
    const shift = c.uniform(P.acidityLogdShift, n);
    const hAcid = new Float64Array(n);
    for (let i = 0; i < n; i++) hAcid[i] = h[i] - shift[i];
    fSolvent = maxOf(sol.map((s) => solventFraction(c, P, s, s === 'vinegar' ? hAcid : h, k, n)), n);
  }
  if (comp.mw > P.mwPenaltyAbove) {
    const pen = c.uniform(P.mwPenalty, n);
    const f = new Float64Array(n);
    for (let i = 0; i < n; i++) f[i] = fSolvent[i] * pen[i];
    fSolvent = f;
  }
  return { fSolvent, fNoacid };
}

/** Filtration and heat draws (after the solvent stage, in model.simulate's order). */
function sharedStage(comp: EngineCompound, prep: EnginePrep, P: Params, c: Cursor): Shared {
  const n = P.draws;
  const filt = prep.filtered;
  const filtDraw = new Uint8Array(n);
  if (filt === 'unknown' && prep.process !== 'distillation') {
    for (let i = 0; i < n; i++) filtDraw[i] = c.nextDouble() < 0.5 ? 1 : 0;
  } else {
    filtDraw.fill(filt === 'yes' || prep.process === 'distillation' ? 1 : 0);
  }
  let allFiltered = true;
  for (let i = 0; i < n; i++) if (!filtDraw[i]) { allFiltered = false; break; }
  const suspApplied = c.uniform(P.appliedWholeSuspended, n); // np.where evaluates both draws, applied first
  const suspUnfiltered = c.uniform(P.unfilteredSuspended, n);
  const susp = filt === 'not_applicable' ? suspApplied : suspUnfiltered;

  // heat: level codes 0 cold, 1 warm, 2 boiled; drawn per sample (Generator.choice) only when heat is not stated
  const known = prep.heat !== 'unknown' ? LEVELS.indexOf(prep.heat) : -1;
  const levels = known < 0 ? c.integers(3, n) : null;
  const alerts = [...comp.heatFlags, ...(comp.volatile && prep.process !== 'distillation' ? ['volatile'] : [])];
  const heatFactor = new Float64Array(n).fill(1);
  for (const a of alerts) {
    const r = P.heat[a];
    if (!r) throw new Error(`no heat range for ${a}`);
    if (levels === null) {
      if (known === 0) continue; // cold: no draws, the factor is unchanged (heat_factor * (1 - 0))
      const v = c.uniform(known === 1 ? r.warm : r.boiled, n);
      for (let i = 0; i < n; i++) heatFactor[i] = heatFactor[i] * (1.0 - v[i]);
      continue;
    }
    const d = new Float64Array(n);
    for (const code of [1, 2]) {
      let m = 0;
      for (let i = 0; i < n; i++) if (levels[i] === code) m++;
      if (m === 0) continue;
      const v = c.uniform(code === 1 ? r.warm : r.boiled, m);
      for (let i = 0, j = 0; i < n; i++) if (levels[i] === code) d[i] = v[j++];
    }
    for (let i = 0; i < n; i++) heatFactor[i] = heatFactor[i] * (1.0 - d[i]);
  }
  return { filtDraw, allFiltered, susp, heatFactor, alerts: alerts.length };
}

function carried(fSolvent: Float64Array, sh: Shared, n: number): Float64Array {
  if (sh.allFiltered) return fSolvent;
  const f = new Float64Array(n);
  for (let i = 0; i < n; i++) f[i] = sh.filtDraw[i] ? fSolvent[i] : fSolvent[i] + sh.susp[i] * (1.0 - fSolvent[i]);
  return f;
}

function totals(fCarried: Float64Array, heatFactor: Float64Array, n: number): Float64Array {
  const t = new Float64Array(n);
  for (let i = 0; i < n; i++) t[i] = Math.min(Math.max(fCarried[i] * heatFactor[i], 0), 1);
  return t;
}

/** model.simulate (the primary pass): median, 5th-95th percentile and the driver medians. */
function primary(comp: EngineCompound, prep: EnginePrep, P: Params, c: Cursor): { sim: Simulation; shared: Shared } {
  const n = P.draws;
  const { fSolvent, fNoacid } = solventStage(comp, prep, P, c, null);
  const sh = sharedStage(comp, prep, P, c);
  const fCarried = carried(fSolvent, sh, n);
  const [p5, p50, p95] = percentiles(totals(fCarried, sh.heatFactor, n), [5, 50, 95], true);
  // Factors that are exactly 1 by construction need no array: filtered everywhere (f_carried is f_solvent, so the
  // ratio is x / x = 1, or 1.0 where f_solvent = 0); no acidity shift or size penalty (f_solvent is f_noacid); no heat
  // alert. Their median is then exactly 1, as numpy's is.
  let filtration = 1;
  if (!sh.allFiltered) {
    const ff = new Float64Array(n);
    for (let i = 0; i < n; i++) ff[i] = fSolvent[i] > 0 ? fCarried[i] / fSolvent[i] : 1.0;
    filtration = median(ff, true);
  }
  let acidity = 1;
  if (fSolvent !== fNoacid) {
    const af = new Float64Array(n);
    for (let i = 0; i < n; i++) af[i] = fNoacid[i] > 0 ? fSolvent[i] / fNoacid[i] : 1.0;
    acidity = median(af, true);
  }
  return {
    sim: {
      likelihood: round4(p50), low: round4(p5), high: round4(p95),
      drivers: { solvent: round4(median(fNoacid)), heat: round4(sh.alerts ? median(sh.heatFactor) : 1), filtration: round4(filtration), acidity: round4(acidity) },
    },
    shared: sh,
  };
}

/** model.simulate (the primary pass, no descriptor error) for one compound and preparation. */
export function simulate(comp: EngineCompound, prep: EnginePrep, P: Params, c: Cursor): Simulation {
  return primary(comp, prep, P, c).sim;
}

/** model.estimate: median and drivers from the primary pass; the 5th-95th range also includes descriptor error (a
 *  second pass with Normal noise on logP, reusing the primary pass's filtration and heat draws). */
export function estimate(comp: EngineCompound, prep: EnginePrep, model: EngineModel, streams: Streams): EngineEstimate {
  const P = model.params;
  const n = P.draws;
  const { sim: s, shared } = primary(comp, prep, P, streams.cursor(prep.seedOffset));
  const sd = model.descriptorError.find((d) => d.descriptor === comp.descriptor)?.sd;
  if (!sd) return { compoundId: comp.compoundId, ...s, rangeModelOnly: [s.low, s.high] };
  const z = streams.standardNormals(prep.seedOffset);
  const noise = new Float64Array(n);
  for (let i = 0; i < n; i++) noise[i] = 0.0 + sd * z[i]; // Generator.normal(0.0, sd): loc + scale * z
  const { fSolvent } = solventStage(comp, prep, P, streams.cursor(prep.seedOffset), noise);
  const [n5, n95] = percentiles(totals(carried(fSolvent, shared, n), shared.heatFactor, n), [5, 95], true);
  return {
    compoundId: comp.compoundId, likelihood: s.likelihood, drivers: s.drivers, rangeModelOnly: [s.low, s.high],
    low: round4(Math.min(round4(n5), s.likelihood)), high: round4(Math.max(round4(n95), s.likelihood)),
  };
}

/** Heuristic flags shown with a compound (model.simulate's `heuristicFlags`). */
export function heuristicFlags(comp: EngineCompound): string[] {
  return [...new Set([...comp.heatFlags, ...(comp.volatile ? ['volatile'] : []), ...(comp.basicN ? ['basic_nitrogen'] : [])])].sort();
}
