import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { HypothesisPage } from '@/features/hypotheses/Hypotheses';
import { confidences, getHypothesis, hypothesisIds } from '@/lib/data/site';

export const dynamicParams = false;
export function generateStaticParams() {
  return hypothesisIds().map((id) => ({ id }));
}
export function generateMetadata({ params }: { params: { id: string } }): Metadata {
  const h = getHypothesis(params.id);
  return { title: h ? `${h.indication} · ${h.taxon}` : 'Hypothesis' };
}
export default function Page({ params }: { params: { id: string } }) {
  const h = getHypothesis(params.id);
  if (!h) notFound();
  return <HypothesisPage h={h} confidences={confidences()} />;
}
