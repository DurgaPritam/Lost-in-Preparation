import type { Preparation } from '../../types';
import { cx, VEHICLE_LABEL } from '../../lib/format';
import { MarkHistorical, MarkModern } from '../icons';

/**
 * Preparation tag. Historical = warm family + square mark + serif vehicle
 * name; modern = cool family + circle mark + sans. Three redundant cues.
 * `filtered: null` prints "filtering not stated" rather than guessing.
 */
export function PrepTag({ prep }: { prep: Preparation }) {
  const hist = prep.family === 'historical';
  const Mark = hist ? MarkHistorical : MarkModern;
  const filt = prep.filtered == null ? 'filtering not stated' : prep.filtered ? 'filtered' : 'unfiltered';
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-sm',
        hist ? 'border-hist-fg bg-hist-bg text-hist-fg' : 'border-mod-fg bg-mod-bg text-mod-fg',
      )}
    >
      <Mark />
      <span className="sr-only">{hist ? 'Historical preparation:' : 'Modern preparation:'}</span>
      <span className={cx(hist && 'font-serif text-base italic')}>{VEHICLE_LABEL[prep.vehicle]}</span>
      <span className={cx('text-xs', prep.filtered == null && 'italic')}>· {filt}</span>
    </span>
  );
}

/** Legend that appears once per chart/table that mixes families. */
export function PrepLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4 text-sm">
      <span className="inline-flex items-center gap-1.5 text-hist-fg"><MarkHistorical /> Historical preparation</span>
      <span className="inline-flex items-center gap-1.5 text-mod-fg"><MarkModern /> Modern study preparation</span>
      <span className="inline-flex items-center gap-1.5 text-unk-fg">
        <span aria-hidden className="inline-block h-2.5 w-4 rounded-sm border border-unk-line bg-hatch-unknown" /> Unknown
      </span>
    </div>
  );
}
