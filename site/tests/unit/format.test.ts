import { describe, expect, it } from 'vitest';
import { ciText, compareRanges, filteredText, intText, pct, rangeSpoken, rangeText, vehicleLabel } from '@/lib/data/format';

describe('compareRanges is the only enriched/weak decision', () => {
  it('needs non-overlapping ranges; touching counts as overlap', () => {
    expect(compareRanges({ low: 0.6, high: 0.9 }, { low: 0.1, high: 0.5 })).toBe('a');
    expect(compareRanges({ low: 0.1, high: 0.5 }, { low: 0.6, high: 0.9 })).toBe('b');
    expect(compareRanges({ low: 0.1, high: 0.5 }, { low: 0.5, high: 0.9 })).toBe('overlap');
  });
  it('an unknown bound is unknown, never 0', () => {
    expect(compareRanges({ low: null, high: 0.5 }, { low: 0.6, high: 0.9 })).toBe('unknown');
    expect(rangeText({ low: null, high: null })).toBe('Unknown');
    expect(rangeSpoken({ low: null, high: null })).toMatch(/unknown/);
  });
});

describe('labels and numbers', () => {
  it('vehicle labels keep solvents apart and never drop an unknown silently', () => {
    expect(vehicleLabel('honey+vinegar')).toBe('Honey + vinegar');
    expect(vehicleLabel('unknown')).toBe('Vehicle unknown');
    expect(vehicleLabel('water+unknown')).toBe('Water');
    expect(vehicleLabel('hydroethanolic')).toBe('Hydroethanolic');
  });
  it('filtration has four states', () => {
    expect([null, true, false, 'not_applicable' as const].map(filteredText)).toEqual(['filtering not stated', 'filtered', 'unfiltered', 'filtering not applicable']);
  });
  it('shares and intervals', () => {
    expect(pct(0.2558)).toBe('26%');
    expect(pct(0.0233, 1)).toBe('2.3%');
    expect(ciText(0.1493, 0.4024)).toBe('95% CI 15–40%');
    expect(ciText(null, 0.4)).toBe('CI not computed');
    expect(intText(1152)).toBe('1,152');
  });
});
