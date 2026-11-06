import Link from '@/components/base/Link';
import type { Coverage, SourceConfidence, SourceWork } from '@/lib/types';
import { AppShell } from '@/components/layout/AppShell';
import { Card } from '@/components/base/Card';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { ExtractionDetectionExplainer } from '@/components/honesty/ExtractionDetectionExplainer';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ReportingGap, type ReportingGapProps } from './ReportingGap';

/**
 * HOME — motivation, then three ways in.
 * The artemisinin story is framed explicitly as motivation, not proof: the
 * caveat sits inside the story block, not in a footnote. Panels are a numbered
 * ordered list so the sequence reads the same to a screen reader.
 */
const STORY = [
  {
    n: '1',
    head: 'The plant was right',
    body: 'In the 4th century CE, Ge Hong’s Handbook of Prescriptions for Emergencies listed qinghao (Artemisia annua) for intermittent fevers.',
  },
  {
    n: '2',
    head: 'The preparation was wrong',
    body: 'When Tu Youyou’s team screened qinghao in the late 1960s and 1970s, their extracts gave inconsistent results. Their standard hot extraction appeared to destroy the activity.',
  },
  {
    n: '3',
    head: 'Reading the recipe again',
    body: 'Ge Hong described soaking the herb in water and wringing out the juice, with no heating. A low-temperature ether extraction recovered the activity and led to the isolation of artemisinin.',
  },
];

const ENTRIES = [
  { href: '/recipes/', title: 'Recipe explorer', body: 'Read what Culpeper and Pliny prescribed, with every extracted field marked in the original passage.' },
  { href: '/compare/', title: 'Compare preparations', body: 'Put a historical preparation beside a modern extract, compound by compound, with ranges.' },
  { href: '/hypotheses/', title: 'Hypotheses', body: 'The plant–use pairs no retrieved study prepared the way the recipe did, ranked, with every caveat.' },
];

export function Home({ coverage, confidences, gap }: { coverage: Coverage; confidences: Record<SourceWork, SourceConfidence>; gap: ReportingGapProps }) {
  const COVERAGE = coverage.nameResolutions;
  return (
    <AppShell current="home" title="Historical recipes, re-read for how they were prepared">
      <section aria-labelledby="story" className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <span className="small-caps text-xs text-ink-subtle">Why preparation matters · motivation, not proof</span>
          <h2 id="story" className="m-0 font-serif text-2xl font-medium">One plant, two preparations</h2>
        </div>
        <ol className="m-0 grid list-none grid-cols-1 gap-4 p-0 md:grid-cols-3">
          {STORY.map((p) => (
            <li key={p.n} className="flex flex-col gap-2 rounded border border-border bg-surface p-5">
              <span className="font-mono text-sm text-ink-subtle">{p.n} / 3</span>
              <h3 className="m-0 font-serif text-xl font-medium text-ink">{p.head}</h3>
              <p className="m-0 text-base text-ink-muted">{p.body}</p>
            </li>
          ))}
        </ol>
        <div className="flex flex-col gap-2 border-t border-border pt-3">
          <p className="m-0 max-w-prose text-base text-ink">
            This is one celebrated case. It shows that preparation can decide what a recipe delivers. It does not show that other historical
            recipes hide overlooked preparations. Testing that, recipe by recipe, with its uncertainty shown, is what this tool is for.
          </p>
          <p className="m-0 text-xs text-ink-subtle">
            Account based on Tu Y. (2011), “The discovery of artemisinin (qinghaosu) and gifts from Chinese medicine”, Nature Medicine 17, 1217–1220.
          </p>
        </div>
      </section>

      {/* SITE: the headline reporting gap, after the artemisinin panels (new section; design tokens and components only). */}
      <ReportingGap {...gap} />

      <section aria-labelledby="start" className="flex flex-col gap-4">
        <h2 id="start" className="m-0 font-serif text-2xl font-medium">Start here</h2>
        <ul className="m-0 grid list-none grid-cols-1 gap-4 p-0 md:grid-cols-3">
          {ENTRIES.map((e) => (
            <li key={e.href} className="flex">
              <Link
                href={e.href}
                className="flex w-full flex-col gap-2 rounded border border-border-strong bg-surface p-5 no-underline transition-shadow duration-fast ease-standard hover:shadow-1"
              >
                <span className="text-lg font-semibold text-ink">{e.title} →</span>
                <span className="text-base text-ink-muted">{e.body}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="trust" className="flex flex-col gap-4">
        <h2 id="trust" className="m-0 font-serif text-2xl font-medium">Before you read any number</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card as="div" title="What has been checked" eyebrow={`Name resolutions · ${COVERAGE.validated + COVERAGE.provisional + COVERAGE.pending} names in the recipes`}>
            <ul className="m-0 flex list-none flex-col gap-2 p-0">
              <li className="flex items-center justify-between gap-3"><EvidenceStatusBadge status="validated" /><span className="num font-mono">{COVERAGE.validated}</span></li>
              <li className="flex items-center justify-between gap-3"><EvidenceStatusBadge status="provisional" /><span className="num font-mono">{COVERAGE.provisional}</span></li>
              <li className="flex items-center justify-between gap-3"><EvidenceStatusBadge status="pending" /><span className="num font-mono">{COVERAGE.pending}</span></li>
            </ul>
          </Card>
          <Card as="div" title="Sources are not equally reliable" eyebrow="Source confidence">
            <div className="flex flex-col items-start gap-2">
              <SourceConfidenceMarker confidence={confidences.culpeper_1652} />
              <SourceConfidenceMarker confidence={confidences.culpeper_1850} />
              <SourceConfidenceMarker confidence={confidences.pliny_nh} />
            </div>
          </Card>
        </div>
        <ExtractionDetectionExplainer variant="panel" />
      </section>
    </AppShell>
  );
}
