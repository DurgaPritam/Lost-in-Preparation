import type { ToxicityCategory, ToxicityRecord } from '../../types';
import { cx } from '../../lib/format';
import { Popover } from '../base/Popover';
import { IconConcern, IconLacking, IconNoReport, IconToxic, IconUnknown } from '../icons';

/**
 * Honesty 7 — toxicity as a compact pill; sources in a popover (click/tap,
 * so links work on touch). Only "Toxicity reported" is filled.
 * "No toxicity reported" is neutral — never green, never a tick — and its
 * popover says it is not evidence of safety.
 * ToxicityNotice replaces every call to action for reported/concern plants.
 */
const SPEC: Record<ToxicityCategory, { label: string; cls: string; Icon: typeof IconToxic; caveat?: string }> = {
  toxic_reported: { label: 'Toxicity reported', cls: 'bg-tox-solid text-tox-on-solid border-tox-solid', Icon: IconToxic },
  concern: { label: 'Toxicity concern', cls: 'bg-tox-bg text-tox-fg border-tox-fg', Icon: IconConcern },
  no_toxicity_reported: { label: 'No toxicity reported', cls: 'text-ink-muted border-border-strong', Icon: IconNoReport, caveat: 'No reports found in the sources checked. This is not evidence of safety.' },
  data_lacking: { label: 'Toxicity data lacking', cls: 'bg-hatch-lacking text-unk-fg border-unk-line', Icon: IconLacking, caveat: 'Too little data to assess.' },
  unknown: { label: 'Toxicity unknown', cls: 'bg-unk-bg text-unk-fg border-dashed border-unk-line', Icon: IconUnknown },
};

export function ToxicityBadge({ record, withSources = true }: { record: ToxicityRecord; withSources?: boolean }) {
  const s = SPEC[record.category];
  const pill = cx('inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 text-sm font-semibold', s.cls);
  if (!withSources) return <span className={pill}><s.Icon size={14} />{s.label}</span>;
  const n = record.sources.length;
  return (
    <Popover
      label={`${s.label}. ${n === 0 ? 'No sources recorded' : `${n} source${n > 1 ? 's' : ''}`}. Show details`}
      triggerClassName={pill}
      trigger={<><s.Icon size={14} />{s.label}<span className="font-normal">· {n}</span></>}
    >
      <div className="flex flex-col gap-2">
        <span className="font-semibold">{s.label}</span>
        {s.caveat && <p className="m-0 text-ink-muted">{s.caveat}</p>}
        {record.note && <p className="m-0">{record.note}</p>}
        {n > 0 ? (
          <ul className="m-0 flex list-disc flex-col gap-1 pl-4">
            {record.sources.map((src) => <li key={src.label}>{src.href ? <a href={src.href} className="text-brand underline underline-offset-2">{src.label}</a> : src.label}</li>)}
          </ul>
        ) : <p className="m-0 text-unk-fg">No sources recorded.</p>}
      </div>
    </Popover>
  );
}

export function ToxicityNotice({ record }: { record: ToxicityRecord }) {
  if (record.category !== 'toxic_reported' && record.category !== 'concern') return null;
  const strong = record.category === 'toxic_reported';
  return (
    <div role="note" className={cx('flex items-start gap-3 rounded-md border p-4 text-sm', strong ? 'border-tox-fg bg-tox-bg text-tox-fg' : 'border-dashed border-tox-fg text-tox-fg')}>
      {strong ? <IconToxic className="mt-0.5 shrink-0" /> : <IconConcern className="mt-0.5 shrink-0" />}
      <p className="m-0">
        {strong
          ? 'Toxicity is reported for this plant. Shown as a historical record for laboratory analysis only — not a preparation to make or take.'
          : 'A toxicity concern is recorded for this plant. Shown for analysis only.'}
      </p>
    </div>
  );
}
