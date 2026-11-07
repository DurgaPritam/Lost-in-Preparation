/**
 * MOCK species profiles for the Preparation Lab (contract: species_profiles.json).
 *
 * The Lab lets a user set solvent × heat × filtration × acidity. The contract
 * already supports this: a SpeciesProfile lists preparations, each with a
 * Preparation and per-compound estimates + drivers. The Lab looks up the
 * preparation matching the controls; when none exists it shows "No estimate
 * for this combination" — it never interpolates.
 *
 * Numbers come from a deliberately crude toy rule and are SNAPPED to
 * multiples of 0.11 so they read as placeholders (0.11, 0.22, 0.33 …).
 * Compound names are real; no number means anything.
 */
import type { CompoundEstimate, Driver, HeatLevel, LikelihoodRange, Preparation, PreparationProfile, SpeciesProfile, ToxicityRecord, Vehicle } from '../types';
import { toxConcern, toxNone, toxReported } from '../gallery/mock';

type Polarity = 'polar' | 'mid' | 'lipo' | 'alkaloid';
interface Cmpd { name: string; cls: string; pol: Polarity; volatile?: boolean; labile?: boolean }

const SOLVENT: Record<string, Record<Polarity, number> & { sure: number }> = {
  water:   { polar: 0.60, mid: 0.30, lipo: 0.10, alkaloid: 0.30, sure: 0.22 },
  wine:    { polar: 0.50, mid: 0.50, lipo: 0.25, alkaloid: 0.40, sure: 0.22 },
  vinegar: { polar: 0.55, mid: 0.30, lipo: 0.10, alkaloid: 0.55, sure: 0.33 },
  oil:     { polar: 0.05, mid: 0.30, lipo: 0.70, alkaloid: 0.35, sure: 0.33 },
  honey:   { polar: 0.45, mid: 0.20, lipo: 0.05, alkaloid: 0.25, sure: 0.55 }, // wide on purpose: shows the wide-uncertainty state
  methanol:{ polar: 0.45, mid: 0.75, lipo: 0.55, alkaloid: 0.70, sure: 0.22 },
};
const snap = (x: number) => Math.round(Math.min(0.99, Math.max(0, x)) / 0.11) * 0.11;

function estimate(c: Cmpd, solvent: string, heat: HeatLevel, filtered: boolean, acid: boolean): { r: LikelihoodRange; drivers: Driver[] } {
  const s = SOLVENT[solvent];
  let v = s[c.pol];
  const heatMul = heat === 'cold' ? (c.volatile ? 1 : 0.8) : heat === 'warm' ? 1 : heat === 'boiled' || heat === 'reflux' ? (c.volatile ? 0.4 : c.labile ? 0.55 : 1.25) : 1;
  v *= heatMul;
  if (acid && c.pol === 'alkaloid') v += 0.2;
  if (filtered && c.pol === 'lipo') v *= 0.85;
  const w = s.sure + (c.pol === 'lipo' && solvent === 'water' ? 0.22 : 0);
  let low = snap(v - w / 2), high = snap(v + w / 2);
  if (high - low < 0.11) high = snap(low + 0.11);
  if (low >= 0.99) low = 0.88;
  const unknown = solvent === 'honey' && c.pol === 'lipo'; // not modelled → Unknown, never 0
  const r: LikelihoodRange = unknown ? { low: null, high: null } : { low: +low.toFixed(2), high: +high.toFixed(2), point: +snap((low + high) / 2).toFixed(2) };

  const solventEffect = s[c.pol] >= 0.45 ? 'raises' : s[c.pol] <= 0.15 ? 'lowers' : 'neutral';
  const drivers: Driver[] = [
    { id: 'solvent', effect: unknown ? 'unknown' : solventEffect, strength: solventEffect === 'neutral' ? null : s[c.pol] >= 0.6 || s[c.pol] <= 0.1 ? 'strong' : 'moderate', heuristic: false,
      note: unknown ? `${solvent} is not modelled for this compound class.` : `${solvent[0].toUpperCase() + solvent.slice(1)} vs a ${c.pol === 'polar' ? 'polar' : c.pol === 'lipo' ? 'lipophilic' : c.pol === 'alkaloid' ? 'basic (alkaloid)' : 'mid-polarity'} compound.` },
    { id: 'heat', effect: heatMul > 1.05 ? 'raises' : heatMul < 0.95 ? 'lowers' : 'neutral', strength: heatMul <= 0.55 || heatMul >= 1.25 ? 'strong' : heatMul === 1 ? null : 'moderate', heuristic: true,
      note: c.volatile && heat !== 'cold' ? 'Volatile: heating treated as driving it off.' : c.labile && (heat === 'boiled' || heat === 'reflux') ? 'Heat-labile: boiling treated as degrading it.' : heat === 'cold' ? 'No heat: slower release assumed.' : 'Heat treated as speeding release.' },
    { id: 'filtration', effect: filtered && c.pol === 'lipo' ? 'lowers' : 'neutral', strength: filtered && c.pol === 'lipo' ? 'weak' : null, heuristic: false,
      note: filtered ? 'Strained: particle-bound material removed.' : 'Unstrained: particles stay in the liquid.' },
    { id: 'acidity', effect: acid && c.pol === 'alkaloid' ? 'raises' : 'neutral', strength: acid && c.pol === 'alkaloid' ? 'moderate' : null, heuristic: true,
      note: acid ? 'Acidic: bases treated as dissolving as salts.' : 'Not acidified.' },
  ];
  return { r, drivers };
}

interface Combo { vehicle: Vehicle; solvent: string; heat: HeatLevel; filtered: boolean; acidified: boolean; label: string }
const COMBOS: Combo[] = [
  { vehicle: 'water', solvent: 'water', heat: 'cold', filtered: true, acidified: false, label: 'Cold water, strained' },
  { vehicle: 'water', solvent: 'water', heat: 'cold', filtered: false, acidified: false, label: 'Cold water, unstrained' },
  { vehicle: 'water', solvent: 'water', heat: 'warm', filtered: true, acidified: false, label: 'Warm water, strained' },
  { vehicle: 'water', solvent: 'water', heat: 'boiled', filtered: true, acidified: false, label: 'Decoction, strained' },
  { vehicle: 'water', solvent: 'water', heat: 'boiled', filtered: false, acidified: false, label: 'Decoction, unstrained' },
  { vehicle: 'wine', solvent: 'wine', heat: 'cold', filtered: true, acidified: false, label: 'Wine, cold, strained' },
  { vehicle: 'wine', solvent: 'wine', heat: 'warm', filtered: true, acidified: false, label: 'Wine, warm, strained' },
  { vehicle: 'vinegar', solvent: 'vinegar', heat: 'cold', filtered: true, acidified: true, label: 'Vinegar, cold, strained' },
  { vehicle: 'vinegar', solvent: 'vinegar', heat: 'boiled', filtered: true, acidified: true, label: 'Vinegar, boiled, strained' },
  { vehicle: 'oil', solvent: 'oil', heat: 'warm', filtered: false, acidified: false, label: 'Oil, warm, unstrained' },
  { vehicle: 'honey', solvent: 'honey', heat: 'warm', filtered: true, acidified: false, label: 'Honey, warm, strained' },
];

function profile(taxon: string, toxicity: ToxicityRecord, cmpds: Cmpd[], modernLabel = 'Methanol extract, reflux, filtered'): SpeciesProfile {
  const preps: PreparationProfile[] = COMBOS.map((c, i) => ({
    id: `${c.solvent}-${c.heat}-${c.filtered ? 'f' : 'u'}-${c.acidified ? 'a' : 'n'}`,
    label: c.label,
    preparation: { family: 'historical', vehicle: c.vehicle, heat: c.heat, filtered: c.filtered, acidified: c.acidified, duration: null } satisfies Preparation,
    origin: i % 4 === 0 ? { kind: 'recipe', recipeId: 'cul-liquorice-decoction', source: 'culpeper_1652' } : { kind: 'study', citation: '[MOCK] Model scenario (no recipe attests this exact preparation)' },
    estimates: cmpds.map((m): CompoundEstimate => {
      const e = estimate(m, c.solvent, c.heat, c.filtered, c.acidified);
      return { compound: m.name, compoundClass: m.cls, likelihood: e.r, drivers: e.drivers };
    }),
  }));
  preps.push({
    id: 'modern-methanol',
    label: modernLabel,
    preparation: { family: 'modern', vehicle: 'methanol_extract', heat: 'reflux', filtered: true, acidified: false, duration: '[MOCK] 2 h' },
    origin: { kind: 'study', citation: '[MOCK] Typical modern protocol (placeholder citation)' },
    estimates: cmpds.map((m) => { const e = estimate(m, 'methanol', 'warm', true, false); return { compound: m.name, compoundClass: m.cls, likelihood: e.r, drivers: e.drivers }; }),
  });
  return { taxon, toxicity, preparations: preps };
}

export const LAB_PROFILES: SpeciesProfile[] = [
  profile('Glycyrrhiza glabra', toxConcern, [
    { name: 'Glycyrrhizin', cls: 'Triterpene saponins', pol: 'polar' },
    { name: 'Liquiritin', cls: 'Flavonoid glycosides', pol: 'polar' },
    { name: 'Isoliquiritigenin', cls: 'Chalcones', pol: 'mid' },
    { name: 'Glabridin', cls: 'Isoflavans', pol: 'lipo' },
  ]),
  profile('Artemisia absinthium', toxConcern, [
    { name: 'Absinthin', cls: 'Sesquiterpene lactones', pol: 'mid', labile: true },
    { name: 'Thujone (α/β)', cls: 'Monoterpenes (volatile oil)', pol: 'lipo', volatile: true },
    { name: 'Quercetin glycosides', cls: 'Flavonoids', pol: 'polar' },
    { name: 'Chlorogenic acid', cls: 'Phenolic acids', pol: 'polar' },
  ]),
  profile('Salvia officinalis', toxNone, [
    { name: 'Rosmarinic acid', cls: 'Phenolic acids', pol: 'polar' },
    { name: 'Carnosic acid', cls: 'Diterpenes', pol: 'lipo', labile: true },
    { name: 'Thujone (α/β)', cls: 'Monoterpenes (volatile oil)', pol: 'lipo', volatile: true },
  ]),
  profile('Conium maculatum', toxReported, [
    { name: 'Coniine', cls: 'Piperidine alkaloids', pol: 'alkaloid', volatile: true },
    { name: 'γ-Coniceine', cls: 'Piperidine alkaloids', pol: 'alkaloid' },
  ]),
];

/** Plants offered in the Lab picker. A plant without a profile shows the "no data" state. */
export const LAB_PLANTS: { taxon: string; common: string; hasProfile: boolean }[] = [
  { taxon: 'Glycyrrhiza glabra', common: 'Liquorice', hasProfile: true },
  { taxon: 'Artemisia absinthium', common: 'Wormwood', hasProfile: true },
  { taxon: 'Salvia officinalis', common: 'Sage', hasProfile: true },
  { taxon: 'Conium maculatum', common: 'Hemlock', hasProfile: true },
  { taxon: 'Mentha sp.', common: 'Mint (genus only)', hasProfile: false },
];

/** Simulated per-species fetch so loading/error are real states. */
export function loadLabProfile(taxon: string, ms = 700): Promise<SpeciesProfile | null> {
  return new Promise((resolve) => setTimeout(() => resolve(LAB_PROFILES.find((p) => p.taxon === taxon) ?? null), ms));
}
