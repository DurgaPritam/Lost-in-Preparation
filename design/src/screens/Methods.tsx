import type { CheckOutcome, MethodComparison, Metric, MetricValue, PositiveControl } from '../types';
import {
  AppShell, Card, ChartTable, Taxon, DataTable, EvidenceStatusBadge, ExtractionDetectionExplainer, HeuristicMarker, LikelihoodBar, PrepTag,
  UnknownValue, cx, isKnownRange, rangeText,
} from '../index';
import { heuristics, validation } from '../contract';

/**
 * METHODS & VALIDATION — how far to trust each step.
 * - Pipeline: one box per stage, each with the evidence status of its validation.
 * - Every metric shows an interval and its evidence status; unmeasured
 *   metrics show "Not yet measured", not a blank.
 * - "Honest findings" gives the negative result (xTB worse than RDKit on
 *   logP) and the borderline positive control the same weight as successes.
 * - Pre-registered checks use outcome markers that don't rely on colour and
 *   never use toxicity red: ✓ Pass (filled), ✕ Fail (outlined), ◐ Borderline
 *   (dashed), ? Not yet run (unknown style).
 */
const fmt2 = (n: number) => n.toFixed(2);

export function OutcomeMarker({ outcome }: { outcome: CheckOutcome }) {
  if (outcome === 'not_run') return <UnknownValue label="Not yet run" />;
  const spec = {
    pass: { g: '✓', t: 'Pass', c: 'border-ink bg-ink text-paper' },
    fail: { g: '✕', t: 'Fail', c: 'border-ink bg-surface text-ink' },
    borderline: { g: '◐', t: 'Borderline', c: 'border-dashed border-ink bg-surface text-ink' },
  }[outcome];
  return (
    <span className={cx('inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-sm font-medium', spec.c)}>
      <span aria-hidden>{spec.g}</span>{spec.t}
    </span>
  );
}

/**
 * Phase 4 fix: a point is never shown without its interval. If the interval
 * is missing, the metric shows "Interval unknown" and the point is withheld
 * (it was previously printed on its own).
 */
const hasInterval = (v: MetricValue): v is MetricValue & { low: number; high: number } => v.low != null && v.high != null;
function MetricText({ v }: { v: MetricValue }) {
  if (v.point == null && v.low == null && v.high == null) return <UnknownValue variant="cell" label="Not yet measured" />;
  if (!hasInterval(v)) return <UnknownValue variant="cell" label="Interval unknown" reason="A point value exists but its interval does not, so it is not shown." />;
  return (
    <span className="num font-mono">
      {`${fmt2(v.low)}–${fmt2(v.high)}`}
      {v.point != null && <span className="text-ink-subtle"> (point {fmt2(v.point)})</span>}
    </span>
  );
}

/** Interval chart for a method comparison; scale fitted to the data. */
function IntervalChart({ c }: { c: MethodComparison }) {
  const max = Math.max(...c.methods.map((m) => m.value.high ?? 0)) * 1.15 || 1;
  const pct = (n: number) => `${(n / max) * 100}%`;
  return (
    <div className="flex flex-col gap-3">
      <span className="text-xs text-ink-subtle">{c.methods[0]?.value.unit} · {c.direction === 'lower_better' ? 'lower is better' : 'higher is better'}</span>
      {c.methods.map((m) => (
        <div key={m.name} className="flex flex-col gap-1">
          <span className="text-sm font-medium">{m.name}</span>
          <div
            role="img"
            aria-label={`${m.name}: ${m.value.low != null && m.value.high != null ? `${fmt2(m.value.low)} to ${fmt2(m.value.high)}` : 'unknown'}`}
            className="relative h-3 rounded-sm border border-border-strong bg-sunken"
          >
            {hasInterval(m.value) && (
              <span className="absolute top-0 h-full rounded-sm bg-ink-muted" style={{ left: pct(m.value.low), width: pct(m.value.high - m.value.low) }} />
            )}
            {hasInterval(m.value) && m.value.point != null && <span className="absolute -top-0.5 h-4 w-0.5 -translate-x-1/2 bg-ink" style={{ left: pct(m.value.point) }} />}
          </div>
          <MetricText v={m.value} />
        </div>
      ))}
      <ChartTable
        caption={`${c.question} (${c.methods[0]?.value.unit}; ${c.direction === 'lower_better' ? 'lower is better' : 'higher is better'})`}
        headers={['Method', 'Interval', 'Point']}
        numeric={[1, 2]}
        rows={c.methods.map((m) => [
          m.name,
          hasInterval(m.value) ? `${fmt2(m.value.low)}–${fmt2(m.value.high)}` : <UnknownValue label="Interval unknown" />,
          hasInterval(m.value) && m.value.point != null ? fmt2(m.value.point) : <UnknownValue />,
        ])}
      />
    </div>
  );
}

function ControlCard({ pc }: { pc: PositiveControl }) {
  return (
    <Card
      eyebrow="Positive control"
      title={<><span>{pc.compound}</span> <span className="font-normal text-ink-muted">in</span> <Taxon name={pc.taxon} /></>}
      meta={<><OutcomeMarker outcome={pc.outcome} /><EvidenceStatusBadge status={pc.evidence} size="sm" /></>}
    >
      <p className="m-0 text-sm text-ink-muted">Expected: {pc.expected}</p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {[pc.a, pc.b].map((x) => (
          <div key={x.label} className="flex flex-col gap-2">
            <PrepTag prep={x.preparation} />
            <LikelihoodBar range={x.likelihood} family={x.preparation.family} label={x.label} width="full" />
          </div>
        ))}
      </div>
      <p className="m-0 max-w-prose text-base">{pc.explanation}</p>
      <ChartTable
        caption={`${pc.compound} in ${pc.taxon}: predicted extraction, range 0–1`}
        headers={['Preparation', 'Range', 'Point']}
        numeric={[1, 2]}
        rows={[pc.a, pc.b].map((x) => [
          x.label,
          isKnownRange(x.likelihood) ? rangeText(x.likelihood) : <UnknownValue />,
          isKnownRange(x.likelihood) && x.likelihood.point != null ? x.likelihood.point.toFixed(2) : <UnknownValue />,
        ])}
      />
    </Card>
  );
}

export function Methods({ onNavigate, data = validation }: { onNavigate?: (p: string) => void; data?: typeof validation }) {
  return (
    <AppShell current="methods" onNavigate={onNavigate}>
      <section aria-labelledby="pipe" className="flex flex-col gap-4">
        <h2 id="pipe" className="m-0 font-serif text-2xl font-medium">Pipeline</h2>
        <ol className="m-0 grid list-none grid-cols-1 gap-3 p-0 sm:grid-cols-2 lg:grid-cols-4">
          {data.pipeline.map((s, i) => (
            <li key={s.id} className="flex flex-col gap-2 rounded border border-border bg-surface p-4">
              <span className="font-mono text-xs text-ink-subtle">{i + 1} of {data.pipeline.length}{i < data.pipeline.length - 1 ? ' →' : ''}</span>
              <span className="text-base font-semibold">{s.name}</span>
              <span className="text-sm text-ink-muted">{s.does}</span>
              <span className="text-sm">{s.tool ?? <UnknownValue label="Tool not documented yet" />}</span>
              <EvidenceStatusBadge status={s.validation} size="sm" />
            </li>
          ))}
        </ol>
        <ExtractionDetectionExplainer />
      </section>

      <section aria-labelledby="metrics" className="flex flex-col gap-4">
        <h2 id="metrics" className="m-0 font-serif text-2xl font-medium">Metrics</h2>
        <DataTable<Metric>
          caption="Every metric with its interval and evidence status (mock values)"
          rows={data.metrics}
          rowKey={(m) => m.id}
          columns={[
            { key: 'stage', header: 'Stage', render: (m) => m.stage },
            { key: 'name', header: 'Metric', render: (m) => <span className="flex flex-col gap-0.5">{m.name}{m.note && <span className="text-xs text-ink-subtle">{m.note}</span>}</span> },
            // Not sortable: metrics have different units, so ordering them by value would be meaningless.
            { key: 'v', header: 'Value', hint: 'interval (point)', numeric: true, render: (m) => <span className="flex flex-col items-end"><MetricText v={m.value} /><span className="text-xs text-ink-subtle">{m.value.unit}</span></span> },
            { key: 'n', header: 'n', numeric: true, sortValue: (m) => m.n, render: (m) => m.n ?? <UnknownValue /> },
            { key: 'ev', header: 'Evidence', render: (m) => <EvidenceStatusBadge status={m.evidence} size="sm" /> },
          ]}
        />
      </section>

      <section aria-labelledby="honest" className="flex flex-col gap-4">
        <h2 id="honest" className="m-0 font-serif text-2xl font-medium">Honest findings</h2>
        <p className="m-0 max-w-prose text-base text-ink-muted">Results that went against us are reported at the same weight as the ones that didn’t.</p>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {data.comparisons.map((c) => (
            <Card
              key={c.id}
              eyebrow="Negative result"
              title={c.question}
              meta={<>
                {/* Phase 4: the card now shows the pre-registered outcome it answers (it was only in the table). */}
                {(() => { const p = data.preregistered.find((x) => x.id === c.preregisteredId); return p ? <span className="inline-flex items-center gap-1.5"><OutcomeMarker outcome={p.outcome} /><span className="text-xs text-ink-subtle">pre-registered</span></span> : null; })()}
                <EvidenceStatusBadge status={c.evidence} size="sm" />
              </>}
            >
              <IntervalChart c={c} />
              <p className="m-0 text-base"><strong className="font-medium">Finding.</strong> {c.finding}</p>
              <p className="m-0 text-base"><strong className="font-medium">Decision.</strong> {c.decision}</p>
            </Card>
          ))}
          {data.positiveControls.map((pc) => <ControlCard key={pc.id} pc={pc} />)}
        </div>
      </section>

      <section aria-labelledby="prereg" className="flex flex-col gap-4">
        <h2 id="prereg" className="m-0 font-serif text-2xl font-medium">Pre-registered checks</h2>
        <DataTable
          caption="Criteria fixed before results were seen"
          rows={data.preregistered}
          rowKey={(p) => p.id}
          columns={[
            { key: 'c', header: 'Criterion', render: (p) => p.criterion },
            { key: 'd', header: 'Registered', sortValue: (p) => p.registeredOn, render: (p) => p.registeredOn ? <span className="font-mono text-sm">{p.registeredOn}</span> : <UnknownValue /> },
            { key: 'o', header: 'Outcome', render: (p) => <span className="flex flex-col items-start gap-1"><OutcomeMarker outcome={p.outcome} /><span className="text-xs text-ink-subtle">{p.detail}</span></span> },
            { key: 'e', header: 'Evidence', render: (p) => <EvidenceStatusBadge status={p.evidence} size="sm" /> },
          ]}
        />
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section aria-labelledby="heur" className="flex flex-col gap-3">
          <h2 id="heur" className="m-0 font-serif text-2xl font-medium">Heuristics register</h2>
          <ul className="m-0 flex list-none flex-col gap-3 p-0">
            {heuristics.map((h) => (
              <li key={h.id} className="flex flex-col gap-1 rounded border border-border bg-surface p-4">
                <HeuristicMarker heuristic={h} />
                <span className="text-sm text-ink-muted">{h.rule}</span>
              </li>
            ))}
          </ul>
        </section>
        <section aria-labelledby="lim" className="flex flex-col gap-3">
          <h2 id="lim" className="m-0 font-serif text-2xl font-medium">Limitations</h2>
          <ol className="m-0 flex flex-col gap-2 pl-5 text-base">
            {data.limitations.map((l) => <li key={l}>{l}</li>)}
          </ol>
        </section>
      </div>
    </AppShell>
  );
}
