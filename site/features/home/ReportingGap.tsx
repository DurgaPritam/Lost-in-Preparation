import Link from '@/components/base/Link';
import type { GapRow } from '@/lib/data/selectors/home';
import { ciText, pct } from '@/lib/data/format';
import { ChartTable } from '@/components/base/ChartTable';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import { ShareBar } from '../shared/ShareBar';

type Set = { vars: GapRow[]; none: GapRow; all: GapRow };
export interface ReportingGapProps { prepared: Set; retrieved: Set; retrievedAbstract: Set; retrievedMethods: Set; v3: GapRow }

/** The caveat travels with the solvent share wherever it is shown. */
export function InflatedSolventCaveat() {
  return (
    <p role="note" className="m-0 rounded-sm border border-dashed border-border-strong bg-surface px-3 py-2 text-sm text-ink-muted">
      <span className="font-medium text-ink">Solvent share is inflated by construction.</span> A study counts as having prepared the plant partly
      because a solvent was stated, so this share is higher than it would be among all studies that prepared the plant.
    </p>
  );
}

const cell = (r: GapRow) => (r.value == null ? <UnknownValue /> : `${pct(r.value)} (${r.k}/${r.n})`);
const ci = (r: GapRow) => (r.value == null ? <UnknownValue /> : ciText(r.low, r.high));

/** SITE (new section, design tokens and components only): the headline reporting gap, after the artemisinin panels. */
export function ReportingGap(p: ReportingGapProps) {
  const n = p.prepared.none.n;
  return (
    <section aria-labelledby="gap" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <span className="small-caps text-xs text-ink-subtle">Headline · descriptive findings, not hypothesis tests</span>
        <h2 id="gap" className="m-0 font-serif text-2xl font-medium">Modern studies rarely say how the plant was prepared</h2>
      </div>
      <p className="m-0 max-w-prose text-base text-ink">
        Of the {n} studies that prepared the plant material (audit v2 eligibility), the share whose text states each preparation variable.
        Solvent, heat, fresh or dried, filtration and plant part each change what a preparation delivers.
      </p>
      <div className="flex flex-wrap items-center gap-2 text-sm text-ink-muted">
        <EvidenceStatusBadge status="pending" size="sm" detail="Coded by the rule-based extractor (a keyword heuristic). Its accuracy awaits the 40-study hand-check." />
        <span>“Stated” means the rule-based extractor coded a value.</span>
      </div>
      <div className="flex flex-col gap-4 rounded border border-border bg-surface p-5">
        {p.prepared.vars.map((r) => (
          <div key={r.key} className="flex flex-col gap-2">
            <ShareBar row={r} />
            {r.inflated && <InflatedSolventCaveat />}
          </div>
        ))}
        <div className="border-t border-border pt-4">
          <ShareBar row={{ ...p.prepared.none, label: 'None of the five stated' }} />
        </div>
        <p className="m-0 text-sm text-ink-muted">
          All five stated: {p.prepared.all.value == null ? <UnknownValue /> : `${pct(p.prepared.all.value)} (${p.prepared.all.k} of ${p.prepared.all.n}; ${ciText(p.prepared.all.low, p.prepared.all.high)})`}.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-3 rounded border border-border bg-surface p-5">
          <span className="small-caps text-xs text-ink-subtle">Every coded study retrieved for a plant–use pair · audit v1</span>
          <ShareBar row={{ ...p.retrieved.none, label: 'None of the five stated' }} />
          <ShareBar row={{ ...p.retrievedAbstract.vars[0], label: 'Heat stated · coded from abstracts' }} />
          <ShareBar row={{ ...p.retrievedMethods.vars[0], label: 'Heat stated · coded from open-access methods' }} />
        </div>
        <div className="flex flex-col gap-3 rounded border border-border bg-surface p-5">
          <span className="small-caps text-xs text-ink-subtle">Direct comparisons · pre-registered v3 screening</span>
          <ShareBar row={p.v3} />
          <p className="m-0 text-sm text-ink-muted">{p.v3.note}</p>
        </div>
      </div>
      <ChartTable
        caption="Share of studies stating each preparation variable, with n and 95% confidence intervals (Wilson)"
        headers={['Variable', 'Prepared the plant: share (k/n)', '95% CI', 'All retrieved: share (k/n)', '95% CI']}
        numeric={[1, 2, 3, 4]}
        rows={[
          ...p.prepared.vars.map((r, i) => [r.inflated ? `${r.label} (inflated by construction)` : r.label, cell(r), ci(r), cell(p.retrieved.vars[i]), ci(p.retrieved.vars[i])]),
          ['None of the five', cell(p.prepared.none), ci(p.prepared.none), cell(p.retrieved.none), ci(p.retrieved.none)],
          ['All five', cell(p.prepared.all), ci(p.prepared.all), cell(p.retrieved.all), ci(p.retrieved.all)],
          ['v3: compared two preparations of the same material', cell(p.v3), ci(p.v3), <UnknownValue key="na" label="Not applicable" />, <UnknownValue key="na2" label="Not applicable" />],
        ]}
      />
      <p className="m-0 max-w-prose text-sm text-ink-muted">
        Fidelity to the historical preparation is supporting detail with small n: see the{' '}
        <Link href="/audit/" className="text-ink underline underline-offset-2">Audit</Link>. How one extraction error changed a hypothesis:{' '}
        <Link href="/case-studies/liquorice/" className="text-ink underline underline-offset-2">the liquorice case study</Link>.
      </p>
    </section>
  );
}
