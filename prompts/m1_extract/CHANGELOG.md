# M1 extraction prompt — changelog

Each version lives in its own folder and is never edited after use. `[m1] prompt` in `config/pipeline.toml` selects the version for extraction. Human annotators always use the full v1 guidelines (`v1/guidelines.md`). Token counts come from `python -m lip m1 prompt-tokens`, which writes `data/interim/m1/prompt_token_counts.json`.

## Response schema used by each version (recorded 2026-11-06)

All three versions used **the same response schema**. It is built in code by `response_schema()` in `pipeline/lip/m1/schema.py`, which has not changed since its first commit (217b991, 2026-11-05). Its documented copy is the frozen [`v1/response.schema.json`](v1/response.schema.json):
- **File sha256:** `8be8df9660493c2aabad25c396c263b378cf3ba4c0d1ae67cf9fa66cdabeb498`.
- **Canonical sha256** (JSON with sorted keys, as hashed into the prompt version): `7516c2c6d49c1134c50e29a6e0e1f98db4402c917d5a52bad8bf8052dac709ac`.

**Check.** Each version string is `m1_extract/<dir>:` followed by the first 10 hex digits of sha256(system prompt + schema + retry template). Rebuilding each version from the committed files and today's `response_schema()` reproduces the recorded strings exactly:

| Version | Rebuilt string | Recorded on |
|---|---|---|
| v1 | `m1_extract/v1:8aadfda9ef` | the committed v1 Groq cache |
| v2 | `m1_extract/v2:36e5019562` | the committed v2 Groq cache |
| v3 | `m1_extract/v3:13ca4093ec` | all 489 approved M1 records |

So v3's extraction used this schema.

**A stray file was removed.** `python -m lip contract` used to write a copy of the schema into the configured prompt folder. When contract v1.6 was generated, this created `v3/response.schema.json`, which was never committed and was byte-identical to `v1/response.schema.json`. The file is deleted.

**The generator is fixed.** It now writes only under `contract/schemas/` and refuses any path in `prompts/`. `tests/test_prompts_frozen.py` pins the sha256 of every file in every prompt version folder, fails if a file is added, and checks that the three recorded version strings still rebuild.

## v3 — 2026-11-06 (approved by the project lead)

**Why.** On the first 10 v2 passages, 31 of 39 Groq responses failed Groq's schema check, and Groq rejects the whole answer when that happens.
- **Cause:** in 23 of the 31, the model added `evidence` entries for free-text fields.
- **Other failures:** some quotes used ellipses, and some categorical values had no supporting quote.

**What changed** (system prompt only; v2's guidelines, worked examples and retry template are copied unchanged). Three rules were added to the quoting rules:
- `evidence` entries are allowed only for the 8 categorical fields (recipeType, part, freshOrDried, solvent, heat, filtered, process, form), never for free-text fields;
- a quote is exact, continuous text, with no ellipsis to skip words;
- every categorical value other than "unknown" needs a supporting quote.

**Size** (`o200k_base`): system prompt 2,602 tokens (v2: 2,494); fixed part with the 888-token schema 3,490 (v2: 3,382).

**Consistency.** All 50 sample passages are re-extracted with v3. The v1 and v2 responses stay in the committed cache under their own prompt versions and are not evaluated.

## v2 — 2026-11-06 (approved by the project lead)

**Why.** On Groq's free tier (8,000 tokens per minute, counting the input, the schema and the full completion allowance), v1's fixed prompt left too little room for an answer and none for a retry.

**What changed:**
- **Fixed prompt.** Cut to about 2,500 tokens:
  - **System text:** tightened.
  - **Guideline sections 1–3 and 5:** condensed.
  - **Section 6:** dropped, because adjudication is for humans only.
  - **Worked examples:** two of v1's four are kept, rendered as compact JSON:
    - `culpeper-1850:herbal:one-blade~2:004` (a single-plant and a compound recipe, a vehicle list, an unfiltered powder in a drink, and an ointment marked not applicable);
    - `culpeper-1850:herbal:one-blade~2:002` (no recipe).
- **Compact retries** (`v2/retry.md`). A retry sends only the passage, the validation errors and the failed recipes, never the full previous answer. Accepted recipes are kept; recipes still failing after the retries are rejected, as before. When the whole answer failed to validate, the retry asks for the full answer again, with the error.

**Unchanged:**
- the response schema;
- the field definitions (§4 of the guidelines, copied word for word; a test checks this);
- the verbatim-quote rule and its program check;
- temperature 0;
- the number of retries.

**Size** (`o200k_base` approximation): the system prompt goes from 5,183 to 2,494 tokens. With the 888-token schema, the fixed part goes from 6,071 to 3,382 tokens. For v1, Groq reported 6,083–6,684 input tokens on first attempts.

**Consistency.** All sample passages are re-extracted with v2, including the 7 first extracted with v1. The v1 responses stay in the committed cache under the v1 prompt version and are not evaluated.

## v1 — 2026-11-05

The first version: system text, the full annotation guidelines, four worked examples from the 1850 Culpeper (excluded from the gold sample), and the strict response schema. A retry appends the previous answer and the errors.
