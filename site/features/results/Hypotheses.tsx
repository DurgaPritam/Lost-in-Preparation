import type { Heuristic, Hypothesis, TrailStep } from '@/lib/types';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { ChartTable } from '@/components/base/ChartTable';
import { MarkHist, MarkMod } from '@/components/base/PrepTag';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import Link from '@/components/base/Link';

/**
 * RANKED HYPOTHESES (M6): a results page reached from Methods & data and the case study (project lead, 2026-11-07).
 * SITE: built from existing v2 components. The three ranked hypotheses stay visible with their caveats and evidence
 * trails; ones with toxicity reported carry the ToxicityNotice and are for analysis only (never planned). This is the
 * M6 ranking, not the Lab Planner's panel.
 */
const STAGE: Record<TrailStep['stage'], string> = { source: 'Source', name: 'Name', preparation: 'Preparation', model: 'Model', audit: 'Audit', toxicity: 'Toxicity' };

function Trail({ h, heuristics }: { h: Hypothesis; heuristics: Heuristic[] }) {
  return (
    <ol className="m-0 flex list-none flex-col p-0">
      {h.trail.map((s, i) => (
        <li key={s.id} className="flex flex-col gap-1.5 border-l border-border-strong pb-5 pl-4 last:pb-0">
          <span className="font-mono text-xs text-ink-subtle">{i + 1} · {STAGE[s.stage]}</span>
          <span className="flex flex-wrap items-center gap-2"><span className="font-semibold">{s.title}</span><EvidenceStatusBadge status={s.evidence} size="sm" /></span>
          <p className="m-0 break-words text-sm text-ink-muted">{s.detail}</p>
          {s.heuristics?.map((id) => { const hh = heuristics.find((x) => x.id === id); return hh ? <span key={id}><HeuristicMarker heuristic={hh} /></span> : null; })}
          {s.refs && s.refs.length > 0 && (
            <ul className="m-0 flex list-none flex-wrap gap-x-3 gap-y-1 p-0 text-xs">
              {s.refs.slice(0, 10).map((r) => <li key={r.label}>{r.href ? (r.href.startsWith('/') ? <Link href={r.href} className="text-brand underline">{r.label}</Link> : <a href={r.href} className="text-brand underline">{r.label}</a>) : r.label}</li>)}
            </ul>
          )}
        </li>
      ))}
    </ol>
  );
}

export function Hypotheses({ hypotheses, heuristics }: { hypotheses: Hypothesis[]; heuristics: Heuristic[] }) {
  return (
    <SiteShell current="docs">
      <Link href="/docs/#findings" className="w-max text-sm text-brand underline">← Methods &amp; data</Link>
      <PageHeader eyebrow="Results · M6 ranking" title="Ranked hypotheses worth re-testing"
        lead="Plant–use pairs that no retrieved modern study tested in the historical preparation, ranked only on predicted profile gaps that hold across the uncertainty range. Each is a hypothesis worth re-testing, not a finding about any remedy." />
      {hypotheses.length === 0 ? <UnknownValue label="No ranked hypotheses in the data" /> : (
        <ol className="m-0 flex list-none flex-col gap-6 p-0">
          {hypotheses.map((h) => {
            const toxic = h.toxicity.category === 'toxic_reported';
            return (
              <li key={h.id} id={h.id} className="flex scroll-mt-24 flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-1 md:p-6">
                <div className="flex flex-wrap items-baseline gap-3">
                  <span className="font-display text-4xl text-ink">{h.rank}</span>
                  <span className="text-sm text-ink-subtle">of {h.rankedOf}</span>
                  <h2 className="m-0 break-words text-xl font-semibold text-ink"><Taxon name={h.taxon} /> · for {h.indication}</h2>
                </div>
                <span className="text-sm text-ink-muted">As written: “{h.indicationAsWritten}” · {h.attestationCount} recipe{h.attestationCount === 1 ? '' : 's'}</span>
                <span className="flex flex-col gap-1 text-sm">
                  <span className="inline-flex items-center gap-2"><MarkHist />Historical: {h.faithful.label}</span>
                  <span className="inline-flex items-center gap-2"><MarkMod />Modern: {h.modern?.label ?? <UnknownValue label="Not modelled" />}</span>
                </span>
                <LikelihoodBar range={h.gap} family="neutral" label={`${h.taxon}, ${h.faithful.label}${h.modern ? ` vs ${h.modern.label}` : ''}`} measure="Predicted profile gap (1 − cosine similarity), 5th–95th percentile" />
                <div className="flex flex-wrap items-center gap-2"><EvidenceStatusBadge wording="validation" status={h.evidence} size="sm" /><ToxicityBadge record={h.toxicity} /></div>
                {toxic && <ToxicityNotice record={h.toxicity} />}
                {toxic && <p className="m-0 text-sm text-ink-muted">For analysis only: not offered for planning, and no Lab link is given.</p>}
                <div className="flex flex-col gap-1">
                  <h3 className="m-0 text-base font-semibold text-ink">Caveats</h3>
                  <ul className="m-0 flex list-disc flex-col gap-1 pl-5 text-sm text-ink-muted">{h.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
                </div>
                <details className="rounded-lg border border-border p-4">
                  <summary className="cursor-pointer font-semibold text-ink">Evidence trail</summary>
                  <div className="mt-3"><Trail h={h} heuristics={heuristics} /></div>
                </details>
              </li>
            );
          })}
        </ol>
      )}
      <ChartTable caption="Ranked hypotheses" headers={['Rank', 'Plant', 'Use', 'Historical', 'Modern', 'Gap 5th–95th', 'Toxicity']} numeric={[0]}
        rows={hypotheses.map((h) => [h.rank, h.taxon, h.indication, h.faithful.label, h.modern?.label ?? '—', h.gap.low != null && h.gap.high != null ? `${h.gap.low.toFixed(3)}–${h.gap.high.toFixed(3)}` : '—', h.toxicity.category.replace(/_/g, ' ')])} />
      <p className="m-0 max-w-prose text-sm text-ink-subtle">The Lab Planner’s re-test panel is a separate result: an exact optimisation over a wider candidate pool (<Link href="/planner/" className="text-brand underline">Lab Planner</Link>).</p>
    </SiteShell>
  );
}
