import { useState } from 'react';
import type { Hypothesis } from '../types';
import {
  AppShell, Button, Card, ChartTable, Taxon, Drawer, EvidenceStatusBadge, ExtractionDetectionExplainer, HeuristicMarker, LikelihoodBar, PrepTag,
  SourceConfidenceMarker, ToxicityBadge, ToxicityNotice, UnknownValue, compareRanges, cx, isKnownRange, rangeText,
} from '../index';
import type { ToxicityCategory } from '../types';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';
import { heuristics, hypotheses as HYPOTHESES } from '../contract';

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
const heur = (id: string) => heuristics.find((h) => h.id === id);
const TOX_WORD: Record<ToxicityCategory, string> = {
  toxic_reported: 'Toxicity reported', concern: 'Toxicity concern', no_toxicity_reported: 'No toxicity reported',
  data_lacking: 'Toxicity data lacking', unknown: 'Toxicity unknown',
};

function HypothesisCard({ h, onTrail }: { h: Hypothesis; onTrail: () => void }) {
  const verdict = compareRanges(h.historicalLikelihood, h.modernLikelihood);
  // Phase 4: an unknown range used to be labelled "ranges overlap"; each case now has its own label.
  const flag =
    verdict === 'overlap' ? 'Weak lead · ranges overlap'
    : verdict === 'b' ? 'Modern preparation higher · not a lead'
    : verdict === 'unknown' ? 'Can’t compare · a range is unknown'
    : null;
  return (
    <Card
      as="article"
      eyebrow={h.rankRange[0] === h.rankRange[1]
        ? `Rank ${h.rank} · the uncertainty allows only this rank`
        : `Rank ${h.rank} · consistent with ranks ${h.rankRange[0]}–${h.rankRange[1]}`}
      title={<><span>{h.compound}</span> <span className="font-normal text-ink-muted">in</span> <Taxon name={h.taxon} /></>}
      meta={<>
        <EvidenceStatusBadge status={h.evidence} size="sm" />
        <ToxicityBadge record={h.toxicity} withSources={false} />
        {flag && <span className="rounded-sm border border-dashed border-ink-muted px-2 py-0.5 text-sm text-ink-muted">{flag}</span>}
      </>}
      footer={<Button size="sm" onClick={onTrail}>Evidence trail</Button>}
    >
      <p className="m-0 max-w-prose text-base">
        Re-test whether the source’s preparation ({h.faithful.label.toLowerCase()}) extracts more {h.compound.toLowerCase()} than the preparation modern studies used ({h.modern.label.toLowerCase()}).
      </p>
      <ToxicityNotice record={h.toxicity} />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-2">
          <span className="small-caps text-xs text-ink-subtle">Faithful preparation</span>
          <PrepTag prep={h.faithful.preparation} />
          <LikelihoodBar range={h.historicalLikelihood} family="historical" label={h.faithful.label.split(',')[0]} width="full" />
        </div>
        <div className="flex flex-col gap-2">
          <span className="small-caps text-xs text-ink-subtle">Modern studies used</span>
          <PrepTag prep={h.modern.preparation} />
          <LikelihoodBar range={h.modernLikelihood} family="modern" label={h.modern.label.split(',')[0]} width="full" />
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <span className="small-caps text-xs text-ink-subtle">Attested in</span>
        <ul className="m-0 flex list-none flex-wrap gap-3 p-0">
          {h.attestation.map((a) => (
            <li key={a.source} className="flex items-center gap-2">
              <SourceConfidenceMarker confidence={a.source === 'pliny_nh' ? sourcePliny : sourceCulpeper} compact />
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

export function Hypotheses({ onNavigate, items = HYPOTHESES }: { onNavigate?: (p: string) => void; items?: Hypothesis[] }) {
  const [open, setOpen] = useState<Hypothesis | null>(null);
  const sorted = [...items].sort((a, b) => a.rank - b.rank);
  return (
    <AppShell current="hypotheses" onNavigate={onNavigate}>
      <div className="flex flex-col gap-3">
        <p className="m-0 max-w-prose text-base text-ink-muted">
          Ranked by the <strong className="font-medium text-ink">conservative gap</strong>: the historical range’s low end minus the modern range’s high end.
          A lead whose ranges overlap ranks last and is marked weak. Rank ranges show which positions the uncertainty allows.
        </p>
        <ExtractionDetectionExplainer />
      </div>
      <h2 id="leads" className="m-0 font-serif text-2xl font-medium">Ranked leads</h2>
      <ol className="m-0 flex list-none flex-col gap-4 p-0" aria-labelledby="leads">
        {sorted.map((h) => <li key={h.id}><HypothesisCard h={h} onTrail={() => setOpen(h)} /></li>)}
      </ol>
      <ChartTable
        label="View all leads as a table"
        caption="Ranked leads: predicted extraction ranges (0–1) for the faithful and modern preparations"
        headers={['Lead', 'Rank (range)', 'Faithful', 'Modern', 'Comparison', 'Toxicity']}
        rows={sorted.map((h) => {
          const v = compareRanges(h.historicalLikelihood, h.modernLikelihood);
          return [
            `${h.compound} in ${h.taxon}`,
            `${h.rank} (${h.rankRange[0]}–${h.rankRange[1]})`,
            isKnownRange(h.historicalLikelihood) ? rangeText(h.historicalLikelihood) : <UnknownValue />,
            isKnownRange(h.modernLikelihood) ? rangeText(h.modernLikelihood) : <UnknownValue />,
            v === 'a' ? 'Faithful higher, no overlap' : v === 'b' ? 'Modern higher, no overlap' : v === 'overlap' ? 'Weak lead: ranges overlap' : <UnknownValue label="Can’t compare" />,
            TOX_WORD[h.toxicity.category],
          ];
        })}
      />

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open ? `${open.compound} in ${open.taxon}` : ''} eyebrow={open ? `Evidence trail · rank ${open.rank}` : undefined}>
        {open && (
          <ol className="m-0 flex list-none flex-col gap-0 p-0">
            {open.trail.map((s, i) => (
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
                    <a
                      key={r.label}
                      href={r.href}
                      onClick={onNavigate ? (e) => { e.preventDefault(); setOpen(null); onNavigate(r.href!); } : undefined}
                      className="w-max text-sm text-ink underline underline-offset-2"
                    >
                      {r.label} →
                    </a>
                  ))}
                </div>
              </li>
            ))}
          </ol>
        )}
      </Drawer>
    </AppShell>
  );
}
