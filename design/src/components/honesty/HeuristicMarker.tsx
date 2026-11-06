import type { ReactNode } from 'react';
import type { Heuristic } from '../../types';
import { Tooltip } from '../base/Tooltip';
import { IconHeuristic } from '../icons';

/**
 * Honesty treatment 6 — heuristics look different from model output.
 * A hollow diamond + the small-caps word "heuristic" + a dashed underline on
 * the value it qualifies. No new colour: it stays in ink so it reads as an
 * annotation, not a category. The tooltip states the rule in plain words.
 */
export interface HeuristicMarkerProps {
  heuristic: Heuristic;
  /** Optional value the heuristic produced, e.g. "acidic: likely". */
  children?: ReactNode;
}

export function HeuristicMarker({ heuristic, children }: HeuristicMarkerProps) {
  return (
    <Tooltip
      content={
        <span className="flex flex-col gap-1">
          <span className="font-medium">Heuristic: {heuristic.label}</span>
          <span className="text-ink-muted">{heuristic.rule}</span>
          <span className="text-ink-subtle">A rule of thumb applied by the model, not a measurement.</span>
        </span>
      }
    >
      <button
        type="button"
        aria-label={`Heuristic: ${heuristic.label}. ${heuristic.rule}`}
        className="inline-flex items-baseline gap-1 text-ink"
      >
        <IconHeuristic size={12} className="self-center text-ink-muted" />
        <span className="small-caps text-xs text-ink-muted">heuristic</span>
        <span className="underline decoration-ink-muted decoration-dashed underline-offset-4">
          {children ?? heuristic.label}
        </span>
      </button>
    </Tooltip>
  );
}
