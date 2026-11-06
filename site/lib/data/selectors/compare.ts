/** Contract species profiles → the design's SpeciesProfile (written per species to public/data/compare/ at build). */
import type { CompoundEstimate, Driver, DriverId, Preparation, PreparationFamily, PreparationProfile, SpeciesProfile } from '../../types';
import type { ContractProfile, ContractProfileIndex } from '../load';
import { toxicityFromIndex } from './common';

const HISTORICAL_VEHICLES = new Set(['water', 'wine', 'vinegar', 'oil', 'honey', 'none', 'other', 'unknown']);

export function keyParts(key: string) {
  const [part, freshOrDried, solvent, heat, filtered] = key.split('|');
  return { part, freshOrDried, solvent, heat, filtered };
}
export function familyOfKey(key: string): PreparationFamily {
  return keyParts(key).solvent.split('+').every((s) => HISTORICAL_VEHICLES.has(s)) ? 'historical' : 'modern';
}
export function preparationOfKey(key: string): Preparation {
  const k = keyParts(key);
  return {
    family: familyOfKey(key), vehicle: k.solvent,
    heat: k.heat === 'unknown' ? null : (k.heat as Preparation['heat']),
    filtered: k.filtered === 'yes' ? true : k.filtered === 'no' ? false : k.filtered === 'not_applicable' ? 'not_applicable' : null,
  };
}
export const prepId = (p: { preparationKey: string; process?: string | null }) => `${p.preparationKey}#${p.process ?? 'unknown'}`;

/**
 * A driver is the model's multiplier for one factor (contract Drivers). Direction and strength are a display binning
 * of that number; the multiplier itself is printed in the note, so the binning hides nothing.
 */
export function driverOf(id: DriverId, m: number, heuristic: boolean): Driver {
  const effect = m > 1.02 ? 'raises' : m < 0.98 ? 'lowers' : 'neutral';
  const strength = effect === 'neutral' ? null
    : effect === 'lowers' ? (m < 0.5 ? 'strong' : m < 0.8 ? 'moderate' : 'weak')
    : (m > 2 ? 'strong' : m > 1.25 ? 'moderate' : 'weak');
  return { id, effect, strength, heuristic, note: `Model multiplier ×${m.toFixed(2)}` };
}

const r3 = (n: number) => Math.round(n * 1000) / 1000;
export function toSpeciesProfile(entry: ContractProfileIndex, profiles: ContractProfile[]): SpeciesProfile {
  const preparations: PreparationProfile[] = profiles.map((p) => ({
    id: prepId(p),
    label: p.preparationLabel ?? p.preparationKey,
    preparation: preparationOfKey(p.preparationKey),
    origin: { kind: 'model', note: `Model preset · ${p.coverageNote}` },
    estimates: p.compounds.map((c): CompoundEstimate => ({
      compound: c.name, compoundClass: c.class,
      likelihood: { low: r3(c.low), high: r3(c.high), point: r3(c.likelihood) },
      drivers: [
        driverOf('solvent', c.drivers.solvent, false),
        driverOf('heat', c.drivers.heat, c.heuristic?.heat ?? true),
        driverOf('filtration', c.drivers.filtration, c.heuristic?.filtration ?? true),
        driverOf('acidity', c.drivers.acidity, c.heuristic?.acidity ?? true),
      ],
    })),
  }));
  return { taxon: entry.acceptedName, toxicity: toxicityFromIndex(entry), preparations };
}

/**
 * Compact form written to public/data/compare/<speciesId>.json (the full SpeciesProfile repeats every compound name
 * and driver note per preparation). Compounds are listed once; each preparation holds one row per compound:
 * [low, high, point, solvent, heat, filtration, acidity, heuristic bits (1 heat · 2 filtration · 4 acidity)] or null
 * when the preparation has no estimate for that compound. expandProfile() rebuilds the SpeciesProfile in the browser.
 */
export interface CompactProfile {
  taxon: string;
  toxicity: SpeciesProfile['toxicity'];
  compounds: [string, string][];
  preps: { id: string; label: string; preparation: Preparation; note: string; rows: (number[] | null)[] }[];
}
export function compactProfile(entry: ContractProfileIndex, profiles: ContractProfile[]): CompactProfile {
  const ids: string[] = [];
  const meta = new Map<string, [string, string]>();
  for (const p of profiles) for (const c of p.compounds) if (!meta.has(c.compoundId)) { meta.set(c.compoundId, [c.name, c.class]); ids.push(c.compoundId); }
  return {
    taxon: entry.acceptedName, toxicity: toxicityFromIndex(entry), compounds: ids.map((i) => meta.get(i)!),
    preps: profiles.map((p) => {
      const by = new Map(p.compounds.map((c) => [c.compoundId, c]));
      return {
        id: prepId(p), label: p.preparationLabel ?? p.preparationKey, preparation: preparationOfKey(p.preparationKey), note: `Model preset · ${p.coverageNote}`,
        rows: ids.map((i) => {
          const c = by.get(i);
          if (!c) return null;
          const h = c.heuristic ?? { heat: true, filtration: true, acidity: true };
          return [r3(c.low), r3(c.high), r3(c.likelihood), r3(c.drivers.solvent), r3(c.drivers.heat), r3(c.drivers.filtration), r3(c.drivers.acidity),
                  (h.heat ? 1 : 0) | (h.filtration ? 2 : 0) | (h.acidity ? 4 : 0)];
        }),
      };
    }),
  };
}
export function expandProfile(cp: CompactProfile): SpeciesProfile {
  return {
    taxon: cp.taxon, toxicity: cp.toxicity,
    preparations: cp.preps.map((p): PreparationProfile => ({
      id: p.id, label: p.label, preparation: p.preparation, origin: { kind: 'model', note: p.note },
      estimates: p.rows.flatMap((r, i): CompoundEstimate[] => r == null ? [] : [{
        compound: cp.compounds[i][0], compoundClass: cp.compounds[i][1], likelihood: { low: r[0], high: r[1], point: r[2] },
        drivers: [driverOf('solvent', r[3], false), driverOf('heat', r[4], !!(r[7] & 1)), driverOf('filtration', r[5], !!(r[7] & 2)), driverOf('acidity', r[6], !!(r[7] & 4))],
      }]),
    })),
  };
}
