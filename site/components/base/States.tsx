'use client';

import type { ReactNode } from 'react';
import { Button } from './Button';
import { IconError, IconInfo } from '../icons';

/**
 * Empty, loading, error. Each says what happened and what to do next in
 * plain language. Empty ≠ Unknown: "no records match" is a result about the
 * query; Unknown is a value in the data. They look different on purpose.
 * Errors are ink + a cross glyph, never toxicity red, so a failed request can
 * never be mistaken for a toxicity signal.
 */
export function EmptyState({ title, body, action }: { title: string; body?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2 rounded border border-border bg-surface p-8">
      <IconInfo className="text-ink-muted" />
      <h3 className="m-0 text-base font-semibold text-ink">{title}</h3>
      {body && <p className="m-0 max-w-prose text-base text-ink-muted">{body}</p>}
      {action}
    </div>
  );
}

/** Skeleton rows; announces once via aria-live. Respects reduced motion. */
export function LoadingState({ label = 'Loading', rows = 3 }: { label?: string; rows?: number }) {
  return (
    <div role="status" aria-live="polite" aria-busy="true" className="flex flex-col gap-3 rounded border border-border bg-surface p-5">
      <span className="text-sm text-ink-muted">{label}…</span>
      {Array.from({ length: rows }, (_, i) => (
        <span key={i} aria-hidden className="h-3 w-full animate-pulse rounded-sm bg-sunken motion-reduce:animate-none" />
      ))}
    </div>
  );
}

export function ErrorState({ title, body, onRetry, detail }: { title: string; body: string; onRetry?: () => void; detail?: string }) {
  return (
    <div role="alert" className="flex flex-col items-start gap-2 rounded border-2 border-ink bg-surface p-5">
      <span className="inline-flex items-center gap-2 text-ink">
        <IconError />
        <h3 className="m-0 text-base font-semibold">{title}</h3>
      </span>
      <p className="m-0 max-w-prose text-base text-ink">{body}</p>
      {detail && <code className="rounded-sm bg-sunken px-2 py-1 font-mono text-xs text-ink-muted">{detail}</code>}
      {onRetry && <Button onClick={onRetry} size="sm">Try again</Button>}
    </div>
  );
}
