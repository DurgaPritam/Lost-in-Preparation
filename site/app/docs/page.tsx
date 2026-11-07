import type { Metadata } from 'next';
import { Docs } from '@/features/docs/Docs';
import { getDocs } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Methods & data' };
export default function Page() {
  return <Docs {...getDocs()} />;
}
