'use client';

import { Fragment, useState, type ReactNode } from 'react';
import type { ExtractedField, ExtractedFieldKind, Passage, Plate, Recipe, SourceConfidence } from '@/lib/types';
import { cx, FIELD_LABEL, HEAT_LABEL, SOURCE_LABEL, vehicleLabel } from '@/lib/data/format';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { LinkButton } from '@/components/base/Button';
import { PlateSlot } from '@/components/base/PlateSlot';
import { PrepTag } from '@/components/base/PrepTag';
import { Taxon } from '@/components/base/Taxon';
import { Tooltip } from '@/components/base/Tooltip';
import { DisputedName } from '@/components/honesty/DisputedName';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import Link from '@/components/base/Link';

/**
 * RECIPE PAGE (design v2 screens/Atlas.tsx RecipePage).
 * SITE: the passage is the real transcription. Quotes that overlap a span already drawn, or that come from the entry
 * heading, are listed in the field cards but not drawn in the passage (a span cannot overlap another); illegible stretches
 * keep their marker in the text and are drawn in place. Logged corrections (contract v1.6, P37a) are listed with their
 * evidence. Lab links are built only from the stated fields, one per species candidate with a profile, and none for a
 * plant with toxicity reported.
 */
const ALL_KINDS: ExtractedFieldKind[] = ['plant', 'part', 'freshOrDried', 'vehicle', 'heat', 'duration', 'filtration', 'process', 'form', 'indication'];

function PassageText({ passage, numbers, active, setActive }: { passage: Passage; numbers: Map<string, number>; active: string | null; setActive: (id: string | null) => void }) {
  type Seg = { kind: 'text'; s: string } | { kind: 'field'; f: ExtractedField } | { kind: 'ill'; id: string; s: string; est: number | null; note?: string };
  const drawn = passage.fields.filter((f) => f.inline);
  const cuts = [
    ...drawn.map((f) => ({ at: f.start, order: 1, seg: { kind: 'field', f } as Seg, end: f.end })),
    ...passage.illegible.map((i) => ({ at: i.at, order: 0, seg: { kind: 'ill', id: i.id, s: passage.text.slice(i.at, i.end), est: i.estChars, note: i.note } as Seg, end: i.end })),
  ].sort((a, b) => a.at - b.at || a.order - b.order);
  const segs: Seg[] = [];
  let pos = 0;
  for (const c of cuts) {
    if (c.at < pos) continue; // an illegible marker inside a drawn span is shown as part of that span
    if (c.at > pos) segs.push({ kind: 'text', s: passage.text.slice(pos, c.at) });
    segs.push(c.seg);
    pos = Math.max(pos, c.end);
  }
  if (pos < passage.text.length) segs.push({ kind: 'text', s: passage.text.slice(pos) });
  return (
    <p className="m-0 max-w-prose break-words font-display text-xl text-ink md:text-2xl">
      {segs.map((s, i) => {
        if (s.kind === 'text') return <Fragment key={i}>{s.s}</Fragment>;
        if (s.kind === 'ill') return (
          <Tooltip key={s.id} content={`Illegible${s.est != null ? `, about ${s.est} characters` : ', length unknown'}. ${s.note ?? ''}`}>
            <button type="button" aria-label="Illegible text" className="mx-0.5 inline-flex items-center rounded border border-dashed border-unk-line bg-unk-bg px-1.5 align-middle font-sans text-sm text-unk-fg">⟦?⟧</button>
          </Tooltip>
        );
        const n = numbers.get(s.f.id)!;
        return (
          <button
            key={s.f.id} type="button"
            aria-label={`Field ${n}: ${FIELD_LABEL[s.f.kind]}, “${passage.text.slice(s.f.start, s.f.end)}”`}
            onMouseEnter={() => setActive(s.f.id)} onMouseLeave={() => setActive(null)} onFocus={() => setActive(s.f.id)} onBlur={() => setActive(null)}
            className={cx('inline rounded bg-hist-bg px-1 text-left font-display text-xl text-ink underline decoration-hist-edge decoration-2 underline-offset-[6px] transition-shadow duration-fast md:text-2xl', active === s.f.id && 'outline outline-2 outline-ink')}
          >
            {passage.text.slice(s.f.start, s.f.end)}<sup className="ml-0.5 font-mono text-xs not-italic text-hist-fg">{n}</sup>
          </button>
        );
      })}
    </p>
  );
}

export interface RecipePageProps {
  recipe: Recipe;
  plate: Plate | null;
  confidence: SourceConfidence;
  labLinks: { taxon: string; href: string; index: number; of: number; stated: { solvent: boolean; heat: boolean; filtered: boolean } }[];
}

export function RecipePage({ recipe, plate, confidence, labLinks }: RecipePageProps) {
  const [active, setActive] = useState<string | null>(null);
  const p = recipe.passage;
  // Fields quoted from the entry heading (start = -1) are numbered after those in the passage.
  const ordered = [...p.fields].sort((a, b) => (a.start < 0 ? 1e9 : a.start) - (b.start < 0 ? 1e9 : b.start));
  const numbers = new Map(ordered.map((f, i) => [f.id, i + 1]));
  const missing = ALL_KINDS.filter((k) => !p.fields.some((f) => f.kind === k));
  const toxic = recipe.toxicity.category === 'toxic_reported';
  const taxon = recipe.name.candidates[0]?.taxon ?? '';
  const title: ReactNode = <><i>{recipe.name.historicalName}</i>{recipe.preparation.vehicle === 'unknown' ? ' · vehicle not stated' : ` in ${vehicleLabel(recipe.preparation.vehicle).toLowerCase()}`}</>;
  const statedNote = (l: RecipePageProps['labLinks'][number]) =>
    [!l.stated.solvent && 'solvent', !l.stated.heat && 'heat', !l.stated.filtered && 'filtration'].filter(Boolean).join(', ');

  return (
    <SiteShell current="atlas">
      <Link href="/atlas/" className="w-max text-sm text-ink-muted underline underline-offset-4">← Recipe Atlas</Link>
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="flex min-w-0 flex-col gap-6 lg:col-span-8">
          <PageHeader eyebrow={`Recipe · ${SOURCE_LABEL[recipe.source].full}`} title={title}>
            <div className="flex flex-wrap items-center gap-2">
              <SourceConfidenceMarker confidence={confidence} />
              <EvidenceStatusBadge status={recipe.evidence} detail={recipe.provenance} />
              <ToxicityBadge record={recipe.toxicity} />
            </div>
          </PageHeader>
          <ToxicityNotice record={recipe.toxicity} />

          <section aria-labelledby="passage" className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-6 shadow-1 md:p-8">
            <h2 id="passage" className="eyebrow m-0 text-ink-subtle">Original passage</h2>
            <PassageText passage={p} numbers={numbers} active={active} setActive={setActive} />
            <p className="m-0 text-xs text-ink-subtle">{p.edition} · {p.locator}</p>
            <div className="flex flex-wrap gap-x-5 gap-y-2 border-t border-border pt-3 text-sm text-ink-muted">
              <span className="inline-flex items-center gap-2"><span aria-hidden className="inline-block h-3 w-6 rounded border-b-2 border-hist-edge bg-hist-bg" />Extracted field (numbered)</span>
              <span className="inline-flex items-center gap-2"><span aria-hidden className="rounded border border-dashed border-unk-line bg-unk-bg px-1 text-xs text-unk-fg">⟦?⟧</span>Illegible in source</span>
            </div>
          </section>

          <section aria-labelledby="fields" className="flex flex-col gap-3">
            <h2 id="fields" className="m-0 font-display text-2xl text-ink">What the pipeline extracted</h2>
            <ol className="m-0 grid list-none grid-cols-1 gap-2 p-0 sm:grid-cols-2">
              {ordered.map((f) => (
                <li key={f.id} onMouseEnter={() => setActive(f.id)} onMouseLeave={() => setActive(null)} className={cx('flex min-w-0 flex-col gap-1.5 rounded-md border p-3 transition-colors duration-fast', active === f.id ? 'border-hist-edge bg-hist-bg' : 'border-border bg-surface')}>
                  <span className="flex items-center justify-between gap-2">
                    <span className="flex items-baseline gap-2"><span className="font-mono text-xs text-hist-fg">{numbers.get(f.id)}</span><span className="eyebrow text-ink-subtle">{FIELD_LABEL[f.kind]}</span></span>
                    <EvidenceStatusBadge status={f.evidence} size="sm" />
                  </span>
                  <span className="break-words text-base text-ink">{f.value ?? <UnknownValue label="Could not normalise" />}</span>
                  <span className="break-words font-display text-md italic text-ink-muted">“{f.quote}”{f.start < 0 && <span className="not-italic text-xs text-ink-subtle"> (from the entry heading)</span>}</span>
                </li>
              ))}
              {missing.map((k) => (
                <li key={k} className="flex flex-col gap-1.5 rounded-md border border-dashed border-unk-line p-3">
                  <span className="eyebrow text-ink-subtle">{FIELD_LABEL[k]}</span>
                  <UnknownValue label="Not stated in source" />
                </li>
              ))}
            </ol>
          </section>

          {recipe.corrections.length > 0 && (
            <section aria-labelledby="corrections" className="flex flex-col gap-3">
              <h2 id="corrections" className="m-0 font-display text-2xl text-ink">Logged corrections</h2>
              <p className="m-0 max-w-prose text-sm text-ink-muted">The fields above are as extracted. These corrections, each with its evidence, are applied in the audit and the ranking (<code className="font-mono text-xs">config/m1_corrections.csv</code>).</p>
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {recipe.corrections.map((c, i) => (
                  <li key={i} className="flex min-w-0 flex-col gap-1 rounded-md border border-border bg-surface p-3 text-sm">
                    <span className="font-semibold text-ink">{FIELD_LABEL[c.field as ExtractedFieldKind] ?? c.field}: <span className="font-mono">{c.from}</span> → <span className="font-mono">{c.to}</span></span>
                    <span className="break-words text-ink-muted">{c.reason}</span>
                    <span className="break-words text-xs text-ink-subtle">Evidence: {c.evidence}</span>
                    <span className="text-xs text-ink-subtle">Requested by {c.requestedBy}; {c.date}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <aside className="flex min-w-0 flex-col gap-6 lg:col-span-4">
          <PlateSlot taxon={taxon || recipe.name.historicalName} plate={plate} size="hero" className="hidden lg:flex" />
          <section aria-labelledby="species" className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5 shadow-1">
            <h2 id="species" className="eyebrow m-0 text-ink-subtle">Species</h2>
            <DisputedName resolution={recipe.name} />
          </section>
          <section aria-labelledby="prep" className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5 shadow-1">
            <h2 id="prep" className="eyebrow m-0 text-ink-subtle">Preparation</h2>
            <PrepTag prep={recipe.preparation} />
            <span className="text-sm text-ink-muted">Heat: {recipe.preparation.heat ? HEAT_LABEL[recipe.preparation.heat] : <UnknownValue label="not stated" />}</span>
            {toxic ? null : recipe.name.state === 'disputed' ? (
              <div className="flex flex-col gap-1 text-sm">
                <span className="text-ink-muted">Disputed name — compare each candidate separately:</span>
                {recipe.name.candidates.map((c, i) => {
                  const l = labLinks.find((x) => x.taxon === c.taxon);
                  return l
                    ? <Link key={c.taxon} href={l.href} className="text-brand underline underline-offset-4"><Taxon name={c.taxon} /> · candidate {i + 1} of {recipe.name.candidates.length} →</Link>
                    : <UnknownValue key={c.taxon} label={`${c.rank === 'genus' ? `${c.taxon} sp.` : c.taxon} · no Lab profile`} />;
                })}
              </div>
            ) : labLinks[0] ? (
              <div className="flex flex-col gap-1.5">
                <LinkButton href={labLinks[0].href} variant="primary" className="w-max">Open this preparation in the Lab</LinkButton>
                {statedNote(labLinks[0]) && <span className="text-xs text-ink-subtle">Not stated in the recipe, so the Lab starts from its default: {statedNote(labLinks[0])}.</span>}
              </div>
            ) : <UnknownValue label="No Lab profile for this plant" />}
          </section>
        </aside>
      </div>
    </SiteShell>
  );
}
