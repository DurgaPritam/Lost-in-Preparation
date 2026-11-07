import { useState, type ReactNode } from 'react';
import {
  Button, ChartTable, DisputedName, Drawer, EmptyState, ErrorState, EvidenceStatusBadge, ExtractionDetectionExplainer, HeuristicMarker,
  LikelihoodBar, LinkButton, LoadingState, PlantCard, PlateSlot, Popover, PrepLegend, PrepTag, SearchField, SegmentedControl,
  SourceConfidenceMarker, Switch, ThemeToggle, ToxicityBadge, ToxicityNotice, UnknownValue,
} from '../index';
import { plates } from '../contract';
import {
  MOCK_NOTE, heurAcidity, heurHeat, nameDisputed, nameGenus, nameResolved, nameUnresolved, prepHist, prepHist2, prepMod,
  rangeNarrow, rangeNoPoint, rangeUnknown, rangeWide, sourceCulpeper, sourcePliny, sourceUnknown,
  toxConcern, toxLacking, toxNone, toxReported, toxUnknown,
} from './mock';

/**
 * COMPONENT GALLERY (v2) — every component in every state, in whichever
 * theme is active. Use the toggle to check Herbarium (light) and Nocturne
 * (dark). Mock values only.
 */
function Block({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <section aria-label={title} className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-1 md:p-6">
      <div className="flex flex-col gap-1">
        <h2 className="m-0 font-display text-2xl text-ink">{title}</h2>
        {note && <p className="m-0 max-w-prose text-sm text-ink-muted">{note}</p>}
      </div>
      {children}
    </section>
  );
}
const Row = ({ children }: { children: ReactNode }) => <div className="flex flex-wrap items-center gap-3">{children}</div>;

export default function Gallery() {
  const [seg, setSeg] = useState<'water' | 'wine' | 'vinegar'>('water');
  const [sw, setSw] = useState(true);
  const [q, setQ] = useState('');
  const [drawer, setDrawer] = useState(false);

  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-20 border-b border-border bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-content items-center justify-between gap-4 px-4 py-3 md:px-8">
          <span className="font-display text-xl text-ink">Lost in Preparation · component gallery</span>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto flex max-w-content flex-col gap-8 px-4 py-10 md:px-8">
        <p className="m-0 font-mono text-xs text-ink-subtle">{MOCK_NOTE}</p>

        <Block title="1 · Evidence status" note="Validated: a person checked it. Provisional: AI-assisted, not yet checked. Pending: not done yet.">
          <Row><EvidenceStatusBadge status="validated" /><EvidenceStatusBadge status="provisional" /><EvidenceStatusBadge status="pending" /></Row>
          <Row><EvidenceStatusBadge status="validated" size="sm" /><EvidenceStatusBadge status="provisional" size="sm" /><EvidenceStatusBadge status="pending" size="sm" /></Row>
        </Block>

        <Block title="2 · Source confidence" note="Culpeper and Pliny are always shown separately; Pliny is lower confidence.">
          <Row><SourceConfidenceMarker confidence={sourceCulpeper} /><SourceConfidenceMarker confidence={sourcePliny} /><SourceConfidenceMarker confidence={sourceUnknown} /></Row>
          <Row><SourceConfidenceMarker confidence={sourceCulpeper} compact /><SourceConfidenceMarker confidence={sourcePliny} compact /></Row>
        </Block>

        <Block title="3 · Disputed names" note="Never shown as settled. Candidates keep their ranges.">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <DisputedName resolution={nameResolved} />
            <DisputedName resolution={nameDisputed} />
            <DisputedName resolution={nameGenus} />
            <DisputedName resolution={nameUnresolved} />
          </div>
          <Row><DisputedName resolution={nameDisputed} layout="inline" /></Row>
        </Block>

        <Block title="4 · Ranges, never points" note="Saffron fill = historical preparation. Aubergine/lilac outline = modern lab method.">
          <PrepLegend />
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            <LikelihoodBar range={rangeNarrow} label="Narrow range" />
            <LikelihoodBar range={rangeWide} label="Wide range" />
            <LikelihoodBar range={rangeNoPoint} label="No point estimate" />
            <LikelihoodBar range={rangeUnknown} label="Unknown range" />
            <LikelihoodBar range={rangeNarrow} compare={rangeWide} label="With modern overlay" />
            <LikelihoodBar range={rangeWide} family="modern" label="Modern only" size="sm" />
          </div>
        </Block>

        <Block title="5 · Extraction vs detection">
          <Row><ExtractionDetectionExplainer /></Row>
          <ExtractionDetectionExplainer variant="panel" />
        </Block>

        <Block title="6 · Heuristic marker">
          <Row><HeuristicMarker heuristic={heurAcidity} /><HeuristicMarker heuristic={heurHeat}>heat effect</HeuristicMarker></Row>
        </Block>

        <Block title="7 · Toxicity" note="Crimson is reserved for toxicity. Toxic plants are analysis-only and never offered as something to try.">
          <Row>
            <ToxicityBadge record={toxReported} /><ToxicityBadge record={toxConcern} /><ToxicityBadge record={toxNone} />
            <ToxicityBadge record={toxLacking} /><ToxicityBadge record={toxUnknown} />
          </Row>
          <ToxicityNotice record={toxReported} />
          <ToxicityNotice record={toxConcern} />
        </Block>

        <Block title="8 · Unknown is a value">
          <Row><UnknownValue /><UnknownValue label="Not stated" variant="cell" /><UnknownValue reason="The source does not say how long." label="Not stated in source" /></Row>
        </Block>

        <Block title="Preparations">
          <Row><PrepTag prep={prepHist} /><PrepTag prep={prepHist2} /><PrepTag prep={prepMod} /><PrepTag prep={prepHist} compact /></Row>
        </Block>

        <Block title="Controls">
          <Row><Button variant="primary">Primary</Button><Button>Secondary</Button><Button variant="ghost">Ghost</Button><Button size="sm">Small</Button><LinkButton href="#/" variant="primary" size="lg">Link button</LinkButton></Row>
          <SegmentedControl label="Solvent" value={seg} onChange={setSeg} options={[{ value: 'water', label: 'Water' }, { value: 'wine', label: 'Wine' }, { value: 'vinegar', label: 'Vinegar' }]} />
          <div className="max-w-sm"><Switch label="Strained" description="Filtration through cloth" checked={sw} onChange={setSw} /></div>
          <div className="max-w-md"><SearchField label="Search recipes" value={q} onChange={setQ} placeholder="Plant, passage or field" /></div>
          <Row>
            <Popover label="About this popover" trigger="Open a popover">
              <p className="m-0 text-sm">Popovers carry the detail behind a compact badge. Escape closes and returns focus.</p>
            </Popover>
            <Button onClick={() => setDrawer(true)}>Open a drawer</Button>
          </Row>
        </Block>

        <Block title="Plates" note="Every image slot names its licence and host. Slots still to source show a drawn placeholder.">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <PlateSlot taxon="Glycyrrhiza glabra" plate={plates[0]} size="card" />
            <PlateSlot taxon="Mentha sp." plate={null} size="card" />
            <div className="flex items-start gap-4"><PlateSlot taxon="Salvia officinalis" plate={plates[2]} size="thumb" /></div>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <PlantCard name={nameResolved} common="Wormwood" plate={plates[1]} recipes={{ culpeper: 2, pliny: 0 }} toxicity={toxConcern} href="#/atlas" />
            <PlantCard name={nameDisputed} common="absinthium" plate={null} recipes={{ culpeper: 0, pliny: 1 }} toxicity={toxConcern} href="#/atlas" />
            <PlantCard name={nameGenus} common="Mint" plate={plates[4]} recipes={{ culpeper: 0, pliny: 1 }} toxicity={toxLacking} href="#/atlas" />
          </div>
        </Block>

        <Block title="States">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <LoadingState />
            <EmptyState title="No recipes match" body="Try fewer filters." />
            <ErrorState title="Could not load the profile" body="The data file did not arrive. Nothing is shown rather than a guess." onRetry={() => {}} />
          </div>
        </Block>

        <Block title="Table fallback">
          <ChartTable caption="Example ranges" headers={['Compound', 'Low', 'High']} numeric={[1, 2]} rows={[['Compound A (mock)', '0.11', '0.33'], ['Compound B (mock)', '0.44', '0.77'], ['Compound C (mock)', <UnknownValue key="u" />, <UnknownValue key="v" />]]} />
        </Block>
      </main>
      <Drawer open={drawer} onClose={() => setDrawer(false)} title="Example drawer" eyebrow="Gallery">
        <p className="m-0 text-ink-muted">Focus is trapped here; Escape closes and returns focus to the button.</p>
      </Drawer>
    </div>
  );
}
