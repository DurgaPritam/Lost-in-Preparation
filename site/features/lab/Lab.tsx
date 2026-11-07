'use client';

import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { EngineModel } from '@/lib/engine';
import type { CompoundEstimate, Driver, Heuristic, LikelihoodRange } from '@/lib/types';
import { compareRanges, cx, DRIVER_LABEL, fmt, isKnownRange, meanWidth, rangeText, slug } from '@/lib/data/format';
import {
  DEFAULT_SETTINGS, HEATS, MODERN_PREPARATION, SOLVENTS, labQueryString, modernPrep, parseLabQuery, prepFor, preparationOfSettings,
  settingsLabel, toEstimates, type LabQuery, type LabSettings,
} from '@/lib/data/selectors/lab';
import type { LabPlant } from '@/lib/data/assemble';
import { useProfile } from '@/features/engine/useProfile';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { SegmentedControl, Switch } from '@/components/base/Controls';
import { ChartTable } from '@/components/base/ChartTable';
import { EmptyState, ErrorState, LoadingState } from '@/components/base/States';
import { LinkButton } from '@/components/base/Button';
import { PlateSlot } from '@/components/base/PlateSlot';
import { Popover } from '@/components/base/Popover';
import { PrepLegend, PrepTag } from '@/components/base/PrepTag';
import { Taxon } from '@/components/base/Taxon';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * PREPARATION LAB — the core product (design v2 screens/Lab.tsx).
 * SITE: the profile is computed live by the preparation engine in a Web Worker (lib/engine, parity-tested against the
 * Python pipeline), not read from pre-computed combinations. Every solvent × heat × filtration combination the model
 * represents has an estimate; "acidified" without vinegar does not (the model's acidity is vinegar on basic nitrogen),
 * so that combination gets the designed no-data state. The URL carries the plant and every setting.
 */
const WIDE = 0.4;
const PER_CLASS = 12;

interface Row { i: number; e: CompoundEstimate; prev?: CompoundEstimate; modern?: CompoundEstimate }

function Delta({ prev, now }: { prev?: LikelihoodRange; now: LikelihoodRange }) {
  if (!prev) return null;
  const v = compareRanges(now, prev);
  const txt = v === 'a' ? '↑ higher' : v === 'b' ? '↓ lower' : v === 'overlap' ? '≈ overlaps' : '? can’t compare';
  return <span className={cx('rounded-full px-2 py-0.5 text-xs font-medium', v === 'a' || v === 'b' ? 'bg-sunken text-ink' : 'text-ink-subtle')} title="Compared with the previous setting; ‘higher/lower’ only when the ranges do not overlap">{txt}</span>;
}

function DriverLine({ d, prev, heur }: { d: Driver; prev?: Driver; heur: Record<string, Heuristic | undefined> }) {
  const changed = prev && prev.effect !== d.effect;
  const effect = d.effect === 'unknown' ? <UnknownValue label="effect unknown" /> : <span>{d.effect === 'raises' ? '↑ raises' : d.effect === 'lowers' ? '↓ lowers' : '– little effect'}{d.strength && d.effect !== 'neutral' ? ` · ${d.strength}` : ''}</span>;
  const h = d.id === 'heat' ? heur.heat : d.id === 'acidity' ? heur.acidity : d.id === 'filtration' ? heur.filtration : undefined;
  return (
    <li className={cx('flex flex-col gap-0.5 rounded px-2 py-1.5', changed && 'bg-hist-bg')}>
      <span className="flex flex-wrap items-baseline gap-x-2">
        {d.heuristic && h ? <HeuristicMarker heuristic={h}>{DRIVER_LABEL[d.id]}</HeuristicMarker> : <span className="font-semibold">{DRIVER_LABEL[d.id]}</span>}
        {effect}
        {changed && <span className="text-xs font-semibold text-hist-fg">changed</span>}
      </span>
      {d.note && <span className="text-xs text-ink-subtle">{d.note}</span>}
    </li>
  );
}

function CompoundRow({ r, showModern, heur }: { r: Row; showModern: boolean; heur: Record<string, Heuristic | undefined> }) {
  const { e, prev, modern } = r;
  return (
    <li className="grid grid-cols-1 gap-2 border-t border-border py-4 md:grid-cols-12 md:items-center md:gap-4">
      <div className="flex min-w-0 items-center justify-between gap-2 md:col-span-3 md:flex-col md:items-start">
        <span className="min-w-0 break-words text-base font-semibold text-ink">{e.compound}</span>
        <Delta prev={prev?.likelihood} now={e.likelihood} />
      </div>
      <div className="min-w-0 md:col-span-7">
        <LikelihoodBar range={e.likelihood} compare={showModern ? modern?.likelihood ?? { low: null, high: null } : null} label={e.compound} />
      </div>
      <div className="md:col-span-2 md:justify-self-end">
        <Popover
          align="end"
          label={`Why does ${e.compound} look like this?`}
          triggerClassName="inline-flex h-8 items-center rounded-full border border-border-strong px-3 text-sm font-medium text-ink hover:bg-sunken"
          trigger={<>Why? <span aria-hidden className="ml-1">›</span></>}
        >
          <div className="flex flex-col gap-2">
            <span className="font-semibold">Why {e.compound} looks like this</span>
            {prev ? (
              <span className="text-ink-muted">Previous setting: {rangeText(prev.likelihood)} → now: {rangeText(e.likelihood)}. Highlighted drivers changed.</span>
            ) : <span className="text-ink-muted">Drivers for the current preparation.</span>}
            <ul className="m-0 flex list-none flex-col gap-1 p-0">
              {e.drivers.map((d) => <DriverLine key={d.id} d={d} prev={prev?.drivers.find((x) => x.id === d.id)} heur={heur} />)}
            </ul>
            <span className="text-xs text-ink-subtle">Drivers explain predicted extraction. They say nothing about how much the plant contained.</span>
          </div>
        </Popover>
      </div>
    </li>
  );
}

function ClassSection({ cls, rows, showModern, heur }: { cls: string; rows: Row[]; showModern: boolean; heur: Record<string, Heuristic | undefined> }) {
  const [all, setAll] = useState(false);
  const shown = all ? rows : rows.slice(0, PER_CLASS);
  const id = `cls-${slug(cls)}`;
  return (
    <section aria-labelledby={id}>
      <h3 id={id} className="m-0 pb-1 text-sm font-semibold uppercase tracking-caps text-ink-subtle">{cls} <span className="num font-mono normal-case tracking-normal">· {rows.length}</span></h3>
      <ul className="m-0 list-none p-0">
        {shown.map((r) => <CompoundRow key={r.i} r={r} showModern={showModern} heur={heur} />)}
      </ul>
      {rows.length > PER_CLASS && (
        // SITE: a species can have hundreds of compounds; each class shows its 12 highest medians first.
        <button type="button" aria-expanded={all} onClick={() => setAll((a) => !a)} className="mt-1 inline-flex h-9 items-center rounded-full border border-border-strong px-3 text-sm font-medium text-ink hover:bg-sunken">
          {all ? `Show the top ${PER_CLASS}` : `Show all ${rows.length} in this class`}
        </button>
      )}
    </section>
  );
}

export interface LabProps { plants: LabPlant[]; genusOnly: string[]; heuristics: Heuristic[]; defaultTaxon: string; model: EngineModel }

export function Lab({ plants, genusOnly, heuristics, defaultTaxon, model }: LabProps) {
  const [mounted, setMounted] = useState(false);
  const [q, setQ] = useState<LabQuery>({ ...DEFAULT_SETTINGS, plant: defaultTaxon, modern: false });
  useEffect(() => {
    const parsed = parseLabQuery(new URLSearchParams(window.location.search));
    setQ({ ...parsed, plant: parsed.plant ?? defaultTaxon });
    setMounted(true);
  }, [defaultTaxon]);
  useEffect(() => {
    if (mounted) window.history.replaceState(null, '', `${window.location.pathname}?${labQueryString(q)}`);
  }, [q, mounted]);

  const s: LabSettings = { solvent: q.solvent, heat: q.heat, filtered: q.filtered, acidified: q.acidified };
  const plant = plants.find((p) => p.taxon === q.plant) ?? null;
  const prep = mounted && plant ? prepFor(model, s) : null;
  const modern = modernPrep(model);
  const profile = useProfile('lab', mounted && plant ? plant.speciesId : null, prep);
  const modernProfile = useProfile('lab-modern', mounted && plant && q.modern ? plant.speciesId : null, modern);

  const heur = useMemo(() => ({
    heat: heuristics.find((h) => h.id === 'heat_sensitivity'), acidity: heuristics.find((h) => h.id === 'acidity'),
    filtration: heuristics.find((h) => h.id === 'filtration_carryover'),
  }), [heuristics]);

  const current = profile.estimates && profile.compounds && profile.speciesId === plant?.speciesId ? toEstimates(profile.compounds, profile.estimates, s) : null;
  // Remember the last setting with data (same plant), for the delta chips and "Why?".
  const lastRef = useRef<{ key: string; speciesId: string; est: CompoundEstimate[] } | null>(null);
  const [prev, setPrev] = useState<CompoundEstimate[] | null>(null);
  useEffect(() => {
    if (profile.status !== 'ready' || !current || !profile.key || !plant) return;
    const last = lastRef.current;
    if (last && last.key !== profile.key) setPrev(last.speciesId === plant.speciesId ? last.est : null);
    lastRef.current = { key: profile.key, speciesId: plant.speciesId, est: current };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.key, profile.status]);
  useEffect(() => { setPrev(null); lastRef.current = null; }, [plant?.speciesId]);

  const modernEst = modernProfile.estimates && modernProfile.compounds && modernProfile.speciesId === plant?.speciesId
    ? toEstimates(modernProfile.compounds, modernProfile.estimates, null) : null;

  const update = (patch: Partial<LabQuery>) => setQ((cur) => {
    const n = { ...cur, ...patch };
    if (patch.solvent) n.acidified = patch.solvent === 'vinegar'; // vinegar is inherently acidic
    return n;
  });

  // Solvent assumptions, read from the model's parameters (engine/model.json), never typed in here.
  const W = model.params.solvents;
  const sameWindow = (x?: { upper?: number[] | null; lower?: number[] | null }, y?: { upper?: number[] | null; lower?: number[] | null }) =>
    !!x && !!y && JSON.stringify([x.upper, x.lower]) === JSON.stringify([y.upper, y.lower]);
  const ef = W.wine?.ethanolFraction;
  const solventNote = q.solvent === 'honey' && sameWindow(W.honey, W.water) ? 'Honey is modelled with the same solvent window as water (an assumption of the model, not a measurement).'
    : q.solvent === 'wine' && ef ? `Wine is modelled as ${Math.round(ef[0] * 100)}–${Math.round(ef[1] * 100)}% ethanol in water (an assumption of the model).`
    : null;
  const toxic = plant?.toxicity.category === 'toxic_reported';
  const updating = profile.status === 'updating';
  const width = current ? meanWidth(current.map((e) => e.likelihood)) : null;
  const rows: Row[] = current ? current.map((e, i) => ({ i, e, prev: prev?.[i], modern: modernEst?.[i] })) : [];
  const classes = [...new Set(rows.map((r) => r.e.compoundClass))].sort();
  const byClass = (cls: string) => rows.filter((r) => r.e.compoundClass === cls)
    .sort((a, b) => (b.e.likelihood.point ?? -1) - (a.e.likelihood.point ?? -1) || a.e.compound.localeCompare(b.e.compound));

  const announce = !mounted ? 'Loading the Lab'
    : !plant ? `No profile for ${q.plant}`
    : !prep ? 'No estimate for this combination'
    : profile.status === 'loading' ? `Computing ${settingsLabel(s)} for ${plant.taxon}`
    : updating ? `Updating to ${settingsLabel(s)}`
    : current ? `Showing ${settingsLabel(s)} for ${plant.taxon}: ${current.length} compounds` : '';

  const controls = (
    <div className="flex flex-col gap-6 rounded-lg border border-border bg-surface p-5 shadow-1 lg:sticky lg:top-24">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="lab-plant" className="eyebrow text-ink-subtle">Plant</label>
        <select id="lab-plant" value={plant ? plant.taxon : ''} onChange={(e) => update({ plant: e.target.value })} className="h-11 w-full rounded-md border border-border-strong bg-paper px-3 text-base text-ink">
          {!plant && <option value="">{q.plant} (no profile)</option>}
          {plants.map((p) => <option key={p.speciesId} value={p.taxon}>{p.taxon} · {p.compounds} compounds{p.toxicity.category === 'toxic_reported' ? ' · toxicity reported' : ''}</option>)}
        </select>
      </div>
      <div className="flex flex-col gap-1.5">
        <SegmentedControl label="Solvent" options={SOLVENTS} value={q.solvent} onChange={(v) => update({ solvent: v })} size="sm" />
        {solventNote && <span className="text-xs text-ink-subtle">{solventNote}</span>}
      </div>
      <SegmentedControl label="Heat" options={HEATS} value={q.heat} onChange={(v) => update({ heat: v })} size="sm" />
      <div className="flex flex-col gap-4 border-t border-border pt-4">
        <Switch label="Filtration" description="Strained through cloth" checked={q.filtered} onChange={(v) => update({ filtered: v })} states={['Unstrained', 'Strained']} />
        <Switch label="Acidity" description={q.solvent === 'vinegar' ? 'Vinegar is acidic; always on' : 'Acid added to the preparation'} checked={q.acidified} onChange={(v) => q.solvent !== 'vinegar' && update({ acidified: v })} states={['Neutral', 'Acidified']} />
      </div>
      <div className="flex flex-col gap-2 border-t border-border pt-4">
        <Switch label="Compare with modern lab method" description={modern ? modern.label : 'No modern method recorded'} checked={q.modern} onChange={(v) => update({ modern: v })} />
      </div>
    </div>
  );

  let body: ReactNode;
  if (!mounted) body = <LoadingState label="Loading the Lab" rows={5} />;
  else if (!plant) body = (
    <EmptyState
      title="No profile for this plant yet"
      body={genusOnly.includes(q.plant ?? '')
        ? <>The name resolves to <Taxon name={`${q.plant} sp.`} /> only at genus level, so there is no species-level compound profile to model. Choose another plant, or see its recipes in the Atlas.</>
        : <>There is no modelled profile for <strong className="font-semibold">{q.plant}</strong>. The Lab covers the {plants.length} species of the study set; choose one, or search the Atlas.</>}
      action={<LinkButton href={`/atlas/${q.plant ? `?q=${encodeURIComponent(q.plant)}` : ''}`} size="sm">Open the Recipe Atlas</LinkButton>}
    />
  );
  else if (!prep) body = (
    <EmptyState
      title="No estimate for this combination"
      body={<>We have not modelled <strong className="font-semibold">{settingsLabel(s)}</strong> for this plant, and the Lab never guesses between settings. The model represents acidity only through vinegar. Try one of these:</>}
      action={
        <ul className="m-0 flex list-none flex-wrap justify-center gap-2 p-0">
          <li><button type="button" onClick={() => update({ solvent: 'vinegar' })} className="inline-flex h-9 items-center rounded-full border border-border-strong px-3 text-sm font-medium hover:bg-sunken">Vinegar, {q.heat}, {q.filtered ? 'strained' : 'unstrained'}</button></li>
          <li><button type="button" onClick={() => update({ acidified: false })} className="inline-flex h-9 items-center rounded-full border border-border-strong px-3 text-sm font-medium hover:bg-sunken">{SOLVENTS.find((x) => x.value === q.solvent)!.label}, neutral</button></li>
        </ul>
      }
    />
  );
  else if (profile.status === 'error') body = <ErrorState title="The profile could not be computed" body="The engine did not return an estimate. Nothing is shown in its place." detail={profile.error ?? undefined} onRetry={() => setQ((x) => ({ ...x }))} />;
  else if (!current) body = <LoadingState label={`Computing the extraction profile for ${plant.taxon}`} rows={5} />;
  else body = (
    <div className={cx('flex flex-col gap-5 transition-opacity duration-base ease-standard', updating && 'opacity-60')} aria-busy={updating}>
      {updating && <span role="status" className="w-max rounded-full border border-dotted border-unk-fg bg-unk-bg px-2.5 py-0.5 text-sm font-semibold text-unk-fg">Updating to {settingsLabel(s)}…</span>}
      {width != null && width >= WIDE && (
        <div role="note" className="flex items-start gap-3 rounded-md border border-dashed border-border-strong bg-unk-bg p-4 text-sm text-ink">
          <span aria-hidden className="mt-0.5 font-mono">±</span>
          <p className="m-0"><strong className="font-semibold">Wide uncertainty.</strong> Ranges for this preparation are wide (average width {fmt(width)}). Differences from other preparations are unlikely to be meaningful.</p>
        </div>
      )}
      {classes.map((cls) => <ClassSection key={`${plant.speciesId}-${cls}`} cls={cls} rows={byClass(cls)} showModern={q.modern} heur={heur} />)}
      <ChartTable
        caption={`Predicted extraction for ${plant.taxon}: ${settingsLabel(s)}${q.modern && modern ? ` vs ${modern.label}` : ''} (range 0–1, ${rows.length} compounds)`}
        headers={q.modern ? ['Compound', 'Class', 'This preparation', 'Modern lab method'] : ['Compound', 'Class', 'This preparation']}
        numeric={q.modern ? [2, 3] : [2]}
        rows={rows.map((r) => {
          const row: ReactNode[] = [r.e.compound, r.e.compoundClass, isKnownRange(r.e.likelihood) ? rangeText(r.e.likelihood) : <UnknownValue />];
          return q.modern ? [...row, r.modern && isKnownRange(r.modern.likelihood) ? rangeText(r.modern.likelihood) : <UnknownValue label={modernProfile.status === 'ready' ? 'Unknown' : 'Computing'} />] : row;
        })}
      />
      <div className="flex flex-wrap gap-3 border-t border-border pt-5">
        <LinkButton href={`/atlas/?q=${encodeURIComponent(plant.taxon)}`}>Recipes using this plant</LinkButton>
        {/* Acceptance check 5: a plant with toxicity reported never gets "Plan an experiment". */}
        {!toxic && <LinkButton href="/planner/" variant="primary">Plan an experiment</LinkButton>}
      </div>
    </div>
  );

  return (
    <SiteShell current="lab">
      <PageHeader eyebrow="Preparation Lab" title={<>Change the preparation. <i className="text-brand">Watch the profile respond.</i></>} lead="Every value is a predicted extraction range, not a measurement. Settings without a modelled estimate say so — the Lab never fills the gaps." />
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="lg:col-span-4">{controls}</div>
        <div className="flex min-w-0 flex-col gap-5 lg:col-span-8" aria-busy={!mounted || profile.status === 'loading'}
             data-engine-status={!mounted ? 'loading' : !plant || !prep ? 'nodata' : profile.status} data-engine-key={profile.key ?? ''} data-engine-ms={profile.ms == null ? '' : profile.ms.toFixed(1)}>
          <p className="sr-only" aria-live="polite">{announce}</p>
          <div className="flex flex-wrap items-start gap-4">
            <PlateSlot plate={plant?.plate} taxon={plant?.taxon ?? q.plant ?? ''} size="thumb" />
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <h2 className="m-0 font-display text-2xl text-ink"><Taxon name={plant?.taxon ?? q.plant ?? ''} /></h2>
              <div className="flex flex-wrap items-center gap-2">
                {plant && <ToxicityBadge record={plant.toxicity} />}
                {plant && prep && <PrepTag prep={preparationOfSettings(s)} />}
                {plant && q.modern && <PrepTag prep={MODERN_PREPARATION} compact />}
                <ExtractionDetectionExplainer />
              </div>
            </div>
          </div>
          {plant && <ToxicityNotice record={plant.toxicity} />}
          {plant && prep && <PrepLegend modernLabel={q.modern && modern ? `Modern lab: ${modern.label}` : 'Modern lab method (turn on to compare)'} />}
          {body}
        </div>
      </div>
    </SiteShell>
  );
}
