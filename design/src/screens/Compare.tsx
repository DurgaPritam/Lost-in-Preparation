import { useEffect, useId, useState } from 'react';
import type { CompoundEstimate, Driver, PreparationProfile, SpeciesProfile } from '../types';
import {
  AppShell, ChartTable, Taxon, ErrorState, ExtractionDetectionExplainer, HeuristicMarker, LikelihoodBar, LoadingState, PrepLegend, PrepTag,
  SourceConfidenceMarker, ToxicityBadge, ToxicityNotice, UnknownValue, compareRanges, cx, isKnownRange, rangeText, slug,
  DRIVER_LABEL, MarkHistorical, MarkModern,
} from '../index';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';
import { PROFILES, loadProfile } from './mock';

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
const HEURISTIC = {
  heat: { id: 'heat_sensitivity', label: 'Heat sensitivity', rule: 'Heat is treated as reducing volatile and heat-labile compounds and raising extraction of stable ones.' },
  acidity: { id: 'acidity', label: 'Acidity', rule: 'Acidic vehicles are treated as favouring extraction of basic compounds as salts.' },
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
              {d.heuristic && (d.id === 'heat' || d.id === 'acidity') ? (
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
        <div className="flex flex-col gap-1">
          <span className="text-base font-medium text-ink">{a.compound}</span>
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

function PrepColumnHeader({ p, side, options, onPick, onNavigate }: { p: PreparationProfile; side: 'A' | 'B'; options: PreparationProfile[]; onPick: (id: string) => void; onNavigate?: (path: string) => void }) {
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
          <a
            href={`/recipes/${p.origin.recipeId}`}
            onClick={onNavigate ? (e) => { e.preventDefault(); onNavigate(`/recipes/${(p.origin as { recipeId: string }).recipeId}`); } : undefined}
            className="text-ink underline underline-offset-2"
          >
            From recipe
          </a>
          <SourceConfidenceMarker confidence={p.origin.source === 'pliny_nh' ? sourcePliny : sourceCulpeper} compact />
        </div>
      ) : (
        <span className="text-sm text-ink-muted">{p.origin.citation}</span>
      )}
    </div>
  );
}

export function Compare({ initialSpecies = 'Artemisia absinthium', onNavigate, load = loadProfile }: {
  initialSpecies?: string; onNavigate?: (p: string) => void; load?: (taxon: string) => Promise<SpeciesProfile>;
}) {
  const [species, setSpecies] = useState(initialSpecies);
  const [state, setState] = useState<{ status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; profile: SpeciesProfile }>({ status: 'loading' });
  const [aId, setAId] = useState<string | null>(null);
  const [bId, setBId] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const speciesId = useId();

  useEffect(() => {
    let live = true;
    setState({ status: 'loading' });
    load(species)
      .then((profile) => {
        if (!live) return;
        setState({ status: 'ready', profile });
        const hist = profile.preparations.find((p) => p.preparation.family === 'historical') ?? profile.preparations[0];
        const mod = profile.preparations.find((p) => p.preparation.family === 'modern' && p.id !== hist.id) ?? profile.preparations[1];
        setAId(hist.id);
        setBId(mod?.id ?? null);
      })
      .catch((e: Error) => live && setState({ status: 'error', message: e.message }));
    return () => { live = false; };
  }, [species, attempt, load]);

  return (
    <AppShell current="compare" onNavigate={onNavigate}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 sm:w-bar-md">
          <label htmlFor={speciesId} className="text-sm font-medium">Species</label>
          <select
            id={speciesId}
            value={species}
            onChange={(e) => setSpecies(e.target.value)}
            className="h-10 rounded border border-border-strong bg-surface px-3 text-base italic text-ink"
          >
            {Object.keys(PROFILES).map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <ExtractionDetectionExplainer />
      </div>

      {state.status === 'loading' && <LoadingState label={`Loading extraction profile for ${species}`} rows={5} />}
      {state.status === 'error' && (
        <ErrorState title="Couldn’t load this species’ profile" body="Nothing has changed on the page. You can try again." detail={state.message} onRetry={() => setAttempt((n) => n + 1)} />
      )}
      {state.status === 'ready' && (() => {
        const prof = state.profile;
        const A = prof.preparations.find((p) => p.id === aId) ?? prof.preparations[0];
        const B = prof.preparations.find((p) => p.id === bId) ?? prof.preparations[1];
        if (!B) return <p className="m-0 text-base text-ink-muted">Only one preparation is recorded for this species, so there is nothing to compare yet.</p>;
        const classes = [...new Set(A.estimates.map((e) => e.compoundClass))];
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
              <PrepColumnHeader p={A} side="A" options={prof.preparations.filter((p) => p.id !== B.id)} onPick={setAId} onNavigate={onNavigate} />
              <PrepColumnHeader p={B} side="B" options={prof.preparations.filter((p) => p.id !== A.id)} onPick={setBId} onNavigate={onNavigate} />
            </div>
            <PrepLegend />

            {classes.map((cls) => (
              <section key={cls} aria-labelledby={`cls-${slug(cls)}`} className="flex flex-col">
                <h3 id={`cls-${slug(cls)}`} className="m-0 pb-2 text-lg font-semibold">{cls}</h3>
                <ul className="m-0 list-none p-0">
                  {A.estimates.filter((e) => e.compoundClass === cls).map((ea) => {
                    const eb = B.estimates.find((x) => x.compound === ea.compound);
                    return eb ? <CompoundRow key={ea.compound} a={ea} b={eb} left={A} right={B} /> : (
                      <li key={ea.compound} className="flex flex-wrap items-center gap-3 border-t border-border py-4">
                        <span className="text-base font-medium">{ea.compound}</span>
                        <UnknownValue label={`Not estimated for preparation B`} />
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))}
            <ChartTable
              caption={`Predicted extraction for ${prof.taxon}: ${A.label} (A) vs ${B.label} (B), range 0–1`}
              headers={['Compound', 'Class', `A · ${A.label}`, `B · ${B.label}`, 'Comparison']}
              numeric={[2, 3]}
              rows={A.estimates.map((ea) => {
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
