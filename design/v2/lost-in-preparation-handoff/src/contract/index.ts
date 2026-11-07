/**
 * TYPED MOCKS, one export per contract file.
 * `npm run mock-data` (scripts/export-mock-data.ts) writes each of these to
 * mock-data/<file>.json, so the JSON can never drift from src/types.ts.
 *
 * The contract file list is ASSUMED (no JSON Schemas received). When the real
 * schemas arrive, rename/reshape here and the screens follow via types.
 *
 * Mock rules: repeating-digit numbers (0.11, 0.22 …), [MOCK] titles,
 * PMIDs of the form 0000000n, no real accuracy figures, no medical claims.
 */
import type {
  AuditBreakdown, Coverage, Heuristic, Hypothesis, LabPlanFile, Plate, Recipe, ReportingGapFile, ReportingGapRow, SourcesFile, SpeciesProfile, Study, Validation,
} from '../types';
import { RECIPES } from './recipes';
import { LAB_PROFILES } from './lab';
import { heurAcidity, heurHeat, toxConcern, toxLacking, toxReported } from '../gallery/mock';
import { wilson } from '../lib/format';

/* recipes.json */
export const recipes: Recipe[] = RECIPES;

/* species_profiles.json (v2: generated per Lab combination; see ./lab.ts) */
export const speciesProfiles: SpeciesProfile[] = LAB_PROFILES;

/* reporting_gap.json (v2, additive) — mock counts; n = 111 studies per detail */
const gapRow = (field: ReportingGapRow['field'], label: string, stated: number, n = 111): ReportingGapRow => {
  const [lo, hi] = wilson(stated, n);
  return { field, label, stated, n, ci: [+lo.toFixed(2), +hi.toFixed(2)], evidence: 'provisional' };
};
export const reportingGap: ReportingGapFile = {
  headline: { field: 'material', text: 'Most modern studies never say whether the plant was fresh or dried.' },
  method: '[MOCK] Each audited study was checked for whether it states each preparation detail. Interval: 95% Wilson interval for the proportion stated.',
  rows: [
    gapRow('solvent', 'Solvent', 99),
    gapRow('plant_part', 'Plant part', 77),
    gapRow('duration', 'Extraction time', 55),
    gapRow('heat', 'Heat / temperature', 44),
    gapRow('ratio', 'Plant-to-solvent ratio', 33),
    gapRow('filtration', 'Filtration', 22),
    gapRow('material', 'Fresh or dried', 11),
  ],
};

/* plates.json (v2, additive) — illustration slots; every image carries its licence */
const plate = (taxon: string): Plate => ({
  taxon, caption: `${taxon} — 19th-century botanical plate (to source)`, status: 'to_source',
  licence: 'Public domain', host: 'Wikimedia Commons', fileUrl: null, imageUrl: null,
});
export const plates: Plate[] = ['Glycyrrhiza glabra', 'Artemisia absinthium', 'Salvia officinalis', 'Conium maculatum', 'Mentha sp.'].map(plate);

/* lab_plan.json (v2, additive) — Lab Planner placeholder until the quantum feature ships */
export const labPlan: LabPlanFile = {
  feature: {
    name: 'Quantum-informed priority',
    status: 'coming_soon',
    release: null,
    description: 'Will add a solvation-based priority score for each experiment. Until it ships, experiments are ordered by the conservative gap only.',
  },
  items: [
    { id: 'lp-1', hypothesisId: 'h-thujone-wine', title: 'Thujone: cold wine vs methanol reflux', compares: ['Wine, cold, 3 days, strained', 'Methanol extract, reflux'], readout: '[MOCK] GC-MS quantification of the extract', effort: 'medium', rank: 1, rankRange: [1, 2], quantumScore: null },
    { id: 'lp-2', hypothesisId: 'h-menthol-oil', title: 'Menthol: warm oil vs hydrodistillation', compares: ['Oil, sun-warmed', 'Hydrodistillation'], readout: '[MOCK] GC-MS quantification of the extract', effort: 'low', rank: 2, rankRange: [1, 3], quantumScore: null },
    { id: 'lp-3', hypothesisId: 'h-glycyrrhizin-decoction', title: 'Glycyrrhizin: strained decoction vs methanol reflux', compares: ['Decoction, strained', 'Methanol extract, reflux'], readout: null, effort: null, rank: 3, rankRange: [2, 4], quantumScore: null },
    { id: 'lp-4', hypothesisId: 'h-absinthin-vinegar', title: 'Absinthin: boiled vinegar vs aqueous decoction', compares: ['Vinegar, boiled to a third', 'Aqueous decoction'], readout: '[MOCK] LC-MS quantification of the extract', effort: 'medium', rank: 4, rankRange: [3, 4], quantumScore: null },
  ],
};

/* heuristics.json */
export const heuristics: Heuristic[] = [
  heurAcidity,
  heurHeat,
  { id: 'ethanol_strength', label: 'Ethanol strength of wine', rule: 'Historical wine is modelled as dilute ethanol of unknown strength; a range of strengths is propagated, not a single value.' },
];

/* coverage.json */
export const coverage: Coverage = { nameResolutions: { validated: 111, provisional: 222, pending: 333 }, recipes: 555, studies: 66 };

/* studies.json */
const S = <T,>(value: T | null, evidence: Study['plantPart']['evidence'] = 'provisional') => ({ value, evidence });
export const studies: Study[] = [
  {
    id: 's-a', pmid: '00000001', title: '[MOCK] Study A — methanol extract of aerial parts', year: 2011, taxon: 'Artemisia absinthium',
    plantPart: S('aerial parts', 'validated'), solvent: S('methanol', 'validated'), heat: S('reflux'), duration: S('2 h'),
    filtered: S(true, 'validated'), ratio: S('1:10 w/v'),
    comparedRecipeIds: ['cul-wormwood-wine', 'pli-absinthium-vinegar'],
    match: { vehicle: 'differs', heat: 'differs', filtration: 'matches' },
  },
  {
    id: 's-b', pmid: '00000002', title: '[MOCK] Study B — aqueous decoction of leaves', year: 2015, taxon: 'Artemisia absinthium',
    plantPart: S('leaves', 'validated'), solvent: S('water', 'validated'), heat: S('boiled', 'validated'), duration: S('30 min'),
    filtered: S(true), ratio: S<string>(null, 'validated'),
    comparedRecipeIds: ['cul-wormwood-wine', 'pli-absinthium-vinegar'],
    match: { vehicle: 'differs', heat: 'differs', filtration: 'matches' },
  },
  {
    id: 's-d', pmid: null, title: '[MOCK] Study D — hydroalcoholic maceration (not indexed in PubMed)', year: null, taxon: 'Artemisia absinthium',
    plantPart: S<string>(null, 'pending'), solvent: S('ethanol 70%'), heat: S('cold'), duration: S('7 days'),
    filtered: S<boolean>(null, 'pending'), ratio: S<string>(null, 'pending'),
    comparedRecipeIds: ['cul-wormwood-wine'],
    match: { vehicle: 'differs', heat: 'matches', filtration: 'not_stated' },
  },
  {
    id: 's-c', pmid: '00000003', title: '[MOCK] Study C — ethanol extract of leaves', year: 2018, taxon: 'Salvia officinalis',
    plantPart: S('leaves', 'validated'), solvent: S('ethanol 96%', 'validated'), heat: S('warm'), duration: S('24 h'),
    filtered: S(true, 'validated'), ratio: S('1:20 w/v'),
    comparedRecipeIds: ['cul-sage-cold'],
    match: { vehicle: 'differs', heat: 'differs', filtration: 'matches' },
  },
  {
    id: 's-e', pmid: '00000004', title: '[MOCK] Study E — cold aqueous infusion of leaves', year: 2020, taxon: 'Salvia officinalis',
    plantPart: S('leaves', 'validated'), solvent: S('water', 'validated'), heat: S('cold', 'validated'), duration: S('12 h'),
    filtered: S(true, 'validated'), ratio: S('1:10 w/v', 'validated'),
    comparedRecipeIds: ['cul-sage-cold'],
    match: { vehicle: 'matches', heat: 'matches', filtration: 'matches' },
  },
  {
    id: 's-f', pmid: '00000005', title: '[MOCK] Study F — hydrodistilled essential oil', year: 2009, taxon: 'Mentha sp.',
    plantPart: S('leaves'), solvent: S('steam (hydrodistillation)'), heat: S('boiled'), duration: S('3 h'),
    filtered: S<boolean>(null, 'pending'), ratio: S<string>(null, 'pending'),
    comparedRecipeIds: ['pli-menta-oil'],
    match: { vehicle: 'differs', heat: 'differs', filtration: 'not_stated' },
  },
];

/* audit_summary.json */
export const auditSummary: AuditBreakdown[] = [
  { source: 'culpeper_1652', plants: 11, studies: 22,
    vehicle: { matches: 1, differs: 18, not_stated: 3 },
    heat: { matches: 4, differs: 11, not_stated: 7 },
    filtration: { matches: 9, differs: 2, not_stated: 11 } },
  { source: 'pliny_nh', plants: 11, studies: 33,
    vehicle: { matches: 0, differs: 30, not_stated: 3 },
    heat: { matches: 3, differs: 22, not_stated: 8 },
    filtration: { matches: 11, differs: 0, not_stated: 22 } },
];

/* hypotheses.json */
const trail = (t: Partial<Record<'source' | 'name' | 'prep' | 'model' | 'audit' | 'tox', string>>, ev: Partial<Record<string, Hypothesis['evidence']>> = {}): Hypothesis['trail'] => [
  { id: 't1', stage: 'source', title: 'Source passages', detail: t.source ?? '', evidence: ev.source ?? 'validated', refs: [{ label: 'Open recipe', href: '/atlas' }] },
  { id: 't2', stage: 'name', title: 'Name resolution', detail: t.name ?? '', evidence: ev.name ?? 'validated' },
  { id: 't3', stage: 'preparation', title: 'Preparation extracted', detail: t.prep ?? '', evidence: ev.prep ?? 'provisional' },
  { id: 't4', stage: 'model', title: 'Extraction estimate', detail: t.model ?? '', evidence: ev.model ?? 'provisional', heuristics: ['heat_sensitivity'] },
  { id: 't5', stage: 'audit', title: 'Modern studies audited', detail: t.audit ?? '', evidence: ev.audit ?? 'provisional', refs: [{ label: 'Open audit', href: '/docs#studies' }] },
  { id: 't6', stage: 'toxicity', title: 'Toxicity check', detail: t.tox ?? '', evidence: ev.tox ?? 'provisional' },
];

export const hypotheses: Hypothesis[] = [
  {
    id: 'h-thujone-wine', rank: 1, rankRange: [1, 2],
    taxon: 'Artemisia absinthium', compound: 'Thujone (α/β)', compoundClass: 'Monoterpenes (volatile oil)',
    faithful: { label: 'Wine, cold, 3 days, strained', preparation: { family: 'historical', vehicle: 'wine', filtered: true, heat: 'cold', duration: '3 days' } },
    modern: { label: 'Methanol extract, reflux', preparation: { family: 'modern', vehicle: 'methanol_extract', filtered: true, heat: 'reflux', duration: '2 h' } },
    historicalLikelihood: { low: 0.55, high: 0.77, point: 0.66 },
    modernLikelihood: { low: 0.11, high: 0.33, point: 0.22 },
    attestation: [{ source: 'culpeper_1652', recipes: 2 }, { source: 'pliny_nh', recipes: 0 }],
    caveats: [
      'Thujone content varies between chemotypes; this estimates extraction, not how much the plant held.',
      'The strength of 17th-century wine is unknown; a range is modelled.',
      'The heat effect is a heuristic, not a measurement.',
    ],
    toxicity: toxConcern, evidence: 'provisional',
    trail: trail({
      source: '2 Culpeper recipes describe a cold wine steep, strained.',
      name: '“Wormwood” → Artemisia absinthium (one candidate).',
      prep: 'Vehicle, heat, duration and straining extracted; quantity unstandardised.',
      model: 'Historical 0.55–0.77 vs modern 0.11–0.33. Ranges do not overlap.',
      audit: 'No audited study used a cold wine preparation (0 of 3).',
      tox: 'Concern recorded (thujone). Laboratory analysis only.',
    }),
  },
  {
    id: 'h-menthol-oil', rank: 2, rankRange: [1, 3],
    taxon: 'Mentha sp.', compound: 'Menthol', compoundClass: 'Monoterpenes (volatile oil)',
    faithful: { label: 'Oil, sun-warmed, some days', preparation: { family: 'historical', vehicle: 'oil', filtered: null, heat: 'warm', duration: null } },
    modern: { label: 'Hydrodistillation', preparation: { family: 'modern', vehicle: 'hydrodistillation', filtered: null, heat: 'boiled', duration: '3 h' } },
    historicalLikelihood: { low: 0.44, high: 0.77, point: 0.55 },
    modernLikelihood: { low: 0.11, high: 0.33, point: 0.22 },
    attestation: [{ source: 'culpeper_1652', recipes: 0 }, { source: 'pliny_nh', recipes: 1 }],
    caveats: [
      'The name resolves to genus only; Mentha species differ in their volatile oils.',
      'Attested once, in the lower-confidence source.',
      'Duration is not stated in the source.',
    ],
    toxicity: toxLacking, evidence: 'pending',
    trail: trail({
      source: '1 Pliny recipe: laid in oil and set in the sun.',
      name: '“menta” → Mentha (genus only).',
      prep: 'Vehicle and warmth extracted; duration could not be normalised.',
      model: 'Historical 0.44–0.77 vs modern 0.11–0.33.',
      audit: '1 audited study, hydrodistillation; filtration not stated.',
      tox: 'Toxicity data lacking.',
    }, { name: 'provisional', model: 'pending' }),
  },
  {
    id: 'h-coniine-oil', rank: 3, rankRange: [2, 3],
    taxon: 'Conium maculatum', compound: 'Coniine', compoundClass: 'Piperidine alkaloids',
    faithful: { label: 'Oil infusion, leaves', preparation: { family: 'historical', vehicle: 'oil', filtered: null, heat: null, duration: null } },
    modern: { label: 'Aqueous extract', preparation: { family: 'modern', vehicle: 'aqueous_extract', filtered: true, heat: 'warm', duration: null } },
    historicalLikelihood: { low: 0.44, high: 0.66, point: 0.55 },
    modernLikelihood: { low: 0.11, high: 0.33, point: 0.22 },
    attestation: [{ source: 'culpeper_1652', recipes: 1 }, { source: 'pliny_nh', recipes: 0 }],
    caveats: ['Heat and duration not stated in the source.', 'Toxicity reported: relevant only to laboratory analysis of the historical record.'],
    toxicity: toxReported, evidence: 'provisional',
    trail: trail({
      source: '1 Culpeper recipe: leaves bruised and infused in oil.',
      name: '“Hemlock” → Conium maculatum (one candidate).',
      prep: 'Vehicle and part extracted; heat and duration not stated.',
      model: 'Historical 0.44–0.66 vs modern 0.11–0.33.',
      audit: 'No audited study used an oil vehicle.',
      tox: 'Toxicity reported. Shown for analysis only.',
    }),
  },
  {
    id: 'h-glycyrrhizin-decoction', rank: 4, rankRange: [3, 4],
    taxon: 'Glycyrrhiza glabra', compound: 'Glycyrrhizin', compoundClass: 'Triterpene saponins',
    faithful: { label: 'Decoction, strained, reduced by a third', preparation: { family: 'historical', vehicle: 'water', filtered: true, heat: 'boiled', acidified: false, duration: 'reduced by one third' } },
    modern: { label: 'Methanol extract, reflux', preparation: { family: 'modern', vehicle: 'methanol_extract', filtered: true, heat: 'reflux', duration: '2 h' } },
    historicalLikelihood: { low: 0.66, high: 0.88, point: 0.77 },
    modernLikelihood: { low: 0.33, high: 0.55, point: 0.44 },
    attestation: [{ source: 'culpeper_1652', recipes: 1 }, { source: 'pliny_nh', recipes: 0 }],
    caveats: ['Glycyrrhizin content differs between sources of root; this estimates extraction only.', 'The reduction step (“a third consumed”) is modelled as prolonged boiling.', 'Heat effect is a heuristic.'],
    toxicity: toxConcern, evidence: 'provisional',
    trail: trail({
      source: '1 Culpeper recipe: root boiled in water until a third is consumed, then strained.',
      name: '“Liquorice” → Glycyrrhiza glabra (one candidate).',
      prep: 'Vehicle, heat, reduction and straining extracted.',
      model: '[MOCK] Historical 0.66–0.88 vs modern 0.33–0.55. Ranges do not overlap.',
      audit: '[MOCK] Audited studies mostly used alcoholic extracts.',
      tox: 'Concern recorded (glycyrrhizin at high intake). Laboratory analysis only.',
    }),
  },
  {
    id: 'h-absinthin-vinegar', rank: 5, rankRange: [5, 5],
    taxon: 'Artemisia absinthium', compound: 'Absinthin', compoundClass: 'Sesquiterpene lactones',
    faithful: { label: 'Vinegar, boiled to a third', preparation: { family: 'historical', vehicle: 'vinegar', filtered: null, heat: 'boiled', duration: null } },
    modern: { label: 'Aqueous decoction', preparation: { family: 'modern', vehicle: 'aqueous_extract', filtered: true, heat: 'boiled', duration: '30 min' } },
    historicalLikelihood: { low: 0.11, high: 0.44, point: 0.22 },
    modernLikelihood: { low: 0.11, high: 0.33, point: 0.22 },
    attestation: [{ source: 'culpeper_1652', recipes: 0 }, { source: 'pliny_nh', recipes: 1 }],
    caveats: ['Ranges overlap: weak lead, listed for completeness.', 'From a disputed name (candidate 1 of 3).', 'Acidity effect is a heuristic.'],
    toxicity: toxConcern, evidence: 'provisional',
    trail: trail({
      source: '1 Pliny recipe: boiled in sharp vinegar to a third.',
      name: '“absinthium” → 3 candidates (disputed); this lead uses candidate 1.',
      prep: 'Vehicle and heat extracted; duration could not be normalised.',
      model: 'Historical 0.11–0.44 vs modern 0.11–0.33. Ranges overlap.',
      audit: '2 audited studies; neither used vinegar.',
      tox: 'Concern recorded.',
    }, { name: 'provisional' }),
  },
];

/* validation.json */
export const validation: Validation = {
  pipeline: [
    { id: 'transcribe', name: 'Transcribe', does: 'Source pages to text, illegible stretches marked ⟦?⟧.', tool: null, validation: 'validated' },
    { id: 'extract', name: 'Extract recipe fields', does: 'Plant, part, vehicle, heat, duration, filtration as character spans.', tool: null, validation: 'provisional' },
    { id: 'resolve', name: 'Resolve names', does: 'Historical name → candidate taxa with confidence ranges.', tool: null, validation: 'provisional' },
    { id: 'compounds', name: 'Look up compounds', does: 'Known constituents per taxon, grouped by class.', tool: null, validation: 'pending' },
    { id: 'estimate', name: 'Estimate extraction', does: 'Likelihood ranges per compound and preparation, from descriptors and heuristics.', tool: 'RDKit', validation: 'provisional' },
    { id: 'audit', name: 'Audit modern studies', does: 'How published studies prepared the same plants.', tool: 'PubMed', validation: 'provisional' },
    { id: 'rank', name: 'Rank hypotheses', does: 'By the conservative gap between ranges, with rank ranges.', tool: null, validation: 'pending' },
  ],
  metrics: [
    { id: 'm-cer', stage: 'Transcribe', name: 'Character error rate vs hand transcription', value: { point: 0.11, low: 0.05, high: 0.22, unit: 'rate (lower is better)' }, n: 111, evidence: 'validated' },
    { id: 'm-fields', stage: 'Extract recipe fields', name: 'Agreement with hand annotation', value: { point: 0.77, low: 0.66, high: 0.88, unit: 'κ' }, n: 111, evidence: 'provisional' },
    { id: 'm-names-c', stage: 'Resolve names', name: 'Top candidate agrees with expert · Culpeper', value: { point: 0.88, low: 0.77, high: 0.99, unit: 'proportion' }, n: 55, evidence: 'validated' },
    { id: 'm-names-p', stage: 'Resolve names', name: 'Top candidate agrees with expert · Pliny', value: { point: 0.44, low: 0.22, high: 0.66, unit: 'proportion' }, n: 55, evidence: 'provisional', note: 'Lower confidence source; many names have no single correct answer.' },
    { id: 'm-logp', stage: 'Estimate extraction', name: 'logP error vs experimental values (RDKit)', value: { point: 0.55, low: 0.44, high: 0.66, unit: 'MAE, log units' }, n: 111, evidence: 'validated' },
    { id: 'm-study', stage: 'Audit modern studies', name: 'Study field extraction agreement', value: { point: null, low: null, high: null, unit: 'κ' }, n: null, evidence: 'pending', note: 'Not yet measured.' },
  ],
  comparisons: [
    {
      id: 'c-xtb', preregisteredId: 'p2', question: 'Does quantum chemistry (xTB) estimate logP better than RDKit?', direction: 'lower_better',
      methods: [
        { name: 'RDKit (Crippen)', value: { point: 0.55, low: 0.44, high: 0.66, unit: 'MAE, log units' } },
        { name: 'xTB (GFN2, implicit solvent)', value: { point: 1.11, low: 0.88, high: 1.33, unit: 'MAE, log units' } },
      ],
      finding: 'No. xTB performed worse than RDKit on our reference set, and the intervals do not overlap.',
      decision: 'The pipeline uses RDKit. xTB results stay in the data download so others can check this.',
      evidence: 'validated',
    },
  ],
  positiveControls: [
    {
      id: 'pc-artemisinin', preregisteredId: 'p1', taxon: 'Artemisia annua', compound: 'Artemisinin',
      a: { label: 'Cold soak, wrung out (as in Ge Hong)', preparation: { family: 'historical', vehicle: 'cold_infusion', filtered: null, heat: 'cold', duration: null }, likelihood: { low: 0.33, high: 0.55, point: 0.44 } },
      b: { label: 'Hot decoction', preparation: { family: 'modern', vehicle: 'aqueous_extract', filtered: true, heat: 'boiled', duration: null }, likelihood: { low: 0.11, high: 0.33, point: 0.22 } },
      expected: 'The cold preparation ranks above the hot decoction.',
      outcome: 'borderline',
      explanation: 'The direction matches the historical account, but the ranges touch at 0.33. By our own pre-registered rule, touching ranges are not a clear difference, so this is borderline, not a pass.',
      evidence: 'validated',
    },
  ],
  preregistered: [
    { id: 'p1', registeredOn: '2026-09-01', criterion: 'Positive control: cold A. annua preparation above hot decoction for artemisinin, ranges not overlapping.', outcome: 'borderline', detail: 'Direction right; ranges touch.', evidence: 'validated' },
    { id: 'p2', registeredOn: '2026-09-01', criterion: 'xTB logP error lower than RDKit logP error on the reference set.', outcome: 'fail', detail: 'xTB worse; intervals do not overlap.', evidence: 'validated' },
    { id: 'p3', registeredOn: '2026-09-01', criterion: 'Culpeper top-candidate name agreement with expert review at or above the registered threshold.', outcome: 'pass', detail: 'Met.', evidence: 'validated' },
    { id: 'p4', registeredOn: '2026-09-01', criterion: 'Pliny top-candidate name agreement with expert review at or above the same threshold.', outcome: 'fail', detail: 'Not met; source treated as lower confidence throughout.', evidence: 'provisional' },
    { id: 'p5', registeredOn: null, criterion: 'Top-5 hypothesis ranks stable when any one heuristic is switched off.', outcome: 'not_run', detail: 'Scheduled.', evidence: 'pending' },
  ],
  limitations: [
    'The model predicts extraction, not detection; plant content is not modelled.',
    'Historical quantities (handfuls, quarts) are unstandardised.',
    'The composition of historical wine and vinegar is unknown and modelled as ranges.',
    'Pliny’s plant names are often disputed; results for Pliny are lower confidence.',
    'Field extraction is AI-assisted; provisional items have not been checked by a person.',
    'The study audit covers indexed literature only and may miss non-English work.',
    'Heuristics (acidity, heat sensitivity) are rules of thumb.',
    'No hypothesis has yet been tested in a laboratory.',
  ],
};

/* sources.json */
export const sources: SourcesFile = {
  sources: [
    { id: 'culpeper', title: 'Nicholas Culpeper, The English Physitian', role: 'historical text', edition: 'London: Peter Cole', year: '1652', licence: 'Public domain (work)', licenceEvidence: 'provisional', url: null, note: 'The digital transcription used, and its licence, are to be confirmed.' },
    { id: 'culpeper-tx', title: 'Transcription of The English Physitian', role: 'historical text', edition: null, year: null, licence: null, licenceEvidence: 'pending', url: null, note: 'Team to confirm source and terms.' },
    { id: 'pliny', title: 'Pliny the Elder, Naturalis Historia (Latin)', role: 'historical text', edition: null, year: 'c. 77 CE', licence: 'Public domain (work)', licenceEvidence: 'provisional', url: null, note: 'Edition used to be confirmed.' },
    { id: 'pliny-tr', title: 'The Natural History of Pliny, trans. J. Bostock & H. T. Riley', role: 'translation', edition: 'London: H. G. Bohn', year: '1855–1857', licence: 'Public domain (translation)', licenceEvidence: 'provisional', url: 'https://www.gutenberg.org/ebooks/57493', note: 'Project Gutenberg vol. 1 linked; confirm this is the text used.' },
    { id: 'taxonomy', title: 'Taxonomic backbone for name resolution', role: 'taxonomy', edition: null, year: null, licence: null, licenceEvidence: 'pending', url: null },
    { id: 'pubmed', title: 'PubMed (NCBI) citation records', role: 'literature', edition: null, year: null, licence: 'NLM terms of use (confirm)', licenceEvidence: 'pending', url: 'https://pubmed.ncbi.nlm.nih.gov/' },
    { id: 'tox', title: 'Toxicity references', role: 'toxicity', edition: null, year: null, licence: null, licenceEvidence: 'pending', url: null },
    { id: 'rdkit', title: 'RDKit', role: 'software', edition: null, year: null, licence: 'BSD 3-Clause', licenceEvidence: 'provisional', url: 'https://www.rdkit.org/' },
    { id: 'xtb', title: 'xtb (Grimme lab)', role: 'software', edition: null, year: null, licence: 'LGPL-3.0', licenceEvidence: 'provisional', url: 'https://github.com/grimme-lab/xtb' },
  ],
  downloads: [
    { file: 'recipes.json', contract: 'Recipe[]', description: 'Recipes with passages, extracted field spans, name resolutions, preparations and toxicity.', format: 'json', licence: null },
    { file: 'species_profiles.json', contract: 'SpeciesProfile[]', description: 'Predicted extraction per compound and preparation, with drivers.', format: 'json', licence: null },
    { file: 'studies.json', contract: 'Study[]', description: 'Modern study preparations, field by field.', format: 'json', licence: null },
    { file: 'audit_summary.json', contract: 'AuditBreakdown[]', description: 'Per-source match counts.', format: 'json', licence: null },
    { file: 'hypotheses.json', contract: 'Hypothesis[]', description: 'Ranked leads with evidence trails.', format: 'json', licence: null },
    { file: 'validation.json', contract: 'Validation', description: 'Pipeline, metrics, method comparisons, controls, pre-registered checks, limitations.', format: 'json', licence: null },
    { file: 'heuristics.json', contract: 'Heuristic[]', description: 'The rules of thumb the model applies.', format: 'json', licence: null },
    { file: 'sources.json', contract: 'SourcesFile', description: 'This table and the download list.', format: 'json', licence: null },
    { file: 'coverage.json', contract: 'Coverage', description: 'Counts shown on Home.', format: 'json', licence: null },
    { file: 'reporting_gap.json', contract: 'ReportingGapFile', description: 'How often modern studies state each preparation detail, with 95% intervals.', format: 'json', licence: null },
    { file: 'plates.json', contract: 'Plate[]', description: 'Illustration slots, each with its licence, host and sourcing status.', format: 'json', licence: null },
    { file: 'lab_plan.json', contract: 'LabPlanFile', description: 'Lab Planner shortlist; quantum priority empty until the feature ships.', format: 'json', licence: null },
  ],
};

/** File name → data. Order = HANDOFF.md order. */
export const CONTRACT_FILES = {
  'recipes.json': recipes,
  'species_profiles.json': speciesProfiles,
  'studies.json': studies,
  'audit_summary.json': auditSummary,
  'hypotheses.json': hypotheses,
  'validation.json': validation,
  'heuristics.json': heuristics,
  'sources.json': sources,
  'coverage.json': coverage,
  // v2 additions (additive)
  'reporting_gap.json': reportingGap,
  'plates.json': plates,
  'lab_plan.json': labPlan,
} as const;
