import type { ReactNode } from 'react';
import Link from '@/components/base/Link';
import { ROUTES, type Route } from '@/lib/ia';
import { cx } from '@/lib/data/format';

/**
 * App shell: a quiet left rail (stacks above content below 900px), a running
 * header with the project name in serif, and a persistent footer line that
 * restates the scope: research tool, no medical claims.
 * The nav is a plain list of links — no icons, no badges competing with the
 * honesty markers in the content.
 */
export interface AppShellProps {
  current: Route['id'];
  /** Overrides the route label as the page's h1 (Home uses a statement, not "Home"). */
  title?: string;
  /** SITE: overrides the route question as the subtitle (the case-study page is a child of Hypotheses). */
  question?: string;
  children: ReactNode;
  onNavigate?: (path: string) => void;
  headerRight?: ReactNode;
}

export function AppShell({ current, title, question, children, onNavigate, headerRight }: AppShellProps) {
  const route = ROUTES.find((r) => r.id === current)!;
  return (
    <div className="min-h-screen bg-paper text-ink">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-surface focus:p-2">
        Skip to content
      </a>
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-content flex-wrap items-center justify-between gap-4 px-4 py-3 md:px-8">
          <div className="flex items-baseline gap-3">
            <span className="font-serif text-xl font-medium">Lost in Preparation</span>
            <span className="hidden text-sm text-ink-subtle sm:inline">EthnoHack 2026 · Traditional Knowledge Mining</span>
          </div>
          {headerRight}
        </div>
      </header>
      <div className="mx-auto flex max-w-content flex-col gap-8 px-4 py-6 md:flex-row md:px-8">
        <nav aria-label="Primary" className="md:w-nav md:shrink-0">
          <ul className="m-0 flex list-none flex-row flex-wrap gap-1 p-0 md:flex-col">
            {ROUTES.map((r) => {
              const on = r.id === current;
              return (
                <li key={r.id}>
                  {/* SITE: next/link (client-side navigation in the static export, prefetch off: components/base/Link) instead of a plain anchor. */}
                  <Link
                    href={r.path}
                    aria-current={on ? 'page' : undefined}
                    onClick={onNavigate ? (e) => { e.preventDefault(); onNavigate(r.path); } : undefined}
                    className={cx(
                      'flex h-10 items-center rounded px-3 text-base',
                      on ? 'bg-sunken font-semibold text-ink' : 'text-ink-muted hover:bg-sunken hover:text-ink',
                    )}
                  >
                    {r.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        <main id="main" className="flex min-w-0 flex-1 flex-col gap-6">
          <div className="flex flex-col gap-1">
            <h1 className="m-0 font-serif text-3xl font-medium">{title ?? route.label}</h1>
            <p className="m-0 max-w-prose text-md text-ink-muted">{question ?? route.question}</p>
          </div>
          {children}
        </main>
      </div>
      <footer className="border-t border-border">
        <p className="mx-auto m-0 max-w-content px-4 py-4 text-sm text-ink-subtle md:px-8">
          A research tool that generates hypotheses for re-testing. It makes no medical claims and gives no guidance on preparing or taking any plant.
        </p>
      </footer>
    </div>
  );
}
