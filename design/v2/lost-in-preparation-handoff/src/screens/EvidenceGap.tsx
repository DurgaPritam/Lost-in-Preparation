import { useState, type MouseEvent } from 'react';
import type { AuditBreakdown, MatchState, ReportingGapRow } from '../types';
import { ChartTable, EvidenceStatusBadge, LinkButton, PageHeader, SegmentedControl, SiteShell, SourceConfidenceMarker, Tooltip, UnknownValue, cx, pct } from '../index';
import { auditSummary, reportingGap } from '../contract';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';

/**
 * THE EVIDENCE GAP — the reporting-gap headline as an interactive visual.
 * Each preparation detail is a row: the solid part is studies that STATE the
 * detail, the hatched part is studies that don't (unknown, never zero), and
 * a whisker shows the 95% interval. Hover, focus or tap a row for n and the
 * interval. A table fallback carries the same numbers.
 */
function GapRow({ r, i }: { r: ReportingGapRow; i: number }) {
  const p = r.stated / r.n;
  const tip = (
    <span className="flex flex-col gap-1">
      <span className="font-semibold">{r.label}</span>
      <span>{r.stated} of {r.n} studies state it ({pct(p)})</span>
      <span className="text-ink-muted">95% interval: {r.ci ? `${pct(r.ci[0])}–${pct(r.ci[1])}` : 'not computed'}</span>
    </span>
  );
  return (
    <li className="grid grid-cols-1 items-center gap-2 md:grid-cols-12 md:gap-4">
      <span className="text-base font-medium text-ink md:col-span-3">{r.label}</span>
      <Tooltip content={tip} className="md:col-span-7">
        <button
          type="button"
          aria-label={`${r.label}: ${r.stated} of ${r.n} studies state it, ${pct(p)}; 95% interval ${r.ci ? `${pct(r.ci[0])} to ${pct(r.ci[1])}` : 'not computed'}.`}
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
    </li>
  );
}

function MatchStrip({ label, c, total }: { label: string; c: Record<MatchState, number>; total: number }) {
  const w = (n: number) => `${(n / Math.max(total, 1)) * 100}%`;
  return (
    <div className="flex flex-col gap-1.5">
      <span className="flex flex-wrap items-baseline justify-between gap-2 text-sm"><span className="font-medium text-ink">{label}</span><span className="num font-mono text-ink-muted">= {c.matches} · ≠ {c.differs} · ? {c.not_stated}</span></span>
      <span role="img" aria-label={`${label}: ${c.matches} same as the recipe, ${c.differs} different, ${c.not_stated} not stated, of ${total}`} className="flex h-3 overflow-hidden rounded-full border border-border-strong">
        <span className="h-full bg-hist-solid" style={{ width: w(c.matches) }} />
        <span className="h-full bg-sunken" style={{ width: w(c.differs) }} />
        <span className="h-full bg-hatch-unknown" style={{ width: w(c.not_stated) }} />
      </span>
    </div>
  );
}

export function EvidenceGap({ onNavigate, data = reportingGap, summary = auditSummary }: { onNavigate?: (p: string) => void; data?: typeof reportingGap; summary?: AuditBreakdown[] }) {
  const [order, setOrder] = useState<'least' | 'most'>('least');
  const rows = [...data.rows].sort((a, b) => (order === 'least' ? a.stated / a.n - b.stated / b.n : b.stated / b.n - a.stated / a.n));
  const head = data.rows.find((r) => r.field === data.headline.field)!;
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); onNavigate(path); } };

  return (
    <SiteShell current="gap" onNavigate={onNavigate}>
      <PageHeader eyebrow="The evidence gap" title={data.headline.text} />
      <section className="grid grid-cols-1 items-end gap-6 rounded-xl border border-border bg-surface p-6 shadow-1 md:grid-cols-12 md:p-10">
        <div className="flex flex-col gap-2 md:col-span-7">
          <span className="font-display text-5xl text-ink">{head.stated}<span className="text-ink-subtle"> / {head.n}</span></span>
          <span className="text-md text-ink-muted">studies state whether the plant was fresh or dried · {pct(head.stated / head.n)} (95% interval {head.ci ? `${pct(head.ci[0])}–${pct(head.ci[1])}` : 'not computed'})</span>
        </div>
        <div className="flex flex-wrap items-center gap-2 md:col-span-5 md:justify-end">
          <EvidenceStatusBadge status={head.evidence} />
          <span className="font-mono text-xs text-ink-subtle">mock counts</span>
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
        <ChartTable
          caption="Preparation details stated by modern studies (mock counts, 95% Wilson interval)"
          headers={['Detail', 'Stated', 'Studies (n)', 'Proportion', '95% interval']}
          numeric={[1, 2, 3, 4]}
          rows={rows.map((r) => [r.label, r.stated, r.n, pct(r.stated / r.n), r.ci ? `${pct(r.ci[0])}–${pct(r.ci[1])}` : <UnknownValue />])}
        />
        <p className="m-0 max-w-prose text-sm text-ink-subtle">{data.method}</p>
      </section>

      <section aria-labelledby="match" className="flex flex-col gap-5">
        <h2 id="match" className="m-0 font-display text-2xl text-ink">When they did say, did it match the recipe?</h2>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {summary.map((b) => (
            <div key={b.source} className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-5 shadow-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <SourceConfidenceMarker confidence={b.source === 'pliny_nh' ? sourcePliny : sourceCulpeper} compact />
                <span className="num font-mono text-sm text-ink-muted">{b.plants} plants · {b.studies} studies</span>
              </div>
              <MatchStrip label="Solvent" c={b.vehicle} total={b.studies} />
              <MatchStrip label="Heat" c={b.heat} total={b.studies} />
              <MatchStrip label="Filtration" c={b.filtration} total={b.studies} />
              <ChartTable caption={`${b.source === 'pliny_nh' ? 'Pliny' : 'Culpeper'}: studies vs the recipe`} headers={['Detail', 'Same', 'Different', 'Not stated']} numeric={[1, 2, 3]}
                rows={([['Solvent', b.vehicle], ['Heat', b.heat], ['Filtration', b.filtration]] as const).map(([k, c]) => [k, c.matches, c.differs, c.not_stated])} />
            </div>
          ))}
        </div>
        <div className={cx('flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-ink-muted')}>
          <span className="inline-flex items-center gap-2"><span aria-hidden className="h-2.5 w-6 rounded-full border border-hist-edge bg-hist-solid" />Same as the recipe</span>
          <span className="inline-flex items-center gap-2"><span aria-hidden className="h-2.5 w-6 rounded-full border border-border-strong bg-sunken" />Different</span>
          <span className="inline-flex items-center gap-2"><span aria-hidden className="h-2.5 w-6 rounded-full border border-unk-line bg-hatch-unknown" />Not stated</span>
        </div>
        <LinkButton href="/docs#studies" onClick={go('/docs')} className="w-max">Every study, field by field →</LinkButton>
      </section>
    </SiteShell>
  );
}
