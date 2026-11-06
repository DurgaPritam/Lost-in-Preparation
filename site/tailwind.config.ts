import type { Config } from 'tailwindcss';

/**
 * Tailwind is configured so that ONLY design tokens exist.
 * `theme` (not `theme.extend`) replaces Tailwind's default palette, type
 * scale, spacing, radii and shadows — a stray `bg-red-500` or `text-[13px]`
 * simply has no default to fall back on. Arbitrary values are blocked by the
 * lint rule in DESIGN.md §10 (no `[#…]` / `[..px]` in className).
 */
const v = (name: string) => `var(--${name})`;

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './features/**/*.{ts,tsx}'],
  theme: {
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      paper: v('c-paper'),
      surface: v('c-surface'),
      sunken: v('c-sunken'),
      raised: v('c-raised'),
      ink: { DEFAULT: v('c-ink'), muted: v('c-ink-muted'), subtle: v('c-ink-subtle') },
      border: { DEFAULT: v('c-border'), strong: v('c-border-strong') },
      focus: v('c-focus'),
      overlay: v('c-overlay'),
      hist: { fg: v('c-hist-fg'), bg: v('c-hist-bg'), solid: v('c-hist-solid'), 'on-solid': v('c-hist-on-solid') },
      mod: { fg: v('c-mod-fg'), bg: v('c-mod-bg'), solid: v('c-mod-solid'), 'on-solid': v('c-mod-on-solid') },
      unk: { fg: v('c-unk-fg'), bg: v('c-unk-bg'), line: v('c-unk-line') },
      prov: { fg: v('c-prov-fg'), bg: v('c-prov-bg') },
      tox: { fg: v('c-tox-fg'), bg: v('c-tox-bg'), solid: v('c-tox-solid'), 'on-solid': v('c-tox-on-solid') },
    },
    fontFamily: {
      serif: v('f-serif'),
      sans: v('f-sans'),
      mono: v('f-mono'),
    },
    fontSize: {
      xs: ['12px', '16px'],
      sm: ['13px', '18px'],
      base: ['15px', '22px'],
      md: ['17px', '26px'],
      lg: ['20px', '28px'],
      xl: ['24px', '32px'],
      '2xl': ['30px', '38px'],
      '3xl': ['38px', '46px'],
    },
    fontWeight: { normal: '400', medium: '500', semibold: '600' },
    letterSpacing: { normal: '0', caps: '0.06em' },
    spacing: {
      0: '0px', px: '1px', 0.5: '2px', 1: '4px', 1.5: '6px', 2: '8px', 2.5: '10px', 3: '12px',
      4: '16px', 5: '20px', 6: '24px', 8: '32px', 10: '40px', 12: '48px', 16: '64px', 20: '80px', 24: '96px',
    },
    borderRadius: { none: '0px', sm: '2px', DEFAULT: '4px', md: '6px', full: '9999px' },
    boxShadow: { none: v('e-0'), 1: v('e-1'), 2: v('e-2'), 3: v('e-3') },
    transitionDuration: { fast: v('d-fast'), base: v('d-base') },
    transitionTimingFunction: { standard: v('ease') },
    screens: { sm: '640px', md: '900px', lg: '1200px' },
    extend: {
      maxWidth: { content: '1200px', prose: '68ch', drawer: '480px', tooltip: 'min(320px, calc(100vw - 32px))' },
      width: { nav: '240px', drawer: '480px', 'bar-sm': '160px', 'bar-md': '256px' },
      outlineColor: { focus: v('c-focus') },
    },
  },
  plugins: [],
} satisfies Config;
