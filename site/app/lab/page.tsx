import type { Metadata } from 'next';
import { Lab } from '@/features/lab/Lab';
import { getLab } from '@/lib/data/site';
import { loadEngineModel } from '@/lib/data/load';

export const metadata: Metadata = { title: 'Preparation Lab' };
export default function Page() {
  return <Lab {...getLab()} model={loadEngineModel()} />;
}
