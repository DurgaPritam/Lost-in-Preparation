'use client';

import { useState } from 'react';
import type { BenchmarkRowView, Heuristic, PanelEntryView, PanelView } from '@/lib/types';
import { cx, pct } from '@/lib/data/format';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { Button } from '@/components/base/Button';
import { ChartTable } from '@/components/base/ChartTable';
import { SegmentedControl } from '@/components/base/Controls';
import { DataTable } from '@/components/base/DataTable';
import { Drawer } from '@/components/base/Drawer';
import { MarkHist, MarkMod } from '@/components/base/PrepTag';
import { Taxon } from '@/components/base/Taxon';
import { EmptyState } from '@/components/base/States';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { ToxicityBadge } from '@/components/honesty/ToxicityBadge';
import Link from '@/components/base/Link';

/**
 * LAB PLANNER: the recommended re-test panel (design v2 screens/LabPlanner.tsx layout; proposal approved 2026-11-07,
 * docs/LAB_PLANNER_PROPOSAL.md). SITE: the "Coming in this release" state is replaced by the exact-solver panel from
 * site-data/lab_panel.json. v2 (pre-registered, docs/QUBO_v2_RULE.md) is displayed; the original v1 result stays visible
 * with its notes. There is no toxic toggle: plants with toxicity reported are excluded and listed. The QAOA benchmark
 * is labelled "Benchmark against exact optimum" (neutral), never a validation or a priority for one experiment.
 */
const SOLVER: Record<string, string> = {
  exact: 'Exact (ILP)', anneal: 'Simulated annealing', greedy: 'Greedy', random: 'Random feasible panel',
  'qaoa-penalty': 'QAOA, penalty mixer', 'qaoa-xy': 'QAOA, XY mixer',
};
const WEIGHT: Record<string, string> = {
  alpha: 'Robust value (α)', beta_class: 'Compound-class coverage (β)', beta_indication: 'Indication coverage (β)', beta_prep: 'Preparation coverage (β)', gamma: 'Redundancy (γ)',
};
const solverLabel = (r: BenchmarkRowView) => `${SOLVER[r.solver] ?? r.solver}${r.p ? `, p = ${r.p}` : ''}`;
const num = (x: number | null, d = 3) => (x == null ? '—' : x.toFixed(d));

function Entry({ e, likely, onTrail }: { e: PanelEntryView; likely: Heuristic | undefined; onTrail: (e: PanelEntryView) => void }) {
  return (
    <li className="grid grid-cols-1 gap-4 rounded-lg border border-border bg-surface p-5 shadow-1 md:grid-cols-12 md:items-start">
      <span className="font-display text-4xl text-ink md:col-span-1">{e.position}</span>
      <div className="flex min-w-0 flex-col gap-2 md:col-span-7">
        <h3 className="m-0 break-words text-lg font-semibold text-ink"><Taxon name={e.species} />: {e.historical} vs {e.modern}</h3>
        <span className="flex flex-col gap-1 text-sm">
          <span className="inline-flex items-center gap-2"><MarkHist />Historical: {e.historical}</span>
          <span className="inline-flex items-center gap-2"><MarkMod />Modern: {e.modern}{e.modernIsDefault && <span className="text-ink-subtle"> (default comparator: no retrieved study used a modelled modern preparation)</span>}</span>
        </span>
        <LikelihoodBar range={e.gap} family="neutral" label={`${e.species}, ${e.historical} vs ${e.modern}`} measure="Robust profile gap (1 − cosine similarity), 5th–95th percentile" size="sm" />
        {e.coverageOnly && <p role="note" className="m-0 rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink">⚑ Entered on coverage, not gap: no compound likely to differ (robust gap {e.gap.low?.toFixed(3)}).</p>}
      </div>
      <dl className="m-0 grid grid-cols-1 gap-3 text-sm md:col-span-4">
        <div><dt className="eyebrow text-ink-subtle">Compounds likely to differ</dt><dd className="m-0 flex flex-wrap items-center gap-2"><span className="num font-mono">{e.differs}</span>{likely && <HeuristicMarker heuristic={likely} />}</dd></div>
        <div><dt className="eyebrow text-ink-subtle">Compound classes</dt><dd className="m-0">{e.classes.map((c) => c.replace(' (heuristic)', '')).join(', ') || '—'}</dd></div>
        <div><dt className="eyebrow text-ink-subtle">For</dt><dd className="m-0">{e.indication}</dd></div>
        <div><dt className="eyebrow text-ink-subtle">Status</dt><dd className="m-0 flex flex-wrap items-center gap-2"><EvidenceStatusBadge wording="validation" status="pending" size="sm" detail="A model-based hypothesis worth re-testing; no person has checked it." /><ToxicityBadge record={e.toxicity} withSources={false} /></dd></div>
      </dl>
      <div className="flex flex-wrap items-center gap-3 md:col-span-12">
        <Button size="sm" onClick={() => onTrail(e)}>Evidence trail</Button>
        {e.labHref && <Link href={e.labHref} className="text-sm text-brand underline">Open the historical preparation in the Lab</Link>}
        <span className="text-xs text-ink-subtle">{e.caveats[0]}{e.caveats.length > 1 ? ` (+${e.caveats.length - 1} more in the trail)` : ''}</span>
      </div>
    </li>
  );
}

function Bars({ rows, metric, title, reference }: { rows: BenchmarkRowView[]; metric: 'ar' | 'pOptimum'; title: string; reference: number | null }) {
  const vals = rows.map((r) => r[metric]).filter((v): v is number => v != null);
  const max = metric === 'ar' ? 1 : Math.max(...vals, reference ?? 0, 1e-9);
  return (
    <div className="flex flex-col gap-2">
      <h4 className="m-0 text-base font-semibold text-ink">{title}</h4>
      <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
        {rows.map((r) => {
          const v = r[metric];
          return (
            <li key={`${r.solver}${r.p}`} className="grid grid-cols-12 items-center gap-2 text-sm">
              <span className="col-span-5 break-words text-ink-muted">{solverLabel(r)}</span>
              <span aria-hidden className="relative col-span-5 block h-4 rounded-full border border-border-strong bg-sunken">
                {v != null && <span aria-hidden className={cx('absolute inset-y-0 left-0 rounded-full', r.solver.startsWith('qaoa') ? 'bg-mod-solid' : 'bg-ink')} style={{ width: `${Math.max(0, Math.min(1, v / max)) * 100}%` }} />}
                {reference != null && <span aria-hidden className="absolute -inset-y-1 w-0.5 bg-hist-edge" style={{ left: `${Math.min(1, reference / max) * 100}%` }} />}
              </span>
              <span className="num col-span-2 text-right font-mono text-ink">{num(v)}</span>
            </li>
          );
        })}
      </ul>
      {reference != null && <span className="inline-flex items-center gap-2 text-xs text-ink-subtle"><span aria-hidden className="h-3 w-0.5 bg-hist-edge" />Uniform random feasible panel: {num(reference)}</span>}
    </div>
  );
}

function Benchmark({ v }: { v: PanelView }) {
  const [n, setN] = useState(String(v.benchmarkSizes[0] ?? ''));
  const rows = v.benchmark.filter((r) => String(r.n) === n);
  const shown = rows.filter((r) => r.solver !== 'random');
  const uniform = rows.find((r) => r.solver === 'random')?.pOptimum ?? null;
  const randomAr = rows.find((r) => r.solver === 'random')?.ar ?? null;
  return (
    <section aria-labelledby="bench" className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-6 shadow-1">
      <div className="flex flex-wrap items-center gap-3">
        <h2 id="bench" className="m-0 font-display text-2xl text-ink">Quantum benchmark</h2>
        <EvidenceStatusBadge wording="validation" status="benchmark" size="sm" />
      </div>
      <p className="m-0 max-w-prose text-ink-muted">The same problem, solved by exact optimisation, two classical heuristics and QAOA (simulated on a laptop) on seeded instances of increasing size. This measures the methods, not the panel: the panel above always comes from the exact solver.</p>
      <SegmentedControl label="Candidates (n)" size="sm" value={n} onChange={setN} options={v.benchmarkSizes.map((s) => ({ value: String(s), label: String(s) }))} />
      <p className="m-0 text-base text-ink"><span className="font-semibold">Which method wins at n = {n}:</span> {v.winners[n] ?? '—'}</p>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Bars rows={shown} metric="ar" title="Approximation ratio (1 = optimum)" reference={randomAr} />
        <Bars rows={shown.filter((r) => r.pOptimum != null)} metric="pOptimum" title="P(sample the optimum)" reference={uniform} />
      </div>
      <p className="m-0 text-xs text-ink-subtle">For greedy and simulated annealing, P(optimum) is the share of instances (greedy) or runs (annealing) that returned the optimum; for QAOA it is the probability of sampling it. Approximation ratio for QAOA is the expected value over feasible samples.</p>
      <ChartTable
        caption={`Benchmark at n = ${n} (k = 4)`}
        headers={['Method', 'Instances', 'Approximation ratio', 'P(optimum)', 'Feasibility', 'Seconds', 'CX all-to-all', 'CX heavy-hex', 'Depth']}
        numeric={[1, 2, 3, 4, 5, 6, 7, 8]}
        rows={rows.map((r) => [solverLabel(r), r.instances, num(r.ar), num(r.pOptimum), num(r.feasibility), r.seconds == null ? '—' : r.seconds.toPrecision(3), r.cxAllToAll ?? '—', r.cxHeavyHex ?? '—', r.depth ?? '—'])}
      />
      {v.noise.length > 0 && (
        <div className="flex flex-col gap-2 rounded-lg border border-dashed border-border-strong p-4">
          <h3 className="m-0 text-base font-semibold text-ink">Under noise</h3>
          <p className="m-0 text-sm text-ink-muted">{v.noiseModel}. {v.hardware.ibmQuantum ? `Hardware: ${v.hardware.ibmQuantum}.` : ''}</p>
          <DataTable caption="QAOA under parametric noise" dense rowKey={(r) => `${r.variant}${r.twoQubitError}`} rows={v.noise}
            columns={[
              { key: 'v', header: 'Mixer', render: (r) => `${r.variant}, p = ${r.p}` },
              { key: 'e', header: 'Two-qubit error', numeric: true, render: (r) => pct(r.twoQubitError, 1) },
              { key: 'po', header: 'P(optimum)', numeric: true, render: (r) => num(r.pOptimum) },
              { key: 'f', header: 'Feasibility', numeric: true, render: (r) => num(r.feasibility) },
            ]} />
        </div>
      )}
      <p className="m-0 text-sm text-ink-subtle">Details: <a href="https://github.com/DurgaPritam/Lost-in-Preperation/blob/main/docs/QUANTUM_RESULTS.md" className="text-brand underline">docs/QUANTUM_RESULTS.md</a> and <a href="https://github.com/DurgaPritam/Lost-in-Preperation/blob/main/docs/QUBO.md" className="text-brand underline">docs/QUBO.md</a>.</p>
    </section>
  );
}

export function LabPlanner({ panel, heuristics }: { panel: PanelView | null; heuristics: Heuristic[] }) {
  const [k, setK] = useState(String(panel?.defaultK ?? 8));
  const [open, setOpen] = useState<PanelEntryView | null>(null);
  const likely = heuristics.find((h) => h.id === 'likely_differ');
  if (!panel) return <SiteShell current="planner"><EmptyState title="No panel yet" body="site-data/lab_panel.json is missing; run python -m lip m8 export." /></SiteShell>;
  const size = panel.sizes.find((z) => String(z.k) === k) ?? panel.sizes[panel.sizes.length - 1];
  return (
    <SiteShell current="planner">
      <PageHeader eyebrow="Lab Planner" title="Which re-tests should a lab run first?" lead={`A panel of ${size.k} re-tests chosen by exact optimisation of the model's predictions: the clearest robust profile gaps, spread across compound classes, uses and preparations, with little overlap and at most ${panel.perSpecies ?? '—'} per plant. Hypotheses worth re-testing, never claims.`} />

      <section aria-labelledby="optimiser" className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-6 shadow-1 md:p-8">
        <div className="flex flex-wrap items-center gap-3">
          <h2 id="optimiser" className="m-0 font-display text-2xl text-ink">Panel optimiser</h2>
          <EvidenceStatusBadge wording="validation" status="pending" size="sm" />
        </div>
        <SegmentedControl label="Panel size" value={k} onChange={setK} options={panel.sizes.map((z) => ({ value: String(z.k), label: String(z.k) }))} />
        <dl className="m-0 grid grid-cols-3 gap-3 text-sm">
          <div><dt className="eyebrow text-ink-subtle">Compound classes</dt><dd className="num m-0 font-mono text-lg">{size.coverage.class}</dd></div>
          <div><dt className="eyebrow text-ink-subtle">Indications</dt><dd className="num m-0 font-mono text-lg">{size.coverage.indication}</dd></div>
          <div><dt className="eyebrow text-ink-subtle">Preparation types</dt><dd className="num m-0 font-mono text-lg">{size.coverage.prep}</dd></div>
        </dl>
        {panel.excludedToxic.length > 0 && (
          <p role="note" className="m-0 rounded-md border border-dashed border-tox-fg p-4 text-sm text-tox-fg">
            Not offered for planning because toxicity is reported: {[...new Set(panel.excludedToxic.map((x) => x.species))].join(', ')} ({panel.excludedToxic.length} candidate{panel.excludedToxic.length === 1 ? '' : 's'}: {panel.excludedToxic.map((x) => x.label.split(': ')[1]).join('; ')}).
          </p>
        )}
        {panel.ineligible.length > 0 && <p className="m-0 text-sm text-ink-muted">Not eligible under rule {panel.ruleVersion}: {panel.ineligible.map((x) => `${x.label} (${x.reason})`).join('; ')}.</p>}
        <a href="#how" className="w-max text-sm text-brand underline">How the panel was chosen</a>
      </section>

      <section aria-labelledby="panel" className="flex flex-col gap-4">
        <h2 id="panel" className="m-0 font-display text-2xl text-ink">Suggested panel ({size.k})</h2>
        <ol className="m-0 flex list-none flex-col gap-4 p-0">
          {size.entries.map((e) => <Entry key={e.id} e={e} likely={likely} onTrail={setOpen} />)}
        </ol>
        <ChartTable caption={`Suggested panel (${size.k})`} headers={['#', 'Plant', 'Historical', 'Modern', 'Robust gap (5th–95th)', 'Compounds likely to differ', 'For']} numeric={[0, 5]}
          rows={size.entries.map((e) => [e.position, e.species, e.historical, e.modern, `${num(e.gap.low)}–${num(e.gap.high)}`, e.differs, e.indication])} />
      </section>

      {panel.original && (
        <section aria-labelledby="original" className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-5">
          <h2 id="original" className="m-0 font-display text-xl text-ink">The original result (rule v1)</h2>
          <p className="m-0 max-w-prose text-sm text-ink-muted">The first panel, before the pre-registered v2 rule (positive robust gap, at least one compound likely to differ, at most one entry per plant). It stays visible as the original result.</p>
          {panel.original.notes.map((n) => <p key={n} role="note" className="m-0 rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink">⚑ {n}</p>)}
          <DataTable caption={`Original panel, rule v1 (k = ${panel.original.k})`} dense rowKey={(e) => e.id} rows={panel.original.entries}
            columns={[
              { key: 'p', header: '#', numeric: true, render: (e) => e.position },
              { key: 's', header: 'Plant', render: (e) => <Taxon name={e.species} /> },
              { key: 'h', header: 'Historical vs modern', render: (e) => `${e.historical} vs ${e.modern}` },
              { key: 'g', header: 'Robust gap', numeric: true, render: (e) => num(e.gap.low) },
              { key: 'd', header: 'Likely to differ', numeric: true, render: (e) => (e.coverageOnly ? `${e.differs} ⚑` : e.differs) },
            ]} />
        </section>
      )}

      <section aria-labelledby="stable" className="flex flex-col gap-3">
        <h2 id="stable" className="m-0 font-display text-2xl text-ink">How stable is this panel?</h2>
        <p className="m-0 max-w-prose text-sm text-ink-muted">Each weight multiplied by 0.5 and by 2, the others fixed. The smallest overlap with the panel above is {num(Math.min(...panel.sensitivity.map((s) => s.jaccard)), 2)} (Jaccard; 1 = the same panel).</p>
        <DataTable caption="Weight sensitivity" dense rowKey={(s) => `${s.weight}${s.factor}`} rows={panel.sensitivity}
          columns={[
            { key: 'w', header: 'Weight', render: (s) => WEIGHT[s.weight] ?? s.weight },
            { key: 'f', header: 'Factor', numeric: true, render: (s) => `×${s.factor}` },
            { key: 'j', header: 'Overlap', numeric: true, render: (s) => num(s.jaccard, 2) },
            { key: 'c', header: 'Changes', render: (s) => (s.added.length ? `+${s.added.length} / −${s.removed.length}` : 'none') },
          ]} />
        {panel.perSpeciesTwo.length > 0 && (
          <p className="m-0 max-w-prose text-sm text-ink-muted">Sensitivity check: allowing two entries per plant gives {panel.perSpeciesTwo.map((z) => `k = ${z.k}: ${new Set(z.entries.map((e) => e.species)).size} plants`).join('; ')} (the displayed panel allows one).</p>
        )}
      </section>

      <details id="how" className="rounded-lg border border-border bg-surface p-5">
        <summary className="cursor-pointer font-semibold text-ink">How the panel was chosen</summary>
        <div className="mt-3 flex max-w-prose flex-col gap-2 text-sm text-ink-muted">
          <p className="m-0">The panel maximises robust value (each candidate’s 5th-percentile profile gap) plus coverage of compound classes, indications and preparation types, minus overlap between the compounds each re-test would measure, for exactly {size.k} re-tests. It is solved exactly with integer programming.</p>
          <p className="m-0">Weights, fixed before any comparison: {Object.entries(panel.weights).map(([w, x]) => `${WEIGHT[w] ?? w} ${x}`).join(', ')}. Pool after rule {panel.ruleVersion}: {panel.poolSize} candidates.</p>
          <p className="m-0">Formulation: <a href="https://github.com/DurgaPritam/Lost-in-Preperation/blob/main/docs/QUBO.md" className="text-brand underline">docs/QUBO.md</a>; rule: <a href={`https://github.com/DurgaPritam/Lost-in-Preperation/blob/main/${panel.ruleDoc}`} className="text-brand underline">{panel.ruleDoc}</a>.</p>
        </div>
      </details>

      <Benchmark v={panel} />

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open ? `${open.species}: ${open.historical} vs ${open.modern}` : ''} eyebrow={open ? 'Evidence trail' : undefined}>
        {open && (
          <div className="flex flex-col gap-4">
            <ul className="m-0 flex list-disc flex-col gap-1 pl-5 text-sm text-ink-muted">{open.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
            <ol className="m-0 flex list-none flex-col gap-2 p-0 text-sm">
              {open.trail.map((t, i) => (
                <li key={`${t.kind}${i}`} className="flex gap-2"><span className="font-mono text-xs text-ink-subtle">{t.kind}</span>
                  {t.href ? (t.href.startsWith('/') ? <Link href={t.href} className="break-all text-brand underline">{t.label}</Link> : <a href={t.href} className="break-all text-brand underline">{t.label}</a>) : <span className="break-all">{t.label}</span>}
                </li>
              ))}
            </ol>
          </div>
        )}
      </Drawer>
    </SiteShell>
  );
}
