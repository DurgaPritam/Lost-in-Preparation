import {
  cloneElement, useId, useLayoutEffect, useRef, useState,
  type FocusEvent, type KeyboardEvent, type MouseEvent, type ReactElement, type ReactNode,
} from 'react';
import { cx } from '../../lib/format';

/**
 * Accessible tooltip ("toggletip"). The trigger must be focusable (button or
 * link). It opens on hover, on keyboard focus AND on click/tap (touch has no
 * hover and iOS doesn't focus buttons on tap); closes on Escape, blur, or a
 * second click. Wired with aria-describedby so screen readers read it after
 * the trigger's name.
 *
 * Phase 4 fixes: the closed tooltip is display:none (an invisible, absolutely
 * positioned box used to widen the page and cause sideways scroll at 390px);
 * when open it is nudged back inside the viewport and flips below the
 * trigger if there is no room above. The child's own handlers are preserved.
 *
 * Content is supplementary: never put the only copy of a fact in a tooltip —
 * badges always print their label inline.
 */
export interface TooltipProps {
  content: ReactNode;
  children: ReactElement;
  side?: 'top' | 'bottom';
  className?: string;
}

type TriggerProps = {
  onFocus?: (e: FocusEvent) => void;
  onBlur?: (e: FocusEvent) => void;
  onClick?: (e: MouseEvent) => void;
  onKeyDown?: (e: KeyboardEvent) => void;
};

export function Tooltip({ content, children, side = 'top', className }: TooltipProps) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [shiftX, setShiftX] = useState(0);
  const [flip, setFlip] = useState(false);
  const tip = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    if (!open || !tip.current) { setShiftX(0); setFlip(false); return; }
    const r = tip.current.getBoundingClientRect();
    const margin = 8;
    const over = r.right - (window.innerWidth - margin);
    setShiftX(over > 0 ? -Math.min(over, r.left - margin) : 0);
    if (side === 'top' && r.top < margin) setFlip(true);
  }, [open, side]);

  const p = children.props as TriggerProps;
  const trigger = cloneElement(children, {
    'aria-describedby': id,
    onFocus: (e: FocusEvent) => { p.onFocus?.(e); setOpen(true); },
    onBlur: (e: FocusEvent) => { p.onBlur?.(e); setOpen(false); },
    onClick: (e: MouseEvent) => { p.onClick?.(e); setOpen((o) => !o); },
    onKeyDown: (e: KeyboardEvent) => { p.onKeyDown?.(e); if (e.key === 'Escape') setOpen(false); },
  } as Record<string, unknown>);
  const below = side === 'bottom' || flip;

  return (
    <span
      className={cx('relative inline-flex', className)}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      {trigger}
      <span
        ref={tip}
        role="tooltip"
        id={id}
        hidden={!open}
        style={shiftX ? { transform: `translateX(${shiftX}px)` } : undefined}
        className={cx(
          'pointer-events-none absolute left-0 z-50 w-max max-w-tooltip rounded border border-border bg-raised px-3 py-2',
          'text-left text-sm font-normal text-ink shadow-2',
          below ? 'top-full mt-2' : 'bottom-full mb-2',
        )}
      >
        {content}
      </span>
    </span>
  );
}
