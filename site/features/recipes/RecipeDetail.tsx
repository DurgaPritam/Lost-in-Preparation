'use client';

import { Fragment, useState, type ReactNode } from 'react';
import Link from '@/components/base/Link';
import type { ExtractedField, ExtractedFieldKind, Passage, Recipe, SourceConfidence, SourceWork } from '@/lib/types';
import { FIELD_LABEL, SOURCE_LABEL, cx, vehicleLabel } from '@/lib/data/format';
import { AppShell } from '@/components/layout/AppShell';
import { PrepTag } from '@/components/base/PrepTag';
import { Tooltip } from '@/components/base/Tooltip';
import { DisputedName } from '@/components/honesty/DisputedName';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * RECIPE DETAIL — the passage is the primary object.
 * Every extracted field is a numbered span in the passage AND a numbered row
 * in the fields table; hovering or focusing either highlights both.
 * Illegible stretches render as ⟦?⟧ in the neutral unknown style, never
 * silently closed up. Fields the passage doesn't state are listed as
 * "Not stated in source" rather than omitted.
 */
/** SITE: the fields M1 extracts (it never extracts quantity, so quantity is not listed as "not stated"). */
const ALL_KINDS: ExtractedFieldKind[] = ['plant', 'part', 'freshOrDried', 'vehicle', 'heat', 'duration', 'filtration', 'process', 'form', 'indication'];

function PassageText({ passage, numbers, active, setActive }: {
  passage: Passage; numbers: Map<string, number>; active: string | null; setActive: (id: string | null) => void;
}) {
  type Seg = { kind: 'text'; s: string } | { kind: 'field'; f: ExtractedField } | { kind: 'ill'; id: string; s: string; est: number | null; note?: string };
  // SITE: only non-overlapping spans are drawn (overlapping quotes stay in the table); the transcription keeps its
  // illegible markers in the text, so an illegible span replaces exactly those characters.
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
  const within = (f: ExtractedField) => passage.fields.filter((g) => g.start >= f.start && g.end <= f.end && g.start >= 0)
    .map((g) => numbers.get(g.id)!).sort((a, b) => a - b);

  return (
    <p className="m-0 max-w-prose font-serif text-lg text-ink">
      {segs.map((s, i) => {
        if (s.kind === 'text') return <Fragment key={i}>{s.s}</Fragment>;
        if (s.kind === 'ill')
          return (
            <Tooltip key={s.id} content={`Illegible${s.est != null ? `, about ${s.est} characters` : ', length unknown'}. ${s.note ?? ''}`}>
              <button type="button" aria-label="Illegible text" className="mx-0.5 inline-flex items-center rounded-sm border border-dashed border-unk-line bg-unk-bg px-1 font-sans text-sm text-unk-fg">
                {s.s}
              </button>
            </Tooltip>
          );
        const ns = within(s.f);
        const on = ns.some((n) => [...numbers.entries()].find(([, v]) => v === n)?.[0] === active);
        return (
          <button
            key={s.f.id}
            type="button"
            aria-label={`Field${ns.length > 1 ? 's' : ''} ${ns.join(', ')}: ${passage.fields.filter((g) => ns.includes(numbers.get(g.id)!)).map((g) => FIELD_LABEL[g.kind]).join(', ')}, “${passage.text.slice(s.f.start, s.f.end)}”`}
            aria-describedby={`row-${s.f.id}`}
            onMouseEnter={() => setActive(s.f.id)}
            onMouseLeave={() => setActive(null)}
            onFocus={() => setActive(s.f.id)}
            onBlur={() => setActive(null)}
            className={cx(
              'inline rounded-sm border-b-2 border-hist-fg bg-hist-bg px-0.5 text-left font-serif text-lg text-ink',
              on && 'outline outline-2 outline-ink',
            )}
          >
            {passage.text.slice(s.f.start, s.f.end)}
            <sup className="ml-0.5 font-mono text-xs text-hist-fg">{ns.join(',')}</sup>
          </button>
        );
      })}
    </p>
  );
}

export function RecipeDetail({ recipe, confidences, profiled }: {
  recipe: Recipe; confidences: Record<SourceWork, SourceConfidence>; profiled: Record<string, string>;
}) {
  const [active, setActive] = useState<string | null>(null);
  const p = recipe.passage;
  // SITE: fields quoted from the entry heading (start = -1) are numbered after those in the passage.
  const ordered = [...p.fields].sort((a, b) => (a.start < 0 ? 1e9 : a.start) - (b.start < 0 ? 1e9 : b.start));
  const compareHref = (taxon: string) => (profiled[taxon] ? `/compare/?species=${encodeURIComponent(profiled[taxon])}` : null);
  const numbers = new Map(ordered.map((f, i) => [f.id, i + 1]));
  const missing = ALL_KINDS.filter((k) => !p.fields.some((f) => f.kind === k));
  const toxic = recipe.toxicity.category === 'toxic_reported';
  const comparable = recipe.name.state === 'resolved' && !toxic && !!recipe.name.candidates[0] && !!compareHref(recipe.name.candidates[0].taxon);
  const title: ReactNode = (
    <>
      <span className="italic">{recipe.name.historicalName}</span>{recipe.preparation.vehicle === 'unknown' ? ' · vehicle not stated' : ` in ${vehicleLabel(recipe.preparation.vehicle).toLowerCase()}`}
    </>
  );

  return (
    <AppShell current="recipes">
      <div className="flex flex-col gap-3">
        <Link href="/recipes/" className="w-max text-sm text-ink-muted underline underline-offset-2">
          ← All recipes
        </Link>
        <span className="small-caps text-xs text-ink-subtle">Recipe · {SOURCE_LABEL[recipe.source].full}</span>
        <h2 className="m-0 font-serif text-2xl font-medium">{title}</h2>
        <div className="flex flex-wrap items-center gap-2">
          <SourceConfidenceMarker confidence={confidences[recipe.source]} />
          <EvidenceStatusBadge status={recipe.evidence} detail={`Extracted by ${recipe.provenance}.`} />
          <ToxicityBadge record={recipe.toxicity} />
        </div>
        <ToxicityNotice record={recipe.toxicity} />
        {recipe.excludedFromHeadline && (
          <p className="m-0 text-sm text-ink-muted">Compound recipe: stored with the others but excluded from the headline analysis, because a mixture’s chemistry can’t be attributed to one plant.</p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section aria-labelledby="passage" className="flex flex-col gap-3">
          <h3 id="passage" className="m-0 text-lg font-semibold">Original passage</h3>
          <figure className="m-0 flex flex-col gap-3 rounded border border-border bg-surface p-5">
            <PassageText passage={p} numbers={numbers} active={active} setActive={setActive} />
            <figcaption className="flex flex-col gap-1 border-t border-border pt-3 text-xs text-ink-subtle">
              <span>{p.edition}</span>
              <span>{p.locator}</span>
            </figcaption>
          </figure>
          <div className="flex flex-wrap items-center gap-4 text-sm text-ink-muted">
            <span className="inline-flex items-center gap-1.5">
              <span aria-hidden className="inline-block h-3 w-6 rounded-sm border-b-2 border-hist-fg bg-hist-bg" /> Extracted field (numbered)
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span aria-hidden className="rounded-sm border border-dashed border-unk-line bg-unk-bg px-1 text-xs text-unk-fg">⟦?⟧</span> Illegible in source
            </span>
          </div>
        </section>

        <section aria-labelledby="fields" className="flex flex-col gap-3">
          <h3 id="fields" className="m-0 text-lg font-semibold">Extracted fields</h3>
          <div className="overflow-x-auto rounded border border-border bg-surface">
            <table className="w-full border-collapse text-sm">
              <caption className="sr-only">Fields extracted from the passage, numbered as in the text</caption>
              <thead className="bg-sunken">
                <tr className="text-left">
                  <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">#</th>
                  <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">Field</th>
                  {/* Phase 4: below 640px "As written" (already highlighted in the passage) is hidden and the
                      evidence badge moves under the normalised value, so no column sits off-screen. */}
                  <th scope="col" className="hidden border-b border-border-strong px-3 py-2 font-medium sm:table-cell">As written</th>
                  <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">Normalised<span className="font-normal sm:hidden"> · evidence</span></th>
                  <th scope="col" className="hidden border-b border-border-strong px-3 py-2 font-medium sm:table-cell">Evidence</th>
                </tr>
              </thead>
              <tbody>
                {ordered.map((f) => (
                  <tr
                    key={f.id}
                    id={`row-${f.id}`}
                    onMouseEnter={() => setActive(f.id)}
                    onMouseLeave={() => setActive(null)}
                    className={cx('border-b border-border', active === f.id && 'bg-hist-bg')}
                  >
                    <td className="num px-3 py-2 font-mono text-hist-fg">{numbers.get(f.id)}</td>
                    <td className="px-3 py-2">{FIELD_LABEL[f.kind]}</td>
                    <td className="hidden px-3 py-2 font-serif text-base italic sm:table-cell">{f.quote}{f.start < 0 && <span className="font-sans text-xs not-italic text-ink-subtle"> (entry heading)</span>}</td>
                    <td className="px-3 py-2">
                      <span className="flex flex-col items-start gap-1">
                        {f.value ?? <UnknownValue label="Could not normalise" />}
                        <span className="sm:hidden"><EvidenceStatusBadge status={f.evidence} size="sm" /></span>
                      </span>
                    </td>
                    <td className="hidden px-3 py-2 sm:table-cell"><EvidenceStatusBadge status={f.evidence} size="sm" /></td>
                  </tr>
                ))}
                {missing.map((k) => (
                  <tr key={k} className="border-b border-border last:border-b-0">
                    <td className="px-3 py-2"><span className="sr-only">Not in passage</span></td>
                    <td className="px-3 py-2">{FIELD_LABEL[k]}</td>
                    <td className="hidden sm:table-cell" />
                    <td className="px-3 py-2"><UnknownValue label="Not stated in source" /></td>
                    <td className="hidden sm:table-cell" />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3 className="m-0 mt-2 text-lg font-semibold">Species</h3>
          <div className="rounded border border-border bg-surface p-5">
            <DisputedName resolution={recipe.name} />
          </div>

          <h3 className="m-0 mt-2 text-lg font-semibold">Preparation</h3>
          <div className="flex flex-wrap items-center gap-2">
            <PrepTag prep={recipe.preparation} />
          </div>
          {comparable && (
            <Link href={compareHref(recipe.name.candidates[0].taxon)!} className="w-max text-base font-medium text-ink underline underline-offset-4">
              Compare with modern preparations →
            </Link>
          )}
          {!toxic && recipe.name.state === 'resolved' && !comparable && (
            <p className="m-0 text-sm text-ink-muted">This species is not in the study set, so it has no extraction profile to compare.</p>
          )}
          {/* Phase 4: disputed names now get one Compare link per species-level candidate (as designed), never one merged link. */}
          {!toxic && recipe.name.state === 'disputed' && (
            <div className="flex flex-col gap-1.5">
              <p className="m-0 text-sm text-ink-muted">The name is disputed, so there is no single species to compare. Compare each candidate separately:</p>
              <ul className="m-0 flex list-none flex-col gap-1 p-0">
                {recipe.name.candidates.map((c, i) => (
                  <li key={c.taxon}>
                    {c.rank === 'species' && compareHref(c.taxon) ? (
                      <Link href={compareHref(c.taxon)!} className="text-base font-medium text-ink underline underline-offset-4">
                        <span className="italic">{c.taxon}</span> · candidate {i + 1} of {recipe.name.candidates.length} →
                      </Link>
                    ) : c.rank === 'species' ? (
                      <UnknownValue label={`${c.taxon} · candidate ${i + 1} of ${recipe.name.candidates.length} · not in the study set, no profile`} />
                    ) : (
                      <UnknownValue label={`${c.taxon} sp. · no species-level profile`} />
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {!toxic && recipe.name.state === 'genus_only' && (
            <p className="m-0 text-sm text-ink-muted">Resolved to genus only, so there is no species-level profile to compare.</p>
          )}
          {!toxic && recipe.name.state === 'unresolved' && (
            <p className="m-0 text-sm text-ink-muted">The name is unresolved, so there is nothing to compare.</p>
          )}
        </section>
      </div>

      {/* SITE (new, design components only): logged corrections, contract v1.6 P37a. */}
      {recipe.corrections.length > 0 && (
        <section aria-labelledby="corrections" className="flex flex-col gap-3">
          <h3 id="corrections" className="m-0 text-lg font-semibold">Logged corrections</h3>
          <p className="m-0 max-w-prose text-sm text-ink-muted">
            The fields above are shown as extracted. These corrections, requested by the project lead with the evidence below, are applied in the
            Phase 5 pairs and Phase 6 ranking. See <Link href="/case-studies/liquorice/" className="text-ink underline underline-offset-2">the liquorice case study</Link>.
          </p>
          <div className="overflow-x-auto rounded border border-border bg-surface" tabIndex={0} role="region" aria-label="Logged corrections (scrolls sideways)">
            <table className="w-full border-collapse text-sm">
              <caption className="sr-only">Logged corrections to this recipe</caption>
              <thead className="bg-sunken">
                <tr className="text-left">
                  <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">Field</th>
                  <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">As extracted</th>
                  <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">Corrected to</th>
                  <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">Reason and evidence</th>
                </tr>
              </thead>
              <tbody>
                {recipe.corrections.map((c) => (
                  <tr key={c.field} className="border-b border-border last:border-b-0 align-top">
                    <th scope="row" className="px-3 py-2 text-left font-medium">{c.field}</th>
                    <td className="px-3 py-2 font-mono">{c.from}</td>
                    <td className="px-3 py-2 font-mono">{c.to}</td>
                    <td className="px-3 py-2"><span className="flex flex-col gap-1"><span>{c.reason}</span><span className="text-xs text-ink-subtle">{c.evidence}</span><span className="text-xs text-ink-subtle">Requested by {c.requestedBy}; applied by {c.appliedBy}; {c.date}</span></span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </AppShell>
  );
}
