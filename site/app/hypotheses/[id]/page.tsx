import { Redirect } from '@/features/shared/Redirect';
import { getHypotheses } from '@/lib/data/site';

export const dynamicParams = false;
export function generateStaticParams() {
  return getHypotheses().map((h) => ({ id: h.id }));
}
export const metadata = { title: 'Moved', robots: { index: false } };
export default function Page() {
  return <Redirect to="/planner/" label="the Lab Planner" />;
}
