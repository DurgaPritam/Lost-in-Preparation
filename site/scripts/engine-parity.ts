/**
 * Parity gate (npm run engine:parity, part of prebuild): the TypeScript engine (lib/engine) must reproduce the
 * Python preparation model (pipeline/lip/m4/model.py) for
 *   1. every species and all 13 pipeline preparations: site-data/profiles/<speciesId>.json, and
 *   2. the preparations outside the grid in site-data/engine/parity.json (unknown heat or filtration, vinegar on basic
 *      nitrogen, mixtures, applied whole, pure ethanol, boiled oil, powder with heat not stated).
 * Compared: median likelihood, 5th and 95th percentiles (with descriptor error), the model-only range (parity cases)
 * and the four driver medians. Same seeds, same draws.
 *
 * TOLERANCE = 1e-4 absolute: one unit in the 4th decimal, the precision both sides round to. The engine reproduces
 * NumPy's generator bit for bit, so a difference can only come from the last bit of exp/log1p (V8 vs the C library)
 * landing on a rounding boundary. Exit 1 (failing the build) on any difference above the tolerance, any compound or
 * preparation out of order, or a model-version mismatch.
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { computeProfile, Streams } from '../lib/engine';
import type { EngineEstimate } from '../lib/engine';
import { loadEngineModel, loadEngineParity, loadEngineSpecies, loadProfile, loadProfileIndex } from '../lib/data/load';

const TOLERANCE = 1e-4;
type Expected = Pick<EngineEstimate, 'likelihood' | 'low' | 'high' | 'drivers'> & { rangeModelOnly?: number[] };

const stats = { values: 0, exact: 0, withinTolerance: 0, maxAbsDiff: 0, failures: [] as string[] };
function compare(where: string, got: EngineEstimate, want: Expected) {
  const pairs: [string, number, number][] = [
    ['likelihood', got.likelihood, want.likelihood], ['low', got.low, want.low], ['high', got.high, want.high],
    ...(['solvent', 'heat', 'filtration', 'acidity'] as const).map((k) => [`drivers.${k}`, got.drivers[k], want.drivers[k]] as [string, number, number]),
    ...(want.rangeModelOnly ? [['rangeModelOnly.low', got.rangeModelOnly[0], want.rangeModelOnly[0]], ['rangeModelOnly.high', got.rangeModelOnly[1], want.rangeModelOnly[1]]] as [string, number, number][] : []),
  ];
  for (const [k, a, b] of pairs) {
    stats.values++;
    const d = Math.abs(a - b);
    stats.maxAbsDiff = Math.max(stats.maxAbsDiff, d);
    if (d === 0) stats.exact++;
    else if (d <= TOLERANCE + 1e-12) stats.withinTolerance++;
    else stats.failures.push(`${where} ${k}: engine ${a}, python ${b}`);
  }
}

const model = loadEngineModel();
const streams = new Streams(model);
const t0 = performance.now();
let profiles = 0;
let estimates = 0;
for (const e of loadProfileIndex()) {
  const species = loadEngineSpecies(e.speciesId);
  if (species.modelVersion !== model.modelVersion) stats.failures.push(`${e.speciesId}: modelVersion ${species.modelVersion} != ${model.modelVersion}`);
  const published = loadProfile(e.file);
  model.preparations.forEach((prep, j) => {
    const prof = published[j];
    if (!prof || prof.preparationLabel !== prep.label) { stats.failures.push(`${e.file}[${j}] is not "${prep.label}"`); return; }
    const got = computeProfile(species, prep, model, streams);
    profiles++;
    prof.compounds.forEach((want, i) => {
      if (got[i]?.compoundId !== want.compoundId) { stats.failures.push(`${e.file}[${j}] compound ${i} order`); return; }
      estimates++;
      compare(`${e.acceptedName} / ${prep.label} / ${want.compoundId}`, got[i], want);
    });
  });
}
const tGrid = performance.now() - t0;
let cases = 0;
for (const c of loadEngineParity()) {
  const got = computeProfile(loadEngineSpecies(c.speciesId), c.preparation, model, streams);
  cases++;
  c.expected.forEach((want, i) => {
    if (got[i]?.compoundId !== want.compoundId) { stats.failures.push(`parity ${c.preparation.label} compound ${i} order`); return; }
    estimates++;
    compare(`parity ${c.speciesId} / ${c.preparation.label} / ${want.compoundId}`, got[i], want);
  });
}
const report = {
  tolerance: TOLERANCE, modelVersion: model.modelVersion, gridProfiles: profiles, parityCases: cases, estimates,
  values: stats.values, exact: stats.exact, withinTolerance: stats.withinTolerance, failures: stats.failures.length,
  maxAbsDiff: stats.maxAbsDiff, gridSeconds: +(tGrid / 1000).toFixed(2), firstFailures: stats.failures.slice(0, 20),
};
mkdirSync(path.resolve(__dirname, '..', '.engine'), { recursive: true });
writeFileSync(path.resolve(__dirname, '..', '.engine', 'parity-report.json'), JSON.stringify(report, null, 2) + '\n');
console.log(`engine parity: ${estimates} estimates (${profiles} grid profiles, ${cases} custom cases), ${stats.values} values: ` +
  `${stats.exact} exact, ${stats.withinTolerance} within ${TOLERANCE}, ${stats.failures.length} beyond; max |diff| ${stats.maxAbsDiff}`);
if (stats.failures.length) {
  console.error(`\nENGINE PARITY FAILED:\n  ${stats.failures.slice(0, 20).join('\n  ')}\n`);
  process.exit(1);
}
