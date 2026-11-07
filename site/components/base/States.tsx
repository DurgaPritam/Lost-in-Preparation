'use client';

import type { ReactNode } from 'react';
import { Button } from './Button';
import { LeafDrawing } from './PlateSlot';

/**
 * Empty / loading / error. Empty states carry the plate drawing (signature
 * element) and say what to do next. Errors are ink + cross glyph, never
 * toxicity red. Loading announces once and respects reduced motion.
 */
export function EmptyState({ title, body, action }: { title: string; body?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border-strong bg-surface px-6 py-10 text-center">
      <LeafDrawing className="h-20 text-brand opacity-70" />
      <h3 className="m-0 font-display text-xl text-ink">{title}</h3>
      {body && <div className="max-w-prose text-base text-ink-muted">{body}</div>}
      {action}
    </div>
  );
}

export function LoadingState({ label = 'Loading', rows = 4 }: { label?: string; rows?: number }) {
  return (
    <div role="status" aria-live="polite" aria-busy="true" className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-6">
      <span className="text-sm text-ink-muted">{label}…</span>
      {Array.from({ length: rows }, (_, i) => (
        <span key={i} aria-hidden className="flex flex-col gap-2">
          <span className="h-3 w-1/3 animate-pulse rounded-full bg-sunken motion-reduce:animate-none" />
          <span className="h-3.5 w-full animate-pulse rounded-full bg-sunken motion-reduce:animate-none" />
        </span>
      ))}
    </div>
  );
}

export function ErrorState({ title, body, onRetry, detail }: { title: string; body: string; onRetry?: () => void; detail?: string }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-2 rounded-lg border-2 border-ink bg-surface p-5">
      <span className="inline-flex items-center gap-2 text-ink">
        <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="8" cy="8" r="6.25" /><path d="M5.8 5.8l4.4 4.4M10.2 5.8l-4.4 4.4" /></svg>
        <h3 className="m-0 text-base font-semibold">{title}</h3>
      </span>
      <p className="m-0 max-w-prose text-base text-ink">{body}</p>
      {detail && <code className="rounded bg-sunken px-2 py-1 font-mono text-xs text-ink-muted">{detail}</code>}
      {onRetry && <Button onClick={onRetry} size="sm">Try again</Button>}
    </div>
  );
}
