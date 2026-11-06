import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: { default: 'Lost in Preparation', template: '%s · Lost in Preparation' },
  description: 'Historical herbal recipes re-read for how they were prepared, with every uncertainty shown. A research tool; no medical claims.',
};
export const viewport: Viewport = { width: 'device-width', initialScale: 1 };

/** SITE: the two body-text faces are preloaded, so they usually arrive with the stylesheet, before first paint, and no
 *  text re-wraps when they swap in (layout shift). Other faces load from styles/fonts.css when a page needs them, with
 *  metric-matched fallbacks (styles/font-fallbacks.css) while they load. */
const PRELOAD_FONTS = ['ibm-plex-sans-latin-400-normal', 'ibm-plex-sans-latin-500-normal'];

/** The Drawer makes #root inert while a dialog is open (design Phase 4), so the app renders inside #root. */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        {PRELOAD_FONTS.map((f) => <link key={f} rel="preload" href={`/fonts/${f}.woff2`} as="font" type="font/woff2" crossOrigin="anonymous" />)}
      </head>
      <body>
        <div id="root">{children}</div>
      </body>
    </html>
  );
}
