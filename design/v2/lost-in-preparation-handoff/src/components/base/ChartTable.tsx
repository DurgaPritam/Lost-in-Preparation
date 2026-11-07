import type { ReactNode } from 'react';

/**
 * Data-table fallback for a chart (Phase 4). Every chart-like view (range
 * bars, match bars, interval charts) gets one, placed right after it: a
 * native <details> disclosure, so it is keyboard- and screen-reader-operable
 * with no script, containing a plain table of exactly the values drawn.
 * Unknown cells must be passed as <UnknownValue/>, never as blanks or zeros.
 */
export interface ChartTableProps {
  caption: string;
  headers: string[];
  rows: ReactNode[][];
  /** Visible summary text; defaults to "View as table". */
  label?: string;
  /** Column indexes to right-align (numbers). */
  numeric?: number[];
}

export function ChartTable({ caption, headers, rows, label = 'View as table', numeric = [] }: ChartTableProps) {
  return (
    <details className="group rounded border border-border bg-surface">
      <summary className="flex min-h-10 cursor-pointer items-center px-3 text-sm font-medium text-ink">
        <span aria-hidden className="mr-2 font-mono text-ink-muted group-open:hidden">+</span>
        <span aria-hidden className="mr-2 hidden font-mono text-ink-muted group-open:inline">−</span>
        {label}
      </summary>
      <div className="overflow-x-auto border-t border-border" tabIndex={0} role="region" aria-label={`${caption} (scrollable)`}>
        <table className="w-full border-collapse text-sm">
          <caption className="px-3 py-2 text-left text-xs text-ink-subtle">{caption}</caption>
          <thead className="bg-sunken">
            <tr>
              {headers.map((h, i) => (
                <th key={h} scope="col" className={`border-b border-border-strong px-3 py-2 font-medium ${numeric.includes(i) ? 'text-right' : 'text-left'}`}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, ri) => (
              <tr key={ri} className="border-b border-border last:border-b-0">
                {r.map((c, ci) => (
                  ci === 0
                    ? <th key={ci} scope="row" className="px-3 py-2 text-left font-normal">{c}</th>
                    : <td key={ci} className={`px-3 py-2 ${numeric.includes(ci) ? 'num text-right font-mono' : ''}`}>{c}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
