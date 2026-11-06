# Lost in Preparation: Design System (Phase 1)

This is the design contract for the build agent. It covers the tokens, the component behaviour and the reasons behind each decision. There are no screens yet.

> **Open dependency.** The project JSON Schemas were not attached in Phase 1. `src/types.ts` holds the shapes this system assumes. Each honesty component takes narrow props (a `LikelihoodRange` or a `ToxicityRecord`, never a whole recipe), so when the schemas arrive only that file and a few small mappers should need to change. Please send the schemas before Phase 2.

---

## 1. Direction

**An interactive supplement to a journal article.** Picture a well-set methods appendix that you can use: warm paper, hairline rules, a serif for the historical voice and a sans-serif for everything the tool computes. The judges (pharmacognosists, a Byzantinist and data scientists) are checking for rigour, so the system's main job is to make uncertainty easy to read. Decoration comes second.

What we deliberately leave out:

- brand-colour primary buttons
- gradients
- coloured left-border cards
- icons in the navigation
- celebratory states
- green "safe" signals

**Two voices, kept apart on purpose:**

| Voice | Typeface | Used for |
|---|---|---|
| Historical (what the sources say) | EB Garamond | Passages, names as written in the source, page titles, historical vehicle names |
| Computed (what the tool infers) | IBM Plex Sans / Plex Mono | All UI, labels, numbers, ranges |

A reader can always tell whether a line came from Culpeper or Pliny or from the model, just by its typeface.

## 2. Tokens

The source of truth is `tokens/tokens.json`. It is mirrored to CSS custom properties in `tokens/tokens.css` and exposed through `tailwind.config.ts`.

- **Only tokens exist.** The Tailwind `theme` is *replaced*, not extended, so `bg-red-500`, `text-[13px]` and `p-7` don't compile. Inline `style` is allowed only for data-driven geometry, such as the left and width of a range band.
- **Themes.** Light is the default. Dark applies with `data-theme="dark"`, or through `prefers-color-scheme` when no theme is set. Components never branch on theme, because every token swaps underneath them.
- **Contrast.** Every text/ground pair was measured, and the ratios are written beside each value in `tokens.json`. The lowest body-text pair is `ink-subtle` on `sunken`, at 5.11:1 in light and 6.24:1 in dark. UI boundaries (`border-strong`, `hist-solid`, focus) are all at or above 3:1. If you change a value, re-measure it.

### Colour meaning

| Role | Light | Why |
|---|---|---|
| Historical preparation | warm umber (`hist-*`) | Recalls iron-gall ink and aged paper. Its fill is **lighter** (L≈0.26). |
| Modern preparation | cobalt (`mod-*`) | Cool and clinical. Its fill is **darker** (L≈0.09). |
| Unknown | warm grey + hatch (`unk-*`) | Neutral: not empty, not zero, not alarming. |
| Provisional (AI reference) | violet (`prov-*`) | Its own hue, so "not human-checked" can't be confused with either preparation family. |
| Toxicity | deep red (`tox-*`) | Reserved: it appears nowhere else, including error states. |

**Never colour alone.** Historical and modern are the one pair that most often sits side by side, so they are told apart in four ways:

1. hue (orange vs blue, which works for colour-blind readers)
2. lightness: historical is always the lighter fill in both themes
3. marker shape: ■ for historical, ● for modern
4. a written label

Red/green is never used as a pair.

### Type scale

The scale runs at a ratio of about 1.2 from a 15px data base: 12 · 13 · 15 · 17 · 20 · 24 · 30 · 38. Nothing is smaller than 12px. Historical passages use 17/26 serif and are capped at 68ch. Numbers use tabular figures throughout, and ranges in tables use Plex Mono so their en-dashes line up.

### Space, radius, elevation

- **Spacing** is on a 4px grid.
- **Radii** are small (2, 4 and 6px) for a printed-page feel. Fully rounded pills are used only for status badges and filter chips.
- **Elevation** has three levels and mostly relies on borders. Cards are flat. Only hover, popovers and the drawer get shadows.

## 3. Information architecture

There are seven destinations, ordered to follow the argument. Each page answers one question, and that question is printed as the page subtitle (`src/ia.ts`).

| # | Page | The one question it answers |
|---|---|---|
| 1 | Home | What does this tool claim, and how far should I trust it? |
| 2 | Recipe explorer | What did Culpeper and Pliny prescribe, and how was it prepared? |
| 3 | Compare | For one plant, how does the historical preparation differ from modern studies? |
| 4 | Audit | Did modern studies test the preparation the sources described? |
| 5 | Hypotheses | Which preparation–compound pairs are worth re-testing, and why? |
| 6 | Methods & validation | How were names resolved and extraction estimated, and what has a person checked? |
| 7 | Data & licences | Where does every record come from, and can I reuse it? |

`ia.ts` also lists the honesty treatments each page must show. The persistent footer repeats the scope on every page: a research tool, no medical claims, no guidance on preparing or taking any plant.

## 4. Honesty treatments (used the same way everywhere)

General rule: **every status is carried by shape, line style and a written word. Colour is a redundant extra cue.** Labels are always printed. Tooltips explain but never hold the only copy of a fact, so they can be hover-free on touch screens and readable in print.

1. **Evidence status: `EvidenceStatusBadge`.**
   - Validated: filled disc with a tick, solid border.
   - Provisional: half-filled disc, dashed violet border.
   - Pending: dashed ring, dotted grey border.
   - The badge is a real button, so the tooltip opens on keyboard focus.
   - The provisional copy says plainly: "AI-generated reference. Not yet checked by a person."
2. **Source confidence: `SourceConfidenceMarker`.**
   - One marker per source. There is deliberately no combined confidence score.
   - Higher confidence: two filled pips, solid border. Lower: one pip, dashed border.
   - Pliny's marker carries its disputed share ("70% of resolved names disputed").
   - Both sources use the historical family, so the meter, not colour, carries the level.
3. **Disputed names: `DisputedName`.**
   - The source's own word leads, in quotation marks and serif italic, because it is a historical string rather than a taxon.
   - A state line follows: Resolved, Disputed (not settled), Genus only, or Unresolved.
   - Every candidate is listed with its own confidence range and evidence status, at **equal visual weight**: no bold winner and no pre-selection.
   - Genus-only names print "*Mentha* sp.", and we never invent a species epithet.
4. **Likelihood with range: `LikelihoodBar`.**
   - The low–high band is the main mark. The point estimate is a thin tick on the band.
   - The printed text leads with the range ("0.33–0.66"), with the point second and muted.
   - The bar has quarter ticks but no gridlines or percentages, to avoid false precision.
   - A wide band is drawn at the same weight as a narrow one, because a wide band is a finding too.
   - Tables sort by range midpoint, and the column header says "range, 0–1".
5. **Extraction vs detection: `ExtractionDetectionExplainer`.**
   - Every likelihood is labelled "Predicted extraction" by default.
   - The inline variant is a sentence with a disclosure. It sits under every chart or table of likelihoods.
   - The panel variant shows the chain: plant content → **extraction** → lab detection. Only the middle step is drawn solid, because it is the only step we model.
6. **Heuristics: `HeuristicMarker`.**
   - Marked with a hollow diamond, the small-caps word *heuristic* and a dashed underline on the value it affects.
   - It uses ink only, with no new hue, so it reads as an annotation rather than a category.
   - Its tooltip states the rule and the words "not a measurement".
7. **Toxicity: `ToxicityBadge` and `ToxicityNotice`.**
   - **Toxicity reported** is the only filled, high-contrast badge in the system.
   - **Concern** uses the same red as an outline.
   - **No toxicity reported** is neutral grey with an empty-square glyph, never green or a tick. Its sources panel says "This is not evidence of safety."
   - **Data lacking** uses the hatch, and **Unknown** uses the standard unknown treatment.
   - Sources open in a click-to-open panel rather than a tooltip, so links can be clicked on touch screens.
   - **Rule for toxic plants:** `ToxicityNotice` replaces any call to action ("explore", "compare", "re-test") on a toxic-reported card or hypothesis. The copy says it is a historical record for analysis only, not a preparation to make or take.
8. **Unknown: `UnknownValue`.**
   - Shown as the word "Unknown" with a dashed-square "?" glyph in neutral grey.
   - Never blank, "—", 0, "N/A" or red.
   - It sorts last in both directions.
   - Every filter facet that can be unknown has an "Unknown (n)" chip.
   - `filtered: null` prints "filtering not stated" rather than guessing.
   - "Unknown" (a value in the data) and "Empty" (no results for a query) look different on purpose.

## 5. Base components

- **Button.** Three variants: primary (inverted ink), secondary and ghost. The primary is ink rather than a brand colour, so it never competes with the meaning colours. Heights are 32, 40 and 48px.
- **Tabs.** WAI-ARIA tabs with arrow, Home and End keys. Selection is shown by weight and an underline, not colour. Counts include unknowns.
- **DataTable.**
  - Journal style: hairline rules, no zebra striping, no vertical lines, a sticky sunken header and right-aligned mono numbers.
  - Unknowns sort last.
  - It scrolls horizontally in its own box on narrow screens.
- **FilterGroup and FilterSummary.**
  - Real checkboxes in a fieldset, with counts on every chip.
  - The "Unknown" chip is dashed.
  - The summary always says how many records are hidden and offers to clear the filters.
- **SearchField.** Has a visible label and a hint that teaches historical-spelling matching.
- **Drawer.** For record detail. It is modal, traps Tab, closes on Escape, returns focus when closed, and is full width below 640px.
- **Tooltip.** Opens on hover and focus, closes on Escape, and is linked with `aria-describedby`.
- **Card and SourcePassage.** Cards are flat. The `meta` row of honesty badges sits **directly under the title**, so status is read before the content. Passages are serif with a citation line.
- **EmptyState, LoadingState, ErrorState.**
  - Errors use ink with a cross glyph, never toxicity red, so a failed request can't look like a toxicity signal.
  - Loading uses skeleton bars that respect reduced-motion settings.
- **PrepTag and PrepLegend.** Historical tags are warm, marked ■ and use serif italic for the vehicle name. Modern tags are cool, marked ● and use sans. The legend appears once on any view that mixes the two families.
- **AppShell.** The seven IA links, the page question as subtitle and the scope footer.

## 6. Accessibility

- Text meets 4.5:1 and UI boundaries meet 3:1, in both themes.
- Focus is a 2px `focus` outline with a 2px offset, visible on every control.
- Interactive elements are real elements (`button`, `a`, `input`, `label`, `details`/`summary`). Clickable table rows are focusable and open on Enter or Space.
- Charts use `role="img"` with a spoken range ("between 0.33 and 0.66, point estimate 0.50, range width 0.33"). Every chart also has a "View as table" data-table fallback (`ChartTable`).
- Motion respects `prefers-reduced-motion`.
- Tooltips open on hover, focus **and** tap. Drawers trap focus, make the page behind them inert, lock background scroll and return focus to their trigger.
- §11 has the Phase 4 audit and how to re-run it (`npm run review`).

## 7. Content rules (for copy in every phase)

- Never use "works", "safe", "effective", "cures", "treats" or "recommended". Use phrasing like "predicted to extract", "reported", "worth re-testing".
- Never show an accuracy, precision or validation percentage that looks real. Mock data uses repeating-digit placeholders (0.11, 0.22, 0.33…) and `[MOCK]` labels.
- Historical passages in the mocks are placeholders, not quotations. The real text comes from the project's transcriptions, with an edition citation.

## 8. Files

The folder structure, run instructions and every dependency version are in **README.md**. Typecheck with `npm run typecheck`. It passes with `strict` on, and every Tailwind class used compiles against the token-only theme.

## 9. Phase 2: core screens

Files: `src/screens/{Home,RecipeExplorer,RecipeDetail,Compare,App}.tsx`, with mock data in `src/screens/mock.ts`. The screens compose Phase 1 components only. Where a screen needs a new arrangement, such as passage spans, the drivers list or the verdict, it is built locally inside that screen from Phase 1 tokens and components. No new tokens and no new component types were added.

New shapes were added to `src/types.ts` and are still **assumed**, because the schemas have not arrived:

- `Passage` with `ExtractedField` offsets and `IllegibleSpan`
- `Recipe`
- `SpeciesProfile`, `PreparationProfile`, `CompoundEstimate` and `Driver`
- `heat` and `duration` on `Preparation`

New routes, as children of the Phase 1 IA: `/recipes/:id` and `/compare?species=`.

### Home

- **The artemisinin story is labelled "motivation, not proof".** It is told in three panels: the plant was right → the preparation was wrong → reading the recipe again.
- **The caveat sits inside the story block,** not in a footnote. It says this is one case and does not show that other recipes hide overlooked preparations.
- **Every claim in the panels is sourced** to Tu (2011), *Nature Medicine* 17:1217–1220. Please have the historian check the wording of panels 1 and 3.
- **Three entry points:** Recipe explorer, Compare and Hypotheses.
- **A "Before you read any number" block** answers the Home question from the IA. It shows evidence-status counts (mock), the two source-confidence markers and the extraction≠detection chain.

### Recipe explorer

- **Search plus five facets:** plant, source, solvent, heat and filtration.
- **Every facet has a "Not stated" or "Unknown" chip with a count,** and counts update against the other active filters.
- **Plant includes a "Disputed name" value,** so disputed recipes can be found, or excluded on purpose.
- **Results are a list of cards rather than a table,** so each row stacks cleanly at 390px.
- **Below 900px, filters collapse** behind a "Filters (n)" button that shows how many are active.

### Recipe detail

- **The passage is the main object.** Each extracted field is a numbered, underlined span on the historical tint. The same number appears in the "Extracted fields" table.
- **Hovering or focusing either the span or its row highlights both.**
- **Spans are buttons, so keyboard users reach every field.** Each one has a spoken label ("Field 3: Heat, 'boiled'").
- **Illegible text is shown as ⟦?⟧ in the neutral unknown style,** with its estimated length, or "length unknown". The text is never silently closed up. The legend under the passage repeats this, so it is not tooltip-only.
- **Fields the source doesn't state** (for example, Quantity) are listed as "Not stated in source". Fields that couldn't be normalised say "Could not normalise".
- **Disputed names get no single "Compare" link.** The page offers one link per candidate instead ("candidate 1 of 3"). Genus-only candidates say there is no species-level profile.
- **Toxic-reported plants get no Compare link at all;** the toxicity notice replaces it.

### Compare (signature view)

- **One species, two preparations (A and B).** Each comes from a recipe (with its source-confidence marker) or from a modern study citation.
- **Compounds are grouped by class.** Each row pairs two LikelihoodBars on the same 0–1 scale.
- **"Enriched here" appears only when the two ranges do not overlap at all,** and touching counts as overlap (`compareRanges` in `lib/format.ts`). The point estimate never decides it. Otherwise the row says:
  - "Ranges overlap · no clear difference"
  - "Can't compare · a range is unknown"
- **The drivers breakdown covers solvent, heat, filtration and acidity.** For each driver it shows a direction (raises / lowers / little effect / unknown) and a strength word, but no fake magnitudes.
- **Heat and acidity carry the heuristic marker.** The panel ends with "Drivers explain the predicted extraction. They say nothing about how much of the compound the plant contained."
- **Drivers open by hover preview on pointer devices, or by tapping or clicking to pin.** Both open the same inline panel, so it works on touch screens.
- **The profile header states which recipes link to the species,** including that "absinthium" is candidate 1 of 3 and disputed.
- **Profiles load per species.** Changing the species shows a skeleton that announces itself to screen readers. A genus-only choice (*Mentha* sp.) shows an error explaining that no species-level profile exists.

### Responsive (390px)

- **Layouts reflow by themselves** using `flex-wrap` and `repeat(auto-fit, minmax(min(Npx, 100%), 1fr))` grids, so the canvas mocks work without media queries. The React code uses the Tailwind `md`/`lg` breakpoints for the same behaviour.
- **The navigation rail becomes a two-column link grid** above the content.
- **Wide tables** (the extracted fields and species candidates) scroll inside their own box. The page itself never scrolls sideways.
- **Every tap target is at least 32px tall,** and 40px for primary controls.

## 10. Guardrails for the build agent

- Don't add a colour, size or shadow. Add a token instead, and record its contrast.
- Lint rule to add: reject `className` values containing `[#`, `[0-9]+px]` or Tailwind default palette names.
- Never render a likelihood without its range, or a likelihood chart without the inline extraction explainer.
- Never render a name resolution without its state line.
- Every toxic-reported plant's card or row must render `ToxicityNotice` and no call to action.
- Never mark a compound "enriched" unless `compareRanges` says the ranges don't overlap.
- Never collapse a disputed name to one species for Compare. Offer each candidate separately.
- Every chart gets a `ChartTable` fallback. Every wide table uses `DataTable` (which stacks into cards on phones) or keeps every column visible at 390px.
- Run `npm run review` before every merge. It must report zero.

## 11. Phase 4: strict review log

### How it was reviewed

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

### Result

| Check | Before fixes | After fixes |
|---|---|---|
| axe violations (WCAG A/AA, both themes) | 0 | **0** |
| Horizontal page overflow | 22 page states | **0** |
| Focus stops without a visible indicator | 0 | **0** |
| Dialog focus trap / return | not tested | **pass** |
| Runtime errors | 0 | **0** |

axe passed even before the fixes. Most of the issues below were found by code review and the screenshots, which is why the review doesn't rely on automated testing alone.

### Issues found and fixed

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

### Not verified (please test before release)

- No manual screen-reader pass (NVDA, JAWS or VoiceOver) has been done. Automated checks and code review cannot replace it.
- axe cannot measure contrast over the hatched "unknown" fills. Those text/ground pairs were checked by script instead (`unk-fg` on `unk-bg`: 5.59:1 light, 6.75:1 dark).
- **The canvas mocks are a visual reference, not production code.** Items 23–25 were mirrored there, but the "View as table" fallbacks and the mobile card tables exist only in the React code. The React code is the source of truth.
- PubMed links built from the placeholder PMIDs (`0000000n`) don't resolve.
- At 390px, the native Compare preparation `<select>` truncates long option labels. The full label is repeated in the tag below it.
