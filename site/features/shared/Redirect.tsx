'use client';

import { useEffect } from 'react';
import { SiteShell } from '@/components/layout/SiteShell';
import { EmptyState } from '@/components/base/States';
import { LinkButton } from '@/components/base/Button';

/** SITE: v1 addresses forward to their v2 pages (design v2 §4). A static export cannot send a server redirect, so the
 *  page replaces the location and also shows the link; vercel.json adds real 301s on the host. */
export function Redirect({ to, label }: { to: string; label: string }) {
  useEffect(() => { window.location.replace(to + window.location.search + window.location.hash); }, [to]);
  return (
    <SiteShell current="landing">
      <EmptyState title="This page has moved" body={`It is now ${label}.`} action={<LinkButton href={to}>Go to {label}</LinkButton>} />
    </SiteShell>
  );
}
