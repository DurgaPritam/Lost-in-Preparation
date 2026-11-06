import type { EvidenceStatus } from '../../types';
import { cx } from '../../lib/format';
import { Tooltip } from '../base/Tooltip';
import { IconPending, IconProvisional, IconValidated } from '../icons';

/**
 * Honesty treatment 1 — evidence status.
 * Three states, three redundant channels: glyph shape (filled / half / dashed),
 * border style (solid / dashed / dotted) and a printed word. Colour is a
 * fourth, optional channel. The label is always visible; the tooltip explains.
 */
const SPEC: Record<EvidenceStatus, { label: string; explain: string; cls: string; Icon: typeof IconValidated }> = {
  validated: {
    label: 'Validated',
    explain: 'A person has checked this against the cited reference.',
    cls: 'border-solid border-ink-muted text-ink bg-surface',
    Icon: IconValidated,
  },
  provisional: {
    label: 'Provisional',
    explain: 'AI-generated reference. Not yet checked by a person. Read it as a lead, not a finding.',
    cls: 'border-dashed border-prov-fg text-prov-fg bg-prov-bg',
    Icon: IconProvisional,
  },
  pending: {
    label: 'Pending',
    explain: 'Not yet assessed. No claim is made either way.',
    cls: 'border-dotted border-unk-fg text-unk-fg bg-unk-bg',
    Icon: IconPending,
  },
};

export interface EvidenceStatusBadgeProps {
  status: EvidenceStatus;
  /** Extra context for the tooltip, e.g. reviewer or date. */
  detail?: string;
  size?: 'sm' | 'md';
}

export function EvidenceStatusBadge({ status, detail, size = 'md' }: EvidenceStatusBadgeProps) {
  const s = SPEC[status];
  return (
    <Tooltip
      content={
        <span className="flex flex-col gap-1">
          <span className="font-medium">{s.label}</span>
          <span className="text-ink-muted">{s.explain}</span>
          {detail && <span className="text-ink-subtle">{detail}</span>}
        </span>
      }
    >
      <button
        type="button"
        className={cx(
          'inline-flex items-center gap-1 rounded-full border font-medium',
          size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2 py-0.5 text-sm',
          s.cls,
        )}
        aria-label={`Evidence status: ${s.label}`}
      >
        <s.Icon size={size === 'sm' ? 12 : 14} />
        {s.label}
      </button>
    </Tooltip>
  );
}
