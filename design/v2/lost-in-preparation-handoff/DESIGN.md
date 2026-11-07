# Lost in Preparation: Design (v2)

A preparation-aware research tool for EthnoHack 2026, Track 1.

> **Historical remedies were recipes, not just plants. See what each preparation actually extracts.**

v2 turns the Phase 1–4 report into a product. The data contract, the eight honesty treatments and the accessibility standard are unchanged. The experience, the information architecture and the visual identity are new.

**Assumption.** The project's JSON Schemas were never attached. `src/types.ts` is the design's assumed contract. v2 changes it only by adding things (§9). When the real schemas arrive, generate types from them and adapt the small mapping at the top of each honesty component.

Contents:

1. Positioning
2. Visual identity: two themes
3. Tokens
4. Information architecture
5. Screens
6. Honesty treatments, v2 forms
7. Components
8. Motion
9. Contract additions
10. Content rules
11. Guardrails for the build agent
12. v2 review log

---

## 1. Positioning

| | |
|---|---|
| **What it is** | A research tool. It turns historical recipes into testable hypotheses about extraction. |
| **Who it serves** | Pharmacognosists, historians of medicine (including Byzantine pharmacology) and data scientists deciding what a lab should re-test. |
| **What it is not** | A remedy finder. It makes no medical claims and gives no guidance on preparing or taking any plant. The footer on every page says so. |
| **How it earns trust** | Every number shows how far to trust it: ranges rather than points, Unknown left visible, disputes left open, and the negative results printed. |

---

## 2. Visual identity: two themes

You chose both directions, each as a theme. The reader picks one with the header toggle; the choice is saved in `localStorage` under `lip-theme`. When nothing is saved, the system preference decides.

| | **Herbarium** (light, Direction A) | **Nocturne** (dark, Direction B) |
|---|---|---|
| Mood | Warm paper, pressed specimens, an apothecary's ledger | An archive at night, a lit specimen cabinet |
| Ground | Paper `#F5F0E4`, surface `#FBF8F1` | Aubergine-black `#120E16`, surface `#1C1621` |
| Ink | Aubergine-ink `#241A28` | Parchment `#F3ECE0` |
| Brand | Botanical green `#2E5A43` | Verdigris `#7DC2A6` |
| Display face | **Fraunces** (variable optical size, set at 144) | **Instrument Serif** (scaled ×1.12) |
| Text face | **Instrument Sans** | **Hanken Grotesk** |
| Numbers | **JetBrains Mono** | **DM Mono** |
| Signature | Plates on saffron-tinted mounts | Plates on dark mounts, with a faint saffron glow on hover |

- **One component set, two themes.** The two themes swap CSS variables only, including the font families (`--f-display`, `--f-sans`, `--f-mono`) and `--display-scale`. There is no theme-specific markup. Tailwind display sizes are `calc(Npx * var(--display-scale))`, so Instrument Serif's smaller x-height matches Fraunces's visual size, which limits layout shift when the theme changes.
- **Botanical plates.** These are public-domain 19th-century plates from Wikimedia Commons. Köhler's *Medizinal-Pflanzen* (1887) is suggested but not yet confirmed. Every image slot (`PlateSlot`) prints its licence, its host and its sourcing status. Until a file is chosen and its licence checked, the slot shows an original line drawing (`LeafDrawing`). The `plates.json` contract field records the status: `to_source`, then `sourced`, then `confirmed`.
- **Fonts.** All six families are vendored as woff2 files in `assets/fonts/`, under the SIL OFL 1.1, with the licence files included. Nothing is loaded from a CDN.

---

## 3. Tokens

`tokens/tokens.json` is the source. `tokens/tokens.css` defines the variables, and `tailwind.config.ts` replaces Tailwind's defaults with tokens only. Every colour has a single meaning:

| Token | Meaning | Light | Dark |
|---|---|---|---|
| `hist` | **The historical preparation.** Saffron, drawn as a *filled* band. | fill `#E0A33A`, edge/text `#83560A` | `#F2B544` |
| `mod` | **The modern lab method.** Drawn as an *outline* band. | `#5B3F7A` (aubergine) | edge `#B9A2E6`, fill `#8B6CCB` (lilac) |
| `tox` | **Toxicity only.** | `#9B2335` (crimson) | `#F4A3AD` (rose) |
| `unk` | **Unknown.** Neutral, with a hatch. | `#5C5754` on `#E8E2DA` | `#B3AAA6` on `#231D25` |
| `prov` | **Provisional evidence.** Neutral and dashed, deliberately not the modern hue. | `#57495A` | `#BFB3C2` |
| `brand` | Wayfinding only: links, primary buttons, focus. **Never means "safe".** | `#2E5A43` | `#7DC2A6` |

Rules behind the palette:

- **Historical and modern differ in three ways, not by hue alone:** fill versus outline, lightness, and a legend. This holds for red–green colour blindness and in greyscale.
- **The light saffron fill is only 1.75:1 on paper.** It therefore always carries its `hist-edge` border, and its text uses `hist-fg` (6.0:1).
- **Contrast.** Every text pair passes 4.5:1 and every UI boundary passes 3:1 in both themes. The pairs were checked by script, and axe checks them on every screen (§12).
- **Spacing.** The base is 4px. v2 adds 3.5, 7, 9, 11, 14 and 28, which are used for control heights (28/36/44), section padding (56) and the sticky offset (112).
- **Radius.** sm 4, default 8, md 12, lg 16, xl 22. Pills are `full`.
- **Elevation.** Levels 1–3 in both themes, plus `glow` in dark only.
- **Motion.** Durations are fast 140, base 240 and bar 480 ms. All are 0 under reduced motion (§8).
- **Type scale.** xs 12, sm 13, base 15, md 17, lg 20, xl 24, 2xl 32, 3xl 44, 4xl 60, 5xl 76.

---

## 4. Information architecture

The front door is the promise and a live demo. Methods & data is reached last, as documentation.

| # | Page | Path | Question it answers |
|---|---|---|---|
| 1 | Landing | `/` | What does each preparation actually extract? |
| 2 | Preparation Lab | `/lab` | If I change the solvent, heat, filtration or acidity, what happens to the profile? |
| 3 | Recipe Atlas | `/atlas`, `/recipes/:id` | What did Culpeper and Pliny prescribe, and how was it prepared? |
| 4 | The evidence gap | `/evidence-gap` | How often do modern studies say how they prepared the plant? |
| 5 | Case study | `/case/liquorice` | What changes when a liquorice recipe is read as a recipe? |
| 6 | Lab Planner | `/planner` | Which experiments should a lab run first? |
| 7 | Methods & data | `/docs` | How was this produced, how far has it been checked, and can I reuse it? |

- **Navigation.** A sticky header holds the wordmark, six links and the theme toggle. Below 1200px the links move into a menu disclosure.
- **Footer.** It states the scope ("No medical claims; no guidance on preparing or taking any plant").
- **Old v1 paths redirect:** `/recipes` → `/atlas`, `/compare` → `/lab`, `/audit` → `/docs` (studies), `/hypotheses` → `/planner`, `/methods` and `/data` → `/docs`.

---

## 5. Screens

Screenshots of every screen are in `screens/`, in both themes at 1440 and 390, and on canvas page 5.

### 5.1 Landing
- **Hero.** The promise in the display face, with the word *recipes* in the brand colour and italic. Two actions: Open the Preparation Lab (primary) and Explore recipes.
- **Live mini-demo.** Real Lab data for liquorice. "Cold water" and "Decoction" are a segmented control, and the bars animate between them. An "Overlay modern lab method" checkbox adds the outline band. Below sit the extraction ≠ detection chip and the label "mock values · scale 0–1".
- **Three ways in.** Plate cards for Explore recipes, Preparation Lab and The evidence gap, followed by the plate licence line.
- **Evidence gap teaser.** "11 of 111" with its interval and evidence status.
- **"Honest by design" panel.** Shows the real badges as they appear in the product.
- **Case study teaser.**

### 5.2 Preparation Lab (the signature view)
- **Controls.** These sit in a sticky panel on desktop and stacked on phone.
  - Plant select.
  - Solvent: Water / Wine / Vinegar / Oil / Honey.
  - Heat: Cold / Warm / Boiled.
  - Filtration and Acidity switches. Vinegar locks acidity on and says why.
  - "Compare with modern lab method" switch.
- **Profile.**
  - Compounds are grouped by class. Each has a `LikelihoodBar` with its range and, after a change, a delta chip: ↑ higher, ↓ lower, or ≈ overlaps. The delta is computed by `compareRanges` against the last setting that had data.
  - **"Why?"** on every compound opens a popover listing the drivers (solvent, heat, filtration, acidity). Each driver shows its effect and strength. Heuristic drivers carry the heuristic marker, and drivers that changed since the last setting are highlighted.
- **Designed states:**
  - **Loading:** skeleton bars, `aria-busy`.
  - **No data for this combination:** the Lab never interpolates. It says no modelled estimate exists and offers the combinations that do exist as buttons.
  - **Genus-only plant** (Mentha sp.): no profile. It explains why and links to the recipe.
  - **Wide uncertainty:** a banner appears when the mean range width is 0.4 or more (honey is wide on purpose in the mocks).
  - **Toxic plant:** a `ToxicityNotice` above the profile, and no "Plan an experiment" action.
- **Accessibility.** A live region announces each change, and the profile has a "View as table" fallback.

### 5.3 Recipe Atlas and recipe pages
- **Atlas.** Search-first, with historical spellings matched. Filter chips: Culpeper, Pliny, Disputed names, Heat stated, Strained. Plant cards carry the plate, the historical name → taxon, counts per source and the toxicity badge. A disputed name prints "3 candidates · disputed" with a candidate strip, never one species.
- **Recipe page.**
  - **The passage.** Set in the display face. Extracted fields are highlighted and numbered, and hovering a field lights its card. Illegible stretches show as ⟦?⟧ buttons.
  - **Extracted fields.** One card per field, with its evidence status and "as written". Kinds missing from the passage print "Not stated in source".
  - **Aside.** The plate, `DisputedName` (expandable, every candidate at equal weight with its range), the preparation, and "Open this preparation in the Lab", which carries the settings in the URL. Disputed names get one Lab link per candidate.

### 5.4 The evidence gap
- **Headline.** "11 / 111 studies state whether the plant was fresh or dried", with its 95% interval.
- **One row per preparation detail.** Solid = stated, hatched = not stated (unknown, never zero), whisker = 95% Wilson interval. Hover, focus or tap a row for n and the interval. The order can be switched between least and most reported. Every chart has a table fallback.
- **"When they did say, did it match the recipe?"** Culpeper and Pliny are shown separately: same / different / not stated strips for solvent, heat and filtration, each with a table. A link leads to every study, field by field.

### 5.5 Case study: liquorice
- **Four chapters:** the misreading, the evidence, the correction, the new result. The copy is marked **[MOCK STORY]**: the structure and tone are final, but the claims must come from the team's own analysis.
- **Figures.** On desktop the figure is sticky and follows the active chapter (IntersectionObserver). On phone each chapter carries its figure inline.
- **Ending.** It closes on a `ToxicityNotice` (a concern is recorded for liquorice) and a sentence saying the page analyses a recipe and does not suggest preparing or taking liquorice.

### 5.6 Lab Planner (placeholder for the quantum feature)
- **"Coming in this release" panel** for *Quantum-informed priority*. It has a disabled switch and the line "the order below never uses it".
- **Ranked experiments.**
  - Each shows its rank and the range of ranks the uncertainty allows ("could be 2–4"), what is compared, and the hypothesis's `LikelihoodBar` with the modern overlay.
  - Readout and effort are shown, or "Not decided" / "Not estimated" when missing.
  - **The Quantum priority field shows "Coming in this release"; it is never 0 and never a fake score.**
  - An "Evidence trail" drawer shows the six steps from source to toxicity check.
- **Withheld leads.** Leads with *toxicity reported* are withheld from planning, and a note counts and names them.

### 5.7 Methods & data (documentation)
- **Navigation.** A sticky table of contents on desktop (it highlights the current section) and wrapped links on phone.
- **Sections:**
  1. Overview: counts, both source markers, the extraction ≠ detection panel.
  2. Pipeline: seven steps with evidence status.
  3. Step metrics: point **with** interval and n; "Not measured" where missing.
  4. Honest findings: xTB versus RDKit, with its pre-registered **Fail**; the artemisinin positive control, **Borderline**.
  5. Pre-registered checks.
  6. Heuristics.
  7. Audited studies: field by field, with "Not stated" cells and match chips (`id="studies"`).
  8. Limitations.
  9. Sources & licences, each licence with its own status.
  10. Downloads: all 12 contract files.

### 5.8 Phone (390px)
Every screen stacks to one column, with no horizontal page scroll (checked automatically). Wide tables become labelled cards (`DataTable`) or scroll inside their own focusable region (`ChartTable`). The navigation becomes a menu, and controls keep their desktop heights (36–44px).

---

## 6. Honesty treatments, v2 forms

The rule from Phase 1 still holds: **every status is carried by shape, line style and a written word; colour is a redundant extra cue.** What changed in v2 is the form, not the meaning. Treatments are now compact pills with a popover for the detail, so the screen stays calm and the reader opts in to the explanation.

| # | Treatment | Component | v2 form |
|---|---|---|---|
| 1 | Evidence status | `EvidenceStatusBadge` | Pill. **Validated**: solid border, filled disc with a tick. **Provisional**: dashed neutral border, half disc. **Pending**: dotted, empty ring. A tooltip explains each ("AI-assisted reference, not yet checked by a person. Read it as a lead, not a finding."). |
| 2 | Source confidence | `SourceConfidenceMarker` | A specimen tag in the display italic, with pips (●● higher, ●○ lower). **Culpeper and Pliny are always separate.** Pliny's tag prints "70% of resolved names disputed". There is no combined score anywhere. |
| 3 | Disputed names | `DisputedName` | The source's word, in quotes and italics, then "→ 3 candidates · disputed" with a candidate strip. It expands to list every candidate at equal weight with its range, sorted by the low end of the range. Genus-only names print "*Mentha* sp.". The name is never shown as settled. |
| 4 | Ranges | `LikelihoodBar` | The band is the mark and the point is a thin tick. Range text comes first in mono ("0.33–0.55 · pt 0.44"). The modern overlay is an outline band. The `aria-label` speaks both ranges. Tables sort by range. |
| 5 | Extraction vs detection | `ExtractionDetectionExplainer` | A chip ("Extraction ≠ detection") with a popover, placed next to every profile. A panel version shows plant content → **extraction** → detection, with only the middle step modelled. |
| 6 | Heuristic | `HeuristicMarker` | A hollow diamond, the small-caps word *heuristic* and a dashed underline. The popover gives the rule and "not a measurement". |
| 7 | Toxicity | `ToxicityBadge`, `ToxicityNotice` | **Reported** is the only filled crimson pill. **Concern** is a crimson outline. **No toxicity reported** is neutral with an empty-square glyph (never green or a tick), and its popover says "not evidence of safety". **Data lacking** is hatched. **Unknown** uses the standard unknown treatment. The source count is on the pill and the sources are in the popover. **Toxic-reported plants never get a "try", "plan" or "explore this preparation" action; `ToxicityNotice` replaces it.** |
| 8 | Unknown | `UnknownValue` | The word (or "Not stated", "Not decided", "Not measured") with a dashed-square glyph in neutral grey. It is never 0, "—", blank, "no" or red, and it sorts last. In charts it is the hatch. |

---

## 7. Components

`src/index.ts` exports everything. New or rewritten in v2:

| Component | Role |
|---|---|
| `SiteShell`, `PageHeader`, `ThemeToggle` | Header, navigation, menu disclosure below 1200px, footer, theme toggle (`aria-label` "Switch to Nocturne (dark) theme"). |
| `SegmentedControl` | `radiogroup` with arrow, Home and End keys. Used for solvent, heat, demo preparation and sort order. |
| `Switch` | `role="switch"` with an optional state word ("Strained" / "Unstrained"). |
| `Popover` | Click disclosure (`aria-expanded`, `aria-controls`). Escape closes it and returns focus, an outside click closes it, and it is clamped to the viewport. Used for every honesty detail that holds links. |
| `Button`, `LinkButton` | Pill-shaped. Variants: primary (brand), secondary, ghost. Sizes: sm, md, lg. |
| `PlateSlot`, `LeafDrawing` | Illustration slot with licence caption. Sizes: thumb, card, hero. |
| `PlantCard` | Atlas card with a stretched link. Its badges stay interactive above the link. |
| `PrepTag`, `PrepLegend`, `MarkHist`, `MarkMod` | Preparation chips and the legend: saffron filled = historical, outline = modern, hatch = unknown. |
| `EmptyState`, `LoadingState`, `ErrorState` | Errors use ink with a cross glyph, never toxicity red. |

Carried over from Phase 4 unchanged: `Tooltip`, `Drawer`, `DataTable`, `ChartTable`, `Tabs`, `FilterGroup`, `SearchField`, `Taxon`, `UnknownValue`.

`#/gallery` shows every component in every state, with the theme toggle.

---

## 8. Motion

- **Bars animate when their range changes** (`.bar-motion`: left, width and opacity over `--d-bar`, 480ms, `cubic-bezier(.2,.7,.2,1)`). This is the only motion that carries meaning: you see what the preparation change did.
- **Smaller motions:** popovers and the case-study figure fade in (`.fade-in`, 240ms), and the evidence-gap rows animate in with a 40ms stagger.
- **Reduced motion.** Under `prefers-reduced-motion: reduce` every duration token is 0ms, so values swap instantly, and `.fade-in` is disabled. Nothing depends on motion to be understood.

---

## 9. Contract additions (additive only)

Existing files and fields are unchanged. New fields are optional, and new files are separate.

| Change | Type | Why |
|---|---|---|
| `Vehicle` gains `'water'`, `'honey'` | union | Lab solvents |
| `Preparation.acidified?: boolean \| null` | optional | Lab acidity toggle (null = not stated) |
| `Study.material?: StatedField<'fresh' \| 'dried'>` | optional | Evidence gap headline |
| **`reporting_gap.json`**: `ReportingGapFile` | new file | Evidence gap rows: stated, n and Wilson CI per detail |
| **`plates.json`**: `Plate[]` | new file | Illustration slots, each with licence, host and status |
| **`lab_plan.json`**: `LabPlanFile` | new file | Lab Planner. `quantumScore` is always null until the feature ships. |

`species_profiles.json` now includes every Lab combination (ids such as `water-boiled-f-n`, `vinegar-boiled-f-a`) plus `modern-methanol` per plant. A combination that is absent means *no estimate*: the Lab says so and never interpolates.

---

## 10. Content rules

- **Never** "works", "safe", "effective", "cures", "treats", "heals" or "recommended". Use phrasing like "predicted to extract", "reported", "worth re-testing", "a hypothesis for the lab, not a finding".
- **Obviously fake numbers only:** repeating digits (0.11, 0.22…), counts like 11/111, `[MOCK]` prefixes, PMIDs `0000000n`. Never a figure that looks like a real accuracy.
- **Passages and the case study are placeholders**, not quotations: `[MOCK]` and `[MOCK STORY]`.
- **Plain language.** Use "Not stated in source" instead of "null", and "Range" instead of "CI" in the Lab (the 95% interval is named where it is a real statistic).

---

## 11. Guardrails for the build agent

1. **Tokens only.** A new colour or size goes into `tokens.json`, `tokens.css` and `tailwind.config.ts`, with its contrast recorded for **both** themes.
2. **Null means unknown.** Never render null as 0, "—", blank, `false` or "no".
3. **Ranges first.** "Higher", "lower" and "overlaps" come only from `compareRanges`.
4. **Never merge Culpeper and Pliny.** Never collapse a disputed name.
5. **Toxicity reported means `ToxicityNotice` and no action.** The Lab hides "Plan an experiment" and the Planner withholds the lead.
6. **The Lab never interpolates.** A missing combination is a designed state.
7. **The Planner's quantum column is "Coming in this release" until the feature ships.** Never a 0, never a placeholder score.
8. **Every image slot shows its licence and host.** Don't ship a plate whose Commons file and licence haven't been confirmed by a person (`status: 'confirmed'`).
9. **Both themes are first-class.** Test every change in Herbarium and Nocturne.
10. **`npm run review` stays at zero** (§12).

---

## 12. v2 review log

### Method
- **Automated (`npm run review`, `tests/review.mjs`).**
  - Covers 15 routes: the gallery, all 7 pages, 4 Lab states and 3 recipe variants. Each runs in Herbarium and Nocturne at 1440 and 390, giving 60 page states.
  - Also covers 17 opened states per theme and width: Lab toggles, the "Why?" popover, the modern overlay, Atlas filters, the illegible-text tooltip, evidence-gap tooltips, the Planner drawer, the gallery drawer and popover, and every table fallback.
  - Checks run: axe-core 4.10 (WCAG 2.0/2.1 A + AA, contrast included), horizontal-overflow detection, a focus-visibility walk at 1440 light, and dialog focus trap and return.
- **Visual review** of full-page screenshots, all saved in `screens/`.
- **Copy scan** for medical-claim and hype words.

### Result

| Check | First run | Final |
|---|---|---|
| axe violations | 38 | **0** |
| Horizontal page overflow | 0 | **0** |
| Focus stops without a visible indicator | 0 | **0** |
| Dialog focus trap / return | pass | **pass** |
| Runtime errors | 4 (harness selector) | **0** |

### Issues found and fixed

| # | Issue | Fix |
|---|---|---|
| 1 | **Spacing classes silently missing.** The token-only theme had no 3.5, 7, 9, 11, 14 or 28. Section padding (`py-14`), control heights (`h-7`, `h-9`, `h-11`) and the sticky offset (`top-28`) were dropped, so sections touched each other. axe can't see this; the screenshots showed it. | Added those steps to the space tokens (§3). |
| 2 | The toxicity source count used `opacity-80`, which fell below 4.5:1 on the light concern badge. | Full opacity. |
| 3 | The Planner's `<dl>` contained a `<div>` without `dt`/`dd` (the badges). | Now a "Status" `dt`/`dd` pair. |
| 4 | Table fallbacks that scroll sideways on phone were not keyboard-focusable. | The scroll box is `tabIndex=0`, `role="region"`, with a label. The same applies to `DataTable`. |
| 5 | **Mock data contradicted itself.** The Lab's modern method gave glycyrrhizin 0.55–0.77, but the hypothesis said 0.33–0.55, and the case study claimed "entirely above". | The toy model's methanol value for polar compounds was aligned, so the Lab, the case study and the Planner now show the same ranges (decoction 0.66–0.88 against modern 0.33–0.55). |
| 6 | The case study said "rank 4" while the Planner showed the same lead at rank 3 (the toxic lead is withheld there). | The case study now quotes the **Planner** rank, with a comment explaining why the two can differ. The Planner drawer no longer prints the hypothesis rank. |
| 7 | Evidence-trail links pointed to v1 routes (`/recipes`, `/audit`). | They now point to `/atlas` and `/docs#studies`, and the router redirects v1 paths. |
| 8 | The Docs downloads listed the three v2 files without descriptions. | Added them to `sources.json`. |
| 9 | Copy: "How well each step works" ("works" is on the banned list, even though it was about the pipeline). | Changed to "How accurate each step is". |

The v1 log (Phase 4, 29 issues) is kept in `docs/review-log-v1.md`. Its component fixes carried over.

### Not verified (please test before release)
- **Screen readers.** No manual pass with NVDA, JAWS or VoiceOver has been done.
- **Theme switch with motion on.** Swapping the font families causes a small reflow. It is mitigated by `--display-scale` but not eliminated, so check it on real devices.
- **Plates.** No real plate has been sourced. Every slot shows the drawn placeholder and "to source".
- **Case study figures.** The sticky figure relies on IntersectionObserver. In browsers without it, the inline figures (phone layout) are the fallback, but the desktop sticky figure stays on chapter I.
- **Contrast over the hatch.** Unknown fills are hatched, which axe cannot measure. Those pairs were checked by script instead.
- **Placeholder PMIDs** (`0000000n`) don't resolve.
