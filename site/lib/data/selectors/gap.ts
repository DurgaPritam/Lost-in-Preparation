/**
 * The evidence gap (design v2 ReportingGapFile), built from metrics.reportingGap (contract v1.6, P37b). Every number is
 * the metric's own value, n and Wilson interval; nothing is recomputed here except stated = round(value * n), the count
 * the metric's note also gives.
 */
import type { EvidenceStatus, ReportingField, ReportingGapRow, ReportingGapView } from '../../types';
import type { ContractMetrics } from '../load';

type GapMetrics = NonNullable<ContractMetrics['reportingGap']>;

const FIELDS: [ReportingField, string, string][] = [
  ['freshOrDried', 'Fresh or dried', 'freshOrDried'],
  ['filtration', 'Filtration', 'filtration'],
  ['heat', 'Heat', 'heat'],
  ['part', 'Plant part', 'part'],
  ['solvent', 'Solvent', 'solvent'],
];
/** "Stated" means the rule-based extractor coded a value: a heuristic whose accuracy awaits the 40-study hand-check. */
const EVIDENCE: EvidenceStatus = 'pending';

function rowOf(g: GapMetrics, key: string, field: ReportingField, label: string, inflated = false): ReportingGapRow | null {
  const m = g[key];
  if (!m || m.status !== 'computed' || m.value == null || m.n == null) return null;
  return {
    field, label, stated: Math.round(m.value * m.n), n: m.n,
    ci: m.low != null && m.high != null ? [m.low, m.high] : null, evidence: EVIDENCE, inflated, note: m.note ?? null,
  };
}

export const INFLATED_SOLVENT_NOTE =
  'Inflated by construction: a study counts as having prepared the plant partly because a solvent was stated, so this share is higher than it would be among all studies that prepared the plant.';

export function toReportingGap(m: ContractMetrics): ReportingGapView {
  const g = m.reportingGap ?? {};
  const rows = FIELDS.map(([f, label, k]) => rowOf(g, `prepared:all:${k}`, f, label, f === 'solvent')).filter((r): r is ReportingGapRow => r !== null);
  const none = rowOf(g, 'prepared:all:none', 'freshOrDried', 'None of the five stated');
  const extra = ([
    ['retrieved:all:none', 'Every coded study retrieved for a plant–use pair (audit v1): none of the five stated'],
    ['retrieved:abstract:heat', 'Heat stated · studies coded from abstracts'],
    ['retrieved:pmc_fulltext:heat', 'Heat stated · studies coded from open-access methods'],
    ['v3:screening', 'Compared two preparations of the same plant material (pre-registered v3 screening)'],
  ] as const).flatMap(([key, label]) => {
    const r = rowOf(g, key, 'heat', label);
    return r ? [{ label, stated: r.stated, n: r.n, ci: r.ci, note: r.note }] : [];
  });
  const head = rows.find((r) => r.field === 'freshOrDried');
  return {
    headline: { field: 'freshOrDried', text: head ? `${head.stated} / ${head.n} studies state whether the plant was fresh or dried` : 'How often studies state how they prepared the plant' },
    method: `Prepared set: the ${rows[0]?.n ?? 'unknown number of'} studies that prepared the plant material (audit v2 eligibility). "Stated" means the rule-based extractor coded a value (heuristic; hand-check pending). 95% Wilson intervals. Descriptive findings, not hypothesis tests. Source: data/interim/m5/reporting_gap.json.`,
    rows, none, extra,
  };
}
