'use client';

/**
 * SITE (new page; design tokens and components only): the liquorice case study. An extraction misclassification, the
 * corpus evidence that corrected it, the logged corrections, and how the hypothesis changed. Data: case_studies.json
 * (contract v1.6, P37d) and the `corrections` of recipes.json (P37a).
 */
import Link from '@/components/base/Link';
import type { SourceConfidence, SourceWork, ToxicityRecord } from '@/lib/types';
import type { CaseView } from '@/lib/data/selectors/caseStudy';
import { SOURCE_LABEL } from '@/lib/data/format';
import { AppShell } from '@/components/layout/AppShell';
import { Card, SourcePassage } from '@/components/base/Card';
import { ChartTable } from '@/components/base/ChartTable';
import { DataTable } from '@/components/base/DataTable';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';

const FIELD_ORDER = ['part', 'solvent', 'heat', 'process', 'filtered'];
const val = (v: string | undefined) => (v == null || v === 'unknown' ? <UnknownValue label="Not stated" /> : <span className="font-mono">{v}</span>);
const GAP = 'Predicted profile gap (1 − cosine similarity)';

export function LiquoriceCase({ view, taxon, toxicity, hypothesisHref, compareHref, beforeCompareHref, confidences }: {
  view: CaseView; taxon: string; toxicity: ToxicityRecord; hypothesisHref: string | null; compareHref: string | null; beforeCompareHref: string | null;
  confidences: Record<SourceWork, SourceConfidence>;
}) {
  const c = view.study;
  const primary = view.corrections.filter((x) => x.recipeId === c.primaryRecipeId);
  const stages = [['Before correction', c.before], ['After correction', c.after]] as const;
  const primarySource: SourceWork = c.primaryRecipeId.startsWith('pliny') ? 'pliny_nh' : c.primaryRecipeId.startsWith('culpeper-1850') ? 'culpeper_1850' : 'culpeper_1652';
  const rankSame = c.before.rank === c.after.rank;
  const larger = c.after.gap.value > c.before.gap.value;
  return (
    <AppShell current="hypotheses" title="Case study: liquorice “juice”" question="How did one extraction error change a hypothesis, and what corrected it?">
      <div className="flex flex-col gap-3">
        <span className="small-caps text-xs text-ink-subtle">Case study · an extraction correction and its effect on one hypothesis</span>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-serif text-xl"><Taxon name={taxon} /></span>
          <span className="text-base text-ink-muted">· {c.indication.label}</span>
          <ToxicityBadge record={toxicity} />
        </div>
        <ToxicityNotice record={toxicity} />
        <p className="m-0 max-w-prose text-base text-ink-muted">{c.label.charAt(0).toUpperCase() + c.label.slice(1)}.</p>
      </div>

      <section aria-labelledby="mis" className="flex flex-col gap-4">
        <h2 id="mis" className="m-0 font-serif text-2xl font-medium">1 · The misclassification</h2>
        <div className="flex flex-wrap items-center gap-2">
          <SourceConfidenceMarker confidence={confidences[primarySource]} />
          <EvidenceStatusBadge status="provisional" size="sm" detail="The recipe was extracted by Claude in a Claude Code session; every quote passed the verbatim check." />
        </div>
        <SourcePassage cite={`${SOURCE_LABEL[primarySource].full} · recipe ${c.primaryRecipeId}`}>“{c.recipeQuote}”</SourcePassage>
        <p className="m-0 max-w-prose text-base">
          The extraction coded the part as <span className="font-mono">{c.extractedAs.part ?? 'unknown'}</span>, the vehicle as{' '}
          <span className="font-mono">{c.extractedAs.solvent ?? 'unknown'}</span> and the heat as <span className="font-mono">{c.extractedAs.heat ?? 'unknown'}</span>,
          so Phase 6 modelled it as <strong className="font-medium">{c.before.faithful}</strong>.
        </p>
        <div className="overflow-x-auto rounded border border-border bg-surface" tabIndex={0} role="region" aria-label="Fields as extracted and as corrected (scrolls sideways)">
          <table className="w-full border-collapse text-sm">
            <caption className="px-3 py-2 text-left text-sm text-ink-muted">Fields as extracted and as corrected</caption>
            <thead className="bg-sunken">
              <tr className="text-left">
                <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">Field</th>
                <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">As extracted</th>
                <th scope="col" className="border-b border-border-strong px-3 py-2 font-medium">Corrected to</th>
              </tr>
            </thead>
            <tbody>
              {FIELD_ORDER.filter((f) => f in c.correctedTo || f in c.extractedAs).map((f) => (
                <tr key={f} className="border-b border-border last:border-b-0">
                  <th scope="row" className="px-3 py-2 text-left font-medium">{f}</th>
                  <td className="px-3 py-2">{val(c.extractedAs[f])}</td>
                  <td className="px-3 py-2">{val(c.correctedTo[f])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="ev" className="flex flex-col gap-4">
        <h2 id="ev" className="m-0 font-serif text-2xl font-medium">2 · The corpus evidence that corrected it</h2>
        <p className="m-0 max-w-prose text-base text-ink-muted">In older pharmacy, liquorice “juice” is a boiled, strained and concentrated water extract of the root, not a fresh pressed juice. The project’s own texts say so.</p>
        {c.evidence.map((e) => (
          <SourcePassage key={e.passageId} cite={`${e.citation} · passage ${e.passageId}`}>{e.text}</SourcePassage>
        ))}
      </section>

      <section aria-labelledby="log" className="flex flex-col gap-4">
        <h2 id="log" className="m-0 font-serif text-2xl font-medium">3 · The logged corrections</h2>
        <p className="m-0 max-w-prose text-base text-ink-muted">
          Requested by the project lead and applied as an overlay: the extraction output itself is never edited. {view.corrections.length} field corrections across{' '}
          {new Set(view.corrections.map((x) => x.recipeId)).size} recipes (<span className="font-mono">config/m1_corrections.csv</span>).
        </p>
        <DataTable
          caption="Every logged correction to a liquorice recipe"
          rowKey={(x) => `${x.recipeId}-${x.field}`}
          rows={view.corrections}
          columns={[
            { key: 'r', header: 'Recipe', render: (x) => <span className="flex flex-col gap-0.5"><Link href={x.href} className="font-mono text-sm text-ink underline underline-offset-2">{x.recipeId}</Link><span className="text-xs text-ink-subtle">{SOURCE_LABEL[x.source].short}</span></span> },
            { key: 'f', header: 'Field', render: (x) => x.field },
            { key: 'from', header: 'As extracted', render: (x) => val(x.from) },
            { key: 'to', header: 'Corrected to', render: (x) => val(x.to) },
            { key: 'why', header: 'Reason', render: (x) => <span className="text-sm">{x.reason}</span> },
          ]}
        />
        {primary.length > 0 && <p className="m-0 text-sm text-ink-muted">Evidence recorded with the corrections: {primary[0].evidence}</p>}
      </section>

      <section aria-labelledby="rank" className="flex flex-col gap-4">
        <h2 id="rank" className="m-0 font-serif text-2xl font-medium">4 · How the hypothesis changed</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {stages.map(([label, st]) => (
            <Card key={label} as="section" eyebrow={label} title={`Rank ${st.rank} of ${st.rankedOf}`}
                  footer={(label.startsWith('After') ? compareHref : beforeCompareHref) ? <Link href={(label.startsWith('After') ? compareHref : beforeCompareHref)!} className="text-sm text-ink underline underline-offset-2">Open this comparison</Link> : undefined}>
              <p className="m-0 text-base">{st.faithful} <span className="text-ink-muted">vs</span> {st.modern}</p>
              <LikelihoodBar range={{ low: st.gap.low, high: st.gap.high, point: st.gap.value }} family="neutral" label="Faithful vs modern" measure={GAP} width="full" showScale />
            </Card>
          ))}
        </div>
        <ChartTable
          label="View the ranking as a table"
          caption="Phase 6 (audit v1): the liquorice hypothesis before and after the correction; gap = 5th / median / 95th percentile"
          headers={['Stage', 'Faithful preparation', 'Modern preparation', 'Rank', 'Gap 5th', 'Median gap', 'Gap 95th']}
          numeric={[3, 4, 5, 6]}
          rows={stages.map(([label, st]) => [label, st.faithful, st.modern, `${st.rank} of ${st.rankedOf}`, st.gap.low.toFixed(2), st.gap.value.toFixed(2), st.gap.high.toFixed(2)])}
        />
        <p className="m-0 max-w-prose text-base">
          {rankSame ? `The rank did not change (${c.after.rank} of ${c.after.rankedOf}).` : `The rank moved from ${c.before.rank} to ${c.after.rank}.`}{' '}
          The median predicted gap went from {c.before.gap.value.toFixed(2)} to {c.after.gap.value.toFixed(2)}: the model predicts that a {c.after.faithful} carries a
          {larger ? ' more different' : ' less different'} compound profile from a {c.after.modern} than a {c.before.faithful} does. It is a hypothesis worth
          re-testing, not a medical claim about liquorice.
        </p>
        {hypothesisHref && <Link href={hypothesisHref} className="w-max text-base font-medium text-ink underline underline-offset-4">Open the hypothesis and its evidence trail →</Link>}
        <ExtractionDetectionExplainer />
      </section>
    </AppShell>
  );
}
