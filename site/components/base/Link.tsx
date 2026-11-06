/** SITE: next/link with prefetch off. Prefetching every in-view link pulled ~1 MB of other pages' payloads on each load
 *  (Lighthouse performance); navigation stays client-side. */
import NextLink from 'next/link';
import type { ComponentProps } from 'react';

export default function Link(props: ComponentProps<typeof NextLink>) {
  return <NextLink prefetch={false} {...props} />;
}
