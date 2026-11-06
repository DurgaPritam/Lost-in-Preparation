import type { NameResolution } from '@/lib/types';
import { cx, fmt, isKnownRange } from '@/lib/data/format';
import { EvidenceStatusBadge } from './EvidenceStatusBadge';
import { UnknownValue } from './UnknownValue';
import { Taxon } from '../base/Taxon';

/**
 * Honesty treatment 3 — disputed names are never shown as settled.
 * The name as written in the source leads, in serif italic with quotation
 * marks (it is a historical string, not a taxon). Below, an explicit state
 * line, then EVERY candidate with its own confidence range and evidence
 * status. No candidate is bolded, starred or pre-selected. Order is by the
 * LOW end of each confidence range (Phase 4: it was by point estimate),
 * unknown ranges last; the visual weight is identical.
 *
 * Genus-only resolutions print "Genus only" and the genus with "sp." —
 * we never invent a species epithet.
 */
export interface DisputedNameProps {
  resolution: NameResolution;
  layout?: 'block' | 'inline';
}

const STATE_LINE: Record<NameResolution['state'], string> = {
  resolved: 'Resolved to one species',
  disputed: 'Disputed — not settled',
  genus_only: 'Genus only — species not determinable',
  unresolved: 'Unresolved',
};

export function DisputedName({ resolution, layout = 'block' }: DisputedNameProps) {
  const { historicalName, state, candidates } = resolution;
  const sorted = [...candidates].sort((a, b) => (b.confidence.low ?? -1) - (a.confidence.low ?? -1));
  const n = candidates.length;

  if (layout === 'inline') {
    return (
      <span className="inline-flex flex-wrap items-baseline gap-x-2">
        <span className="font-serif text-md italic text-ink">“{historicalName}”</span>
        {state === 'unresolved' ? (
          <UnknownValue label="Unresolved" />
        ) : state === 'disputed' ? (
          <span className="text-sm text-ink-muted">
            {n} candidates · disputed
          </span>
        ) : (
          <span className="text-sm text-ink-muted">
            {sorted[0] && <Taxon name={sorted[0].rank === 'genus' ? `${sorted[0].taxon} sp.` : sorted[0].taxon} />}
            {state === 'genus_only' && <span> · genus only</span>}
          </span>
        )}
      </span>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col">
        <span className="small-caps text-xs text-ink-subtle">As written in source</span>
        <span className="font-serif text-xl italic text-ink">“{historicalName}”</span>
      </div>
      <div
        className={cx(
          'inline-flex w-max items-center gap-1.5 rounded-sm border px-2 py-0.5 text-sm',
          state === 'resolved' ? 'border-border-strong text-ink' : 'border-dashed border-ink-muted text-ink-muted',
        )}
      >
        {STATE_LINE[state]}
        {state === 'disputed' && <span>· {n} candidates</span>}
      </div>

      {state === 'unresolved' || n === 0 ? (
        <UnknownValue variant="cell" label="No candidate species" reason="The name could not be matched to any taxon." />
      ) : (
        // Phase 4: scroll box so three columns never push a 390px page sideways.
        <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <caption className="sr-only">Candidate taxa for “{historicalName}”</caption>
          <thead>
            <tr className="text-left text-xs text-ink-subtle">
              <th scope="col" className="py-1 pr-3 font-medium">Candidate</th>
              <th scope="col" className="py-1 pr-3 font-medium">Match confidence</th>
              <th scope="col" className="py-1 font-medium">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((c) => (
              <tr key={c.taxon} className="border-t border-border">
                <td className="py-1.5 pr-3">
                  <span className="text-ink"><Taxon name={c.rank === 'genus' ? `${c.taxon} sp.` : c.taxon} /></span>
                  {c.authority && <span className="text-ink-subtle"> {c.authority}</span>}
                  {c.rank === 'genus' && <span className="ml-1 text-xs text-ink-muted">(genus)</span>}
                </td>
                <td className="num py-1.5 pr-3 font-mono">
                  {isKnownRange(c.confidence) ? (
                    <span>
                      {fmt(c.confidence.low)}–{fmt(c.confidence.high)}
                    </span>
                  ) : (
                    /* SITE: M2 gives a heuristic score without an interval; the score is in the reason, never shown as a range. */
                    <UnknownValue
                      label="Interval unknown"
                      reason={c.confidence.point != null ? `Heuristic match score ${fmt(c.confidence.point)}. No interval is computed, so no range is shown.` : undefined}
                    />
                  )}
                </td>
                <td className="py-1.5">
                  <EvidenceStatusBadge status={c.evidence} size="sm" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}
