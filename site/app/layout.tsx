import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import { THEME_BOOT_SCRIPT } from '@/components/layout/SiteShell';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: { default: 'Lost in Preparation', template: '%s · Lost in Preparation' },
  description: 'Historical remedies were recipes, not just plants. See what each preparation would extract, with the uncertainty left in. A research tool; no medical claims.',
};
/** SITE: the active theme's display and body faces are preloaded (decided after the theme script, so a dark reader
 *  never downloads the light faces first). With the metric-matched fallbacks this keeps the first screen from shifting. */
const PRELOAD: Record<'light' | 'dark', string[]> = {
  light: ['fraunces-latin-opsz-normal', 'instrument-sans-latin-400-normal', 'instrument-sans-latin-600-normal'],
  dark: ['instrument-serif-latin-400-normal', 'hanken-grotesk-latin-400-normal', 'hanken-grotesk-latin-600-normal'],
};
const PRELOAD_SCRIPT = `try{var t=document.documentElement.dataset.theme;var d=t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches;(${JSON.stringify(PRELOAD)})[d?'dark':'light'].forEach(function(f){var l=document.createElement('link');l.rel='preload';l.as='font';l.type='font/woff2';l.crossOrigin='anonymous';l.href='/fonts/'+f+'.woff2';document.head.appendChild(l)})}catch(e){}`;
export const viewport: Viewport = { width: 'device-width', initialScale: 1 };

/** The Drawer makes #root inert while a dialog is open (design Phase 4), so the app renders inside #root. The theme
 *  script runs before first paint: the stored choice (or ?theme=light|dark) wins, otherwise the system preference. */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT_SCRIPT }} />
        <script dangerouslySetInnerHTML={{ __html: PRELOAD_SCRIPT }} />
      </head>
      <body>
        <div id="root">{children}</div>
      </body>
    </html>
  );
}
