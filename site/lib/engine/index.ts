/**
 * Preparation engine: the M4 model, in the browser. Pure functions, no I/O; callers pass the validated
 * engine/model.json and engine/<speciesId>.json (contract v1.7, P38).
 */
import { estimate, heuristicFlags, Streams } from './model';
import type { EngineEstimate, EngineModel, EnginePrep, EngineSpecies } from './types';

export { estimate, heuristicFlags, simulate, Streams } from './model';
export { choiceKey, customSeedOffset, fnv1a32, preparationFor, type PrepChoice } from './prep';
export type * from './types';

/** One preparation for every compound of a species, in species order. */
export function computeProfile(species: EngineSpecies, prep: EnginePrep, model: EngineModel, streams = new Streams(model)): EngineEstimate[] {
  return species.compounds.map((c) => estimate(c, prep, model, streams));
}

export const flagsOf = heuristicFlags;
