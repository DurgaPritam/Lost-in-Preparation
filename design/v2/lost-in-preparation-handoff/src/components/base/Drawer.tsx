import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { IconClose } from '../icons';

/**
 * Right-hand detail drawer (record detail, provenance, sources). Modal:
 * scrim, focus moves in on open and returns on close, Escape closes, Tab is
 * trapped. Full width below 640px.
 */
export interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  /** Small line above the title, e.g. "Recipe · Culpeper 1652". */
  eyebrow?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Drawer({ open, onClose, title, eyebrow, children, footer }: DrawerProps) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const returnTo = useRef<HTMLElement | null>(null);

  // Phase 4: keep the latest onClose in a ref so a parent re-render (new
  // inline callback) doesn't re-run the effect and yank focus back to the panel.
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    if (!open) return;
    returnTo.current = document.activeElement as HTMLElement;
    panel.current?.focus();
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden'; // no background scroll behind a modal
    const appRoot = document.getElementById('root');
    appRoot?.setAttribute('inert', '');
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeRef.current();
      if (e.key === 'Tab' && panel.current) {
        const f = panel.current.querySelectorAll<HTMLElement>('button, a[href], input, select, textarea, summary, [tabindex]:not([tabindex="-1"])');
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        const a = document.activeElement;
        if (e.shiftKey && (a === first || a === panel.current)) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && a === last) { e.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
      appRoot?.removeAttribute('inert');
      returnTo.current?.focus();
    };
  }, [open]);

  if (!open) return null;
  // Phase 4: portalled to <body> so the rest of the app (#root) can be made
  // inert while the dialog is open — screen-reader browse mode and Tab can no
  // longer wander into the page behind the scrim.
  return createPortal(
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-overlay" onClick={onClose} aria-hidden />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
        tabIndex={-1}
        className="relative flex h-full w-full flex-col border-l border-border bg-surface shadow-3 sm:w-drawer"
      >
        <header className="flex items-start justify-between gap-4 border-b border-border p-5">
          <div className="flex flex-col gap-1">
            {eyebrow && <span className="small-caps text-xs text-ink-subtle">{eyebrow}</span>}
            <h2 id={id} className="m-0 font-serif text-xl font-medium text-ink">{title}</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Close panel" className="inline-flex h-10 w-10 items-center justify-center rounded hover:bg-sunken">
            <IconClose />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
        {footer && <footer className="border-t border-border p-4">{footer}</footer>}
      </div>
    </div>,
    document.body,
  );
}
