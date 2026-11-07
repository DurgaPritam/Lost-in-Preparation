import { Redirect } from '@/features/shared/Redirect';

export const metadata = { title: 'Moved', robots: { index: false } };
export default function Page() {
  return <Redirect to="/planner/" label="the Lab Planner" />;
}
