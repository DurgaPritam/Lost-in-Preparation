'use client';

import { useState } from 'react';
import type { Heuristic, Hypothesis, LabPlanFile, LabPlanItem } from '@/lib/types';
import { isKnownRange, rangeText } from '@/lib/data/format';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { Button, LinkButton } from '@/components/base/Button';
import { ChartTable } from '@/components/base/ChartTable';
import { Switch } from '@/components/base/Controls';
import { Drawer } from '@/components/base/Drawer';
import { MarkHist, MarkMod } from '@/components/base/PrepTag';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { ToxicityBadge } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import Link from '@/components/base/Link';

/**
 * LAB PLANNER — placeholder for the quantum feature (design v2 screens/LabPlanner.tsx).
 * SITE: the experiments are the ranked hypotheses (hypotheses.json); each is a species-level predicted profile gap, so the
 * bar is that gap (1 − cosine similarity), not a compound likelihood. Readout and effort are not decided anywhere in the
 * data and the ranking records no rank interval, so they read "Not decided" / "Not estimated". The quantum score is null:
 * "Coming in this release", never 0.
 */
const STAGE: Record<Hypothesis['trail'][number]['stage'], string> = { source: 'Source', name: 'Name', preparation: 'Preparation', model: 'Model', audit: 'Audit', toxicity: 'Toxicity' };

function ComingSoon() {
  return <span className="inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-full border border-dotted border-unk-fg bg-unk-bg px-2.5 text-sm font-semibold text-unk-fg"><span aria-hidden>◌</span>Coming in this release</span>;
}

export function LabPlanner({ plan, withheld, planned, heuristics }: { plan: LabPlanFile; withheld: Hypothesis[]; planned: Hypothesis[]; heuristics: Heuristic[] }) {
  const [open, setOpen] = useState<Hypothesis | null>(null);
  const soon = plan.feature.status === 'coming_soon';
  return (
    <SiteShell current="planner">
      <PageHeader eyebrow="Lab Planner · preview" title="Which experiments should a lab run first?" lead="A shortlist of re-tests, ordered by how clearly the historical preparation’s predicted profile separates from the modern method’s, using only the conservative end of the range." />

      <section aria-labelledby="feature" className="grid grid-cols-1 items-center gap-6 overflow-hidden rounded-xl border border-border bg-surface p-6 shadow-1 md:grid-cols-12 md:p-8">
        <div className="flex flex-col gap-3 md:col-span-8">
          <ComingSoon />
          <h2 id="feature" className="m-0 font-display text-2xl text-ink">{plan.feature.name}</h2>
          <p className="m-0 max-w-prose text-ink-muted">{plan.feature.description}</p>
          <p className="m-0 text-sm text-ink-subtle">Release: {plan.feature.release ?? 'date not set'}</p>
        </div>
        <div className="flex flex-col gap-3 rounded-lg border border-dashed border-border-strong p-4 md:col-span-4">
          <Switch label="Use quantum-informed priority" description={soon ? 'Available when the feature ships' : 'Re-orders the list'} checked={false} onChange={() => {}} />
          <span className="text-xs text-ink-subtle">Disabled in this preview — the order below never uses it.</span>
        </div>
      </section>

      <section aria-labelledby="queue" className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h2 id="queue" className="m-0 font-display text-2xl text-ink">Suggested order</h2>
          <span className="text-sm text-ink-muted">{plan.items.length} experiment{plan.items.length === 1 ? '' : 's'} · {withheld.length} lead{withheld.length === 1 ? '' : 's'} withheld (toxicity reported)</span>
        </div>
        <ol className="m-0 flex list-none flex-col gap-4 p-0">
          {plan.items.map((it: LabPlanItem) => {
            const h = planned.find((x) => x.id === it.hypothesisId);
            return (
              <li key={it.id} className="grid grid-cols-1 gap-4 rounded-lg border border-border bg-surface p-5 shadow-1 md:grid-cols-12 md:items-center">
                <div className="flex items-baseline gap-3 md:col-span-2 md:flex-col md:gap-0">
                  <span className="font-display text-4xl text-ink">{it.rank}</span>
                  <span className="text-xs text-ink-subtle">{it.rankRange ? (it.rankRange[0] === it.rankRange[1] ? 'only this rank' : `could be ${it.rankRange[0]}–${it.rankRange[1]}`) : <UnknownValue label="Rank range not estimated" />}</span>
                </div>
                <div className="flex min-w-0 flex-col gap-2 md:col-span-6">
                  <h3 className="m-0 break-words text-lg font-semibold text-ink">{it.title}</h3>
                  {h && <span className="text-sm text-ink-muted"><Taxon name={h.taxon} /> · for {h.indication} (as written: “{h.indicationAsWritten}”)</span>}
                  <span className="flex flex-col gap-1 text-sm">
                    <span className="inline-flex items-center gap-2"><MarkHist />{it.compares[0]}</span>
                    <span className="inline-flex items-center gap-2"><MarkMod />{it.compares[1]}</span>
                  </span>
                  {h && <LikelihoodBar range={h.gap} family="neutral" label={it.title} measure="Predicted profile gap (1 − cosine similarity)" size="sm" />}
                </div>
                <dl className="m-0 grid grid-cols-2 gap-3 text-sm md:col-span-4 md:grid-cols-1">
                  <div><dt className="eyebrow text-ink-subtle">Readout</dt><dd className="m-0">{it.readout ?? <UnknownValue label="Not decided" />}</dd></div>
                  <div><dt className="eyebrow text-ink-subtle">Effort</dt><dd className="m-0">{it.effort ?? <UnknownValue label="Not estimated" />}</dd></div>
                  <div><dt className="eyebrow text-ink-subtle">Quantum priority</dt><dd className="m-0">{it.quantumScore && isKnownRange(it.quantumScore) ? rangeText(it.quantumScore) : <ComingSoon />}</dd></div>
                  <div><dt className="eyebrow text-ink-subtle">Status</dt><dd className="m-0 flex flex-wrap items-center gap-2">{h ? <><EvidenceStatusBadge status={h.evidence} size="sm" /><ToxicityBadge record={h.toxicity} withSources={false} /></> : <UnknownValue />}</dd></div>
                </dl>
                {h && <div className="md:col-span-12"><Button size="sm" onClick={() => setOpen(h)}>Evidence trail</Button></div>}
              </li>
            );
          })}
        </ol>
        {withheld.length > 0 && (
          <p role="note" className="m-0 rounded-md border border-dashed border-tox-fg p-4 text-sm text-tox-fg">
            {withheld.length} lead{withheld.length === 1 ? ' is' : 's are'} not offered for planning because toxicity is reported ({withheld.map((h) => `${h.taxon}, ${h.faithful.label}`).join('; ')}). They remain visible in Methods &amp; data for analysis only.
          </p>
        )}
        <ChartTable
          caption="Suggested experiments"
          headers={['Experiment', 'Rank', 'Could be', 'Readout', 'Effort', 'Quantum priority']}
          rows={plan.items.map((it) => [it.title, it.rank, it.rankRange ? `${it.rankRange[0]}–${it.rankRange[1]}` : <UnknownValue label="Not estimated" />, it.readout ?? <UnknownValue label="Not decided" />, it.effort ?? <UnknownValue label="Not estimated" />, it.quantumScore ? 'scored' : 'Coming in this release'])}
        />
        <LinkButton href="/lab/" className="w-max">Explore a preparation in the Lab →</LinkButton>
      </section>

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open ? `${open.taxon}: ${open.faithful.label}` : ''} eyebrow={open ? 'Evidence trail' : undefined}>
        {open && (
          <ol className="m-0 flex list-none flex-col p-0">
            {open.trail.map((s, i) => (
              <li key={s.id} className="flex flex-col gap-1.5 border-l border-border-strong pb-5 pl-4 last:pb-0">
                <span className="font-mono text-xs text-ink-subtle">{i + 1} · {STAGE[s.stage]}</span>
                <span className="flex flex-wrap items-center gap-2"><span className="font-semibold">{s.title}</span><EvidenceStatusBadge status={s.evidence} size="sm" /></span>
                <p className="m-0 break-words text-sm text-ink-muted">{s.detail}</p>
                {s.heuristics?.map((id) => { const hh = heuristics.find((x) => x.id === id); return hh ? <span key={id}><HeuristicMarker heuristic={hh} /></span> : null; })}
                {s.refs && s.refs.length > 0 && (
                  <ul className="m-0 flex list-none flex-wrap gap-x-3 gap-y-1 p-0 text-xs">
                    {s.refs.slice(0, 8).map((r) => <li key={r.label}>{r.href ? (r.href.startsWith('/') ? <Link href={r.href} className="text-brand underline">{r.label}</Link> : <a href={r.href} className="text-brand underline">{r.label}</a>) : r.label}</li>)}
                  </ul>
                )}
              </li>
            ))}
          </ol>
        )}
      </Drawer>
    </SiteShell>
  );
}
