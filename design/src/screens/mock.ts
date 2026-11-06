/**
 * MOCK DATA for the Phase 2 screens. Shapes follow src/types.ts (assumed
 * until the project JSON Schemas arrive).
 * - All likelihoods use repeating digits (0.11, 0.22 …): placeholders only.
 * - Passages are invented, labelled [MOCK], and are NOT quotations of
 *   Culpeper or Pliny. Plant and compound names are real so the layout is
 *   realistic; no number attached to them means anything.
 * - Offsets are computed from the text so spans can't drift.
 */
import type { ExtractedField, Passage, Recipe, SpeciesProfile, EvidenceStatus, ExtractedFieldKind } from '../types';
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

export const RECIPES: Recipe[] = [
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

/* ───────────── Compare: species profiles (loaded per species) ───────────── */

const D = {
  wineSolvent: { id: 'solvent', effect: 'raises', strength: 'moderate', heuristic: false, note: 'Dilute ethanol carries mid-polarity compounds.' },
  methanol: { id: 'solvent', effect: 'raises', strength: 'strong', heuristic: false, note: 'Methanol carries a wide polarity range.' },
  water: { id: 'solvent', effect: 'lowers', strength: 'moderate', heuristic: false, note: 'Water carries little of the less polar compounds.' },
  cold: { id: 'heat', effect: 'raises', strength: 'moderate', heuristic: true, note: 'No heating: volatile compounds treated as retained.' },
  reflux: { id: 'heat', effect: 'lowers', strength: 'strong', heuristic: true, note: 'Prolonged heat: volatile and heat-labile compounds treated as reduced.' },
  refluxUp: { id: 'heat', effect: 'raises', strength: 'moderate', heuristic: true, note: 'Heat treated as raising extraction of stable compounds.' },
  filtered: { id: 'filtration', effect: 'lowers', strength: 'weak', heuristic: false, note: 'Particulate-bound material removed.' },
  filtNeutral: { id: 'filtration', effect: 'neutral', strength: null, heuristic: false },
  acidMild: { id: 'acidity', effect: 'neutral', strength: 'weak', heuristic: true, note: 'Wine is mildly acidic; little effect assumed here.' },
  acidNone: { id: 'acidity', effect: 'neutral', strength: null, heuristic: true },
  acidUnknown: { id: 'acidity', effect: 'unknown', strength: null, heuristic: true, note: 'Acidity of this vehicle not modelled.' },
} as const;

export const PROFILES: Record<string, SpeciesProfile> = {
  'Artemisia absinthium': {
    taxon: 'Artemisia absinthium',
    toxicity: toxConcern,
    preparations: [
      {
        id: 'p-wine', label: 'Wine, cold, 3 days, strained',
        preparation: { family: 'historical', vehicle: 'wine', filtered: true, heat: 'cold', duration: '3 days' },
        origin: { kind: 'recipe', recipeId: 'cul-wormwood-wine', source: 'culpeper_1652' },
        estimates: [
          { compound: 'Absinthin', compoundClass: 'Sesquiterpene lactones', likelihood: { low: 0.33, high: 0.55, point: 0.44 }, drivers: [D.wineSolvent, D.cold, D.filtered, D.acidMild] },
          { compound: 'Artabsin', compoundClass: 'Sesquiterpene lactones', likelihood: { low: 0.22, high: 0.55, point: 0.33 }, drivers: [D.wineSolvent, D.cold, D.filtered, D.acidMild] },
          { compound: 'Thujone (α/β)', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: 0.55, high: 0.77, point: 0.66 }, drivers: [D.wineSolvent, D.cold, D.filtNeutral, D.acidNone] },
          { compound: 'Sabinene', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: 0.33, high: 0.66, point: 0.5 }, drivers: [D.wineSolvent, D.cold, D.filtNeutral, D.acidNone] },
          { compound: 'Quercetin glycosides', compoundClass: 'Flavonoids', likelihood: { low: 0.33, high: 0.66, point: 0.44 }, drivers: [D.wineSolvent, D.cold, D.filtered, D.acidMild] },
          { compound: 'Artemetin', compoundClass: 'Flavonoids', likelihood: { low: null, high: null }, drivers: [D.wineSolvent, D.cold, D.filtered, D.acidUnknown] },
          { compound: 'Chlorogenic acid', compoundClass: 'Phenolic acids', likelihood: { low: 0.22, high: 0.44, point: 0.33 }, drivers: [D.wineSolvent, D.cold, D.filtered, D.acidMild] },
        ],
      },
      {
        id: 'p-methanol', label: 'Methanol extract, reflux, filtered',
        preparation: { family: 'modern', vehicle: 'methanol_extract', filtered: true, heat: 'reflux', duration: '[MOCK] 2 h' },
        origin: { kind: 'study', citation: '[MOCK] Study A (placeholder citation)' },
        estimates: [
          { compound: 'Absinthin', compoundClass: 'Sesquiterpene lactones', likelihood: { low: 0.66, high: 0.88, point: 0.77 }, drivers: [D.methanol, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Artabsin', compoundClass: 'Sesquiterpene lactones', likelihood: { low: 0.44, high: 0.77, point: 0.55 }, drivers: [D.methanol, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Thujone (α/β)', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: 0.11, high: 0.33, point: 0.22 }, drivers: [D.methanol, D.reflux, D.filtNeutral, D.acidNone] },
          { compound: 'Sabinene', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: 0.11, high: 0.44, point: 0.22 }, drivers: [D.methanol, D.reflux, D.filtNeutral, D.acidNone] },
          { compound: 'Quercetin glycosides', compoundClass: 'Flavonoids', likelihood: { low: 0.55, high: 0.88, point: 0.66 }, drivers: [D.methanol, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Artemetin', compoundClass: 'Flavonoids', likelihood: { low: 0.44, high: 0.77, point: 0.55 }, drivers: [D.methanol, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Chlorogenic acid', compoundClass: 'Phenolic acids', likelihood: { low: 0.44, high: 0.77, point: 0.66 }, drivers: [D.methanol, D.refluxUp, D.filtered, D.acidNone] },
        ],
      },
      {
        id: 'p-decoction', label: 'Aqueous decoction, boiled, filtered',
        preparation: { family: 'modern', vehicle: 'aqueous_extract', filtered: true, heat: 'boiled', duration: '[MOCK] 30 min' },
        origin: { kind: 'study', citation: '[MOCK] Study B (placeholder citation)' },
        estimates: [
          { compound: 'Absinthin', compoundClass: 'Sesquiterpene lactones', likelihood: { low: 0.11, high: 0.33, point: 0.22 }, drivers: [D.water, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Artabsin', compoundClass: 'Sesquiterpene lactones', likelihood: { low: 0.11, high: 0.33 }, drivers: [D.water, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Thujone (α/β)', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: 0.11, high: 0.22, point: 0.11 }, drivers: [D.water, D.reflux, D.filtNeutral, D.acidNone] },
          { compound: 'Sabinene', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: null, high: null }, drivers: [D.water, D.reflux, D.filtNeutral, D.acidNone] },
          { compound: 'Quercetin glycosides', compoundClass: 'Flavonoids', likelihood: { low: 0.33, high: 0.55, point: 0.44 }, drivers: [D.water, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Artemetin', compoundClass: 'Flavonoids', likelihood: { low: 0.11, high: 0.33 }, drivers: [D.water, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Chlorogenic acid', compoundClass: 'Phenolic acids', likelihood: { low: 0.55, high: 0.77, point: 0.66 }, drivers: [D.water, D.refluxUp, D.filtered, D.acidNone] },
        ],
      },
    ],
  },
  'Salvia officinalis': {
    taxon: 'Salvia officinalis',
    toxicity: toxNone,
    preparations: [
      {
        id: 's-cold', label: 'Cold infusion, 1 night, strained',
        preparation: { family: 'historical', vehicle: 'cold_infusion', filtered: true, heat: 'cold', duration: '≈1 night' },
        origin: { kind: 'recipe', recipeId: 'cul-sage-cold', source: 'culpeper_1652' },
        estimates: [
          { compound: 'Rosmarinic acid', compoundClass: 'Phenolic acids', likelihood: { low: 0.44, high: 0.66, point: 0.55 }, drivers: [D.water, D.cold, D.filtered, D.acidNone] },
          { compound: 'Carnosic acid', compoundClass: 'Diterpenes', likelihood: { low: 0.11, high: 0.22, point: 0.11 }, drivers: [D.water, D.cold, D.filtered, D.acidNone] },
          { compound: 'Thujone (α/β)', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: 0.22, high: 0.55, point: 0.33 }, drivers: [D.water, D.cold, D.filtNeutral, D.acidNone] },
        ],
      },
      {
        id: 's-ethanol', label: 'Ethanol extract, warm, filtered',
        preparation: { family: 'modern', vehicle: 'ethanol_extract', filtered: true, heat: 'warm', duration: '[MOCK] 24 h' },
        origin: { kind: 'study', citation: '[MOCK] Study C (placeholder citation)' },
        estimates: [
          { compound: 'Rosmarinic acid', compoundClass: 'Phenolic acids', likelihood: { low: 0.55, high: 0.77, point: 0.66 }, drivers: [D.methanol, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Carnosic acid', compoundClass: 'Diterpenes', likelihood: { low: 0.55, high: 0.88, point: 0.77 }, drivers: [D.methanol, D.refluxUp, D.filtered, D.acidNone] },
          { compound: 'Thujone (α/β)', compoundClass: 'Monoterpenes (volatile oil)', likelihood: { low: 0.22, high: 0.44, point: 0.33 }, drivers: [D.methanol, D.reflux, D.filtNeutral, D.acidNone] },
        ],
      },
    ],
  },
};

/** Simulated per-species fetch so the loading state is real. */
export function loadProfile(taxon: string, ms = 900): Promise<SpeciesProfile> {
  return new Promise((resolve, reject) =>
    setTimeout(() => (PROFILES[taxon] ? resolve(PROFILES[taxon]) : reject(new Error(`No profile for ${taxon}`))), ms),
  );
}

export const COVERAGE_MOCK = { validated: 111, provisional: 222, pending: 333 };
