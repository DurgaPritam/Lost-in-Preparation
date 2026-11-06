import type { Metadata } from 'next';
import { Audit } from '@/features/audit/Audit';
import { getAudit } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Audit' };
export default function Page() {
  const a = getAudit();
  return <Audit v1={{ id: 'v1', ...a.v1 }} v2={{ id: 'v2', ...a.v2 }} headline={a.headline} auditV2={a.auditV2} confidences={a.confidences} />;
}
