"""Descriptive reporting-gap findings (not hypothesis tests). Each share comes with n and a Wilson 95% CI.

1. Of the coded modern studies, the share whose text STATES each preparation variable (solvent, heat, part, fresh or
   dried, filtration) and the share stating none. "States" means the rule-based extractor coded a non-unknown value
   for at least one of the study's preparations (HEURISTIC; extractor accuracy awaits the 40-study hand-check).
   Two sets, both from the frozen audits:
     prepared   studies eligible under audit v2: they prepared the plant material (data/interim/m5/v2/audit_studies.json)
     retrieved  every study coded under audit v1, whether or not it prepared the plant (data/interim/m5/audit_studies.json)
   Each is also split by what was coded: open-access methods sections vs abstracts.
2. The pre-registered v3 screening: of the article screenings whose tables were examined, how many compared two
   preparations of the same plant material in a usable table (data/interim/m4/literature_prereg_v3.json).
Output: data/interim/m5/reporting_gap.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..m2.evaluate import wilson
from ..paths import INTERIM

OUT = INTERIM / "m5" / "reporting_gap.json"
VARS = {"solvent": "solvent", "heat": "heat", "part": "part", "freshOrDried": "freshOrDried", "filtration": "filtered"}


def _share(k: int, n: int) -> dict:
    lo, hi = wilson(k, n) if n else (None, None)
    return {"k": k, "n": n, "value": round(k / n, 4) if n else None, "low": None if lo is None else round(lo, 4),
            "high": None if hi is None else round(hi, 4)}


def _stated(s: dict, f: str) -> bool:
    return any(p.get(f, "unknown") != "unknown" for p in s["preparations"])


def _block(studies: list[dict]) -> dict:
    n = len(studies)
    out = {v: _share(sum(_stated(s, f) for s in studies), n) for v, f in VARS.items()}
    out["none"] = _share(sum(not any(_stated(s, f) for f in VARS.values()) for s in studies), n)
    out["all five"] = _share(sum(all(_stated(s, f) for f in VARS.values()) for s in studies), n)
    return out


def run() -> dict:
    sets = {"prepared": json.loads((INTERIM / "m5" / "v2" / "audit_studies.json").read_text())["studies"],
            "retrieved": json.loads((INTERIM / "m5" / "audit_studies.json").read_text())["studies"]}
    out = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "label": "descriptive findings, not hypothesis tests; 'stated' = coded by the rule-based extractor (heuristic, hand-check pending)",
           "sets": {}}
    for name, st in sets.items():
        out["sets"][name] = {"extractor": st[0]["extractor"] if st else None, "all": _block(st),
                             **{src: _block([s for s in st if s["evidenceSource"] == src]) for src in ("pmc_fulltext", "abstract")}}
    v3 = json.loads((INTERIM / "m4" / "literature_prereg_v3.json").read_text())
    ev = [(pid, w) for v in v3["screening"].values() for pid, w in v["screened"]]
    ex = [(p, w) for p, w in ev if w.startswith("eligible") or w == "ineligible: no eligible table"]
    el = [(p, w) for p, w in ex if w.startswith("eligible")]
    out["v3Screening"] = {"source": "data/interim/m4/literature_prereg_v3.json (pre-registered, docs/PREREGISTRATION_v3.md)",
                          "screeningsWithTablesExamined": len(ex), "distinctArticlesWithTablesExamined": len({p for p, _ in ex}),
                          "eligibleScreenings": len(el), "eligibleDistinctArticles": len({p for p, _ in el}),
                          "share": _share(len(el), len(ex)),
                          "note": "share of article screenings whose tables were examined (after licence and title checks) that "
                                  "compared two preparations of the same plant material in a usable table"}
    OUT.write_text(json.dumps(out, indent=2))
    return out
