import type { LikelihoodRange } from '@/lib/types';
import { cx, fmt, isKnownRange, rangeSpoken } from '@/lib/data/format';
import { UnknownValue } from './UnknownValue';

/**
 * Honesty 4 — every likelihood is a RANGE.
 * - The saffron band (historical preparation) is the value; the point is a
 *   thin ink tick on it. Light theme draws the band with a darker edge (the
 *   saffron fill alone is under 3:1 on paper).
 * - `compare` overlays the modern lab method as an OUTLINED aubergine/lilac
 *   band — fill style + lightness, not hue alone, separates the two.
 * - Bands animate between preparations (480ms; 0ms under reduced motion).
 * - Unknown fills the whole track with the neutral hatch.
 */
export interface LikelihoodBarProps {
  range: LikelihoodRange;
  compare?: LikelihoodRange | null;
  compareLabel?: string;
  label?: string;
  measure?: string;
  family?: 'historical' | 'modern' | 'neutral';
  showValue?: boolean;
  size?: 'sm' | 'md';
}

const clamp = (n: number) => Math.max(0, Math.min(1, n));
const pct = (n: number) => `${clamp(n) * 100}%`;
/** SITE: the band's width is clamp(high) - clamp(low), so a range that runs past the track (e.g. an error interval drawn
 *  on a 0–1.5 scale) ends at the edge instead of widening the page. */
const span = (lo: number, hi: number) => `${Math.max(0, clamp(hi) - clamp(lo)) * 100}%`;

export function LikelihoodBar({ range, compare, compareLabel = 'modern lab method', label, measure = 'Predicted extraction', family = 'historical', showValue = true, size = 'md' }: LikelihoodBarProps) {
  const known = isKnownRange(range);
  const cKnown = compare ? isKnownRange(compare) : false;
  const spoken = rangeSpoken(range, `${label ? label + ': ' : ''}${measure}`) + (compare ? ` ${cKnown ? `Compared with ${compareLabel}: between ${fmt(compare!.low!)} and ${fmt(compare!.high!)}.` : `${compareLabel}: unknown.`}` : '');
  const band =
    family === 'historical' ? 'bg-hist-solid border border-hist-edge shadow-glow'
    : family === 'modern' ? 'border-2 border-mod-edge'
    : 'bg-ink-muted';
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div
        role="img"
        aria-label={spoken}
        className={cx('relative w-full rounded-full border border-border-strong', size === 'sm' ? 'h-3' : 'h-4', known ? 'bg-sunken' : 'bg-hatch-unknown')}
      >
        {[0.25, 0.5, 0.75].map((t) => <span key={t} aria-hidden className="absolute inset-y-0 w-px bg-border" style={{ left: pct(t) }} />)}
        <span
          aria-hidden
          className={cx('bar-motion absolute inset-y-0.5 rounded-full', band)}
          style={known ? { left: pct(range.low), width: span(range.low, range.high), opacity: 1 } : { left: 0, width: 0, opacity: 0 }}
        />
        {known && range.point != null && (
          <span aria-hidden className="bar-motion absolute -inset-y-0.5 w-0.5 -translate-x-1/2 rounded-full bg-ink" style={{ left: pct(range.point) }} />
        )}
        {compare && cKnown && (
          <span aria-hidden className="bar-motion absolute -inset-y-1 rounded-full border-2 border-mod-edge" style={{ left: pct(compare.low!), width: span(compare.low!, compare.high!) }} />
        )}
      </div>
      {showValue && (
        <div aria-hidden className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
          {known ? (
            <span className="num font-mono text-ink">{fmt(range.low)}–{fmt(range.high)}{range.point != null && <span className="text-ink-subtle"> · pt {fmt(range.point)}</span>}</span>
          ) : <UnknownValue />}
          {compare && (cKnown
            ? <span className="num font-mono text-mod-fg">lab {fmt(compare.low!)}–{fmt(compare.high!)}</span>
            : <span className="text-unk-fg">lab: unknown</span>)}
        </div>
      )}
    </div>
  );
}
