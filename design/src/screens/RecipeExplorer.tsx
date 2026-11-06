import { useMemo, useState } from 'react';
import type { Recipe } from '../types';
import {
  AppShell, Button, DisputedName, EmptyState, EvidenceStatusBadge, FilterGroup, FilterSummary, PrepTag,
  SearchField, SourceConfidenceMarker, ToxicityBadge, VEHICLE_LABEL, HEAT_LABEL, SOURCE_LABEL, cx,
} from '../index';
import { sourceCulpeper, sourcePliny } from '../gallery/mock';
import { RECIPES } from './mock';

/**
 * RECIPE EXPLORER — search + five facets (plant, source, solvent, heat,
 * filtration). Every facet has an Unknown option with a count, so a filter
 * can never silently drop "not stated" recipes. Results are a list, not a
 * table, so a row reflows to a stacked card at 390px.
 */
type Facet = 'plant' | 'source' | 'solvent' | 'heat' | 'filtration';
const facetValue: Record<Facet, (r: Recipe) => string> = {
  plant: (r) => (r.name.state === 'resolved' || r.name.state === 'genus_only' ? r.name.candidates[0]?.taxon ?? 'unknown' : r.name.state === 'disputed' ? 'disputed' : 'unknown'),
  source: (r) => r.source,
  solvent: (r) => r.preparation.vehicle,
  heat: (r) => r.preparation.heat ?? 'unknown',
  filtration: (r) => (r.preparation.filtered == null ? 'unknown' : r.preparation.filtered ? 'filtered' : 'unfiltered'),
};
const facetLabel = (f: Facet, v: string): string => {
  if (v === 'unknown') return f === 'filtration' || f === 'heat' ? 'Not stated' : 'Unknown';
  if (f === 'source') return SOURCE_LABEL[v as keyof typeof SOURCE_LABEL].short;
  if (f === 'solvent') return VEHICLE_LABEL[v as keyof typeof VEHICLE_LABEL];
  if (f === 'heat') return HEAT_LABEL[v as keyof typeof HEAT_LABEL];
  if (f === 'plant' && v === 'disputed') return 'Disputed name';
  if (f === 'filtration') return v === 'filtered' ? 'Filtered' : 'Unfiltered';
  return v;
};
const LEGEND: Record<Facet, string> = { plant: 'Plant', source: 'Source', solvent: 'Solvent', heat: 'Heat', filtration: 'Filtration' };
const FACETS: Facet[] = ['plant', 'source', 'solvent', 'heat', 'filtration'];
const empty = (): Record<Facet, string[]> => ({ plant: [], source: [], solvent: [], heat: [], filtration: [] });

export function RecipeExplorer({ onOpen, onNavigate, recipes = RECIPES }: { onOpen?: (id: string) => void; onNavigate?: (p: string) => void; recipes?: Recipe[] }) {
  const [q, setQ] = useState('');
  const [sel, setSel] = useState(empty);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const matchesQuery = (r: Recipe) => {
    if (!q.trim()) return true;
    const hay = [r.name.historicalName, ...r.name.candidates.map((c) => c.taxon), r.passage.text].join(' ').toLowerCase();
    return hay.includes(q.trim().toLowerCase());
  };
  const matchesFacets = (r: Recipe, except?: Facet) =>
    FACETS.every((f) => f === except || sel[f].length === 0 || sel[f].includes(facetValue[f](r)));

  const shown = recipes.filter((r) => matchesQuery(r) && matchesFacets(r));

  // Counts reflect the other active filters (standard faceted search).
  const options = useMemo(() => {
    const out = {} as Record<Facet, { value: string; label: string; count: number }[]>;
    for (const f of FACETS) {
      const counts = new Map<string, number>();
      for (const r of recipes) counts.set(facetValue[f](r), 0);
      counts.set('unknown', counts.get('unknown') ?? 0);
      for (const r of recipes) if (matchesQuery(r) && matchesFacets(r, f)) counts.set(facetValue[f](r), (counts.get(facetValue[f](r)) ?? 0) + 1);
      out[f] = [...counts.entries()]
        .sort(([a], [b]) => (a === 'unknown' ? 1 : b === 'unknown' ? -1 : a.localeCompare(b)))
        .map(([value, count]) => ({ value, label: facetLabel(f, value), count }));
    }
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recipes, q, sel]);

  const activeCount = FACETS.reduce((n, f) => n + sel[f].length, 0);

  return (
    <AppShell current="recipes" onNavigate={onNavigate}>
      <div className="flex flex-col gap-4">
        <SearchField label="Search plants, names and passages" value={q} onChange={setQ} hint="Historical spellings are matched: try “wormwood” or “absinthium”." />
        <div className="md:hidden">
          <Button aria-expanded={filtersOpen} aria-controls="recipe-filters" onClick={() => setFiltersOpen((o) => !o)}>
            Filters{activeCount > 0 ? ` (${activeCount})` : ''}
          </Button>
        </div>
        <div id="recipe-filters" className={cx('flex-col gap-4 rounded border border-border bg-surface p-4 md:flex', filtersOpen ? 'flex' : 'hidden')}>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {FACETS.map((f) => (
              <FilterGroup key={f} legend={LEGEND[f]} options={options[f]} selected={sel[f]} onChange={(next) => setSel((s) => ({ ...s, [f]: next }))} />
            ))}
          </div>
        </div>
        <FilterSummary shown={shown.length} total={recipes.length} onClear={() => { setSel(empty()); setQ(''); }} />
      </div>

      {shown.length === 0 ? (
        <EmptyState
          title="No recipes match"
          body="Try removing a filter. Recipes whose preparation is not stated are kept under each facet’s “Not stated” option."
          action={<Button size="sm" onClick={() => setSel(empty())}>Clear filters</Button>}
        />
      ) : (
        <ul className="m-0 flex list-none flex-col gap-3 p-0" aria-label="Recipes">
          {shown.map((r) => (
            <li key={r.id}>
              <article className="flex flex-col gap-3 rounded border border-border bg-surface p-4 md:p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <h2 className="m-0 text-base font-normal">
                    <a
                      href={`/recipes/${r.id}`}
                      onClick={onOpen ? (e) => { e.preventDefault(); onOpen(r.id); } : undefined}
                      className="text-ink no-underline hover:underline"
                    >
                      <DisputedName resolution={r.name} layout="inline" />
                    </a>
                  </h2>
                  <SourceConfidenceMarker confidence={r.source === 'pliny_nh' ? sourcePliny : sourceCulpeper} compact />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <PrepTag prep={r.preparation} />
                  {r.preparation.heat === undefined || r.preparation.heat === null ? null : (
                    <span className="text-sm text-ink-muted">{HEAT_LABEL[r.preparation.heat]}</span>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <EvidenceStatusBadge status={r.evidence} size="sm" />
                  <ToxicityBadge record={r.toxicity} withSources={false} />
                </div>
              </article>
            </li>
          ))}
        </ul>
      )}
    </AppShell>
  );
}
