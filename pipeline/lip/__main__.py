"""CLI

  python -m lip fetch [--refresh]        download raw texts, write data/raw/manifest.json
  python -m lip ingest                   Phase 1: passages.parquet + site-data/sources.json
  python -m lip contract                 regenerate contract/schemas/*.schema.json
  python -m lip m1 sample                draw the gold sample + build annotation/data.js
  python -m lip m1 extract --scope sample|all [--provider ollama|anthropic] [--limit N] [--yes]
  python -m lip m1 eval                  metrics vs gold + kappa -> site-data/metrics.json
  python -m lip m1 errors                docs/extraction_errors.md from the error tally
  python -m lip m2 resolve [--limit N]   name inventory -> species candidates (GBIF + WFO)
  python -m lip m2 evalset               30-name scholarly identification template
  python -m lip m2 eval                  top-1 / top-3 accuracy vs the filled template
  python -m lip m3 compounds             LOTUS (Wikidata) compounds per species, RDKit-standardised
  python -m lip m3 studyset              study-set proposal table for human approval
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _has_credentials() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    return (Path.home() / ".config" / "anthropic").exists()


def m1(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="lip m1")
    ap.add_argument("cmd", choices=["sample", "extract", "eval", "errors"])
    ap.add_argument("--scope", choices=["sample", "all"], default="sample")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--provider", choices=["ollama", "anthropic"], help="overrides config/pipeline.toml")
    ap.add_argument("--yes", action="store_true", help="confirm a full-corpus (paid) run")
    a = ap.parse_args(argv)

    if a.cmd == "sample":
        from .m1 import annotation, sample
        out = sample.write()
        print(json.dumps({k: out[k] for k in ("seed", "allocation", "frameSize")}, indent=2))
        print("wrote", sample.SAMPLE_PATH, "and", annotation.build())
    elif a.cmd == "extract":
        from .m1 import extract, providers, sample
        name = a.provider or providers.load_config()["provider"]
        if name == "anthropic" and not _has_credentials():
            print("No Anthropic credentials found (ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN / `ant auth login`).\n"
                  "Set one and re-run; nothing was sent.", file=sys.stderr)
            return 2
        from .m1.prompt import load_passages
        if a.scope == "sample":
            ids = [p["passageId"] for p in json.loads(sample.SAMPLE_PATH.read_text())["passages"]]
            df = load_passages().set_index("passage_id").loc[ids].reset_index()
        else:
            if not a.yes:
                print("A full-corpus run processes every recipe-scope passage (paid with the anthropic provider; "
                      "hours with a local model). Re-run with --yes to confirm.", file=sys.stderr)
                return 2
            allp = load_passages()
            df = allp[allp.recipe_scope & (allp.passage_type == "body")].reset_index(drop=True)
        if a.limit:
            df = df.head(a.limit)
        try:
            summary = extract.run(providers.from_config(name), df, a.scope)
        except providers.ProviderError as e:
            print(str(e), file=sys.stderr)
            return 2
        print(json.dumps(summary, indent=2, default=str))
    elif a.cmd == "eval":
        from .m1 import evaluate
        m = evaluate.evaluate()
        print(m.model_dump_json(indent=2)[:4000])
    elif a.cmd == "errors":
        from .m1 import evaluate
        print(evaluate.write_error_doc())
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "help"
    if cmd == "fetch":
        from . import fetch
        fetch.fetch(refresh="--refresh" in argv)
    elif cmd == "ingest":
        from . import ingest
        print(json.dumps(ingest.run(), indent=2, ensure_ascii=False))
    elif cmd == "contract":
        from . import contract_gen
        print("\n".join(contract_gen.write()))
    elif cmd == "m1":
        return m1(argv[1:])
    elif cmd == "m2":
        from .m2 import evaluate as m2eval, resolve
        sub = argv[1] if len(argv) > 1 else "resolve"
        if sub == "resolve":
            lim = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else None
            print(json.dumps(resolve.main(lim), indent=2))
        elif sub == "evalset":
            print(m2eval.write_template())
        elif sub == "eval":
            print(json.dumps(m2eval.evaluate(), indent=2, default=str))
    elif cmd == "m3":
        from .m3 import compounds, study_set
        sub = argv[1] if len(argv) > 1 else "compounds"
        if sub == "compounds":
            print(json.dumps(compounds.main(), indent=2))
        elif sub == "studyset":
            print(study_set.main())
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
