import type { Metadata } from 'next';
import { Impact } from '@/features/impact/Impact';
import { getImpact } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Impact & ethics' };
export default function Page() {
  return <Impact {...getImpact()} />;
}
