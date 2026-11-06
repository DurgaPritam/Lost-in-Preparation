import { cx } from '../../lib/format';

/**
 * Filter chips are real checkboxes inside a fieldset (keyboard + screen
 * reader for free). Every group shows counts, and any facet that can be
 * unknown MUST include an "Unknown" option — filtering never hides unknowns
 * silently. `FilterSummary` states what is hidden.
 */
export interface FilterOption {
  value: string;
  label: string;
  count: number;
}
export interface FilterGroupProps {
  legend: string;
  options: FilterOption[];
  selected: string[];
  onChange: (next: string[]) => void;
}

export function FilterGroup({ legend, options, selected, onChange }: FilterGroupProps) {
  const toggle = (v: string) =>
    onChange(selected.includes(v) ? selected.filter((s) => s !== v) : [...selected, v]);
  return (
    <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
      <legend className="mb-2 text-xs font-medium text-ink-subtle small-caps">{legend}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((o) => {
          const on = selected.includes(o.value);
          const unknown = o.value === 'unknown';
          return (
            <label
              key={o.value}
              className={cx(
                'inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-full border px-3 text-sm',
                'has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-focus',
                on ? 'border-ink bg-ink text-paper' : 'border-border-strong bg-surface text-ink hover:bg-sunken',
                unknown && !on && 'border-dashed text-unk-fg',
              )}
            >
              <input type="checkbox" className="sr-only" checked={on} onChange={() => toggle(o.value)} />
              {o.label}
              <span className={cx('num', on ? 'text-paper' : 'text-ink-subtle')}>{o.count}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export function FilterSummary({ shown, total, onClear }: { shown: number; total: number; onClear: () => void }) {
  const hidden = total - shown;
  return (
    <p className="m-0 flex flex-wrap items-center gap-2 text-sm text-ink-muted" aria-live="polite">
      Showing <span className="num font-medium text-ink">{shown}</span> of <span className="num">{total}</span>
      {hidden > 0 && (
        <>
          · {hidden} hidden by filters
          <button type="button" onClick={onClear} className="text-ink underline underline-offset-2">
            Clear filters
          </button>
        </>
      )}
    </p>
  );
}
