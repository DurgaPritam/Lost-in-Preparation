import type { GapRow } from '@/lib/data/selectors/home';
import { ciText, pct } from '@/lib/data/format';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * SITE (new, built from tokens only, like the design's local MatchBar / IntervalChart): a share of studies (0–100%)
 * with its 95% CI band and a point tick. The band is the main mark; the printed text leads with k of n and the CI.
 */
export function ShareBar({ row }: { row: GapRow }) {
  const known = row.value != null && row.low != null && row.high != null;
  const p = (n: number) => `${Math.max(0, Math.min(1, n)) * 100}%`;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
        <span className="font-medium text-ink">{row.label}</span>
        {known ? (
          <span className="num font-mono text-ink">
            {pct(row.value!)} <span className="text-ink-muted">({row.k} of {row.n}; {ciText(row.low, row.high)})</span>
          </span>
        ) : (
          <UnknownValue label="Not computed" />
        )}
      </div>
      <div
        role="img"
        aria-label={known ? `${row.label}: ${pct(row.value!)} of ${row.n} studies, 95% confidence interval ${pct(row.low!)} to ${pct(row.high!)}.` : `${row.label}: not computed.`}
        className={known ? 'relative h-3 rounded-sm border border-border-strong bg-sunken' : 'relative h-3 rounded-sm border border-border-strong bg-hatch-unknown'}
      >
        {[0.25, 0.5, 0.75].map((t) => <span key={t} aria-hidden className="absolute top-0 h-full w-px bg-border" style={{ left: p(t) }} />)}
        {known && (
          <>
            <span aria-hidden className="absolute top-0 h-full rounded-sm bg-ink-muted" style={{ left: p(row.low!), width: p(row.high! - row.low!) }} />
            <span aria-hidden className="absolute -top-0.5 h-4 w-0.5 -translate-x-1/2 bg-ink" style={{ left: p(row.value!) }} />
          </>
        )}
      </div>
    </div>
  );
}
