import type { ReactNode } from 'react';
import { cx } from '../../lib/format';

/**
 * Flat card: 1px border on surface, elevation 0. Only interactive cards get
 * elevation 1 on hover. No coloured left borders, no gradients.
 * `meta` is the row of honesty badges; it sits directly under the title so
 * status is read BEFORE the content.
 */
export interface CardProps {
  title?: ReactNode;
  eyebrow?: string;
  meta?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  as?: 'article' | 'section' | 'div';
  interactive?: boolean;
  className?: string;
}

export function Card({ title, eyebrow, meta, children, footer, as: Tag = 'article', interactive, className }: CardProps) {
  return (
    <Tag
      className={cx(
        'flex flex-col gap-3 rounded border border-border bg-surface p-5',
        interactive && 'transition-shadow duration-fast ease-standard hover:shadow-1',
        className,
      )}
    >
      {(eyebrow || title) && (
        <header className="flex flex-col gap-1">
          {eyebrow && <span className="small-caps text-xs text-ink-subtle">{eyebrow}</span>}
          {title && <h3 className="m-0 text-lg font-semibold text-ink">{title}</h3>}
        </header>
      )}
      {meta && <div className="flex flex-wrap items-center gap-2">{meta}</div>}
      {children && <div className="flex flex-col gap-3 text-base text-ink">{children}</div>}
      {footer && <footer className="mt-auto flex flex-wrap items-center gap-2 border-t border-border pt-3">{footer}</footer>}
    </Tag>
  );
}

/** A quotation from a historical source. Serif, with citation line. */
export function SourcePassage({ children, cite }: { children: ReactNode; cite: string }) {
  return (
    <figure className="m-0 flex flex-col gap-2 border-y border-border py-3">
      <blockquote className="m-0 max-w-prose font-serif text-md text-ink">{children}</blockquote>
      <figcaption className="text-xs text-ink-subtle">{cite}</figcaption>
    </figure>
  );
}
