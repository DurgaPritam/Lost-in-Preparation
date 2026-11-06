import { describe, expect, it } from 'vitest';
import { getRecipeSummaries } from '@/lib/data/assemble';
import { FACETS, emptySelection, facetOptions, facetValue, filterRecipes } from '@/lib/data/selectors/recipeFacets';

const all = getRecipeSummaries();

describe('recipe facets', () => {
  it('every facet lists Unknown, last, and unfiltered counts add up to the total', () => {
    const o = facetOptions(all, '', emptySelection());
    for (const f of FACETS) {
      expect(o[f].at(-1)?.value).toBe('unknown');
      expect(o[f].reduce((n, x) => n + x.count, 0)).toBe(all.length);
    }
  });
  it('a facet count equals the number of recipes the filter then shows', () => {
    const o = facetOptions(all, '', emptySelection());
    for (const opt of o.heat) {
      const sel = { ...emptySelection(), heat: [opt.value] };
      expect(filterRecipes(all, '', sel).length).toBe(opt.count);
    }
  });
  it('choosing "Not stated" keeps exactly the recipes whose heat is unknown', () => {
    const shown = filterRecipes(all, '', { ...emptySelection(), heat: ['unknown'] });
    expect(shown.length).toBeGreaterThan(0);
    expect(shown.every((r) => facetValue.heat(r) === 'unknown')).toBe(true);
  });
  it('search is case-insensitive over the recipe text', () => {
    const lower = filterRecipes(all, 'decoction', emptySelection()).length;
    expect(lower).toBeGreaterThan(0);
    expect(filterRecipes(all, '  DECOCTION ', emptySelection()).length).toBe(lower);
  });
});
