'use client';

import { useEffect, useState, type MouseEvent, type ReactNode } from 'react';
import type {
  AuditBreakdown, CheckOutcome, Coverage, Heuristic, MatchState, Metric, MetricValue, SourceConfidence, SourceWork, SourcesFile, StatedField, Study, Validation,
} from '@/lib/types';
import { cx, fmt, HEAT_LABEL, pct, ciText } from '@/lib/data/format';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { Button } from '@/components/base/Button';
import { ChartTable } from '@/components/base/ChartTable';
import { DataTable, type Column } from '@/components/base/DataTable';
import { ErrorState, LoadingState } from '@/components/base/States';
import { Tabs } from '@/components/base/Tabs';
import { Taxon } from '@/components/base/Taxon';
import { IconConcern, IconError, IconPending, IconValidated } from '@/components/icons';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * METHODS & DATA — documentation (design v2 screens/Docs.tsx).
 * SITE: the audited studies are the real audit rows, loaded per version when the section is reached
 * (/data/audit-studies-<v>.json), with v1 (as pre-registered, with its design flaw) and v2 (the re-analysis, small n)
 * in tabs. Duration and ratio are not coded by the extractor, so those columns are fresh or dried and plant part.
 * An outcome recorded but not graded pass/fail reads "Outcome not graded".
 */
const TOC = [
  ['overview', 'Overview'], ['pipeline', 'Pipeline'], ['metrics', 'How accurate each step is'], ['findings', 'Honest findings'],
  ['preregistered', 'Pre-registered checks'], ['heuristics', 'Heuristics'], ['studies', 'Audited studies'], ['limitations', 'Limitations'],
  ['sources', 'Sources & licences'], ['downloads', 'Downloads'],
] as const;
const PAGE = 50;

function MetricText({ v }: { v: MetricValue }) {
  if (v.point == null && (v.low == null || v.high == null)) return <UnknownValue label="Not measured" />;
  const interval = v.low != null && v.high != null ? `${fmt(v.low)}–${fmt(v.high)}` : null;
  return (
    <span className="num font-mono">
      {v.point != null ? fmt(v.point) : <UnknownValue label="Point not recorded" />}
      <span className="text-ink-muted"> ({interval ? `95% interval ${interval}` : 'interval unknown'})</span>
      <span className="block font-sans text-xs text-ink-subtle">{v.unit}</span>
    </span>
  );
}

const OUTCOME: Record<Exclude<CheckOutcome, 'reported'>, { label: string; Icon: typeof IconValidated; cls: string }> = {
  pass: { label: 'Pass', Icon: IconValidated, cls: 'border-brand text-brand' },
  fail: { label: 'Fail', Icon: IconError, cls: 'border-tox-fg text-tox-fg' },
  borderline: { label: 'Borderline', Icon: IconConcern, cls: 'border-hist-edge text-hist-fg' },
  not_run: { label: 'Not run yet', Icon: IconPending, cls: 'border-dashed border-unk-line text-unk-fg' },
};
function OutcomeMarker({ outcome }: { outcome: CheckOutcome }) {
  if (outcome === 'reported') return <UnknownValue label="Outcome not graded" reason="The result is recorded in metrics.json but not graded pass or fail there; see the detail." />;
  const o = OUTCOME[outcome];
  return <span className={cx('inline-flex h-6 items-center gap-1 whitespace-nowrap rounded-full border px-2 text-xs font-semibold', o.cls)}><o.Icon size={13} className="shrink-0" />{o.label}</span>;
}

function Stated<T>({ f, show }: { f: StatedField<T>; show?: (v: T) => string }) {
  if (f.value == null) return <UnknownValue label="Not stated" variant="cell" />;
  return <span className="inline-flex flex-wrap items-center gap-1.5">{show ? show(f.value) : String(f.value).replace(/_/g, ' ')}<EvidenceStatusBadge status={f.evidence} size="sm" detail="Coded by the rule-based extractor; hand-check pending." /></span>;
}
function MatchChip({ aspect, state }: { aspect: string; state: MatchState }) {
  const t = state === 'matches' ? 'same as recipe' : state === 'differs' ? 'different' : state === 'no_analogue' ? 'no modern analogue' : 'not stated';
  return (
    <span className={cx('inline-flex h-6 items-center gap-1 whitespace-nowrap rounded-full border px-2 text-xs',
      state === 'matches' && 'border-hist-edge bg-hist-bg text-hist-fg',
      state === 'differs' && 'border-border-strong bg-sunken text-ink',
      (state === 'not_stated' || state === 'no_analogue') && 'border-dashed border-unk-line bg-unk-bg text-unk-fg')}>
      <span className="font-semibold">{aspect}:</span> {t}
    </span>
  );
}
const STUDY_COLUMNS: Column<Study>[] = [
  { key: 'title', header: 'Study', render: (s) => (
    <span className="flex flex-col gap-0.5">
      <span className="font-medium">{s.title}</span>
      <span className="text-xs text-ink-subtle">{s.year ?? 'Year unknown'} · {s.pmid
        ? <a href={`https://pubmed.ncbi.nlm.nih.gov/${s.pmid}/`} className="inline-block py-1 text-brand underline">PMID {s.pmid}</a>
        : 'Not indexed in PubMed'} · coded from {s.evidenceSource === 'pmc_fulltext' ? 'open-access methods' : 'title and abstract'}</span>
    </span>
  ) },
  { key: 'taxon', header: 'Plant', render: (s) => <span className="flex flex-col gap-0.5"><Taxon name={s.taxon} /><span className="text-xs text-ink-subtle">{s.indication}</span></span>, sortValue: (s) => s.taxon },
  { key: 'part', header: 'Part', render: (s) => <Stated f={s.plantPart} /> },
  { key: 'solvent', header: 'Solvent', render: (s) => <Stated f={s.solvent} /> },
  { key: 'heat', header: 'Heat', render: (s) => <Stated f={s.heat} show={(v) => HEAT_LABEL[v]} /> },
  { key: 'material', header: 'Fresh or dried', render: (s) => <Stated f={s.freshOrDried} /> },
  { key: 'filtered', header: 'Filtered', render: (s) => <Stated f={s.filtered} show={(v) => (v === 'not_applicable' ? 'Not applicable' : v ? 'Yes' : 'No')} /> },
  { key: 'match', header: 'vs the recipe', render: (s) => (
    <span className="flex flex-wrap gap-1"><MatchChip aspect="Solvent" state={s.match.vehicle} /><MatchChip aspect="Heat" state={s.match.heat} /><MatchChip aspect="Filtration" state={s.match.filtration} /></span>
  ) },
];

function Section({ id, title, lead, children }: { id: string; title: string; lead?: ReactNode; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="flex scroll-mt-28 flex-col gap-4 border-t border-border pt-10 first:border-t-0 first:pt-0">
      <h2 id={`${id}-h`} tabIndex={-1} className="m-0 font-display text-2xl text-ink">{title}</h2>
      {lead && <div className="m-0 max-w-prose text-ink-muted">{lead}</div>}
      {children}
    </section>
  );
}

function StudiesTable({ version, rows }: { version: 'v1' | 'v2'; rows: number }) {
  const [data, setData] = useState<Study[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [limit, setLimit] = useState(PAGE);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let live = true;
    setFailed(false);
    fetch(`/data/audit-studies-${version}.json`).then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: Study[]) => { if (live) setData(d); }).catch(() => { if (live) setFailed(true); });
    return () => { live = false; };
  }, [version, attempt]);
  if (failed) return <ErrorState title="The study table did not load" body="The counts above are complete; the per-study rows need this file." onRetry={() => setAttempt((n) => n + 1)} />;
  if (!data) return <LoadingState label={`Loading ${rows} study preparations`} rows={3} />;
  return (
    <div className="flex flex-col gap-3">
      <DataTable<Study> caption={`Audited modern studies, audit ${version} (one row per study preparation)`} rows={data.slice(0, limit)} rowKey={(s) => s.id} columns={STUDY_COLUMNS} dense />
      {data.length > limit && (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => setLimit((l) => l + PAGE)}>Show {Math.min(PAGE, data.length - limit)} more</Button>
          <span className="num text-sm text-ink-muted">{limit} of {data.length} shown</span>
        </div>
      )}
    </div>
  );
}

interface MetricLike { status: string; value?: number | null; low?: number | null; high?: number | null; n?: number | null; note?: string | null }
export interface DocsProps {
  validation: Validation; sources: SourcesFile; heuristics: Heuristic[]; confidences: Record<SourceWork, SourceConfidence>;
  coverage: Coverage; modelledSpecies: number;
  audit: {
    v1: { breakdowns: AuditBreakdown[]; units: number; rows: number }; v2: { breakdowns: AuditBreakdown[]; units: number; rows: number };
    headline: MetricLike; auditV2: { label: string; overallFidelity: MetricLike; unknownUnits: number; noModernAnalogueUnits: number; eligibleStudies: number; pairsWithRecords: number; pairs: number } | null;
  };
}

function Share({ m, what }: { m: MetricLike | null | undefined; what: string }) {
  if (!m || m.status !== 'computed' || m.value == null || m.n == null) return <UnknownValue label="Not computed" />;
  return <span className="num font-mono">{pct(m.value)} <span className="text-ink-muted">({Math.round(m.value * m.n)} of {m.n} {what}; 95% interval {ciText(m.low, m.high)})</span></span>;
}

export function Docs({ validation: v, sources, heuristics, confidences, coverage, modelledSpecies, audit }: DocsProps) {
  const [active, setActive] = useState<string>('overview');
  const [tab, setTab] = useState('v2');
  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver((es) => {
      const vis = es.filter((e) => e.isIntersecting)[0];
      if (vis) setActive(vis.target.id);
    }, { rootMargin: '-20% 0px -70% 0px' });
    TOC.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    if (window.location.hash) requestAnimationFrame(() => document.getElementById(window.location.hash.slice(1))?.scrollIntoView({ block: 'start' }));
    return () => io.disconnect();
  }, []);
  const jump = (id: string) => (e: MouseEvent) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ block: 'start' });
    document.getElementById(`${id}-h`)?.focus({ preventScroll: true });
    window.history.replaceState(null, '', `#${id}`);
  };
  const a2 = audit.auditV2;
  const unknownV1 = (audit.headline.note ?? '').match(/\((\d+) unknown\)/)?.[1];

  return (
    <SiteShell current="docs">
      <PageHeader eyebrow="Methods & data · documentation" title="How it was made, how far it was checked, and how to reuse it" lead="Everything behind the Lab, the Atlas and the evidence gap. Every value here comes from the published data files, with its interval and evidence status." />

      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
        <nav aria-label="On this page" className="lg:col-span-3">
          <ul className="m-0 flex list-none flex-wrap gap-x-4 gap-y-2 p-0 text-sm lg:sticky lg:top-28 lg:flex-col lg:gap-1 lg:border-l lg:border-border">
            {TOC.map(([id, label]) => (
              <li key={id}>
                <a href={`/docs/#${id}`} onClick={jump(id)} aria-current={active === id ? 'location' : undefined}
                  className={cx('block py-1 no-underline lg:-ml-px lg:border-l-2 lg:pl-4', active === id ? 'font-semibold text-ink lg:border-brand' : 'text-ink-muted underline lg:border-transparent lg:no-underline hover:text-ink')}>
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex min-w-0 flex-col gap-10 lg:col-span-9">
          <Section id="overview" title="Overview" lead="Three historical sources, read as recipes: every passage is transcribed, its preparation fields extracted, its plant names resolved to candidate species, and each preparation’s extraction estimated as a range.">
            <dl className="m-0 grid grid-cols-2 gap-4 md:grid-cols-4">
              {([['Recipes', coverage.recipes], ['Studies audited', coverage.studies], ['Modelled species', modelledSpecies], ['Names pending check', coverage.nameResolutions.pending]] as const).map(([k, n]) => (
                <div key={k} className="rounded-lg border border-border bg-surface p-4"><dt className="eyebrow text-ink-subtle">{k}</dt><dd className="m-0 num font-display text-3xl text-ink">{n}</dd></div>
              ))}
            </dl>
            <div className="flex flex-wrap items-center gap-2">
              <SourceConfidenceMarker confidence={confidences.culpeper_1652} />
              <SourceConfidenceMarker confidence={confidences.culpeper_1850} />
              <SourceConfidenceMarker confidence={confidences.pliny_nh} />
            </div>
            <ExtractionDetectionExplainer variant="panel" />
          </Section>

          <Section id="pipeline" title="Pipeline" lead="Each step shows one of three statuses: human-validated, AI-assisted check (provisional), or human validation pending. AI-assisted checks help find problems; they are never a validation.">
            <ol className="m-0 flex list-none flex-col gap-0 p-0">
              {v.pipeline.map((p, i) => (
                <li key={p.id} className="grid grid-cols-[2rem_1fr] gap-3 border-l border-border-strong pb-5 pl-0 last:pb-0">
                  <span className="num -ml-3 flex h-6 w-6 items-center justify-center rounded-full border border-border-strong bg-paper font-mono text-xs text-ink">{i + 1}</span>
                  <span className="flex min-w-0 flex-col gap-1">
                    <span className="flex flex-wrap items-center gap-2"><span className="font-semibold text-ink">{p.name}</span><EvidenceStatusBadge wording="validation" status={p.validation} size="sm" />{p.tool && <span className="font-mono text-xs text-ink-subtle">{p.tool}</span>}</span>
                    <span className="text-sm text-ink-muted">{p.does}</span>
                  </span>
                </li>
              ))}
            </ol>
          </Section>

          <Section id="metrics" title="How accurate each step is" lead="Each value is a point with its 95% interval and sample size. A step not yet measured says so.">
            <DataTable<Metric>
              caption="Step metrics"
              rows={v.metrics}
              rowKey={(m) => m.id}
              columns={[
                { key: 'stage', header: 'Step', render: (m) => m.stage, sortValue: (m) => m.stage },
                { key: 'name', header: 'Measure', render: (m) => <span className="flex flex-col gap-0.5">{m.name}{m.note && <span className="text-xs text-ink-subtle">{m.note}</span>}</span> },
                { key: 'value', header: 'Value', render: (m) => <MetricText v={m.value} /> },
                { key: 'n', header: 'n', numeric: true, render: (m) => (m.n == null ? <UnknownValue variant="cell" /> : m.n), sortValue: (m) => m.n },
                { key: 'ev', header: 'Status', render: (m) => <EvidenceStatusBadge wording="validation" status={m.evidence} size="sm" /> },
              ]}
            />
          </Section>

          <Section id="findings" title="Honest findings" lead="Including the ones that did not go our way.">
            {v.comparisons.map((c) => {
              const pre = v.preregistered.find((p) => p.id === c.preregisteredId);
              return (
                <article key={c.id} className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-1 md:p-6">
                  <div className="flex flex-wrap items-center gap-2">{pre && <OutcomeMarker outcome={pre.outcome} />}{pre && <span className="font-mono text-xs text-ink-subtle">pre-registered check {pre.id.toUpperCase()}</span>}<EvidenceStatusBadge wording="validation" status={c.evidence} size="sm" /></div>
                  <h3 className="m-0 text-lg font-semibold text-ink">{c.question}</h3>
                  <ul className="m-0 flex list-none flex-col gap-3 p-0">
                    {c.methods.map((m) => (
                      <li key={m.name} className="grid grid-cols-1 gap-1 md:grid-cols-12 md:items-center md:gap-4">
                        <span className="text-sm font-medium md:col-span-4">{m.name}</span>
                        <span className="md:col-span-5"><LikelihoodBar range={{ low: m.value.low != null ? m.value.low / 1.5 : null, high: m.value.high != null ? m.value.high / 1.5 : null }} family="neutral" showValue={false} label={`${m.name}, error`} measure="Error (scaled to 0–1.5 log units)" size="sm" /></span>
                        <span className="text-sm md:col-span-3"><MetricText v={m.value} /></span>
                      </li>
                    ))}
                  </ul>
                  <span className="text-xs text-ink-subtle">{c.direction === 'lower_better' ? 'Lower is better.' : 'Higher is better.'} Bar scale 0–1.5 log units.</span>
                  <p className="m-0 font-semibold text-ink">{c.finding}</p>
                  <p className="m-0 text-ink-muted">{c.decision}</p>
                  <ChartTable caption={c.question} headers={['Method', 'Error', 'Low', 'High']} numeric={[1, 2, 3]}
                    rows={c.methods.map((m) => [m.name, m.value.point != null ? fmt(m.value.point) : <UnknownValue />, m.value.low != null ? fmt(m.value.low) : <UnknownValue />, m.value.high != null ? fmt(m.value.high) : <UnknownValue />])} />
                </article>
              );
            })}
            {v.positiveControls.map((pc) => (
              <article key={pc.id} className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-1 md:p-6">
                <div className="flex flex-wrap items-center gap-2"><OutcomeMarker outcome={pc.outcome} /><span className="font-mono text-xs text-ink-subtle">positive control{pc.preregisteredId ? ` · pre-registered check ${pc.preregisteredId.toUpperCase()}` : ''}</span><EvidenceStatusBadge wording="validation" status={pc.evidence} size="sm" /></div>
                <h3 className="m-0 text-lg font-semibold text-ink">{pc.compound} in <Taxon name={pc.taxon} /></h3>
                <p className="m-0 text-sm text-ink-muted">Expected: {pc.expected}</p>
                {pc.a && pc.b && <LikelihoodBar range={pc.a.likelihood} compare={pc.b.likelihood} compareLabel={pc.b.label} label={`${pc.compound}, ${pc.a.label}`} />}
                <p className="m-0 break-words text-ink">{pc.explanation}</p>
              </article>
            ))}
          </Section>

          <Section id="preregistered" title="Pre-registered checks" lead="Criteria fixed before the results were seen. Outcomes are reported as they came out, including fails.">
            <ol className="m-0 flex list-none flex-col gap-3 p-0">
              {v.preregistered.map((p) => (
                <li key={p.id} className="grid grid-cols-1 gap-2 rounded-lg border border-border bg-surface p-4 md:grid-cols-12 md:gap-4">
                  <span className="flex flex-wrap items-center gap-2 md:col-span-3 md:flex-col md:items-start"><span className="font-mono text-xs text-ink-subtle">{p.id.toUpperCase()} · {p.registeredOn ?? 'date unknown'}</span><OutcomeMarker outcome={p.outcome} /></span>
                  <span className="flex min-w-0 flex-col gap-1 md:col-span-9"><span className="text-ink">{p.criterion}</span><span className="flex flex-wrap items-center gap-2 break-words text-sm text-ink-muted">{p.detail}<EvidenceStatusBadge wording="validation" status={p.evidence} size="sm" /></span></span>
                </li>
              ))}
            </ol>
          </Section>

          <Section id="heuristics" title="Heuristics" lead="Rules of thumb the model applies where no measurement exists. Anywhere one is used, it is marked.">
            <ul className="m-0 flex list-none flex-col gap-3 p-0">
              {heuristics.map((h) => (
                <li key={h.id} className="flex flex-col gap-1 rounded-lg border border-dashed border-border-strong p-4">
                  <span><HeuristicMarker heuristic={h} /></span>
                  <span className="text-sm text-ink-muted">{h.rule}</span>
                </li>
              ))}
            </ul>
          </Section>

          <Section id="studies" title="Audited studies" lead="Every modern study, field by field. “Not stated” means the paper does not say; it is never read as “no”. Both pre-registered analyses are reported as they are; the analysis is frozen.">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-4">
                <span className="eyebrow text-ink-subtle">Audit v1 · as pre-registered</span>
                <span className="text-sm">Share faithful to the historical preparation: <Share m={audit.headline} what="units with a known status" /></span>
                {unknownV1 && <span className="text-xs text-ink-subtle">{unknownV1} more units have an unknown status and are not in the share.</span>}
                <p role="note" className="m-0 rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink"><span className="font-semibold">Design flaw.</span> v1’s solvent rule makes every non-water recipe unmatchable: only a historical water preparation could ever match a modern solvent. Its share mostly reflects the protocol, not the literature.</p>
              </div>
              <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-4">
                <span className="eyebrow text-ink-subtle">Audit v2 · {a2?.label ?? 're-analysis'}</span>
                <span className="text-sm">Share faithful: <Share m={a2?.overallFidelity} what="units with a known status" /></span>
                {a2 && <p role="note" className="m-0 rounded-sm border border-dashed border-border-strong px-3 py-2 text-sm text-ink"><span className="font-semibold">Small n.</span> Only {a2.overallFidelity.n} (plant–use pair, study) units have a known status: {a2.unknownUnits} are unknown and {a2.noModernAnalogueUnits} have no modern analogue. {a2.eligibleStudies} studies were eligible across {a2.pairsWithRecords} of {a2.pairs} pairs. Too few to estimate a field-wide rate.</p>}
              </div>
            </div>
            <Tabs label="Audit version" value={tab} onChange={setTab} items={[
              { id: 'v2', label: 'v2 · re-analysis', count: audit.v2.rows, panel: tab === 'v2' ? <StudiesTable version="v2" rows={audit.v2.rows} /> : null },
              { id: 'v1', label: 'v1 · as pre-registered', count: audit.v1.rows, panel: tab === 'v1' ? <StudiesTable version="v1" rows={audit.v1.rows} /> : null },
            ]} />
          </Section>

          <Section id="limitations" title="Limitations">
            <ul className="m-0 flex flex-col gap-2 pl-5 text-ink">{v.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          </Section>

          <Section id="sources" title="Sources & licences" lead="Each licence carries its own status: human-validated only once a person has read the terms.">
            <DataTable
              caption="Sources and licences"
              rows={sources.sources}
              rowKey={(s) => s.id}
              columns={[
                { key: 'title', header: 'Source', render: (s) => <span className="flex flex-col gap-0.5"><span className="font-medium">{s.url ? <a href={s.url} className="text-brand underline">{s.title}</a> : s.title}</span>{s.note && <span className="text-xs text-ink-subtle">{s.note}</span>}</span> },
                { key: 'role', header: 'Role', render: (s) => s.role, sortValue: (s) => s.role },
                { key: 'edition', header: 'Edition · year', render: (s) => (s.edition || s.year ? [s.edition, s.year].filter(Boolean).join(' · ') : <UnknownValue variant="cell" label="Not recorded" />) },
                { key: 'licence', header: 'Licence', render: (s) => <span className="inline-flex flex-wrap items-center gap-1.5">{s.licence ?? <UnknownValue variant="cell" label="To confirm" />}<EvidenceStatusBadge wording="validation" status={s.licenceEvidence} size="sm" /></span> },
              ]}
            />
            <p className="m-0 text-sm text-ink-subtle">Code: MIT. The project’s derived data: CC BY 4.0, with the exceptions in LICENSE-DATA (Culpeper 1652 CC0; the Gutenberg passages public domain in the USA; short third-party quotes keep their own licences). Illustrations: 19th-century public-domain plates from Wikimedia Commons, listed with author, date and licence on the <a href="/credits/" className="underline">credits page</a>.</p>
          </Section>

          <Section id="downloads" title="Downloads" lead="The same files that drive every screen, checked against the data contract at build time.">
            <ul className="m-0 grid list-none grid-cols-1 gap-3 p-0 md:grid-cols-2">
              {sources.downloads.map((d) => (
                <li key={d.file} className="flex min-w-0 flex-col gap-1 rounded-lg border border-border bg-surface p-4">
                  <a href={`/data/${d.file}`} download className="break-all font-mono text-sm font-medium text-brand underline">{d.file}</a>
                  <span className="text-sm text-ink-muted">{d.description}</span>
                  <span className="text-xs text-ink-subtle">{d.contract} · licence {d.licence ?? 'to confirm'}</span>
                </li>
              ))}
            </ul>
          </Section>
        </div>
      </div>
    </SiteShell>
  );
}
