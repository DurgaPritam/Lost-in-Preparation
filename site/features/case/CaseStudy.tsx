'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import type { Heuristic, Hypothesis, Plate, Recipe, SourceConfidence, ToxicityRecord } from '@/lib/types';
import { SOURCE_LABEL } from '@/lib/data/format';
import { preparationOfKey } from '@/lib/data/selectors/prepKey';
import type { CaseFigure } from '@/lib/data/assemble';
import type { CaseView } from '@/lib/data/selectors/caseStudy';
import { SiteShell } from '@/components/layout/SiteShell';
import { ChartTable } from '@/components/base/ChartTable';
import { LinkButton } from '@/components/base/Button';
import { PlateSlot } from '@/components/base/PlateSlot';
import { PrepLegend, PrepTag } from '@/components/base/PrepTag';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { HeuristicMarker } from '@/components/honesty/HeuristicMarker';
import { LikelihoodBar } from '@/components/honesty/LikelihoodBar';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge, ToxicityNotice } from '@/components/honesty/ToxicityBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import Link from '@/components/base/Link';

/**
 * CASE STUDY — liquorice as a scroll story in four chapters (design v2 screens/CaseStudy.tsx).
 * SITE: the design's [MOCK STORY] copy is replaced by the project's own analysis, written from case_studies.json
 * (contract v1.6, P37d) and the corrected recipes; every number comes from that file or the published profiles. The
 * plant has toxicity reported, so the page ends on the ToxicityNotice with no "Try it in the Lab" or Planner action
 * (acceptance check 5; the lead is withheld from the Planner).
 */
type Step = 0 | 1 | 2 | 3;

export interface CaseStudyProps extends CaseView {
  taxon: string; toxicity: ToxicityRecord; plate: Plate | null; recipe: Recipe | null; recipeHref: string | null; confidence: SourceConfidence | null;
  hypothesis: Hypothesis | null; plannerRank: number | null; withheldFromPlanner: boolean; before: CaseFigure | null; after: CaseFigure | null;
  toxicReported: boolean; heat: Heuristic | undefined;
}

const human = (v: string) => v.replace(/_/g, ' ');

function FigureBars({ f, family }: { f: CaseFigure; family?: 'historical' }) {
  return (
    <div className="flex flex-col gap-3">
      <PrepLegend modernLabel={f.compareLabel} />
      {f.rows.map((r) => (
        <div key={r.compound} className="flex flex-col gap-1">
          <span className="break-words text-sm font-semibold">{r.compound} <span className="font-normal text-ink-subtle">· {r.compoundClass}</span></span>
          <LikelihoodBar range={r.a} compare={r.b} compareLabel={f.compareLabel} label={`${r.compound}, ${f.label}`} family={family} size="sm" />
        </div>
      ))}
      <span className="text-xs text-ink-subtle">{f.shown} of {f.total} compounds: those whose ranges separate most between the two preparations. Model estimates, not measurements.</span>
    </div>
  );
}

export function CaseStudy(props: CaseStudyProps) {
  const { study: c, corrections, taxon, toxicity, plate, recipe, recipeHref, confidence, hypothesis: h, withheldFromPlanner, before, after, heat } = props;
  const [step, setStep] = useState<Step>(0);
  const refs = useRef<Array<HTMLElement | null>>([]);
  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver((entries) => {
      const vis = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (vis) setStep(Number((vis.target as HTMLElement).dataset.step) as Step);
    }, { rootMargin: '-40% 0px -40% 0px', threshold: [0, 0.25, 0.5, 1] });
    refs.current.forEach((r) => r && io.observe(r));
    return () => io.disconnect();
  }, []);

  const recipeIds = [...new Set(corrections.map((x) => x.recipeId))];
  const ex = c.extractedAs;
  const co = c.correctedTo;
  const extractedPrep = preparationOfKey(`${ex.part}|unknown|${ex.solvent}|${ex.heat}|${ex.filtered}`);
  const correctedPrep = preparationOfKey(`${co.part}|unknown|${co.solvent}|${co.heat}|${co.filtered}`);
  const fmtGap = (g: { value: number; low: number; high: number }) => `${g.low.toFixed(2)}–${g.high.toFixed(2)} (median ${g.value.toFixed(2)})`;

  const CHAPTERS: { n: string; title: string; body: ReactNode }[] = [
    { n: 'I', title: 'The misreading', body: <>The extraction read the recipe’s <i>{c.title.replace(/^.*?“|”.*$/g, '')}</i> literally: part {human(ex.part)}, solvent {human(ex.solvent)}, heat {human(ex.heat)}, process {human(ex.process)}. So the pipeline modelled it as <strong className="font-semibold">{c.before.faithful}</strong> and compared that with the {c.before.modern}.</> },
    { n: 'II', title: 'The evidence', body: <>The correction rests on the corpus itself: it cites {c.evidence.length} passage{c.evidence.length === 1 ? '' : 's'} on what the juice was{c.evidence[0] ? <>, among them “{c.evidence[0].text}” ({c.evidence[0].citation}).</> : '.'}</> },
    { n: 'III', title: 'The correction', body: <>{corrections.length} field correction{corrections.length === 1 ? '' : 's'} across {recipeIds.length} recipe{recipeIds.length === 1 ? '' : 's'} were logged, each with its evidence, and applied: part {human(co.part)}, solvent {human(co.solvent)}, heat {human(co.heat)}, process {human(co.process)}, filtered {human(co.filtered)}. The recipes themselves stay as extracted.</> },
    { n: 'IV', title: 'The new result', body: <>Modelled as {c.after.faithful} against the {c.after.modern}, the predicted profile gap moves from {fmtGap(c.before.gap)} to {fmtGap(c.after.gap)}; the lead stays rank {c.after.rank} of {c.after.rankedOf}. It is a hypothesis for the lab, not a finding, and not a recommendation.</> },
  ];

  function Figure({ s }: { s: Step }) {
    if (s === 0) return (
      <div className="flex flex-col gap-4">
        <span className="eyebrow text-ink-subtle">As first extracted</span>
        <div className="flex flex-wrap gap-2"><PrepTag prep={extractedPrep} /></div>
        {before ? <FigureBars f={before} /> : <UnknownValue label="Profile not available" />}
      </div>
    );
    if (s === 1) return (
      <div className="flex flex-col gap-4">
        <span className="eyebrow text-ink-subtle">The recipe, as written</span>
        <blockquote className="m-0 break-words font-display text-xl italic text-ink">“{c.recipeQuote}”</blockquote>
        {recipe && <span className="text-xs text-ink-subtle">{SOURCE_LABEL[recipe.source].full} · <Link href={recipeHref ?? '#'} className="underline underline-offset-2">the recipe page</Link></span>}
        <div className="flex flex-wrap gap-2">{confidence && <SourceConfidenceMarker confidence={confidence} />}{recipe && <EvidenceStatusBadge status={recipe.evidence} size="sm" />}</div>
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {c.evidence.map((e) => <li key={e.passageId} className="rounded-md border border-border p-3 text-sm"><span className="font-display text-md italic">“{e.text}”</span><span className="block text-xs text-ink-subtle">{e.citation}</span></li>)}
        </ul>
      </div>
    );
    if (s === 2) return (
      <div className="flex flex-col gap-4">
        <span className="eyebrow text-ink-subtle">Corrected: {c.after.faithful} (saffron) vs {c.after.modern} (outline)</span>
        <div className="flex flex-wrap gap-2"><PrepTag prep={correctedPrep} /></div>
        {after ? <FigureBars f={after} /> : <UnknownValue label="Profile not available" />}
        {heat && <span className="text-sm text-ink-muted">Boiling: <HeuristicMarker heuristic={heat}>heat effect</HeuristicMarker></span>}
      </div>
    );
    return (
      <div className="flex flex-col gap-4">
        <span className="eyebrow text-ink-subtle">{withheldFromPlanner ? 'Withheld from the Lab Planner (toxicity reported)' : 'Lead'}</span>
        <span className="font-display text-2xl text-ink"><Taxon name={taxon} /> · {c.indication.label}</span>
        <LikelihoodBar range={{ low: c.before.gap.low, high: c.before.gap.high, point: c.before.gap.value }} family="neutral" label="Before the correction" measure="Predicted profile gap (1 − cosine similarity)" />
        <span className="text-xs text-ink-subtle">Before: {c.before.faithful} vs {c.before.modern} · rank {c.before.rank} of {c.before.rankedOf}</span>
        <LikelihoodBar range={{ low: c.after.gap.low, high: c.after.gap.high, point: c.after.gap.value }} family="neutral" label="After the correction" measure="Predicted profile gap (1 − cosine similarity)" />
        <span className="text-xs text-ink-subtle">After: {c.after.faithful} vs {c.after.modern} · rank {c.after.rank} of {c.after.rankedOf}</span>
        <div className="flex flex-wrap gap-2">{h && <EvidenceStatusBadge status={h.evidence} size="sm" />}<ToxicityBadge record={toxicity} /></div>
        {h && <ul className="m-0 flex flex-col gap-1 pl-5 text-sm text-ink-muted">{h.caveats.map((x) => <li key={x}>{x}</li>)}</ul>}
      </div>
    );
  }

  return (
    <SiteShell current="case" bleed>
      <header className="border-b border-border bg-surface">
        <div className="mx-auto grid max-w-content grid-cols-1 items-end gap-8 px-4 py-12 md:px-8 lg:grid-cols-12">
          <div className="flex flex-col gap-4 lg:col-span-8">
            <span className="eyebrow text-brand">Case study · an extraction correction</span>
            <h1 className="m-0 font-display text-4xl text-ink md:text-5xl">Liquorice, read as a <i className="text-brand">recipe</i></h1>
            <p className="m-0 max-w-prose text-lg text-ink-muted">{c.title}: one root, followed from a historical passage to a hypothesis a lab could test.</p>
            <div className="flex flex-wrap items-center gap-2"><ExtractionDetectionExplainer /><ToxicityBadge record={toxicity} /></div>
          </div>
          <div className="lg:col-span-4"><PlateSlot taxon={taxon} plate={plate} size="card" /></div>
        </div>
      </header>

      <div className="mx-auto grid max-w-content grid-cols-1 gap-10 px-4 py-12 md:px-8 lg:grid-cols-12">
        <ol className="m-0 flex list-none flex-col gap-10 p-0 lg:col-span-6 lg:gap-0">
          {CHAPTERS.map((ch, i) => (
            <li key={ch.n}>
              <section ref={(el) => { refs.current[i] = el; }} data-step={i} aria-labelledby={`ch-${i}`} className="flex flex-col gap-4 lg:min-h-[70vh] lg:justify-center">
                <span className="font-display text-3xl text-hist-fg" aria-hidden>{ch.n}.</span>
                <h2 id={`ch-${i}`} className="m-0 font-display text-3xl text-ink">{ch.title}</h2>
                <p className="m-0 max-w-prose break-words text-md text-ink-muted">{ch.body}</p>
                <div className="rounded-lg border border-border bg-surface p-5 shadow-1 lg:hidden"><Figure s={i as Step} /></div>
              </section>
            </li>
          ))}
        </ol>
        <aside aria-label="Figure for the current chapter" className="hidden lg:col-span-6 lg:block">
          <div className="sticky top-28 flex flex-col gap-3">
            <span className="font-mono text-xs text-ink-subtle">Chapter {CHAPTERS[step].n} of IV</span>
            <div key={step} className="fade-in rounded-xl border border-border bg-surface p-6 shadow-2"><Figure s={step} /></div>
          </div>
        </aside>
      </div>

      <section aria-labelledby="record" className="border-t border-border">
        <div className="mx-auto flex max-w-content flex-col gap-4 px-4 py-12 md:px-8">
          <h2 id="record" className="m-0 font-display text-2xl text-ink">The record</h2>
          <ChartTable
            label="Before and after the correction (table)"
            caption={`${taxon}, ${c.indication.label}: Phase 6 ranking before and after the logged correction`}
            headers={['', 'Faithful preparation', 'Modern', 'Rank', 'Gap (5th–95th, median)']}
            rows={[['Before', c.before.faithful, c.before.modern, `${c.before.rank} of ${c.before.rankedOf}`, fmtGap(c.before.gap)],
                   ['After', c.after.faithful, c.after.modern, `${c.after.rank} of ${c.after.rankedOf}`, fmtGap(c.after.gap)]]}
          />
          <ChartTable
            label={`The ${corrections.length} logged corrections (table)`}
            caption="Field corrections, as logged in config/m1_corrections.csv"
            headers={['Recipe', 'Field', 'From', 'To', 'Requested by']}
            rows={corrections.map((x) => [<Link key={x.recipeId} href={x.href} className="font-mono text-xs underline">{x.recipeId}</Link>, x.field, x.from, x.to, x.requestedBy])}
          />
          <ToxicityNotice record={toxicity} />
          <div className="flex flex-wrap gap-3">
            {recipeHref && <LinkButton href={recipeHref}>Read the recipe</LinkButton>}
            <LinkButton href="/docs/#findings">How the ranking is made</LinkButton>
          </div>
          <p className="m-0 text-sm text-ink-subtle"><Taxon name={taxon} />: this page analyses a historical recipe and an extraction correction. It does not suggest preparing or taking liquorice.</p>
        </div>
      </section>
    </SiteShell>
  );
}
