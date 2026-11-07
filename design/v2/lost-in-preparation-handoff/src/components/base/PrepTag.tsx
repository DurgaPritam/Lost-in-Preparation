import type { Preparation } from '../../types';
import { cx, HEAT_LABEL, VEHICLE_LABEL } from '../../lib/format';

/**
 * Preparation tag. Historical = saffron tint + square mark + display-serif
 * vehicle; modern lab = aubergine/lilac outline + round mark + sans.
 * Unstated details read "not stated" rather than being guessed.
 */
export function MarkHist({ className }: { className?: string }) {
  return <span aria-hidden className={cx('inline-block h-2.5 w-2.5 shrink-0 rounded-sm border border-hist-edge bg-hist-solid', className)} />;
}
export function MarkMod({ className }: { className?: string }) {
  return <span aria-hidden className={cx('inline-block h-2.5 w-2.5 shrink-0 rounded-full border-2 border-mod-edge', className)} />;
}

export function PrepTag({ prep, compact }: { prep: Preparation; compact?: boolean }) {
  const hist = prep.family === 'historical';
  const bits = [
    prep.heat ? HEAT_LABEL[prep.heat].toLowerCase() : 'heat not stated',
    prep.filtered == null ? 'filtering not stated' : prep.filtered ? 'strained' : 'unstrained',
    ...(prep.acidified ? ['acidified'] : []),
  ];
  return (
    <span
      className={cx(
        'inline-flex max-w-full flex-wrap items-center gap-x-1.5 rounded-full px-3 py-0.5 text-sm',
        hist ? 'bg-hist-bg text-hist-fg' : 'border border-mod-edge text-mod-fg',
      )}
    >
      {hist ? <MarkHist /> : <MarkMod />}
      <span className="sr-only">{hist ? 'Historical preparation:' : 'Modern lab method:'}</span>
      <span className={cx('font-medium', hist && 'font-display italic')}>{VEHICLE_LABEL[prep.vehicle]}</span>
      {!compact && <span className="text-ink-muted">· {bits.join(' · ')}</span>}
    </span>
  );
}

/** One legend for any view that mixes families. */
export function PrepLegend({ modernLabel = 'Modern lab method' }: { modernLabel?: string }) {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-ink-muted">
      <span className="inline-flex items-center gap-2"><span aria-hidden className="inline-block h-2.5 w-6 rounded-full border border-hist-edge bg-hist-solid" />This preparation (range)</span>
      <span className="inline-flex items-center gap-2"><span aria-hidden className="inline-block h-2.5 w-6 rounded-full border-2 border-mod-edge" />{modernLabel}</span>
      <span className="inline-flex items-center gap-2"><span aria-hidden className="inline-block h-2.5 w-6 rounded-full border border-unk-line bg-hatch-unknown" />Unknown</span>
    </div>
  );
}
