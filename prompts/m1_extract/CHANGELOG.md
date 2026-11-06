# M1 extraction prompt — changelog

Each version lives in its own folder and is never edited after use. `[m1] prompt` in `config/pipeline.toml` selects the version for extraction. Human annotators always use the full v1 guidelines (`v1/guidelines.md`). Token counts come from `python -m lip m1 prompt-tokens`, which writes `data/interim/m1/prompt_token_counts.json`.

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
