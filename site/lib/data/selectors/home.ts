/** Home page view: name-resolution coverage by evidence status, counts, and the reporting-gap headline. */
import type { Coverage, EvidenceStatus } from '../../types';
import type { ContractMetrics, ContractRecipe, ContractSpecies } from '../load';
import { candidateEvidence } from './common';

export function coverage(species: ContractSpecies[], recipes: ContractRecipe[], studies: number): Coverage {
  const byName = new Map<string, EvidenceStatus>();
  for (const s of species) byName.set(s.id.split('|')[1], candidateEvidence(s.basis));
  const counts: Record<EvidenceStatus, number> = { validated: 0, provisional: 0, pending: 0 };
  byName.forEach((e) => { counts[e] += 1; });
  return { nameResolutions: counts, recipes: recipes.length, studies };
}

export interface GapRow { key: string; label: string; value: number | null; low: number | null; high: number | null; n: number | null; k: number | null; note: string; inflated: boolean }
const VARS: [string, string][] = [['heat', 'Heat'], ['freshOrDried', 'Fresh or dried'], ['filtration', 'Filtration'], ['solvent', 'Solvent'], ['part', 'Plant part']];

function row(m: ContractMetrics['reportingGap'], key: string, label: string): GapRow {
  const x = m[key];
  const value = x && x.status === 'computed' ? x.value ?? null : null;
  const n = x?.n ?? null;
  return { key, label, value, low: x?.low ?? null, high: x?.high ?? null, n, k: value != null && n != null ? Math.round(value * n) : null,
           note: x?.note ?? 'Not computed', inflated: key.startsWith('prepared') && key.endsWith(':solvent') };
}

/** The reporting-gap headline (contract v1.6 metrics.reportingGap). `set` = prepared (audit v2 eligibility) or retrieved (audit v1). */
export function reportingGap(m: ContractMetrics) {
  const g = m.reportingGap ?? {};
  const set = (s: 'prepared' | 'retrieved', part = 'all') => ({
    vars: VARS.map(([v, l]) => row(g, `${s}:${part}:${v}`, l)),
    none: row(g, `${s}:${part}:none`, 'None of the five'),
    all: row(g, `${s}:${part}:all five`, 'All five'),
  });
  return { prepared: set('prepared'), retrieved: set('retrieved'), retrievedAbstract: set('retrieved', 'abstract'),
           retrievedMethods: set('retrieved', 'pmc_fulltext'), v3: row(g, 'v3:screening', 'Compared two preparations of the same material') };
}
