/** Contract hypotheses (+ audit, profiles, index) → the design's Hypothesis cards and evidence trail. */
import { neutralWording } from '../wording';
import type { Hypothesis, SourceWork, TrailStep } from '../../types';
import type { ContractAudit, ContractHypothesis, ContractProfile, ContractProfileIndex } from '../load';
import { labHrefOfKey, preparationOfKey } from './prepKey';
import { sourceWork, toxicityCategory, toxicityFromIndex } from './common';
import { recipeSlug } from './recipes';

export const hypothesisId = (h: Pick<ContractHypothesis, 'speciesId' | 'indication'>) => `${h.speciesId}-${h.indication?.meshId ?? 'none'}`;

/** The modern preparation is recorded in the evidence trail's profile reference: "<speciesId>:<faithful> vs <modern>". */
export function modernLabel(h: ContractHypothesis): string | null {
  const ref = h.evidenceTrail.find((e) => e.kind === 'profile')?.ref ?? '';
  const m = ref.match(/ vs (.+)$/);
  return m ? m[1] : null;
}

export function toHypothesis(h: ContractHypothesis, ctx: { index: ContractProfileIndex[]; audit: ContractAudit[]; profiles: ContractProfile[]; rankedOf: number }): Hypothesis {
  const entry = ctx.index.find((e) => e.speciesId === h.speciesId);
  const taxon = entry?.acceptedName ?? h.speciesId;
  const meshId = h.indication?.meshId;
  const recipeIds = [...new Set(ctx.audit.filter((r) => r.speciesId === h.speciesId && r.indication?.meshId === meshId).flatMap((r) => r.historicalRecipeIds))];
  const bySource = new Map<SourceWork, number>();
  for (const id of recipeIds) {
    const w = sourceWork(id.startsWith('pliny') ? 'pliny-nh' : id.split(':')[0]);
    bySource.set(w, (bySource.get(w) ?? 0) + 1);
  }
  const ml = modernLabel(h);
  const modernProfile = ml ? ctx.profiles.find((p) => p.preparationLabel === ml) : undefined;
  const gr = h.gapRanking ?? null;
  const studies = h.evidenceTrail.filter((e) => e.kind === 'study').map((e) => e.ref.replace(/^pmid:/, ''));
  const trailRecipes = h.evidenceTrail.filter((e) => e.kind === 'recipe').map((e) => e.ref);
  const trail: TrailStep[] = [
    { id: 'source', stage: 'source', title: `${recipeIds.length} historical recipe${recipeIds.length === 1 ? '' : 's'} for this use`,
      detail: `Indication as written: “${h.indicationAsWritten}”. Provisional extraction; every quote passed the verbatim check.`,
      evidence: 'provisional', refs: trailRecipes.map((id) => ({ label: `Recipe ${id}`, href: `/recipes/${recipeSlug(id)}/` })) },
    { id: 'name', stage: 'name', title: `Name resolved to ${taxon}`, detail: 'Resolution from GBIF / WFO evidence with heuristic weights; awaiting the 30-name scholarly check.',
      evidence: 'pending' },
    { id: 'preparation', stage: 'preparation', title: `Faithful preparation: ${h.faithfulPreparationText}`,
      detail: `Contract preparation key ${h.faithfulPreparation}.${h.caveats.some((c) => c.includes('correction')) ? ' Uses a logged extraction correction.' : ''}`,
      evidence: 'provisional' },
    { id: 'model', stage: 'model', title: `Predicted profile gap ${h.profileGap.low.toFixed(2)}–${h.profileGap.high.toFixed(2)} (median ${h.profileGap.value.toFixed(2)})`,
      detail: gr ? `${gr.rule}. ${gr.compoundsUsed} compounds used, ${gr.compoundsExcludedWide} excluded as too wide.` : 'Ranking inputs not recorded.',
      evidence: 'pending', heuristics: ['heat_sensitivity', 'acidity', 'filtration_carryover'],
      // Acceptance check 5: a toxic_reported plant never gets a Lab link. SITE: the v1 Compare link became a Lab link.
      refs: (() => {
        if (toxicityCategory(entry?.toxicityFlag ?? h.toxicityFlag) === 'toxic_reported') return [];
        const href = labHrefOfKey(taxon, h.faithfulPreparation);
        return href ? [{ label: 'Open the faithful preparation in the Lab', href }] : [];
      })() },
    { id: 'audit', stage: 'audit', title: 'No retrieved study prepared it faithfully',
      detail: `${studies.length} retrieved stud${studies.length === 1 ? 'y' : 'ies'} listed; coded by the rule-based extractor (heuristic; not independently validated).`,
      evidence: 'pending', refs: studies.map((p) => ({ label: `PMID ${p}`, href: `https://pubmed.ncbi.nlm.nih.gov/${p}/` })) },
    { id: 'toxicity', stage: 'toxicity', title: 'Toxicity entry', detail: neutralWording(h.toxicityNote) ?? 'No curated toxicity entry. Unknown is not evidence of safety.',
      evidence: 'provisional' },
  ];
  return {
    id: hypothesisId(h), rank: h.rank, rankedOf: ctx.rankedOf, rankByMedianGap: gr?.rankByMedianGap ?? null, taxon, speciesId: h.speciesId,
    indication: h.indication?.label ?? h.indicationAsWritten, indicationAsWritten: h.indicationAsWritten,
    faithful: { label: h.faithfulPreparationText, preparation: preparationOfKey(h.faithfulPreparation), key: h.faithfulPreparation },
    // The modern preparation is what modern studies used, so it is always the modern family (water can be either).
    modern: ml ? { label: ml, preparation: { ...(modernProfile ? preparationOfKey(modernProfile.preparationKey) : { vehicle: 'unknown', filtered: null }), family: 'modern' } } : null,
    gap: { low: h.profileGap.low, high: h.profileGap.high, point: h.profileGap.value },
    gapThreshold: gr?.gapThreshold ?? null, pGapAboveThreshold: gr?.pGapAboveThreshold ?? null,
    compoundsUsed: gr?.compoundsUsed ?? null, compoundsExcludedWide: gr?.compoundsExcludedWide ?? null, rule: gr?.rule ?? null,
    attestation: [...bySource.entries()].map(([source, recipes]) => ({ source, recipes })), attestationCount: h.attestationCount,
    caveats: h.caveats, toxicity: toxicityFromIndex(entry, h.toxicityFlag, h.toxicityNote), evidence: 'provisional', trail,
  };
}
