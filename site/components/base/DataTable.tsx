'use client';

import { useMemo, useState, type ReactNode } from 'react';
import { cx } from '@/lib/data/format';
import { IconSort } from '../icons';

/**
 * Journal-style table: hairline rules, no zebra, no vertical lines, sticky
 * header on sunken ground, numbers right-aligned in tabular mono.
 * Sorting puts null / Unknown LAST in both directions — Unknown is never
 * sorted as zero. Wraps in a horizontal scroll box at narrow widths.
 */
export interface Column<R> {
  key: string;
  header: string;
  /** Short explanation shown under the header (e.g. "range, 0–1"). */
  hint?: string;
  numeric?: boolean;
  /** Sort key; return null for unknown. Omit to make the column unsortable. */
  sortValue?: (row: R) => number | string | null;
  render: (row: R) => ReactNode;
}
export interface DataTableProps<R> {
  caption: string;
  columns: Column<R>[];
  rows: R[];
  rowKey: (row: R) => string;
  onRowClick?: (row: R) => void;
  dense?: boolean;
  /** Below 900px, render rows as labelled cards instead of a scrolling table. Default true. */
  stackOnMobile?: boolean;
}

export function DataTable<R>({ caption, columns, rows, rowKey, onRowClick, dense, stackOnMobile = true }: DataTableProps<R>) {
  const [sort, setSort] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null);

  const sorted = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sortValue) return rows;
    const sv = col.sortValue;
    return [...rows].sort((a, b) => {
      const x = sv(a), y = sv(b);
      if (x == null && y == null) return 0;
      if (x == null) return 1; // unknown last, always
      if (y == null) return -1;
      const c = x < y ? -1 : x > y ? 1 : 0;
      return sort.dir === 'asc' ? c : -c;
    });
  }, [rows, columns, sort]);

  const toggle = (key: string) =>
    setSort((s) => (s?.key !== key ? { key, dir: 'desc' } : s.dir === 'desc' ? { key, dir: 'asc' } : null));

  const pad = dense ? 'px-3 py-1.5' : 'px-3 py-2.5';
  const [first, ...rest] = columns;

  return (
    <>
    {stackOnMobile && (
      /* Phase 4: below 900px each row becomes a labelled card, so no column
         (often the evidence column) is hidden off-screen in a scroll box. */
      <div className="flex flex-col gap-2 md:hidden">
        <p className="m-0 text-sm text-ink-muted">{caption}</p>
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {sorted.map((r) => (
            <li
              key={rowKey(r)}
              onClick={onRowClick ? () => onRowClick(r) : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={onRowClick ? (e) => {
                if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onRowClick(r); }
              } : undefined}
              className={cx('flex flex-col gap-2 rounded border border-border bg-surface p-4', onRowClick && 'cursor-pointer')}
            >
              <div className="text-base">{first.render(r)}</div>
              <dl className="m-0 grid grid-cols-1 gap-2">
                {rest.map((c) => (
                  <div key={c.key} className="flex flex-col gap-0.5">
                    <dt className="small-caps text-xs text-ink-subtle">{c.header}{c.hint ? ` · ${c.hint}` : ''}</dt>
                    <dd className={cx('m-0 text-base', c.numeric && 'num font-mono')}>{c.render(r)}</dd>
                  </div>
                ))}
              </dl>
            </li>
          ))}
        </ul>
      </div>
    )}
    <div tabIndex={0} role="region" aria-label={`${caption} (scrollable)`} className={cx('w-full overflow-x-auto rounded border border-border bg-surface', stackOnMobile && 'hidden md:block')}>
      <table className="w-full border-collapse text-base">
        <caption className="px-3 py-2 text-left text-sm text-ink-muted">{caption}</caption>
        <thead className="sticky top-0 bg-sunken">
          <tr>
            {columns.map((c) => {
              const dir = sort?.key === c.key ? sort.dir : 'none';
              return (
                <th
                  key={c.key}
                  scope="col"
                  aria-sort={dir === 'asc' ? 'ascending' : dir === 'desc' ? 'descending' : undefined}
                  className={cx('border-b border-border-strong text-sm font-medium text-ink', pad, c.numeric ? 'text-right' : 'text-left')}
                >
                  {c.sortValue ? (
                    <button type="button" onClick={() => toggle(c.key)} className="inline-flex items-center gap-1 hover:underline">
                      {c.header}
                      <IconSort dir={dir} size={12} />
                    </button>
                  ) : (
                    c.header
                  )}
                  {c.hint && <span className="block text-xs font-normal text-ink-subtle">{c.hint}</span>}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => (
            <tr
              key={rowKey(r)}
              onClick={onRowClick ? () => onRowClick(r) : undefined}
              /* Phase 4: clickable rows were mouse-only. They are now focusable and open on Enter/Space. */
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={onRowClick ? (e) => {
                if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onRowClick(r); }
              } : undefined}
              className={cx('border-b border-border last:border-b-0', onRowClick && 'cursor-pointer hover:bg-sunken focus-visible:bg-sunken')}
            >
              {columns.map((c) => (
                <td key={c.key} className={cx(pad, 'align-top', c.numeric && 'num text-right font-mono')}>
                  {c.render(r)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </>
  );
}
