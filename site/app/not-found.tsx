import { SiteShell } from '@/components/layout/SiteShell';
import { EmptyState } from '@/components/base/States';
import { LinkButton } from '@/components/base/Button';

export default function NotFound() {
  return (
    <SiteShell current="landing">
      <EmptyState title="No page at this address" body="The link may be out of date." action={<LinkButton href="/">Back to the start</LinkButton>} />
    </SiteShell>
  );
}
