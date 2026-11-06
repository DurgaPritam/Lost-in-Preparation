/**
 * Preparations for the engine. A combination that is one of the 13 pipeline preparations uses that preparation's
 * seedOffset, so its result equals the published profile exactly. Any other combination gets the deterministic
 * seedOffset in engine/model.json `customSeedRule` (FNV-1a hash), the same rule the pipeline used for parity.json.
 * Solvent, heat, filtration and process stay separate inputs (non-negotiable 4).
 */
import type { EngineModel, EnginePrep, Filtered, Heat, Process } from './types';

export interface PrepChoice {
  solvents: string[];
  heat: Heat;
  filtered: Filtered;
  process: Process | null;
}

/** 32-bit FNV-1a of the UTF-8 bytes. */
export function fnv1a32(s: string): number {
  let h = 0x811c9dc5;
  for (const b of new TextEncoder().encode(s)) {
    h ^= b;
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

export const choiceKey = (p: PrepChoice) => `${[...p.solvents].sort().join('+')}|${p.heat}|${p.filtered}|${p.process ?? ''}`;

export const customSeedOffset = (p: PrepChoice) => 1000 + (fnv1a32(choiceKey(p)) % 1_000_000);

/** The engine preparation for a choice: the grid entry when it is one of the 13, otherwise a custom one. */
export function preparationFor(model: EngineModel, p: PrepChoice): EnginePrep {
  const key = choiceKey(p);
  const grid = model.preparations.find((g) => choiceKey({ solvents: g.solvents, heat: g.heat, filtered: g.filtered, process: g.process }) === key);
  if (grid) return grid;
  return {
    seedOffset: customSeedOffset(p), key: `unknown|unknown|${[...p.solvents].sort().join('+')}|${p.heat}|${p.filtered}`,
    label: 'custom preparation', solvents: [...p.solvents], heat: p.heat, filtered: p.filtered, process: p.process,
  };
}
