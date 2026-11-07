import { useState, type MouseEvent } from 'react';
import {
  EvidenceStatusBadge, ExtractionDetectionExplainer, LikelihoodBar, LinkButton, PlateSlot, SegmentedControl, SiteShell,
  SourceConfidenceMarker, Taxon, ToxicityBadge, UnknownValue,
} from '../index';
import { LAB_PROFILES } from '../contract/lab';
import { plates, reportingGap } from '../contract';
import { sourceCulpeper, sourcePliny, toxNone } from '../gallery/mock';
import { pct } from '../lib/format';

/**
 * LANDING — the promise, a live mini-demo, three paths.
 * The demo is the real Lab data for liquorice: cold water vs decoction,
 * bars animate on toggle; an optional modern-lab overlay. Mock values.
 */
const liquorice = LAB_PROFILES.find((p) => p.taxon === 'Glycyrrhiza glabra')!;
const PREPS = {
  cold: liquorice.preparations.find((p) => p.id === 'water-cold-f-n')!,
  decoction: liquorice.preparations.find((p) => p.id === 'water-boiled-f-n')!,
};
const modern = liquorice.preparations.find((p) => p.preparation.family === 'modern')!;
const headline = reportingGap.rows.find((r) => r.field === reportingGap.headline.field)!;

export function Landing({ onNavigate }: { onNavigate?: (p: string) => void }) {
  const [which, setWhich] = useState<'cold' | 'decoction'>('cold');
  const [overlay, setOverlay] = useState(false);
  const prep = PREPS[which];
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); onNavigate(path); } };

  const PATHS = [
    { n: '01', title: 'Explore recipes', body: 'Search Culpeper and Pliny. Every plant, every passage, every extracted field — disputes left visible.', href: '/atlas', cta: 'Open the Recipe Atlas', taxon: 'Artemisia absinthium' },
    { n: '02', title: 'Preparation Lab', body: 'Change the solvent, heat, filtration and acidity. Watch the compound profile respond, ranges and all.', href: '/lab', cta: 'Start in the Lab', taxon: 'Glycyrrhiza glabra' },
    { n: '03', title: 'The evidence gap', body: 'How rarely modern studies say how they prepared the plant they tested.', href: '/evidence-gap', cta: 'See the gap', taxon: 'Salvia officinalis' },
  ];

  return (
    <SiteShell current="landing" onNavigate={onNavigate} bleed>
      {/* HERO */}
      <section className="mx-auto grid max-w-content grid-cols-1 items-center gap-10 px-4 pb-16 pt-10 md:px-8 md:pt-16 lg:grid-cols-12 lg:gap-14">
        <div className="flex flex-col gap-6 lg:col-span-6">
          <span className="eyebrow text-brand">Preparation-aware research tool</span>
          <h1 className="m-0 font-display text-4xl text-ink md:text-5xl">Historical remedies were <i className="text-brand">recipes</i>, not just plants.</h1>
          <p className="m-0 max-w-prose text-lg text-ink-muted">See what each preparation actually extracts — with the uncertainty left in.</p>
          <div className="flex flex-wrap gap-3">
            <LinkButton href="/lab" onClick={go('/lab')} variant="primary" size="lg">Open the Preparation Lab</LinkButton>
            <LinkButton href="/atlas" onClick={go('/atlas')} size="lg">Explore recipes</LinkButton>
          </div>
          <p className="m-0 text-sm text-ink-subtle">For pharmacognosists, historians of medicine and labs deciding what to test. Culpeper (1652) and Pliny’s <i>Natural History</i>.</p>
        </div>

        {/* Live mini-demo */}
        <div className="flex flex-col overflow-hidden rounded-xl border border-border bg-surface shadow-2 lg:col-span-6">
          <div className="flex items-center gap-4 border-b border-border p-4 md:p-5">
            <PlateSlot taxon="Glycyrrhiza glabra" plate={plates.find((p) => p.taxon === 'Glycyrrhiza glabra')} size="thumb" />
            <div className="flex min-w-0 flex-col gap-1">
              <span className="eyebrow text-ink-subtle">Try it · live</span>
              <span className="font-display text-xl text-ink"><Taxon name="Glycyrrhiza glabra" /> <span className="font-sans text-base text-ink-muted">· liquorice root</span></span>
              <span className="text-xs text-ink-subtle">Plate slot · public domain · Wikimedia Commons · to source</span>
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
            <ul className="m-0 flex list-none flex-col gap-4 p-0">
              {prep.estimates.map((e) => (
                <li key={e.compound} className="flex flex-col gap-1.5">
                  <span className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="font-semibold text-ink">{e.compound}</span>
                    <span className="text-sm text-ink-subtle">{e.compoundClass}</span>
                  </span>
                  <LikelihoodBar range={e.likelihood} label={`${e.compound}, ${prep.label}`} compare={overlay ? modern.estimates.find((m) => m.compound === e.compound)?.likelihood : null} compareLabel={modern.label} />
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap items-center gap-2 border-t border-border pt-4 text-sm text-ink-subtle">
              <ExtractionDetectionExplainer />
              <span className="font-mono text-xs">mock values · scale 0–1</span>
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
                <PlateSlot taxon={p.taxon} plate={plates.find((x) => x.taxon === p.taxon)} showCaption={false} className="[&>div]:rounded-none [&>div]:border-0 [&>div]:border-b" />
                <div className="flex flex-1 flex-col gap-2 p-5">
                  <span className="font-mono text-xs text-brand">{p.n}</span>
                  <h3 className="m-0 font-display text-2xl text-ink">
                    <a href={p.href} onClick={go(p.href)} className="text-ink no-underline after:absolute after:inset-0">{p.title}</a>
                  </h3>
                  <p className="m-0 text-ink-muted">{p.body}</p>
                  <span className="mt-auto pt-2 font-semibold text-brand group-hover:underline">{p.cta} →</span>
                </div>
              </li>
            ))}
          </ul>
          <p className="m-0 text-xs text-ink-subtle">Illustrations: 19th-century botanical plates, public domain, from Wikimedia Commons (slots shown with placeholders until each file and licence is confirmed).</p>
        </div>
      </section>

      {/* EVIDENCE GAP TEASER + HONESTY */}
      <section className="mx-auto grid max-w-content grid-cols-1 gap-8 px-4 py-14 md:px-8 lg:grid-cols-2">
        <div className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-6 shadow-1 md:p-8">
          <span className="eyebrow text-ink-subtle">The evidence gap · mock</span>
          <p className="m-0 font-display text-4xl text-ink">{headline.stated} <span className="text-ink-muted">of</span> {headline.n}</p>
          <p className="m-0 text-md text-ink-muted">modern studies say whether the plant was fresh or dried ({pct(headline.stated / headline.n)}; 95% interval {headline.ci ? `${pct(headline.ci[0])}–${pct(headline.ci[1])}` : 'not computed'}).</p>
          <div className="flex flex-wrap items-center gap-2"><EvidenceStatusBadge status={headline.evidence} size="sm" /></div>
          <LinkButton href="/evidence-gap" onClick={go('/evidence-gap')} className="w-max">See every detail →</LinkButton>
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
            <SourceConfidenceMarker confidence={sourceCulpeper} compact />
            <SourceConfidenceMarker confidence={sourcePliny} compact />
            <ToxicityBadge record={toxNone} />
            <UnknownValue />
          </div>
          <p className="m-0 text-ink-muted">Ranges, not points. Disputed plant names stay disputed. Unknowns stay visible. Toxic plants are analysis-only.</p>
          <a href="/docs" onClick={go('/docs')} className="w-max font-semibold text-brand underline underline-offset-4">How it was made: Methods &amp; data</a>
        </div>
      </section>

      {/* CASE STUDY TEASER */}
      <section className="border-t border-border bg-surface">
        <div className="mx-auto flex max-w-content flex-col items-start gap-4 px-4 py-14 md:px-8">
          <span className="eyebrow text-brand">Case study</span>
          <h2 className="m-0 max-w-prose font-display text-3xl text-ink">Liquorice, read as a recipe</h2>
          <p className="m-0 max-w-prose text-md text-ink-muted">The misreading, the evidence, the correction and the new result — one plant, followed through the tool.</p>
          <LinkButton href="/case/liquorice" onClick={go('/case/liquorice')}>Read the case study →</LinkButton>
        </div>
      </section>
    </SiteShell>
  );
}
