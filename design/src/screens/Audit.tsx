import { useState } from 'react';
import type { AuditBreakdown, MatchState, StatedField, Study } from '../types';
import {
  AppShell, ChartTable, Taxon, DataTable, Drawer, EvidenceStatusBadge, FilterGroup, FilterSummary, SourceConfidenceMarker, UnknownValue, cx, type Column,
} from '../index';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';
import { auditSummary as SUMMARY, studies as STUDIES } from '../contract';

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
  const all = [s.plantPart, s.solvent, s.heat, s.duration, s.filtered, s.ratio].map((f) => f.evidence);
  return ORDER[Math.max(...all.map((e) => ORDER.indexOf(e)))];
};

function MatchBar({ label, counts, total }: { label: string; counts: Record<MatchState, number>; total: number }) {
  const pct = (n: number) => `${(n / Math.max(total, 1)) * 100}%`;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
        <span className="font-medium text-ink">{label}</span>
        <span className="num text-ink-muted">
          <span className="text-ink">= {counts.matches}</span> · ≠ {counts.differs} · <span className="text-unk-fg">? {counts.not_stated}</span>
        </span>
      </div>
      <div
        role="img"
        aria-label={`${label}: ${counts.matches} same as source, ${counts.differs} differ, ${counts.not_stated} not stated, of ${total} studies`}
        className="flex h-3 overflow-hidden rounded-sm border border-border-strong"
      >
        <span className="h-full bg-ink" style={{ width: pct(counts.matches) }} />
        <span className="h-full bg-sunken" style={{ width: pct(counts.differs) }} />
        <span className="h-full bg-hatch-unknown" style={{ width: pct(counts.not_stated) }} />
      </div>
    </div>
  );
}

function SourceBreakdown({ b }: { b: AuditBreakdown }) {
  const pliny = b.source === 'pliny_nh';
  return (
    <section className="flex flex-col gap-4 rounded border border-border bg-surface p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <SourceConfidenceMarker confidence={pliny ? sourcePliny : sourceCulpeper} />
        <span className="num text-sm text-ink-muted">{b.plants} plants · {b.studies} studies</span>
      </div>
      <MatchBar label="Solvent / vehicle" counts={b.vehicle} total={b.studies} />
      <MatchBar label="Heat" counts={b.heat} total={b.studies} />
      <MatchBar label="Filtration" counts={b.filtration} total={b.studies} />
      {pliny && <p className="m-0 text-xs text-ink-subtle">Counts include every candidate species of disputed names, so plants may be counted more than once.</p>}
      <ChartTable
        caption={`${pliny ? 'Pliny, NH' : 'Culpeper 1652'}: modern studies compared with the source's preparation (${b.studies} studies)`}
        headers={['Aspect', 'Same as source', 'Differs', 'Not stated']}
        numeric={[1, 2, 3]}
        rows={([['Solvent / vehicle', b.vehicle], ['Heat', b.heat], ['Filtration', b.filtration]] as const).map(([k, c]) => [k, c.matches, c.differs, c.not_stated])}
      />
    </section>
  );
}

export function Audit({ onNavigate, studies = STUDIES, summary = SUMMARY }: { onNavigate?: (p: string) => void; studies?: Study[]; summary?: AuditBreakdown[] }) {
  const taxa = [...new Set(studies.map((s) => s.taxon))];
  const [sel, setSel] = useState<string[]>([]);
  const [open, setOpen] = useState<Study | null>(null);
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
              <a href={pubmedUrl(s.pmid)} className="font-mono text-mod-fg underline underline-offset-2">PMID {s.pmid}</a>
            ) : (
              <UnknownValue label="Not in PubMed" />
            )}
          </span>
        </span>
      ),
    },
    { key: 'taxon', header: 'Plant', render: (s) => <Taxon name={s.taxon} /> },
    { key: 'part', header: 'Part', render: (s) => <Stated f={s.plantPart} /> },
    { key: 'solvent', header: 'Solvent', render: (s) => <Stated f={s.solvent} /> },
    { key: 'heat', header: 'Heat', render: (s) => <Stated f={s.heat} /> },
    { key: 'dur', header: 'Duration', render: (s) => <Stated f={s.duration} /> },
    { key: 'filt', header: 'Filtration', render: (s) => <Stated f={s.filtered} render={(v) => (v ? 'filtered' : 'unfiltered')} /> },
    { key: 'ratio', header: 'Ratio', render: (s) => <Stated f={s.ratio} /> },
    {
      key: 'vs', header: 'vs historical', hint: 'vehicle · heat · filtration',
      render: (s) => (
        <span className="flex flex-col items-start gap-1">
          <MatchChip state={s.match.vehicle} aspect="Vehicle" /><MatchChip state={s.match.heat} aspect="Heat" /><MatchChip state={s.match.filtration} aspect="Filtration" />
        </span>
      ),
    },
    { key: 'ev', header: 'Field evidence', hint: 'weakest field', render: (s) => <EvidenceStatusBadge status={weakest(s)} size="sm" /> },
  ];

  return (
    <AppShell current="audit" onNavigate={onNavigate}>
      <section aria-labelledby="by-source" className="flex flex-col gap-4">
        <h2 id="by-source" className="m-0 font-serif text-2xl font-medium">By source</h2>
        <p className="m-0 max-w-prose text-base text-ink-muted">For plants each source prescribes: how often modern studies used the same solvent, heat and filtration. “Not stated” means the paper does not say.</p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {summary.map((b) => <SourceBreakdown key={b.source} b={b} />)}
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-ink-muted">
          <span className="inline-flex items-center gap-1.5"><span aria-hidden className="h-2.5 w-4 rounded-sm bg-ink" /> Same as source</span>
          <span className="inline-flex items-center gap-1.5"><span aria-hidden className="h-2.5 w-4 rounded-sm border border-border-strong bg-sunken" /> Differs</span>
          <span className="inline-flex items-center gap-1.5 text-unk-fg"><span aria-hidden className="h-2.5 w-4 rounded-sm border border-unk-line bg-hatch-unknown" /> Not stated</span>
        </div>
      </section>

      <section aria-labelledby="studies" className="flex flex-col gap-4">
        <h2 id="studies" className="m-0 font-serif text-2xl font-medium">Studies</h2>
        <FilterGroup
          legend="Plant"
          options={taxa.map((t) => ({ value: t, label: t, count: studies.filter((s) => s.taxon === t).length }))}
          selected={sel}
          onChange={setSel}
        />
        <FilterSummary shown={shown.length} total={studies.length} onClear={() => setSel([])} />
        <DataTable caption="Modern study preparations compared with the historical preparation" columns={columns} rows={shown} rowKey={(s) => s.id} dense />
      </section>

      <Drawer open={!!open} onClose={() => setOpen(null)} title={open?.title ?? ''} eyebrow={open ? `Study · ${open.taxon}` : undefined}>
        {open && (
          <div className="flex flex-col gap-4">
            {open.pmid ? <a href={pubmedUrl(open.pmid)} className="w-max font-mono text-mod-fg underline">Open PMID {open.pmid} in PubMed</a> : <UnknownValue label="Not indexed in PubMed" />}
            <table className="w-full border-collapse text-sm">
              <caption className="sr-only">Extracted fields with evidence status</caption>
              <tbody>
                {([['Plant part', open.plantPart], ['Solvent', open.solvent], ['Heat', open.heat], ['Duration', open.duration], ['Filtration', open.filtered], ['Ratio', open.ratio]] as const).map(([k, f]) => (
                  <tr key={k} className="border-b border-border">
                    <th scope="row" className="py-2 pr-3 text-left font-medium">{k}</th>
                    <td className="py-2 pr-3">{f.value == null ? <UnknownValue label="Not stated" /> : typeof f.value === 'boolean' ? (f.value ? 'filtered' : 'unfiltered') : String(f.value)}</td>
                    <td className="py-2"><EvidenceStatusBadge status={f.evidence} size="sm" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="m-0 text-sm text-ink-muted">Compared against {open.comparedRecipeIds.length} historical recipe{open.comparedRecipeIds.length === 1 ? '' : 's'}.</p>
          </div>
        )}
      </Drawer>
    </AppShell>
  );
}
