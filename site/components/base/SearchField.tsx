'use client';

import { useId } from 'react';
import { IconClose, IconSearch } from '../icons';

/**
 * Search across historical names, modern taxa and compounds. The visible
 * label is required (no placeholder-as-label). Hint text teaches that
 * historical spellings are matched ("Wormwood", "absinthium").
 */
export interface SearchFieldProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  hint?: string;
  placeholder?: string;
}

export function SearchField({ label, value, onChange, hint, placeholder }: SearchFieldProps) {
  const id = useId();
  const hintId = `${id}-hint`;
  return (
    <div className="flex w-full flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-ink">{label}</label>
      <div className="relative flex items-center">
        <IconSearch className="pointer-events-none absolute left-3 text-ink-muted" />
        <input
          id={id}
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-describedby={hint ? hintId : undefined}
          className="h-10 w-full rounded border border-border-strong bg-surface pl-10 pr-10 text-base text-ink placeholder:text-ink-subtle"
        />
        {value && (
          <button
            type="button"
            onClick={() => onChange('')}
            aria-label="Clear search"
            className="absolute right-1 inline-flex h-8 w-8 items-center justify-center rounded text-ink-muted hover:bg-sunken"
          >
            <IconClose />
          </button>
        )}
      </div>
      {hint && <p id={hintId} className="m-0 text-xs text-ink-subtle">{hint}</p>}
    </div>
  );
}
