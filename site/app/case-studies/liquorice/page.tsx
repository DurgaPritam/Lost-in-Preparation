import { Redirect } from '@/features/shared/Redirect';

export const metadata = { title: 'Moved', robots: { index: false } };
export default function Page() {
  return <Redirect to="/case/liquorice/" label="the liquorice case study" />;
}
