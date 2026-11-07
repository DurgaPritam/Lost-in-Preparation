"""AI-assisted check of the rule-based extractor (provisional). Basis "ai_assisted_check"; never human validation.

Claude agents (prompt prompts/m5_ai_check/v1/prompt.md) coded the 40 hand-check studies BLIND to the extractor's output:
they saw only the study texts and, for the 3 studies with several extracted preparations, the extractor's solvent wording
that identifies each row. This module

  ingest(dir)  gathers their codes into data/reference/m5_ai_check_v1.json (with model, prompt version and date);
  run()        verifies every quote verbatim against the local study texts, compares the codes with the extractor's
               values in data/reference/m5_handcheck_v1.csv (read only; its human_* columns stay for people), and
               writes per-field agreement with Wilson 95% intervals to data/interim/m5/ai_check_eval.json and to
               metrics.provisional["m5ExtractorAiCheck"]. Gold and human fields are never written.

Caveats recorded with the result:
  - an AI checking a rule system is not a human reading; the AI coder can share the extractor's blind spots or add its own;
  - rows are not independent (3 studies contribute 10 of the 47 rows), so the intervals are optimistic;
  - on the 10 multi-preparation rows the row label shows the extractor's solvent wording, so solvent is not blind there;
    solvent agreement is also reported on the 37 single-preparation rows.
"""
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from contract import models as C

from .. import metrics_store
from ..m2.evaluate import wilson
from ..http import CACHE
from ..paths import INTERIM, ROOT

CODES = ROOT / "data" / "reference" / "m5_ai_check_v1.json"
SHEET = ROOT / "data" / "reference" / "m5_handcheck_v1.csv"
TEXTS = CACHE / "m5_handcheck" / "handcheck_v1_texts.md"
PROMPT = ROOT / "prompts" / "m5_ai_check" / "v1" / "prompt.md"
OUT = INTERIM / "m5" / "ai_check_eval.json"
FIELDS = ("solvent", "heat", "part", "freshOrDried")
LABEL = "AI-assisted check of the rule-based extractor (provisional)"
BASIS = "ai_assisted_check"
ALLOWED = {"solvent": {e.value for e in C.ModernSolvent}, "heat": {e.value for e in C.Heat},
           "part": {e.value for e in C.Part}, "freshOrDried": {e.value for e in C.FreshOrDried}}


def ingest(src_dir: str, model: str = "claude-opus-5-5") -> dict:
    rows = []
    for f in sorted(Path(src_dir).glob("batch*_out.json")):
        rows += json.loads(f.read_text())
    sheet = list(csv.DictReader(SHEET.open()))
    want = [(r["pmid"], int(r["preparation"])) for r in sheet]
    got = {(str(r["pmid"]), int(r["preparation"])): r for r in rows}
    missing = [k for k in want if k not in got]
    if missing:
        raise SystemExit(f"AI codes missing for {len(missing)} rows: {missing[:5]}")
    out = {
        "basis": BASIS, "label": LABEL,
        "provenance": {"model": model, "tool": "Claude Code agents (3 batches)", "prompt": str(PROMPT.relative_to(ROOT)),
                       "promptVersion": "v1", "promptSha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest(),
                       "blind": "coders saw only the study texts and, for multi-preparation studies, the extractor's solvent wording as a row label",
                       "codedOn": date.today().isoformat()},
        "rows": [{"pmid": p, "preparation": i, **{k: got[(p, i)].get(k, "") for k in
                  ("solvent", "solvent_quote", "heat", "heat_quote", "part", "part_quote", "freshOrDried", "freshOrDried_quote", "note")}}
                 for p, i in want],
    }
    CODES.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return {"rows": len(out["rows"]), "out": str(CODES.relative_to(ROOT))}


def _sections() -> dict[str, str] | None:
    if not TEXTS.exists():
        return None
    md = TEXTS.read_text()
    return {re.match(r"## PMID (\d+)", s).group(1): s for s in re.split(r"\n(?=## PMID )", md)[1:]}


def _rate(k: int, n: int) -> dict:
    lo, hi = wilson(k, n) if n else (None, None)
    return {"k": k, "n": n, "value": round(k / n, 4) if n else None, "low": round(lo, 4) if n else None, "high": round(hi, 4) if n else None}


def run() -> dict:
    codes = json.loads(CODES.read_text())
    sheet = {(r["pmid"], int(r["preparation"])): r for r in csv.DictReader(SHEET.open())}
    per_study = Counter(p for p, _ in sheet)
    secs = _sections()
    problems, rows = [], []
    for c in codes["rows"]:
        r = sheet[(c["pmid"], c["preparation"])]
        for f in FIELDS:
            v, q = c[f], (c.get(f"{f}_quote") or "").strip()
            if v not in ALLOWED[f]:
                problems.append(f"{c['pmid']}#{c['preparation']} {f}: value {v!r} not allowed")
            if v != "unknown" and not q:
                problems.append(f"{c['pmid']}#{c['preparation']} {f}: value without a quote")
            if q and secs is not None and q not in secs.get(c["pmid"], ""):
                problems.append(f"{c['pmid']}#{c['preparation']} {f}: quote not found verbatim")
        rows.append({"pmid": c["pmid"], "preparation": c["preparation"], "evidenceSource": r["evidenceSource"],
                     "multi": per_study[c["pmid"]] > 1, **{f"ai_{f}": c[f] for f in FIELDS}, **{f"rule_{f}": r[f"rule_{f}"] for f in FIELDS}})
    if problems:
        raise SystemExit("AI codes failed the checks:\n  " + "\n  ".join(problems))

    def agree(rs, f):
        return sum(x[f"ai_{f}"] == x[f"rule_{f}"] for x in rs)

    fields = {}
    for f in FIELDS:
        both_unknown = sum(x[f"ai_{f}"] == x[f"rule_{f}"] == "unknown" for x in rows)
        both_stated_same = sum(x[f"ai_{f}"] == x[f"rule_{f}"] != "unknown" for x in rows)
        rule_missed = sum(x[f"rule_{f}"] == "unknown" != x[f"ai_{f}"] for x in rows)
        rule_only = sum(x[f"ai_{f}"] == "unknown" != x[f"rule_{f}"] for x in rows)
        conflict = sum("unknown" != x[f"ai_{f}"] != x[f"rule_{f}"] != "unknown" for x in rows)
        stated = [x for x in rows if x[f"ai_{f}"] != "unknown" and x[f"rule_{f}"] != "unknown"]
        fields[f] = {
            "agreement": _rate(agree(rows, f), len(rows)),
            "bySource": {s: _rate(agree([x for x in rows if x["evidenceSource"] == s], f), sum(x["evidenceSource"] == s for x in rows))
                         for s in sorted({x["evidenceSource"] for x in rows})},
            "agreementWhereBothStated": _rate(sum(x[f"ai_{f}"] == x[f"rule_{f}"] for x in stated), len(stated)),
            "breakdown": {"bothUnknown": both_unknown, "bothStatedSame": both_stated_same, "ruleUnknownAiStated": rule_missed,
                          "ruleStatedAiUnknown": rule_only, "bothStatedDifferent": conflict},
            "disagreements": [{"pmid": x["pmid"], "preparation": x["preparation"], "rule": x[f"rule_{f}"], "ai": x[f"ai_{f}"]}
                              for x in rows if x[f"ai_{f}"] != x[f"rule_{f}"]],
        }
    single = [x for x in rows if not x["multi"]]
    fields["solvent"]["agreementSinglePreparationRows"] = _rate(agree(single, "solvent"), len(single))
    out = {
        "basis": BASIS, "label": LABEL, "provenance": codes["provenance"],
        "quotesVerified": secs is not None,
        "rows": len(rows), "studies": len(per_study),
        "agreementDefinition": "same code (unknown = unknown counts as agreement); Wilson 95% interval over rows",
        "caveats": [
            "An AI checking a rule system, not a human reading: the AI coder may share the extractor's blind spots or add its own.",
            "Rows are not independent: 3 studies contribute 10 of the rows, so the intervals are optimistic.",
            "On multi-preparation rows the row label shows the extractor's solvent wording, so solvent is not blind there "
            "(solvent agreement is also reported on the single-preparation rows).",
        ],
        "fields": fields,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    src = str(OUT.relative_to(ROOT))
    metrics_store.update_provisional("m5ExtractorAiCheck", C.ProvisionalSection(
        basis=BASIS, label=LABEL,
        metrics={f"{f} agreement": C.Metric(status=C.MetricStatus.computed, value=v["agreement"]["value"], low=v["agreement"]["low"],
                                            high=v["agreement"]["high"], n=v["agreement"]["n"], sourceFile=src,
                                            note=f"{v['agreement']['k']}/{v['agreement']['n']} rows agree; AI coder vs rule-based extractor; not human validation")
                 for f, v in fields.items()}))
    return {"rows": len(rows), "quotesVerified": secs is not None,
            **{f: f"{v['agreement']['k']}/{v['agreement']['n']}" for f, v in fields.items()}}
