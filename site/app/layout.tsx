import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: { default: 'Lost in Preparation', template: '%s · Lost in Preparation' },
  description: 'Historical herbal recipes re-read for how they were prepared, with every uncertainty shown. A research tool; no medical claims.',
};
export const viewport: Viewport = { width: 'device-width', initialScale: 1 };

/** The Drawer makes #root inert while a dialog is open (design Phase 4), so the app renders inside #root. */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div id="root">{children}</div>
      </body>
    </html>
  );
}
