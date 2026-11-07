import type { EvidenceStatus } from '@/lib/types';
import { cx } from '@/lib/data/format';
import { Tooltip } from '../base/Tooltip';
import { IconPending, IconProvisional, IconValidated } from '../icons';

/**
 * Honesty 1 — evidence status, as a compact pill.
 * Shape + border style + word carry the meaning; colour is redundant.
 *   Validated   filled disc ✓, solid ink border
 *   Provisional half disc, DASHED border (AI reference, not human-checked)
 *   Pending     dashed ring, DOTTED border, unknown grey
 * v2: Provisional is neutral (prov-*) — it no longer shares the modern-lab hue.
 */
const SPEC: Record<EvidenceStatus, { label: string; explain: string; cls: string; Icon: typeof IconValidated }> = {
  validated: { label: 'Validated', explain: 'A person has checked this against the cited reference.', cls: 'border-ink text-ink', Icon: IconValidated },
  provisional: { label: 'Provisional', explain: 'AI-generated reference. Not yet checked by a person. Read it as a lead, not a finding.', cls: 'border-dashed border-prov-fg bg-prov-bg text-prov-fg', Icon: IconProvisional },
  pending: { label: 'Pending', explain: 'Not yet assessed. No claim is made either way.', cls: 'border-dotted border-unk-fg bg-unk-bg text-unk-fg', Icon: IconPending },
};

export function EvidenceStatusBadge({ status, detail, size = 'md' }: { status: EvidenceStatus; detail?: string; size?: 'sm' | 'md' }) {
  const s = SPEC[status];
  return (
    <Tooltip content={<span className="flex flex-col gap-1"><span className="font-semibold">{s.label}</span><span className="text-ink-muted">{s.explain}</span>{detail && <span className="text-ink-subtle">{detail}</span>}</span>}>
      <button
        type="button"
        aria-label={`Evidence: ${s.label}`}
        className={cx('inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border font-semibold', size === 'sm' ? 'h-6 px-2 text-xs' : 'h-7 px-2.5 text-sm', s.cls)}
      >
        <s.Icon size={size === 'sm' ? 12 : 14} />
        {s.label}
      </button>
    </Tooltip>
  );
}
