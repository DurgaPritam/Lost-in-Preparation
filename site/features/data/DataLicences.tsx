'use client';

import type { SourceRecord, SourcesFile } from '@/lib/types';
import { AppShell } from '@/components/layout/AppShell';
import { DataTable } from '@/components/base/DataTable';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { UnknownValue } from '@/components/honesty/UnknownValue';

/**
 * DATA & LICENCES — where every record comes from, and whether it can be reused.
 * - The licence column carries its own evidence status: "provisional" means
 *   the licence is our reading and hasn't been checked by a person yet.
 * - Missing edition/year/licence render as Unknown, never blank.
 * - Downloads are the contract files themselves; their licence is Unknown
 *   until the team chooses one, and the page says so.
 */
export function DataLicences({ data, contractVersion }: { data: SourcesFile; contractVersion: string }) {
  return (
    <AppShell current="data">
      <section aria-labelledby="src" className="flex flex-col gap-4">
        <h2 id="src" className="m-0 font-serif text-2xl font-medium">Sources</h2>
        <DataTable<SourceRecord>
          caption="Texts, data and software used, with edition, year and licence"
          rows={data.sources}
          rowKey={(s) => s.id}
          columns={[
            {
              key: 't', header: 'Source', render: (s) => (
                <span className="flex flex-col gap-0.5">
                  {s.url ? <a href={s.url} className="text-ink underline underline-offset-2">{s.title}</a> : <span>{s.title}</span>}
                  {s.note && <span className="text-xs text-ink-subtle">{s.note}</span>}
                </span>
              ),
            },
            { key: 'r', header: 'Role', render: (s) => <span className="text-sm text-ink-muted">{s.role}</span> },
            { key: 'e', header: 'Edition', render: (s) => s.edition ?? <UnknownValue label="To confirm" /> },
            { key: 'y', header: 'Year', render: (s) => s.year ?? <UnknownValue /> },
            {
              key: 'l', header: 'Licence', hint: 'with check status', render: (s) => (
                <span className="flex flex-col items-start gap-1">
                  {s.licence ?? <UnknownValue label="Not yet determined" />}
                  <EvidenceStatusBadge status={s.licenceEvidence} size="sm" detail={s.licenceEvidence === 'provisional' ? 'The rights statement was checked by the pipeline, not yet by a person. The team must confirm it before publishing.' : undefined} />
                </span>
              ),
            },
          ]}
        />
      </section>

      <section aria-labelledby="dl" className="flex flex-col gap-4">
        <h2 id="dl" className="m-0 font-serif text-2xl font-medium">Downloads</h2>
        <p className="m-0 max-w-prose text-base text-ink-muted">Each file is one contract file of the pipeline (contract {contractVersion}), exactly as the site reads it and validated against its JSON Schema at build time. A licence for the derived data has not been chosen yet.</p>
        <ul className="m-0 grid list-none grid-cols-1 gap-3 p-0 md:grid-cols-2">
          {data.downloads.map((d) => (
            <li key={d.file} className="flex flex-col gap-1.5 rounded border border-border bg-surface p-4">
              <a href={`/data/${d.file}`} download className="w-max font-mono text-base text-ink underline underline-offset-2">{d.file}</a>
              <span className="text-sm text-ink-muted">{d.description}</span>
              <span className="flex flex-wrap items-center gap-3 text-xs text-ink-subtle">
                <span className="font-mono">{d.contract}</span>
                <span>{d.format.toUpperCase()}</span>
                {d.licence ?? <UnknownValue label="Licence not chosen" />}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </AppShell>
  );
}
