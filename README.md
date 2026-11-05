# Lost in Preparation

> The plant may be right. The preparation may be wrong.

**Lost in Preparation** reads historical herbal recipes, models what each preparation would deliver chemically, and audits whether modern studies tested the remedy *the way it was made*. Its output is a ranked list of **hypotheses worth re-testing**, each prepared as the recipe said. It never claims that a remedy works or is safe.

In the 1970s, Tu Youyou's team kept failing to get antimalarial activity from sweet wormwood until a 4th-century text by Ge Hong pointed them away from heat. A low-temperature extraction then yielded artemisinin (Nobel Prize, 2015). The plant was right all along; the preparation was not.

Built for EthnoHack 2026, Track 1 (Traditional Knowledge Mining).

## What's in the box

| Stage | What it does | Status |
|---|---|---|
| Ingest | Culpeper 1652 (EEBO-TCP), Culpeper 1850 and Pliny (Bostock & Riley) → stable, located passages; 1850↔1652 crosswalk | done |
| M1 Recipes | Structured recipes extracted by an LLM, every field backed by a verbatim quote; local (Ollama) or Claude provider | built; awaiting gold set |
| M2 Names | Historical name → accepted species (WFO), up to 3 candidates with confidence | in progress |
| M3 Compounds | Known compounds per species (LOTUS via Wikidata), standardised with RDKit | in progress |
| M4–M6 | Preparation model, modern-methods audit, mismatch ranking | planned |

**Scope:** only **single-plant recipes** enter the core analysis (M4–M6) and the headline numbers. Compound recipes, with two or more ingredients besides the vehicle, are extracted and stored in `recipes.json` with `excludedFromHeadline: true`. They are left out because a mixture's chemistry can't be attributed to one plant.

## Repository

```
pipeline/lip/      Python package: ingest, segmenters, M1 extraction/evaluation, name & compound resolution
contract/          data contract: pydantic models + generated JSON Schemas for the 7 site-data files
prompts/m1_extract versioned extraction prompt, guidelines, worked examples, response schema
config/            sources, pipeline settings (LLM provider), crosswalk reviewer overrides
annotation/        static annotation & adjudication tool (open index.html in a browser)
data/gold/         gold-set sample and annotations
site-data/         exported files for the web explorer
docs/              data licences, extraction error analysis
METHODS.md         how every dataset is produced
```

## Reproduce

```bash
python3.11 -m venv .venv && .venv/bin/pip install pandas pyarrow pydantic anthropic lxml rdkit pytest
export PYTHONPATH=pipeline:.
.venv/bin/python -m lip fetch          # raw texts, checksums pinned in data/raw/manifest.json
.venv/bin/python -m lip ingest         # passages + crosswalk
.venv/bin/python -m lip contract       # contract JSON Schemas
.venv/bin/python -m lip m1 sample      # gold sample + annotation tool data
.venv/bin/python -m pytest
```

**Local extraction** (no API costs): install [Ollama](https://ollama.com), run `ollama pull qwen2.5:7b-instruct`, then `python -m lip m1 extract --scope sample`. To use Claude instead, set `provider = "anthropic"` in `config/pipeline.toml` and export `ANTHROPIC_API_KEY`.

## Data and licences

All texts are public domain or CC0; see [docs/DATA_LICENCES.md](docs/DATA_LICENCES.md). Method details are in [METHODS.md](METHODS.md).

**AI disclosure:** recipe extraction uses an LLM (local open-weight model or Claude). The provider, model, model version and prompt version are recorded on every extracted record. Parts of this codebase were written with AI assistance.
