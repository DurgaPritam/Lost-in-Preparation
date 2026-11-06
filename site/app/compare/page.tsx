import type { Metadata } from 'next';
import { Compare } from '@/features/compare/Compare';
import { confidences, getCompareIndex } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Compare preparations' };
export default function Page() {
  const idx = getCompareIndex();
  return <Compare species={idx.species} defaults={idx.default} confidences={confidences()} />;
}
