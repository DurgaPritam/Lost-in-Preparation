# Phase 9: reproducibility test and final README checklist

Prepared on 2026-11-06. Nothing here makes the repository public or deploys the site; both wait for the project lead's confirmation.

## 1. Fresh-clone reproducibility test

Run it with `scripts/repro_fresh_clone.sh [REPO] [REF]`. The script does the following:
1. Clones `REF` into a temporary directory, which contains committed files only.
2. Installs `requirements.txt` (exact versions) and `site/package-lock.json`.
3. Runs every pipeline step with `LIP_CACHE_ONLY=1`, no API keys and an empty `HOME`. `LIP_CACHE_ONLY=1` makes `lip/__init__.py` refuse every network connection, so a cache miss fails loudly and never re-downloads silently.
4. Compares each regenerated file with the commit. A file whose only differences are timestamps counts as reproduced.

### First run (commit 7738000)

**Without any download** (strict cache-only), these reproduce from committed files alone:
- `lip contract` (the schemas, identical);
- `lip m6 hypotheses`;
- `lip results`;
- every website gate: `npm ci`, type-check, lint, Vitest and the build, which validates every site-data file.

These fail, because they need the raw historical texts (git-ignored; built by `lip ingest` into `data/interim/passages.parquet`):
- `lip site`;
- `lip ingest` itself;
- `lip m5 audit-v2`;
- most of `pytest`.

**After `lip fetch`** (4 public-domain texts, keyless, each checked against the SHA-256 pinned in `data/raw/manifest.json`; all 4 matched), with cache-only for everything else:
- `lip ingest` and `lip site` reproduce. Their outputs differ from the commit only in timestamps, except one file: the committed `data/interim/ingest_report.json` is stale (it says contract 1.3; the regenerated one says 1.6).
- **pytest: 296 passed, 5 failed.** All 5 need git-ignored download caches, and in each case cache-only correctly refused the network:

| Test | Needs |
|---|---|
| `test_m1_prompt_v2::test_v2_is_small_and_v1_is_unchanged` | tiktoken's `o200k_base` file (downloaded by tiktoken) |
| `test_prereg_v3::test_double_ratio_sign_and_rules` | cached PubChem structures |
| `test_provisional_and_m4::test_toxicity_screen_is_cited_and_conservative` | the cached Wikipedia page |
| `test_water_check_and_toxicity::test_toxicity_quotes_reverify_against_sources` | the cached EMA / PMC source documents |
| `test_water_check_and_toxicity::test_quote_for_unlicensed_article_is_refused` | the cached Europe PMC licence lookup |

### Decisions needed before the final run

1. **Raw texts.** Should the test run `lip fetch` (keyless, checksum-verified) before cache-only mode? The alternative is committing the raw texts: Culpeper 1652 is CC0, and the Gutenberg texts would need the Project Gutenberg header and licence kept, or the trademark removed. *Recommended:* fetch with checksum verification, and keep the raw texts out of the repo.
2. **The 5 cache-dependent tests.** Should they get a `needs_cache` marker that skips them, with the reason, when their cache is absent? The alternative is committing the small cached responses they read: PubChem JSON, EMA PDFs (reproduction authorised), the Wikipedia page (CC BY-SA), and PMC pages (some are CC BY-NC-ND, which would contradict the no-full-text rule). *Recommended:* the skip marker.
3. **Stale file.** Refresh the stale `data/interim/ingest_report.json`.

### Decisions applied (2026-11-07)

1. **Raw texts:** the test runs `python -m lip fetch --verify`, which downloads the 4 texts and requires each to match the SHA-256 pinned in `data/raw/manifest.json`, without rewriting the manifest. The texts are not committed. Everything else still runs cache-only.
2. **Cache-dependent tests:** the 5 tests skip when their git-ignored cache is missing. The skip message names the cache and the command that fetches it (`tests/_cache.py`).
3. **Stale file:** `data/interim/ingest_report.json` is regenerated (contract 1.7).
4. **Licences:** `LICENSE` (MIT, code) and `LICENSE-DATA` (CC BY 4.0, derived data), with the exceptions listed in each and in the README and `docs/DATA_LICENCES.md`.
5. **PMC12309076:** the excerpt is trimmed to the table caption and the one row the check matched. That row is *linalool acetate*, not linalool, so the frozen pre-registered v1 check counted a misread row. The result is unchanged; the misread is reported.
6. **README:** pinned install, the fresh-clone test, the licence wording and the study-set status are updated.

### Re-run (2026-11-07, commit 4f0b623)

The checklist was re-run after the v2 site, Phase 8 and the AI-assisted checks.

- **Fresh-clone test: PASS.** `scripts/repro_fresh_clone.sh` now also installs `requirements-quantum.txt` and runs
  `lip m5 gap-sensitivity`, `lip m1 review-priority`, `lip m8 pool` and `lip m8 export`.
  - **Reproduce from committed files:** every step expected to.
  - **Refuse loudly, as expected:** `lip m5 ai-check` (needs the git-ignored study texts) and `lip m5 audit-v2` (needs the literature caches).
  - **Regenerated outputs:** they differ from the commit only in timestamps.
  - **Not re-run:** the full QAOA benchmark (`lip m8 bench`, about 45 minutes). Its committed outputs are exported and validated instead.
- **Fixed in this re-run:**
  - **Stale contract version:** four committed files still said contract 1.7; they are regenerated at 1.9.
  - **A test missing its skip:** one cache-dependent test failed instead of skipping (`test_prereg_v3`; the code tolerates PubChem misses quietly), so it now checks for the cache.
  - **Quotes from abstracts and unlicensed articles:** the AI-check file held verbatim quotes from them. It now keeps only their position and SHA-256 (docs/DATA_LICENCES.md).
- **Gates:**
  - Python tests pass. In the fresh clone, 4 skip, each naming its missing cache.
  - Site: lint, type-check, Vitest, the engine parity gate, the build and Playwright pass.
  - Lighthouse runs in both themes; the latest scores are in `site/perf/`.
  - CI on `main` passes.
- **Secrets:** gitleaks over every commit found nothing, and `.env` was never committed.
- **Licences:** LICENSE now notes that the two Fraunces files are a modified version (OFL 1.1). LICENSE-DATA now says
  the plates are public domain *as stated on Commons*, read by an AI-assisted check, with human confirmation pending.

### Still open

1. **Human validations** (RESULTS.md "Validation status"):
   - the gold annotation and the 15-passage re-annotation;
   - the 40-study hand-check of the extractor;
   - the 30-name scholarly identifications;
   - a person's confirmation of the 15 plate licences;
   - human review of the AI-drafted toxicity entries and the genus-signal audit.
2. **History of `data/reference/m5_ai_check_v1.json`:** commit `ccb6fe4` holds 27 short verbatim quotes (up to 100
   characters each, attributed by PMID) from PubMed abstracts and from articles with no stated licence. They were
   removed from the current tree.
   - **Options:** keep them (your original rule allowed "short attributed evidence quotes"), or rewrite that one file
     out of history with `git filter-repo` before the repository is made public. That needs a force-push; the local
     `backup-before-trailer-cleanup` tag is unaffected.
3. **Repository rename** to `Lost-in-Preparation`, then update the remote and every reference. This waits on the
   project lead's confirmation.
4. **Making the repository public** and **deploying the site** wait on the project lead's confirmation. After
   deployment: the CI badge and the live URL in the README.
5. **Optional:** `CITATION.cff`, and the team and contact details in the README.
6. **Still awaited from earlier:** the reasons for species 17–27.

## 2. Final README checklist

| # | Item | Status |
|---|---|---|
| 1 | One-paragraph claim with "hypotheses worth re-testing" and no medical claims | done |
| 2 | Headline (the reporting gap) with n and 95% CI, generated by `lip results` | done |
| 3 | Validation status table | done: every item has one of four statuses (human-validated, validated against external data, AI-assisted check (provisional), human validation pending). The human validations listed under "Still open" are pending. |
| 4 | Limitations, including extraction vs detection, Pliny's lower confidence and AI-made references | done |
| 5 | AI disclosure: model, prompt version and the session-extraction caveat | done. The response-schema hash is recorded in `prompts/m1_extract/CHANGELOG.md`. |
| 6 | **Licence for the repository** (code, and the project's own derived data) | **done** (2026-11-07): MIT and CC BY 4.0. Previously missing. No `LICENSE` file. Needs a decision (for example MIT or Apache-2.0 for code, and CC BY 4.0 for derived data), with exceptions for third-party quotes: CC BY-SA (Wikipedia, Lewis & Short), CC BY-NC(-ND/-SA) (PMC), and EMA's attribution terms. |
| 7 | "Data and licences" section | **done** (2026-11-07). Previously needed wording: "All texts are public domain or CC0" should say: Gutenberg texts are public domain in the USA only, and short third-party quotes keep their own licences (see `docs/DATA_LICENCES.md`). |
| 8 | Reproduce section uses pinned versions | **done** (2026-11-07). Previously: It installs unpinned packages; it should use `pip install -r requirements.txt`, Python 3.11. |
| 9 | Reproducibility test and cache-only mode documented | **done** (2026-11-07). Previously to add: `LIP_CACHE_ONLY=1`, `scripts/repro_fresh_clone.sh`, and what needs a download. |
| 10 | Website section, CI badge and live URL | Section done; the CI badge and the live URL are pending deployment. |
| 11 | Stage table statuses up to date | **done** (2026-11-07). Previously: The "Study set" row says "awaiting approval", but the study set has re-review decisions recorded; the reasons for species 17–27 are still awaited. |
| 12 | How to cite (`CITATION.cff`) | **missing (optional).** |
| 13 | Hackathon track, team and contact | Track stated; team and contact not stated. |
| 14 | Secrets | done. gitleaks over all 66 commits found nothing; the Groq key's value does not occur in the history or the working tree; `.env` was never committed. |
| 15 | Third-party text audit | done. No abstracts or full article texts in the tree or the history (see the audit report). |
