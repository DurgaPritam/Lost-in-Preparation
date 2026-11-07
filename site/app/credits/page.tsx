import type { Metadata } from 'next';
import { Credits } from '@/features/credits/Credits';
import { getCredits } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Credits' };
export default function Page() {
  return <Credits {...getCredits()} />;
}
