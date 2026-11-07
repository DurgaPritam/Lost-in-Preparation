import { cx } from '@/lib/data/format';
import { Popover } from '../base/Popover';
import { IconInfo } from '../icons';

/**
 * Honesty 5 — the model predicts EXTRACTION, not lab DETECTION.
 * - `chip` (default): a compact pill that opens a 3-step explanation. Place
 *   it beside every set of likelihood bars.
 * - `panel`: the full three-step chain, for Methods and the case study.
 * Only step 2 is drawn solid: it is the only step we model.
 */
const STEPS = [
  { k: 'Plant content', body: 'How much the plant held. Varies by species, part, season, storage.', inModel: false },
  { k: 'Extraction', body: 'Whether the preparation would carry it into the liquid. This is what we estimate.', inModel: true },
  { k: 'Lab detection', body: 'Whether an assay would find it. Also depends on content and the method’s limit of detection.', inModel: false },
];

function Steps({ compact }: { compact?: boolean }) {
  return (
    <ol className={cx('m-0 grid list-none gap-2 p-0', compact ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-3 md:gap-3')}>
      {STEPS.map((s, i) => (
        <li key={s.k} className={cx('flex flex-col gap-0.5 rounded-md border p-3', s.inModel ? 'border-ink bg-surface' : 'border-dashed border-border-strong')}>
          <span className="eyebrow text-ink-subtle">{i + 1} · {s.inModel ? 'modelled' : 'outside the model'}</span>
          <span className="font-semibold text-ink">{s.k}</span>
          <span className="text-sm text-ink-muted">{s.body}</span>
        </li>
      ))}
    </ol>
  );
}

export function ExtractionDetectionExplainer({ variant = 'chip' }: { variant?: 'chip' | 'panel' }) {
  if (variant === 'panel') {
    return (
      <section aria-labelledby="xd" className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5">
        <h3 id="xd" className="m-0 font-display text-xl text-ink">Extraction is not detection</h3>
        <Steps />
      </section>
    );
  }
  return (
    <Popover
      label="Extraction is not detection: what these bars mean"
      triggerClassName="inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-full border border-border-strong px-2.5 text-sm text-ink-muted hover:text-ink"
      trigger={<><IconInfo size={14} />Extraction ≠ detection</>}
    >
      <div className="flex w-full flex-col gap-3">
        <p className="m-0">These bars predict whether a preparation would <strong className="font-semibold">extract</strong> each compound — not whether a lab would <strong className="font-semibold">detect</strong> it.</p>
        <Steps compact />
      </div>
    </Popover>
  );
}
