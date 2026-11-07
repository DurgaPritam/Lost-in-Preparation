import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from 'react';
import {
  EvidenceStatusBadge, ExtractionDetectionExplainer, HeuristicMarker, LikelihoodBar, LinkButton, PlateSlot, PrepLegend, PrepTag,
  SiteShell, SourceConfidenceMarker, Taxon, ToxicityBadge, ToxicityNotice,
} from '../index';
import { LAB_PROFILES } from '../contract/lab';
import { heuristics, hypotheses, labPlan, plates, recipes } from '../contract';
import { sourceCulpeper } from '../gallery/mock';

/**
 * CASE STUDY — liquorice as a scroll story in four chapters:
 * the misreading → the evidence → the correction → the new result.
 * Desktop: the figure is sticky and follows the active chapter (Intersection
 * Observer). Phone: each chapter carries its own figure inline. Reduced
 * motion: figures swap instantly (bar transitions are 0ms).
 *
 * THE NARRATIVE IS A [MOCK STORY] PLACEHOLDER: structure and tone are
 * final, the claims must come from the team's own liquorice analysis.
 */
const lq = LAB_PROFILES.find((p) => p.taxon === 'Glycyrrhiza glabra')!;
const decoction = lq.preparations.find((p) => p.id === 'water-boiled-f-n')!;
const modern = lq.preparations.find((p) => p.preparation.family === 'modern')!;
const recipe = recipes.find((r) => r.id === 'cul-liquorice-decoction')!;
const lead = hypotheses.find((h) => h.id === 'h-glycyrrhizin-decoction')!;
const heat = heuristics.find((h) => h.id === 'heat_sensitivity')!;
/** Planner rank (toxic-reported leads are withheld there, so it can differ from the hypothesis rank). */
const planned = labPlan.items.find((i) => i.hypothesisId === lead.id);

type Step = 0 | 1 | 2 | 3;
const CHAPTERS: { n: string; title: string; body: ReactNode }[] = [
  { n: 'I', title: 'The misreading', body: <>[MOCK STORY] Most modern work on liquorice root starts from a solvent extract chosen for the laboratory, not from the way the root was prepared in the recipes. The plant is the same; the preparation is not.</> },
  { n: 'II', title: 'The evidence', body: <>[MOCK STORY] Culpeper’s recipe is specific: the root is scraped, bruised, boiled in water until a third is gone, then strained. Each of those details is extracted from the passage and checked.</> },
  { n: 'III', title: 'The correction', body: <>[MOCK STORY] Modelled as written — a strained decoction — the predicted profile shifts towards the water-soluble compounds. The modern method, overlaid, tells a different story for the less polar ones.</> },
  { n: 'IV', title: 'The new result', body: <>[MOCK STORY] One lead survives the conservative test: the decoction’s range for glycyrrhizin sits entirely above the modern method’s. It is a hypothesis for the lab — not a finding, and not a recommendation.</> },
];

function Figure({ step }: { step: Step }) {
  if (step === 0) return (
    <div className="flex flex-col gap-4">
      <span className="eyebrow text-ink-subtle">What modern studies usually test</span>
      <PrepTag prep={modern.preparation} />
      {modern.estimates.map((e) => <div key={e.compound} className="flex flex-col gap-1"><span className="text-sm font-semibold">{e.compound}</span><LikelihoodBar range={e.likelihood} family="modern" label={`${e.compound}, ${modern.label}`} size="sm" /></div>)}
    </div>
  );
  if (step === 1) return (
    <div className="flex flex-col gap-4">
      <span className="eyebrow text-ink-subtle">The recipe, as written</span>
      <blockquote className="m-0 font-display text-xl italic text-ink">“{recipe.passage.text.replace('[MOCK] ', '')}”</blockquote>
      <span className="text-xs text-ink-subtle">[MOCK] passage · {recipe.passage.edition}</span>
      <div className="flex flex-wrap gap-2"><SourceConfidenceMarker confidence={sourceCulpeper} /><EvidenceStatusBadge status={recipe.evidence} size="sm" /></div>
      <PrepTag prep={recipe.preparation} />
    </div>
  );
  if (step === 2) return (
    <div className="flex flex-col gap-4">
      <span className="eyebrow text-ink-subtle">Decoction (saffron) vs modern method (outline)</span>
      <PrepLegend modernLabel={modern.label} />
      {decoction.estimates.map((e) => <div key={e.compound} className="flex flex-col gap-1"><span className="text-sm font-semibold">{e.compound}</span><LikelihoodBar range={e.likelihood} compare={modern.estimates.find((m) => m.compound === e.compound)?.likelihood} compareLabel={modern.label} label={e.compound} size="sm" /></div>)}
      <span className="text-sm text-ink-muted">Boiling: <HeuristicMarker heuristic={heat}>heat effect</HeuristicMarker></span>
    </div>
  );
  return (
    <div className="flex flex-col gap-4">
      <span className="eyebrow text-ink-subtle">{planned ? <>Lab Planner · rank {planned.rank} (could be {planned.rankRange[0]}–{planned.rankRange[1]})</> : 'Lead'}</span>
      <span className="font-display text-2xl text-ink">{lead.compound}</span>
      <LikelihoodBar range={lead.historicalLikelihood} compare={lead.modernLikelihood} compareLabel={lead.modern.label} label={`${lead.compound}, ${lead.faithful.label}`} />
      <div className="flex flex-wrap gap-2"><EvidenceStatusBadge status={lead.evidence} size="sm" /><ToxicityBadge record={lead.toxicity} /></div>
      <ul className="m-0 flex flex-col gap-1 pl-5 text-sm text-ink-muted">{lead.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
    </div>
  );
}

export function CaseStudy({ onNavigate }: { onNavigate?: (p: string) => void }) {
  const [step, setStep] = useState<Step>(0);
  const refs = useRef<Array<HTMLElement | null>>([]);
  const go = (path: string) => (e: MouseEvent) => { if (onNavigate) { e.preventDefault(); onNavigate(path); } };

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver((entries) => {
      const vis = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (vis) setStep(Number((vis.target as HTMLElement).dataset.step) as Step);
    }, { rootMargin: '-40% 0px -40% 0px', threshold: [0, 0.25, 0.5, 1] });
    refs.current.forEach((r) => r && io.observe(r));
    return () => io.disconnect();
  }, []);

  return (
    <SiteShell current="case" onNavigate={onNavigate} bleed>
      <header className="border-b border-border bg-surface">
        <div className="mx-auto grid max-w-content grid-cols-1 items-end gap-8 px-4 py-12 md:px-8 lg:grid-cols-12">
          <div className="flex flex-col gap-4 lg:col-span-8">
            <span className="eyebrow text-brand">Case study · [MOCK STORY]</span>
            <h1 className="m-0 font-display text-4xl text-ink md:text-5xl">Liquorice, read as a <i className="text-brand">recipe</i></h1>
            <p className="m-0 max-w-prose text-lg text-ink-muted">One root, followed from a 1652 passage to a hypothesis a lab could test.</p>
            <div className="flex flex-wrap items-center gap-2"><ExtractionDetectionExplainer /><ToxicityBadge record={lq.toxicity} /></div>
          </div>
          <div className="lg:col-span-4"><PlateSlot taxon="Glycyrrhiza glabra" plate={plates.find((p) => p.taxon === 'Glycyrrhiza glabra')} size="card" /></div>
        </div>
      </header>

      <div className="mx-auto grid max-w-content grid-cols-1 gap-10 px-4 py-12 md:px-8 lg:grid-cols-12">
        <ol className="m-0 flex list-none flex-col gap-10 p-0 lg:col-span-6 lg:gap-0">
          {CHAPTERS.map((c, i) => (
            <li key={c.n}>
              <section ref={(el) => { refs.current[i] = el; }} data-step={i} aria-labelledby={`ch-${i}`} className="flex flex-col gap-4 lg:min-h-[70vh] lg:justify-center">
                <span className="font-display text-3xl text-hist-fg" aria-hidden>{c.n}.</span>
                <h2 id={`ch-${i}`} className="m-0 font-display text-3xl text-ink">{c.title}</h2>
                <p className="m-0 max-w-prose text-md text-ink-muted">{c.body}</p>
                <div className="rounded-lg border border-border bg-surface p-5 shadow-1 lg:hidden"><Figure step={i as Step} /></div>
              </section>
            </li>
          ))}
        </ol>
        <aside aria-label="Figure for the current chapter" className="hidden lg:col-span-6 lg:block">
          <div className="sticky top-28 flex flex-col gap-3">
            <span className="font-mono text-xs text-ink-subtle">Chapter {CHAPTERS[step].n} of IV</span>
            <div key={step} className="fade-in rounded-xl border border-border bg-surface p-6 shadow-2"><Figure step={step} /></div>
          </div>
        </aside>
      </div>

      <section className="border-t border-border">
        <div className="mx-auto flex max-w-content flex-col gap-4 px-4 py-12 md:px-8">
          <ToxicityNotice record={lq.toxicity} />
          <div className="flex flex-wrap gap-3">
            <LinkButton href="/lab?plant=Glycyrrhiza%20glabra&solvent=water&heat=boiled" onClick={go('/lab?plant=Glycyrrhiza%20glabra&solvent=water&heat=boiled')} variant="primary">Try it in the Lab</LinkButton>
            <LinkButton href="/planner" onClick={go('/planner')}>See it in the Lab Planner</LinkButton>
          </div>
          <p className="m-0 text-sm text-ink-subtle"><Taxon name="Glycyrrhiza glabra" />: this page analyses a historical recipe. It does not suggest preparing or taking liquorice.</p>
        </div>
      </section>
    </SiteShell>
  );
}
