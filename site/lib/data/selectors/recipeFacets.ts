/**
 * Recipe explorer search and facets (moved here from the design's RecipeExplorer so the page can precompute its first
 * screen and the logic is unit-tested). Every facet keeps an Unknown option with a count, so a filter never silently
 * drops "not stated" recipes.
 */
import type { RecipeSummary } from '../../types';
import { HEAT_LABEL, SOURCE_LABEL, vehicleLabel } from '../format';

/** Recipes per page in the explorer (631 real recipes), shared by the static first screen and the client list. */
export const RECIPE_PAGE = 40;

export type Facet = 'plant' | 'source' | 'solvent' | 'heat' | 'filtration';
export type Selection = Record<Facet, string[]>;
export interface FacetOption { value: string; label: string; count: number }

export const FACETS: Facet[] = ['plant', 'source', 'solvent', 'heat', 'filtration'];
export const FACET_LEGEND: Record<Facet, string> = { plant: 'Plant', source: 'Source', solvent: 'Solvent', heat: 'Heat', filtration: 'Filtration' };
export const emptySelection = (): Selection => ({ plant: [], source: [], solvent: [], heat: [], filtration: [] });

export const facetValue: Record<Facet, (r: RecipeSummary) => string> = {
  plant: (r) => (r.name.state === 'resolved' || r.name.state === 'genus_only' ? r.name.candidates[0]?.taxon ?? 'unknown' : r.name.state === 'disputed' ? 'disputed' : 'unknown'),
  source: (r) => r.source,
  solvent: (r) => r.preparation.vehicle,
  heat: (r) => r.preparation.heat ?? 'unknown',
  filtration: (r) => (r.preparation.filtered == null ? 'unknown' : r.preparation.filtered === 'not_applicable' ? 'not_applicable' : r.preparation.filtered ? 'filtered' : 'unfiltered'),
};

export const facetLabel = (f: Facet, v: string): string => {
  if (v === 'unknown') return f === 'filtration' || f === 'heat' ? 'Not stated' : 'Unknown';
  if (f === 'source') return SOURCE_LABEL[v as keyof typeof SOURCE_LABEL].short;
  if (f === 'solvent') return vehicleLabel(v);
  if (f === 'heat') return HEAT_LABEL[v as keyof typeof HEAT_LABEL];
  if (f === 'plant' && v === 'disputed') return 'Disputed name';
  if (f === 'filtration') return v === 'filtered' ? 'Filtered' : v === 'not_applicable' ? 'Not applicable' : 'Unfiltered';
  return v;
};

export const matchesQuery = (r: RecipeSummary, q: string) => !q.trim() || r.search.includes(q.trim().toLowerCase());
export const matchesFacets = (r: RecipeSummary, sel: Selection, except?: Facet) =>
  FACETS.every((f) => f === except || sel[f].length === 0 || sel[f].includes(facetValue[f](r)));
export const filterRecipes = (rs: RecipeSummary[], q: string, sel: Selection) => rs.filter((r) => matchesQuery(r, q) && matchesFacets(r, sel));

/** Counts reflect the other active filters (standard faceted search). Unknown is always listed, last. */
export function facetOptions(rs: RecipeSummary[], q: string, sel: Selection): Record<Facet, FacetOption[]> {
  const out = {} as Record<Facet, FacetOption[]>;
  for (const f of FACETS) {
    const counts = new Map<string, number>();
    for (const r of rs) counts.set(facetValue[f](r), 0);
    counts.set('unknown', counts.get('unknown') ?? 0);
    for (const r of rs) if (matchesQuery(r, q) && matchesFacets(r, sel, f)) counts.set(facetValue[f](r), (counts.get(facetValue[f](r)) ?? 0) + 1);
    out[f] = [...counts.entries()]
      .sort(([a, ca], [b, cb]) => (a === 'unknown' ? 1 : b === 'unknown' ? -1 : f === 'plant' ? cb - ca || a.localeCompare(b) : a.localeCompare(b)))
      .map(([value, count]) => ({ value, label: facetLabel(f, value), count }));
  }
  return out;
}
