import { Fragment, useMemo, useState, type MouseEvent } from 'react';
import type { ExtractedField, ExtractedFieldKind, Passage, Recipe } from '../types';
import {
  EmptyState, EvidenceStatusBadge, LinkButton, PageHeader, PlantCard, PlateSlot, PrepTag, SiteShell, SourceConfidenceMarker,
  ToxicityBadge, ToxicityNotice, Tooltip, UnknownValue, DisputedName, Taxon, cx, FIELD_LABEL, HEAT_LABEL, SOURCE_LABEL, VEHICLE_LABEL,
} from '../index';
import { plates, recipes as RECIPES } from '../contract';
import { LAB_PLANTS } from '../contract/lab';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';
import { IconSearch } from '../components/icons';

/**
 * RECIPE ATLAS — search first, then plant cards with plates, then recipes.
 * A recipe page shows the original passage with every extracted field as a
 * highlighted, numbered span, illegible text as ⟦?⟧, and disputed names as
 * an elegant expandable list.
 */
const COMMON: Record<string, string> = {
  'Glycyrrhiza glabra': 'Liquorice', 'Artemisia absinthium': 'Wormwood', 'Salvia officinalis': 'Sage', 'Conium maculatum': 'Hemlock', Mentha: 'Mint',
};
const plantKey = (r: Recipe) => (r.name.state === 'disputed' ? `“${r.name.historicalName}”` : r.name.candidates[0]?.taxon ?? r.name.historicalName);
type Chip = 'culpeper' | 'pliny' | 'disputed' | 'heat-stated' | 'strained';
const CHIPS: { id: Chip; label: string }[] = [
  { id: 'culpeper', label: 'Culpeper' }, { id: 'pliny', label: 'Pliny' }, { id: 'disputed', label: 'Disputed names' },
  { id: 'heat-stated', label: 'Heat stated' }, { id: 'strained', label: 'Strained' },
];

export function Atlas({ onNavigate, recipes = RECIPES }: { onNavigate?: (p: string) => void; recipes?: Recipe[] }) {
  const [q, setQ] = useState('');
  const [chips, setChips] = useState<Chip[]>([]);
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); onNavigate(path); } };
  const toggle = (c: Chip) => setChips((cs) => (cs.includes(c) ? cs.filter((x) => x !== c) : [...cs, c]));

  const shown = recipes.filter((r) => {
    const hay = [r.name.historicalName, ...r.name.candidates.map((c) => c.taxon), COMMON[r.name.candidates[0]?.taxon ?? ''] ?? '', r.passage.text, VEHICLE_LABEL[r.preparation.vehicle]].join(' ').toLowerCase();
    if (q.trim() && !hay.includes(q.trim().toLowerCase())) return false;
    if (chips.includes('culpeper') && !chips.includes('pliny') && r.source !== 'culpeper_1652') return false;
    if (chips.includes('pliny') && !chips.includes('culpeper') && r.source !== 'pliny_nh') return false;
    if (chips.includes('disputed') && r.name.state !== 'disputed') return false;
    if (chips.includes('heat-stated') && !r.preparation.heat) return false;
    if (chips.includes('strained') && r.preparation.filtered !== true) return false;
    return true;
  });
  const plants = useMemo(() => {
    const m = new Map<string, Recipe[]>();
    shown.forEach((r) => m.set(plantKey(r), [...(m.get(plantKey(r)) ?? []), r]));
    return [...m.entries()];
  }, [shown]);

  return (
    <SiteShell current="atlas" onNavigate={onNavigate}>
      <PageHeader eyebrow="Recipe Atlas" title="Every recipe, read as a recipe" lead="Search plants, historical names, preparations or words in the passage. Historical spellings are matched." />
      <div className="flex flex-col gap-4">
        <label htmlFor="atlas-q" className="sr-only">Search the Atlas</label>
        <div className="relative">
          <IconSearch size={20} className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-ink-muted" />
          <input
            id="atlas-q" type="search" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Try “liquorice”, “absinthium”, “vinegar”, “strain”…"
            className="h-14 w-full rounded-full border border-border-strong bg-surface pl-14 pr-5 text-md text-ink shadow-1 placeholder:text-ink-subtle"
          />
        </div>
        <div role="group" aria-label="Filters" className="flex flex-wrap gap-2">
          {CHIPS.map((c) => {
            const on = chips.includes(c.id);
            return <button key={c.id} type="button" aria-pressed={on} onClick={() => toggle(c.id)} className={cx('h-9 rounded-full border px-4 text-sm font-medium', on ? 'border-ink bg-ink text-paper' : 'border-border-strong text-ink-muted hover:text-ink')}>{c.label}</button>;
          })}
        </div>
        <p className="m-0 text-sm text-ink-muted" aria-live="polite">{shown.length} of {recipes.length} recipes · {plants.length} plants{chips.length || q ? ' · ' : ''}{(chips.length > 0 || q) && <button type="button" onClick={() => { setChips([]); setQ(''); }} className="text-ink underline underline-offset-4">clear</button>}</p>
      </div>

      {plants.length === 0 ? (
        <EmptyState title="Nothing matches" body="Try a historical spelling, or clear the filters. Recipes whose details are not stated stay visible unless you filter them out." action={<button type="button" onClick={() => { setChips([]); setQ(''); }} className="h-10 rounded-full border border-border-strong px-4 font-semibold">Clear search and filters</button>} />
      ) : (
        <section aria-labelledby="plants">
          <h2 id="plants" className="sr-only">Plants</h2>
          <ul className="m-0 grid list-none grid-cols-1 gap-6 p-0 sm:grid-cols-2 lg:grid-cols-3">
            {plants.map(([key, rs]) => {
              const r0 = rs[0];
              const taxon = r0.name.candidates[0]?.taxon ?? '';
              return (
                <li key={key} className="flex flex-col gap-2">
                  <PlantCard
                    name={r0.name}
                    common={r0.name.state === 'disputed' ? `“${r0.name.historicalName}”` : COMMON[taxon] ?? r0.name.historicalName}
                    plate={plates.find((p) => p.taxon === taxon || p.taxon === `${taxon} sp.`)}
                    recipes={{ culpeper: rs.filter((x) => x.source === 'culpeper_1652').length, pliny: rs.filter((x) => x.source === 'pliny_nh').length }}
                    toxicity={r0.toxicity}
                    href={`/recipes/${r0.id}`}
                    onOpen={onNavigate ? () => onNavigate(`/recipes/${r0.id}`) : undefined}
                  />
                  {rs.length > 1 && (
                    <ul className="m-0 flex list-none flex-col gap-1 p-0 text-sm">
                      {rs.map((r) => <li key={r.id}><a href={`/recipes/${r.id}`} onClick={go(`/recipes/${r.id}`)} className="text-brand underline underline-offset-4">{SOURCE_LABEL[r.source].short}: {VEHICLE_LABEL[r.preparation.vehicle]}</a></li>)}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </SiteShell>
  );
}

/* ───────────── Recipe page ───────────── */

const ALL_KINDS: ExtractedFieldKind[] = ['plant', 'part', 'quantity', 'vehicle', 'heat', 'duration', 'filtration'];

function PassageText({ passage, numbers, active, setActive }: { passage: Passage; numbers: Map<string, number>; active: string | null; setActive: (id: string | null) => void }) {
  type Seg = { kind: 'text'; s: string } | { kind: 'field'; f: ExtractedField } | { kind: 'ill'; id: string; est: number | null; note?: string };
  const cuts = [
    ...passage.fields.map((f) => ({ at: f.start, order: 1, seg: { kind: 'field', f } as Seg, end: f.end })),
    ...passage.illegible.map((i) => ({ at: i.at, order: 0, seg: { kind: 'ill', id: i.id, est: i.estChars, note: i.note } as Seg, end: i.at })),
  ].sort((a, b) => a.at - b.at || a.order - b.order);
  const segs: Seg[] = [];
  let pos = 0;
  for (const c of cuts) { if (c.at > pos) segs.push({ kind: 'text', s: passage.text.slice(pos, c.at) }); segs.push(c.seg); pos = Math.max(pos, c.end); }
  if (pos < passage.text.length) segs.push({ kind: 'text', s: passage.text.slice(pos) });
  return (
    <p className="m-0 max-w-prose font-display text-2xl text-ink">
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
            className={cx('inline rounded bg-hist-bg px-1 text-left font-display text-2xl text-ink underline decoration-hist-edge decoration-2 underline-offset-[6px] transition-shadow duration-fast', active === s.f.id && 'outline outline-2 outline-ink')}
          >
            {passage.text.slice(s.f.start, s.f.end)}<sup className="ml-0.5 font-mono text-xs not-italic text-hist-fg">{n}</sup>
          </button>
        );
      })}
    </p>
  );
}

export function RecipePage({ recipe, onNavigate }: { recipe: Recipe; onNavigate?: (p: string) => void }) {
  const [active, setActive] = useState<string | null>(null);
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); onNavigate(path); } };
  const p = recipe.passage;
  const ordered = [...p.fields].sort((a, b) => a.start - b.start);
  const numbers = new Map(ordered.map((f, i) => [f.id, i + 1]));
  const missing = ALL_KINDS.filter((k) => !p.fields.some((f) => f.kind === k));
  const toxic = recipe.toxicity.category === 'toxic_reported';
  const taxon = recipe.name.candidates[0]?.taxon ?? '';
  const inLab = recipe.name.state === 'resolved' && !toxic && LAB_PLANTS.some((x) => x.taxon === taxon && x.hasProfile);
  const labPath = `/lab?plant=${encodeURIComponent(taxon)}${['water', 'wine', 'vinegar', 'oil', 'honey'].includes(recipe.preparation.vehicle) ? `&solvent=${recipe.preparation.vehicle}` : ''}${recipe.preparation.heat ? `&heat=${recipe.preparation.heat}` : ''}${recipe.preparation.filtered != null ? `&strained=${recipe.preparation.filtered}` : ''}`;

  return (
    <SiteShell current="atlas" onNavigate={onNavigate}>
      <a href="/atlas" onClick={go('/atlas')} className="w-max text-sm text-ink-muted underline underline-offset-4">← Recipe Atlas</a>
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="flex flex-col gap-6 lg:col-span-8">
          <PageHeader
            eyebrow={`Recipe · ${SOURCE_LABEL[recipe.source].full}`}
            title={<><i>{recipe.name.historicalName}</i> in {VEHICLE_LABEL[recipe.preparation.vehicle].toLowerCase()}</>}
          >
            <div className="flex flex-wrap items-center gap-2">
              <SourceConfidenceMarker confidence={recipe.source === 'pliny_nh' ? sourcePliny : sourceCulpeper} />
              <EvidenceStatusBadge status={recipe.evidence} />
              <ToxicityBadge record={recipe.toxicity} />
            </div>
          </PageHeader>
          <ToxicityNotice record={recipe.toxicity} />

          <section aria-labelledby="passage" className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-6 shadow-1 md:p-8">
            <h2 id="passage" className="eyebrow m-0 text-ink-subtle">Original passage</h2>
            <PassageText passage={p} numbers={numbers} active={active} setActive={setActive} />
            <p className="m-0 text-xs text-ink-subtle">{p.edition} · {p.locator}</p>
            <div className="flex flex-wrap gap-x-5 gap-y-2 border-t border-border pt-3 text-sm text-ink-muted">
              <span className="inline-flex items-center gap-2"><span aria-hidden className="inline-block h-3 w-6 rounded bg-hist-bg underline decoration-hist-edge" style={{ borderBottom: '2px solid var(--c-hist-edge)' }} />Extracted field (numbered)</span>
              <span className="inline-flex items-center gap-2"><span aria-hidden className="rounded border border-dashed border-unk-line bg-unk-bg px-1 text-xs text-unk-fg">⟦?⟧</span>Illegible in source</span>
            </div>
          </section>

          <section aria-labelledby="fields" className="flex flex-col gap-3">
            <h2 id="fields" className="m-0 font-display text-2xl text-ink">What the pipeline extracted</h2>
            <ol className="m-0 grid list-none grid-cols-1 gap-2 p-0 sm:grid-cols-2">
              {ordered.map((f) => (
                <li key={f.id} onMouseEnter={() => setActive(f.id)} onMouseLeave={() => setActive(null)} className={cx('flex flex-col gap-1.5 rounded-md border p-3 transition-colors duration-fast', active === f.id ? 'border-hist-edge bg-hist-bg' : 'border-border bg-surface')}>
                  <span className="flex items-center justify-between gap-2">
                    <span className="flex items-baseline gap-2"><span className="font-mono text-xs text-hist-fg">{numbers.get(f.id)}</span><span className="eyebrow text-ink-subtle">{FIELD_LABEL[f.kind]}</span></span>
                    <EvidenceStatusBadge status={f.evidence} size="sm" />
                  </span>
                  <span className="text-base text-ink">{f.value ?? <UnknownValue label="Could not normalise" />}</span>
                  <span className="font-display text-md italic text-ink-muted">“{p.text.slice(f.start, f.end)}”</span>
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
        </div>

        <aside className="flex flex-col gap-6 lg:col-span-4">
          <PlateSlot taxon={taxon || recipe.name.historicalName} plate={plates.find((x) => x.taxon === taxon)} size="hero" className="hidden lg:flex" />
          <section aria-labelledby="species" className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5 shadow-1">
            <h2 id="species" className="eyebrow m-0 text-ink-subtle">Species</h2>
            <DisputedName resolution={recipe.name} />
          </section>
          <section aria-labelledby="prep" className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5 shadow-1">
            <h2 id="prep" className="eyebrow m-0 text-ink-subtle">Preparation</h2>
            <PrepTag prep={recipe.preparation} />
            <span className="text-sm text-ink-muted">Heat: {recipe.preparation.heat ? HEAT_LABEL[recipe.preparation.heat] : <UnknownValue label="not stated" />}</span>
            {inLab && <LinkButton href={labPath} onClick={go(labPath)} variant="primary" className="w-max">Open this preparation in the Lab</LinkButton>}
            {!toxic && recipe.name.state === 'disputed' && (
              <div className="flex flex-col gap-1 text-sm">
                <span className="text-ink-muted">Disputed name — compare each candidate separately:</span>
                {recipe.name.candidates.map((c, i) => c.rank === 'species' && LAB_PLANTS.some((x) => x.taxon === c.taxon && x.hasProfile)
                  ? <a key={c.taxon} href={`/lab?plant=${encodeURIComponent(c.taxon)}`} onClick={go(`/lab?plant=${encodeURIComponent(c.taxon)}`)} className="text-brand underline underline-offset-4"><Taxon name={c.taxon} /> · candidate {i + 1} of {recipe.name.candidates.length} →</a>
                  : <UnknownValue key={c.taxon} label={`${c.rank === 'genus' ? `${c.taxon} sp.` : c.taxon} · no Lab profile`} />)}
              </div>
            )}
          </section>
        </aside>
      </div>
    </SiteShell>
  );
}
