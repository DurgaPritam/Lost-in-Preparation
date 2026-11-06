import type { Metadata } from 'next';
import { Hypotheses } from '@/features/hypotheses/Hypotheses';
import { confidences, getHypotheses } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Hypotheses' };
export default function Page() {
  const hs = getHypotheses();
  return <Hypotheses items={hs} confidences={confidences()} rule={hs[0]?.rule ?? null} />;
}
