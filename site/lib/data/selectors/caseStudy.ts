/** case_studies.json (+ the corrected recipes) → the Liquorice case-study page. */
import type { RecipeCorrectionView } from '../../types';
import type { ContractCase, ContractRecipe } from '../load';
import { sourceWork } from './common';
import { recipeSlug } from './recipes';

export interface CaseView {
  study: ContractCase;
  corrections: (RecipeCorrectionView & { recipeId: string; href: string; source: ReturnType<typeof sourceWork>; quote: string })[];
}
export function caseView(c: ContractCase, recipes: ContractRecipe[]): CaseView {
  const by = new Map(recipes.map((r) => [r.id, r]));
  const corrections = c.correctedRecipeIds.flatMap((id) => {
    const r = by.get(id);
    return (r?.corrections ?? []).map((x) => ({ ...x, from: x.from, recipeId: id, href: `/recipes/${recipeSlug(id)}/`, source: sourceWork(r!.sourceId),
                                             quote: r!.evidence.recipe?.[0]?.quote ?? '' }));
  });
  return { study: c, corrections };
}
