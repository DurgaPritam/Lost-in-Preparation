import { Redirect } from '@/features/shared/Redirect';
import { getHypotheses } from '@/lib/data/site';

export const dynamicParams = false;
export function generateStaticParams() {
  return getHypotheses().map((h) => ({ id: h.id }));
}
export const metadata = { title: 'Moved', robots: { index: false } };
export default function Page({ params }: { params: { id: string } }) {
  return <Redirect to={`/hypotheses/#${params.id}`} label="the ranked hypotheses" />;
}
