# m5_ai_check prompt changelog

Prompt versions are frozen once used (`tests/test_prompts_frozen.py` pins every file).

## v1 (2026-11-07)

- Used once, by three Claude agents (`claude-opus-5-5`, Claude Code) to code the 40 hand-check studies (47 preparations) blind to the rule-based extractor's output, for the AI-assisted check of the extractor (basis `ai_assisted_check`; provisional, never human validation).
- `prompt.md` sha256 `71f1b0f225100c89333319eaba7e082bc8a6f2af2c67ecbfaff336cbf35c9b0f`, recorded in `data/reference/m5_ai_check_v1.json` (`provenance.promptSha256`).
- Output schema: one JSON object per row with `solvent`, `heat`, `part`, `freshOrDried`, an exact quote for each, and a `note`.
