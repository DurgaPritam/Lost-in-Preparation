import { forwardRef, type AnchorHTMLAttributes, type ButtonHTMLAttributes } from 'react';
import { cx } from '../../lib/format';

/**
 * Pill buttons. Primary uses the brand colour (botanical green / verdigris):
 * brand is wayfinding, never a judgement. Heights 32 / 40 / 48.
 */
type Variant = 'primary' | 'secondary' | 'ghost';
type Size = 'sm' | 'md' | 'lg';
const V: Record<Variant, string> = {
  primary: 'bg-brand text-brand-on border-brand hover:opacity-90',
  secondary: 'bg-transparent text-ink border-border-strong hover:bg-sunken',
  ghost: 'bg-transparent text-ink border-transparent hover:bg-sunken',
};
const S: Record<Size, string> = { sm: 'h-8 px-3 text-sm', md: 'h-10 px-4 text-base', lg: 'h-12 px-6 text-base' };
const base = 'inline-flex items-center justify-center gap-2 rounded-full border font-semibold no-underline transition-[background-color,opacity] duration-fast ease-standard disabled:cursor-not-allowed disabled:border-border disabled:bg-sunken disabled:text-ink-subtle';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> { variant?: Variant; size?: Size }
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button({ variant = 'secondary', size = 'md', className, type = 'button', ...rest }, ref) {
  return <button ref={ref} type={type} className={cx(base, V[variant], S[size], className)} {...rest} />;
});

export interface LinkButtonProps extends AnchorHTMLAttributes<HTMLAnchorElement> { variant?: Variant; size?: Size }
export function LinkButton({ variant = 'secondary', size = 'md', className, ...rest }: LinkButtonProps) {
  return <a className={cx(base, V[variant], S[size], className)} {...rest} />;
}
