/** Contract audit records (v1 audit.json, v2 audit_v2.json) → the design's Study rows and per-source breakdowns. */
import type { AuditBreakdown, HeatLevel, MatchState, SourceWork, StatedField, Study } from '../../types';
import type { ContractAudit } from '../load';
import { sourceWork } from './common';

type Code = 'match' | 'mismatch' | 'unknown' | 'no_analogue';

/** Best outcome over a unit's comparisons, as the audit protocols define it: any match → matches; every known
 *  comparison differs → differs; every comparison no-analogue → no_analogue; otherwise not stated. */
export function bestState(codes: Code[]): MatchState {
  if (codes.includes('match')) return 'matches';
  const real = codes.filter((c) => c !== 'no_analogue');
  const known = real.filter((c) => c !== 'unknown');
  if (known.length && known.length === real.length) return 'differs';
  if (codes.length && !real.length) return 'no_analogue';
  return 'not_stated';
}

const stated = <T,>(v: string, map?: (x: string) => T): StatedField<T> =>
  ({ value: v === 'unknown' ? null : map ? map(v) : (v as unknown as T), evidence: 'pending' });

export interface AuditView { rows: Study[]; units: Unit[] }
export interface Unit { pairKey: string; pmid: string; sources: SourceWork[]; speciesId: string; state: Record<'vehicle' | 'heat' | 'filtration' | 'part' | 'freshOrDried' | 'overall', MatchState> }

export function auditView(records: ContractAudit[], speciesName: (id: string) => string): AuditView {
  type Acc = { codes: Record<string, Code[]>; recipes: Set<string>; sources: Set<SourceWork>; study: ContractAudit['studies'][number]; speciesId: string; indication: string };
  const rows = new Map<string, Acc>();
  const units = new Map<string, { codes: Record<string, Code[]>; sources: Set<SourceWork>; speciesId: string; pmid: string; pairKey: string }>();
  for (const r of records) {
    const pairKey = `${r.speciesId}|${r.indication?.meshId ?? 'none'}`;
    const srcs = new Set(r.historicalRecipeIds.map((id) => sourceWork(id.startsWith('pliny') ? 'pliny-nh' : id.split(':')[0])));
    const prepIdx = new Map<string, number>();
    for (const s of r.studies) {
      const i = prepIdx.get(s.pmid) ?? 0;
      prepIdx.set(s.pmid, i + 1);
      const rk = `${pairKey}|${s.pmid}|${i}`;
      const acc = rows.get(rk) ?? { codes: {}, recipes: new Set(), sources: new Set(), study: s, speciesId: r.speciesId, indication: r.indication?.label ?? r.indicationAsWritten };
      const uk = `${pairKey}|${s.pmid}`;
      const u = units.get(uk) ?? { codes: {}, sources: new Set(), speciesId: r.speciesId, pmid: s.pmid, pairKey };
      const m = s.match as Record<string, Code>;
      for (const [f, c] of Object.entries(m)) {
        (acc.codes[f] ??= []).push(c);
        (u.codes[f] ??= []).push(c);
      }
      r.historicalRecipeIds.forEach((x) => acc.recipes.add(x));
      srcs.forEach((x) => { acc.sources.add(x); u.sources.add(x); });
      rows.set(rk, acc);
      units.set(uk, u);
    }
  }
  const st = (codes: Record<string, Code[]>, f: string) => bestState(codes[f] ?? []);
  return {
    rows: [...rows.entries()].map(([id, a]) => ({
      id, pmid: a.study.pmid || null, title: a.study.title, year: a.study.year ?? null, taxon: speciesName(a.speciesId), indication: a.indication,
      plantPart: stated<string>(a.study.part, (x) => x.replace(/_/g, ' ')), solvent: stated<string>(a.study.solvent === 'unknown' ? 'unknown' : a.study.solventText),
      heat: stated<HeatLevel>(a.study.heat), freshOrDried: stated<string>(a.study.freshOrDried),
      filtered: stated<boolean | 'not_applicable'>(a.study.filtered, (x) => (x === 'yes' ? true : x === 'no' ? false : 'not_applicable')),
      evidenceSource: a.study.evidenceSource, methodsSnippet: a.study.methodsSnippet ?? null, comparedRecipeIds: [...a.recipes],
      match: { vehicle: st(a.codes, 'solvent'), heat: st(a.codes, 'heat'), filtration: st(a.codes, 'filtration'), part: st(a.codes, 'part'),
               freshOrDried: st(a.codes, 'freshOrDried'), overall: st(a.codes, 'overall') },
    })),
    units: [...units.values()].map((u) => ({
      pairKey: u.pairKey, pmid: u.pmid, sources: [...u.sources], speciesId: u.speciesId,
      state: { vehicle: st(u.codes, 'solvent'), heat: st(u.codes, 'heat'), filtration: st(u.codes, 'filtration'), part: st(u.codes, 'part'),
               freshOrDried: st(u.codes, 'freshOrDried'), overall: st(u.codes, 'overall') },
    })),
  };
}

const zero = (): Record<MatchState, number> => ({ matches: 0, differs: 0, not_stated: 0, no_analogue: 0 });
/** One breakdown per source; a (pair, study) unit counts under every source that attests the pair. */
export function breakdowns(units: Unit[]): AuditBreakdown[] {
  const works: SourceWork[] = ['culpeper_1652', 'culpeper_1850', 'pliny_nh'];
  return works.map((w) => {
    const us = units.filter((u) => u.sources.includes(w));
    const b = { source: w, plants: new Set(us.map((u) => u.speciesId)).size, studies: us.length, vehicle: zero(), heat: zero(), filtration: zero() };
    for (const u of us) { b.vehicle[u.state.vehicle] += 1; b.heat[u.state.heat] += 1; b.filtration[u.state.filtration] += 1; }
    return b;
  }).filter((b) => b.studies > 0);
}
