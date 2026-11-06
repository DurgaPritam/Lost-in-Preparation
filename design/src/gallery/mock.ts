/**
 * MOCK DATA for the gallery only.
 * Numbers are deliberately artificial (repeating digits: 0.11, 0.22, 0.33 …)
 * so nobody can mistake them for results. Passages are placeholders, not
 * quotations. Toxicity sources are placeholder labels, not citations.
 * Shapes follow src/types.ts (to be replaced by the project JSON Schemas).
 */
import type { Heuristic, NameResolution, Preparation, SourceConfidence, ToxicityRecord, LikelihoodRange } from '../types';

export const MOCK_NOTE = 'Mock data. All numbers are placeholders with no meaning.';

export const sourceCulpeper: SourceConfidence = { source: 'culpeper_1652', level: 'higher', disputedShare: null, note: 'English vernacular names; most resolve to one species.' };
export const sourcePliny: SourceConfidence = { source: 'pliny_nh', level: 'lower', disputedShare: 0.7, note: 'Latin names from the 1st century; many map to several taxa.' };
export const sourceUnknown: SourceConfidence = { source: 'pliny_nh', level: 'unknown', disputedShare: null };

export const nameResolved: NameResolution = {
  historicalName: 'Wormwood', source: 'culpeper_1652', state: 'resolved',
  candidates: [{ taxon: 'Artemisia absinthium', authority: 'L.', rank: 'species', confidence: { low: 0.77, high: 0.99, point: 0.88 }, evidence: 'validated' }],
};
export const nameDisputed: NameResolution = {
  historicalName: 'absinthium', source: 'pliny_nh', state: 'disputed',
  candidates: [
    { taxon: 'Artemisia absinthium', authority: 'L.', rank: 'species', confidence: { low: 0.22, high: 0.66, point: 0.44 }, evidence: 'provisional' },
    { taxon: 'Artemisia pontica', authority: 'L.', rank: 'species', confidence: { low: 0.11, high: 0.55, point: 0.33 }, evidence: 'provisional' },
    { taxon: 'Artemisia', rank: 'genus', confidence: { low: null, high: null }, evidence: 'pending' },
  ],
};
export const nameGenus: NameResolution = {
  historicalName: 'menta', source: 'pliny_nh', state: 'genus_only',
  candidates: [{ taxon: 'Mentha', rank: 'genus', confidence: { low: 0.55, high: 0.88, point: 0.66 }, evidence: 'provisional' }],
};
export const nameUnresolved: NameResolution = { historicalName: '[illegible name]', source: 'pliny_nh', state: 'unresolved', candidates: [] };

export const rangeNarrow: LikelihoodRange = { low: 0.55, high: 0.66, point: 0.6 };
export const rangeWide: LikelihoodRange = { low: 0.11, high: 0.88, point: 0.5 };
export const rangeNoPoint: LikelihoodRange = { low: 0.22, high: 0.44 };
export const rangeUnknown: LikelihoodRange = { low: null, high: null };

export const heurAcidity: Heuristic = { id: 'acidity', label: 'Acidity', rule: 'Vinegar is treated as favouring extraction of basic compounds (e.g. alkaloids) as salts.' };
export const heurHeat: Heuristic = { id: 'heat_sensitivity', label: 'Heat sensitivity', rule: 'Prolonged boiling is treated as reducing volatile and heat-labile compounds.' };

export const toxReported: ToxicityRecord = { category: 'toxic_reported', sources: [{ label: '[MOCK] Toxicology reference A' }, { label: '[MOCK] Poison-centre monograph B' }] };
export const toxConcern: ToxicityRecord = { category: 'concern', sources: [{ label: '[MOCK] Review C' }], note: 'Concern recorded for one constituent at high intake.' };
export const toxNone: ToxicityRecord = { category: 'no_toxicity_reported', sources: [{ label: '[MOCK] Database D' }] };
export const toxLacking: ToxicityRecord = { category: 'data_lacking', sources: [] };
export const toxUnknown: ToxicityRecord = { category: 'unknown', sources: [] };

export const prepHist: Preparation = { family: 'historical', vehicle: 'wine', filtered: null };
export const prepHist2: Preparation = { family: 'historical', vehicle: 'decoction', filtered: true };
export const prepMod: Preparation = { family: 'modern', vehicle: 'methanol_extract', filtered: true };

export interface MockRow {
  id: string;
  name: NameResolution;
  prep: Preparation;
  extraction: LikelihoodRange;
  tox: ToxicityRecord;
}
export const rows: MockRow[] = [
  { id: 'r1', name: nameResolved, prep: prepHist, extraction: rangeNarrow, tox: toxConcern },
  { id: 'r2', name: nameDisputed, prep: prepHist2, extraction: rangeWide, tox: toxNone },
  { id: 'r3', name: nameGenus, prep: { family: 'historical', vehicle: 'vinegar', filtered: false }, extraction: rangeUnknown, tox: toxLacking },
  { id: 'r4', name: { historicalName: 'Hemlock', source: 'culpeper_1652', state: 'resolved', candidates: [{ taxon: 'Conium maculatum', authority: 'L.', rank: 'species', confidence: { low: 0.66, high: 0.99, point: 0.88 }, evidence: 'validated' }] }, prep: { family: 'historical', vehicle: 'oil', filtered: null }, extraction: rangeNoPoint, tox: toxReported },
];
