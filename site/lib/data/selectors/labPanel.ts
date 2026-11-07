/**
 * The Lab Planner's re-test panel, from site-data/lab_panel.json (contract v1.9 P40 + v2 amendment). Nothing is computed
 * here except labels and links: every number is the file's own. The displayed panel is v2 (docs/QUBO_v2_RULE.md); the
 * original v1 result stays visible with its notes. Plants with toxicity reported are excluded and listed, never planned.
 */
import type { BenchmarkRowView, PanelEntryView, PanelSizeView, PanelView, ToxicityRecord } from '../../types';
import type { ContractLabPanel } from '../load';
import { labHref } from './lab';

type Cand = ContractLabPanel['panel'][number];

/** M4 preparation label -> Lab settings, where the Lab can show it (it has no setting for juice or powder). */
const LAB: Record<string, { solvent: 'water' | 'wine' | 'vinegar' | 'oil'; heat: 'cold' | 'warm' | 'boiled'; acidified?: boolean }> = {
  'cold water infusion': { solvent: 'water', heat: 'cold' },
  'hot water infusion (tea)': { solvent: 'water', heat: 'warm' },
  'decoction in water': { solvent: 'water', heat: 'boiled' },
  'steeped in wine': { solvent: 'wine', heat: 'cold' },
  'decoction in wine': { solvent: 'wine', heat: 'boiled' },
  'steeped in vinegar': { solvent: 'vinegar', heat: 'cold', acidified: true },
  'infused oil': { solvent: 'oil', heat: 'warm' },
};

export function labLinkFor(species: string, historical: string, toxic: boolean): string | null {
  const s = LAB[historical];
  if (!s || toxic) return null;   // acceptance check 5: never a Lab link for a plant with toxicity reported
  return labHref({ plant: species, solvent: s.solvent, heat: s.heat, filtered: true, acidified: !!s.acidified });
}

export function toPanelView(lp: ContractLabPanel, toxicityOf: (speciesId: string) => ToxicityRecord, recipeHref: (recipeId: string) => string | null): PanelView {
  const entry = (c: Cand, coverageOnly = false): PanelEntryView => {
    const tox = toxicityOf(c.speciesId);
    return {
      position: c.position, id: c.candidateId, speciesId: c.speciesId, species: c.species, historical: c.historicalPreparation,
      modern: c.modernComparator, modernIsDefault: c.modernComparatorBasis === 'default', indication: c.indication.label,
      gap: { low: c.gap.p5, high: c.gap.p95, point: c.gap.p50 }, differs: c.compoundsLikelyToDiffer, classes: c.compoundClasses,
      toxicity: tox, caveats: c.caveats, coverageOnly,
      trail: c.evidenceTrail.map((e) => ({
        kind: e.kind,
        label: e.kind === 'recipe' ? `Recipe ${e.ref.split(':').slice(-2).join(' ')}` : e.kind === 'study' ? `PubMed ${e.ref.replace('pmid:', '')}`
          : e.kind === 'profile' ? `Profiles: ${c.historicalPreparation} vs ${c.modernComparator}` : `Species ${c.species}`,
        href: e.kind === 'recipe' ? recipeHref(e.ref) : e.kind === 'study' ? `https://pubmed.ncbi.nlm.nih.gov/${e.ref.replace('pmid:', '')}/`
          : e.kind === 'profile' ? labLinkFor(c.species, c.historicalPreparation, tox.category === 'toxic_reported') : null,
      })),
      labHref: labLinkFor(c.species, c.historicalPreparation, tox.category === 'toxic_reported'),
    };
  };
  const size = (k: number, cands: Cand[], objective: number | null, coverage: Record<string, number>): PanelSizeView => ({
    k, entries: cands.map((c) => entry(c)), objective, coverage: { class: coverage.class ?? 0, indication: coverage.indication ?? 0, prep: coverage.prep ?? 0 },
  });
  const defaultCoverage = (() => {
    const classes = new Set(lp.panel.flatMap((c) => c.compoundClasses));
    const inds = new Set(lp.panel.flatMap((c) => c.indications));
    const preps = new Set(lp.panel.map((c) => c.historicalPreparation));
    return { class: classes.size, indication: inds.size, prep: preps.size };
  })();
  const sizes = [
    ...lp.alternatives.filter((a) => a.toxicRule === lp.toxicRule && a.perSpecies === lp.perSpecies).map((a) => size(a.k, a.panel, a.objective, a.coverage)),
    size(lp.k, lp.panel, null, defaultCoverage),
  ].sort((a, b) => a.k - b.k);
  const benchmark: BenchmarkRowView[] = lp.benchmark.filter((r) => r.k === 4).map((r) => ({
    n: r.n, solver: r.solver, p: r.p ?? null, instances: r.instances, ar: r.meanApproximationRatio ?? null, pOptimum: r.pOptimum ?? null,
    feasibility: r.feasibility ?? null, seconds: r.meanSeconds ?? null, cxAllToAll: r.twoQubitGatesAllToAll ?? null, cxHeavyHex: r.twoQubitGatesHeavyHex ?? null,
    depth: r.depthAllToAll ?? null,
  }));
  return {
    ruleVersion: lp.ruleVersion, ruleDoc: lp.ruleDoc, perSpecies: lp.perSpecies ?? null, defaultK: lp.k, poolSize: lp.poolSize, weights: lp.weights,
    sizes,
    perSpeciesTwo: lp.perSpeciesSensitivity.map((a) => size(a.k, a.panel, a.objective, a.coverage)).sort((a, b) => a.k - b.k),
    original: lp.original ? {
      k: lp.original.k, objective: lp.original.objective, notes: lp.original.notes,
      entries: lp.original.panel.map((c) => entry(c, c.compoundsLikelyToDiffer === 0)),
    } : null,
    excludedToxic: lp.excludedToxic.map((x) => ({ species: x.species, label: `${x.species}: ${x.historicalPreparation} vs ${x.modernComparator}` })),
    ineligible: lp.ineligible.map((x) => ({ label: `${x.species}: ${x.historicalPreparation} vs ${x.modernComparator}`, reason: x.reason })),
    sensitivity: lp.sensitivity.map((s) => ({ weight: s.weight, factor: s.factor, jaccard: s.jaccardWithDefault, added: s.added, removed: s.removed })),
    benchmark, benchmarkSizes: [...new Set(benchmark.map((r) => r.n))].sort((a, b) => a - b),
    winners: lp.winnerBySize,
    noise: lp.noise.map((r) => ({ variant: r.variant, p: r.p, twoQubitError: r.twoQubitError, pOptimum: r.pOptimum, feasibility: r.feasibility, ar: r.meanArFeasible ?? null })),
    noiseModel: lp.noiseModel, hardware: lp.hardware,
  };
}

/** The QAOA summary for Methods & data, from the benchmark rows (nothing typed by hand). */
export function quantumSummary(v: PanelView) {
  const q = v.benchmark.filter((r) => r.solver.startsWith('qaoa') && r.ar != null);
  const rnd = v.benchmark.filter((r) => r.solver === 'random' && r.ar != null && q.some((x) => x.n === r.n));
  const uniform = (n: number) => v.benchmark.find((r) => r.solver === 'random' && r.n === n)?.pOptimum ?? null;
  return {
    qaoaAr: q.length ? [Math.min(...q.map((r) => r.ar!)), Math.max(...q.map((r) => r.ar!))] as [number, number] : null,
    randomAr: rnd.length ? [Math.min(...rnd.map((r) => r.ar!)), Math.max(...rnd.map((r) => r.ar!))] as [number, number] : null,
    sizes: [...new Set(q.map((r) => r.n))].sort((a, b) => a - b),
    bestRatio: [...new Set(q.map((r) => r.n))].sort((a, b) => a - b).map((n) => {
      const best = q.filter((r) => r.n === n && r.pOptimum != null).sort((a, b) => b.pOptimum! - a.pOptimum!)[0];
      const u = uniform(n);
      return best && u ? { n, solver: best.solver, p: best.p, pOptimum: best.pOptimum!, uniform: u } : null;
    }).filter((x): x is NonNullable<typeof x> => x !== null),
  };
}
