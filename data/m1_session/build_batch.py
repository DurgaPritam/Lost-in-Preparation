"""Helper for writing session-extraction batches: fills boilerplate only (defaults to "unknown", the principal
ingredient, quotesFromHeading, fieldConfidence). Every value and every quote passed in is the extractor's own
judgment. Usage: from build_batch import R, write; write(scope, n, {pid: [R(...), ...]}).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
PROMPT_VERSION = "m1_extract/v3:13ca4093ec"


def R(quote, plant, ind, *, heading=False, ingredients=None, rtype="single_plant", part="unknown", fod="unknown",
      solvent=("unknown",), heat="unknown", heatText="unknown", dur="unknown", filt="unknown", process="unknown",
      form="unknown", ev=None, conf=0.85):
    ev = ev or {}
    ings = ingredients or [(plant, part, "principal", "plant")]
    evidence = []
    for f, q in ev.items():
        for x in ([q] if isinstance(q, str) else q):
            evidence.append({"field": f, "quote": x})
    return {"recipeQuote": quote, "recipeType": rtype,
            "ingredients": [{"plantNameAsWritten": n, "part": p, "role": ro, "kind": k} for n, p, ro, k in ings],
            "plantNameAsWritten": plant, "part": part, "freshOrDried": fod, "solvent": list(solvent), "heat": heat,
            "heatText": heatText, "durationText": dur, "filtered": filt, "process": process, "form": form,
            "indicationAsWritten": ind, "evidence": evidence,
            "quotesFromHeading": ["plantNameAsWritten", "ingredients"] if heading else [],
            "fieldConfidence": [{"field": f, "confidence": conf} for f in ev]}


def write(scope: str, n: int, passages: dict) -> Path:
    out = HERE / scope / f"batch_{n:02d}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"batch": n, "scope": scope, "author": "Claude via Claude Code session", "model": "claude-opus-5-5",
                               "promptVersion": PROMPT_VERSION,
                               "writtenOn": datetime.now(timezone.utc).date().isoformat(),
                               "note": "written directly from prompt v3's instructions without consulting the silver reference set",
                               "passages": {pid: {"recipes": rs} for pid, rs in passages.items()}},
                              ensure_ascii=False, indent=1))
    return out
