'use client';

import type { NameResolution, Plate, SourceWork, ToxicityRecord } from '@/lib/types';
import Link from './Link';
import { PlateSlot } from './PlateSlot';
import { Taxon } from './Taxon';
import { ToxicityBadge } from '../honesty/ToxicityBadge';
import { DisputedName } from '../honesty/DisputedName';

/**
 * Plant card for the Recipe Atlas: plate, the name as written, the resolved
 * taxon (or the dispute), recipe count per source, toxicity. The whole title
 * is the link; badges stay outside the link so they remain separately
 * operable (no nested interactive elements).
 */
export interface PlantCardProps {
  name: NameResolution;
  common: string;
  plate?: Plate | null;
  /** SITE: one count per source; the two Culpeper editions are separate works and are never merged. */
  recipes: Record<SourceWork, number>;
  toxicity: ToxicityRecord;
  href: string;
  onOpen?: () => void;
}

export function PlantCard({ name, common, plate, recipes, toxicity, href, onOpen }: PlantCardProps) {
  const taxon = name.candidates[0]?.taxon ?? name.historicalName;
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-lg border border-border bg-surface shadow-1 transition-shadow duration-base ease-standard hover:shadow-2">
      <PlateSlot plate={plate} taxon={name.state === 'disputed' ? name.historicalName : taxon} showCaption={false} className="[&>div]:rounded-none [&>div]:border-0 [&>div]:border-b" />
      <div className="flex flex-1 flex-col gap-3 p-5">
        <h3 className="m-0 font-display text-2xl text-ink">
          <Link href={href} onClick={onOpen ? (e) => { e.preventDefault(); onOpen(); } : undefined} className="text-ink no-underline after:absolute after:inset-0 group-hover:underline">
            {common}
          </Link>
        </h3>
        <div className="text-sm text-ink-muted">
          {name.state === 'disputed' ? <DisputedName resolution={name} layout="inline" /> : <><span className="font-display italic">“{name.historicalName}”</span> → <Taxon name={name.state === 'genus_only' ? `${taxon} sp.` : taxon} /></>}
        </div>
        <div className="mt-auto flex flex-wrap items-center justify-between gap-2">
          <span className="num font-mono text-xs text-ink-subtle">Culpeper 1652 {recipes.culpeper_1652} · 1850 {recipes.culpeper_1850} · Pliny {recipes.pliny_nh}</span>
          <span className="relative z-10"><ToxicityBadge record={toxicity} withSources={false} /></span>
        </div>
      </div>
    </article>
  );
}
