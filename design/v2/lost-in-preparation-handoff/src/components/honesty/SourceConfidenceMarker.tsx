import type { SourceConfidence } from '../../types';
import { cx, SOURCE_LABEL } from '../../lib/format';
import { Tooltip } from '../base/Tooltip';

/**
 * Honesty 2 — source confidence as a specimen tag, one per source, never
 * merged. Two pips + solid edge = higher; one pip + dashed edge = lower.
 * The disputed share (Pliny) shows on the tag unless `compact`.
 */
export function SourceConfidenceMarker({ confidence, compact = false }: { confidence: SourceConfidence; compact?: boolean }) {
  const src = SOURCE_LABEL[confidence.source];
  const filled = confidence.level === 'higher' ? 2 : confidence.level === 'lower' ? 1 : 0;
  const word = confidence.level === 'higher' ? 'Higher' : confidence.level === 'lower' ? 'Lower' : 'Unknown';
  const share = confidence.disputedShare != null ? `${Math.round(confidence.disputedShare * 100)}% of resolved names disputed` : null;
  return (
    <Tooltip content={<span className="flex flex-col gap-1"><span className="font-display text-lg italic">{src.full}</span><span>Source confidence: {word.toLowerCase()}</span>{share && <span className="text-ink-muted">{share}</span>}{confidence.note && <span className="text-ink-subtle">{confidence.note}</span>}</span>}>
      <button
        type="button"
        aria-label={`Source: ${src.full}. Confidence ${word.toLowerCase()}${share ? `. ${share}` : ''}.`}
        className={cx('inline-flex h-7 items-center gap-2 whitespace-nowrap rounded border border-hist-edge px-2.5 text-sm text-hist-fg', confidence.level !== 'higher' && 'border-dashed')}
      >
        <span className="font-display text-md italic">{src.short}</span>
        <span aria-hidden className="flex gap-0.5">
          {[0, 1].map((i) => <span key={i} className={cx('h-2.5 w-1.5 rounded-sm border border-hist-edge', i < filled && 'bg-hist-edge')} />)}
        </span>
        {!compact && <span>{word}</span>}
        {!compact && share && <span className="hidden text-xs sm:inline">· {share}</span>}
      </button>
    </Tooltip>
  );
}
