import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { RecipeDetail } from '@/features/recipes/RecipeDetail';
import { getCompareIndex, confidences, getRecipe, recipeSlugs } from '@/lib/data/site';

export const dynamicParams = false;
export function generateStaticParams() {
  return recipeSlugs().map((id) => ({ id }));
}
export function generateMetadata({ params }: { params: { id: string } }): Metadata {
  const r = getRecipe(params.id);
  return { title: r ? `“${r.name.historicalName}” · recipe` : 'Recipe' };
}
export default function Page({ params }: { params: { id: string } }) {
  const r = getRecipe(params.id);
  if (!r) notFound();
  const profiled = Object.fromEntries(getCompareIndex().species.map((s) => [s.taxon, s.speciesId]));
  return <RecipeDetail recipe={r} confidences={confidences()} profiled={profiled} />;
}
