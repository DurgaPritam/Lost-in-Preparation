import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { RecipePage } from '@/features/atlas/RecipePage';
import { getRecipe, recipeSlugs } from '@/lib/data/site';

export const dynamicParams = false;
export function generateStaticParams() {
  return recipeSlugs().map((id) => ({ id }));
}
export function generateMetadata({ params }: { params: { id: string } }): Metadata {
  const r = getRecipe(params.id);
  return { title: r ? `${r.recipe.name.historicalName} · recipe` : 'Recipe' };
}
export default function Page({ params }: { params: { id: string } }) {
  const r = getRecipe(params.id);
  if (!r) notFound();
  return <RecipePage {...r} />;
}
