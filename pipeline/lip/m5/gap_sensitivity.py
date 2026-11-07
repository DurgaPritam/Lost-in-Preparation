"""AI-assisted sensitivity check (provisional) of the reporting gap. Basis "ai_assisted_check"; never human validation.

The frozen reporting-gap shares (data/interim/m5/reporting_gap.json) count a study as STATING a variable when the
rule-based extractor coded a non-unknown value for any of its preparations. The AI-assisted check of the extractor
(data/reference/m5_ai_check_v1.json) shows the extractor often leaves stated values unknown. This module asks: if the
extractor's error rates on the 40 checked studies applied to every coded study, how would each share change?

At study level, on the 40 checked studies, per evidence source (open-access methods vs abstract):
  m = P(AI coder states a value | extractor unknown)      (the extractor's miss rate)
  f = P(AI coder unknown        | extractor stated a value) (the extractor's false-stated rate)
For a coded set with, per source, R studies stated and U unknown by the extractor, the adjusted count is
  sum over sources of  R * (1 - f) + U * m,
using the pooled rate when a source has no checked study in that denominator. The interval is a percentile bootstrap
(B = 2000, seed 20261107) that resamples the checked studies and the coded set within each source.

Assumptions (HEURISTIC): the AI coder's reading stands in for the truth (it is an AI, not a person); the checked studies
are representative of every coded set (only 10 of the 40 are in the 43-study prepared set); errors are independent of
the plant and indication. Filtration was not part of the AI check, so its share is not adjusted, and neither are
"none" and "all five", which depend on filtration.

Also reports, on the 40 checked studies themselves, the share stated by the extractor beside the share stated by the
AI coder. The frozen headline numbers are never changed. Writes data/interim/m5/reporting_gap_sensitivity.json and
metrics.provisional["reportingGapSensitivity"].
"""
import csv
import json
import random

from contract import models as C

from .. import metrics_store
from ..m2.evaluate import wilson
from ..paths import INTERIM, ROOT
from .reporting_gap import VARS

AI = ROOT / "data" / "reference" / "m5_ai_check_v1.json"
SHEET = ROOT / "data" / "reference" / "m5_handcheck_v1.csv"
OUT = INTERIM / "m5" / "reporting_gap_sensitivity.json"
FIELDS = ("solvent", "heat", "part", "freshOrDried")     # the fields the AI check coded
SOURCES = ("pmc_fulltext", "abstract")
LABEL = "AI-assisted sensitivity check (provisional)"
B, SEED = 2000, 20261107


def _checked() -> list[dict]:
    """One record per checked study: source, and whether the extractor / the AI coder stated each field."""
    ai = json.loads(AI.read_text())["rows"]
    rule = list(csv.DictReader(SHEET.open()))
    out = {}
    for r in rule:
        s = out.setdefault(r["pmid"], {"pmid": r["pmid"], "source": r["evidenceSource"], "rule": set(), "ai": set()})
        s["rule"] |= {f for f in FIELDS if r[f"rule_{f}"] != "unknown"}
    for a in ai:
        out[a["pmid"]]["ai"] |= {f for f in FIELDS if a[f] != "unknown"}
    return list(out.values())


def _rates(chk: list[dict], f: str) -> dict:
    def one(xs):
        unk = [x for x in xs if f not in x["rule"]]
        st = [x for x in xs if f in x["rule"]]
        return {"missK": sum(f in x["ai"] for x in unk), "missN": len(unk),
                "falseK": sum(f not in x["ai"] for x in st), "falseN": len(st)}
    out = {src: one([x for x in chk if x["source"] == src]) for src in SOURCES}
    out["pooled"] = one(chk)
    return out


def _mf(rates: dict, src: str) -> tuple[float, float]:
    r, p = rates[src], rates["pooled"]
    m = r["missK"] / r["missN"] if r["missN"] else (p["missK"] / p["missN"] if p["missN"] else 0.0)
    fs = r["falseK"] / r["falseN"] if r["falseN"] else (p["falseK"] / p["falseN"] if p["falseN"] else 0.0)
    return m, fs


def _adjusted(counts: dict, rates: dict) -> float:
    n = sum(c["n"] for c in counts.values())
    adj = 0.0
    for src, c in counts.items():
        m, fs = _mf(rates, src)
        adj += c["stated"] * (1 - fs) + (c["n"] - c["stated"]) * m
    return adj / n if n else float("nan")


def _counts(studies: list[dict], f: str) -> dict:
    fld = VARS[f]
    return {src: {"n": sum(s["evidenceSource"] == src for s in studies),
                  "stated": sum(s["evidenceSource"] == src and any(p.get(fld, "unknown") != "unknown" for p in s["preparations"]) for s in studies)}
            for src in SOURCES}


def _share(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "value": round(k / n, 4), "low": round(lo, 4), "high": round(hi, 4)}


def run() -> dict:
    chk = _checked()
    sets = {"prepared": json.loads((INTERIM / "m5" / "v2" / "audit_studies.json").read_text())["studies"],
            "retrieved": json.loads((INTERIM / "m5" / "audit_studies.json").read_text())["studies"]}
    frozen = json.loads((INTERIM / "m5" / "reporting_gap.json").read_text())["sets"]
    rng = random.Random(SEED)
    by_src = {src: [x for x in chk if x["source"] == src] for src in SOURCES}
    out = {"basis": "ai_assisted_check", "label": LABEL,
           "method": "study-level miss and false-stated rates from the AI-assisted check, per evidence source, applied to each coded set; "
                     f"percentile bootstrap B = {B}, seed {SEED}, resampling checked studies and coded studies within source",
           "assumptions": ["the AI coder's reading stands in for the truth (an AI, not a person)",
                           "the 40 checked studies represent every coded set (only 10 are in the 43-study prepared set)",
                           "filtration, 'none' and 'all five' are not adjusted: filtration was not in the AI check"],
           "checkedStudies": len(chk), "checkedInPrepared": len({x["pmid"] for x in chk} & {s["pmid"] for s in sets["prepared"]}),
           "rates": {}, "checked40": {}, "sets": {}}
    for f in FIELDS:
        out["rates"][f] = _rates(chk, f)
        out["checked40"][f] = {"rule": _share(sum(f in x["rule"] for x in chk), len(chk)),
                               "ai": _share(sum(f in x["ai"] for x in chk), len(chk))}
    for name, studies in sets.items():
        by_set_src = {src: [s for s in studies if s["evidenceSource"] == src] for src in SOURCES}
        out["sets"][name] = {}
        for f in FIELDS:
            counts = _counts(studies, f)
            point = _adjusted(counts, out["rates"][f])
            boots = []
            for _ in range(B):
                c_star = [x for src in SOURCES for x in rng.choices(by_src[src], k=len(by_src[src]))]
                s_star = [s for src in SOURCES for s in (rng.choices(by_set_src[src], k=len(by_set_src[src])) if by_set_src[src] else [])]
                boots.append(_adjusted(_counts(s_star, f), _rates(c_star, f)))
            boots.sort()
            fz = frozen[name]["all"][f if f != "filtration" else "filtration"]
            out["sets"][name][f] = {"frozen": fz, "adjusted": {"value": round(point, 4), "low": round(boots[int(0.025 * B)], 4),
                                                               "high": round(boots[int(0.975 * B) - 1], 4), "n": fz["n"]}}
        out["sets"][name]["filtration"] = {"frozen": frozen[name]["all"]["filtration"], "adjusted": None,
                                           "note": "not computed: filtration was not part of the AI-assisted check"}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    src = str(OUT.relative_to(ROOT))
    metrics = {}
    for name in sets:
        for f, v in out["sets"][name].items():
            a = v["adjusted"]
            metrics[f"{name}:all:{f}"] = (C.Metric(status=C.MetricStatus.computed, value=a["value"], low=a["low"], high=a["high"], n=a["n"], sourceFile=src,
                                                   note=f"share stating {f} if the extractor's error rates from the AI-assisted check applied (frozen: {v['frozen']['k']}/{v['frozen']['n']}); provisional")
                                          if a else C.not_computed(v["note"]))
    for f, v in out["checked40"].items():
        for who in ("rule", "ai"):
            x = v[who]
            metrics[f"checked40:{who}:{f}"] = C.Metric(status=C.MetricStatus.computed, value=x["value"], low=x["low"], high=x["high"], n=x["n"], sourceFile=src,
                                                       note=f"{x['k']}/{x['n']} checked studies stating {f}, coded by the {'rule-based extractor' if who == 'rule' else 'AI coder'}")
    metrics_store.update_provisional("reportingGapSensitivity", C.ProvisionalSection(basis="ai_assisted_check", label=LABEL, metrics=metrics))
    return {f: {"prepared frozen": out["sets"]["prepared"][f]["frozen"]["value"], "prepared adjusted": out["sets"]["prepared"][f]["adjusted"]}
            for f in FIELDS}
