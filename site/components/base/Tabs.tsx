'use client';

import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react';
import { cx } from '@/lib/data/format';

/**
 * WAI-ARIA tabs with roving tabindex (Left/Right/Home/End). Selected tab
 * uses a 2px ink underline — weight, not colour, marks selection.
 * Optional `count` renders e.g. "Disputed (14)"; counts include Unknown.
 */
export interface TabItem {
  id: string;
  label: string;
  count?: number;
  panel: ReactNode;
}
export interface TabsProps {
  items: TabItem[];
  value: string;
  onChange: (id: string) => void;
  label: string;
}

export function Tabs({ items, value, onChange, label }: TabsProps) {
  const base = useId();
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const idx = Math.max(0, items.findIndex((t) => t.id === value));

  const onKey = (e: KeyboardEvent) => {
    const last = items.length - 1;
    const next =
      e.key === 'ArrowRight' ? (idx === last ? 0 : idx + 1)
      : e.key === 'ArrowLeft' ? (idx === 0 ? last : idx - 1)
      : e.key === 'Home' ? 0
      : e.key === 'End' ? last
      : null;
    if (next == null) return;
    e.preventDefault();
    onChange(items[next].id);
    refs.current[next]?.focus();
  };

  return (
    <div className="flex flex-col gap-4">
      <div role="tablist" aria-label={label} onKeyDown={onKey} className="flex flex-wrap gap-1 border-b border-border">
        {items.map((t, i) => {
          const sel = i === idx;
          return (
            <button
              key={t.id}
              ref={(el) => { refs.current[i] = el; }}
              role="tab"
              id={`${base}-tab-${t.id}`}
              aria-selected={sel}
              aria-controls={`${base}-panel-${t.id}`}
              tabIndex={sel ? 0 : -1}
              onClick={() => onChange(t.id)}
              className={cx(
                '-mb-px h-10 border-b-2 px-3 text-base',
                sel ? 'border-ink font-semibold text-ink' : 'border-transparent text-ink-muted hover:text-ink',
              )}
            >
              {t.label}
              {t.count != null && <span className="num ml-1 text-ink-subtle">({t.count})</span>}
            </button>
          );
        })}
      </div>
      {items.map((t, i) => (
        <div
          key={t.id}
          role="tabpanel"
          id={`${base}-panel-${t.id}`}
          aria-labelledby={`${base}-tab-${t.id}`}
          hidden={i !== idx}
          tabIndex={0}
        >
          {t.panel}
        </div>
      ))}
    </div>
  );
}
