/** metrics.json → the design's Validation view (Methods & validation page). */
import type { CheckOutcome, Metric, ValidationStatus, MetricValue, PipelineStage, PositiveControl, PreregisteredCheck, Validation, MethodComparison } from '../../types';
import type { ContractMetric, ContractMetrics } from '../load';

export const metricValue = (m: ContractMetric | null | undefined, unit: string): MetricValue => ({
  point: m && m.status === 'computed' ? m.value ?? null : null,
  low: m && m.status === 'computed' ? m.low ?? null : null,
  high: m && m.status === 'computed' ? m.high ?? null : null,
  unit,
});

export function outcomeOf(result: string | null | undefined): CheckOutcome {
  const r = (result ?? '').toLowerCase();
  if (r.startsWith('borderline')) return 'borderline';
  if (r === 'pass') return 'pass';
  if (r === 'fail') return 'fail';
  return 'not_run';
}

/** SITE: the stage each AI-assisted section checks (validation wording, 2026-11-07). The logP descriptor is validated
 *  against external data (measured values), but the preparation model itself has only AI-assisted checks, so M4 is not shown as validated. */
const PROV_STAGE: Record<string, string> = {
  nameResolutionVsDraft: 'M2', m5ExtractorAiCheck: 'M5', extractionVsSilver: 'M1',
  prepModelVsLiterature_exploratory: 'M4', prepModelVsLiterature_preregistered: 'M4', prepModelVsLiterature_preregistered_v2: 'M4', prepModelVsLiterature_preregistered_v3: 'M4',
};

export function toValidation(m: ContractMetrics): Validation {
  const x = m.extraction.overall?.part?.f1 ?? null;
  const top1 = m.nameResolution.top1 ?? null;
  const rd = m.logPError.rdkit ?? null;
  const xt = m.logPError.xtb ?? null;
  const pipeline: PipelineStage[] = [
    { id: 'ingest', name: 'Ingest', does: 'Culpeper 1652, Culpeper 1850 and Pliny (Bostock & Riley) into located passages.', tool: 'TEI and Project Gutenberg parsers', validation: 'pending' },
    { id: 'm1', name: 'Recipes (M1)', does: 'Structured recipes, every field backed by a verbatim quote; failures rejected, never repaired.', tool: m.extraction.run ? `${m.extraction.run.provider} · ${m.extraction.run.model}` : null, validation: x && x.status === 'computed' ? 'validated' : 'pending' },
    { id: 'm2', name: 'Names (M2)', does: 'Historical name → accepted species (WFO), with candidates, confidence and disputed flags.', tool: 'GBIF + WFO, heuristic weights', validation: top1 && top1.status === 'computed' ? 'validated' : m.provisional.nameResolutionVsDraft ? 'provisional' : 'pending' },
    { id: 'm3', name: 'Compounds (M3)', does: 'Known compounds per species (LOTUS via Wikidata), standardised with RDKit.', tool: 'LOTUS · RDKit', validation: 'pending' },
    { id: 'm4', name: 'Preparation model (M4)', does: 'Predicted extraction per compound and preparation, with ranges; solvent, heat, filtration and acidity separate.', tool: 'RDKit Crippen logP; GFN2-xTB compared', validation: 'provisional' },
    { id: 'm5', name: 'Audit (M5)', does: 'How modern studies prepared each plant, coded with a versioned keyword lexicon; unstated = unknown.', tool: 'Rule-based extractor (no LLM)', validation: m.provisional.m5ExtractorAiCheck ? 'provisional' : 'pending' },
    { id: 'm6', name: 'Ranking (M6)', does: 'Hypotheses ranked only on profile gaps that hold across the uncertainty range.', tool: 'Coupled Monte Carlo draws', validation: 'pending' },
  ];
  const metrics: Metric[] = [];
  const push = (id: string, stage: string, name: string, mm: ContractMetric | null | undefined, unit: string, evidence: ValidationStatus, note?: string) =>
    metrics.push({ id, stage, name, value: metricValue(mm, unit), n: mm?.n ?? null, evidence: mm && mm.status === 'computed' ? evidence : 'pending', note: note ?? mm?.note ?? undefined });
  push('m1-f1', 'M1', 'Extraction F1 (part) vs human gold', x, 'F1, 0–1', 'validated');
  push('m1-rej', 'M1', 'Recipes rejected by the verbatim check', m.extraction.spanRejectionRate, 'share, 0–1', 'provisional');
  push('m1-kappa', 'M1', 'Annotator agreement (heat)', m.interAnnotatorAgreement.heat, 'Cohen κ', 'validated');
  push('m2-top1', 'M2', 'Top-1 vs scholarly identifications', top1, 'share, 0–1', 'validated');
  for (const [k, v] of Object.entries(m.nameResolution)) if (k.startsWith('disputedShare')) push(`m2-${k}`, 'M2', `Resolved names disputed${k.includes(':') ? ` · ${k.split(':')[1]}` : ' · all sources'}`, v, 'share, 0–1', 'pending');
  push('m4-rdkit', 'M4', 'logP error, RDKit Crippen (MAE vs experiment)', rd, 'logP units', 'external');
  push('m4-xtb', 'M4', 'logP error, GFN2-xTB (MAE vs experiment)', xt, 'logP units', 'external');
  push('m5-v1', 'M5', 'Audit v1: share of studies faithful (as pre-registered)', m.headlineMatchRate, 'share, 0–1', 'pending');
  if (m.auditV2) push('m5-v2', 'M5', 'Audit v2: share of studies faithful (re-analysis)', m.auditV2.overallFidelity, 'share, 0–1', 'pending');
  for (const [key, sec] of Object.entries(m.provisional)) for (const [mk, mv] of Object.entries(sec.metrics)) push(`prov-${key}-${mk}`, PROV_STAGE[key] ?? 'AI-assisted check', `${sec.label} · ${mk}`, mv, 'share, 0–1', 'provisional');

  const comparisons: MethodComparison[] = rd && xt ? [{
    id: 'logp', question: 'Does GFN2-xTB predict logP better than RDKit’s Crippen method?', direction: 'lower_better',
    methods: [{ name: 'RDKit Crippen logP', value: metricValue(rd, 'MAE, logP units') }, { name: 'GFN2-xTB / ALPB', value: metricValue(xt, 'MAE, logP units') }],
    finding: xt.low != null && rd.high != null && xt.low > rd.high ? 'GFN2-xTB had a larger error than RDKit, and the intervals do not overlap.'
      : rd.low != null && xt.high != null && rd.low > xt.high ? 'RDKit had a larger error than GFN2-xTB, and the intervals do not overlap.' : 'The intervals overlap: no clear difference.',
    decision: 'The descriptor with the lower error is the model’s default; the other is kept as a comparison.', evidence: 'external',
  }] : [];
  const art = m.artemisininCheck;
  const positiveControls: PositiveControl[] = [{
    id: 'artemisinin', preregisteredId: 'pr-artemisinin', taxon: 'Artemisia annua', compound: 'Artemisinin', expected: 'Low in cold water, high in a low-temperature nonpolar extract (pre-registered thresholds in the explanation).',
    outcome: art.status === 'computed' ? outcomeOf(art.result) : 'not_run', explanation: art.explanation ?? 'No explanation recorded.',
    evidence: art.status === 'computed' ? 'provisional' : 'pending',
  }];
  const preregistered: PreregisteredCheck[] = [
    { id: 'pr-artemisinin', registeredOn: null, criterion: 'Artemisinin known-case test', outcome: art.status === 'computed' ? outcomeOf(art.result) : 'not_run', detail: art.result ?? 'Not run', evidence: art.status === 'computed' ? 'provisional' : 'pending' },
    ...Object.entries(m.provisional).filter(([k]) => k.startsWith('prepModelVsLiterature_preregistered')).map(([k, sec]): PreregisteredCheck => {
      const first = Object.entries(sec.metrics)[0];
      return { id: `pr-${k}`, registeredOn: null, criterion: sec.label, outcome: 'reported',
               detail: first ? `${first[0]}: ${first[1].status === 'computed' && first[1].value != null ? first[1].value.toFixed(2) : 'not computed'}${first[1].n ? ` (n = ${first[1].n})` : ''}` : 'No metric recorded',
               evidence: 'provisional' };
    }),
  ];
  const limitations = [
    'Extraction is not detection: the model predicts extracted fractions, while studies record detection, which also depends on plant content and detection limits.',
    'One descriptor: the aqueous prediction rests on Crippen logP alone; solubility, melting point, dose and contact time are not modelled.',
    'Heuristic factors (heat, volatility, filtration carry-over, acidity) have assumed ranges and are not fitted to data.',
    'The recipe extraction was written by an AI in a Claude Code session; the human gold annotation is not done yet.',
    'The audit coding is a keyword heuristic; abstracts often omit preparation details, so many studies stay unknown. Its accuracy has only an AI-assisted check (provisional); the human hand-check is pending.',
    'Pliny is lower confidence than Culpeper: a 19th-century translation of a 1st-century text, with far more disputed names.',
    'LOTUS records compounds per organism, not per plant part, so a recipe’s part cannot be matched to the part analysed.',
  ];
  return { pipeline, metrics, comparisons, positiveControls, preregistered, limitations };
}
