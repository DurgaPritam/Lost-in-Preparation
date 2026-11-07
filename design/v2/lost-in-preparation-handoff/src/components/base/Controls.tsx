import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react';
import { cx } from '../../lib/format';

/**
 * Lab controls.
 * SegmentedControl — a WAI-ARIA radiogroup: one tab stop, arrow keys move
 *   and select, Home/End jump. Selection = filled ink pill (light) / saffron
 *   pill (dark comes from the same tokens: brand on brand-on).
 * Switch — role="switch" button with a visible label and state text.
 */
export interface SegOption<T extends string> { value: T; label: string; hint?: string; disabled?: boolean }
export interface SegmentedControlProps<T extends string> {
  label: string;
  options: SegOption<T>[];
  value: T;
  onChange: (v: T) => void;
  size?: 'sm' | 'md';
  hideLabel?: boolean;
}

export function SegmentedControl<T extends string>({ label, options, value, onChange, size = 'md', hideLabel }: SegmentedControlProps<T>) {
  const id = useId();
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const enabled = options.filter((o) => !o.disabled);
  const onKey = (e: KeyboardEvent) => {
    const i = enabled.findIndex((o) => o.value === value);
    const next =
      e.key === 'ArrowRight' || e.key === 'ArrowDown' ? enabled[(i + 1) % enabled.length]
      : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? enabled[(i - 1 + enabled.length) % enabled.length]
      : e.key === 'Home' ? enabled[0] : e.key === 'End' ? enabled[enabled.length - 1] : null;
    if (!next) return;
    e.preventDefault();
    onChange(next.value);
    refs.current[options.indexOf(next)]?.focus();
  };
  return (
    <div className="flex flex-col gap-1.5">
      <span id={id} className={cx('eyebrow text-ink-subtle', hideLabel && 'sr-only')}>{label}</span>
      <div role="radiogroup" aria-labelledby={id} onKeyDown={onKey} className="inline-flex w-max max-w-full flex-wrap gap-1 rounded-full bg-sunken p-1">
        {options.map((o, i) => {
          const on = o.value === value;
          return (
            <button
              key={o.value}
              ref={(el) => { refs.current[i] = el; }}
              type="button"
              role="radio"
              aria-checked={on}
              aria-disabled={o.disabled || undefined}
              tabIndex={on ? 0 : -1}
              title={o.hint}
              onClick={() => !o.disabled && onChange(o.value)}
              className={cx(
                'rounded-full font-medium transition-colors duration-fast ease-standard',
                size === 'sm' ? 'h-8 px-3 text-sm' : 'h-10 px-4 text-base',
                on ? 'bg-ink text-paper shadow-1' : 'text-ink-muted hover:text-ink',
                o.disabled && 'cursor-not-allowed text-ink-subtle line-through decoration-ink-subtle',
              )}
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export interface SwitchProps {
  label: ReactNode;
  checked: boolean;
  onChange: (v: boolean) => void;
  description?: string;
  /** Visible state words, e.g. ['Unstrained', 'Strained']. */
  states?: [string, string];
}

export function Switch({ label, checked, onChange, description, states }: SwitchProps) {
  const id = useId();
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="flex flex-col">
        <span id={id} className="text-base font-medium text-ink">{label}</span>
        {description && <span className="text-sm text-ink-subtle">{description}</span>}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-labelledby={id}
        onClick={() => onChange(!checked)}
        className="inline-flex shrink-0 items-center gap-2"
      >
        {states && <span className="text-sm text-ink-muted">{checked ? states[1] : states[0]}</span>}
        <span aria-hidden className={cx('relative inline-flex h-6 w-10 rounded-full border transition-colors duration-fast ease-standard', checked ? 'border-brand bg-brand' : 'border-border-strong bg-sunken')}>
          <span className={cx('absolute top-0.5 h-4 w-4 rounded-full shadow-1 transition-[left] duration-fast ease-standard', checked ? 'left-5 bg-brand-on' : 'left-0.5 bg-ink-muted')} />
        </span>
      </button>
    </div>
  );
}
