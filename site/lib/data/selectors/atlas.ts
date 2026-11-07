/** Recipe Atlas: grouping and search (pure; used by the page builder and in the browser). */
import type { NameResolution, RecipeSummary } from '../../types';

/** Recipes are grouped by the top candidate's taxon, or by the historical name when the name is disputed or unresolved
 *  (a disputed name is never filed under one species). */
export const plantKeyOf = (n: NameResolution) =>
  n.state === 'disputed' || n.state === 'unresolved' || !n.candidates[0] ? `“${n.historicalName}”` : n.candidates[0].taxon;

/** SITE: three source chips (the corpus has two Culpeper editions, never merged), plus the design's three. */
export type AtlasChip = 'culpeper_1652' | 'culpeper_1850' | 'pliny_nh' | 'disputed' | 'heat-stated' | 'strained';
export const ATLAS_CHIPS: { id: AtlasChip; label: string }[] = [
  { id: 'culpeper_1652', label: 'Culpeper 1652' }, { id: 'culpeper_1850', label: 'Culpeper 1850' }, { id: 'pliny_nh', label: 'Pliny' },
  { id: 'disputed', label: 'Disputed names' }, { id: 'heat-stated', label: 'Heat stated' }, { id: 'strained', label: 'Strained' },
];

/** Search covers the historical name, candidate taxa, the passage text and normalised field values (RecipeSummary.search),
 *  case-insensitive. Source chips combine with OR; the other chips with AND. */
export function recipeMatches(r: RecipeSummary, q: string, chips: AtlasChip[]): boolean {
  const t = q.trim().toLowerCase();
  if (t && !r.search.includes(t) && !r.name.candidates.some((c) => c.taxon.toLowerCase().includes(t))) return false;
  const sources: string[] = chips.filter((c) => c === 'culpeper_1652' || c === 'culpeper_1850' || c === 'pliny_nh');
  if (sources.length && !sources.includes(r.source)) return false;
  if (chips.includes('disputed') && r.name.state !== 'disputed') return false;
  if (chips.includes('heat-stated') && !r.preparation.heat) return false;
  if (chips.includes('strained') && r.preparation.filtered !== true) return false;
  return true;
}
