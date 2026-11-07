import type { Metadata } from 'next';
import { EvidenceGap } from '@/features/gap/EvidenceGap';
import { getGap } from '@/lib/data/site';

export const metadata: Metadata = { title: 'The evidence gap' };
export default function Page() {
  const { gap, audit } = getGap();
  return <EvidenceGap gap={gap} audit={{ v2: audit.v2, auditV2: audit.auditV2, confidences: audit.confidences }} />;
}
