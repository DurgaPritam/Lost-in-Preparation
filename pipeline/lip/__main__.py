"""CLI

  python -m lip fetch [--refresh]        download raw texts, write data/raw/manifest.json
  python -m lip fetch --verify           download missing raw texts and check them against the pinned checksums
  python -m lip ingest                   Phase 1: passages.parquet + site-data/sources.json
  python -m lip contract                 regenerate contract/schemas/*.schema.json
  python -m lip m1 sample                draw the gold sample + build annotation/data.js
  python -m lip m1 extract --scope sample|all [--provider groq|ollama|anthropic] [--limit N] [--yes]
  python -m lip m1 eval [--reference gold|silver]   metrics vs gold (+kappa), or vs the AI silver set (provisional)
  python -m lip m1 silver                build/validate the AI silver reference set (provisional, not gold)
  python -m lip m1 errors                docs/extraction_errors.md from the error tally
  python -m lip m2 resolve [--limit N]   name inventory -> species candidates (GBIF + WFO)
  python -m lip m2 evalset               30-name scholarly identification template
  python -m lip m2 drafts                AI-drafted, source-quoted identifications (unverified) for the template
  python -m lip m2 eval                  top-1 / top-3 vs human identifications (+ provisional vs AI drafts)
  python -m lip m3 compounds             LOTUS (Wikidata) compounds per species, RDKit-standardised
  python -m lip m3 studyset              study-set proposal table for human approval
  python -m lip m3 review                study-set review sheet -> docs/STUDY_SET_REVIEW.csv / .md
  python -m lip m4 validate-logp         RDKit vs GFN2-xTB logP against experiment (needs .tools/xtb-env)
  python -m lip m4 water-calibration     cold-water likelihood vs logP diagnostic (no model change)
  python -m lip m5 pairs                 Phase 5 species–indication pairs from the M1 session extraction
  python -m lip m5 audit                 Phase 5 audit (docs/AUDIT_PROTOCOL_v1.md): retrieval, rule-based coding, matching
  python -m lip m5 audit-v2              Phase 5 audit v2 (docs/AUDIT_PROTOCOL_v2.md): pre-registered re-analysis
  python -m lip m1 review-priority       10 passages a human reviewer should check first (AI-assisted, not an evaluation)
  python -m lip m5 handcheck-eval        extractor accuracy from the filled 40-study hand-check sheet
  python -m lip m5 ai-check-ingest DIR   gather the AI coders' blind codes (prompts/m5_ai_check/v1) -> data/reference/m5_ai_check_v1.json
  python -m lip m5 ai-check              AI-assisted check of the rule-based extractor (provisional; never human validation)
  python -m lip m5 gap-sensitivity       AI-assisted sensitivity check (provisional) of the reporting gap
  python -m lip m8 pool                  Phase 8 candidate pool (species, historical preparation, modern comparator)
  python -m lip m8 bench [--no-qaoa] [--v1]  Phase 8 benchmark (default: panel v2, docs/QUBO_v2_RULE.md): ILP, greedy, annealing, QAOA; panel; figures
  python -m lip m8 export                site-data/lab_panel.json (contract P40) and docs/QUANTUM_RESULTS.md
  python -m lip m6 hypotheses            Phase 6: rank never-faithfully-tested pairs (hypotheses worth re-testing)
  python -m lip m6 rank-demo             robust ranking rule on model-only candidate pairs + stability test (not hypotheses)
  python -m lip m4 run                   artemisinin check, literature check, profiles -> site-data/profiles.json
  python -m lip m4 engine-export         Preparation Lab inputs -> site-data/engine/ (self-checked against the profiles)
  python -m lip plates                   public-domain botanical plates from Wikimedia Commons -> site-data/plates.json, docs/IMAGE_CREDITS.md
  python -m lip plates-check             AI-assisted reading of each plate's Commons page (provisional) -> data/reference/plates_ai_check_v1.json
  python -m lip site                     write recipes/species, prune stale profiles, validate site-data/, docs/SITE_DATA_STATUS.md
  python -m lip review-merge             review pass v1 (provisional): toxicity, plates, genus audit, study-set rationale -> data/reference/review_v1.json
  python -m lip results                  RESULTS.md from pipeline outputs (validated vs provisional, labelled)
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
    ap.add_argument("cmd", choices=["sample", "extract", "eval", "errors", "silver", "prompt-tokens", "session-ingest", "session-show", "reannotation-subset", "review-priority"])
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--scope", choices=["sample", "all", "approved"], default="sample")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--provider", choices=["groq", "ollama", "anthropic"], help="overrides config/pipeline.toml")
    ap.add_argument("--yes", action="store_true", help="confirm a full-corpus (paid) run")
    ap.add_argument("--reference", choices=["gold", "silver"], default="gold",
                    help="eval: 'silver' scores against the AI reference set (provisional; written to metrics.provisional only)")
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
                print("A full-corpus run processes every recipe-scope passage (rate-limited with groq, paid with anthropic; "
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
        m = evaluate.evaluate(a.reference)
        print(m.model_dump_json(indent=2)[:4000])
    elif a.cmd == "review-priority":
        from .m1 import review_priority
        print(json.dumps(review_priority.run(), indent=2))
    elif a.cmd == "reannotation-subset":
        from .m1 import sample
        print(json.dumps(sample.write_reannotation_subset(), indent=2))
    elif a.cmd == "session-ingest":
        from .m1 import session
        print(json.dumps(session.ingest(a.scope), indent=2))
    elif a.cmd == "session-show":
        from .m1 import session
        print(session.show(a.scope, a.start, a.limit or 10))
    elif a.cmd == "prompt-tokens":
        from .m1 import token_counts
        print(json.dumps(token_counts.run(), indent=2))
    elif a.cmd == "silver":
        from .m1 import silver
        print(json.dumps(silver.build(), indent=2))
    elif a.cmd == "errors":
        from .m1 import evaluate
        print(evaluate.write_error_doc())
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "help"
    if cmd == "fetch":
        from . import fetch
        fetch.fetch(refresh="--refresh" in argv, verify_only="--verify" in argv)
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
        elif sub == "drafts":
            from .m2 import drafts
            d = drafts.build(m2eval.EVAL_PATH)
            print(f"drafted {int((d.draftAcceptedName != '').sum())} of {len(d)} names (basis ai_drafted_unverified)")
    elif cmd == "m3":
        from .m3 import compounds, study_set
        sub = argv[1] if len(argv) > 1 else "compounds"
        if sub == "compounds":
            print(json.dumps(compounds.main(), indent=2))
        elif sub == "studyset":
            print(study_set.main())
        elif sub == "review":
            from .m3 import review_sheet
            d = review_sheet.build()
            print(f"wrote {review_sheet.OUT_CSV.name} and {review_sheet.OUT_MD.name}: {len(d)} species")
    elif cmd == "plates":
        from . import plates
        print(json.dumps(plates.run(), indent=2, ensure_ascii=False))
    elif cmd == "plates-check":
        from . import plates_check
        print(json.dumps(plates_check.run(), indent=2, ensure_ascii=False))
    elif cmd == "review-merge":
        from . import review_merge
        print(json.dumps(review_merge.run(), indent=2, ensure_ascii=False))
    elif cmd == "site":
        from . import site_export
        print(json.dumps(site_export.run(), indent=2))
    elif cmd == "results":
        from . import results
        print(results.build())
    elif cmd == "m4":
        sub = argv[1] if len(argv) > 1 else "run"
        if sub == "validate-logp":
            from .m4 import validate_logp
            print(json.dumps(validate_logp.run(), indent=2))
        elif sub == "water-calibration":
            from .m4 import water_calibration
            print(json.dumps(water_calibration.run(), indent=2))
        elif sub == "run":
            from .m4 import run
            print(json.dumps(run.main(), indent=2))
        elif sub == "engine-export":
            from .m4 import engine_export
            print(json.dumps(engine_export.run(), indent=2))
    elif cmd == "m5":
        sub = argv[1] if len(argv) > 1 else "audit"
        if sub == "literature":
            from .m5 import literature
            print(json.dumps({k: v for k, v in literature.run().items() if k != "species"}, indent=2, default=str))
        elif sub == "pairs":
            from .m5 import pairs
            print(json.dumps(pairs.build()["counts"], indent=2))
        elif sub == "audit":
            from .m5 import audit
            print(json.dumps(audit.run(), indent=2, default=str))
        elif sub == "audit-v2":
            from .m5 import audit_v2
            print(json.dumps(audit_v2.run(), indent=2, default=str))
        elif sub == "handcheck-eval":
            from .m5 import audit
            print(json.dumps(audit.handcheck_eval(), indent=2))
        elif sub == "ai-check-ingest":
            from .m5 import ai_check
            print(json.dumps(ai_check.ingest(argv[2]), indent=2))
        elif sub == "ai-check":
            from .m5 import ai_check
            print(json.dumps(ai_check.run(), indent=2))
        elif sub == "gap-sensitivity":
            from .m5 import gap_sensitivity
            print(json.dumps(gap_sensitivity.run(), indent=2))
    elif cmd == "m8":
        sub = argv[1] if len(argv) > 1 else "bench"
        if sub == "pool":
            from .m8 import pool
            print(json.dumps(pool.build(), indent=2))
        elif sub == "bench":
            from .m8 import bench
            print(json.dumps(bench.run(qaoa_on="--no-qaoa" not in argv, version="v1" if "--v1" in argv else "v2"), indent=2))
        elif sub == "export":
            from .m8 import export
            print(json.dumps(export.run(), indent=2, ensure_ascii=False))
    elif cmd == "m6":
        sub = argv[1] if len(argv) > 1 else "rank-demo"
        if sub == "hypotheses":
            from .m6 import hypotheses
            print(json.dumps(hypotheses.run(argv[2] if len(argv) > 2 else "v1"), indent=2))
        elif sub == "rank-demo":
            from .m6 import ranking
            print(json.dumps({k: v for k, v in ranking.stability().items() if k != "top"}, indent=2))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
