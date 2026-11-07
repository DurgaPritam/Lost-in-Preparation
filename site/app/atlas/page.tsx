import type { Metadata } from 'next';
import { Atlas } from '@/features/atlas/Atlas';
import { getAtlas } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Recipe Atlas' };
export default function Page() {
  return <Atlas {...getAtlas()} />;
}
