'use client';

import { useMemo, useState } from 'react';
import type { EngineModel } from '@/lib/engine';
import type { ReportingGapView, SourceConfidence, SourceWork } from '@/lib/types';
import { compareRanges, pct } from '@/lib/data/format';
import { modernPrep, prepFor, toEstimates } from '@/lib/data/selectors/lab';
import type { LabPlant } from '@/lib/data/assemble';
import { useProfile } from '@/features/engine/useProfile';
import { SiteShell } from '@/components/layout/SiteShell';
import { SegmentedControl } from '@/components/base/Controls';
import { LinkButton } from '@/components/base/Button';
import { LoadingState } from '@/components/base/States';
import { PlateSlot } from '@/components/base/PlateSlot';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import Link from '@/components/base/Link';

/**
 * LANDING — the promise, a live mini-demo, three paths (design v2 screens/Landing.tsx).
 * SITE: the demo is computed live by the preparation engine in its Web Worker for a plant with no toxicity reported
 * (liquorice, the design's choice, has toxicity reported in this data, and a front-door "try it" must never feature a
 * toxic plant). It shows the five compounds whose predicted median changes most between the two preparations, and says
 * so. Values are model estimates, not mocks.
 */
const SHOW = 5;

export interface LandingProps {
  demo: LabPlant;
  gap: ReportingGapView;
  confidences: Record<SourceWork, SourceConfidence>;
  pathPlates: ({ taxon: string; plate: LabPlant['plate'] } | null)[];
  caseTitle: string | null;
  plateCount: number;
  model: EngineModel;
}

export function Landing({ demo, gap, confidences, pathPlates, caseTitle, model }: LandingProps) {
  const [which, setWhich] = useState<'cold' | 'decoction'>('cold');
  const [overlay, setOverlay] = useState(false);
  const coldPrep = prepFor(model, { solvent: 'water', heat: 'cold', filtered: true, acidified: false });
  const decPrep = prepFor(model, { solvent: 'water', heat: 'boiled', filtered: true, acidified: false });
  const cold = useProfile('demo-cold', demo.speciesId, coldPrep);
  const dec = useProfile('demo-decoction', demo.speciesId, decPrep);
  const mod = useProfile('demo-modern', overlay ? demo.speciesId : null, modernPrep(model));

  const view = useMemo(() => {
    if (!cold.estimates || !dec.estimates || !cold.compounds) return null;
    const c = toEstimates(cold.compounds, cold.estimates, null);
    const d = toEstimates(cold.compounds, dec.estimates, null);
    const order = c.map((_, i) => i).sort((i, j) =>
      Math.abs((d[j].likelihood.point ?? 0) - (c[j].likelihood.point ?? 0)) - Math.abs((d[i].likelihood.point ?? 0) - (c[i].likelihood.point ?? 0))
      || c[i].compound.localeCompare(c[j].compound)).slice(0, SHOW);
    return { c, d, order, total: c.length };
  }, [cold.estimates, dec.estimates, cold.compounds]);
  const m = mod.estimates && mod.compounds ? toEstimates(mod.compounds, mod.estimates, null) : null;
  const shown = view ? (which === 'cold' ? view.c : view.d) : null;
  const label = which === 'cold' ? 'cold water infusion' : 'decoction in water';
  const head = gap.rows.find((r) => r.field === gap.headline.field) ?? null;

  const PATHS = [
    { n: '01', title: 'Explore recipes', body: 'Search Culpeper and Pliny. Every plant, every passage, every extracted field — disputes left visible.', href: '/atlas/', cta: 'Open the Recipe Atlas', p: pathPlates[0] },
    { n: '02', title: 'Preparation Lab', body: 'Change the solvent, heat, filtration and acidity. Watch the compound profile respond, ranges and all.', href: '/lab/', cta: 'Start in the Lab', p: pathPlates[1] },
    { n: '03', title: 'The evidence gap', body: 'How rarely modern studies say how they prepared the plant they tested.', href: '/evidence-gap/', cta: 'See the gap', p: pathPlates[2] },
  ];

  return (
    <SiteShell current="landing" bleed>
      {/* HERO */}
      <section className="mx-auto grid max-w-content grid-cols-1 items-center gap-10 px-4 pb-16 pt-10 md:px-8 md:pt-16 lg:grid-cols-12 lg:gap-14">
        <div className="flex flex-col gap-6 lg:col-span-6">
          <span className="eyebrow text-brand">Preparation-aware research tool</span>
          <h1 className="m-0 font-display text-4xl text-ink md:text-5xl">Historical remedies were <i className="text-brand">recipes</i>, not just plants.</h1>
          <p className="m-0 max-w-prose text-lg text-ink-muted">See what each preparation would extract — with the uncertainty left in.</p>
          <div className="flex flex-wrap gap-3">
            <LinkButton href="/lab/" variant="primary" size="lg">Open the Preparation Lab</LinkButton>
            <LinkButton href="/atlas/" size="lg">Explore recipes</LinkButton>
          </div>
          <p className="m-0 text-sm text-ink-subtle">For pharmacognosists, historians of medicine and labs deciding what to test. Culpeper (1652 and 1850 editions) and Pliny’s <i>Natural History</i>.</p>
        </div>

        {/* Live mini-demo (engine in a Web Worker) */}
        <div className="flex flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-2 lg:col-span-6">
          <div className="flex items-center gap-4 border-b border-border p-4 md:p-5">
            <PlateSlot taxon={demo.taxon} plate={demo.plate} size="thumb" />
            <div className="flex min-w-0 flex-col gap-1">
              <span className="eyebrow text-ink-subtle">Live · computed in your browser</span>
              <span className="font-display text-xl text-ink"><Taxon name={demo.taxon} /></span>
              <span className="flex flex-wrap items-center gap-2"><ToxicityBadge record={demo.toxicity} /></span>
            </div>
          </div>
          <div className="flex flex-col gap-5 p-4 md:p-5">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <SegmentedControl label="Preparation" hideLabel value={which} onChange={setWhich} options={[{ value: 'cold', label: 'Cold water' }, { value: 'decoction', label: 'Decoction' }]} />
              <label className="inline-flex items-center gap-2 text-sm text-ink-muted">
                <input type="checkbox" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} className="h-4 w-4 accent-[var(--c-mod-solid)]" />
                Overlay modern lab method
              </label>
            </div>
            {!view || !shown ? <LoadingState label="Computing the two preparations" rows={SHOW} /> : (
              <ul className="m-0 flex list-none flex-col gap-4 p-0" data-engine-status="ready">
                {view.order.map((i) => {
                  const e = shown[i];
                  const other = which === 'cold' ? view.d[i] : view.c[i];
                  const v = compareRanges(e.likelihood, other.likelihood);
                  return (
                    <li key={i} className="flex flex-col gap-1.5">
                      <span className="flex flex-wrap items-baseline justify-between gap-2">
                        <span className="min-w-0 break-words font-semibold text-ink">{e.compound}</span>
                        <span className="text-sm text-ink-subtle">{e.compoundClass}{v === 'overlap' ? ' · ranges overlap' : ''}</span>
                      </span>
                      <LikelihoodBar range={e.likelihood} label={`${e.compound}, ${label}`} compare={overlay ? (m?.[i]?.likelihood ?? { low: null, high: null }) : null} compareLabel="modern methanol extract" />
                    </li>
                  );
                })}
              </ul>
            )}
            <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4 text-sm text-ink-subtle">
              <ExtractionDetectionExplainer />
              <span className="font-mono text-xs">model estimates · scale 0–1 · {view ? `${SHOW} of ${view.total} compounds: the largest predicted changes` : 'computing'}</span>
            </div>
          </div>
        </div>
      </section>

      {/* THREE PATHS */}
      <section aria-labelledby="paths" className="border-t border-border bg-surface">
        <div className="mx-auto flex max-w-content flex-col gap-8 px-4 py-14 md:px-8">
          <h2 id="paths" className="m-0 font-display text-3xl text-ink">Three ways in</h2>
          <ul className="m-0 grid list-none grid-cols-1 gap-6 p-0 md:grid-cols-3">
            {PATHS.map((p) => (
              <li key={p.n} className="group relative flex flex-col overflow-hidden rounded-lg border border-border bg-paper shadow-1 transition-shadow duration-base ease-standard hover:shadow-2">
                <PlateSlot taxon={p.p?.taxon ?? ''} plate={p.p?.plate} showCaption={false} className="[&>div]:rounded-none [&>div]:border-0 [&>div]:border-b" />
                <div className="flex flex-1 flex-col gap-2 p-5">
                  <span className="font-mono text-xs text-brand">{p.n}</span>
                  <h3 className="m-0 font-display text-2xl text-ink">
                    <Link href={p.href} className="text-ink no-underline after:absolute after:inset-0">{p.title}</Link>
                  </h3>
                  <p className="m-0 text-ink-muted">{p.body}</p>
                  {p.p && <span className="text-xs text-ink-subtle">Plate: <Taxon name={p.p.taxon} /></span>}
                  <span className="mt-auto pt-2 font-semibold text-brand group-hover:underline">{p.cta} →</span>
                </div>
              </li>
            ))}
          </ul>
          <p className="m-0 text-xs text-ink-subtle">Illustrations: 19th-century botanical plates, public domain, from Wikimedia Commons; licences read from Commons; not yet independently confirmed. <Link href="/credits/" className="underline underline-offset-2">Image credits</Link>.</p>
        </div>
      </section>

      {/* EVIDENCE GAP TEASER + HONESTY */}
      <section className="mx-auto grid max-w-content grid-cols-1 gap-8 px-4 py-14 md:px-8 lg:grid-cols-2">
        <div className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-6 shadow-1 md:p-8">
          <span className="eyebrow text-ink-subtle">The evidence gap</span>
          {head ? (
            <>
              <p className="m-0 font-display text-4xl text-ink">{head.stated} <span className="text-ink-muted">of</span> {head.n}</p>
              <p className="m-0 text-md text-ink-muted">modern studies that prepared the plant say whether it was fresh or dried ({pct(head.stated / head.n)}; 95% interval {head.ci ? `${pct(head.ci[0])}–${pct(head.ci[1])}` : 'not computed'}).</p>
              <div className="flex flex-wrap items-center gap-2"><EvidenceStatusBadge status={head.evidence} size="sm" detail="“Stated” means the rule-based extractor coded a value. Its accuracy is checked only against a second coding of a study sample, so the share is provisional." /></div>
            </>
          ) : <UnknownValue label="Not computed" />}
          <LinkButton href="/evidence-gap/" className="w-max">See every detail →</LinkButton>
        </div>
        <div className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-6 shadow-1 md:p-8">
          <span className="eyebrow text-ink-subtle">Honest by design</span>
          <h2 className="m-0 font-display text-2xl text-ink">Every number shows how far to trust it</h2>
          <div className="flex flex-wrap items-center gap-2">
            <EvidenceStatusBadge status="validated" size="sm" />
            <EvidenceStatusBadge status="provisional" size="sm" />
            <EvidenceStatusBadge status="pending" size="sm" />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <SourceConfidenceMarker confidence={confidences.culpeper_1652} compact />
            <SourceConfidenceMarker confidence={confidences.culpeper_1850} compact />
            <SourceConfidenceMarker confidence={confidences.pliny_nh} compact />
            <UnknownValue />
          </div>
          <p className="m-0 text-ink-muted">Ranges, not points. Disputed plant names stay disputed. Unknowns stay visible. Plants with toxicity reported are analysis-only.</p>
          <Link href="/docs/" className="w-max font-semibold text-brand underline underline-offset-4">How it was made: Methods &amp; data</Link>
        </div>
      </section>

      {/* CASE STUDY TEASER */}
      <section className="border-t border-border bg-surface">
        <div className="mx-auto flex max-w-content flex-col items-start gap-4 px-4 py-14 md:px-8">
          <span className="eyebrow text-brand">Case study</span>
          <h2 className="m-0 max-w-prose font-display text-3xl text-ink">Liquorice, read as a recipe</h2>
          <p className="m-0 max-w-prose text-md text-ink-muted">{caseTitle ? `${caseTitle}: ` : ''}the misreading, the evidence, the correction and the new result — one plant, followed through the tool.</p>
          <LinkButton href="/case/liquorice/">Read the case study →</LinkButton>
        </div>
      </section>
    </SiteShell>
  );
}
