/**
 * Lab Planner (design v2 lab_plan.json), derived from the ranked hypotheses: the quantum feature is not built, so its
 * score is null ("Coming in this release"); the readout and effort are not decided anywhere in the data, and the
 * ranking records no rank interval, so those are null too (shown as Unknown). Leads whose toxicity is reported are
 * withheld from planning and named (acceptance check 5); the rest keep their order.
 */
import type { Hypothesis, LabPlanFile } from '../../types';

export function toLabPlan(hs: Hypothesis[]): { plan: LabPlanFile; withheld: Hypothesis[]; planned: Hypothesis[] } {
  const sorted = [...hs].sort((a, b) => a.rank - b.rank);
  const withheld = sorted.filter((h) => h.toxicity.category === 'toxic_reported');
  const planned = sorted.filter((h) => h.toxicity.category !== 'toxic_reported');
  return {
    plan: {
      feature: {
        name: 'Quantum-informed priority', status: 'coming_soon', release: null,
        description: 'Will add a solvation-based priority score for each experiment. Until it ships, experiments are ordered by the conservative profile gap only.',
      },
      items: planned.map((h, i) => ({
        id: `lp-${h.id}`, hypothesisId: h.id,
        title: `${h.taxon}: ${h.faithful.label} vs ${h.modern?.label ?? 'the modern method'}`,
        compares: [h.faithful.label, h.modern?.label ?? 'modern method not modelled'],
        readout: null, effort: null, rank: i + 1, rankRange: null, quantumScore: null,
      })),
    },
    withheld, planned,
  };
}
