'use client';

import { useEffect, useMemo, useState } from 'react';
import type { RecipeSummary, SourceConfidence, SourceWork } from '@/lib/types';
import { cx, SOURCE_LABEL, vehicleLabel } from '@/lib/data/format';
import { ATLAS_CHIPS, plantKeyOf, recipeMatches, type AtlasChip } from '@/lib/data/selectors/atlas';
import { recipeSlug } from '@/lib/data/selectors/recipeSlug';
import type { AtlasPlant } from '@/lib/data/assemble';
import { SiteShell, PageHeader } from '@/components/layout/SiteShell';
import { EmptyState, ErrorState, LoadingState } from '@/components/base/States';
import { PlantCard } from '@/components/base/PlantCard';
import { IconSearch } from '@/components/icons';
import Link from '@/components/base/Link';

/**
 * RECIPE ATLAS — search first, then plant cards with plates, then recipes (design v2 screens/Atlas.tsx).
 * SITE: the plant cards render statically; the recipe index (/data/recipe-index.json) loads when a search or filter is
 * used. `?q=` and `?plant=` make every search and every plant shareable. A card lists up to LINKS recipes and links to
 * the plant's own view for the rest.
 */
const LINKS = 4;

export function Atlas({ plants, total }: { plants: AtlasPlant[]; total: number; confidences: Record<SourceWork, SourceConfidence> }) {
  const [q, setQ] = useState('');
  const [chips, setChips] = useState<AtlasChip[]>([]);
  const [plant, setPlant] = useState<string | null>(null);
  const [index, setIndex] = useState<RecipeSummary[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const qs = new URLSearchParams(window.location.search);
    setQ(qs.get('q') ?? '');
    setPlant(qs.get('plant'));
    setMounted(true);
  }, []);
  useEffect(() => {
    if (!mounted) return;
    const p = new URLSearchParams();
    if (q.trim()) p.set('q', q.trim());
    if (plant) p.set('plant', plant);
    const s = p.toString();
    window.history.replaceState(null, '', `${window.location.pathname}${s ? `?${s}` : ''}`);
  }, [q, plant, mounted]);

  const filtering = q.trim() !== '' || chips.length > 0;
  useEffect(() => {
    if (!filtering || index || failed) return;
    fetch('/data/recipe-index.json').then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d: RecipeSummary[]) => setIndex(d)).catch(() => setFailed(true));
  }, [filtering, index, failed]);
  const toggle = (c: AtlasChip) => setChips((cs) => (cs.includes(c) ? cs.filter((x) => x !== c) : [...cs, c]));
  const clear = () => { setChips([]); setQ(''); setPlant(null); };

  const view = useMemo(() => {
    let ps = plant ? plants.filter((p) => p.key === plant) : plants;
    let shownRecipes = ps.reduce((n, p) => n + p.total, 0);
    let linksOf = (p: AtlasPlant) => p.links;
    if (filtering && index) {
      const hit = new Map<string, Set<string>>();
      for (const r of index) {
        if (!recipeMatches(r, q, chips)) continue;
        const k = plantKeyOf(r.name);
        if (!hit.has(k)) hit.set(k, new Set());
        hit.get(k)!.add(recipeSlug(r.id));
      }
      ps = ps.filter((p) => hit.has(p.key));
      shownRecipes = ps.reduce((n, p) => n + hit.get(p.key)!.size, 0);
      linksOf = (p) => p.links.filter((l) => hit.get(p.key)!.has(l.slug));
    }
    return { ps, shownRecipes, linksOf };
  }, [plants, plant, filtering, index, q, chips]);

  const waiting = filtering && !index && !failed;

  return (
    <SiteShell current="atlas">
      <PageHeader eyebrow="Recipe Atlas" title="Every recipe, read as a recipe" lead="Search plants, historical names, preparations or words in the passage. Historical spellings are matched as written." />
      <div className="flex flex-col gap-4">
        <label htmlFor="atlas-q" className="sr-only">Search the Atlas</label>
        <div className="relative">
          <IconSearch size={20} className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-ink-muted" />
          <input
            id="atlas-q" type="search" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder="Try “wormwood”, “absinthium”, “vinegar”, “strain”…"
            className="h-14 w-full rounded-full border border-border-strong bg-surface pl-14 pr-5 text-md text-ink shadow-1 placeholder:text-ink-subtle"
          />
        </div>
        <div role="group" aria-label="Filters" className="flex flex-wrap gap-2">
          {ATLAS_CHIPS.map((c) => {
            const on = chips.includes(c.id);
            return <button key={c.id} type="button" aria-pressed={on} onClick={() => toggle(c.id)} className={cx('h-9 rounded-full border px-4 text-sm font-medium', on ? 'border-ink bg-ink text-paper' : 'border-border-strong text-ink-muted hover:text-ink')}>{c.label}</button>;
          })}
        </div>
        <p className="m-0 text-sm text-ink-muted" aria-live="polite">
          {waiting ? 'Searching every recipe…' : `${view.shownRecipes} of ${total} recipes · ${view.ps.length} plants`}
          {(chips.length > 0 || q || plant) && <> · <button type="button" onClick={clear} className="text-ink underline underline-offset-4">clear</button></>}
        </p>
        {plant && <p className="m-0 text-sm text-ink-muted">Showing one plant: <strong className="font-semibold text-ink">{plant}</strong>.</p>}
      </div>

      {failed && filtering ? (
        <ErrorState title="The recipe index did not load" body="Search and filters need the full recipe list. The plant cards are complete without them." onRetry={() => setFailed(false)} />
      ) : waiting ? (
        <LoadingState label="Searching every recipe" rows={3} />
      ) : view.ps.length === 0 ? (
        <EmptyState title="Nothing matches" body="Try a historical spelling, or clear the filters. Recipes whose details are not stated stay visible unless you filter them out." action={<button type="button" onClick={clear} className="h-10 rounded-full border border-border-strong px-4 font-semibold">Clear search and filters</button>} />
      ) : (
        <section aria-labelledby="plants">
          <h2 id="plants" className="sr-only">Plants</h2>
          <ul className="m-0 grid list-none grid-cols-1 gap-6 p-0 sm:grid-cols-2 lg:grid-cols-3">
            {view.ps.map((p) => {
              const links = view.linksOf(p);
              const one = plant === p.key;
              return (
                <li key={p.key} className="flex flex-col gap-2">
                  <PlantCard name={p.name} common={p.disputed ? `“${p.name.historicalName}”` : p.name.historicalName} plate={p.plate} recipes={p.recipes} toxicity={p.toxicity} href={p.href} />
                  {links.length > 1 && (
                    <ul className="m-0 flex list-none flex-col gap-1 p-0 text-sm">
                      {(one ? links : links.slice(0, LINKS)).map((r) => (
                        <li key={r.slug}><Link href={`/recipes/${r.slug}/`} className="text-brand underline underline-offset-4">{SOURCE_LABEL[r.source].short}: {vehicleLabel(r.vehicle)}</Link></li>
                      ))}
                      {!one && links.length > LINKS && (
                        <li><button type="button" onClick={() => { setPlant(p.key); window.scrollTo(0, 0); }} className="text-ink underline underline-offset-4">All {links.length} recipes for this plant →</button></li>
                      )}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </SiteShell>
  );
}
