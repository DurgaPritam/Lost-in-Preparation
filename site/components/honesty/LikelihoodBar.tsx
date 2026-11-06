import type { LikelihoodRange, PreparationFamily } from '@/lib/types';
import { cx, fmt, isKnownRange, rangeSpoken } from '@/lib/data/format';
import { MarkHistorical, MarkModern } from '../icons';
import { UnknownValue } from './UnknownValue';

/**
 * Honesty treatment 4 — every likelihood is a range.
 * The low–high band is the dominant mark; the point estimate is a thin
 * tick drawn ON the band, never a separate bar. The printed value leads with
 * the range ("0.33–0.66") and puts the point second and muted. Unknown ranges
 * fill the whole track with the neutral hatch and print "Unknown".
 *
 * Historical vs modern: colour family + lightness (historical lighter) +
 * marker shape (square vs circle) in the label. Never colour alone.
 *
 * What it measures defaults to "Predicted extraction" (treatment 5); pass a
 * different `measure` only for name-resolution confidence.
 */
export interface LikelihoodBarProps {
  range: LikelihoodRange;
  family?: PreparationFamily | 'neutral';
  label?: string;
  measure?: string;
  showScale?: boolean;
  width?: 'sm' | 'md' | 'full';
}

const FILL: Record<NonNullable<LikelihoodBarProps['family']>, string> = {
  historical: 'bg-hist-solid',
  modern: 'bg-mod-solid',
  neutral: 'bg-ink-muted',
};
const TEXT: Record<NonNullable<LikelihoodBarProps['family']>, string> = {
  historical: 'text-hist-fg',
  modern: 'text-mod-fg',
  neutral: 'text-ink',
};

export function LikelihoodBar({
  range,
  family = 'neutral',
  label,
  measure = 'Predicted extraction',
  showScale = false,
  width = 'md',
}: LikelihoodBarProps) {
  const known = isKnownRange(range);
  const pct = (n: number) => `${Math.max(0, Math.min(1, n)) * 100}%`;
  const Mark = family === 'historical' ? MarkHistorical : family === 'modern' ? MarkModern : null;

  return (
    <div className={cx('flex flex-col gap-1', width === 'sm' ? 'w-bar-sm' : width === 'md' ? 'w-bar-md' : 'w-full')}>
      {label && (
        <div className={cx('flex items-center gap-1.5 text-sm', TEXT[family])}>
          {Mark && <Mark />}
          <span className="font-medium">{label}</span>
          <span className="text-ink-subtle">· {measure}</span>
        </div>
      )}
      <div
        role="img"
        aria-label={rangeSpoken(range, `${label ? label + ': ' : ''}${measure}`)}
        className={cx(
          'relative h-3 rounded-sm border border-border-strong',
          known ? 'bg-sunken' : 'bg-hatch-unknown',
        )}
      >
        {/* quarter ticks */}
        {[0.25, 0.5, 0.75].map((t) => (
          <span key={t} aria-hidden className="absolute top-0 h-full w-px bg-border" style={{ left: pct(t) }} />
        ))}
        {known && (
          <>
            <span
              aria-hidden
              className={cx('absolute top-0 h-full rounded-sm', FILL[family])}
              style={{ left: pct(range.low), width: pct(range.high - range.low) }}
            />
            {range.point != null && (
              <span
                aria-hidden
                className="absolute -top-0.5 h-4 w-0.5 -translate-x-1/2 bg-ink"
                style={{ left: pct(range.point) }}
              />
            )}
          </>
        )}
      </div>
      {/* Visible value; aria-hidden because the role="img" label above already says it in full. */}
      <div aria-hidden className="flex items-baseline justify-between gap-2 text-sm">
        {known ? (
          <span className="num font-mono text-ink">
            {fmt(range.low)}–{fmt(range.high)}
            {range.point != null && <span className="text-ink-subtle"> (point {fmt(range.point)})</span>}
          </span>
        ) : (
          <UnknownValue />
        )}
        {showScale && <span className="num font-mono text-xs text-ink-subtle">scale 0–1</span>}
      </div>
    </div>
  );
}
