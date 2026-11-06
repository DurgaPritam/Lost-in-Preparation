import { useEffect, useState, type ReactNode } from 'react';
import {
  Button, Card, DataTable, DisputedName, Drawer, EmptyState, ErrorState, EvidenceStatusBadge,
  ExtractionDetectionExplainer, FilterGroup, FilterSummary, HeuristicMarker, LikelihoodBar, LoadingState,
  PrepLegend, PrepTag, SearchField, SourceConfidenceMarker, SourcePassage, Tabs, ToxicityBadge, ToxicityNotice,
  Tooltip, UnknownValue,
} from '../index';
import { ROUTES } from '../ia';
import { rangeText } from '../lib/format';
import * as M from './mock';

/**
 * Component gallery. Every component in every state, light and dark, using
 * mock data only. This page is the visual contract for the build agent.
 */

function Section({ id, title, lead, children }: { id: string; title: string; lead?: string; children: ReactNode }) {
  return (
    <section aria-labelledby={id} className="flex flex-col gap-4 border-t border-border pt-8">
      <div className="flex flex-col gap-1">
        <h2 id={id} className="m-0 font-serif text-2xl font-medium text-ink">{title}</h2>
        {lead && <p className="m-0 max-w-prose text-base text-ink-muted">{lead}</p>}
      </div>
      {children}
    </section>
  );
}
function Spec({ name, children }: { name: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="font-mono text-xs text-ink-subtle">{name}</span>
      <div className="flex flex-wrap items-start gap-3">{children}</div>
    </div>
  );
}

const SWATCHES: Array<[string, string]> = [
  ['paper', 'bg-paper'], ['surface', 'bg-surface'], ['sunken', 'bg-sunken'], ['raised', 'bg-raised'],
  ['ink', 'bg-ink'], ['ink-muted', 'bg-ink-muted'], ['ink-subtle', 'bg-ink-subtle'], ['border-strong', 'bg-border-strong'],
  ['hist-fg', 'bg-hist-fg'], ['hist-solid', 'bg-hist-solid'], ['hist-bg', 'bg-hist-bg'],
  ['mod-fg', 'bg-mod-fg'], ['mod-solid', 'bg-mod-solid'], ['mod-bg', 'bg-mod-bg'],
  ['unk-fg', 'bg-unk-fg'], ['unk-bg', 'bg-unk-bg'], ['unknown hatch', 'bg-hatch-unknown'],
  ['prov-fg', 'bg-prov-fg'], ['prov-bg', 'bg-prov-bg'],
  ['tox-solid', 'bg-tox-solid'], ['tox-fg', 'bg-tox-fg'], ['tox-bg', 'bg-tox-bg'], ['focus', 'bg-focus'],
];
const TYPE: Array<[string, string, string]> = [
  ['3xl / serif', 'font-serif text-3xl', 'Recipe explorer'],
  ['2xl / serif', 'font-serif text-2xl', 'Wormwood in wine'],
  ['xl / serif italic', 'font-serif text-xl italic', '“absinthium”'],
  ['md / serif (passages)', 'font-serif text-md', 'MOCK PASSAGE — transcribed recipe text appears here, in the source’s spelling.'],
  ['lg / sans semibold', 'text-lg font-semibold', 'Predicted extraction by vehicle'],
  ['base / sans (UI, data)', 'text-base', 'Filtered decoction, 2 modern studies'],
  ['sm / sans', 'text-sm', 'Provisional · AI reference, not human-checked'],
  ['xs / small caps', 'text-xs small-caps text-ink-subtle', 'As written in source'],
  ['sm / mono (ranges)', 'font-mono text-sm', '0.33–0.66 (point 0.50)'],
];

export default function Gallery() {
  // Phase 4: start from the theme already in force (?theme=…, or the system
  // preference) instead of always forcing light.
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const set = document.documentElement.dataset.theme;
    if (set === 'dark' || set === 'light') return set;
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });
  const [tab, setTab] = useState('all');
  const [vehicles, setVehicles] = useState<string[]>([]);
  const [q, setQ] = useState('');
  const [drawer, setDrawer] = useState(false);

  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto flex max-w-content flex-col gap-10 px-4 py-10 md:px-8">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-col gap-1">
            <span className="small-caps text-xs text-ink-subtle">Design system · Phase 1</span>
            <h1 className="m-0 font-serif text-3xl font-medium">Lost in Preparation — component gallery</h1>
            <p className="m-0 text-sm text-ink-muted">{M.MOCK_NOTE}</p>
          </div>
          <Button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-pressed={theme === 'dark'}>
            {theme === 'light' ? 'Dark theme' : 'Light theme'}
          </Button>
        </header>

        <Section id="f-colour" title="Colour" lead="Semantic roles only. Historical is warm and lighter; modern is cool and darker; unknown is neutral and hatched. Toxicity red appears nowhere else.">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
            {SWATCHES.map(([n, c]) => (
              <div key={n} className="flex flex-col gap-1">
                <span className={`h-12 rounded border border-border ${c}`} />
                <span className="font-mono text-xs text-ink-muted">{n}</span>
              </div>
            ))}
          </div>
          <PrepLegend />
        </Section>

        <Section id="f-type" title="Type" lead="EB Garamond for the historical voice (passages, names as written, page titles). IBM Plex Sans for everything the tool computes. Plex Mono for numbers in ranges.">
          <div className="flex flex-col gap-3">
            {TYPE.map(([n, c, s]) => (
              <div key={n} className="grid grid-cols-1 items-baseline gap-2 md:grid-cols-4">
                <span className="font-mono text-xs text-ink-subtle">{n}</span>
                <span className={`md:col-span-3 ${c}`}>{s}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section id="f-space" title="Space, radius, elevation">
          <div className="flex flex-wrap items-end gap-3">
            {['w-1', 'w-2', 'w-3', 'w-4', 'w-6', 'w-8', 'w-12', 'w-16'].map((w) => (
              <div key={w} className="flex flex-col items-start gap-1">
                <span className={`h-4 bg-ink-muted ${w}`} />
                <span className="font-mono text-xs text-ink-subtle">{w.replace('w-', '')}</span>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-4">
            {['rounded-sm', 'rounded', 'rounded-md', 'rounded-full'].map((r) => (
              <span key={r} className={`flex h-12 w-24 items-center justify-center border border-border-strong bg-surface font-mono text-xs ${r}`}>{r}</span>
            ))}
            {['shadow-none', 'shadow-1', 'shadow-2', 'shadow-3'].map((s) => (
              <span key={s} className={`flex h-12 w-24 items-center justify-center rounded border border-border bg-surface font-mono text-xs ${s}`}>{s}</span>
            ))}
          </div>
        </Section>

        <Section id="h1" title="1 · Evidence status" lead="Shape, border style and word carry the meaning; colour is redundant. Focus or hover for the explanation.">
          <Spec name="EvidenceStatusBadge">
            <EvidenceStatusBadge status="validated" detail="Reviewer: [MOCK]" />
            <EvidenceStatusBadge status="provisional" />
            <EvidenceStatusBadge status="pending" />
            <EvidenceStatusBadge status="provisional" size="sm" />
          </Spec>
        </Section>

        <Section id="h2" title="2 · Source confidence" lead="One marker per source, never averaged. Pliny is shown lower (dashed, one pip) with its disputed share.">
          <Spec name="SourceConfidenceMarker">
            <SourceConfidenceMarker confidence={M.sourceCulpeper} />
            <SourceConfidenceMarker confidence={M.sourcePliny} />
            <SourceConfidenceMarker confidence={M.sourcePliny} compact />
            <SourceConfidenceMarker confidence={M.sourceUnknown} />
          </Spec>
        </Section>

        <Section id="h3" title="3 · Disputed names" lead="The source’s word leads. Every candidate is listed at equal weight with its own range and status.">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card as="div"><DisputedName resolution={M.nameDisputed} /></Card>
            <Card as="div"><DisputedName resolution={M.nameGenus} /></Card>
            <Card as="div"><DisputedName resolution={M.nameResolved} /></Card>
            <Card as="div"><DisputedName resolution={M.nameUnresolved} /></Card>
          </div>
          <Spec name="DisputedName layout=inline">
            <DisputedName resolution={M.nameDisputed} layout="inline" />
            <DisputedName resolution={M.nameGenus} layout="inline" />
            <DisputedName resolution={M.nameUnresolved} layout="inline" />
          </Spec>
        </Section>

        <Section id="h4" title="4 · Likelihood with range" lead="The band is the value. A wide band is a finding about uncertainty, shown as prominently as a narrow one.">
          <Spec name="LikelihoodBar">
            <LikelihoodBar range={M.rangeNarrow} family="historical" label="Wine, unfiltered" showScale />
            <LikelihoodBar range={M.rangeWide} family="modern" label="Methanol extract" showScale />
            <LikelihoodBar range={M.rangeNoPoint} family="neutral" label="No point estimate" />
            <LikelihoodBar range={M.rangeUnknown} family="historical" label="Vinegar" />
          </Spec>
        </Section>

        <Section id="h5" title="5 · Extraction vs detection">
          <ExtractionDetectionExplainer variant="inline" />
          <ExtractionDetectionExplainer variant="panel" />
        </Section>

        <Section id="h6" title="6 · Heuristic marker" lead="Annotation, not category: ink only, hollow diamond, dashed underline.">
          <p className="m-0 max-w-prose text-base">
            Alkaloid extraction is raised for this preparation because the vehicle is{' '}
            <HeuristicMarker heuristic={M.heurAcidity}>acidic</HeuristicMarker>, and volatile oils are lowered because it was{' '}
            <HeuristicMarker heuristic={M.heurHeat}>boiled long</HeuristicMarker>.
          </p>
        </Section>

        <Section id="h7" title="7 · Toxicity" lead="Only “toxicity reported” is filled. “No toxicity reported” is neutral, never green, never a tick.">
          <Spec name="ToxicityBadge">
            <ToxicityBadge record={M.toxReported} />
            <ToxicityBadge record={M.toxConcern} />
            <ToxicityBadge record={M.toxNone} />
            <ToxicityBadge record={M.toxLacking} />
            <ToxicityBadge record={M.toxUnknown} />
          </Spec>
          <Spec name="ToxicityNotice (replaces any call to action)">
            <ToxicityNotice record={M.toxReported} />
            <ToxicityNotice record={M.toxConcern} />
          </Spec>
        </Section>

        <Section id="h8" title="8 · Unknown value" lead="A value, not an absence. Neutral grey, always the word, sorted last, counted in filters.">
          <Spec name="UnknownValue">
            <UnknownValue />
            <UnknownValue label="Not stated in source" reason="The recipe does not say whether it was strained." />
            <UnknownValue variant="cell" />
          </Spec>
        </Section>

        <Section id="b-controls" title="Buttons, search, filters, tabs">
          <Spec name="Button">
            <Button variant="primary">Open hypothesis</Button>
            <Button>Compare preparations</Button>
            <Button variant="ghost">Download CSV</Button>
            <Button size="sm">Small</Button>
            <Button disabled>Disabled</Button>
          </Spec>
          <div className="max-w-prose">
            <SearchField label="Search plants, names and compounds" value={q} onChange={setQ} hint="Historical spellings are matched: try “wormwood” or “absinthium”." />
          </div>
          <FilterGroup
            legend="Vehicle"
            options={[{ value: 'wine', label: 'Wine', count: 11 }, { value: 'vinegar', label: 'Vinegar', count: 22 }, { value: 'decoction', label: 'Decoction', count: 33 }, { value: 'unknown', label: 'Unknown', count: 44 }]}
            selected={vehicles}
            onChange={setVehicles}
          />
          <FilterSummary shown={vehicles.length ? 66 : 110} total={110} onClear={() => setVehicles([])} />
          <Tabs
            label="Recipe set"
            value={tab}
            onChange={setTab}
            items={[
              { id: 'all', label: 'All', count: 110, panel: <p className="m-0 text-ink-muted">All recipes (mock).</p> },
              { id: 'culpeper', label: 'Culpeper', count: 55, panel: <p className="m-0 text-ink-muted">Culpeper recipes (mock).</p> },
              { id: 'pliny', label: 'Pliny', count: 55, panel: <p className="m-0 text-ink-muted">Pliny recipes (mock).</p> },
            ]}
          />
        </Section>

        <Section id="b-table" title="Table" lead="Unknown sorts last in both directions. Click a row to open the drawer.">
          <DataTable
            caption="Mock recipes with predicted extraction (range, 0–1)"
            rows={M.rows}
            rowKey={(r) => r.id}
            onRowClick={() => setDrawer(true)}
            columns={[
              { key: 'name', header: 'Name in source', render: (r) => <DisputedName resolution={r.name} layout="inline" /> },
              { key: 'prep', header: 'Preparation', render: (r) => <PrepTag prep={r.prep} /> },
              {
                key: 'x', header: 'Predicted extraction', hint: 'range, 0–1', numeric: true,
                sortValue: (r) => (r.extraction.low == null || r.extraction.high == null ? null : (r.extraction.low + r.extraction.high) / 2),
                render: (r) => (r.extraction.low == null ? <UnknownValue variant="cell" /> : rangeText(r.extraction)),
              },
              { key: 'tox', header: 'Toxicity', render: (r) => <ToxicityBadge record={r.tox} withSources={false} /> },
            ]}
          />
        </Section>

        <Section id="b-cards" title="Cards and drawer">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card
              eyebrow="Hypothesis · mock"
              title="Wine preparation may carry compound class A that methanol studies did not test"
              interactive
              meta={<><EvidenceStatusBadge status="provisional" size="sm" /><SourceConfidenceMarker confidence={M.sourceCulpeper} compact /><ToxicityBadge record={M.toxConcern} withSources={false} /></>}
              footer={<Button size="sm" onClick={() => setDrawer(true)}>View reasoning</Button>}
            >
              <LikelihoodBar range={M.rangeNarrow} family="historical" label="Wine" width="full" />
              <LikelihoodBar range={M.rangeWide} family="modern" label="Methanol extract" width="full" />
              <ExtractionDetectionExplainer />
            </Card>
            <Card
              eyebrow="Recipe · mock"
              title={<span className="font-serif text-xl font-medium">Hemlock in oil</span>}
              meta={<><EvidenceStatusBadge status="validated" size="sm" /><ToxicityBadge record={M.toxReported} withSources={false} /></>}
            >
              <SourcePassage cite="[MOCK] Culpeper 1652, entry placeholder">MOCK PASSAGE — transcribed recipe text appears here.</SourcePassage>
              <ToxicityNotice record={M.toxReported} />
            </Card>
          </div>
          <Drawer open={drawer} onClose={() => setDrawer(false)} title="“absinthium” in wine" eyebrow="Recipe · Pliny, NH · mock"
            footer={<Button onClick={() => setDrawer(false)}>Close</Button>}>
            <div className="flex flex-col gap-5">
              <div className="flex flex-wrap gap-2"><SourceConfidenceMarker confidence={M.sourcePliny} /><EvidenceStatusBadge status="provisional" /></div>
              <DisputedName resolution={M.nameDisputed} />
              <PrepTag prep={M.prepHist} />
              <LikelihoodBar range={M.rangeWide} family="historical" label="Wine" width="full" showScale />
              <ExtractionDetectionExplainer />
              <ToxicityBadge record={M.toxNone} />
            </div>
          </Drawer>
        </Section>

        <Section id="b-states" title="Empty, loading, error, tooltip">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <EmptyState title="No recipes match these filters" body="Filters hide 110 recipes. Unknown values are included unless you exclude them." action={<Button size="sm">Clear filters</Button>} />
            <LoadingState label="Loading recipes" />
            <ErrorState title="Couldn’t load the audit table" body="The data file didn’t respond. Nothing on this page has changed." onRetry={() => {}} detail="GET /data/audit.json · 503 (mock)" />
          </div>
          <Tooltip content="Tooltips add explanation; they never hold the only copy of a fact.">
            <button type="button" className="w-max text-sm text-ink underline decoration-dotted underline-offset-4">Hover or focus me</button>
          </Tooltip>
        </Section>

        <Section id="ia" title="Information architecture" lead="Seven destinations, each answering one question.">
          <ol className="m-0 grid list-none grid-cols-1 gap-3 p-0 md:grid-cols-2">
            {ROUTES.map((r, i) => (
              <li key={r.id} className="flex flex-col gap-1 rounded border border-border bg-surface p-4">
                <span className="font-mono text-xs text-ink-subtle">{String(i + 1).padStart(2, '0')} · {r.path}</span>
                <span className="text-base font-semibold">{r.label}</span>
                <span className="text-sm text-ink-muted">{r.question}</span>
                <span className="text-xs text-ink-subtle">Honesty treatments: {r.treatments.join(', ')}</span>
              </li>
            ))}
          </ol>
        </Section>
      </div>
    </div>
  );
}
