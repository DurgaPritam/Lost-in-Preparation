import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from 'react';
import type { CompoundEstimate, Driver, HeatLevel, LikelihoodRange, PreparationProfile, SpeciesProfile, Vehicle } from '../types';
import {
  ChartTable, EmptyState, ExtractionDetectionExplainer, HeuristicMarker, LikelihoodBar, LinkButton, LoadingState, PageHeader, PlateSlot, Popover,
  PrepLegend, PrepTag, SegmentedControl, SiteShell, Switch, Taxon, ToxicityBadge, ToxicityNotice, UnknownValue,
  compareRanges, cx, DRIVER_LABEL, fmt, isKnownRange, meanWidth, rangeText, slug,
} from '../index';
import { LAB_PLANTS, loadLabProfile } from '../contract/lab';
import { heuristics, plates } from '../contract';

/**
 * PREPARATION LAB — the core product.
 * Controls: plant · solvent (water, wine, vinegar, oil, honey) · heat (cold,
 * warm, boiled) · filtration · acidity · "compare with modern lab method".
 * The profile updates live, grouped by compound class, every value a range.
 *
 * States designed: loading · plant without a profile · combination without
 * an estimate (never interpolated) · wide uncertainty · toxic plant.
 * "Why did this change?" on every compound compares with the previous setting.
 */
export type Solvent = 'water' | 'wine' | 'vinegar' | 'oil' | 'honey';
export type Heat = Extract<HeatLevel, 'cold' | 'warm' | 'boiled'>;
export interface Settings { solvent: Solvent; heat: Heat; filtered: boolean; acidified: boolean }

const SOLVENTS: { value: Solvent; label: string }[] = [
  { value: 'water', label: 'Water' }, { value: 'wine', label: 'Wine' }, { value: 'vinegar', label: 'Vinegar' }, { value: 'oil', label: 'Oil' }, { value: 'honey', label: 'Honey' },
];
const HEATS: { value: Heat; label: string }[] = [{ value: 'cold', label: 'Cold' }, { value: 'warm', label: 'Warm' }, { value: 'boiled', label: 'Boiled' }];
const HEUR = { heat: heuristics.find((h) => h.id === 'heat_sensitivity')!, acidity: heuristics.find((h) => h.id === 'acidity')! };
const WIDE = 0.4;

const findPrep = (p: SpeciesProfile, s: Settings) =>
  p.preparations.find((x) => x.preparation.family === 'historical' && x.preparation.vehicle === (s.solvent as Vehicle) && x.preparation.heat === s.heat && x.preparation.filtered === s.filtered && !!x.preparation.acidified === s.acidified) ?? null;
const modernOf = (p: SpeciesProfile) => p.preparations.find((x) => x.preparation.family === 'modern') ?? null;
const settingsOf = (x: PreparationProfile): Settings => ({ solvent: x.preparation.vehicle as Solvent, heat: x.preparation.heat as Heat, filtered: !!x.preparation.filtered, acidified: !!x.preparation.acidified });

function Delta({ prev, now }: { prev?: LikelihoodRange; now: LikelihoodRange }) {
  if (!prev) return null;
  const v = compareRanges(now, prev);
  const txt = v === 'a' ? '↑ higher' : v === 'b' ? '↓ lower' : v === 'overlap' ? '≈ overlaps' : '? can’t compare';
  return <span className={cx('rounded-full px-2 py-0.5 text-xs font-medium', v === 'a' || v === 'b' ? 'bg-sunken text-ink' : 'text-ink-subtle')} title="Compared with the previous setting; ‘higher/lower’ only when the ranges do not overlap">{txt}</span>;
}

function DriverLine({ d, prev }: { d: Driver; prev?: Driver }) {
  const changed = prev && prev.effect !== d.effect;
  const effect = d.effect === 'unknown' ? <UnknownValue label="effect unknown" /> : <span>{d.effect === 'raises' ? '↑ raises' : d.effect === 'lowers' ? '↓ lowers' : '– little effect'}{d.strength && d.effect !== 'neutral' ? ` · ${d.strength}` : ''}</span>;
  return (
    <li className={cx('flex flex-col gap-0.5 rounded px-2 py-1.5', changed && 'bg-hist-bg')}>
      <span className="flex flex-wrap items-baseline gap-x-2">
        {d.heuristic && (d.id === 'heat' || d.id === 'acidity') ? <HeuristicMarker heuristic={HEUR[d.id]}>{DRIVER_LABEL[d.id]}</HeuristicMarker> : <span className="font-semibold">{DRIVER_LABEL[d.id]}</span>}
        {effect}
        {changed && <span className="text-xs font-semibold text-hist-fg">changed</span>}
      </span>
      {d.note && <span className="text-xs text-ink-subtle">{d.note}</span>}
    </li>
  );
}

function CompoundRow({ e, prev, modern, showModern }: { e: CompoundEstimate; prev?: CompoundEstimate; modern?: CompoundEstimate; showModern: boolean }) {
  return (
    <li className="grid grid-cols-1 gap-2 border-t border-border py-4 md:grid-cols-12 md:items-center md:gap-4">
      <div className="flex items-center justify-between gap-2 md:col-span-3 md:flex-col md:items-start">
        <span className="text-base font-semibold text-ink">{e.compound}</span>
        <Delta prev={prev?.likelihood} now={e.likelihood} />
      </div>
      <div className="md:col-span-7">
        <LikelihoodBar range={e.likelihood} compare={showModern ? modern?.likelihood ?? { low: null, high: null } : null} label={e.compound} />
      </div>
      <div className="md:col-span-2 md:justify-self-end">
        <Popover
          align="end"
          label={`Why did ${e.compound} change?`}
          triggerClassName="inline-flex h-8 items-center rounded-full border border-border-strong px-3 text-sm font-medium text-ink hover:bg-sunken"
          trigger={<>Why? <span aria-hidden className="ml-1">›</span></>}
        >
          <div className="flex flex-col gap-2">
            <span className="font-semibold">Why {e.compound} looks like this</span>
            {prev ? (
              <span className="text-ink-muted">Previous setting: {rangeText(prev.likelihood)} → now: {rangeText(e.likelihood)}. Highlighted drivers changed.</span>
            ) : <span className="text-ink-muted">Drivers for the current preparation.</span>}
            <ul className="m-0 flex list-none flex-col gap-1 p-0">
              {e.drivers.map((d) => <DriverLine key={d.id} d={d} prev={prev?.drivers.find((x) => x.id === d.id)} />)}
            </ul>
            <span className="text-xs text-ink-subtle">Drivers explain predicted extraction. They say nothing about how much the plant contained.</span>
          </div>
        </Popover>
      </div>
    </li>
  );
}

export function Lab({ onNavigate, initialPlant = 'Glycyrrhiza glabra', initial, load = loadLabProfile }: { onNavigate?: (p: string) => void; initialPlant?: string; initial?: Partial<Settings>; load?: (t: string) => Promise<SpeciesProfile | null> }) {
  const [plant, setPlant] = useState(initialPlant);
  const [profile, setProfile] = useState<SpeciesProfile | null | 'loading'>('loading');
  const [s, setS] = useState<Settings>(() => { const b: Settings = { solvent: 'water', heat: 'cold', filtered: true, acidified: false, ...initial }; b.acidified = b.solvent === 'vinegar' || b.acidified; return b; });
  const [showModern, setShowModern] = useState(false);
  const prevPrep = useRef<PreparationProfile | null>(null);
  const [prev, setPrev] = useState<PreparationProfile | null>(null);

  useEffect(() => {
    let live = true;
    setProfile('loading'); setPrev(null); prevPrep.current = null;
    load(plant).then((p) => live && setProfile(p));
    return () => { live = false; };
  }, [plant, load]);

  const ready = profile !== 'loading' && profile !== null ? profile : null;
  const prep = ready ? findPrep(ready, s) : null;
  const modern = ready ? modernOf(ready) : null;

  // Remember the last preparation that had data, for "Why did this change?" and deltas.
  useEffect(() => {
    if (prep && prevPrep.current && prevPrep.current.id !== prep.id) setPrev(prevPrep.current);
    if (prep) prevPrep.current = prep;
  }, [prep]);

  const update = (patch: Partial<Settings>) => setS((cur) => {
    const n = { ...cur, ...patch };
    if (patch.solvent) n.acidified = patch.solvent === 'vinegar'; // vinegar is inherently acidic
    return n;
  });

  const announce = profile === 'loading' ? `Loading ${plant}` : profile === null ? `No profile for ${plant}` : !prep ? 'No estimate for this combination' : `Showing ${prep.label} for ${plant}: ${prep.estimates.length} compounds`;
  const width = prep ? meanWidth(prep.estimates.map((e) => e.likelihood)) : null;
  const toxic = ready?.toxicity.category === 'toxic_reported';
  const plateFor = plates.find((p) => p.taxon === plant);
  const classes = prep ? [...new Set(prep.estimates.map((e) => e.compoundClass))] : [];
  const available = ready ? ready.preparations.filter((x) => x.preparation.family === 'historical') : [];
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); onNavigate(path); } };

  const controls = (
    <div className="flex flex-col gap-6 rounded-lg border border-border bg-surface p-5 shadow-1 lg:sticky lg:top-24">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="lab-plant" className="eyebrow text-ink-subtle">Plant</label>
        <select id="lab-plant" value={plant} onChange={(e) => setPlant(e.target.value)} className="h-11 w-full rounded-md border border-border-strong bg-paper px-3 text-base text-ink">
          {LAB_PLANTS.map((p) => <option key={p.taxon} value={p.taxon}>{p.common} — {p.taxon}</option>)}
        </select>
      </div>
      <SegmentedControl label="Solvent" options={SOLVENTS} value={s.solvent} onChange={(v) => update({ solvent: v })} size="sm" />
      <SegmentedControl label="Heat" options={HEATS} value={s.heat} onChange={(v) => update({ heat: v })} size="sm" />
      <div className="flex flex-col gap-4 border-t border-border pt-4">
        <Switch label="Filtration" description="Strained through cloth" checked={s.filtered} onChange={(v) => update({ filtered: v })} states={['Unstrained', 'Strained']} />
        <Switch label="Acidity" description={s.solvent === 'vinegar' ? 'Vinegar is acidic; always on' : 'Acid added to the preparation'} checked={s.acidified} onChange={(v) => s.solvent !== 'vinegar' && update({ acidified: v })} states={['Neutral', 'Acidified']} />
      </div>
      <div className="flex flex-col gap-2 border-t border-border pt-4">
        <Switch label="Compare with modern lab method" description={modern ? modern.label : 'No modern method recorded'} checked={showModern} onChange={setShowModern} />
      </div>
    </div>
  );

  let body: ReactNode;
  if (profile === 'loading') body = <LoadingState label={`Loading the extraction profile for ${plant}`} rows={5} />;
  else if (profile === null) body = (
    <EmptyState
      title="No profile for this plant yet"
      body={<>The name resolves to <Taxon name={plant} /> only at genus level, so there is no species-level compound profile to model. Choose another plant, or see its recipes in the Atlas.</>}
      action={<LinkButton href="/atlas" onClick={go('/atlas')} size="sm">Open the Recipe Atlas</LinkButton>}
    />
  );
  else if (!prep) body = (
    <EmptyState
      title="No estimate for this combination"
      body={<>We have not modelled <strong className="font-semibold">{SOLVENTS.find((x) => x.value === s.solvent)!.label.toLowerCase()}, {s.heat}, {s.filtered ? 'strained' : 'unstrained'}{s.acidified ? ', acidified' : ''}</strong> for this plant, and the Lab never guesses between settings. Try one of these:</>}
      action={
        <ul className="m-0 flex list-none flex-wrap justify-center gap-2 p-0">
          {available.slice(0, 6).map((x) => (
            <li key={x.id}><button type="button" onClick={() => setS(settingsOf(x))} className="inline-flex h-9 items-center rounded-full border border-border-strong px-3 text-sm font-medium hover:bg-sunken">{x.label}</button></li>
          ))}
        </ul>
      }
    />
  );
  else body = (
    <div className="flex flex-col gap-5">
      {width != null && width >= WIDE && (
        <div role="note" className="flex items-start gap-3 rounded-md border border-dashed border-border-strong bg-unk-bg p-4 text-sm text-ink">
          <span aria-hidden className="mt-0.5 font-mono">±</span>
          <p className="m-0"><strong className="font-semibold">Wide uncertainty.</strong> Ranges for this preparation are wide (average width {fmt(width)}). Differences from other preparations are unlikely to be meaningful.</p>
        </div>
      )}
      {classes.map((cls) => (
        <section key={cls} aria-labelledby={`cls-${slug(cls)}`}>
          <h3 id={`cls-${slug(cls)}`} className="m-0 pb-1 text-sm font-semibold uppercase tracking-caps text-ink-subtle">{cls}</h3>
          <ul className="m-0 list-none p-0">
            {prep.estimates.filter((e) => e.compoundClass === cls).map((e) => (
              <CompoundRow key={e.compound} e={e} prev={prev?.estimates.find((x) => x.compound === e.compound)} modern={modern?.estimates.find((x) => x.compound === e.compound)} showModern={showModern} />
            ))}
          </ul>
        </section>
      ))}
      <ChartTable
        caption={`Predicted extraction for ${plant}: ${prep.label}${showModern && modern ? ` vs ${modern.label}` : ''} (range 0–1)`}
        headers={showModern ? ['Compound', 'Class', 'This preparation', 'Modern lab method'] : ['Compound', 'Class', 'This preparation']}
        numeric={showModern ? [2, 3] : [2]}
        rows={prep.estimates.map((e) => {
          const m = modern?.estimates.find((x) => x.compound === e.compound);
          const row = [e.compound, e.compoundClass, isKnownRange(e.likelihood) ? rangeText(e.likelihood) : <UnknownValue />];
          return showModern ? [...row, m && isKnownRange(m.likelihood) ? rangeText(m.likelihood) : <UnknownValue />] : row;
        })}
      />
      <div className="flex flex-wrap gap-3 border-t border-border pt-5">
        <LinkButton href="/atlas" onClick={go('/atlas')}>Recipes using this plant</LinkButton>
        {!toxic && <LinkButton href="/planner" onClick={go('/planner')} variant="primary">Plan an experiment</LinkButton>}
      </div>
    </div>
  );

  return (
    <SiteShell current="lab" onNavigate={onNavigate}>
      <PageHeader eyebrow="Preparation Lab" title={<>Change the preparation. <i className="text-brand">Watch the profile respond.</i></>} lead="Every value is a predicted extraction range, not a measurement. Settings without a modelled estimate say so — the Lab never fills the gaps." />
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="lg:col-span-4">{controls}</div>
        <div className="flex min-w-0 flex-col gap-5 lg:col-span-8" aria-busy={profile === 'loading'}>
          <p className="sr-only" aria-live="polite">{announce}</p>
          <div className="flex flex-wrap items-start gap-4">
            <PlateSlot plate={plateFor} taxon={plant} size="thumb" />
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <h2 className="m-0 font-display text-2xl text-ink"><Taxon name={plant} /></h2>
              <div className="flex flex-wrap items-center gap-2">
                {ready && <ToxicityBadge record={ready.toxicity} />}
                {prep && <PrepTag prep={prep.preparation} />}
                <ExtractionDetectionExplainer />
              </div>
            </div>
          </div>
          {ready && <ToxicityNotice record={ready.toxicity} />}
          {prep && <PrepLegend modernLabel={showModern && modern ? `Modern lab: ${modern.label}` : 'Modern lab method (turn on to compare)'} />}
          {body}
        </div>
      </div>
    </SiteShell>
  );
}
