/**
 * ALL number and label formatting for the site lives here (design/src/lib/format.ts plus SITE additions).
 * compareRanges() remains the only function allowed to say "enriched" or "weak".
 */
import type { LikelihoodRange, Vehicle, SourceWork, HeatLevel, ExtractedFieldKind, DriverId, Preparation, MatchState } from '../types';

export const HEAT_LABEL: Record<HeatLevel, string> = { cold: 'Cold', warm: 'Warm', boiled: 'Boiled', reflux: 'Reflux' };
/** SITE: the fields M1 extracts (design listed quantity, which M1 never extracts). */
export const FIELD_LABEL: Record<ExtractedFieldKind, string> = {
  plant: 'Plant', part: 'Part', freshOrDried: 'Fresh or dried', vehicle: 'Solvent / vehicle', heat: 'Heat',
  duration: 'Duration', filtration: 'Filtration', process: 'Process', form: 'Form', indication: 'Use (as written)',
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

/** SITE: one label per contract vehicle value (historical Solvent and ModernSolvent enums). */
export const VEHICLE_LABEL: Record<string, string> = {
  water: 'Water', wine: 'Wine', vinegar: 'Vinegar', oil: 'Oil', honey: 'Honey', none: 'No vehicle', other: 'Other vehicle',
  methanol: 'Methanol', ethanol: 'Ethanol', hydroethanolic: 'Hydroethanolic', hexane: 'Hexane', chloroform: 'Chloroform',
  ethyl_acetate: 'Ethyl acetate', dichloromethane: 'Dichloromethane', acetone: 'Acetone', co2: 'Supercritical CO₂',
  unknown: 'Vehicle unknown',
};
/** "honey+vinegar" → "Honey + vinegar". Unknown parts never vanish: an all-unknown key prints "Vehicle unknown". */
export const vehicleLabel = (v: Vehicle): string => {
  const parts = v.split('+').filter((x) => x && x !== 'unknown');
  if (parts.length === 0) return VEHICLE_LABEL.unknown;
  return parts.map((p, i) => (i === 0 ? VEHICLE_LABEL[p] ?? p : (VEHICLE_LABEL[p] ?? p).toLowerCase())).join(' + ');
};

export const filteredText = (f: Preparation['filtered']) =>
  f == null ? 'filtering not stated' : f === 'not_applicable' ? 'filtering not applicable' : f ? 'filtered' : 'unfiltered';

export const SOURCE_LABEL: Record<SourceWork, { short: string; full: string }> = {
  culpeper_1652: { short: 'Culpeper 1652', full: 'Culpeper, The English Physitian (1652)' },
  culpeper_1850: { short: 'Culpeper 1850', full: 'Culpeper, The Complete Herbal (1850 edition)' },
  pliny_nh: { short: 'Pliny, NH', full: 'Pliny the Elder, Naturalis Historia (Bostock & Riley translation)' },
};

export const MATCH_LABEL: Record<MatchState, string> = {
  matches: 'same as source', differs: 'differs', not_stated: 'not stated', no_analogue: 'no modern analogue',
};

/** SITE: shares (0–1) as whole percentages; a share is never shown without n. */
export const pct = (v: number, digits = 0) => `${(v * 100).toFixed(digits)}%`;
export const shareText = (k: number, n: number) => `${k} of ${n}`;
/** "95% CI 15–40%". Null bounds print "CI not computed", never 0. */
export const ciText = (low: number | null | undefined, high: number | null | undefined, digits = 0) =>
  low == null || high == null ? 'CI not computed' : `95% CI ${(low * 100).toFixed(digits)}–${(high * 100).toFixed(digits)}%`;
export const intText = (n: number) => n.toLocaleString('en-GB');
/** Mean width of the known ranges; used to flag "wide uncertainty" (design v2). */
export const meanWidth = (rs: LikelihoodRange[]) => {
  const k = rs.filter(isKnownRange);
  return k.length ? k.reduce((s, r) => s + (r.high - r.low), 0) / k.length : null;
};
