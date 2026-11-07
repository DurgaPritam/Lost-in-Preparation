/** Name-resolution coverage by evidence status, and counts (Methods & data overview). */
import type { Coverage, EvidenceStatus } from '../../types';
import type { ContractRecipe, ContractSpecies } from '../load';
import { candidateEvidence } from './common';

export function coverage(species: ContractSpecies[], recipes: ContractRecipe[], studies: number): Coverage {
  const byName = new Map<string, EvidenceStatus>();
  for (const s of species) byName.set(s.id.split('|')[1], candidateEvidence(s.basis));
  const counts: Record<EvidenceStatus, number> = { validated: 0, provisional: 0, pending: 0 };
  byName.forEach((e) => { counts[e] += 1; });
  return { nameResolutions: counts, recipes: recipes.length, studies };
}
