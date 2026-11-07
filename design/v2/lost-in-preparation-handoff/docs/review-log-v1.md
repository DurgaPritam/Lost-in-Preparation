# Review log, v1 (Phase 4)

Kept for the record. The v1 screens it covers were replaced in v2; the component fixes (Tooltip, Drawer, DataTable, ChartTable, Taxon, UnknownValue) carried over unchanged. The v2 review is in DESIGN.md §12.

## How it was reviewed

1. **Automated, re-runnable: `npm run review` (`tests/review.mjs`).**
   - Builds and serves the app.
   - Covers 11 routes (gallery, 7 pages, 3 recipe variants), each in light and dark, at 1440px and 390px: 44 page states.
   - On top of those, 14 opened states: drawers, drivers panels, table fallbacks and toxicity sources.
   - In each state it runs **axe-core 4.10 (WCAG 2.0/2.1 A + AA, colour contrast included)** and checks for horizontal page overflow.
   - At 1440px light it tabs through every page, checking that each focus stop has a visible indicator.
   - In every dialog it checks that focus stays trapped inside and returns to the trigger on Escape.
2. **Code review** of every component and screen against the eight honesty rules.
3. **Visual review** of full-page 390px screenshots of every screen in both themes.
4. **Copy scan** of all React source, the canvas mocks and the docs for medical-claim and hype words.

## Result

| Check | Before fixes | After fixes |
|---|---|---|
| axe violations (WCAG A/AA, both themes) | 0 | **0** |
| Horizontal page overflow | 22 page states | **0** |
| Focus stops without a visible indicator | 0 | **0** |
| Dialog focus trap / return | not tested | **pass** |
| Runtime errors | 0 | **0** |

axe passed even before the fixes. Most of the issues below were found by code review and the screenshots, which is why the review doesn't rely on automated testing alone.

## Issues found and fixed

**Accessibility**

| # | Issue | Fix |
|---|---|---|
| 1 | Closed tooltips were invisible but still laid out. They widened the page, causing sideways scroll at 390px on 11 page states, and up to 1492px wide at 1440px. | A closed tooltip is now `display: none`. An open one is nudged back inside the viewport and flips below its trigger when there's no room above. The max width is now a token: `min(320px, 100vw − 32px)`. |
| 2 | Tooltips couldn't be opened on touch screens (hover and focus only, and iOS doesn't focus a button on tap). | Tooltips now also toggle on click or tap. |
| 3 | The tooltip silently replaced its trigger's own `onFocus`, `onBlur` and `onClick` handlers. | The handlers are now combined, so both run. |
| 4 | The Compare drivers panel used the `hidden` attribute together with a `grid` class. The class won, so the panel was always shown. | The panel now renders only when open. A global `[hidden]{display:none!important}` rule prevents this whole class of bug. |
| 5 | Compare's compound-class headings had ids with spaces and parentheses, which broke their `aria-labelledby` links. | Ids now go through a new `slug()` helper. |
| 6 | No chart had a data-table fallback. | New `ChartTable` ("View as table") on Compare, Audit (both sources), Hypotheses, and Methods (xTB comparison and positive control). |
| 7 | Clickable `DataTable` rows only worked with a mouse. | Rows are focusable and open on Enter or Space. |
| 8 | Drawer problems: any parent re-render pulled focus back to the panel; Shift+Tab from the panel escaped the dialog; the page behind stayed reachable; the background scrolled. | The close handler is held in a ref. The trap now wraps from the panel. The drawer is portalled to `<body>`, with `#root` made `inert` while it is open. Background scroll is locked. |
| 9 | Hypotheses jumped from the page heading (h1) straight to card titles (h3). | Added an h2, "Ranked leads", and labelled the list with it. |
| 10 | `LikelihoodBar` values were read out twice, and its unknown state was plain text instead of the Unknown component. | The visible value line is hidden from screen readers (the image label already says it in full). The unknown state now uses `UnknownValue`. |
| 11 | In Recipe detail, the empty "#" cell of unstated fields was read out as "en dash". | Replaced with screen-reader text: "Not in passage". |
| 12 | The `UnknownValue` glyph was squashed to a dot in narrow table cells. | The glyph no longer shrinks. |
| 13 | The gallery always forced the light theme, so its dark-theme checks were really testing light. | It now starts from `?theme=` or the system preference. |
| 14 | Compare's "From recipe" link and the Hypotheses evidence-trail links bypassed the router, and some used `href="#"`. | They now go through `onNavigate`. Links with no target are no longer rendered. |

**Consistency of the honesty treatments**

| # | Issue | Fix |
|---|---|---|
| 15 | Methods could print a metric's point value without its interval, and the interval chart drew a point tick with no band. | The point is withheld and "Interval unknown" is shown instead. |
| 16 | The Methods metrics table could be sorted by value, which mixes κ, error rates and proportions. | That column is no longer sortable. |
| 17 | Hypotheses labelled an unknown range, and a lead where modern was higher, as "Weak lead · ranges overlap". | Each case now has its own label: "Can't compare", "Modern preparation higher · not a lead", "Weak lead". |
| 18 | `DisputedName` sorted candidates by their point estimate. | They are now sorted by the low end of each range, with unknowns last. |
| 19 | The hydrodistillation study showed the tag "Aqueous extract" because that vehicle was missing. | Added a `hydrodistillation` vehicle to the type, labels and mock data. |
| 20 | Recipe detail had no per-candidate Compare links for disputed names, contrary to §9 and the canvas. | Added one link per species-rank candidate. Genus-only and unresolved names each get their own message. |
| 21 | The xTB negative-result card didn't show its pre-registered Fail; it appeared only in the table. | Added an optional `preregisteredId` to `MethodComparison` and `PositiveControl`. The card now shows the outcome marker. |
| 22 | "*Mentha sp.*" was set fully in italics. Botanical convention keeps "sp." upright. | New `Taxon` component, used on every screen. |
| 23 | The Audit match chips weren't labelled and relied on column order. | Chips now read "Vehicle ≠ differs", "Heat = same as source", and so on (also fixed in the canvas). |
| 24 | "Consistent with ranks 4–4" read oddly. | Now reads "The uncertainty allows only this rank" (also fixed in the canvas). |

**Language**

| # | Issue | Fix |
|---|---|---|
| 25 | "Treat as a lead" in the Provisional tooltip uses "treat", a medical verb, in a herbal context. | Now reads "Read it as a lead, not a finding" (React and canvas). |

The scan found no other medical-claim or hype terms. "Safety" appears only in "not evidence of safety", which is the intended disclaimer.

**Mobile (390px)**

| # | Issue | Fix |
|---|---|---|
| 26 | The wide tables (Audit: 10 columns; Methods: metrics and pre-registered checks; Data: sources) pushed the evidence and licence columns off-screen inside a scroll box. | Below 900px, `DataTable` now stacks each row into a labelled card. |
| 27 | Recipe detail's fields table hid the Evidence column at 390px. | Below 640px the evidence badge sits under the normalised value. "As written" is hidden there, since it is already highlighted in the passage. |
| 28 | `DisputedName`'s candidate table could push a narrow container sideways. | It now scrolls inside its own box. |

**Handoff**

| # | Issue | Fix |
|---|---|---|
| 29 | Fonts were loaded from the Google Fonts CDN (a third-party request, and no offline use). | The fonts are now vendored in `assets/fonts/` with their OFL licences. |

## Not verified (please test before release)

- No manual screen-reader pass (NVDA, JAWS or VoiceOver) has been done. Automated checks and code review cannot replace it.
- axe cannot measure contrast over the hatched "unknown" fills. Those text/ground pairs were checked by script instead (`unk-fg` on `unk-bg`: 5.59:1 light, 6.75:1 dark).
- **The canvas mocks are a visual reference, not production code.** Items 23–25 were mirrored there, but the "View as table" fallbacks and the mobile card tables exist only in the React code. The React code is the source of truth.
- PubMed links built from the placeholder PMIDs (`0000000n`) don't resolve.
- At 390px, the native Compare preparation `<select>` truncates long option labels. The full label is repeated in the tag below it.
