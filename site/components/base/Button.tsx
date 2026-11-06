'use client';

import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cx } from '@/lib/data/format';

/**
 * Three variants only. Primary is ink-on-paper inverted (not a brand colour),
 * so it never competes with the historical/modern families or toxicity red.
 * Minimum hit area 36px (md) / 44px (lg for touch-primary actions).
 */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

const V = {
  primary: 'bg-ink text-paper border-ink hover:bg-ink-muted hover:border-ink-muted',
  secondary: 'bg-surface text-ink border-border-strong hover:bg-sunken',
  ghost: 'bg-transparent text-ink border-transparent hover:bg-sunken',
};
const S = { sm: 'h-8 px-3 text-sm', md: 'h-10 px-4 text-base', lg: 'h-12 px-5 text-base' };

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'secondary', size = 'md', className, type = 'button', ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded border font-medium',
        'transition-colors duration-fast ease-standard',
        'disabled:cursor-not-allowed disabled:border-border disabled:bg-sunken disabled:text-ink-subtle',
        V[variant],
        S[size],
        className,
      )}
      {...rest}
    />
  );
});
