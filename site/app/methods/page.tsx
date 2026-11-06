import type { Metadata } from 'next';
import { Methods } from '@/features/methods/Methods';
import { getValidation } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Methods & validation' };
export default function Page() {
  return <Methods data={getValidation()} />;
}
