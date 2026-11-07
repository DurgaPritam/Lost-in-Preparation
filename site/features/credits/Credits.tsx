'use client';

import type { ContractPlate } from '@/lib/data/load';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { DataTable } from '@/components/base/DataTable';
import { PlateSlot } from '@/components/base/PlateSlot';
import { Taxon } from '@/components/base/Taxon';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';
import { toPlate } from '@/lib/data/selectors/plates';

/**
 * CREDITS (SITE addition, built from the design's components): the botanical plates with source, author, date and
 * licence as recorded from Wikimedia Commons (site-data/plates.json, also docs/IMAGE_CREDITS.md), the fonts and the
 * ported code.
 */
const FONTS = [
  ['Fraunces', 'Herbarium display'], ['Instrument Sans', 'Herbarium text'], ['JetBrains Mono', 'Herbarium numbers'],
  ['Instrument Serif', 'Nocturne display'], ['Hanken Grotesk', 'Nocturne text'], ['DM Mono', 'Nocturne numbers'],
] as const;

export function Credits({ plates }: { plates: ContractPlate[] }) {
  const sourced = plates.filter((p) => p.image);
  const none = plates.filter((p) => !p.image);
  return (
    <SiteShell current="credits">
      <PageHeader eyebrow="Credits" title="Images, type and code" lead="Every botanical plate is an 18th- or 19th-century plate whose Wikimedia Commons page states a public-domain licence, downloaded once and served from this site. Author, date and licence are as Commons states them. An AI agent has read each page (provisional); each licence still awaits a person’s confirmation." />
      <section aria-labelledby="plates" className="flex flex-col gap-4">
        <h2 id="plates" className="m-0 font-display text-2xl text-ink">Botanical plates</h2>
        <DataTable
          caption={`Botanical plates (${sourced.length} sourced)`}
          rows={sourced}
          rowKey={(p) => p.speciesId}
          columns={[
            { key: 'plate', header: 'Plate', render: (p) => <PlateSlot plate={toPlate(p)} taxon={p.taxon} size="thumb" /> },
            { key: 'taxon', header: 'Plant', render: (p) => <span className="flex flex-col gap-0.5"><Taxon name={p.taxon} />{p.matchedName && p.matchedName !== p.taxon && <span className="text-xs text-ink-subtle">titled <i>{p.matchedName}</i></span>}</span>, sortValue: (p) => p.taxon },
            { key: 'work', header: 'Plate series', render: (p) => p.work ?? <UnknownValue variant="cell" label="Not recorded" /> },
            { key: 'author', header: 'Author (as on Commons)', render: (p) => p.author ?? <UnknownValue variant="cell" label="Not stated" /> },
            { key: 'date', header: 'Date field on Commons', render: (p) => p.date ?? <UnknownValue variant="cell" label="Not stated" /> },
            { key: 'licence', header: 'Licence (as on Commons)', render: (p) => <span className="flex flex-col gap-0.5"><span>{p.licence}</span><span className="text-xs italic text-ink-subtle">licence to confirm</span></span> },
            { key: 'aicheck', header: 'AI check of the Commons page', render: (p) => (p.aiCheck ? (
              <span className="flex flex-col gap-1">
                <span><EvidenceStatusBadge wording="validation" status="provisional" size="sm" detail={p.aiCheck.statement} /></span>
                <span className="font-mono text-xs">{p.aiCheck.licenceTemplates.length ? p.aiCheck.licenceTemplates.map((t) => `{{${t}}}`).join(', ') : 'no licence template found'}</span>
                <span className="text-xs text-ink-subtle">{p.aiCheck.statement}</span>
                {p.aiCheck.flags.map((f) => <span key={f} className="text-xs text-ink-muted">⚑ {f}</span>)}
              </span>
            ) : <UnknownValue variant="cell" label="Not checked" />) },
            { key: 'file', header: 'Commons file', render: (p) => (p.fileUrl ? <a href={p.fileUrl} className="break-all text-brand underline">{decodeURIComponent(p.fileUrl.split('/').pop() ?? '')}</a> : <UnknownValue variant="cell" />) },
          ]}
        />
        {none.length > 0 && (
          <p className="m-0 max-w-prose text-sm text-ink-muted">No plate was found for {none.map((p, i) => <span key={p.speciesId}>{i > 0 && (i === none.length - 1 ? ' and ' : ', ')}<Taxon name={p.taxon} /></span>)} in the three series searched (Köhler 1883–1898, Thomé 1885, Sturm 1796–1855); they show the drawn placeholder instead of a doubtful image.</p>
        )}
      </section>
      <section aria-labelledby="type" className="flex flex-col gap-3">
        <h2 id="type" className="m-0 font-display text-2xl text-ink">Typefaces</h2>
        <ul className="m-0 flex list-none flex-col gap-1 p-0 text-sm">
          {FONTS.map(([f, use]) => <li key={f}><span className="font-semibold">{f}</span> · {use} · SIL Open Font License 1.1 (licence file in <code className="font-mono text-xs">/fonts/</code>)</li>)}
        </ul>
      </section>
      <section aria-labelledby="code" className="flex flex-col gap-3">
        <h2 id="code" className="m-0 font-display text-2xl text-ink">Code</h2>
        <p className="m-0 max-w-prose text-sm text-ink-muted">The in-browser preparation engine includes a port of NumPy 2.4.6’s random-number generator and its ziggurat tables (BSD-3-Clause, NumPy Developers). The site’s own code is MIT; its derived data are CC BY 4.0 with the exceptions in LICENSE-DATA.</p>
      </section>
    </SiteShell>
  );
}
