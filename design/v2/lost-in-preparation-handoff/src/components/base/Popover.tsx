import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { cx } from '../../lib/format';

/**
 * Click/tap disclosure that floats a small panel next to its trigger. Used for
 * the compact honesty details (toxicity sources, "Extraction ≠ detection",
 * "Why did this change?"). Unlike Tooltip it can hold links and controls.
 *
 * - Trigger is a real <button aria-expanded aria-controls>.
 * - Escape closes and returns focus to the trigger; an outside click closes.
 * - The panel is nudged inside the viewport and never widens the page.
 * - Opening fades in 6px; reduced motion removes the animation.
 */
export interface PopoverProps {
  trigger: ReactNode;
  /** Accessible name when the trigger is icon-only. */
  label?: string;
  children: ReactNode;
  triggerClassName?: string;
  align?: 'start' | 'end';
  width?: 'sm' | 'md';
  /** Controlled mode (optional). */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function Popover({ trigger, label, children, triggerClassName, align = 'start', width = 'md', open: openProp, onOpenChange }: PopoverProps) {
  const id = useId();
  const [inner, setInner] = useState(false);
  const open = openProp ?? inner;
  const setOpen = (o: boolean) => { onOpenChange?.(o); if (openProp === undefined) setInner(o); };
  const wrap = useRef<HTMLSpanElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const [shift, setShift] = useState(0);

  useLayoutEffect(() => {
    if (!open || !panel.current) { setShift(0); return; }
    const r = panel.current.getBoundingClientRect();
    const m = 8;
    if (r.right > window.innerWidth - m) setShift(-(r.right - (window.innerWidth - m)));
    else if (r.left < m) setShift(m - r.left);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => { if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { setOpen(false); btn.current?.focus(); } };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDoc); document.removeEventListener('keydown', onKey); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  return (
    <span ref={wrap} className="relative inline-flex">
      <button
        ref={btn}
        type="button"
        aria-expanded={open}
        aria-controls={id}
        aria-label={label}
        onClick={() => setOpen(!open)}
        className={triggerClassName}
      >
        {trigger}
      </button>
      {open && (
        <div
          ref={panel}
          id={id}
          style={shift ? { transform: `translateX(${shift}px)` } : undefined}
          className={cx(
            'fade-in absolute top-full z-40 mt-2 rounded-md border border-border bg-raised p-4 text-left text-sm font-normal text-ink shadow-2',
            align === 'end' ? 'right-0' : 'left-0',
            width === 'sm' ? 'w-max max-w-tooltip' : 'w-max max-w-tooltip md:max-w-prose',
          )}
        >
          {children}
        </div>
      )}
    </span>
  );
}
