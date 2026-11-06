'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from '@/components/base/Link';
import type { RecipeSummary as Recipe, SourceConfidence, SourceWork } from '@/lib/types';
import { HEAT_LABEL, cx } from '@/lib/data/format';
import { FACETS, FACET_LEGEND, RECIPE_PAGE, emptySelection, facetOptions, filterRecipes, type Facet, type FacetOption } from '@/lib/data/selectors/recipeFacets';
import { recipeSlug } from '@/lib/data/selectors/recipes';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/base/Button';
import { EmptyState, ErrorState, LoadingState } from '@/components/base/States';
import { FilterGroup, FilterSummary } from '@/components/base/Filters';
import { PrepTag } from '@/components/base/PrepTag';
import { SearchField } from '@/components/base/SearchField';
import { DisputedName } from '@/components/honesty/DisputedName';
import { EvidenceStatusBadge } from '@/components/honesty/EvidenceStatusBadge';
import { SourceConfidenceMarker } from '@/components/honesty/SourceConfidenceMarker';
import { ToxicityBadge } from '@/components/honesty/ToxicityBadge';

/**
 * RECIPE EXPLORER — search + five facets (plant, source, solvent, heat,
 * filtration). Every facet has an Unknown option with a count, so a filter
 * can never silently drop "not stated" recipes. Results are a list, not a
 * table, so a row reflows to a stacked card at 390px.
 * SITE: facet logic lives in lib/data/selectors/recipeFacets.ts. The first screen (first PAGE recipes and the unfiltered
 * facet counts) is rendered statically; the full list loads from /data/recipe-index.json after it, and searching or
 * filtering before it arrives shows a loading state rather than partial counts.
 */

/** SITE: 631 real recipes, so the list renders PAGE cards at a time and the plant facet shows its most frequent
 *  values first (every value stays reachable through "Show all"). */
const PAGE = RECIPE_PAGE;
const PLANT_CHIPS = 12;

export function RecipeExplorer({ initial, total, initialOptions, confidences }: {
  initial: Recipe[]; total: number; initialOptions: Record<Facet, FacetOption[]>; confidences: Record<SourceWork, SourceConfidence>;
}) {
  const [q, setQ] = useState('');
  const [sel, setSel] = useState(emptySelection);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [limit, setLimit] = useState(PAGE);
  const [allPlants, setAllPlants] = useState(false);
  const [all, setAll] = useState<Recipe[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let live = true;
    setFailed(false);
    fetch('/data/recipe-index.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: Recipe[]) => { if (live) setAll(d); })
      .catch(() => { if (live) setFailed(true); });
    return () => { live = false; };
  }, [attempt]);

  const filtering = q.trim() !== '' || FACETS.some((f) => sel[f].length > 0);
  const shown = all ? filterRecipes(all, q, sel) : initial;
  const shownCount = all ? shown.length : total;
  const waiting = !all && (filtering || limit > initial.length);
  const options = useMemo(() => (all ? facetOptions(all, q, sel) : initialOptions), [all, q, sel, initialOptions]);

  const activeCount = FACETS.reduce((n, f) => n + sel[f].length, 0);

  return (
    <AppShell current="recipes">
      <div className="flex flex-col gap-4">
        <SearchField label="Search plants, names, uses and recipe text" value={q} onChange={(v) => { setQ(v); setLimit(PAGE); }} hint="Historical spellings are matched as written: try “wormwood”, “Juyce” or “decoction”." />
        <div className="md:hidden">
          <Button aria-expanded={filtersOpen} aria-controls="recipe-filters" onClick={() => setFiltersOpen((o) => !o)}>
            Filters{activeCount > 0 ? ` (${activeCount})` : ''}
          </Button>
        </div>
        <div id="recipe-filters" className={cx('flex-col gap-4 rounded border border-border bg-surface p-4 md:flex', filtersOpen ? 'flex' : 'hidden')}>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {FACETS.map((f) => {
              const opts = f === 'plant' && !allPlants
                ? options[f].filter((o, i) => i < PLANT_CHIPS || o.value === 'unknown' || o.value === 'disputed' || sel.plant.includes(o.value))
                : options[f];
              return (
                <div key={f} className="flex flex-col gap-2">
                  <FilterGroup legend={FACET_LEGEND[f]} options={opts} selected={sel[f]} onChange={(next) => { setSel((s) => ({ ...s, [f]: next })); setLimit(PAGE); }} />
                  {f === 'plant' && options.plant.length > PLANT_CHIPS + 2 && (
                    <button type="button" aria-expanded={allPlants} onClick={() => setAllPlants((o) => !o)} className="w-max text-sm text-ink-muted underline underline-offset-2 hover:text-ink">
                      {allPlants ? 'Show the most frequent plants' : `Show all ${options.plant.length} plant values`}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        <FilterSummary shown={shownCount} total={total} onClear={() => { setSel(emptySelection()); setQ(''); }} />
      </div>

      {failed && !all && (
        <ErrorState title="The full recipe list did not load"
          body={waiting ? 'Search, filters and the rest of the list need the full list.' : `The first ${initial.length} recipes are shown below; search, filters and the rest of the list need the full list.`}
          onRetry={() => setAttempt((n) => n + 1)} />
      )}
      {waiting ? (
        failed ? null : <LoadingState label="Loading all recipes" />
      ) : shown.length === 0 ? (
        <EmptyState
          title="No recipes match"
          body="Try removing a filter. Recipes whose preparation is not stated are kept under each facet’s “Not stated” option."
          action={<Button size="sm" onClick={() => setSel(emptySelection())}>Clear filters</Button>}
        />
      ) : (
        <ul className="m-0 flex list-none flex-col gap-3 p-0" aria-label="Recipes">
          {shown.slice(0, limit).map((r) => (
            <li key={r.id}>
              <article className="flex flex-col gap-3 rounded border border-border bg-surface p-4 md:p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <h2 className="m-0 text-base font-normal">
                    <Link href={`/recipes/${recipeSlug(r.id)}/`} className="text-ink no-underline hover:underline">
                      <DisputedName resolution={r.name} layout="inline" />
                    </Link>
                  </h2>
                  <SourceConfidenceMarker confidence={confidences[r.source]} compact />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <PrepTag prep={r.preparation} />
                  {r.preparation.heat === undefined || r.preparation.heat === null ? null : (
                    <span className="text-sm text-ink-muted">{HEAT_LABEL[r.preparation.heat]}</span>
                  )}
                </div>
                {r.indication && <p className="m-0 max-w-prose font-serif text-md text-ink-muted">“{r.indication}”</p>}
                <div className="flex flex-wrap items-center gap-2">
                  <EvidenceStatusBadge status={r.evidence} size="sm" />
                  <ToxicityBadge record={r.toxicity} withSources={false} />
                </div>
              </article>
            </li>
          ))}
        </ul>
      )}
      {!waiting && shownCount > limit && (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => setLimit((l) => l + PAGE)}>Show {Math.min(PAGE, shownCount - limit)} more</Button>
          <span className="num text-sm text-ink-muted">{limit} of {shownCount} shown</span>
        </div>
      )}
    </AppShell>
  );
}
