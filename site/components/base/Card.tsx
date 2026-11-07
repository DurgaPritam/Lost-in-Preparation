import type { ReactNode } from 'react';
import { cx } from '@/lib/data/format';

/**
 * Card: rounded surface with a hairline and soft shadow. The honesty `meta`
 * row sits directly under the title, so status is read before content.
 */
export interface CardProps {
  title?: ReactNode;
  eyebrow?: ReactNode;
  meta?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  as?: 'article' | 'section' | 'div';
  className?: string;
  titleLevel?: 2 | 3;
}

export function Card({ title, eyebrow, meta, children, footer, as: Tag = 'article', className, titleLevel = 3 }: CardProps) {
  const H = titleLevel === 2 ? 'h2' : 'h3';
  return (
    <Tag className={cx('flex flex-col gap-4 rounded-lg border border-border bg-surface p-5 shadow-1 md:p-6', className)}>
      {(eyebrow || title) && (
        <header className="flex flex-col gap-1">
          {eyebrow && <span className="eyebrow text-ink-subtle">{eyebrow}</span>}
          {title && <H className="m-0 font-display text-xl text-ink">{title}</H>}
        </header>
      )}
      {meta && <div className="flex flex-wrap items-center gap-2">{meta}</div>}
      {children && <div className="flex flex-col gap-3 text-base text-ink">{children}</div>}
      {footer && <footer className="mt-auto flex flex-wrap items-center gap-2 border-t border-border pt-4">{footer}</footer>}
    </Tag>
  );
}

/** A quotation from a historical source: display serif, citation line. */
export function SourcePassage({ children, cite }: { children: ReactNode; cite: string }) {
  return (
    <figure className="m-0 flex flex-col gap-2 border-l-0 py-1">
      <blockquote className="m-0 max-w-prose font-display text-xl italic text-ink">{children}</blockquote>
      <figcaption className="text-xs text-ink-subtle">{cite}</figcaption>
    </figure>
  );
}
