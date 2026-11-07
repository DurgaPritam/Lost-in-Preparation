import { Redirect } from '@/features/shared/Redirect';

export const metadata = { title: 'Moved', robots: { index: false } };
export default function Page() {
  return <Redirect to="/docs/#downloads" label="Downloads in Methods & data" />;
}
