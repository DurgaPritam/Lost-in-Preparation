import { useEffect, useId, useState, type MouseEvent, type ReactNode } from 'react';
import { ROUTES, type Route } from '../../ia';
import { cx } from '../../lib/format';
import { IconMenu, IconMoon, IconSun } from '../icons';

/**
 * Theme: Herbarium (light) and Nocturne (dark) are one product with two
 * modes. Default = system preference; the toggle stores the choice
 * (localStorage, wrapped in try/catch) and sets <html data-theme>.
 */
type Theme = 'light' | 'dark';
const KEY = 'lip-theme';
export function currentTheme(): Theme {
  const set = document.documentElement.dataset.theme;
  if (set === 'light' || set === 'dark') return set;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
export function applyStoredTheme() {
  try { const t = localStorage.getItem(KEY); if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t; } catch { /* storage unavailable */ }
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => (typeof document === 'undefined' ? 'light' : currentTheme()));
  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
  const next: Theme = theme === 'light' ? 'dark' : 'light';
  return (
    <button
      type="button"
      onClick={() => { setTheme(next); try { localStorage.setItem(KEY, next); } catch { /* ignore */ } }}
      aria-label={`Switch to ${next === 'dark' ? 'Nocturne (dark)' : 'Herbarium (light)'} theme`}
      className="inline-flex h-10 items-center gap-2 rounded-full border border-border-strong px-3 text-sm font-medium text-ink hover:bg-sunken"
    >
      {theme === 'light' ? <IconMoon /> : <IconSun />}
      <span className="hidden sm:inline">{theme === 'light' ? 'Nocturne' : 'Herbarium'}</span>
    </button>
  );
}

export interface SiteShellProps {
  current: Route['id'];
  children: ReactNode;
  onNavigate?: (path: string) => void;
  /** Full-bleed pages (landing, case study) manage their own width. */
  bleed?: boolean;
}

export function SiteShell({ current, children, onNavigate, bleed }: SiteShellProps) {
  const [menu, setMenu] = useState(false);
  const menuId = useId();
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); setMenu(false); onNavigate(path); } };
  const nav = ROUTES.filter((r) => r.nav);
  return (
    <div className="min-h-screen bg-paper text-ink">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:p-2">Skip to content</a>
      <header className="sticky top-0 z-30 border-b border-border bg-paper">
        <div className="mx-auto flex max-w-content items-center justify-between gap-4 px-4 py-3 md:px-8">
          <a href="/" onClick={go('/')} className="flex items-baseline gap-2 text-ink no-underline">
            <span className="font-display text-xl">Lost <i className="text-brand">in</i> Preparation</span>
          </a>
          <nav aria-label="Primary" className="hidden lg:block">
            <ul className="m-0 flex list-none items-center gap-1 p-0">
              {nav.map((r) => (
                <li key={r.id}>
                  <a
                    href={r.path}
                    onClick={go(r.path)}
                    aria-current={r.id === current ? 'page' : undefined}
                    className={cx('inline-flex h-10 items-center rounded-full px-3 text-sm font-medium no-underline', r.id === current ? 'bg-sunken text-ink' : 'text-ink-muted hover:text-ink')}
                  >
                    {r.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button type="button" aria-expanded={menu} aria-controls={menuId} onClick={() => setMenu((m) => !m)} aria-label="Menu" className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border-strong lg:hidden">
              <IconMenu />
            </button>
          </div>
        </div>
        {menu && (
          <nav id={menuId} aria-label="Primary" className="fade-in border-t border-border lg:hidden">
            <ul className="m-0 grid list-none grid-cols-1 gap-1 p-3 sm:grid-cols-2">
              {nav.map((r) => (
                <li key={r.id}>
                  <a href={r.path} onClick={go(r.path)} aria-current={r.id === current ? 'page' : undefined} className={cx('flex h-11 items-center rounded-md px-3 text-base no-underline', r.id === current ? 'bg-sunken font-semibold text-ink' : 'text-ink-muted')}>
                    {r.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </header>
      <main id="main" className={cx(!bleed && 'mx-auto flex max-w-content flex-col gap-10 px-4 py-8 md:px-8 md:py-12')}>
        {children}
      </main>
      <footer className="mt-16 border-t border-border">
        <div className="mx-auto flex max-w-content flex-col gap-2 px-4 py-8 text-sm text-ink-subtle md:flex-row md:items-center md:justify-between md:px-8">
          <span>A research tool that generates hypotheses for re-testing. No medical claims; no guidance on preparing or taking any plant.</span>
          <a href="/docs" onClick={go('/docs')} className="text-ink-muted underline underline-offset-4">Methods &amp; data</a>
        </div>
      </footer>
    </div>
  );
}

/** Page header used by every non-landing page. */
export function PageHeader({ eyebrow, title, lead, children }: { eyebrow?: string; title: ReactNode; lead?: ReactNode; children?: ReactNode }) {
  return (
    <div className="flex flex-col gap-3">
      {eyebrow && <span className="eyebrow text-brand">{eyebrow}</span>}
      <h1 className="m-0 font-display text-3xl text-ink md:text-4xl">{title}</h1>
      {lead && <p className="m-0 max-w-prose text-md text-ink-muted">{lead}</p>}
      {children}
    </div>
  );
}
