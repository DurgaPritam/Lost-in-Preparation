import type { ReactNode } from 'react';
import type { Heuristic } from '@/lib/types';
import { Tooltip } from '../base/Tooltip';
import { IconHeuristic } from '../icons';

/**
 * Honesty 6 — heuristics are marked as rules of thumb: hollow diamond, the
 * small-caps word "heuristic", a dashed underline. Ink only (an annotation,
 * not a category). The tooltip states the rule and "not a measurement".
 */
export function HeuristicMarker({ heuristic, children }: { heuristic: Heuristic; children?: ReactNode }) {
  return (
    <Tooltip content={<span className="flex flex-col gap-1"><span className="font-semibold">Heuristic · {heuristic.label}</span><span className="text-ink-muted">{heuristic.rule}</span><span className="text-ink-subtle">A rule of thumb applied by the model, not a measurement.</span></span>}>
      <button type="button" aria-label={`Heuristic: ${heuristic.label}. ${heuristic.rule}`} className="inline-flex items-baseline gap-1 text-ink">
        <IconHeuristic size={11} className="self-center text-ink-muted" />
        <span className="small-caps text-xs text-ink-muted">heuristic</span>
        <span className="underline decoration-ink-muted decoration-dashed underline-offset-4">{children ?? heuristic.label}</span>
      </button>
    </Tooltip>
  );
}
