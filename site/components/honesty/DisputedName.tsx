'use client';

import { useId, useState } from 'react';
import type { NameResolution } from '@/lib/types';
import { cx, isKnownRange } from '@/lib/data/format';
import { EvidenceStatusBadge } from './EvidenceStatusBadge';
import { UnknownValue } from './UnknownValue';
import { LikelihoodBar } from './LikelihoodBar';
import { Taxon } from '../base/Taxon';

/**
 * Honesty 3 — disputed names, shown elegantly and never as settled.
 * inline: “absinthium” → 3 candidates · disputed, with an equal-weight
 *         candidate strip (segments sized by the LOW end of each range;
 *         unknown = hatched segment).
 * block:  the same header plus an expandable list: every candidate with its
 *         own confidence range bar and evidence badge. No winner, no star.
 * Genus-only prints "Mentha sp. · genus only" — never an invented epithet.
 */
const STATE: Record<NameResolution['state'], string> = {
  resolved: 'resolved', disputed: 'disputed', genus_only: 'genus only', unresolved: 'unresolved',
};

function Strip({ r }: { r: NameResolution }) {
  if (r.state !== 'disputed') return null;
  return (
    <span aria-hidden className="flex h-1.5 w-24 gap-0.5">
      {r.candidates.map((c) => (
        <span key={c.taxon} className={cx('rounded-full', isKnownRange(c.confidence) ? 'bg-ink-muted' : 'bg-hatch-unknown border border-unk-line')} style={{ flexGrow: isKnownRange(c.confidence) ? Math.max(0.15, c.confidence.low) : 0.15 }} />
      ))}
    </span>
  );
}

export function DisputedName({ resolution, layout = 'block' }: { resolution: NameResolution; layout?: 'block' | 'inline' }) {
  const { historicalName, state, candidates } = resolution;
  const sorted = [...candidates].sort((a, b) => (b.confidence.low ?? -1) - (a.confidence.low ?? -1));
  const n = candidates.length;
  const [open, setOpen] = useState(state === 'disputed');
  const id = useId();

  const summary =
    state === 'unresolved' ? <UnknownValue label="Unresolved" />
    : state === 'disputed' ? <span className="inline-flex items-center gap-2 text-sm text-ink-muted"><span>→ {n} candidates · disputed</span><Strip r={resolution} /></span>
    : <span className="text-sm text-ink-muted">→ <Taxon name={sorted[0].rank === 'genus' ? `${sorted[0].taxon} sp.` : sorted[0].taxon} />{state === 'genus_only' && ' · genus only'}</span>;

  if (layout === 'inline') {
    return (
      <span className="inline-flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span className="font-display text-lg italic text-ink">“{historicalName}”</span>
        {summary}
      </span>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-display text-2xl italic text-ink">“{historicalName}”</span>
        {summary}
      </div>
      {state !== 'unresolved' && n > 0 && (
        <>
          <button type="button" aria-expanded={open} aria-controls={id} onClick={() => setOpen((o) => !o)} className="w-max text-sm font-medium text-brand underline underline-offset-4">
            {open ? 'Hide' : 'Show'} {n === 1 ? 'the candidate' : `all ${n} candidates`} ({STATE[state]})
          </button>
          {open && (
            <ul id={id} className="fade-in m-0 flex list-none flex-col gap-3 p-0">
              {sorted.map((c) => (
                <li key={c.taxon} className="flex flex-col gap-1.5 rounded-md border border-border bg-surface p-3">
                  <span className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-base text-ink">
                      <Taxon name={c.rank === 'genus' ? `${c.taxon} sp.` : c.taxon} authority={c.authority} />
                      {c.rank === 'genus' && <span className="ml-1 text-xs text-ink-subtle">(genus)</span>}
                    </span>
                    <EvidenceStatusBadge status={c.evidence} size="sm" />
                  </span>
                  {isKnownRange(c.confidence)
                    ? <LikelihoodBar range={c.confidence} family="neutral" measure="Match confidence" label={c.taxon} size="sm" />
                    // SITE: M2 gives a heuristic score without an interval; it is in the reason, never drawn as a range.
                    : <UnknownValue label="Interval unknown" reason={c.confidence.point != null ? `Heuristic match score ${c.confidence.point.toFixed(2)}. No interval is computed, so no range is shown.` : 'No match confidence recorded.'} />}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
