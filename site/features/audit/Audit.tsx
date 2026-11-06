'use client';

import { useEffect, useState } from 'react';
import Link from '@/components/base/Link';
import type { AuditBreakdown, MatchState, SourceConfidence, SourceWork, StatedField, Study } from '@/lib/types';
import { HEAT_LABEL, SOURCE_LABEL, ciText, cx, pct } from '@/lib/data/format';
import { recipeSlug } from '@/lib/data/selectors/recipes';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/base/Button';
import { Card } from '@/components/base/Card';
import { ChartTable } from '@/components/base/ChartTable';
import { DataTable, type Column } from '@/components/base/DataTable';
import { Drawer } from '@/components/base/Drawer';
import { FilterGroup, FilterSummary } from '@/components/base/Filters';
import { ErrorState, LoadingState } from '@/components/base/States';
import { Tabs } from '@/components/base/Tabs';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * AUDIT — how modern studies prepared each plant, compared with the source.
 * - Per-source breakdown first (the answer), study table second (the evidence).
 * - Every unstated field renders as "Not stated", never blank, and is
 *   counted in the breakdown's "not stated" segment.
 * - Match chips use shape + word: "= Same as source", "≠ Differs", "? Not stated".
 * - Per-field evidence status lives in the study drawer, so the table stays
 *   scannable; the row shows the weakest status.
 */
export const pubmedUrl = (pmid: string) => `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`;

/** Phase 4: each chip now names its aspect ("Heat ≠ differs"); three unlabelled chips relied on column order. */
export function MatchChip({ state, aspect }: { state: MatchState; aspect?: string }) {
  if (state === 'not_stated') return <UnknownValue label={aspect ? `${aspect}: not stated` : 'Not stated'} />;
  // SITE: audit v2 only. Never counted as "differs".
  if (state === 'no_analogue') return <UnknownValue label={aspect ? `${aspect}: no modern analogue` : 'No modern analogue'} reason="The historical vehicle (e.g. honey, oxymel, milk) has no modern solvent analogue; reported separately, never as unfaithful." />;
  return (
    <span className={cx('inline-flex items-center gap-1 rounded-sm border px-1.5 text-sm', state === 'matches' ? 'border-ink bg-surface text-ink' : 'border-dashed border-border-strong text-ink-muted')}>
      {aspect && <span className="font-medium">{aspect}</span>}
      <span aria-hidden className="font-mono">{state === 'matches' ? '=' : '≠'}</span>
      {state === 'matches' ? 'same as source' : 'differs'}
    </span>
  );
}

function Stated<T>({ f, render = (v: T) => String(v) }: { f: StatedField<T>; render?: (v: T) => string }) {
  return f.value == null ? <UnknownValue variant="cell" label="Not stated" /> : <span>{render(f.value)}</span>;
}

const ORDER = ['validated', 'provisional', 'pending'] as const;
const weakest = (s: Study) => {
  const all = [s.plantPart, s.solvent, s.heat, s.freshOrDried, s.filtered].map((f) => f.evidence);
  return ORDER[Math.max(...all.map((e) => ORDER.indexOf(e)))];
};

function MatchBar({ label, counts, total }: { label: string; counts: Record<MatchState, number>; total: number }) {
  const w = (n: number) => `${(n / Math.max(total, 1)) * 100}%`;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
        <span className="font-medium text-ink">{label}</span>
        <span className="num text-ink-muted">
          <span className="text-ink">= {counts.matches}</span> · ≠ {counts.differs} · <span className="text-unk-fg">? {counts.not_stated}</span>
          {counts.no_analogue > 0 && <span className="text-unk-fg"> · no analogue {counts.no_analogue}</span>}
        </span>
      </div>
      <div
        role="img"
        aria-label={`${label}: ${counts.matches} same as source, ${counts.differs} differ, ${counts.not_stated} not stated${counts.no_analogue ? `, ${counts.no_analogue} no modern analogue` : ''}, of ${total} studies`}
        className="flex h-3 overflow-hidden rounded-sm border border-border-strong"
      >
        <span className="h-full bg-ink" style={{ width: w(counts.matches) }} />
        <span className="h-full bg-sunken" style={{ width: w(counts.differs) }} />
        <span className="h-full bg-hatch-unknown" style={{ width: w(counts.not_stated) }} />
        {counts.no_analogue > 0 && <span className="h-full border-l border-dashed border-unk-line bg-unk-bg" style={{ width: w(counts.no_analogue) }} />}
      </div>
    </div>
  );
}

function SourceBreakdown({ b, confidences }: { b: AuditBreakdown; confidences: Record<SourceWork, SourceConfidence> }) {
  const pliny = b.source === 'pliny_nh';
  return (
    <section className="flex flex-col gap-4 rounded border border-border bg-surface p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <SourceConfidenceMarker confidence={confidences[b.source]} />
        <span className="num text-sm text-ink-muted">{b.plants} plants · {b.studies} (pair, study) units</span>
      </div>
      <MatchBar label="Solvent / vehicle" counts={b.vehicle} total={b.studies} />
      <MatchBar label="Heat" counts={b.heat} total={b.studies} />
      <MatchBar label="Filtration" counts={b.filtration} total={b.studies} />
      {pliny && <p className="m-0 text-xs text-ink-subtle">Pliny is a 19th-century translation with far more disputed names; read these counts with lower confidence.</p>}
      <p className="m-0 text-xs text-ink-subtle">A (plant–use pair, study) unit counts under every source that attests the pair.</p>
      <ChartTable
        caption={`${SOURCE_LABEL[b.source].short}: modern studies compared with the source's preparation (${b.studies} units)`}
        headers={['Aspect', 'Same as source', 'Differs', 'Not stated', 'No modern analogue']}
        numeric={[1, 2, 3, 4]}
        rows={([['Solvent / vehicle', b.vehicle], ['Heat', b.heat], ['Filtration', b.filtration]] as const).map(([k, c]) => [k, c.matches, c.differs, c.not_stated, c.no_analogue])}
      />
    </section>
  );
}

interface MetricLike { status: string; value?: number | null; low?: number | null; high?: number | null; n?: number | null; note?: string | null }
/** SITE: study rows are not in the page; StudiesTable loads /data/audit-studies-<id>.json when its tab is shown. */
type Version = { id: 'v1' | 'v2'; rows: number; breakdowns: AuditBreakdown[]; units: number };
export interface AuditV2Like {
  label: string; protocol: string; overallFidelity: MetricLike; perVariableFidelity: Record<string, MetricLike>;
  solventWineCutoffSensitivity: Record<string, MetricLike>; units: number; unknownUnits: number; noModernAnalogueUnits: number;
  eligibleStudies: number; pairsWithRecords: number; pairs: number;
}
const PAGE = 50;

/** SITE: share k of n with its CI; never a point without its interval. */
function Share({ m, what }: { m: MetricLike | null | undefined; what: string }) {
  if (!m || m.status !== 'computed' || m.value == null || m.n == null) return <UnknownValue label="Not computed" />;
  const k = Math.round(m.value * m.n);
  return (
    <span className="num font-mono text-base">
      {pct(m.value)} <span className="text-ink-muted">({k} of {m.n} {what}; {ciText(m.low, m.high)})</span>
    </span>
  );
}

function StudiesTable({ studies }: { studies: Study[] }) {
  const taxa = [...new Set(studies.map((s) => s.taxon))].sort();
  const [sel, setSel] = useState<string[]>([]);
  const [open, setOpen] = useState<Study | null>(null);
  const [limit, setLimit] = useState(PAGE);
  const shown = studies.filter((s) => sel.length === 0 || sel.includes(s.taxon));

  const columns: Column<Study>[] = [
    {
      key: 'study', header: 'Study',
      sortValue: (s) => s.year,
      render: (s) => (
        <span className="flex flex-col gap-0.5">
          <button type="button" onClick={() => setOpen(s)} className="text-left text-ink underline underline-offset-2">{s.title}</button>
          <span className="flex flex-wrap items-center gap-2 text-sm text-ink-muted">
            {s.year ?? <UnknownValue label="Year unknown" />}
            {s.pmid ? (
              <a href={pubmedUrl(s.pmid)} className="inline-block py-1 font-mono text-mod-fg underline underline-offset-2">PMID {s.pmid}</a>
            ) : (
              <UnknownValue label="Not in PubMed" />
            )}
          </span>
        </span>
      ),
    },
    { key: 'taxon', header: 'Plant', render: (s) => <span className="flex flex-col gap-0.5"><Taxon name={s.taxon} /><span className="text-xs text-ink-subtle">{s.indication}</span></span> },
    { key: 'part', header: 'Part', render: (s) => <Stated f={s.plantPart} /> },
    { key: 'solvent', header: 'Solvent', render: (s) => <Stated f={s.solvent} /> },
    { key: 'heat', header: 'Heat', render: (s) => <Stated f={s.heat} render={(v) => HEAT_LABEL[v]} /> },
    { key: 'fod', header: 'Fresh or dried', render: (s) => <Stated f={s.freshOrDried} /> },
    { key: 'filt', header: 'Filtration', render: (s) => <Stated f={s.filtered} render={(v) => (v === 'not_applicable' ? 'not applicable' : v ? 'filtered' : 'unfiltered')} /> },
    {
      key: 'vs', header: 'vs historical', hint: 'vehicle · heat · filtration',
      render: (s) => (
        <span className="flex flex-col items-start gap-1">
          <MatchChip state={s.match.vehicle} aspect="Vehicle" /><MatchChip state={s.match.heat} aspect="Heat" /><MatchChip state={s.match.filtration} aspect="Filtration" />
        </span>
      ),
    },
    { key: 'ev', header: 'Field evidence', hint: 'weakest field', render: (s) => <EvidenceStatusBadge status={weakest(s)} size="sm" detail="Coded by the rule-based extractor; hand-check pending." /> },
  ];

  return (
    <div className="flex flex-col gap-4">
      <FilterGroup legend="Plant" options={taxa.map((t) => ({ value: t, label: t, count: studies.filter((s) => s.taxon === t).length }))} selected={sel} onChange={(n) => { setSel(n); setLimit(PAGE); }} />
      <FilterSummary shown={shown.length} total={studies.length} onClear={() => setSel([])} />
      <DataTable caption="Modern study preparations compared with the historical preparation (one row per study preparation)" columns={columns} rows={shown.slice(0, limit)} rowKey={(s) => s.id} dense />
      {shown.length > limit && (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => setLimit((l) => l + PAGE)}>Show {Math.min(PAGE, shown.length - limit)} more</Button>
          <span className="num text-sm text-ink-muted">{limit} of {shown.length} shown</span>
        </div>
      )}
      <Drawer open={!!open} onClose={() => setOpen(null)} title={open?.title ?? ''} eyebrow={open ? `Study · ${open.taxon} · ${open.indication}` : undefined}>
        {open && (
          <div className="flex flex-col gap-4">
            {open.pmid ? <a href={pubmedUrl(open.pmid)} className="w-max font-mono text-mod-fg underline">Open PMID {open.pmid} in PubMed</a> : <UnknownValue label="Not indexed in PubMed" />}
            <table className="w-full border-collapse text-sm">
              <caption className="sr-only">Extracted fields with evidence status</caption>
              <tbody>
                {([['Plant part', open.plantPart], ['Solvent', open.solvent], ['Heat', open.heat], ['Fresh or dried', open.freshOrDried], ['Filtration', open.filtered]] as const).map(([k, f]) => (
                  <tr key={k} className="border-b border-border">
                    <th scope="row" className="py-2 pr-3 text-left font-medium">{k}</th>
                    <td className="py-2 pr-3">{f.value == null ? <UnknownValue label="Not stated" /> : typeof f.value === 'boolean' ? (f.value ? 'filtered' : 'unfiltered') : String(f.value).replace(/_/g, ' ')}</td>
                    <td className="py-2"><EvidenceStatusBadge status={f.evidence} size="sm" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="m-0 text-sm text-ink-muted">Coded from: {open.evidenceSource === 'pmc_fulltext' ? 'open-access methods section' : 'title and abstract'}.</p>
            {open.methodsSnippet && <p className="m-0 max-w-prose text-sm text-ink">“{open.methodsSnippet}”</p>}
            <div className="flex flex-col gap-1">
              <p className="m-0 text-sm text-ink-muted">Compared against {open.comparedRecipeIds.length} historical recipe{open.comparedRecipeIds.length === 1 ? '' : 's'}:</p>
              <ul className="m-0 flex list-none flex-col gap-1 p-0 text-sm">
                {open.comparedRecipeIds.slice(0, 8).map((id) => <li key={id}><Link href={`/recipes/${recipeSlug(id)}/`} className="font-mono text-ink underline underline-offset-2">{id}</Link></li>)}
              </ul>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}

function StudiesLoader({ id, rows }: { id: Version['id']; rows: number }) {
  const [studies, setStudies] = useState<Study[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let live = true;
    setFailed(false);
    fetch(`/data/audit-studies-${id}.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: Study[]) => { if (live) setStudies(d); })
      .catch(() => { if (live) setFailed(true); });
    return () => { live = false; };
  }, [id, attempt]);
  if (failed) return <ErrorState title="The study table did not load" body="The breakdowns above are complete; the per-study rows need this file." onRetry={() => setAttempt((n) => n + 1)} />;
  if (!studies) return <LoadingState label={`Loading ${rows} study preparations`} />;
  return <StudiesTable studies={studies} />;
}

function VersionPanel({ v, confidences }: { v: Version; confidences: Record<SourceWork, SourceConfidence> }) {
  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-4">
        <h3 className="m-0 text-lg font-semibold">By source</h3>
        <p className="m-0 max-w-prose text-base text-ink-muted">For plants each source prescribes: how often modern studies used the same solvent, heat and filtration. “Not stated” means the paper does not say.</p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {v.breakdowns.map((b) => <SourceBreakdown key={b.source} b={b} confidences={confidences} />)}
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-ink-muted">
          <span className="inline-flex items-center gap-1.5"><span aria-hidden className="h-2.5 w-4 rounded-sm bg-ink" /> Same as source</span>
          <span className="inline-flex items-center gap-1.5"><span aria-hidden className="h-2.5 w-4 rounded-sm border border-border-strong bg-sunken" /> Differs</span>
          <span className="inline-flex items-center gap-1.5 text-unk-fg"><span aria-hidden className="h-2.5 w-4 rounded-sm border border-unk-line bg-hatch-unknown" /> Not stated</span>
        </div>
      </section>
      <section className="flex flex-col gap-4">
        <h3 className="m-0 text-lg font-semibold">Studies</h3>
        <StudiesLoader id={v.id} rows={v.rows} />
      </section>
    </div>
  );
}

export function Audit({ v1, v2, headline, auditV2, confidences }: {
  v1: Version; v2: Version; headline: MetricLike; auditV2: AuditV2Like | null; confidences: Record<SourceWork, SourceConfidence>;
}) {
  const [tab, setTab] = useState('v1');
  const hn = headline.note ?? '';
  const unknownV1 = hn.match(/\((\d+) unknown\)/)?.[1];
  return (
    <AppShell current="audit">
      {/* SITE (new section): v1 and v2 side by side. */}
      <section aria-labelledby="versions" className="flex flex-col gap-4">
        <h2 id="versions" className="m-0 font-serif text-2xl font-medium">Two pre-registered analyses</h2>
        <p className="m-0 max-w-prose text-base text-ink-muted">Both protocols were committed before their results existed. The analysis is frozen: v1 and v2 are reported as they are.</p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card as="section" eyebrow="Audit v1 · as pre-registered" title="Share of studies faithful to the historical preparation"
                meta={<EvidenceStatusBadge status="pending" size="sm" detail="Rule-based coding; the 40-study hand-check is pending." />}>
            <Share m={headline} what="studies with a known status" />
            {unknownV1 && <p className="m-0 text-sm text-ink-muted">{unknownV1} more units have an unknown status and are not in the share.</p>}
            <p role="note" className="m-0 rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink">
              <span className="font-medium">Design flaw.</span> v1’s solvent rule makes every non-water recipe unmatchable: only a historical water
              preparation could ever match a modern solvent. Its headline mostly reflects the protocol, not the literature.
            </p>
          </Card>
          <Card as="section" eyebrow={auditV2 ? `Audit v2 · ${auditV2.label}` : 'Audit v2'} title="Share of studies faithful to the historical preparation"
                meta={<EvidenceStatusBadge status="pending" size="sm" detail="Rule-based coding; the 40-study hand-check is pending." />}>
            {auditV2 ? (
              <>
                <Share m={auditV2.overallFidelity} what="studies with a known status" />
                <p role="note" className="m-0 rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink">
                  <span className="font-medium">Small n.</span> Only {auditV2.overallFidelity.n} (plant–use pair, study) units have a known status:{' '}
                  {auditV2.unknownUnits} are unknown and {auditV2.noModernAnalogueUnits} have no modern analogue. {auditV2.eligibleStudies} studies were
                  eligible across {auditV2.pairsWithRecords} of {auditV2.pairs} pairs. These counts are too small to estimate a field-wide rate.
                </p>
                <ul className="m-0 flex list-none flex-col gap-2 p-0">
                  {Object.entries(auditV2.perVariableFidelity).map(([k, m]) => (
                    <li key={k} className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
                      <span className="font-medium">{k === 'freshOrDried' ? 'Fresh or dried' : k[0].toUpperCase() + k.slice(1)} matches</span>
                      <Share m={m} what="known" />
                    </li>
                  ))}
                </ul>
              </>
            ) : <UnknownValue label="Audit v2 not in site-data" />}
          </Card>
        </div>
        <p className="m-0 max-w-prose text-sm text-ink-muted">
          Fidelity is supporting detail. The headline is the reporting gap: most studies do not say how they prepared the plant (<Link href="/" className="text-ink underline underline-offset-2">Home</Link>).
        </p>
      </section>

      <section aria-labelledby="detail" className="flex flex-col gap-4">
        <h2 id="detail" className="m-0 font-serif text-2xl font-medium">By source and study</h2>
        <Tabs label="Audit version" value={tab} onChange={setTab} items={[
          // SITE: only the selected panel is rendered (both panels in the DOM made a 16,000-node page).
          { id: 'v1', label: 'v1 · as pre-registered', count: v1.units, panel: tab === 'v1' ? <VersionPanel v={v1} confidences={confidences} /> : null },
          { id: 'v2', label: 'v2 · re-analysis', count: v2.units, panel: tab === 'v2' ? <VersionPanel v={v2} confidences={confidences} /> : null },
        ]} />
      </section>
    </AppShell>
  );
}
