'use client';

import type { SourceConfidence } from '@/lib/types';
import { cx, SOURCE_LABEL } from '@/lib/data/format';
import { Tooltip } from '../base/Tooltip';
import { UnknownValue } from './UnknownValue';

/**
 * Honesty treatment 2 — source confidence, per source, never merged.
 * Culpeper and Pliny each get their own marker wherever a claim depends on
 * them. Confidence is shown as a two-pip meter (filled = higher) plus the word,
 * plus the disputed share when known. Both sources use the historical family;
 * the meter, not colour, distinguishes the levels.
 *
 * There is deliberately no combined "overall source confidence".
 */
export interface SourceConfidenceMarkerProps {
  confidence: SourceConfidence;
  compact?: boolean;
}

export function SourceConfidenceMarker({ confidence, compact = false }: SourceConfidenceMarkerProps) {
  const src = SOURCE_LABEL[confidence.source];
  const filled = confidence.level === 'higher' ? 2 : confidence.level === 'lower' ? 1 : 0;
  const levelWord =
    confidence.level === 'higher' ? 'Higher confidence' : confidence.level === 'lower' ? 'Lower confidence' : null;
  const share =
    confidence.disputedShare != null ? `${Math.round(confidence.disputedShare * 100)}% of resolved names disputed` : null;

  return (
    <Tooltip
      content={
        <span className="flex flex-col gap-1">
          <span className="font-serif text-md italic">{src.full}</span>
          <span>{levelWord ?? 'Source confidence unknown'}</span>
          {share && <span className="text-ink-muted">{share}</span>}
          {confidence.note && <span className="text-ink-subtle">{confidence.note}</span>}
        </span>
      }
    >
      <button
        type="button"
        aria-label={`Source: ${src.full}. ${levelWord ?? 'Confidence unknown'}${share ? '. ' + share : ''}.`}
        className={cx(
          'inline-flex items-center gap-2 rounded border border-hist-fg bg-hist-bg px-2 py-0.5 text-sm text-hist-fg',
          confidence.level === 'lower' && 'border-dashed',
        )}
      >
        <span className="font-serif text-base italic">{src.short}</span>
        {levelWord ? (
          <span className="inline-flex items-center gap-1">
            <span aria-hidden className="flex gap-0.5">
              {[0, 1].map((i) => (
                <span key={i} className={cx('h-2.5 w-1.5 rounded-sm border border-hist-fg', i < filled && 'bg-hist-fg')} />
              ))}
            </span>
            {!compact && <span>{confidence.level === 'higher' ? 'Higher' : 'Lower'}</span>}
          </span>
        ) : (
          <UnknownValue label="Confidence unknown" />
        )}
        {!compact && share && <span className="text-xs text-hist-fg">· {share}</span>}
      </button>
    </Tooltip>
  );
}
