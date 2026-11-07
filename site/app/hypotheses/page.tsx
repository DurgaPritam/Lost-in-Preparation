import type { Metadata } from 'next';
import { Hypotheses } from '@/features/results/Hypotheses';
import { getHypotheses } from '@/lib/data/site';
import { HEURISTICS } from '@/lib/data/heuristics';

export const metadata: Metadata = { title: 'Ranked hypotheses' };
export default function Page() {
  return <Hypotheses hypotheses={getHypotheses()} heuristics={HEURISTICS} />;
}
