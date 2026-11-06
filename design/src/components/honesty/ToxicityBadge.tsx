import { useId, useState } from 'react';
import type { ToxicityCategory, ToxicityRecord } from '../../types';
import { cx } from '../../lib/format';
import { IconConcern, IconLacking, IconNoReport, IconToxic, IconUnknown } from '../icons';

/**
 * Honesty treatment 7 — toxicity, with sources, and a hard rule:
 * toxic plants never look like something to try.
 *
 * - toxic_reported: the only FILLED, high-contrast badge in the system.
 * - concern: same red family, outline only.
 * - no_toxicity_reported: neutral outline. Deliberately NOT green, NOT a tick:
 *   absence of reports is not evidence of safety, and the copy says so.
 * - data_lacking: neutral hatch.
 * - unknown: the standard Unknown treatment.
 *
 * Sources open in a disclosure (not a hover tooltip) so links are clickable
 * and readable on touch. `ToxicityNotice` is the block that replaces any
 * call-to-action on cards and hypothesis rows for toxic_reported plants.
 */
const SPEC: Record<ToxicityCategory, { label: string; cls: string; Icon: typeof IconToxic; caveat?: string }> = {
  toxic_reported: { label: 'Toxicity reported', cls: 'bg-tox-solid text-tox-on-solid border-tox-solid', Icon: IconToxic },
  concern: { label: 'Toxicity concern', cls: 'bg-tox-bg text-tox-fg border-tox-fg', Icon: IconConcern },
  no_toxicity_reported: {
    label: 'No toxicity reported',
    cls: 'bg-surface text-ink-muted border-border-strong',
    Icon: IconNoReport,
    caveat: 'No reports found in the sources checked. This is not evidence of safety.',
  },
  data_lacking: {
    label: 'Toxicity data lacking',
    cls: 'bg-hatch-lacking text-unk-fg border-unk-line',
    Icon: IconLacking,
    caveat: 'Too little data to assess.',
  },
  unknown: { label: 'Toxicity unknown', cls: 'bg-unk-bg text-unk-fg border-dashed border-unk-line', Icon: IconUnknown },
};

export interface ToxicityBadgeProps {
  record: ToxicityRecord;
  /** Show the sources disclosure. */
  withSources?: boolean;
}

export function ToxicityBadge({ record, withSources = true }: ToxicityBadgeProps) {
  const s = SPEC[record.category];
  const id = useId();
  const [open, setOpen] = useState(false);
  const n = record.sources.length;
  return (
    <span className="inline-flex flex-col gap-1">
      <span className="inline-flex flex-wrap items-center gap-2">
        <span className={cx('inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-sm font-medium', s.cls)}>
          <s.Icon size={14} />
          {s.label}
        </span>
        {withSources && (
          <button
            type="button"
            aria-expanded={open}
            aria-controls={id}
            onClick={() => setOpen((o) => !o)}
            className="text-xs text-ink-muted underline underline-offset-2 hover:text-ink"
          >
            {n === 0 ? 'No sources' : `${n} source${n > 1 ? 's' : ''}`}
          </button>
        )}
      </span>
      {withSources && open && (
        <div id={id} className="flex max-w-prose flex-col gap-1 rounded border border-border bg-raised p-3 text-sm shadow-2">
          {s.caveat && <p className="m-0 text-ink-muted">{s.caveat}</p>}
          {record.note && <p className="m-0 text-ink">{record.note}</p>}
          {n > 0 ? (
            <ul className="m-0 flex list-none flex-col gap-1 p-0">
              {record.sources.map((src) => (
                <li key={src.label}>
                  {src.href ? (
                    <a href={src.href} className="text-mod-fg underline underline-offset-2">{src.label}</a>
                  ) : (
                    <span>{src.label}</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="m-0 text-unk-fg">No sources recorded.</p>
          )}
        </div>
      )}
    </span>
  );
}

/** Replaces any "explore / prepare / test" affordance for toxic_reported plants. */
export function ToxicityNotice({ record }: { record: ToxicityRecord }) {
  if (record.category !== 'toxic_reported' && record.category !== 'concern') return null;
  const strong = record.category === 'toxic_reported';
  return (
    <div
      role="note"
      className={cx(
        'flex items-start gap-2 rounded border p-3 text-sm',
        strong ? 'border-tox-fg bg-tox-bg text-tox-fg' : 'border-dashed border-tox-fg bg-surface text-tox-fg',
      )}
    >
      {strong ? <IconToxic className="mt-0.5 shrink-0" /> : <IconConcern className="mt-0.5 shrink-0" />}
      <p className="m-0">
        {strong
          ? 'Toxicity is reported for this plant. Shown as a historical record for analysis only — not a preparation to make or take.'
          : 'A toxicity concern is recorded for this plant. Shown for analysis only.'}
      </p>
    </div>
  );
}
