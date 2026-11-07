import type { Config } from 'tailwindcss';

/**
 * Token-only Tailwind theme (v2). `theme` REPLACES Tailwind's defaults, so
 * only design tokens compile. Every colour is a CSS variable that swaps
 * between Herbarium (light) and Nocturne (dark); fonts swap the same way.
 * Inline `style` is allowed only for data-driven geometry (bar positions).
 */
const v = (name: string) => `var(--${name})`;

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './features/**/*.{ts,tsx}'],
  theme: {
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      paper: v('c-paper'), surface: v('c-surface'), sunken: v('c-sunken'), raised: v('c-raised'),
      ink: { DEFAULT: v('c-ink'), muted: v('c-ink-muted'), subtle: v('c-ink-subtle') },
      border: { DEFAULT: v('c-border'), strong: v('c-border-strong') },
      focus: v('c-focus'),
      overlay: v('c-overlay'),
      brand: { DEFAULT: v('c-brand'), soft: v('c-brand-soft'), on: v('c-brand-on') },
      hist: { fg: v('c-hist-fg'), bg: v('c-hist-bg'), solid: v('c-hist-solid'), edge: v('c-hist-edge'), 'on-solid': v('c-hist-on-solid') },
      mod: { fg: v('c-mod-fg'), bg: v('c-mod-bg'), solid: v('c-mod-solid'), edge: v('c-mod-edge') },
      unk: { fg: v('c-unk-fg'), bg: v('c-unk-bg'), line: v('c-unk-line') },
      prov: { fg: v('c-prov-fg'), bg: v('c-prov-bg') },
      tox: { fg: v('c-tox-fg'), bg: v('c-tox-bg'), solid: v('c-tox-solid'), 'on-solid': v('c-tox-on-solid') },
    },
    fontFamily: { display: v('f-display'), sans: v('f-sans'), mono: v('f-mono') },
    fontSize: {
      xs: ['12px', '16px'], sm: ['13px', '18px'], base: ['15px', '22px'], md: ['17px', '26px'], lg: ['20px', '28px'],
      // Display sizes scale with --display-scale so Instrument Serif (dark) matches Fraunces' optical size.
      xl: ['calc(24px * var(--display-scale))', '1.25'],
      '2xl': ['calc(32px * var(--display-scale))', '1.18'],
      '3xl': ['calc(44px * var(--display-scale))', '1.1'],
      '4xl': ['calc(60px * var(--display-scale))', '1.04'],
      '5xl': ['calc(76px * var(--display-scale))', '1'],
    },
    fontWeight: { normal: '400', medium: '500', semibold: '600' },
    letterSpacing: { normal: '0', caps: '0.12em', display: v('display-tracking') },
    spacing: {
      0: '0px', px: '1px', 0.5: '2px', 1: '4px', 1.5: '6px', 2: '8px', 2.5: '10px', 3: '12px', 3.5: '14px',
      4: '16px', 5: '20px', 6: '24px', 7: '28px', 8: '32px', 9: '36px', 10: '40px', 11: '44px', 12: '48px',
      14: '56px', 16: '64px', 20: '80px', 24: '96px', 28: '112px',
    },
    borderRadius: { none: '0px', sm: '4px', DEFAULT: '8px', md: '12px', lg: '16px', xl: '22px', full: '9999px' },
    boxShadow: { none: 'none', 1: v('e-1'), 2: v('e-2'), 3: v('e-3'), glow: v('e-glow') },
    transitionDuration: { fast: v('d-fast'), base: v('d-base'), bar: v('d-bar') },
    transitionTimingFunction: { standard: v('ease') },
    screens: { sm: '640px', md: '900px', lg: '1200px' },
    extend: {
      maxWidth: { content: '1200px', prose: '68ch', drawer: '480px', tooltip: 'min(320px, calc(100vw - 32px))' },
      width: { nav: '240px', drawer: '480px', 'bar-sm': '160px', 'bar-md': '256px', plate: '72px' },
      height: { plate: '96px' },
      aspectRatio: { card: '4 / 3', portrait: '3 / 4', wide: '16 / 9' },
      outlineColor: { focus: v('c-focus') },
    },
  },
  plugins: [],
} satisfies Config;
