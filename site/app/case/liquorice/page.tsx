import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { CaseStudy } from '@/features/case/CaseStudy';
import { getCase } from '@/lib/data/site';
import { HEURISTICS } from '@/lib/data/heuristics';

export const metadata: Metadata = { title: 'Case study: liquorice' };
export default function Page() {
  const c = getCase();
  if (!c) notFound();
  return <CaseStudy {...c} heat={HEURISTICS.find((h) => h.id === 'heat_sensitivity')} />;
}
