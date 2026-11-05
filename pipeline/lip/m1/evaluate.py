"""M1 evaluation: per-field precision/recall/F1 vs the adjudicated gold set, Cohen's kappa between
the two annotators, bootstrap 95% CIs, and an error tally. Writes site-data/metrics.json.

Scoring (documented in docs/extraction_eval.md)
- Recipes are aligned within a passage, greedily by character IoU of their recipe spans
  (ties broken by the number of agreeing categorical fields). Without spans: mean token-F1 of plant
  name and indication, threshold 0.5.
- Per field, on aligned pairs: both known & equal -> TP; both known & different -> FP + FN;
  predicted known, gold unknown -> FP; predicted unknown, gold known -> FN; both unknown -> nothing.
  Unaligned predicted recipes count FP for every known field; unaligned gold recipes count FN.
- `solvent` is scored as a set (unknown removed); `ingredients` as a set of names.
- Free-text fields match when token-F1 >= 0.5 (lenient, stated in metrics notes).
- Bootstrap: 2000 resamples of passages (stratified for the overall number), seed fixed.
"""
from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from contract import models as C

from .. import PIPELINE_VERSION
from ..paths import INTERIM, ROOT, SITE_DATA
from .sample import ALLOCATION, SAMPLE_PATH
from .schema import CATEGORICAL_FIELDS, SET_FIELDS, TEXT_FIELDS

UNK = C.UNKNOWN
SCORED_FIELDS = CATEGORICAL_FIELDS + SET_FIELDS + TEXT_FIELDS + ["ingredients"]
KAPPA_FIELDS = CATEGORICAL_FIELDS + SET_FIELDS
ANN_DIR = ROOT / "data" / "gold" / "annotations"
GOLD_PATH = ANN_DIR / "gold.json"
PRED_PATH = INTERIM / "m1" / "predictions_sample.json"
RUN_PATH = INTERIM / "m1" / "run_sample.json"
DETAIL_PATH = INTERIM / "m1" / "eval_detail.json"
TALLY_PATH = INTERIM / "m1" / "error_tally.json"
B = 2000
SEED = 7
TEXT_THRESHOLD = 0.5


def _rel(p) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


# --- normalisation ------------------------------------------------------------------------

def tokens(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def tok_f1(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    common = sum((Counter(ta) & Counter(tb)).values())
    if not common:
        return 0.0
    p, r = common / len(tb), common / len(ta)
    return 2 * p * r / (p + r)


def flat_from_annotation(r: dict) -> dict:
    span = r.get("recipeSpan") or {}
    out = {f: r.get(f, UNK) for f in CATEGORICAL_FIELDS + TEXT_FIELDS}
    out["solvent"] = sorted(set(r.get("solvent") or [UNK]) - {UNK})
    out["ingredients"] = [g.get("plantNameAsWritten", "") for g in r.get("ingredients", [])]
    out["span"] = (span["start"], span["end"]) if "start" in span and span["start"] is not None and span["start"] >= 0 else None
    out["spanText"] = span.get("quote", "")
    return out


def flat_from_contract(r: dict) -> dict:
    out = {f: r.get(f, UNK) for f in CATEGORICAL_FIELDS + TEXT_FIELDS}
    out["solvent"] = sorted(set(r.get("solvent") or [UNK]) - {UNK})
    out["ingredients"] = [g["plantNameAsWritten"] for g in r.get("ingredients", [])]
    q = (r.get("evidence", {}).get("recipe") or [None])[0]
    out["span"] = (q["start"], q["end"]) if q and q["start"] >= 0 else None
    out["spanText"] = q["quote"] if q else ""
    return out


def load_annotation_file(path) -> dict[str, list[dict]]:
    """passageId -> flat recipes, for passages marked done."""
    data = json.loads(path.read_text())
    return {pid: [flat_from_annotation(r) for r in p.get("recipes", [])]
            for pid, p in data.get("passages", {}).items() if p.get("done")}


def load_predictions(path=None) -> dict[str, list[dict]] | None:
    path = path or PRED_PATH
    if not path.exists():
        return None
    by: dict[str, list[dict]] = defaultdict(list)
    for r in json.loads(path.read_text()):
        by[r["passage"]["passageId"]].append(flat_from_contract(r))
    return by


# --- alignment ----------------------------------------------------------------------------

def _iou(a, b) -> float:
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = max(a[1], b[1]) - min(a[0], b[0])
    return inter / union if union else 0.0


def _agree(g: dict, p: dict) -> int:
    return sum(1 for f in CATEGORICAL_FIELDS if g[f] == p[f] and g[f] != UNK)


def pair_score(g: dict, p: dict) -> float:
    if g["span"] and p["span"]:
        iou = _iou(g["span"], p["span"])
        return iou + 0.01 * _agree(g, p) if iou > 0 else 0.0
    sim = (tok_f1(g["plantNameAsWritten"], p["plantNameAsWritten"]) + tok_f1(g["indicationAsWritten"], p["indicationAsWritten"])) / 2
    return sim + 0.01 * _agree(g, p) if sim >= TEXT_THRESHOLD else 0.0


def align(gold: list[dict], pred: list[dict]):
    cands = sorted(((pair_score(g, p), gi, pi) for gi, g in enumerate(gold) for pi, p in enumerate(pred)), reverse=True)
    used_g, used_p, pairs = set(), set(), []
    for s, gi, pi in cands:
        if s <= 0 or gi in used_g or pi in used_p:
            continue
        pairs.append((gi, pi))
        used_g.add(gi)
        used_p.add(pi)
    return pairs, [i for i in range(len(gold)) if i not in used_g], [i for i in range(len(pred)) if i not in used_p]


# --- per-field counts ---------------------------------------------------------------------

def _known(f: str, v) -> int:
    if f in SET_FIELDS or f == "ingredients":
        return len(v)
    return 0 if v in (UNK, "", None) else 1


def _match_list(gl: list[str], pl: list[str]) -> int:
    used, tp = set(), 0
    for g in gl:
        for j, p in enumerate(pl):
            if j not in used and tok_f1(g, p) >= TEXT_THRESHOLD:
                used.add(j)
                tp += 1
                break
    return tp


def compare_field(f: str, g, p) -> tuple[int, int, int]:
    if f in SET_FIELDS:
        sg, sp = set(g), set(p)
        return len(sg & sp), len(sp - sg), len(sg - sp)
    if f == "ingredients":
        tp = _match_list(g, p)
        return tp, len(p) - tp, len(g) - tp
    gk, pk = _known(f, g), _known(f, p)
    if gk and pk:
        eq = tok_f1(g, p) >= TEXT_THRESHOLD if f in TEXT_FIELDS else g == p
        return (1, 0, 0) if eq else (0, 1, 1)
    return 0, pk, gk


def passage_counts(gold: list[dict], pred: list[dict]):
    pairs, ug, up = align(gold, pred)
    counts = {f: [0, 0, 0] for f in SCORED_FIELDS}
    errors = []
    for gi, pi in pairs:
        g, p = gold[gi], pred[pi]
        for f in SCORED_FIELDS:
            tp, fp, fn = compare_field(f, g[f], p[f])
            c = counts[f]
            c[0] += tp; c[1] += fp; c[2] += fn
            if fp or fn:
                kind = "wrong_value" if (_known(f, g[f]) and _known(f, p[f])) else ("missed" if fn else "spurious")
                errors.append({"type": kind, "field": f, "gold": g[f], "pred": p[f], "goldSpan": g["spanText"][:160]})
    for gi in ug:
        for f in SCORED_FIELDS:
            counts[f][2] += _known(f, gold[gi][f])
        errors.append({"type": "recipe_missed", "field": "recipe", "gold": gold[gi]["spanText"][:160], "pred": None})
    for pi in up:
        for f in SCORED_FIELDS:
            counts[f][1] += _known(f, pred[pi][f])
        errors.append({"type": "recipe_spurious", "field": "recipe", "gold": None, "pred": pred[pi]["spanText"][:160]})
    counts["_recipe"] = [len(pairs), len(up), len(ug)]
    return counts, errors


def prf(tp: int, fp: int, fn: int) -> tuple[float | None, float | None, float | None]:
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = (2 * p * r / (p + r) if (p + r) else 0.0) if p is not None and r is not None else None
    return p, r, f


def _sum(counts: list[dict], f: str) -> tuple[int, int, int]:
    return tuple(sum(c[f][i] for c in counts) for i in range(3))  # type: ignore[return-value]


def _ci(samples: list[float | None]) -> tuple[float | None, float | None]:
    v = sorted(x for x in samples if x is not None)
    if len(v) < 20:
        return None, None
    return v[int(0.025 * len(v))], v[min(len(v) - 1, int(0.975 * len(v)))]


def prf_with_ci(per_passage: dict[str, dict], strata: dict[str, str], field: str, keys: list[str],
                stratified: bool, source_file: str) -> C.PRF:
    rng = random.Random(SEED)
    point = prf(*_sum([per_passage[k] for k in keys], field))
    groups = defaultdict(list)
    for k in keys:
        groups[strata[k] if stratified else "_"].append(k)
    boots = [[], [], []]
    for _ in range(B):
        res = [per_passage[rng.choice(g)] for g in groups.values() for _ in g]
        for i, v in enumerate(prf(*_sum(res, field))):
            boots[i].append(v)
    tp, fp, fn = _sum([per_passage[k] for k in keys], field)
    out = []
    for i, name in enumerate(("precision", "recall", "f1")):
        lo, hi = _ci(boots[i])
        if point[i] is None:
            out.append(C.not_computed(f"undefined: zero denominator (tp={tp}, fp={fp}, fn={fn})"))
        else:
            out.append(C.Metric(status="computed", value=round(point[i], 4), low=None if lo is None else round(lo, 4),
                                high=None if hi is None else round(hi, 4), n=len(keys), sourceFile=source_file,
                                note=f"tp={tp} fp={fp} fn={fn}; 95% CI: passage bootstrap, B={B}"))
    return C.PRF(precision=out[0], recall=out[1], f1=out[2])


# --- inter-annotator agreement --------------------------------------------------------------

def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def _label(f: str, v) -> str:
    return "+".join(v) if f in SET_FIELDS else str(v)


def kappa_metrics(a: dict[str, list[dict]], b: dict[str, list[dict]], strata: dict[str, str]) -> dict[str, C.Metric]:
    keys = sorted(set(a) & set(b) & set(strata))
    per_passage = {}
    for k in keys:
        pairs, _, _ = align(a[k], b[k])
        per_passage[k] = {
            f: [(_label(f, a[k][i][f] if f not in SET_FIELDS else a[k][i][f] or [UNK]),
                 _label(f, b[k][j][f] if f not in SET_FIELDS else b[k][j][f] or [UNK])) for i, j in pairs]
            for f in KAPPA_FIELDS
        }
        per_passage[k]["passageHasRecipe"] = [(str(bool(a[k])), str(bool(b[k])))]
    out = {}
    rng = random.Random(SEED)
    for f in KAPPA_FIELDS + ["passageHasRecipe"]:
        allp = [x for k in keys for x in per_passage[k][f]]
        kap = cohen_kappa(allp)
        if kap is None:
            out[f] = C.not_computed("no aligned annotator pairs" if not allp else "kappa undefined (both annotators used a single category)")
            continue
        boots = []
        for _ in range(B):
            res = [x for _ in keys for x in per_passage[rng.choice(keys)][f]]
            boots.append(cohen_kappa(res))
        lo, hi = _ci(boots)
        out[f] = C.Metric(status="computed", value=round(kap, 4), low=None if lo is None else round(lo, 4),
                          high=None if hi is None else round(hi, 4), n=len(allp),
                          sourceFile=_rel(DETAIL_PATH),
                          note=f"Cohen's kappa over {len(allp)} aligned recipe pairs in {len(keys)} passages; 'unknown' is a category")
    return out


# --- top level ----------------------------------------------------------------------------

def _not_computed_prf(note: str) -> C.PRF:
    return C.PRF(precision=C.not_computed(note), recall=C.not_computed(note), f1=C.not_computed(note))


def _annotator_files():
    return sorted(p for p in ANN_DIR.glob("*.json") if p.name != "gold.json") if ANN_DIR.exists() else []


def evaluate() -> C.Metrics:
    sample = json.loads(SAMPLE_PATH.read_text())
    strata = {p["passageId"]: p["stratum"] for p in sample["passages"]}
    gold = load_annotation_file(GOLD_PATH) if GOLD_PATH.exists() else None
    pred = load_predictions()
    detail: dict = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    # extraction P/R/F1
    reasons = []
    if gold is None:
        reasons.append(f"awaiting adjudicated gold set ({_rel(GOLD_PATH)})")
    if pred is None:
        reasons.append(f"awaiting LLM predictions on the sample ({_rel(PRED_PATH)}); run `python -m lip m1 extract --scope sample`")
    source_file = _rel(DETAIL_PATH)
    if reasons:
        note = "; ".join(reasons)
        overall = {f: _not_computed_prf(note) for f in SCORED_FIELDS}
        by_source = {s: {f: _not_computed_prf(note) for f in SCORED_FIELDS} for s in ALLOCATION}
        detection = {k: _not_computed_prf(note) for k in ["overall", *ALLOCATION]}
    else:
        keys = sorted(k for k in gold if k in strata)
        per_passage, all_errors = {}, []
        for k in keys:
            per_passage[k], errs = passage_counts(gold[k], pred.get(k, []))
            all_errors += [dict(e, passageId=k, stratum=strata[k]) for e in errs]
        detail.update(perPassage=per_passage, nGold=len(keys), missingFromSample=sorted(set(strata) - set(keys)))
        overall = {f: prf_with_ci(per_passage, strata, f, keys, True, source_file) for f in SCORED_FIELDS}
        by_source = {s: {f: prf_with_ci(per_passage, strata, f, [k for k in keys if strata[k] == s], False, source_file)
                         for f in SCORED_FIELDS} for s in ALLOCATION}
        detection = {"overall": prf_with_ci(per_passage, strata, "_recipe", keys, True, source_file)}
        detection.update({s: prf_with_ci(per_passage, strata, "_recipe", [k for k in keys if strata[k] == s], False, source_file)
                          for s in ALLOCATION})
        TALLY_PATH.parent.mkdir(parents=True, exist_ok=True)
        TALLY_PATH.write_text(json.dumps(all_errors, ensure_ascii=False, indent=1))

    # span rejection rate
    run_info = None
    if RUN_PATH.exists():
        run = json.loads(RUN_PATH.read_text())
        run_info = C.ExtractionRun(**run["run"], promptVersion=run["promptVersion"])
        n = run["recipesReturned"]
        rej = C.Metric(status="computed", value=round(run["recipesRejected"] / n, 4) if n else 0.0, n=n,
                       sourceFile=_rel(RUN_PATH),
                       note=f"recipes dropped after {run.get('retriesUsed', 0)} retries because a quote was not verbatim; "
                            f"{run.get('passagesFailedWhole', 0)} passages failed whole (refusal/max_tokens/schema)")
    else:
        rej = C.not_computed("awaiting LLM run on the sample")

    # kappa
    files = _annotator_files()
    if len(files) == 2:
        a, b = (load_annotation_file(p) for p in files)
        iaa = kappa_metrics(a, b, strata)
        detail["annotators"] = [p.stem for p in files]
    else:
        iaa = {f: C.not_computed(f"needs exactly 2 annotator files in {_rel(ANN_DIR)}/ (found {len(files)})")
               for f in KAPPA_FIELDS + ["passageHasRecipe"]}

    later = lambda phase: C.not_computed(f"computed in {phase}")  # noqa: E731
    m = C.Metrics(
        generatedAt=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        pipelineVersion=PIPELINE_VERSION,
        extraction=C.ExtractionMetrics(run=run_info, overall=overall, bySource=by_source, recipeDetection=detection, spanRejectionRate=rej),
        interAnnotatorAgreement=iaa,
        nameResolution={"top1": later("Phase 3 (M2)"), "top3": later("Phase 3 (M2)"), "disputedShare": later("Phase 3 (M2)")},
        logPError={"rdkit": later("Phase 4 (M4)"), "xtb": later("Phase 4 (M4)")},
        headlineMatchRate=later("Phase 6 (M5/M6)"),
        artemisininCheck=C.CheckResult(status="not_computed", explanation="computed in Phase 4 (M4)"),
    )
    DETAIL_PATH.parent.mkdir(parents=True, exist_ok=True)
    DETAIL_PATH.write_text(json.dumps(detail, ensure_ascii=False, indent=1, default=str))
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    (SITE_DATA / "metrics.json").write_text(m.model_dump_json(indent=2, by_alias=True) + "\n")
    return m


def write_error_doc(top: int = 10) -> str:
    """docs/extraction_errors.md from the error tally (counts are generated; interpretation is human)."""
    path = ROOT / "docs" / "extraction_errors.md"
    head = "# M1 extraction errors\n\nGenerated by `python -m lip m1 errors` from `data/interim/m1/error_tally.json`. Do not edit the counts by hand.\n\n"
    if not TALLY_PATH.exists():
        body = ("**Status: not yet available.** The error analysis needs both the adjudicated gold set "
                "(`data/gold/annotations/gold.json`) and LLM predictions on the sample. Neither exists yet:\n\n"
                "- the extraction has not been run on the gold sample yet;\n"
                "- the two independent human annotations and the adjudication are not complete.\n\n"
                "Once both exist, run `python -m lip m1 eval` and then `python -m lip m1 errors`.\n")
        path.write_text(head + body)
        return path.read_text()
    errs = json.loads(TALLY_PATH.read_text())

    def key(e):
        if e["field"] in CATEGORICAL_FIELDS:
            return (e["type"], e["field"], f"gold={e['gold']} → pred={e['pred']}")
        return (e["type"], e["field"], "")
    groups = defaultdict(list)
    for e in errs:
        groups[key(e)].append(e)
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]))[:top]
    lines = [head, f"Total error events: {len(errs)}. Top {len(ranked)} patterns:\n"]
    for i, ((typ, field, detail), es) in enumerate(ranked, 1):
        by_stratum = Counter(e["stratum"] for e in es)
        lines.append(f"## {i}. `{typ}` · `{field}` {detail} — {len(es)} events\n")
        lines.append("Strata: " + ", ".join(f"{s} {n}" for s, n in by_stratum.most_common()) + "\n")
        for e in es[:3]:
            lines.append(f"- `{e['passageId']}`: gold `{e['gold']}` · pred `{e['pred']}`" + (f" — “{e.get('goldSpan','')}”" if e.get("goldSpan") else ""))
        lines.append("\n**Interpretation:** _to be written after reviewing the examples._\n")
    path.write_text("\n".join(lines))
    return path.read_text()
