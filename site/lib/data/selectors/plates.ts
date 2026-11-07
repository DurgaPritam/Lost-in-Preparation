/** Botanical plates (contract v1.8, P39: site-data/plates.json) as the design's Plate. */
import type { Plate } from '../../types';
import type { ContractPlate } from '../load';

export function toPlate(p: ContractPlate): Plate {
  return {
    taxon: p.taxon, caption: p.caption, status: p.status === 'confirmed' ? 'confirmed' : p.status === 'sourced' ? 'sourced' : 'to_source',
    licence: p.licence, host: p.host === 'Wikimedia Commons' ? 'Wikimedia Commons' : null, fileUrl: p.fileUrl,
    imageUrl: p.image?.src ?? null, author: p.author, date: p.date, work: p.work, image: p.image,
  };
}

export const plateFor = (plates: Plate[], taxon: string | null | undefined) =>
  (taxon ? plates.find((p) => p.taxon === taxon) : undefined) ?? null;
