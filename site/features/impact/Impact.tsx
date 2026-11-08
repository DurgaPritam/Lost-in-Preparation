'use client';

import type { ReactNode } from 'react';
import type { ReportingGapRow } from '@/lib/types';
import Link from '@/components/base/Link';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { DataTable } from '@/components/base/DataTable';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { pct } from '@/lib/data/format';

/**
 * IMPACT & ETHICS (SITE addition, not in the design handoff): who the outputs are for, the reporting checklist the
 * headline finding implies, the terms on which traditional knowledge is used, and what scaling beyond the hackathon
 * needs. Every number comes from site-data (metrics.reportingGap, recipes.json, hypotheses.json); nothing is typed in.
 */

/** What a methods section would state for each of the audit's five variables (the audit lexicon's fields). */
const ASK: Record<ReportingGapRow['field'], string> = {
  solvent: 'The liquid used and its strength (water, wine or ethanol %, oil, vinegar), and the plant-to-solvent ratio.',
  part: 'The plant part (root, leaf, flower, seed, whole aerial parts) and its identification (voucher specimen).',
  heat: 'Cold, warm or boiled, with temperature and duration.',
  freshOrDried: 'Fresh or dried material, and how it was dried.',
  filtration: 'Whether the preparation was strained or filtered before use or analysis.',
};

const ciText = (ci: [number, number] | null) => (ci ? `${pct(ci[0])}–${pct(ci[1])}` : 'not computed');

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section aria-labelledby={id} className="flex flex-col gap-4">
      <h2 id={id} className="m-0 font-display text-2xl text-ink">{title}</h2>
      {children}
    </section>
  );
}

function Audience({ who, gets, children }: { who: string; gets: string; children: ReactNode }) {
  return (
    <li className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-5">
      <span className="eyebrow text-brand">{who}</span>
      <span className="font-semibold text-ink">{gets}</span>
      <span className="text-sm text-ink-muted">{children}</span>
    </li>
  );
}

export interface ImpactProps {
  rows: ReportingGapRow[];

  compared: { stated: number; n: number; ci: [number, number] | null } | null;
  recipes: number;
  hypotheses: number;
}

export function Impact({ rows, compared, recipes, hypotheses }: ImpactProps) {
  const n = rows[0]?.n;
  const heat = rows.find((r) => r.field === 'heat');
  const fresh = rows.find((r) => r.field === 'freshOrDried');
  return (
    <SiteShell current="impact">
      <PageHeader
        eyebrow="Impact & ethics"
        title="Who this is for, and the terms it keeps"
        lead="The headline finding is that modern studies rarely say how they prepared a plant. This page sets out who can act on that, the reporting checklist it implies, the terms on which this project uses traditional knowledge, and what it would take to go beyond the hackathon."
      />

      <Section id="who" title="Who can use it">
        <ul className="m-0 grid list-none gap-4 p-0 md:grid-cols-2">
          <Audience who="Drug discovery" gets="A short list of experiments, each prepared as the recipe said">
            Natural-product labs usually screen a standard solvent extract. The <Link href="/planner/" className="text-brand underline">Lab Planner</Link> picks
            a re-test panel from the {hypotheses} ranked hypotheses: plant–use pairs never tested the way they were made, with toxic species excluded.
            Artemisinin is the reference case: the activity was there once the preparation followed the old text.
          </Audience>
          <Audience who="Journals and reviewers" gets="A five-item reporting checklist">
            {heat && fresh && <>Of {heat.n} studies that prepared the plant, {heat.stated} said whether heat was used and {fresh.stated} whether the plant was fresh or dried. </>}
            The checklist below costs authors a few lines of methods text and makes a negative result interpretable.
          </Audience>
          <Audience who="Public health" gets="A way to see what a home preparation contains">
            People take plants as teas, decoctions, tinctures and oils, not as lab extracts. A study of one preparation can say little about another, and that
            cuts both ways: a compound of concern can be present in one and absent from the other. The <Link href="/lab/" className="text-brand underline">Preparation Lab</Link> shows
            the predicted difference with its uncertainty range. It gives no guidance on preparing or taking any plant.
          </Audience>
          <Audience who="Conservation of knowledge" gets={`${recipes} recipes kept with their exact words`}>
            Databases of traditional uses usually record a plant and a use, and drop the preparation. Here every recipe field is tied to a verbatim quote, so the
            how is kept alongside the what. A smaller, better-aimed set of experiments should also need less plant material to be collected for screening; we
            have not measured that.
          </Audience>
        </ul>
      </Section>

      <Section id="checklist" title="A preparation reporting checklist (proposed)">
        <p className="m-0 max-w-prose text-sm text-ink-muted">
          The five details the audit codes, with what a methods section would state and how often the {n ?? ''} studies that prepared the plant stated it.
          A sixth item applies whenever a study evaluates a traditional use: test at least one preparation made the traditional way, alongside the lab extract.
          {compared && <> Today, {compared.stated} of {compared.n} article screenings ({pct(compared.stated / compared.n, 1)}, 95% interval {ciText(compared.ci)}) compared two preparations of the same plant material.</>}
        </p>
        <DataTable
          caption="Preparation reporting checklist, with the share of studies stating each item"
          rows={rows}
          rowKey={(r) => r.field}
          columns={[
            { key: 'item', header: 'Item', render: (r) => <span className="font-semibold">{r.label}</span> },
            { key: 'ask', header: 'What to state', render: (r) => ASK[r.field] },
            { key: 'now', header: 'Stated today', render: (r) => <span className="font-mono text-sm">{r.stated}/{r.n} · {pct(r.stated / r.n)} <span className="text-ink-subtle">(95% interval {ciText(r.ci)})</span>{r.inflated && <span className="block text-xs text-ink-subtle">inflated by construction: eligibility partly selects on a stated solvent</span>}</span>, sortValue: (r) => r.stated / r.n },
          ]}
        />
        <p className="m-0 flex flex-wrap items-center gap-2 text-sm text-ink-muted">
          <EvidenceStatusBadge wording="validation" status="pending" size="sm" detail="The shares come from the rule-based extractor; its human hand-check is pending." />
          The checklist is a proposal from this project; no journal has adopted it. Details: <Link href="/evidence-gap/" className="text-brand underline">the evidence gap</Link>.
        </p>
      </Section>

      <Section id="ethics" title="Traditional knowledge: whose knowledge, on what terms">
        <ul className="m-0 flex max-w-prose list-disc flex-col gap-3 pl-5 text-ink-muted">
          <li>
            <span className="font-semibold text-ink">Only published, public-domain texts.</span> The recipes come from Culpeper (1652 and 1850) and Pliny’s <i>Natural History</i> in
            a 19th-century translation. No knowledge was collected from a living community, so no community’s consent was needed and none was bypassed. This
            was a deliberate choice for a hackathon, where there is no time to build a partnership properly.
          </li>
          <li>
            <span className="font-semibold text-ink">These texts are themselves compilations.</span> Both authors drew on earlier, often unnamed, practitioners. We
            credit the texts; we cannot credit those people, and we say so rather than treat the knowledge as authorless.
          </li>
          <li>
            <span className="font-semibold text-ink">Living traditions would need different terms.</span> Before this method touches the knowledge of a living
            community, the project would follow the CARE Principles for Indigenous Data Governance (collective benefit, authority to control, responsibility,
            ethics), seek free, prior and informed consent through a community partnership, and agree access and benefit-sharing terms in line with the Nagoya
            Protocol. The community, not the project, would decide what is published. Our CC BY licence would not be the default for that data; Local Contexts
            Traditional Knowledge labels are one way to carry the community’s terms with it.
          </li>
          <li>
            <span className="font-semibold text-ink">No medical claims.</span> The outputs are hypotheses worth re-testing. Every species in the study set carries a
            cited toxicity entry (not yet reviewed by a toxicologist), and plants with reported toxicity never get a Lab link, a plan action or a Planner slot.
          </li>
        </ul>
      </Section>

      <Section id="scale" title="Beyond the hackathon">
        <div className="grid gap-6 md:grid-cols-2">
          <div className="flex flex-col gap-2">
            <h3 className="m-0 text-lg font-semibold text-ink">What already generalises</h3>
            <ul className="m-0 flex list-disc flex-col gap-2 pl-5 text-sm text-ink-muted">
              <li>Name resolution uses World Flora Online and compounds come from LOTUS: both are global, not European.</li>
              <li>The preparation model handles solvent, heat, filtration and acidity as separate factors, which any recipe tradition can be described with.</li>
              <li>The audit lexicon is versioned and the audit protocol is fixed before retrieval, so a new plant set can be audited the same way.</li>
              <li>Running costs are close to zero: the site is static, and the pipeline reruns from a fresh clone with no API keys.</li>
            </ul>
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="m-0 text-lg font-semibold text-ink">What it needs next, in order</h3>
            <ol className="m-0 flex list-decimal flex-col gap-2 pl-5 text-sm text-ink-muted">
              <li>Independent checks: the 50-passage reference annotation, the 40-study hand-check, 30 scholarly name identifications and the toxicity review.</li>
              <li>A partner lab to run the top re-test panel, each plant prepared as the recipe said, beside a standard extract.</li>
              <li>Paired measurements for water preparations, where the model is unvalidated.</li>
              <li>More texts, in more languages, each with a scholar of that tradition: the bottleneck is expertise in historical plant names, not computing power.</li>
              <li>Taking the reporting checklist to ethnopharmacology journals.</li>
            </ol>
          </div>
        </div>
      </Section>
    </SiteShell>
  );
}
