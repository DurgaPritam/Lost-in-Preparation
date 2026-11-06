import type { Metadata } from 'next';
import { RecipeExplorer } from '@/features/recipes/RecipeExplorer';
import { RECIPE_PAGE } from '@/lib/data/selectors/recipeFacets';
import { getRecipeExplorer } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Recipe explorer' };
export default function Page() {
  return <RecipeExplorer {...getRecipeExplorer(RECIPE_PAGE)} />;
}
