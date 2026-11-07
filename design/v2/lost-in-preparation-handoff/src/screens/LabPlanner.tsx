import { useState, type MouseEvent } from 'react';
import type { Hypothesis, LabPlanItem } from '../types';
import {
  Button, ChartTable, Drawer, EvidenceStatusBadge, HeuristicMarker, LikelihoodBar, LinkButton, MarkHist, MarkMod, PageHeader,
  SiteShell, Switch, Taxon, ToxicityBadge, UnknownValue, isKnownRange, rangeText,
} from '../index';
import { heuristics, hypotheses, labPlan } from '../contract';

/**
 * LAB PLANNER — "Which experiments should a lab run first?"
 * Placeholder for the upcoming quantum feature, designed as a real screen:
 * - Experiments ordered by the conservative gap (rank + the ranks the
 *   uncertainty allows), each linked to its full evidence trail.
 * - The quantum-informed priority column exists but is visibly empty
 *   ("Coming in this release") — never a zero, never a fake score.
 * - Leads with toxicity REPORTED are withheld from planning and counted.
 */
const STAGE: Record<Hypothesis['trail'][number]['stage'], string> = { source: 'Source', name: 'Name', preparation: 'Preparation', model: 'Model', audit: 'Audit', toxicity: 'Toxicity' };

function ComingSoon() {
  return <span className="inline-flex h-7 items-center gap-1.5 whitespace-nowrap rounded-full border border-dotted border-unk-fg bg-unk-bg px-2.5 text-sm font-semibold text-unk-fg"><span aria-hidden>◌</span>Coming in this release</span>;
}

export function LabPlanner({ onNavigate, plan = labPlan }: { onNavigate?: (p: string) => void; plan?: typeof labPlan }) {
  const [open, setOpen] = useState<Hypothesis | null>(null);
  const withheld = hypotheses.filter((h) => h.toxicity.category === 'toxic_reported');
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); onNavigate(path); } };
  const soon = plan.feature.status === 'coming_soon';

  return (
    <SiteShell current="planner" onNavigate={onNavigate}>
      <PageHeader eyebrow="Lab Planner · preview" title="Which experiments should a lab run first?" lead="A shortlist of re-tests, ordered by how clearly the historical preparation separates from the modern method. Placeholder data." />

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
          <span className="text-sm text-ink-muted">{plan.items.length} experiments · {withheld.length} lead{withheld.length === 1 ? '' : 's'} withheld (toxicity reported)</span>
        </div>
        <ol className="m-0 flex list-none flex-col gap-4 p-0">
          {plan.items.map((it: LabPlanItem) => {
            const h = hypotheses.find((x) => x.id === it.hypothesisId);
            return (
              <li key={it.id} className="grid grid-cols-1 gap-4 rounded-lg border border-border bg-surface p-5 shadow-1 md:grid-cols-12 md:items-center">
                <div className="flex items-baseline gap-3 md:col-span-2 md:flex-col md:gap-0">
                  <span className="font-display text-4xl text-ink">{it.rank}</span>
                  <span className="text-xs text-ink-subtle">{it.rankRange[0] === it.rankRange[1] ? 'only this rank' : `could be ${it.rankRange[0]}–${it.rankRange[1]}`}</span>
                </div>
                <div className="flex min-w-0 flex-col gap-2 md:col-span-6">
                  <h3 className="m-0 text-lg font-semibold text-ink">{it.title}</h3>
                  {h && <span className="text-sm text-ink-muted"><Taxon name={h.taxon} /></span>}
                  <span className="flex flex-col gap-1 text-sm">
                    <span className="inline-flex items-center gap-2"><MarkHist />{it.compares[0]}</span>
                    <span className="inline-flex items-center gap-2"><MarkMod />{it.compares[1]}</span>
                  </span>
                  {h && <LikelihoodBar range={h.historicalLikelihood} compare={h.modernLikelihood} compareLabel={h.modern.label} label={it.title} size="sm" />}
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
            {withheld.length} lead{withheld.length === 1 ? ' is' : 's are'} not offered for planning because toxicity is reported ({withheld.map((h) => h.compound).join(', ')}). They remain visible in Methods &amp; data for analysis only.
          </p>
        )}
        <ChartTable
          caption="Suggested experiments (placeholder data)"
          headers={['Experiment', 'Rank', 'Could be', 'Readout', 'Effort', 'Quantum priority']}
          rows={plan.items.map((it) => [it.title, it.rank, `${it.rankRange[0]}–${it.rankRange[1]}`, it.readout ?? <UnknownValue label="Not decided" />, it.effort ?? <UnknownValue label="Not estimated" />, it.quantumScore ? 'scored' : 'Coming in this release'])}
        />
        <LinkButton href="/lab" onClick={go('/lab')} className="w-max">Explore a preparation in the Lab →</LinkButton>
      </section>

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open ? `${open.compound} in ${open.taxon}` : ''} eyebrow={open ? 'Evidence trail' : undefined}>
        {open && (
          <ol className="m-0 flex list-none flex-col p-0">
            {open.trail.map((s, i) => (
              <li key={s.id} className="flex flex-col gap-1.5 border-l border-border-strong pb-5 pl-4 last:pb-0">
                <span className="font-mono text-xs text-ink-subtle">{i + 1} · {STAGE[s.stage]}</span>
                <span className="flex flex-wrap items-center gap-2"><span className="font-semibold">{s.title}</span><EvidenceStatusBadge status={s.evidence} size="sm" /></span>
                <p className="m-0 text-sm text-ink-muted">{s.detail}</p>
                {s.heuristics?.map((id) => { const hh = heuristics.find((x) => x.id === id); return hh ? <span key={id}><HeuristicMarker heuristic={hh} /></span> : null; })}
              </li>
            ))}
          </ol>
        )}
      </Drawer>
    </SiteShell>
  );
}
