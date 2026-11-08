# Devpost submission: Lost in Preparation

Copy-paste text for the EthnoHack 2026 Devpost form. Every number here comes from `README.md`, `RESULTS.md`, `docs/QUANTUM_RESULTS.md` or `docs/QAOA_v3_RESULTS.md`; if those change, re-copy them.

## Submission checklist

| Required item | Where it is |
|---|---|
| Project title | "Project title" below |
| Selected challenge track | "Challenge track" below |
| Team members | "Team members" below: **fill in before submitting** |
| Problem statement | "Problem statement" below |
| Description of the solution | "What it does", "Impact and ethics" |
| Technologies and tools used | "How we built it", "Built with" |
| Data sources and attribution | "Data sources and attribution" below |
| Results and/or prototype description | "Results" below; the live prototype is in "Links" |
| GitHub repository | "Links" (**the repository must be public**) |
| Pitch/demo video (max 10 minutes) | "Links": **add the video URL**; script in `docs/VIDEO_SCRIPT.md` (about 3 minutes) |
| Slide deck (max 10 slides) | "Links": 10 slides, **export as PDF and upload, or share the link** |
| Limitations, assumptions and future work | "Limitations and assumptions", "What's next" |

## Project title

Lost in Preparation

## Challenge track

Track 1: Traditional Knowledge Mining

## Team members

[Name, role, GitHub handle, email for each member: fill in before submitting]

## Tagline (≤ 200 chars)

The plant may be right. The preparation may be wrong. We read historical herbal recipes and audit whether modern studies tested them the way they were made.

## Inspiration

In the 1970s, Tu Youyou's team kept failing to get antimalarial activity from sweet wormwood. Then a 4th-century text by Ge Hong pointed them away from heat. A low-temperature extraction then yielded artemisinin, and a Nobel Prize in 2015. The plant had been right all along; the preparation had not.

That made us ask how often modern studies of traditional remedies test the plant the way the recipe actually prepared it: cold infusion or decoction, wine or water, fresh juice or dried powder, strained or not. And when they don't, can we even tell?

## Problem statement

Traditional remedies are recipes: a plant, a solvent, heat or none, a plant part, fresh or dried material, strained or not. Each choice changes which compounds end up in the preparation. Modern pharmacology usually tests a plant as a standard solvent extract, and rarely reports enough about the preparation to tell whether a traditional remedy was ever tested the way it was made. Artemisinin shows what is at stake: the activity was found only once researchers followed a 4th-century text's preparation and avoided heat. Promising leads may be dismissed, or never examined, because the preparation was lost between the recipe and the lab.

## What it does

Lost in Preparation is a pipeline and a website that:

1. **Reads historical herbals** (Culpeper 1652 and 1850, and Pliny's *Natural History* as translated by Bostock and Riley) and extracts structured recipes. Every field is backed by a verbatim quote from the source, so a failed quote check rejects the recipe.
2. **Resolves historical plant names** to accepted species (World Flora Online), with candidates, confidence and flags for disputed names.
3. **Looks up the known compounds** for each species (LOTUS via Wikidata, standardised with RDKit).
4. **Models what each preparation delivers chemically.** Solvent, heat, filtration and acidity are separate factors with Monte Carlo uncertainty ranges, and the artemisinin case serves as a sanity check.
5. **Audits the modern literature.** For each plant and historical use, it records how modern studies prepared the plant, under a protocol fixed before any study was retrieved.
6. **Ranks hypotheses worth re-testing**: plant–use pairs never tested the way they were made, ranked only on gaps that hold across the uncertainty range. It then picks a re-test panel by exact optimisation and benchmarks classical and simulated-quantum (QAOA) solvers against that optimum.

**Headline finding: a reporting gap.** Among 43 modern studies that prepared the plant material, the share stating each preparation variable was:
- heat: 26% (95% CI 15–40%);
- fresh or dried: 16% (8–30%);
- filtration: 12% (5–24%);
- all five variables: 0% (0–8%).

Only 2.3% (95% CI 1.1–5.0%) of screened articles compared two preparations of the same plant material. So it is usually impossible to tell whether a remedy was ever tested the way it was made.

The website lets anyone explore all of this:
- **Preparation Lab:** switch solvent, heat and straining and watch the predicted compound profile change. It runs live in the browser, and every setting is a shareable URL.
- **Recipe Atlas:** 631 recipe pages, each with its source quotes.
- **Evidence gap:** the reporting-gap figures above.
- **Liquorice case study.**
- **Lab Planner:** the suggested re-test panel.
- **Impact & ethics:** who can use the outputs, a proposed preparation reporting checklist, the terms for traditional knowledge, and the plan beyond the hackathon.

**It never claims a remedy works or is safe.** Its output is hypotheses worth re-testing, each with a cited toxicity entry.

## Results

- **Headline: a reporting gap** (descriptive; n and 95% Wilson intervals). Of 43 modern studies that prepared the plant material, the share stating heat was 26% (15–40%), fresh or dried 16% (8–30%), filtration 12% (5–24%), and all five details 0% (0–8%). Only 2.3% (1.1–5.0%) of 257 article screenings compared two preparations of the same plant material.
- **Fidelity audit** (supporting, small n). Pre-registered v2: 0 of 11 units with a known status were faithful to the historical preparation (32 unknown). Audit v1 had a design flaw; it is reported as it stands, and v2 was pre-registered before it ran.
- **Hypotheses worth re-testing.** 3 plant–use pairs never tested the way they were made, ranked only on gaps that hold across the uncertainty range. The top one, *Glycyrrhiza glabra* (liquorice) for liver diseases, changed after a logged extraction correction (median gap 0.20 → 0.42).
- **Re-test panel.** An 8-experiment panel chosen by exact optimisation of a QUBO (robust gap + coverage − redundancy), toxic species excluded, under a pre-registered rule.
- **Quantum benchmark.** QAOA (penalty and XY mixers, simulated) against the exact optimum. Mean probability of sampling the optimum, as a multiple of a random feasible panel: 2.7× / 1.5× / 0.7× at 8 / 12 / 16 candidates in v2, and up to 5.0× / 4.8× / 2.2× in the pre-registered v3 (cost rescaling, INTERP to p = 5, CVaR). Simulated annealing found the optimum on every run. At 0.5% two-qubit error, P(optimum) fell from 0.19 to 0.02. **No quantum advantage is claimed.**
- **Quantum chemistry.** GFN2-xTB logP against 150 measured compounds: mean absolute error 1.51, against 0.66 for RDKit's Crippen logP, so the model uses RDKit.
- **Preparation model.** 18/18 essential-oil rows agree with it; water preparations remain unvalidated (too few studies reported a compound as absent).
- **Prototype.** A live website (see Links): Preparation Lab, Recipe Atlas (631 recipe pages), evidence gap, liquorice case study, ranked hypotheses, Lab Planner with the quantum benchmark, Methods & data, Impact & ethics.

## Impact and ethics

- **Drug discovery:** the Lab Planner gives natural-product labs a short re-test panel, each plant prepared as the recipe said, with toxic species excluded. Artemisinin is the reference case.
- **Journals and reviewers:** the headline finding implies a five-item **preparation reporting checklist** (solvent, plant part, heat, fresh or dried, filtration), plus a sixth: when a study evaluates a traditional use, test at least one preparation made the traditional way. It costs authors a few lines of methods text and makes a negative result interpretable.
- **Public health:** people take plants as teas, decoctions, tinctures and oils, not lab extracts. The Lab shows how far a preparation's predicted profile differs, compounds of concern included. It gives no guidance on preparing or taking any plant.
- **Conservation of knowledge:** plant-use databases usually drop the preparation. Here every recipe field is tied to a verbatim quote, so the *how* is kept with the *what*.
- **Ethics:** we used only published, public-domain texts, so no living community's knowledge was taken without consent. Extending the method to living traditions would follow the CARE Principles, free, prior and informed consent through a community partnership, and Nagoya Protocol access and benefit-sharing terms. The community would decide what is published, not us.
- **Feasibility:** World Flora Online and LOTUS are global, the static site costs nothing to run, and the pipeline reruns from a fresh clone with no API keys. The bottleneck to scaling is expertise in historical plant names, not computing.

## How we built it

- **Pipeline (Python 3.11):** a versioned data contract (Pydantic → JSON Schema → generated TypeScript and Zod types), with TEI/EEBO and Gutenberg ingestion and pinned SHA-256 checksums. Compound handling uses RDKit, with GFN2-xTB as a cross-check against experimental logP. The modern-methods audit is coded by rules from a versioned lexicon, and each check was pre-registered before its data was collected.
- **Recipe extraction:** written by Claude (`claude-opus-5-5`) in a Claude Code session, following a frozen prompt (v3). Every record passes the same verbatim-quote validator, and failures are logged rather than repaired. The model, the prompt version and the date are recorded on each record.
- **Optimisation (Phase 8):** the re-test panel is a QUBO (robust gap + coverage − redundancy), solved exactly. Greedy, simulated annealing and QAOA (penalty and XY mixers, simulated in Qiskit Aer with a noise sweep) are benchmarked against the exact optimum. No quantum advantage is claimed.
- **Website:** Next.js static export (TypeScript strict, Tailwind). The M4 preparation model is ported to TypeScript and runs in a Web Worker, and the build fails unless it reproduces every published Python estimate exactly. Every data file is checked against the contract schemas when the site builds.
- **Quality gates:** 306 Python tests; type-check, lint, Vitest, Playwright and axe in both themes on desktop and at 390 px; and Lighthouse. A fresh-clone reproducibility script reruns the pipeline with no API keys and network access refused.

## Challenges we ran into

- **Our first audit protocol had a design flaw.** Its solvent rule made every non-water recipe unmatchable, so v1 measured our protocol rather than the field. We kept v1 frozen and reported it, then pre-registered a v2 re-analysis instead of quietly fixing it.
- **Historical plant names are slippery.** Pliny's 19th-century translation often uses disputed identifications, so Pliny is marked lower confidence throughout, and a genus "false friends" audit checks the names.
- **Validating the preparation model honestly.** It agrees with 18/18 essential-oil rows, but water preparations remain unvalidated: we found too few literature rows that reported a compound as absent. We say so on the site rather than overstating it.
- **Avoiding circular evaluation.** The same AI wrote the extraction guidelines and the silver set, so we refuse to score extraction against that set. It will be scored only against a human gold annotation.
- **A real correction mid-project.** An extraction error changed the top hypothesis (liquorice, median gap 0.20 → 0.42). We logged the correction and turned it into a public case study.

## Accomplishments that we're proud of

- A quantified, reproducible **reporting gap**, with n and 95% CIs for every figure.
- **Every recipe field traces to a verbatim quote** from a public-domain source.
- A browser engine with **exact parity** to the Python model, enforced as a build gate.
- **Pre-registration, frozen protocols and published failures** (audit v1, the inconclusive v3 check) rather than only the results that worked.
- A clear **validation status** for each result: human-validated, validated against external data, AI-assisted check (provisional), or human validation pending.

## What we learned

- Whether a remedy "doesn't work" in a modern study often can't be judged, because the study never says how the plant was prepared.
- AI-assisted extraction is powerful, but only trustworthy when every claim can be checked mechanically against its source text.
- Quantum optimisation is fun to benchmark, but on problems this size an exact solver is the honest baseline.

## Data sources and attribution

**Historical texts (all ingested only after their licence was checked):**
- Nicholas Culpeper, *The English Physitian* (London, 1652): EEBO-TCP A35365, **CC0 1.0**.
- Nicholas Culpeper, *The Complete Herbal* (London: Thomas Kelly, 1850): Project Gutenberg #49513, public domain in the USA.
- Pliny the Elder, *Natural History*, tr. John Bostock and H. T. Riley (Bohn, 1856), vols 4 and 5: Project Gutenberg #61113 and #60688, public domain in the USA.

**Databases and services:**
- World Flora Online (name matching; CC0) and the GBIF Backbone Taxonomy (CC BY 4.0, doi:10.15468/39omei).
- LOTUS natural-product occurrences via Wikidata (CC0); PubChem (structures); Crossref metadata (CC0).
- Europe PMC / PubMed / PMC Open Access for the modern-methods audit: only identifiers, titles, MeSH terms and short attributed quotes from openly licensed articles are in the repository; abstracts and article texts are not.
- SangsterLogP dataset: Cirino, T., Sangster, J., Charochkina, L., & Tetko, I. (2026). Zenodo, https://doi.org/10.5281/zenodo.19387552, **CC BY 4.0** (logP validation).
- European Medicines Agency HMPC monographs and public statements (one attributed sentence per species, for the toxicity entries).
- Wikipedia (CC BY-SA 4.0) and Lewis & Short, *A Latin Dictionary* (PerseusDL, CC BY-SA 4.0), for drafted name identifications (provisional).
- Botanical plates: 18th- and 19th-century illustrations whose Wikimedia Commons pages state public domain, credited one by one on the site's Credits page.
- Software: xtb 6.7.1 (LGPL-3.0), RDKit, Qiskit and Qiskit Aer; fonts under the SIL Open Font License.

The full register, article by article, is `docs/DATA_LICENCES.md`. Our code is MIT and our derived data CC BY 4.0, with third-party quotations keeping their own licences.

## Limitations and assumptions

- **Extraction is not detection.** The model predicts the fraction of a compound a preparation extracts; studies report whether it was detected, which also depends on how much the plant contains. LOTUS has no abundance data, so the two cannot be fully separated.
- **The preparation model is a hypothesis generator, not a validated predictor.** It is best supported for essential-oil compounds and unvalidated for water preparations, and its ranges are wide once descriptor error is included.
- **Human validation is still pending.** The recipe extraction, the audit coding, the name identifications and the toxicity entries have automated or AI-assisted checks only; AI-assisted checks are labelled provisional and never counted as validation.
- **Small numbers.** The reporting gap rests on 43 studies and the fidelity audit on 11 known units; we report intervals rather than field-wide rates.
- **Source confidence.** Pliny's 19th-century translation often uses disputed plant names, so Pliny-derived results are marked lower confidence. Only single-plant recipes enter the headline analysis.
- **Rule-based audit coding.** "Stated" means the rule-based extractor coded a value from a versioned lexicon; abstracts report less than methods sections.
- **Quantum results are simulations** on small instances (noise-free statevector, plus a parametric noise model), not runs on quantum hardware.
- **Scope of knowledge.** Only published, public-domain European texts were used; no living community's knowledge was collected.
- **No medical claims.** The outputs are hypotheses worth re-testing; nothing on the site is guidance on preparing or taking any plant.

## What's next

- Complete the pending human validations: a gold annotation of 50 passages, a hand-check of 40 studies, 30 scholarly name identifications, and review of the toxicity entries.
- Add more herbals and more languages (Latin, Arabic and Chinese materia medica).
- Validate the preparation model for water preparations with paired lab measurements.
- Partner with a lab to run the top re-test panel, with each plant prepared as the recipe said.
- Propose a short "preparation reporting" checklist for ethnopharmacology journals.

## Built with

python, rdkit, xtb, pydantic, pandas, pyarrow, qiskit, qiskit-aer, pulp, next.js, react, typescript, tailwind-css, zod, web-workers, vitest, playwright, axe-core, lighthouse, vercel, claude, claude-code, wikidata, world-flora-online, lotus, europe-pmc

## Links

- Code: https://github.com/DurgaPritam/Lost-in-Preparation
- Live site: https://lost-in-preparation.vercel.app
- Video: `[add the YouTube or Vimeo link]`
- Slide deck (10 slides): `[upload the PDF export, or add the shared link]`

---

## Demo video

The shot list, narration and recording steps are in [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md).
