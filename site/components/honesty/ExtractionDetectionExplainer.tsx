import { cx } from '@/lib/data/format';
import { IconInfo } from '../icons';

/**
 * Honesty treatment 5 — the model predicts extraction, not detection.
 *
 * Two forms:
 * - `variant="inline"`: one sentence + disclosure, placed under any chart or
 *   table of extraction likelihoods.
 * - `variant="panel"`: a three-step chain for Methods and first-run help.
 *   Step 2 (what we model) is the only solid box; steps 1 and 3 are dashed to
 *   show they are outside the model.
 */
export interface ExtractionDetectionExplainerProps {
  variant?: 'inline' | 'panel';
}

const STEPS = [
  {
    k: 'Plant content',
    body: 'How much of the compound the plant material held. Varies with species, part, season, storage. Not modelled.',
    inModel: false,
  },
  {
    k: 'Extraction',
    body: 'Whether the preparation (vehicle, heat, time, filtering) would carry the compound into the liquid. This is what we estimate.',
    inModel: true,
  },
  {
    k: 'Lab detection',
    body: 'Whether an assay would find it. Depends on content, extraction AND the method’s limit of detection. Not predicted.',
    inModel: false,
  },
];

export function ExtractionDetectionExplainer({ variant = 'inline' }: ExtractionDetectionExplainerProps) {
  if (variant === 'inline') {
    return (
      <details className="group text-sm text-ink-muted">
        <summary className="inline-flex cursor-pointer list-none items-center gap-1.5">
          <IconInfo size={14} />
          <span>
            These are <strong className="font-medium text-ink">predicted extraction</strong> likelihoods, not lab detection.
          </span>
          <span className="underline underline-offset-2">Why it matters</span>
        </summary>
        <p className="mb-0 mt-2 max-w-prose">
          A compound can be extracted and still go undetected if the plant held little of it, or if the assay is not
          sensitive enough. Read a high value as “this preparation would plausibly carry it”, never as “it was present”.
        </p>
      </details>
    );
  }
  return (
    <section aria-labelledby="xd-title" className="flex flex-col gap-3 rounded border border-border bg-surface p-5">
      <h3 id="xd-title" className="m-0 text-base font-semibold text-ink">
        Extraction is not detection
      </h3>
      <ol className="m-0 grid list-none grid-cols-1 gap-3 p-0 md:grid-cols-3">
        {STEPS.map((s, i) => (
          <li
            key={s.k}
            className={cx(
              'flex flex-col gap-1 rounded border p-3',
              s.inModel ? 'border-ink bg-raised' : 'border-dashed border-border-strong bg-transparent',
            )}
          >
            <span className="small-caps text-xs text-ink-subtle">
              Step {i + 1} · {s.inModel ? 'modelled' : 'outside the model'}
            </span>
            <span className="text-base font-medium text-ink">{s.k}</span>
            <span className="text-sm text-ink-muted">{s.body}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
