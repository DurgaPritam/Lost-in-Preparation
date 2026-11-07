import { useEffect, useState, type MouseEvent, type ReactNode } from 'react';
import type { CheckOutcome, Metric, MetricValue, Study, StatedField } from '../types';
import {
  ChartTable, DataTable, EvidenceStatusBadge, ExtractionDetectionExplainer, HeuristicMarker, IconConcern, IconError, IconPending, IconValidated,
  LikelihoodBar, PageHeader, SiteShell, SourceConfidenceMarker, Taxon, UnknownValue, cx, fmt, type Column,
} from '../index';
import { CONTRACT_FILES, coverage, heuristics, sources, studies, validation } from '../contract';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';

/**
 * METHODS & DATA — documentation, not the front door.
 * A sticky table of contents (lg) or a wrapped link list (phone), then one
 * section per question a reviewer asks: how was it made, how well does each
 * step work, what did we pre-register and what happened, which rules of thumb
 * are used, which studies were audited, what are the limits, can I reuse it.
 */
const TOC = [
  ['overview', 'Overview'],
  ['pipeline', 'Pipeline'],
  ['metrics', 'How accurate each step is'],
  ['findings', 'Honest findings'],
  ['preregistered', 'Pre-registered checks'],
  ['heuristics', 'Heuristics'],
  ['studies', 'Audited studies'],
  ['limitations', 'Limitations'],
  ['sources', 'Sources & licences'],
  ['downloads', 'Downloads'],
] as const;

/** A metric as text: point with its interval, or Unknown. Never a bare point. */
function MetricText({ v }: { v: MetricValue }) {
  if (v.point == null && (v.low == null || v.high == null)) return <UnknownValue label="Not measured" />;
  const interval = v.low != null && v.high != null ? `${fmt(v.low)}–${fmt(v.high)}` : null;
  return (
    <span className="num font-mono">
      {v.point != null ? fmt(v.point) : '—'}
      <span className="text-ink-muted"> ({interval ? `95% interval ${interval}` : 'interval unknown'})</span>
      <span className="block font-sans text-xs text-ink-subtle">{v.unit}</span>
    </span>
  );
}

const OUTCOME: Record<CheckOutcome, { label: string; Icon: typeof IconValidated; cls: string }> = {
  pass: { label: 'Pass', Icon: IconValidated, cls: 'border-brand text-brand' },
  fail: { label: 'Fail', Icon: IconError, cls: 'border-tox-fg text-tox-fg' },
  borderline: { label: 'Borderline', Icon: IconConcern, cls: 'border-hist-edge text-hist-fg' },
  not_run: { label: 'Not run yet', Icon: IconPending, cls: 'border-dashed border-unk-line text-unk-fg' },
};
function OutcomeMarker({ outcome }: { outcome: CheckOutcome }) {
  const o = OUTCOME[outcome];
  return <span className={cx('inline-flex h-6 items-center gap-1 whitespace-nowrap rounded-full border px-2 text-xs font-semibold', o.cls)}><o.Icon size={13} className="shrink-0" />{o.label}</span>;
}

function Stated<T>({ f, show }: { f: StatedField<T>; show?: (v: T) => string }) {
  if (f.value == null) return <UnknownValue label="Not stated" variant="cell" />;
  return <span className="inline-flex flex-wrap items-center gap-1.5">{show ? show(f.value) : String(f.value)}<EvidenceStatusBadge status={f.evidence} size="sm" /></span>;
}

function MatchChip({ aspect, state }: { aspect: string; state: Study['match']['vehicle'] }) {
  const t = state === 'matches' ? 'same as recipe' : state === 'differs' ? 'different' : 'not stated';
  return (
    <span className={cx('inline-flex h-6 items-center gap-1 whitespace-nowrap rounded-full border px-2 text-xs',
      state === 'matches' && 'border-hist-edge bg-hist-bg text-hist-fg',
      state === 'differs' && 'border-border-strong bg-sunken text-ink',
      state === 'not_stated' && 'border-dashed border-unk-line bg-unk-bg text-unk-fg')}>
      <span className="font-semibold">{aspect}:</span> {t}
    </span>
  );
}

const STUDY_COLUMNS: Column<Study>[] = [
  { key: 'title', header: 'Study', render: (s) => (
    <span className="flex flex-col gap-0.5">
      <span className="font-medium">{s.title}</span>
      <span className="text-xs text-ink-subtle">{s.year ?? 'Year unknown'} · {s.pmid
        ? <a href={`https://pubmed.ncbi.nlm.nih.gov/${s.pmid}/`} className="text-brand underline">PMID {s.pmid} (mock)</a>
        : 'Not indexed in PubMed'}</span>
    </span>
  ) },
  { key: 'taxon', header: 'Plant', render: (s) => <Taxon name={s.taxon} />, sortValue: (s) => s.taxon },
  { key: 'part', header: 'Part', render: (s) => <Stated f={s.plantPart} /> },
  { key: 'solvent', header: 'Solvent', render: (s) => <Stated f={s.solvent} /> },
  { key: 'heat', header: 'Heat', render: (s) => <Stated f={s.heat} /> },
  { key: 'duration', header: 'Duration', render: (s) => <Stated f={s.duration} /> },
  { key: 'filtered', header: 'Filtered', render: (s) => <Stated f={s.filtered} show={(v) => (v ? 'Yes' : 'No')} /> },
  { key: 'ratio', header: 'Ratio', render: (s) => <Stated f={s.ratio} /> },
  { key: 'match', header: 'vs the recipe', render: (s) => (
    <span className="flex flex-wrap gap-1"><MatchChip aspect="Solvent" state={s.match.vehicle} /><MatchChip aspect="Heat" state={s.match.heat} /><MatchChip aspect="Filtration" state={s.match.filtration} /></span>
  ) },
];

function Section({ id, title, lead, children }: { id: string; title: string; lead?: ReactNode; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="flex scroll-mt-28 flex-col gap-4 border-t border-border pt-10 first:border-t-0 first:pt-0">
      <h2 id={`${id}-h`} tabIndex={-1} className="m-0 font-display text-2xl text-ink">{title}</h2>
      {lead && <p className="m-0 max-w-prose text-ink-muted">{lead}</p>}
      {children}
    </section>
  );
}

export function Docs({ onNavigate }: { onNavigate?: (p: string) => void }) {
  const [active, setActive] = useState<string>('overview');
  const v = validation;

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver((es) => {
      const vis = es.filter((e) => e.isIntersecting)[0];
      if (vis) setActive(vis.target.id);
    }, { rootMargin: '-20% 0px -70% 0px' });
    TOC.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    return () => io.disconnect();
  }, []);

  const jump = (id: string) => (e: MouseEvent) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ block: 'start' });
    document.getElementById(`${id}-h`)?.focus({ preventScroll: true });
  };

  return (
    <SiteShell current="docs" onNavigate={onNavigate}>
      <PageHeader eyebrow="Methods & data · documentation" title="How it was made, how far it was checked, and how to reuse it" lead="Everything behind the Lab, the Atlas and the evidence gap. Mock values throughout; every figure here is a placeholder in the contract’s shape." />

      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
        <nav aria-label="On this page" className="lg:col-span-3">
          <ul className="m-0 flex list-none flex-wrap gap-x-4 gap-y-2 p-0 text-sm lg:sticky lg:top-28 lg:flex-col lg:gap-1 lg:border-l lg:border-border">
            {TOC.map(([id, label]) => (
              <li key={id}>
                <a href={`/docs#${id}`} onClick={jump(id)} aria-current={active === id ? 'location' : undefined}
                  className={cx('block py-1 no-underline lg:-ml-px lg:border-l-2 lg:pl-4', active === id ? 'font-semibold text-ink lg:border-brand' : 'text-ink-muted underline lg:border-transparent lg:no-underline hover:text-ink')}>
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex min-w-0 flex-col gap-10 lg:col-span-9">
          <Section id="overview" title="Overview" lead="Two historical sources, read as recipes: every passage is transcribed, its preparation fields extracted, its plant names resolved to candidate species, and each preparation’s extraction estimated as a range.">
            <dl className="m-0 grid grid-cols-2 gap-4 md:grid-cols-4">
              {[['Recipes', coverage.recipes], ['Studies audited', coverage.studies], ['Names validated', coverage.nameResolutions.validated], ['Names pending', coverage.nameResolutions.pending]].map(([k, n]) => (
                <div key={k} className="rounded-lg border border-border bg-surface p-4"><dt className="eyebrow text-ink-subtle">{k}</dt><dd className="m-0 num font-display text-3xl text-ink">{n}</dd></div>
              ))}
            </dl>
            <div className="flex flex-wrap items-center gap-2">
              <SourceConfidenceMarker confidence={sourceCulpeper} />
              <SourceConfidenceMarker confidence={sourcePliny} />
            </div>
            <ExtractionDetectionExplainer variant="panel" />
          </Section>

          <Section id="pipeline" title="Pipeline" lead="Seven steps, each with its own evidence status. A step is validated only when a person has checked it against a reference.">
            <ol className="m-0 flex list-none flex-col gap-0 p-0">
              {v.pipeline.map((p, i) => (
                <li key={p.id} className="grid grid-cols-[2rem_1fr] gap-3 border-l border-border-strong pb-5 pl-0 last:pb-0">
                  <span className="num -ml-3 flex h-6 w-6 items-center justify-center rounded-full border border-border-strong bg-paper font-mono text-xs text-ink">{i + 1}</span>
                  <span className="flex flex-col gap-1">
                    <span className="flex flex-wrap items-center gap-2"><span className="font-semibold text-ink">{p.name}</span><EvidenceStatusBadge status={p.validation} size="sm" />{p.tool && <span className="font-mono text-xs text-ink-subtle">{p.tool}</span>}</span>
                    <span className="text-sm text-ink-muted">{p.does}</span>
                  </span>
                </li>
              ))}
            </ol>
          </Section>

          <Section id="metrics" title="How accurate each step is" lead="Each value is a point with its 95% interval and sample size. Pliny and Culpeper are reported separately. A step not yet measured says so.">
            <DataTable<Metric>
              caption="Step metrics (mock values)"
              rows={v.metrics}
              rowKey={(m) => m.id}
              columns={[
                { key: 'stage', header: 'Step', render: (m) => m.stage, sortValue: (m) => m.stage },
                { key: 'name', header: 'Measure', render: (m) => <span className="flex flex-col gap-0.5">{m.name}{m.note && <span className="text-xs text-ink-subtle">{m.note}</span>}</span> },
                { key: 'value', header: 'Value', render: (m) => <MetricText v={m.value} /> },
                { key: 'n', header: 'n', numeric: true, render: (m) => (m.n == null ? <UnknownValue variant="cell" /> : m.n), sortValue: (m) => m.n },
                { key: 'ev', header: 'Status', render: (m) => <EvidenceStatusBadge status={m.evidence} size="sm" /> },
              ]}
            />
          </Section>

          <Section id="findings" title="Honest findings" lead="Including the ones that did not go our way.">
            {v.comparisons.map((c) => {
              const pre = v.preregistered.find((p) => p.id === c.preregisteredId);
              return (
                <article key={c.id} className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-1 md:p-6">
                  <div className="flex flex-wrap items-center gap-2">{pre && <OutcomeMarker outcome={pre.outcome} />}{pre && <span className="font-mono text-xs text-ink-subtle">pre-registered check {pre.id.toUpperCase()}</span>}<EvidenceStatusBadge status={c.evidence} size="sm" /></div>
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
                <div className="flex flex-wrap items-center gap-2"><OutcomeMarker outcome={pc.outcome} /><span className="font-mono text-xs text-ink-subtle">positive control · pre-registered check {pc.preregisteredId?.toUpperCase()}</span><EvidenceStatusBadge status={pc.evidence} size="sm" /></div>
                <h3 className="m-0 text-lg font-semibold text-ink">{pc.compound} in <Taxon name={pc.taxon} /></h3>
                <p className="m-0 text-sm text-ink-muted">Expected: {pc.expected}</p>
                <LikelihoodBar range={pc.a.likelihood} compare={pc.b.likelihood} compareLabel={pc.b.label} label={`${pc.compound}, ${pc.a.label}`} />
                <p className="m-0 text-ink">{pc.explanation}</p>
              </article>
            ))}
          </Section>

          <Section id="preregistered" title="Pre-registered checks" lead="Criteria fixed before the results were seen. Outcomes are reported as they came out, including fails.">
            <ol className="m-0 flex list-none flex-col gap-3 p-0">
              {v.preregistered.map((p) => (
                <li key={p.id} className="grid grid-cols-1 gap-2 rounded-lg border border-border bg-surface p-4 md:grid-cols-12 md:gap-4">
                  <span className="flex flex-wrap items-center gap-2 md:col-span-3 md:flex-col md:items-start"><span className="font-mono text-xs text-ink-subtle">{p.id.toUpperCase()} · {p.registeredOn ?? 'date unknown'}</span><OutcomeMarker outcome={p.outcome} /></span>
                  <span className="flex flex-col gap-1 md:col-span-9"><span className="text-ink">{p.criterion}</span><span className="flex flex-wrap items-center gap-2 text-sm text-ink-muted">{p.detail}<EvidenceStatusBadge status={p.evidence} size="sm" /></span></span>
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

          <Section id="studies" title="Audited studies" lead="Every modern study, field by field. “Not stated” means the paper does not say; it is never read as “no”.">
            <DataTable<Study> caption="Audited modern studies (mock records)" rows={studies} rowKey={(s) => s.id} columns={STUDY_COLUMNS} dense />
          </Section>

          <Section id="limitations" title="Limitations">
            <ul className="m-0 flex flex-col gap-2 pl-5 text-ink">{v.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
          </Section>

          <Section id="sources" title="Sources & licences" lead="Each licence carries its own status: validated only once a person has read the terms.">
            <DataTable
              caption="Sources and licences"
              rows={sources.sources}
              rowKey={(s) => s.id}
              columns={[
                { key: 'title', header: 'Source', render: (s) => <span className="flex flex-col gap-0.5"><span className="font-medium">{s.url ? <a href={s.url} className="text-brand underline">{s.title}</a> : s.title}</span>{s.note && <span className="text-xs text-ink-subtle">{s.note}</span>}</span> },
                { key: 'role', header: 'Role', render: (s) => s.role, sortValue: (s) => s.role },
                { key: 'edition', header: 'Edition · year', render: (s) => (s.edition || s.year ? [s.edition, s.year].filter(Boolean).join(' · ') : <UnknownValue variant="cell" label="Not recorded" />) },
                { key: 'licence', header: 'Licence', render: (s) => <span className="inline-flex flex-wrap items-center gap-1.5">{s.licence ?? <UnknownValue variant="cell" label="To confirm" />}<EvidenceStatusBadge status={s.licenceEvidence} size="sm" /></span> },
              ]}
            />
            <p className="m-0 text-sm text-ink-subtle">Illustrations: 19th-century botanical plates, public domain, hosted on Wikimedia Commons. Each image slot names its file and licence; slots still marked “to source” show a drawn placeholder.</p>
          </Section>

          <Section id="downloads" title="Downloads" lead="The same files that drive every screen. Shapes are documented in HANDOFF.md.">
            <ul className="m-0 grid list-none grid-cols-1 gap-3 p-0 md:grid-cols-2">
              {Object.keys(CONTRACT_FILES).map((file) => {
                const d = sources.downloads.find((x) => x.file === file);
                return (
                  <li key={file} className="flex flex-col gap-1 rounded-lg border border-border bg-surface p-4">
                    <a href={`data/${file}`} download className="font-mono text-sm font-medium text-brand underline">{file}</a>
                    <span className="text-sm text-ink-muted">{d?.description ?? 'v2 addition — see HANDOFF.md.'}</span>
                    <span className="text-xs text-ink-subtle">{d?.contract ?? 'v2 contract'} · licence {d?.licence ?? 'to confirm'}</span>
                  </li>
                );
              })}
            </ul>
          </Section>
        </div>
      </div>
    </SiteShell>
  );
}
