'use client';

import { useEffect, useId, useState } from 'react';
import Link from '@/components/base/Link';
import type { CompoundEstimate, Driver, PreparationProfile, SourceConfidence, SourceWork, SpeciesProfile } from '@/lib/types';
import { DRIVER_LABEL, compareRanges, cx, isKnownRange, rangeText, slug } from '@/lib/data/format';
import { heuristic } from '@/lib/data/heuristics';
import { expandProfile, type CompactProfile } from '@/lib/data/selectors/compare';
import { AppShell } from '@/components/layout/AppShell';
import { ChartTable } from '@/components/base/ChartTable';
import { PrepLegend, PrepTag } from '@/components/base/PrepTag';
import { ErrorState, LoadingState } from '@/components/base/States';
import { Taxon } from '@/components/base/Taxon';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import { MarkHistorical, MarkModern } from '@/components/icons';

/**
 * COMPARE — the signature view. Two preparations of ONE species, side by side.
 *
 * - Compounds are grouped by class; each row pairs two LikelihoodBars on the
 *   same 0–1 scale.
 * - "Enriched here" appears only when the two ranges do not overlap at all.
 *   Overlap → "No clear difference". Either range unknown → "Can't compare".
 *   Point estimates are never used to decide this.
 * - Drivers (solvent, heat, filtration, acidity) open per row: hover previews
 *   on pointer devices; tap/click pins. Heat and acidity carry the heuristic
 *   marker.
 * - Profiles load per species, so there is a real loading and error state.
 */
/** SITE: rule texts from lib/data/heuristics.ts; whether a driver is heuristic comes from the profile's `heuristic` flags. */
const HEURISTIC = {
  heat: heuristic('heat_sensitivity')!, acidity: heuristic('acidity')!, filtration: heuristic('filtration_carryover')!,
};

function DriverList({ drivers }: { drivers: Driver[] }) {
  return (
    <ul className="m-0 flex list-none flex-col gap-1.5 p-0 text-sm">
      {drivers.map((d) => {
        const label = DRIVER_LABEL[d.id];
        const effect =
          d.effect === 'unknown' ? <UnknownValue label="Effect unknown" /> :
          <span className="text-ink">
            <span aria-hidden className="font-mono">{d.effect === 'raises' ? '↑' : d.effect === 'lowers' ? '↓' : '–'}</span>{' '}
            {d.effect === 'neutral' ? 'little effect' : d.effect}{d.strength && d.effect !== 'neutral' ? ` · ${d.strength}` : ''}
          </span>;
        return (
          <li key={d.id} className="flex flex-col gap-0.5">
            <span className="flex flex-wrap items-baseline gap-2">
              {d.heuristic && (d.id === 'heat' || d.id === 'acidity' || d.id === 'filtration') ? (
                <HeuristicMarker heuristic={HEURISTIC[d.id]}>{label}</HeuristicMarker>
              ) : (
                <span className="font-medium text-ink">{label}</span>
              )}
              {effect}
            </span>
            {d.note && <span className="text-xs text-ink-subtle">{d.note}</span>}
          </li>
        );
      })}
    </ul>
  );
}

function Verdict({ a, b, aLabel, bLabel }: { a: CompoundEstimate; b: CompoundEstimate; aLabel: string; bLabel: string }) {
  const r = compareRanges(a.likelihood, b.likelihood);
  if (r === 'unknown') return <UnknownValue label="Can’t compare" reason="At least one range is unknown." />;
  if (r === 'overlap') return <span className="text-sm text-ink-muted">Ranges overlap · no clear difference</span>;
  const left = r === 'a';
  return (
    <span className={cx('inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-sm font-medium', left ? 'border-hist-fg bg-hist-bg text-hist-fg' : 'border-mod-fg bg-mod-bg text-mod-fg')}>
      {left ? <MarkHistorical /> : <MarkModern />}
      Enriched in {left ? aLabel : bLabel}
      <span className="font-normal">· ranges don’t overlap</span>
    </span>
  );
}

function CompoundRow({ a, b, left, right }: { a: CompoundEstimate; b: CompoundEstimate; left: PreparationProfile; right: PreparationProfile }) {
  const [pinned, setPinned] = useState(false);
  const [hover, setHover] = useState(false);
  const open = pinned || hover;
  const id = useId();
  const famA = left.preparation.family;
  const famB = right.preparation.family;
  const r = compareRanges(a.likelihood, b.likelihood);
  return (
    <li
      className="flex flex-col gap-3 border-t border-border py-4"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className="grid grid-cols-1 items-start gap-3 md:grid-cols-4">
        <div className="flex min-w-0 flex-col gap-1">
          {/* SITE: long IUPAC names wrap, so they cannot push a 390px page sideways. */}
          <span className="break-words text-base font-medium text-ink">{a.compound}</span>
          <button
            type="button"
            aria-expanded={open}
            aria-controls={id}
            onClick={() => setPinned((p) => !p)}
            className="w-max text-sm text-ink-muted underline underline-offset-2 hover:text-ink"
          >
            {pinned ? 'Hide drivers' : 'Drivers'}
          </button>
        </div>
        <div className="flex flex-col gap-1">
          <LikelihoodBar range={a.likelihood} family={famA} label={left.label.split(',')[0]} width="full" />
          {r === 'a' && <span className="text-xs font-medium text-hist-fg">Enriched here</span>}
        </div>
        <div className="flex flex-col gap-1">
          <LikelihoodBar range={b.likelihood} family={famB} label={right.label.split(',')[0]} width="full" />
          {r === 'b' && <span className={cx('text-xs font-medium', famB === 'modern' ? 'text-mod-fg' : 'text-hist-fg')}>Enriched here</span>}
        </div>
        <div className="flex items-start md:justify-end">
          <Verdict a={a} b={b} aLabel={left.label.split(',')[0]} bLabel={right.label.split(',')[0]} />
        </div>
      </div>
      {open && <div id={id} className="grid grid-cols-1 gap-4 rounded border border-border bg-raised p-4 shadow-2 md:grid-cols-2">
        <div className="flex flex-col gap-2">
          <span className={cx('inline-flex items-center gap-1.5 text-sm font-medium', famA === 'historical' ? 'text-hist-fg' : 'text-mod-fg')}>
            {famA === 'historical' ? <MarkHistorical /> : <MarkModern />} Drivers · {left.label}
          </span>
          <DriverList drivers={a.drivers} />
        </div>
        <div className="flex flex-col gap-2">
          <span className={cx('inline-flex items-center gap-1.5 text-sm font-medium', famB === 'historical' ? 'text-hist-fg' : 'text-mod-fg')}>
            {famB === 'historical' ? <MarkHistorical /> : <MarkModern />} Drivers · {right.label}
          </span>
          <DriverList drivers={b.drivers} />
        </div>
        <p className="m-0 text-xs text-ink-subtle md:col-span-2">Drivers explain the predicted extraction. They say nothing about how much of the compound the plant contained.</p>
      </div>}
    </li>
  );
}

function PrepColumnHeader({ p, side, options, onPick, confidences }: { p: PreparationProfile; side: 'A' | 'B'; options: PreparationProfile[]; onPick: (id: string) => void; confidences: Record<SourceWork, SourceConfidence> }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-2 rounded border border-border bg-surface p-4">
      <label htmlFor={id} className="small-caps text-xs text-ink-subtle">Preparation {side}</label>
      <select
        id={id}
        value={p.id}
        onChange={(e) => onPick(e.target.value)}
        className="h-10 w-full rounded border border-border-strong bg-surface px-3 text-base text-ink"
      >
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.preparation.family === 'historical' ? '■ Historical · ' : '● Modern · '}{o.label}
          </option>
        ))}
      </select>
      <PrepTag prep={p.preparation} />
      {p.origin.kind === 'recipe' ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <Link href={`/recipes/${p.origin.recipeId}/`} className="text-ink underline underline-offset-2">From recipe</Link>
          <SourceConfidenceMarker confidence={confidences[p.origin.source]} compact />
        </div>
      ) : p.origin.kind === 'study' ? (
        <span className="text-sm text-ink-muted">{p.origin.citation}</span>
      ) : (
        <span className="text-sm text-ink-muted">{p.origin.note}</span>
      )}
    </div>
  );
}

const PER_CLASS = 12;
const mid = (e: CompoundEstimate) => (isKnownRange(e.likelihood) ? (e.likelihood.low + e.likelihood.high) / 2 : -1);

/** SITE: species, A and B live in the URL (?species=&a=&b=), so every comparison has a shareable link. */
function readQuery() {
  if (typeof window === 'undefined') return { species: null, a: null, b: null };
  const q = new URLSearchParams(window.location.search);
  return { species: q.get('species'), a: q.get('a'), b: q.get('b') };
}
function writeQuery(species: string, a: string | null, b: string | null) {
  const q = new URLSearchParams({ species });
  if (a) q.set('a', a);
  if (b) q.set('b', b);
  window.history.replaceState(null, '', `${window.location.pathname}?${q.toString()}`);
}

export function Compare({ species: speciesList, defaults, confidences }: {
  species: { speciesId: string; taxon: string }[]; defaults: { species: string; a?: string; b?: string };
  confidences: Record<SourceWork, SourceConfidence>;
}) {
  const [species, setSpecies] = useState<string | null>(null);
  const [state, setState] = useState<{ status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; profile: SpeciesProfile }>({ status: 'loading' });
  const [aId, setAId] = useState<string | null>(null);
  const [bId, setBId] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [openClasses, setOpenClasses] = useState<string[]>([]);
  const speciesId = useId();
  const taxonOf = (id: string | null) => speciesList.find((s) => s.speciesId === id)?.taxon ?? id ?? '';

  useEffect(() => {
    const q = readQuery();
    const sp = q.species && speciesList.some((s) => s.speciesId === q.species) ? q.species : defaults.species;
    setSpecies(sp);
    if (q.species === sp && (q.a || q.b)) { setAId(q.a); setBId(q.b); }
    else if (sp === defaults.species) { setAId(defaults.a ?? null); setBId(defaults.b ?? null); }
  }, [speciesList, defaults]);

  useEffect(() => {
    if (!species) return;
    let live = true;
    setState({ status: 'loading' });
    fetch(`/data/compare/${encodeURIComponent(species)}.json`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status} for ${species}`); return r.json() as Promise<CompactProfile>; })
      .then((cp) => {
        const profile = expandProfile(cp);
        if (!live) return;
        setState({ status: 'ready', profile });
        const has = (id: string | null) => !!id && profile.preparations.some((p) => p.id === id);
        const hist = profile.preparations.find((p) => p.preparation.family === 'historical') ?? profile.preparations[0];
        setAId((cur) => (has(cur) ? cur : hist.id));
        setBId((cur) => {
          if (has(cur)) return cur;
          const mod = profile.preparations.find((p) => p.preparation.family === 'modern' && p.id !== hist.id) ?? profile.preparations[1];
          return mod?.id ?? null;
        });
      })
      .catch((e: Error) => live && setState({ status: 'error', message: e.message }));
    return () => { live = false; };
  }, [species, attempt]);

  useEffect(() => { if (species && state.status === 'ready') writeQuery(species, aId, bId); }, [species, aId, bId, state.status]);

  return (
    <AppShell current="compare">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 sm:w-bar-md">
          <label htmlFor={speciesId} className="text-sm font-medium">Species</label>
          <select
            id={speciesId}
            value={species ?? ''}
            onChange={(e) => { setSpecies(e.target.value); setAId(null); setBId(null); setOpenClasses([]); }}
            className="h-10 rounded border border-border-strong bg-surface px-3 text-base italic text-ink"
          >
            {speciesList.map((t) => <option key={t.speciesId} value={t.speciesId}>{t.taxon}</option>)}
          </select>
        </div>
        <ExtractionDetectionExplainer />
      </div>

      {/* SITE: the loading state holds a screen's height so the footer does not jump when the profile arrives (layout shift). */}
      {state.status === 'loading' && <div className="min-h-screen"><LoadingState label={`Loading extraction profile for ${taxonOf(species)}`} rows={5} /></div>}
      {state.status === 'error' && (
        <ErrorState title="Couldn’t load this species’ profile" body="Nothing has changed on the page. You can try again." detail={state.message} onRetry={() => setAttempt((n) => n + 1)} />
      )}
      {state.status === 'ready' && (() => {
        const prof = state.profile;
        const A = prof.preparations.find((p) => p.id === aId) ?? prof.preparations[0];
        const B = prof.preparations.find((p) => p.id === bId) ?? prof.preparations[1];
        if (!B) return <p className="m-0 text-base text-ink-muted">Only one preparation is recorded for this species, so there is nothing to compare yet.</p>;
        const classes = [...new Set(A.estimates.map((e) => e.compoundClass))].sort();
        const visible = classes.flatMap((cls) => {
          const all = A.estimates.filter((e) => e.compoundClass === cls).sort((x, y) => mid(y) - mid(x));
          return openClasses.includes(cls) ? all : all.slice(0, PER_CLASS);
        });
        return (
          <>
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="m-0 font-serif text-2xl font-medium"><Taxon name={prof.taxon} /></h2>
                <ToxicityBadge record={prof.toxicity} />
              </div>
              {prof.fromName && (
                <p className="m-0 text-sm text-ink-muted">
                  Profile for candidate {prof.fromName.candidateIndex} of {prof.fromName.candidateCount} for “{prof.fromName.historicalName}”. The name is disputed; other candidates have their own profiles.
                </p>
              )}
              <ToxicityNotice record={prof.toxicity} />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <PrepColumnHeader p={A} side="A" options={prof.preparations.filter((p) => p.id !== B.id)} onPick={setAId} confidences={confidences} />
              <PrepColumnHeader p={B} side="B" options={prof.preparations.filter((p) => p.id !== A.id)} onPick={setBId} confidences={confidences} />
            </div>
            <PrepLegend />

            {classes.map((cls) => {
              const all = A.estimates.filter((e) => e.compoundClass === cls).sort((x, y) => mid(y) - mid(x));
              const open = openClasses.includes(cls);
              return (
                <section key={cls} aria-labelledby={`cls-${slug(cls)}`} className="flex flex-col">
                  <h3 id={`cls-${slug(cls)}`} className="m-0 pb-2 text-lg font-semibold">{cls} <span className="num text-base font-normal text-ink-subtle">({all.length})</span></h3>
                  <ul className="m-0 list-none p-0">
                    {(open ? all : all.slice(0, PER_CLASS)).map((ea, i) => {
                      const eb = B.estimates.find((x) => x.compound === ea.compound);
                      return eb ? <CompoundRow key={`${ea.compound}-${i}`} a={ea} b={eb} left={A} right={B} /> : (
                        <li key={`${ea.compound}-${i}`} className="flex flex-wrap items-center gap-3 border-t border-border py-4">
                          <span className="min-w-0 break-words text-base font-medium">{ea.compound}</span>
                          <UnknownValue label={`Not estimated for preparation B`} />
                        </li>
                      );
                    })}
                  </ul>
                  {all.length > PER_CLASS && (
                    <button type="button" aria-expanded={open} onClick={() => setOpenClasses((o) => (open ? o.filter((c) => c !== cls) : [...o, cls]))}
                      className="mt-2 w-max text-sm text-ink-muted underline underline-offset-2 hover:text-ink">
                      {open ? `Show the first ${PER_CLASS}` : `Show all ${all.length} compounds in this class`}
                    </button>
                  )}
                </section>
              );
            })}
            <ChartTable
              caption={`Predicted extraction for ${prof.taxon}: ${A.label} (A) vs ${B.label} (B), range 0–1 (the compounds shown above)`}
              headers={['Compound', 'Class', `A · ${A.label}`, `B · ${B.label}`, 'Comparison']}
              numeric={[2, 3]}
              rows={visible.map((ea) => {
                const eb = B.estimates.find((x) => x.compound === ea.compound);
                const v = eb ? compareRanges(ea.likelihood, eb.likelihood) : 'unknown';
                return [
                  ea.compound,
                  ea.compoundClass,
                  isKnownRange(ea.likelihood) ? rangeText(ea.likelihood) : <UnknownValue />,
                  eb && isKnownRange(eb.likelihood) ? rangeText(eb.likelihood) : <UnknownValue />,
                  v === 'a' ? 'Enriched in A' : v === 'b' ? 'Enriched in B' : v === 'overlap' ? 'Ranges overlap' : <UnknownValue label="Can’t compare" />,
                ];
              })}
            />
            <ExtractionDetectionExplainer variant="panel" />
          </>
        );
      })()}
    </AppShell>
  );
}
