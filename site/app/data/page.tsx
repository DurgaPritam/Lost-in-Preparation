import type { Metadata } from 'next';
import { DataLicences } from '@/features/data/DataLicences';
import { CONTRACT_VERSION } from '@/lib/data/generated';
import { getSources } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Data & licences' };
export default function Page() {
  return <DataLicences data={getSources()} contractVersion={CONTRACT_VERSION} />;
}
