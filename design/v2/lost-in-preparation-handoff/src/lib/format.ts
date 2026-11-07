import type { LikelihoodRange, Vehicle, SourceWork, HeatLevel, ExtractedFieldKind, DriverId } from '../types';

export const HEAT_LABEL: Record<HeatLevel, string> = { cold: 'Cold', warm: 'Warm', boiled: 'Boiled', reflux: 'Reflux' };
export const FIELD_LABEL: Record<ExtractedFieldKind, string> = {
  plant: 'Plant', part: 'Part', vehicle: 'Solvent / vehicle', quantity: 'Quantity',
  heat: 'Heat', duration: 'Duration', filtration: 'Filtration',
};
export const DRIVER_LABEL: Record<DriverId, string> = { solvent: 'Solvent', heat: 'Heat', filtration: 'Filtration', acidity: 'Acidity' };

/**
 * Two ranges differ only when they do not overlap at all (touching counts as
 * overlap). Returns which side is enriched, 'overlap', or 'unknown'.
 */
export function compareRanges(a: LikelihoodRange, b: LikelihoodRange): 'a' | 'b' | 'overlap' | 'unknown' {
  if (a.low == null || a.high == null || b.low == null || b.high == null) return 'unknown';
  if (a.low > b.high) return 'a';
  if (b.low > a.high) return 'b';
  return 'overlap';
}

export const cx = (...parts: Array<string | false | null | undefined>) =>
  parts.filter(Boolean).join(' ');

/** Safe id fragment: "Monoterpenes (volatile oil)" → "monoterpenes-volatile-oil". */
export const slug = (s: string) =>
  s.normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

/** Two decimals, en dash for ranges. Never rounds an unknown to 0. */
export const fmt = (n: number) => n.toFixed(2);

export const isKnownRange = (r: LikelihoodRange | null | undefined): r is { low: number; high: number; point?: number | null } =>
  !!r && r.low != null && r.high != null;

export const rangeText = (r: LikelihoodRange) =>
  isKnownRange(r) ? `${fmt(r.low)}–${fmt(r.high)}` : 'Unknown';

export const rangeSpoken = (r: LikelihoodRange, what = 'Estimated likelihood') =>
  isKnownRange(r)
    ? `${what} between ${fmt(r.low)} and ${fmt(r.high)}` +
      (r.point != null ? `, point estimate ${fmt(r.point)}` : '') +
      `. Range width ${fmt(r.high - r.low)}.`
    : `${what} unknown.`;

export const VEHICLE_LABEL: Record<Vehicle, string> = {
  cold_infusion: 'Cold infusion',
  decoction: 'Decoction',
  wine: 'Wine',
  vinegar: 'Vinegar',
  oil: 'Oil',
  ethanol_extract: 'Ethanol extract',
  methanol_extract: 'Methanol extract',
  aqueous_extract: 'Aqueous extract',
  hydrodistillation: 'Hydrodistillation',
  water: 'Water',
  honey: 'Honey',
  unknown: 'Vehicle unknown',
};

/** Wilson 95% interval for k of n (used to build mock reporting-gap data). */
export function wilson(k: number, n: number, z = 1.96): [number, number] {
  if (n === 0) return [0, 1];
  const p = k / n, d = 1 + (z * z) / n;
  const c = (p + (z * z) / (2 * n)) / d;
  const h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  return [Math.max(0, c - h), Math.min(1, c + h)];
}
export const pct = (x: number) => `${Math.round(x * 100)}%`;
/** Mean width of the known ranges; used to flag "wide uncertainty". */
export const meanWidth = (rs: LikelihoodRange[]) => {
  const k = rs.filter(isKnownRange);
  return k.length ? k.reduce((s, r) => s + (r.high - r.low), 0) / k.length : null;
};

export const SOURCE_LABEL: Record<SourceWork, { short: string; full: string }> = {
  culpeper_1652: { short: 'Culpeper 1652', full: "Culpeper, The English Physitian (1652)" },
  pliny_nh: { short: 'Pliny, NH', full: 'Pliny the Elder, Naturalis Historia' },
};
