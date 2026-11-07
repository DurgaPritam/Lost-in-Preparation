import type { EvidenceStatus, ValidationStatus } from '@/lib/types';
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

/** SITE: validation wording for Methods & data, so each validation item reads one of three plain statuses (project lead,
 *  2026-11-07). Shape, border and colour are the design's; only the word and explanation change. */
const VALIDATION_WORDING: Record<ValidationStatus, { label: string; explain: string }> = {
  validated: { label: 'Human-validated', explain: 'Checked by a person against the cited reference.' },
  external: { label: 'Validated against external data', explain: 'Compared with an independent, published dataset (for example measured experimental values). No AI-made reference is involved.' },
  provisional: { label: 'AI-assisted check (provisional)', explain: 'Checked by an AI, or against a reference an AI made. Useful for finding problems; never a validation.' },
  pending: { label: 'Human validation pending', explain: 'No independent check yet. No claim is made either way.' },
};

export function EvidenceStatusBadge({ status, detail, size = 'md', wording = 'evidence' }: { status: ValidationStatus; detail?: string; size?: 'sm' | 'md'; wording?: 'evidence' | 'validation' }) {
  // 'external' keeps the design's solid "validated" shape; the word (and brand border) tells it apart from a person's check.
  const base = status === 'external' ? { ...SPEC.validated, cls: 'border-brand text-brand' } : SPEC[status];
  const s = wording === 'validation' || status === 'external' ? { ...base, ...VALIDATION_WORDING[status] } : base;
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
