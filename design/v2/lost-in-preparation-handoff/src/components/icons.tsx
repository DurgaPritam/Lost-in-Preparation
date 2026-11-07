import type { SVGProps } from 'react';

/**
 * Glyphs carry meaning on their own so no status depends on colour alone.
 * All are 16px, stroke = currentColor, decorative by default (aria-hidden);
 * the adjacent text label is the accessible name.
 */
type P = SVGProps<SVGSVGElement> & { size?: number };
const base = ({ size = 16, ...p }: P) => ({
  width: size, height: size, viewBox: '0 0 16 16', fill: 'none',
  stroke: 'currentColor', strokeWidth: 1.5, strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const, 'aria-hidden': true, focusable: false, ...p,
});

/** Validated: filled disc with check. */
export const IconValidated = (p: P) => (
  <svg {...base(p)}><circle cx="8" cy="8" r="6.25" fill="currentColor" /><path d="M5.2 8.2l1.9 1.9 3.7-4" stroke="var(--c-surface)" /></svg>
);
/** Provisional: half-filled disc. */
export const IconProvisional = (p: P) => (
  <svg {...base(p)}><circle cx="8" cy="8" r="6.25" /><path d="M8 1.75a6.25 6.25 0 0 1 0 12.5z" fill="currentColor" stroke="none" /></svg>
);
/** Pending: dashed empty ring. */
export const IconPending = (p: P) => (
  <svg {...base(p)}><circle cx="8" cy="8" r="6.25" strokeDasharray="2.2 2.2" /></svg>
);
/** Heuristic: hollow diamond (rule of thumb, not measured). */
export const IconHeuristic = (p: P) => (
  <svg {...base(p)}><path d="M8 2l6 6-6 6-6-6z" /></svg>
);
/** Toxicity reported: triangle with bar. */
export const IconToxic = (p: P) => (
  <svg {...base(p)}><path d="M8 2.2L14.3 13.5H1.7z" /><path d="M8 6.5v3.2" /><path d="M8 11.6v.1" strokeWidth={2} /></svg>
);
/** Concern: circle with bar. */
export const IconConcern = (p: P) => (
  <svg {...base(p)}><circle cx="8" cy="8" r="6.25" /><path d="M8 4.8v3.8" /><path d="M8 11v.1" strokeWidth={2} /></svg>
);
/** No toxicity reported: empty square (absence of a report, not a tick). */
export const IconNoReport = (p: P) => (
  <svg {...base(p)}><rect x="2.5" y="2.5" width="11" height="11" rx="1" /><path d="M5 8h6" /></svg>
);
/** Unknown: question mark in a dashed square. */
export const IconUnknown = (p: P) => (
  <svg {...base(p)}><rect x="2.5" y="2.5" width="11" height="11" rx="1" strokeDasharray="2 2" /><path d="M6.4 6.4a1.7 1.7 0 1 1 2.4 1.5c-.5.3-.8.6-.8 1.2" /><path d="M8 11.2v.1" strokeWidth={2} /></svg>
);
/** Data lacking: hatched square. */
export const IconLacking = (p: P) => (
  <svg {...base(p)}><rect x="2.5" y="2.5" width="11" height="11" rx="1" /><path d="M2.5 9.5l7-7M6.5 13.5l7-7" /></svg>
);
/** Historical marker: square. Modern marker: circle. Used in legends and bars. */
export const MarkHistorical = (p: P) => (
  <svg {...base({ size: 10, ...p })} viewBox="0 0 10 10"><rect x="1" y="1" width="8" height="8" fill="currentColor" stroke="none" /></svg>
);
export const MarkModern = (p: P) => (
  <svg {...base({ size: 10, ...p })} viewBox="0 0 10 10"><circle cx="5" cy="5" r="4" fill="currentColor" stroke="none" /></svg>
);
/** System error (not toxicity): circle with a cross. */
export const IconError = (p: P) => (
  <svg {...base(p)}><circle cx="8" cy="8" r="6.25" /><path d="M5.8 5.8l4.4 4.4M10.2 5.8l-4.4 4.4" /></svg>
);
export const IconInfo =(p: P) => (
  <svg {...base(p)}><circle cx="8" cy="8" r="6.25" /><path d="M8 7.2v4" /><path d="M8 4.8v.1" strokeWidth={2} /></svg>
);
export const IconSearch = (p: P) => (
  <svg {...base(p)}><circle cx="7" cy="7" r="4.5" /><path d="M10.5 10.5L14 14" /></svg>
);
export const IconClose = (p: P) => (
  <svg {...base(p)}><path d="M4 4l8 8M12 4l-8 8" /></svg>
);
export const IconChevron = (p: P) => (
  <svg {...base(p)}><path d="M6 4l4 4-4 4" /></svg>
);
export const IconSort = ({ dir, ...p }: P & { dir: 'asc' | 'desc' | 'none' }) => (
  <svg {...base(p)}>
    <path d="M5 6.5L8 3.5l3 3" opacity={dir === 'desc' ? 0.3 : 1} />
    <path d="M5 9.5l3 3 3-3" opacity={dir === 'asc' ? 0.3 : 1} />
  </svg>
);

/* v2 additions */
export const IconSun = (p: P) => (
  <svg {...base(p)}><circle cx="8" cy="8" r="3" /><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1" /></svg>
);
export const IconMoon = (p: P) => (
  <svg {...base(p)}><path d="M13 9.6A5.5 5.5 0 0 1 6.4 3a5.5 5.5 0 1 0 6.6 6.6z" /></svg>
);
export const IconMenu = (p: P) => (
  <svg {...base(p)}><path d="M2.5 4.5h11M2.5 8h11M2.5 11.5h11" /></svg>
);
export const IconArrowRight = (p: P) => (
  <svg {...base(p)}><path d="M3 8h10M9 4l4 4-4 4" /></svg>
);
