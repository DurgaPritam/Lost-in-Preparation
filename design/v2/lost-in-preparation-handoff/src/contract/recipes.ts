/**
 * MOCK DATA for the Phase 2 screens. Shapes follow src/types.ts (assumed
 * until the project JSON Schemas arrive).
 * - All likelihoods use repeating digits (0.11, 0.22 …): placeholders only.
 * - Passages are invented, labelled [MOCK], and are NOT quotations of
 *   Culpeper or Pliny. Plant and compound names are real so the layout is
 *   realistic; no number attached to them means anything.
 * - Offsets are computed from the text so spans can't drift.
 */
import type { ExtractedField, Passage, Recipe, EvidenceStatus, ExtractedFieldKind } from '../types';
import { nameDisputed, nameGenus, toxConcern, toxLacking, toxNone, toxReported } from '../gallery/mock';

function field(text: string, phrase: string, kind: ExtractedFieldKind, value: string | null, evidence: EvidenceStatus, n = 0): ExtractedField {
  let start = -1;
  for (let i = 0; i <= n; i++) start = text.indexOf(phrase, start + 1);
  if (start < 0) throw new Error(`mock: "${phrase}" not in passage`);
  return { id: `${kind}-${start}`, kind, start, end: start + phrase.length, value, evidence };
}
const before = (text: string, phrase: string) => text.indexOf(phrase);

const T1 = '[MOCK] Take the tops of Wormwood, two handfuls, and steep them cold in a quart of white wine three days; then strain it through a linen cloth, and keep it close stopped in a glass.';
const P1: Passage = {
  text: T1,
  edition: '[MOCK] Culpeper, The English Physitian (1652), transcription placeholder',
  locator: 'entry “Wormwood”, placeholder locator',
  fields: [
    field(T1, 'tops', 'part', 'flowering tops', 'validated'),
    field(T1, 'Wormwood', 'plant', 'Wormwood', 'validated'),
    field(T1, 'two handfuls', 'quantity', '2 handfuls (unstandardised)', 'provisional'),
    field(T1, 'cold', 'heat', 'cold', 'provisional'),
    field(T1, 'white wine', 'vehicle', 'wine', 'validated'),
    field(T1, 'three days', 'duration', '3 days', 'validated'),
    field(T1, 'strain it through', 'filtration', 'filtered (cloth)', 'provisional'),
  ],
  illegible: [{ id: 'ill-1', at: before(T1, 'linen'), estChars: 4, note: 'Ink loss in the scanned copy; about 4 characters.' }],
};

const T2 = '[MOCK] The tops of absinthium are boiled in sharp vinegar until it comes to a third part; it is then pressed out, and the liquor kept in a sealed vessel.';
const P2: Passage = {
  text: T2,
  edition: '[MOCK] Pliny the Elder, Naturalis Historia, translation placeholder',
  locator: 'book and chapter placeholder',
  fields: [
    field(T2, 'tops', 'part', 'flowering tops', 'provisional'),
    field(T2, 'absinthium', 'plant', 'absinthium (disputed)', 'provisional'),
    field(T2, 'boiled', 'heat', 'boiled', 'provisional'),
    field(T2, 'sharp vinegar', 'vehicle', 'vinegar', 'provisional'),
    field(T2, 'until it comes to a third part', 'duration', null, 'pending'),
    field(T2, 'pressed out', 'filtration', 'pressed; straining not stated', 'provisional'),
  ],
  illegible: [
    { id: 'ill-2', at: before(T2, 'until'), estChars: null, note: 'Lacuna in the source text; length unknown.' },
  ],
};

const T3 = '[MOCK] Menta is laid in oil and set in the sun for some days.';
const P3: Passage = {
  text: T3, edition: '[MOCK] Pliny the Elder, Naturalis Historia, translation placeholder', locator: 'placeholder',
  fields: [
    field(T3, 'Menta', 'plant', 'menta (genus only)', 'provisional'),
    field(T3, 'oil', 'vehicle', 'oil', 'provisional'),
    field(T3, 'set in the sun', 'heat', 'warm', 'provisional'),
    field(T3, 'some days', 'duration', null, 'pending'),
  ],
  illegible: [],
};

const T4 = '[MOCK] Hemlock leaves bruised and infused in oil.';
const P4: Passage = {
  text: T4, edition: '[MOCK] Culpeper, The English Physitian (1652), transcription placeholder', locator: 'placeholder',
  fields: [
    field(T4, 'Hemlock', 'plant', 'Hemlock', 'validated'),
    field(T4, 'leaves', 'part', 'leaf', 'validated'),
    field(T4, 'oil', 'vehicle', 'oil', 'validated'),
  ],
  illegible: [],
};

const T5 = '[MOCK] The leaves of Sage, a handful, infused in cold water a night, and strained.';
const P5: Passage = {
  text: T5, edition: '[MOCK] Culpeper, The English Physitian (1652), transcription placeholder', locator: 'placeholder',
  fields: [
    field(T5, 'leaves', 'part', 'leaf', 'validated'),
    field(T5, 'Sage', 'plant', 'Sage', 'validated'),
    field(T5, 'a handful', 'quantity', '1 handful (unstandardised)', 'provisional'),
    field(T5, 'cold water', 'vehicle', 'cold infusion', 'validated'),
    field(T5, 'a night', 'duration', '≈1 night', 'provisional'),
    field(T5, 'strained', 'filtration', 'filtered', 'validated'),
  ],
  illegible: [],
};

const T6 = '[MOCK] Take the root of Liquorice, scrape and bruise it, and boil it in fair water till a third part be consumed; then strain it, and keep it for use.';
const P6: Passage = {
  text: T6, edition: '[MOCK] Culpeper, The English Physitian (1652), transcription placeholder', locator: 'entry “Liquorice”, placeholder locator',
  fields: [
    field(T6, 'root', 'part', 'root', 'validated'),
    field(T6, 'Liquorice', 'plant', 'Liquorice', 'validated'),
    field(T6, 'boil', 'heat', 'boiled', 'validated'),
    field(T6, 'fair water', 'vehicle', 'water', 'validated'),
    field(T6, 'till a third part be consumed', 'duration', 'reduced by one third', 'provisional'),
    field(T6, 'strain it', 'filtration', 'filtered', 'validated'),
  ],
  illegible: [{ id: 'ill-6', at: T6.indexOf('keep'), estChars: 3, note: 'Faded type; about 3 characters.' }],
};

export const RECIPES: Recipe[] = [
  {
    id: 'cul-liquorice-decoction', source: 'culpeper_1652', evidence: 'validated',
    name: { historicalName: 'Liquorice', source: 'culpeper_1652', state: 'resolved', candidates: [{ taxon: 'Glycyrrhiza glabra', authority: 'L.', rank: 'species', confidence: { low: 0.77, high: 0.99, point: 0.88 }, evidence: 'validated' }] },
    preparation: { family: 'historical', vehicle: 'water', filtered: true, heat: 'boiled', acidified: false, duration: 'reduced by one third' },
    passage: P6, toxicity: toxConcern,
  },
  {
    id: 'cul-wormwood-wine', source: 'culpeper_1652', evidence: 'validated',
    name: { historicalName: 'Wormwood', source: 'culpeper_1652', state: 'resolved', candidates: [{ taxon: 'Artemisia absinthium', authority: 'L.', rank: 'species', confidence: { low: 0.77, high: 0.99, point: 0.88 }, evidence: 'validated' }] },
    preparation: { family: 'historical', vehicle: 'wine', filtered: true, heat: 'cold', duration: '3 days' },
    passage: P1, toxicity: toxConcern,
  },
  {
    id: 'pli-absinthium-vinegar', source: 'pliny_nh', evidence: 'provisional',
    name: nameDisputed,
    preparation: { family: 'historical', vehicle: 'vinegar', filtered: null, heat: 'boiled', duration: null },
    passage: P2, toxicity: toxConcern,
  },
  {
    id: 'pli-menta-oil', source: 'pliny_nh', evidence: 'pending',
    name: nameGenus,
    preparation: { family: 'historical', vehicle: 'oil', filtered: null, heat: 'warm', duration: null },
    passage: P3, toxicity: toxLacking,
  },
  {
    id: 'cul-hemlock-oil', source: 'culpeper_1652', evidence: 'validated',
    name: { historicalName: 'Hemlock', source: 'culpeper_1652', state: 'resolved', candidates: [{ taxon: 'Conium maculatum', authority: 'L.', rank: 'species', confidence: { low: 0.66, high: 0.99, point: 0.88 }, evidence: 'validated' }] },
    preparation: { family: 'historical', vehicle: 'oil', filtered: null, heat: null, duration: null },
    passage: P4, toxicity: toxReported,
  },
  {
    id: 'cul-sage-cold', source: 'culpeper_1652', evidence: 'provisional',
    name: { historicalName: 'Sage', source: 'culpeper_1652', state: 'resolved', candidates: [{ taxon: 'Salvia officinalis', authority: 'L.', rank: 'species', confidence: { low: 0.66, high: 0.88, point: 0.77 }, evidence: 'provisional' }] },
    preparation: { family: 'historical', vehicle: 'cold_infusion', filtered: true, heat: 'cold', duration: '≈1 night' },
    passage: P5, toxicity: toxNone,
  },
];
