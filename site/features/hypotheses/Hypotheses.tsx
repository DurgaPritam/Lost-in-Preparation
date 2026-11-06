'use client';

import { useState } from 'react';
import Link from '@/components/base/Link';
import type { Hypothesis, SourceConfidence, SourceWork, ToxicityCategory } from '@/lib/types';
import { cx, isKnownRange, pct, rangeText } from '@/lib/data/format';
import { heuristic } from '@/lib/data/heuristics';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/base/Button';
import { Card } from '@/components/base/Card';
import { ChartTable } from '@/components/base/ChartTable';
import { Drawer } from '@/components/base/Drawer';
import { PrepTag } from '@/components/base/PrepTag';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * HYPOTHESES — ranked leads worth re-testing.
 * - Ranked by the conservative gap (historical low − modern high), never by
 *   point estimates. Each rank shows the ranks consistent with uncertainty.
 * - Caveats are always visible on the card, not hidden behind a click.
 * - Attestation is counted per source; Pliny keeps its lower-confidence marker.
 * - Overlapping ranges are labelled "Weak lead".
 * - Toxic-reported leads show ToxicityNotice; wording is analytical only.
 * - The evidence trail drawer lists each pipeline step with its own status.
 */
const STAGE_LABEL: Record<Hypothesis['trail'][number]['stage'], string> = {
  source: 'Source', name: 'Name', preparation: 'Preparation', model: 'Model', audit: 'Audit', toxicity: 'Toxicity',
};
const heur = heuristic;
/** SITE: a lead is weak when the gap's 5th percentile is below the ranking rule's threshold (both from the data). */
export const isWeak = (h: Hypothesis) => h.gap.low != null && h.gapThreshold != null && h.gap.low < h.gapThreshold;
const GAP_MEASURE = 'Predicted profile gap (1 − cosine similarity)';
const TOX_WORD: Record<ToxicityCategory, string> = {
  toxic_reported: 'Toxicity reported', concern: 'Toxicity concern', no_toxicity_reported: 'No toxicity reported',
  data_lacking: 'Toxicity data lacking', unknown: 'Toxicity unknown',
};

export function HypothesisCard({ h, onTrail, confidences, standalone = false }: { h: Hypothesis; onTrail?: () => void; confidences: Record<SourceWork, SourceConfidence>; standalone?: boolean }) {
  const flag = !isKnownRange(h.gap) ? 'Can’t rank · the gap’s range is unknown'
    : isWeak(h) ? `Weak lead · the gap’s 5th percentile is below ${h.gapThreshold}` : null;
  return (
    <Card
      as="article"
      eyebrow={`Rank ${h.rank} of ${h.rankedOf} · ranked by the gap’s 5th percentile${h.rankByMedianGap != null && h.rankByMedianGap !== h.rank ? ` (rank ${h.rankByMedianGap} by median gap)` : ''}`}
      title={<><span>{h.indication}</span> <span className="font-normal text-ink-muted">·</span> <Taxon name={h.taxon} /></>}
      meta={<>
        <EvidenceStatusBadge status={h.evidence} size="sm" detail="Built on the AI-made recipe extraction and the rule-based audit; neither is human-checked yet." />
        <ToxicityBadge record={h.toxicity} withSources={false} />
        {flag && <span className="rounded-sm border border-dashed border-ink-muted px-2 py-0.5 text-sm text-ink-muted">{flag}</span>}
      </>}
      footer={onTrail ? <><Button size="sm" onClick={onTrail}>Evidence trail</Button>{!standalone && <Link href={`/hypotheses/${h.id}/`} className="text-sm text-ink underline underline-offset-2">Link to this hypothesis</Link>}</> : undefined}
    >
      <p className="m-0 max-w-prose text-base">
        Re-test whether the source’s preparation ({h.faithful.label}) gives a different compound profile from the preparation modern studies used{h.modern ? ` (${h.modern.label})` : ''}.
      </p>
      <p className="m-0 max-w-prose font-serif text-md text-ink-muted">Use as written: “{h.indicationAsWritten}”</p>
      <ToxicityNotice record={h.toxicity} />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-2">
          <span className="small-caps text-xs text-ink-subtle">Faithful preparation</span>
          <PrepTag prep={h.faithful.preparation} />
          <span className="text-sm text-ink-muted">{h.faithful.label}</span>
        </div>
        <div className="flex flex-col gap-2">
          <span className="small-caps text-xs text-ink-subtle">Modern studies used</span>
          {h.modern ? <><PrepTag prep={h.modern.preparation} /><span className="text-sm text-ink-muted">{h.modern.label}</span></> : <UnknownValue label="Not recorded" />}
        </div>
      </div>
      <LikelihoodBar range={h.gap} family="neutral" label="Faithful vs modern" measure={GAP_MEASURE} width="full" showScale />
      {h.pGapAboveThreshold != null && h.gapThreshold != null && (
        <p className="m-0 text-sm text-ink-muted">Share of model draws with a gap above {h.gapThreshold}: {pct(h.pGapAboveThreshold)}. {h.compoundsUsed} compounds used, {h.compoundsExcludedWide} left out as too uncertain.</p>
      )}
      <div className="flex flex-col gap-2">
        <span className="small-caps text-xs text-ink-subtle">Attested in</span>
        <ul className="m-0 flex list-none flex-wrap gap-3 p-0">
          {h.attestation.map((a) => (
            <li key={a.source} className="flex items-center gap-2">
              <SourceConfidenceMarker confidence={confidences[a.source]} compact />
              <span className={cx('num text-sm', a.recipes === 0 ? 'text-ink-subtle' : 'text-ink')}>
                {a.recipes} recipe{a.recipes === 1 ? '' : 's'}
              </span>
            </li>
          ))}
        </ul>
      </div>
      <div className="flex flex-col gap-2">
        <span className="small-caps text-xs text-ink-subtle">Caveats</span>
        <ul className="m-0 flex flex-col gap-1 pl-5 text-sm text-ink-muted">
          {h.caveats.map((c) => <li key={c}>{c}</li>)}
        </ul>
      </div>
    </Card>
  );
}

export function Trail({ h, onLink }: { h: Hypothesis; onLink?: () => void }) {
  return (
    <ol className="m-0 flex list-none flex-col gap-0 p-0">
      {h.trail.map((s, i) => (
        <li key={s.id} className="flex gap-3 border-l border-border-strong pb-5 pl-4 last:pb-0">
          <div className="flex flex-col gap-1.5">
            <span className="font-mono text-xs text-ink-subtle">{i + 1} · {STAGE_LABEL[s.stage]}</span>
            <span className="flex flex-wrap items-center gap-2">
              <span className="text-base font-semibold">{s.title}</span>
              <EvidenceStatusBadge status={s.evidence} size="sm" />
            </span>
            <p className="m-0 text-sm text-ink-muted">{s.detail}</p>
            {s.heuristics?.map((id) => { const hh = heur(id); return hh ? <span key={id}><HeuristicMarker heuristic={hh} /></span> : null; })}
            {s.refs?.filter((r) => r.href).map((r) => (
              r.href!.startsWith('http')
                ? <a key={r.label} href={r.href} className="w-max text-sm text-ink underline underline-offset-2">{r.label} →</a>
                : <Link key={r.label} href={r.href!} onClick={onLink} className="w-max text-sm text-ink underline underline-offset-2">{r.label} →</Link>
            ))}
          </div>
        </li>
      ))}
    </ol>
  );
}

export function Hypotheses({ items, confidences, rule }: { items: Hypothesis[]; confidences: Record<SourceWork, SourceConfidence>; rule: string | null }) {
  const [open, setOpen] = useState<Hypothesis | null>(null);
  const sorted = [...items].sort((a, b) => a.rank - b.rank);
  return (
    <AppShell current="hypotheses">
      <div className="flex flex-col gap-3">
        <p className="m-0 max-w-prose text-base text-ink-muted">
          Plant–use pairs that no retrieved modern study prepared the way the recipe did, ranked by the{' '}
          <strong className="font-medium text-ink">predicted profile gap</strong> between the faithful and the modern preparation: only gaps that hold
          across the uncertainty range count. {rule ? `Rule: ${rule}.` : ''}
        </p>
        <p className="m-0 max-w-prose text-sm text-ink-muted">
          How a single extraction error changed the top lead: <Link href="/case-studies/liquorice/" className="text-ink underline underline-offset-2">the liquorice case study</Link>.
        </p>
        <ExtractionDetectionExplainer />
      </div>
      <h2 id="leads" className="m-0 font-serif text-2xl font-medium">Ranked leads</h2>
      <ol className="m-0 flex list-none flex-col gap-4 p-0" aria-labelledby="leads">
        {sorted.map((h) => <li key={h.id}><HypothesisCard h={h} onTrail={() => setOpen(h)} confidences={confidences} /></li>)}
      </ol>
      <ChartTable
        label="View all leads as a table"
        caption="Ranked leads: predicted profile gap (5th–95th percentile, 0–1) between the faithful and the modern preparation"
        headers={['Lead', 'Rank', 'Faithful', 'Modern', 'Gap (5th–95th)', 'Median gap', 'Toxicity']}
        numeric={[4, 5]}
        rows={sorted.map((h) => [
          `${h.indication} · ${h.taxon}`,
          `${h.rank} of ${h.rankedOf}`,
          h.faithful.label,
          h.modern ? h.modern.label : <UnknownValue key="m" />,
          isKnownRange(h.gap) ? rangeText(h.gap) : <UnknownValue key="g" />,
          h.gap.point != null ? h.gap.point.toFixed(2) : <UnknownValue key="p" />,
          TOX_WORD[h.toxicity.category],
        ])}
      />

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open ? `${open.indication} · ${open.taxon}` : ''} eyebrow={open ? `Evidence trail · rank ${open.rank}` : undefined}>
        {open && <Trail h={open} onLink={() => setOpen(null)} />}
      </Drawer>
    </AppShell>
  );
}

/** SITE (shareable URL per hypothesis): the card plus its evidence trail inline. */
export function HypothesisPage({ h, confidences }: { h: Hypothesis; confidences: Record<SourceWork, SourceConfidence> }) {
  return (
    <AppShell current="hypotheses">
      <Link href="/hypotheses/" className="w-max text-sm text-ink-muted underline underline-offset-2">← All hypotheses</Link>
      {/* SITE: the card's title is an h3 (design Card); this keeps the heading order h1 → h2 → h3. */}
      <h2 className="sr-only">Hypothesis</h2>
      <HypothesisCard h={h} confidences={confidences} standalone />
      <ExtractionDetectionExplainer />
      <section aria-labelledby="trail" className="flex flex-col gap-3">
        <h2 id="trail" className="m-0 font-serif text-2xl font-medium">Evidence trail</h2>
        <Trail h={h} />
      </section>
    </AppShell>
  );
}
