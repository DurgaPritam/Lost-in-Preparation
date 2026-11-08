# Demo video script, v2 (about 3:05): the whole site, with the quantum work

For the EthnoHack 2026 Devpost video. Read it at a calm, steady pace (about 145 words a minute). Every number comes from `README.md`, `RESULTS.md`, `docs/QUANTUM_RESULTS.md` or `docs/QAOA_v3_RESULTS.md`.

- **Live site:** https://lost-in-preparation.vercel.app
- **Footage (already recorded, no screen recording needed):** eight clips in `~/Desktop/LiP_demo_footage_v2/`. To re-record: `cd site && BASE_URL=https://lost-in-preparation.vercel.app OUT=~/Desktop/LiP_demo_footage_v2 npx tsx scripts/demo-footage.ts` (add `ONLY=atlas,lab` for some clips).
- **Stills:** the deck's cover, quantum and closing slides.

## What to record

Record **11 voice files**, one per shot, and save them in **`~/Desktop/LiP_voice_v2/`** named `01.m4a` … `11.m4a`. Leave about a second of silence at the start and end of each; the edit trims it. Re-record any line you stumble on.

## The script

| # | Name | On screen | Say |
|---|---|---|---|
| 01 | Hook | Deck cover slide | "In the 1970s, a fourth-century recipe led Tu Youyou to artemisinin, and a Nobel Prize. The plant had always been right. The preparation had been wrong. This is Lost in Preparation." |
| 02 | Landing | Landing page: the mini-demo switches cold water to a decoction, then overlays the modern lab method | "Historical remedies were recipes, not just plants. Our model predicts what each preparation extracts. Switch cold water to a decoction and the compound profile changes; overlay the modern lab method and it changes again." |
| 03 | Recipe Atlas | Search “wormwood”, then a liquorice recipe page with the original 1652 passage and the extracted fields | "The Recipe Atlas holds 631 recipes from Culpeper's herbals and Pliny. Every field, the plant, the solvent, the heat, the straining, is backed by a verbatim quote from the source, and every historical name is resolved to an accepted species." |
| 04 | Preparation Lab | Clary sage: cold water, boiled, wine, oil; unstrained; the modern-method overlay | "The Preparation Lab runs our model live in the browser: solvent, heat, straining and acidity as separate factors, every compound with a Monte Carlo uncertainty range. The browser engine reproduces our Python model exactly, and every setting is a shareable link." |
| 05 | Evidence gap | The evidence gap rows, re-sorted, then “did it match the recipe?” | "Then we audited modern studies, under a protocol fixed in advance. The headline is a reporting gap: of 43 studies that prepared the plant, 26% stated the heat, 16% fresh or dried, 12% the filtration, and none stated all five. So most negative results can't tell us whether a remedy was ever tested the way it was made." |
| 06 | Case study and hypotheses | Liquorice case study, then the ranked hypotheses | "We publish our corrections: a logged extraction error changed our top hypothesis, liquorice, and became this case study. The output is a ranked list of hypotheses worth re-testing." |
| 07 | Quantum chemistry | Methods & data: the pipeline, then “Where quantum helps” | "Quantum methods enter twice. First, quantum chemistry: we computed how each compound partitions between oil and water with GFN2-xTB, and tested it against 150 measured values. The classical descriptor was more accurate, so the model uses it, and we say so." |
| 08 | Quantum optimisation | Lab Planner: panel sizes, the suggested panel, its stability, “How the panel was chosen”, then the quantum benchmark at 8, 12 and 16 candidates, and the noise table | "Second, quantum optimisation. Choosing which experiments a lab should run is a constrained selection problem: large robust gaps, broad coverage, little redundancy, and no toxic plants. We wrote it as a QUBO, the native input of quantum optimisers, and solved it exactly for the panel you see. Then we benchmarked QAOA against that exact optimum, with a penalty mixer and with an XY mixer that keeps the panel size fixed by construction. We report the approximation ratio, the chance of sampling the optimum, two-qubit gate counts on IBM's heavy-hex layout, and how fast the signal fades under noise." |
| 09 | Quantum result | Deck quantum slide | "The result: on eight to twelve candidates, QAOA beats random guessing, and our pre-registered version three lifts that to about five times random. But classical annealing finds the optimum every time, and noise erases the signal quickly. So we claim no quantum advantage at this scale; the benchmark is ready for when hardware can run deeper circuits." |
| 10 | Impact and ethics | Impact & ethics page: audiences, the reporting checklist, the terms for traditional knowledge, the next steps | "It's built for natural-product labs, for journals, through a five-item preparation reporting checklist, and for public health. We used only public-domain texts; living traditions would take part on their own terms, under the CARE principles and Nagoya benefit-sharing." |
| 11 | Close | Deck closing slide | "Lost in Preparation. The plant may be right; the preparation may be wrong." |

## Delivery notes

- Say "Q-A-O-A" letter by letter or "kwah-oh-ah"; pick one and keep it. "QUBO" is "KYOO-boh". "GFN2-xTB" is "G-F-N-two, x-T-B".
- Slow down on the numbers in shots 05 and 09; they are the two moments judges remember.
- Never say a remedy "works", "is safe", "is effective", "cures" or "treats". Never say "quantum advantage" without "no" in front of it.

## Checklist before uploading

- [ ] Under the Devpost time limit (this script runs about 3:05).
- [ ] The repository is public (the closing slide shows its link).
- [ ] Upload to YouTube (unlisted is fine) or Vimeo, and paste the link into Devpost.
