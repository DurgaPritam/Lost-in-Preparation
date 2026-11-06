/**
 * Preparation engine unit tests. Reference values were produced by NumPy 2.4.6 (the pipeline's version):
 *   rng = np.random.default_rng(seed); rng.bit_generator.random_raw(4), rng.random(3), rng.uniform(-3.0, -1.5, 4),
 *   rng.normal(0.0, 1.0, 4), rng.integers(0, 3, 12), np.percentile(x, [5, 50, 95]), np.median(x).
 * The full parity gate (every species x 13 preparations + 27 off-grid cases) is scripts/engine-parity.ts (prebuild).
 */
import { describe, expect, it } from 'vitest';
import { computeProfile, customSeedOffset, fnv1a32, preparationFor, Streams } from '@/lib/engine';
import { fma } from '@/lib/engine/numpy/fma';
import { Cursor, PCG64, RawStream, standardNormals } from '@/lib/engine/numpy/random';
import { median, percentiles, round4 } from '@/lib/engine/numpy/stats';
import { loadEngineModel, loadEngineParity, loadEngineSpecies, loadProfile, loadProfileIndex } from '@/lib/data/load';

const SEED = 20261105;

describe('NumPy generator port', () => {
  it('PCG64 seeded through SeedSequence gives numpy raw uint64s', () => {
    const g = new PCG64(SEED);
    expect([g.next64(), g.next64(), g.next64(), g.next64()].map(String))
      .toEqual(['14061539702924302709', '17707059117683106070', '17341609989838256509', '9991626627985639602']);
  });
  it('random, uniform (fused multiply-add), integers and normal match numpy', () => {
    expect(Array.from(new Cursor(new RawStream(SEED)).random(3))).toEqual([0.7622775947200852, 0.9599015981860641, 0.9400905612689482]);
    expect(Array.from(new Cursor(new RawStream(SEED)).uniform([-3.0, -1.5], 4)))
      .toEqual([-1.8565836079198723, -1.5601476027209038, -1.5898641580965778, -2.1875292527455468]);
    expect(Array.from(new Cursor(new RawStream(7)).integers(3, 12))).toEqual([2, 1, 2, 2, 1, 2, 2, 0, 0, 0, 0, 2]);
    expect(Array.from(standardNormals(SEED + 10_000_019, 4)))
      .toEqual([-0.19563783356561523, -0.38976537191515076, -0.9731945934129964, -0.7188953343430454]);
  });
});

describe('fma', () => {
  it('rounds once where a * b + c rounds twice', () => {
    expect(fma(0.1, 10, -1)).toBe(5.551115123125783e-17); // exact 0.1 * 10 - 1
    expect(0.1 * 10 - 1).toBe(0);
    const e = 1 + 2 ** -52;
    expect(fma(e, e, -1)).toBe(2 ** -51 + 2 ** -104);
    expect(e * e - 1).toBe(2 ** -51);
  });
  it('agrees with plain arithmetic when the product is exact', () => {
    for (const [a, b, c] of [[1.5, 2, 0.25], [3, 0.5, -1], [0, 7.25, 1e-300], [-2, 0.125, 4]]) expect(fma(a, b, c)).toBe(a * b + c);
  });
});

describe('numpy percentile / median', () => {
  it('linear percentiles and median equal numpy for even and odd n', () => {
    const x = new Cursor(new RawStream(1)).random(400);
    expect(percentiles(x, [5, 50, 95])).toEqual([0.05215114171696012, 0.47712174111904604, 0.954308488385987]);
    expect(median(x)).toBe(0.47712174111904604);
    const y = new Cursor(new RawStream(2)).random(401);
    expect(percentiles(y, [5, 50, 95])).toEqual([0.05570471002213384, 0.48707329776837693, 0.9529776429441803]);
    expect(median(y)).toBe(0.48707329776837693);
  });
  it('the input is left unchanged unless in-place is requested', () => {
    const x = new Cursor(new RawStream(3)).random(50);
    const copy = x.slice();
    percentiles(x, [5, 95]);
    median(x);
    expect(Array.from(x)).toEqual(Array.from(copy));
  });
  it('round4 is Python round(x, 4)', () => {
    // expected values are Python's: round(0.12345678, 4), round(0.99995, 4) (0.99995 is stored as 0.99995000000000000551), ...
    expect([round4(0.12345678), round4(0.99995), round4(0.00004999), round4(1)]).toEqual([0.1235, 1, 0, 1]);
  });
});

describe('preparations and seeds', () => {
  const model = loadEngineModel();
  it('FNV-1a matches the Python exporter', () => {
    expect(fnv1a32('a')).toBe(3826002220);
    expect(fnv1a32('water|cold|yes|infusion')).toBe(611673888);
  });
  it('a grid combination maps to its own preparation and seed; others get the custom seed rule', () => {
    for (const g of model.preparations) {
      expect(preparationFor(model, { solvents: g.solvents, heat: g.heat, filtered: g.filtered, process: g.process })).toBe(g);
    }
    for (const c of loadEngineParity()) expect(customSeedOffset(c.preparation)).toBe(c.preparation.seedOffset);
  });
});

describe('engine vs pipeline (one species; the full gate runs in prebuild)', () => {
  it('every preparation of the smallest species equals the published profile exactly', () => {
    const model = loadEngineModel();
    const e = loadProfileIndex().reduce((a, b) => (b.compounds < a.compounds ? b : a));
    const species = loadEngineSpecies(e.speciesId);
    const published = loadProfile(e.file);
    const streams = new Streams(model);
    model.preparations.forEach((prep, j) => {
      const got = computeProfile(species, prep, model, streams);
      expect(got.map(({ compoundId, likelihood, low, high, drivers }) => ({ compoundId, likelihood, low, high, drivers })))
        .toEqual(published[j].compounds.map(({ compoundId, likelihood, low, high, drivers }) => ({ compoundId, likelihood, low, high, drivers })));
    });
  });
});
