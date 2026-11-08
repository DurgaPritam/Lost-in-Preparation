# Demo video script (about 3:00)

For the EthnoHack 2026 Devpost video. It is written to be read aloud at a calm pace (about 140 words a minute), and every number in it comes from `README.md` / `RESULTS.md`.

- **Live site:** https://lost-in-preparation.vercel.app
- **Slides:** the pitch deck (Lost in Preparation — EthnoHack 2026 pitch); only the cover and the closing slide are used in the video.
- **Footage:** six clips in `~/Desktop/LiP_demo_footage/` (1920×1080, no cursor, steady scrolling). To re-record them:
  ```bash
  cd site
  BASE_URL=https://lost-in-preparation.vercel.app OUT=~/Desktop/LiP_demo_footage npx tsx scripts/demo-footage.ts
  # one clip only: add ONLY=impact (or landing, lab, evidence-gap, case-liquorice, lab-planner)
  ```

## Two ways to make it

**A. Narration over the recorded clips (recommended; cleanest result).**
1. Record your voice reading the "Say" column, one shot at a time (QuickTime → File → New Audio Recording, or your phone in a quiet room). Re-record any shot you stumble on; no need to do it in one take.
2. In iMovie (or CapCut, or DaVinci Resolve), put the clips on the timeline in the order below, then each voice recording under its shot.
3. Trim the first 0.5 s of each clip (the page settling), and trim or speed up each clip (up to 1.25×) to fit its voice line. Cut rather than rush the voice.
4. For shots 1 and 9, screenshot the deck's cover and closing slides (present mode, full screen) and use them as stills.
5. Export 1080p and upload to YouTube (unlisted is fine) or Vimeo; paste the link in Devpost.

**B. One live screen recording.**
Press ⌘⇧5, choose "Record Entire Screen", turn on the microphone in Options, and follow the "Show" column on the live site in a full-screen browser window at 100% zoom with the light (Herbarium) theme. Rehearse twice first. Close other tabs, and turn on Do Not Disturb.

## Shot list

| # | Time | Show | Do | Say |
|---|---|---|---|---|
| 1 | 0:00–0:12 | Deck cover slide | Hold | "In the 1970s, Tu Youyou's team couldn't get antimalarial activity from sweet wormwood, until a fourth-century text pointed them away from heat. The result was artemisinin, and a Nobel Prize." |
| 2 | 0:12–0:35 | Clip 1 · landing (`/`) | Mini-demo switches cold water → decoction, then the modern-method overlay | "The plant was right. The preparation was wrong. A historical remedy is a recipe: a solvent, heat, a plant part, fresh or dried, strained or not. Lost in Preparation reads those recipes from Culpeper and Pliny, and asks whether modern science ever tested them the way they were made." |
| 3 | 0:35–1:00 | Clip 2 · Preparation Lab | Clary sage: cold water → boiled → wine → oil → vinegar, then unstrained, then the modern method | "The Preparation Lab models what each preparation extracts, live in your browser. Every compound has an uncertainty range, and the browser engine reproduces our Python model exactly: the build fails if it doesn't. Every setting is a shareable link." |
| 4 | 1:00–1:35 | Clip 3 · Evidence gap | Scroll to the rows, re-sort them | "Then we audited the modern literature, under a protocol fixed before we retrieved a single study. The headline is a reporting gap. Of 43 studies that prepared the plant, only 26% said whether they used heat, 16% whether it was fresh or dried, 12% whether they strained it, and none stated all five. Only about 2% compared two preparations at all. So when a study finds nothing, you usually can't tell whether the remedy was ever tested the way it was made." |
| 5 | 1:35–1:55 | Clip 4 · Liquorice case study | Slow scroll | "We publish our mistakes. An extraction error affected liquorice; we logged the correction, our top hypothesis changed, and it became this case study. Every recipe field traces to a verbatim quote, and every result says how far it has been checked." |
| 6 | 1:55–2:20 | Clip 5 · Lab Planner | Panel size 8 → 4 → 6 → 8, then the benchmark | "The output is a short list of experiments a lab could run: plants never tested the way they were made, chosen by exact optimisation, with toxic species excluded. We benchmarked simulated quantum solvers against the exact answer, and claim no quantum advantage." |
| 7 | 2:20–2:45 | Clip 6 · Impact & ethics | Scroll: audiences → checklist → ethics → next steps | "It's for natural-product labs, for journals, through a five-item preparation reporting checklist, and for public health, because people take teas and decoctions, not lab extracts. We used only public-domain texts. Work with living traditions would follow the CARE principles and Nagoya benefit-sharing, on the community's terms." |
| 8 | 2:45–2:55 | Clip 2 or 1, last seconds (or the Lab, paused) | Hold | "Next: independent checks of our extraction, a partner lab to run the panel, and more traditions, with their own scholars." |
| 9 | 2:55–3:05 | Deck closing slide | Hold | "Lost in Preparation. The plant may be right; the preparation may be wrong." |

## Words to avoid in the narration

Never say a remedy "works", "is safe", "is effective", "cures" or "treats" anything. The outputs are **hypotheses worth re-testing**. If you ad-lib, say "predicted" for the model and "stated" for the audit.

## Checklist before uploading

- [ ] Under 3 minutes (check the Devpost rules for the exact limit).
- [ ] Voice is clearly louder than any background; no music over speech.
- [ ] The live URL is visible at least once (the browser address bar in option B, or the closing slide).
- [ ] Team names on the closing slide.
