/** Contract preparation keys ("part|freshOrDried|solvent(+joined)|heat|filtered", P4) → the design's Preparation, and
 *  the Lab settings a key maps to (only when the Lab can represent it exactly). */
import type { Preparation, PreparationFamily } from '../../types';
import { labHref, type LabHeat, type LabSolvent } from './lab';

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
    acidified: k.solvent.split('+').includes('vinegar') ? true : null,
  };
}
const LAB_SOLVENTS = new Set<string>(['water', 'wine', 'vinegar', 'oil', 'honey']);
/** The Lab URL for a preparation key, or null when the Lab has no exact equivalent (mixtures, no vehicle, unstated
 *  heat or filtration, modern solvents): a link must never land on a different preparation. */
export function labHrefOfKey(taxon: string, key: string): string | null {
  const k = keyParts(key);
  if (!LAB_SOLVENTS.has(k.solvent) || !['cold', 'warm', 'boiled'].includes(k.heat) || !['yes', 'no'].includes(k.filtered)) return null;
  return labHref({ plant: taxon, solvent: k.solvent as LabSolvent, heat: k.heat as LabHeat, filtered: k.filtered === 'yes', acidified: k.solvent === 'vinegar' });
}
