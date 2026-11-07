import type { Plate } from '../../types';
import { cx } from '../../lib/format';
import { Taxon } from './Taxon';

/**
 * Botanical plate slot — the signature element. Shows the sourced 19th-century
 * plate when `plate.imageUrl` exists; otherwise a drawn placeholder (an
 * original, generic leaf-and-stem line drawing). EVERY slot prints its licence
 * and host, and its sourcing status, so an unlicensed image can never slip in.
 *
 * In dark theme the drawing is light-on-dark (Nocturne); real plates should be
 * shown as-is on a paper-coloured mat in both themes.
 */
export interface PlateSlotProps {
  plate?: Plate | null;
  taxon: string;
  size?: 'thumb' | 'card' | 'hero';
  showCaption?: boolean;
  className?: string;
}

export function LeafDrawing({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 44 64" className={className} aria-hidden focusable="false">
      <path d="M22 62 C22 44 21 28 23 4" fill="none" stroke="currentColor" strokeWidth="0.9" />
      <g fill="none" stroke="currentColor" strokeWidth="0.75">
        <path d="M22 50 C14 48 9 44 7 40 C13 41 18 44 22 50" /><path d="M22 50 C30 48 35 44 37 40 C31 41 26 44 22 50" />
        <path d="M22 38 C15 36 11 32 9 28 C15 29 19 32 22 38" /><path d="M22 38 C29 36 33 32 35 28 C29 29 25 32 22 38" />
        <path d="M22.5 26 C16 24 13 20 12 16 C17 17 20 20 22.5 26" /><path d="M22.5 26 C29 24 32 20 33 16 C28 17 25 20 22.5 26" />
        <path d="M23 12 C20 10 19 7 20 4 C22 6 23 9 23 12" />
      </g>
    </svg>
  );
}

const SIZE = {
  thumb: 'h-plate w-plate rounded',
  card: 'aspect-card w-full rounded-md',
  hero: 'aspect-portrait w-full rounded-lg',
};

export function PlateSlot({ plate, taxon, size = 'card', showCaption = true, className }: PlateSlotProps) {
  const sourced = !!plate?.imageUrl;
  const licence = plate?.licence ?? 'Licence not set';
  const host = plate?.host ?? 'host not set';
  const status = plate?.status === 'confirmed' ? 'licence confirmed' : plate?.status === 'sourced' ? 'licence to confirm' : 'plate to source';
  return (
    <figure className={cx('m-0 flex flex-col gap-1.5', className)}>
      <div className={cx('relative flex items-center justify-center overflow-hidden border border-border bg-hist-bg text-brand', SIZE[size])}>
        {sourced ? (
          <img src={plate!.imageUrl!} alt={`Botanical plate of ${taxon}`} className="h-full w-full object-contain" />
        ) : (
          <LeafDrawing className={size === 'thumb' ? 'h-16' : 'h-3/4 opacity-80'} />
        )}
      </div>
      {showCaption && size !== 'thumb' && (
        <figcaption className="text-xs text-ink-subtle">
          <Taxon name={taxon} /> · {licence} · {host} · <span className="italic">{status}</span>
        </figcaption>
      )}
    </figure>
  );
}
