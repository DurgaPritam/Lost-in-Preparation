import Link from '@/components/base/Link';
import { AppShell } from '@/components/layout/AppShell';
import { EmptyState } from '@/components/base/States';

export default function NotFound() {
  return (
    <AppShell current="home" title="Page not found">
      <EmptyState title="Nothing at this address" body="The link may be out of date." action={<Link href="/" className="text-ink underline underline-offset-2">Go to Home</Link>} />
    </AppShell>
  );
}
