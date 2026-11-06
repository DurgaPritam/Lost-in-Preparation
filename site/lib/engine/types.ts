/** Engine types, inferred from the contract's generated Zod schemas (contract v1.7, P38). */
import type { z } from 'zod';
import type * as G from '../data/generated';

export type EngineModel = z.infer<typeof G.engineModel.schema>;
export type EngineSpecies = z.infer<typeof G.engineSpecies.schema>;
export type EngineCompound = EngineSpecies['compounds'][number];
export type EnginePrep = EngineModel['preparations'][number];
export type EngineParityCase = z.infer<typeof G.engineParity.schema>[number];
export type EngineEstimate = EngineParityCase['expected'][number];
export type Heat = EnginePrep['heat'];
export type Filtered = EnginePrep['filtered'];
export type Process = NonNullable<EnginePrep['process']>;
