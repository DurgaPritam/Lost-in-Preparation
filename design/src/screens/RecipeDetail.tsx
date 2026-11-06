import { Fragment, useState, type ReactNode } from 'react';
import type { ExtractedField, ExtractedFieldKind, Passage, Recipe } from '../types';
import {
  AppShell, DisputedName, EvidenceStatusBadge, PrepTag, SourceConfidenceMarker, ToxicityBadge, ToxicityNotice,
  Tooltip, UnknownValue, FIELD_LABEL, SOURCE_LABEL, VEHICLE_LABEL, cx,
} from '../index';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';

/**
 * RECIPE DETAIL — the passage is the primary object.
 * Every extracted field is a numbered span in the passage AND a numbered row
 * in the fields table; hovering or focusing either highlights both.
 * Illegible stretches render as ⟦?⟧ in the neutral unknown style, never
 * silently closed up. Fields the passage doesn't state are listed as
 * "Not stated in source" rather than omitted.
 */
const ALL_KINDS: ExtractedFieldKind[] = ['plant', 'part', 'quantity', 'vehicle', 'heat', 'duration', 'filtration'];

function PassageText({ passage, numbers, active, setActive }: {
  passage: Passage; numbers: Map<string, number>; active: string | null; setActive: (id: string | null) => void;
}) {
  type Seg = { kind: 'text'; s: string } | { kind: 'field'; f: ExtractedField } | { kind: 'ill'; id: string; est: number | null; note?: string };
  const cuts = [
    ...passage.fields.map((f) => ({ at: f.start, order: 1, seg: { kind: 'field', f } as Seg, end: f.end })),
    ...passage.illegible.map((i) => ({ at: i.at, order: 0, seg: { kind: 'ill', id: i.id, est: i.estChars, note: i.note } as Seg, end: i.at })),
  ].sort((a, b) => a.at - b.at || a.order - b.order);
  const segs: Seg[] = [];
  let pos = 0;
  for (const c of cuts) {
    if (c.at > pos) segs.push({ kind: 'text', s: passage.text.slice(pos, c.at) });
    segs.push(c.seg);
    pos = Math.max(pos, c.end);
  }
  if (pos < passage.text.length) segs.push({ kind: 'text', s: passage.text.slice(pos) });

  return (
    <p className="m-0 max-w-prose font-serif text-lg text-ink">
      {segs.map((s, i) => {
        if (s.kind === 'text') return <Fragment key={i}>{s.s}</Fragment>;
        if (s.kind === 'ill')
          return (
            <Tooltip key={s.id} content={`Illegible${s.est != null ? `, about ${s.est} characters` : ', length unknown'}. ${s.note ?? ''}`}>
              <button type="button" aria-label="Illegible text" className="mx-0.5 inline-flex items-center rounded-sm border border-dashed border-unk-line bg-unk-bg px-1 font-sans text-sm text-unk-fg">
                ⟦?⟧
              </button>
            </Tooltip>
          );
        const n = numbers.get(s.f.id)!;
        const on = active === s.f.id;
        return (
          <button
            key={s.f.id}
            type="button"
            aria-label={`Field ${n}: ${FIELD_LABEL[s.f.kind]}, “${passage.text.slice(s.f.start, s.f.end)}”`}
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
            <sup className="ml-0.5 font-mono text-xs text-hist-fg">{n}</sup>
          </button>
        );
      })}
    </p>
  );
}

export function RecipeDetail({ recipe, onBack, onCompare, onNavigate }: {
  recipe: Recipe; onBack?: () => void; onCompare?: (taxon: string) => void; onNavigate?: (p: string) => void;
}) {
  const [active, setActive] = useState<string | null>(null);
  const p = recipe.passage;
  const ordered = [...p.fields].sort((a, b) => a.start - b.start);
  const numbers = new Map(ordered.map((f, i) => [f.id, i + 1]));
  const missing = ALL_KINDS.filter((k) => !p.fields.some((f) => f.kind === k));
  const toxic = recipe.toxicity.category === 'toxic_reported';
  const comparable = recipe.name.state === 'resolved' && !toxic;
  const title: ReactNode = (
    <>
      <span className="italic">{recipe.name.historicalName}</span> in {VEHICLE_LABEL[recipe.preparation.vehicle].toLowerCase()}
    </>
  );

  return (
    <AppShell current="recipes" onNavigate={onNavigate}>
      <div className="flex flex-col gap-3">
        <a href="/recipes" onClick={onBack ? (e) => { e.preventDefault(); onBack(); } : undefined} className="w-max text-sm text-ink-muted underline underline-offset-2">
          ← All recipes
        </a>
        <span className="small-caps text-xs text-ink-subtle">Recipe · {SOURCE_LABEL[recipe.source].full}</span>
        <h2 className="m-0 font-serif text-2xl font-medium">{title}</h2>
        <div className="flex flex-wrap items-center gap-2">
          <SourceConfidenceMarker confidence={recipe.source === 'pliny_nh' ? sourcePliny : sourceCulpeper} />
          <EvidenceStatusBadge status={recipe.evidence} />
          <ToxicityBadge record={recipe.toxicity} />
        </div>
        <ToxicityNotice record={recipe.toxicity} />
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
                    <td className="hidden px-3 py-2 font-serif text-base italic sm:table-cell">{p.text.slice(f.start, f.end)}</td>
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
            <a
              href={`/compare?species=${encodeURIComponent(recipe.name.candidates[0].taxon)}`}
              onClick={onCompare ? (e) => { e.preventDefault(); onCompare(recipe.name.candidates[0].taxon); } : undefined}
              className="w-max text-base font-medium text-ink underline underline-offset-4"
            >
              Compare with modern preparations →
            </a>
          )}
          {/* Phase 4: disputed names now get one Compare link per species-level candidate (as designed), never one merged link. */}
          {!toxic && recipe.name.state === 'disputed' && (
            <div className="flex flex-col gap-1.5">
              <p className="m-0 text-sm text-ink-muted">The name is disputed, so there is no single species to compare. Compare each candidate separately:</p>
              <ul className="m-0 flex list-none flex-col gap-1 p-0">
                {recipe.name.candidates.map((c, i) => (
                  <li key={c.taxon}>
                    {c.rank === 'species' ? (
                      <a
                        href={`/compare?species=${encodeURIComponent(c.taxon)}`}
                        onClick={onCompare ? (e) => { e.preventDefault(); onCompare(c.taxon); } : undefined}
                        className="text-base font-medium text-ink underline underline-offset-4"
                      >
                        <span className="italic">{c.taxon}</span> · candidate {i + 1} of {recipe.name.candidates.length} →
                      </a>
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
    </AppShell>
  );
}
