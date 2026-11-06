import { cx } from '../../lib/format';
import { Tooltip } from '../base/Tooltip';
import { IconUnknown } from '../icons';

/**
 * Honesty treatment 8 — "Unknown" is a real value.
 * Rendered as the word "Unknown" with a dashed-square glyph in neutral grey:
 * never blank, never "—", never 0, never red. It sorts last in tables and is
 * counted in filters ("Unknown (12)") so it can't be silently dropped.
 */
export interface UnknownValueProps {
  /** Why it's unknown: "Not stated in source", "No modern study found". */
  reason?: string;
  /** Override word, e.g. "Not stated". Keep it neutral. */
  label?: string;
  variant?: 'inline' | 'cell';
  className?: string;
}

export function UnknownValue({ reason, label = 'Unknown', variant = 'inline', className }: UnknownValueProps) {
  const body = (
    <span
      className={cx(
        'inline-flex items-center gap-1 text-unk-fg',
        variant === 'cell' && 'rounded-sm border border-dashed border-unk-line bg-unk-bg px-1.5 text-sm',
        className,
      )}
    >
      {/* shrink-0: the glyph was squashed to a dot in narrow table cells (Phase 4). */}
      <IconUnknown size={14} className="shrink-0" />
      <span>{label}</span>
    </span>
  );
  if (!reason) return body;
  return (
    <Tooltip content={reason}>
      <button type="button" className="inline-flex" aria-label={`${label}: ${reason}`}>
        {body}
      </button>
    </Tooltip>
  );
}
