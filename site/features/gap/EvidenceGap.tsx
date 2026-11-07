'use client';

import { useState } from 'react';
import type { AuditBreakdown, MatchState, ReportingGapRow, ReportingGapView, SourceConfidence, SourceWork } from '@/lib/types';
import { pct } from '@/lib/data/format';
import { INFLATED_SOLVENT_NOTE, SENSITIVITY_LABEL } from '@/lib/data/selectors/gap';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { ChartTable } from '@/components/base/ChartTable';
import { LinkButton } from '@/components/base/Button';
import { SegmentedControl } from '@/components/base/Controls';
import { Tooltip } from '@/components/base/Tooltip';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * THE EVIDENCE GAP (design v2 screens/EvidenceGap.tsx), from metrics.reportingGap.
 * SITE: the solvent row carries the inflated-by-construction caveat wherever it appears; "none of the five", the
 * all-retrieved-studies figures and the v3 screening are shown below the rows; "did it match" uses audit v2 (the
 * pre-registered re-analysis) with its small-n note, and links to v1 (as pre-registered, with its design flaw) in Docs.
 */
const ciText = (ci: [number, number] | null) => (ci ? `${pct(ci[0])}–${pct(ci[1])}` : 'not computed');

/** SITE: the AI-assisted sensitivity check (provisional) under each row; the frozen share above is unchanged. */
function sensText(r: ReportingGapRow): string {
  const s = r.sensitivity;
  if (!s) return '';
  if ('notComputed' in s) return s.notComputed;
  const c = s.checkedRule && s.checkedAi ? ` On the ${s.checkedRule[1]} checked studies: ${s.checkedRule[0]} stated by the extractor, ${s.checkedAi[0]} by the AI coder.` : '';
  return `${pct(s.point)} (95% interval ${pct(s.low)}–${pct(s.high)}) if the extractor's error rates from the AI check applied.${c}`;
}

function Sensitivity({ r }: { r: ReportingGapRow }) {
  return (
    <p className="m-0 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-ink-muted md:col-span-12">
      <EvidenceStatusBadge wording="validation" status="provisional" size="sm" detail="An AI coder's reading of 40 studies stands in for the truth. Not human validation." />
      <span><span className="font-semibold text-ink">{SENSITIVITY_LABEL}:</span> {sensText(r)}</span>
    </p>
  );
}

function GapRow({ r, i }: { r: ReportingGapRow; i: number }) {
  const p = r.stated / r.n;
  const tip = (
    <span className="flex flex-col gap-1">
      <span className="font-semibold">{r.label}</span>
      <span>{r.stated} of {r.n} studies state it ({pct(p)})</span>
      <span className="text-ink-muted">95% interval: {ciText(r.ci)}</span>
      {r.inflated && <span className="text-ink-subtle">{INFLATED_SOLVENT_NOTE}</span>}
    </span>
  );
  return (
    <li className="grid grid-cols-1 items-center gap-2 md:grid-cols-12 md:gap-4">
      <span className="text-base font-medium text-ink md:col-span-3">{r.label}{r.inflated && <span className="ml-1 text-xs font-normal text-ink-subtle">(inflated)</span>}</span>
      <Tooltip content={tip} className="md:col-span-7">
        <button
          type="button"
          aria-label={`${r.label}: ${r.stated} of ${r.n} studies state it, ${pct(p)}; 95% interval ${r.ci ? `${pct(r.ci[0])} to ${pct(r.ci[1])}` : 'not computed'}.${r.inflated ? ' Inflated by construction.' : ''}`}
          className="relative block h-7 w-full overflow-visible rounded-full border border-border-strong bg-hatch-unknown"
        >
          <span aria-hidden className="bar-motion absolute inset-y-0 left-0 rounded-full bg-ink" style={{ width: `${p * 100}%`, transitionDelay: `${i * 40}ms` }} />
          {r.ci && (
            <span aria-hidden className="absolute top-1/2 h-0.5 -translate-y-1/2 bg-hist-edge" style={{ left: `${r.ci[0] * 100}%`, width: `${(r.ci[1] - r.ci[0]) * 100}%` }}>
              <span className="absolute -top-1.5 left-0 h-3.5 w-0.5 bg-hist-edge" /><span className="absolute -top-1.5 right-0 h-3.5 w-0.5 bg-hist-edge" />
            </span>
          )}
        </button>
      </Tooltip>
      <span className="num font-mono text-sm text-ink md:col-span-2 md:text-right">{r.stated}/{r.n} · {pct(p)}</span>
      {r.sensitivity && <Sensitivity r={r} />}
      {r.inflated && <p role="note" className="m-0 rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink md:col-span-12"><span className="font-semibold">Solvent share is inflated by construction.</span> {INFLATED_SOLVENT_NOTE.replace(/^Inflated by construction: a/, 'A')}</p>}
    </li>
  );
}

function MatchStrip({ label, c, total }: { label: string; c: Record<MatchState, number>; total: number }) {
  const w = (n: number) => `${(n / Math.max(total, 1)) * 100}%`;
  return (
    <div className="flex flex-col gap-1.5">
      <span className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
        <span className="font-medium text-ink">{label}</span>
        <span className="num font-mono text-ink-muted">= {c.matches} · ≠ {c.differs} · ? {c.not_stated}{c.no_analogue > 0 && ` · no analogue ${c.no_analogue}`}</span>
      </span>
      <span role="img" aria-label={`${label}: ${c.matches} same as the recipe, ${c.differs} different, ${c.not_stated} not stated${c.no_analogue ? `, ${c.no_analogue} no modern analogue` : ''}, of ${total}`} className="flex h-3 overflow-hidden rounded-full border border-border-strong">
        <span className="h-full bg-hist-solid" style={{ width: w(c.matches) }} />
        <span className="h-full bg-sunken" style={{ width: w(c.differs) }} />
        <span className="h-full bg-hatch-unknown" style={{ width: w(c.not_stated) }} />
        {c.no_analogue > 0 && <span className="h-full border-l border-dashed border-unk-line bg-unk-bg" style={{ width: w(c.no_analogue) }} />}
      </span>
    </div>
  );
}

interface AuditLike {
  v2: { breakdowns: AuditBreakdown[]; units: number };
  auditV2: { label: string; units: number; unknownUnits: number; noModernAnalogueUnits: number; overallFidelity: { n?: number | null } } | null;
  confidences: Record<SourceWork, SourceConfidence>;
}

export function EvidenceGap({ gap, audit }: { gap: ReportingGapView; audit: AuditLike }) {
  const [order, setOrder] = useState<'least' | 'most'>('least');
  const rows = [...gap.rows].sort((a, b) => (order === 'least' ? a.stated / a.n - b.stated / b.n : b.stated / b.n - a.stated / a.n));
  const head = gap.rows.find((r) => r.field === gap.headline.field) ?? null;
  const v2 = audit.auditV2;
  const SOURCE_NAME: Record<SourceWork, string> = { culpeper_1652: 'Culpeper 1652', culpeper_1850: 'Culpeper 1850', pliny_nh: 'Pliny' };

  return (
    <SiteShell current="gap">
      <PageHeader eyebrow="The evidence gap" title={gap.headline.text} />
      <section className="grid grid-cols-1 items-end gap-6 rounded-xl border border-border bg-surface p-6 shadow-1 md:grid-cols-12 md:p-10">
        <div className="flex flex-col gap-2 md:col-span-7">
          {head ? (
            <>
              <span className="font-display text-5xl text-ink">{head.stated}<span className="text-ink-subtle"> / {head.n}</span></span>
              <span className="text-md text-ink-muted">studies that prepared the plant state whether it was fresh or dried · {pct(head.stated / head.n)} (95% interval {ciText(head.ci)})</span>
            </>
          ) : <UnknownValue label="Not computed" />}
        </div>
        <div className="flex flex-wrap items-center gap-2 md:col-span-5 md:justify-end">
          {head && <EvidenceStatusBadge status={head.evidence} detail="“Stated” = coded by the rule-based extractor; its accuracy awaits the 40-study hand-check." />}
          <span className="font-mono text-xs text-ink-subtle">descriptive · not a hypothesis test</span>
        </div>
      </section>

      <section aria-labelledby="details" className="flex flex-col gap-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-col gap-1">
            <h2 id="details" className="m-0 font-display text-2xl text-ink">How often each preparation detail is stated</h2>
            <p className="m-0 text-sm text-ink-muted">Solid = stated · hatched = not stated (unknown) · whisker = 95% interval. Hover, focus or tap a bar for n.</p>
          </div>
          <SegmentedControl label="Order" size="sm" value={order} onChange={setOrder} options={[{ value: 'least', label: 'Least reported first' }, { value: 'most', label: 'Most reported first' }]} />
        </div>
        <ol className="m-0 flex list-none flex-col gap-4 p-0">
          {rows.map((r, i) => <GapRow key={r.field} r={r} i={i} />)}
        </ol>
        {gap.none && (
          <p className="m-0 text-base text-ink">
            <span className="font-semibold">{gap.none.label}:</span> <span className="num font-mono">{gap.none.stated} of {gap.none.n} · {pct(gap.none.stated / gap.none.n)}</span> <span className="text-ink-muted">(95% interval {ciText(gap.none.ci)})</span>
          </p>
        )}
        <ChartTable
          caption="Preparation details stated by modern studies that prepared the plant (95% Wilson interval)"
          headers={['Detail', 'Stated', 'Studies (n)', 'Proportion', '95% interval', SENSITIVITY_LABEL]}
          numeric={[1, 2, 3, 4]}
          rows={[...rows, ...(gap.none ? [gap.none] : [])].map((r) => [r.inflated ? `${r.label} (inflated by construction)` : r.label, r.stated, r.n, pct(r.stated / r.n), r.ci ? ciText(r.ci) : <UnknownValue />, r.sensitivity ? sensText(r) : <UnknownValue label="Not computed" />])}
        />
        <p className="m-0 max-w-prose text-sm text-ink-subtle">{gap.method}</p>
        {gap.extra.length > 0 && (
          <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-5">
            <h3 className="m-0 text-base font-semibold text-ink">Other study sets</h3>
            <ul className="m-0 flex list-none flex-col gap-1.5 p-0 text-sm">
              {gap.extra.map((x) => (
                <li key={x.label} className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-ink">{x.label}</span>
                  <span className="num font-mono text-ink-muted">{x.stated} of {x.n} · {pct(x.stated / x.n)} (95% interval {ciText(x.ci)})</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section aria-labelledby="match" className="flex flex-col gap-5">
        <h2 id="match" className="m-0 font-display text-2xl text-ink">When they did say, did it match the recipe?</h2>
        <p role="note" className="m-0 max-w-prose rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink">
          <span className="font-semibold">Audit v2{v2 ? ` · ${v2.label}` : ''}. Small n:</span> {v2 ? <>only {v2.overallFidelity.n ?? 'an unknown number of'} (plant–use pair, study) units have a known status; {v2.unknownUnits} are unknown and {v2.noModernAnalogueUnits} have no modern analogue.</> : 'counts not computed.'} Too few to estimate a field-wide rate. Audit v1 (as pre-registered, with its design flaw) is in Methods &amp; data.
        </p>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {audit.v2.breakdowns.map((b) => (
            <div key={b.source} className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-5 shadow-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <SourceConfidenceMarker confidence={audit.confidences[b.source]} compact />
                <span className="num font-mono text-sm text-ink-muted">{b.plants} plants · {b.studies} units</span>
              </div>
              <MatchStrip label="Solvent" c={b.vehicle} total={b.studies} />
              <MatchStrip label="Heat" c={b.heat} total={b.studies} />
              <MatchStrip label="Filtration" c={b.filtration} total={b.studies} />
              <ChartTable caption={`${SOURCE_NAME[b.source]}: studies vs the recipe (audit v2)`} headers={['Detail', 'Same', 'Different', 'Not stated', 'No modern analogue']} numeric={[1, 2, 3, 4]}
                rows={([['Solvent', b.vehicle], ['Heat', b.heat], ['Filtration', b.filtration]] as const).map(([k, c]) => [k, c.matches, c.differs, c.not_stated, c.no_analogue])} />
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-ink-muted">
          <span className="inline-flex items-center gap-2"><span aria-hidden className="h-2.5 w-6 rounded-full border border-hist-edge bg-hist-solid" />Same as the recipe</span>
          <span className="inline-flex items-center gap-2"><span aria-hidden className="h-2.5 w-6 rounded-full border border-border-strong bg-sunken" />Different</span>
          <span className="inline-flex items-center gap-2"><span aria-hidden className="h-2.5 w-6 rounded-full border border-unk-line bg-hatch-unknown" />Not stated</span>
          <span className="inline-flex items-center gap-2"><span aria-hidden className="h-2.5 w-6 rounded-full border border-dashed border-unk-line bg-unk-bg" />No modern analogue</span>
        </div>
        <LinkButton href="/docs/#studies" className="w-max">Every study, field by field →</LinkButton>
      </section>
    </SiteShell>
  );
}
