"""Diagnostic (no model change): how the cold-water likelihood behaves across logP.

Writes data/interim/m4/water_calibration.json and docs/figures/water_likelihood_vs_logp.svg.
- curve: the primary model's cold-water median and 5–95% range on a logP grid (no heat alert, MW 300);
- points: every study-set compound's cold-water median (data/interim/m4/profiles_long.parquet);
- artemisinin sensitivity: the same model at the Crippen logP it uses and at the experimental logP
  PubChem lists (SangsterLogP). These are sensitivity numbers for the diagnosis only; they do not
  change the model, its thresholds or the recorded artemisinin result.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ..http import get_json
from ..paths import INTERIM, ROOT
from . import model as M

OUT_JSON = INTERIM / "m4" / "water_calibration.json"
OUT_SVG = ROOT / "docs" / "figures" / "water_likelihood_vs_logp.svg"
PREP = "cold water infusion"
ART_CRIPPEN = 2.395  # data/interim/m4/artemisinin_check.json "lipophilicity"
PUBCHEM_LOGP = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/68827/JSON"


def _exp_logp_artemisinin() -> dict:
    d = get_json("pubchem", PUBCHEM_LOGP, params={"heading": "LogP"})
    refs = {r["ReferenceNumber"]: r.get("SourceName") for r in d["Record"].get("Reference", [])}
    for sec in d["Record"]["Section"]:
        stack = [sec]
        while stack:
            s = stack.pop()
            stack.extend(s.get("Section", []))
            for i in s.get("Information", []):
                v = i.get("Value", {})
                txt = (v.get("StringWithMarkup") or [{}])[0].get("String")
                if txt:
                    return {"value": float(txt), "source": f"PubChem CID 68827, LogP ({refs.get(i.get('ReferenceNumber'))})",
                            "url": "https://pubchem.ncbi.nlm.nih.gov/compound/68827#section=LogP"}
    return {"value": None, "source": "unknown"}


def _sim(h: float, cfg: dict, **kw) -> dict:
    c = M.Compound("grid", float(h), False, [], False, 300.0)
    return M.estimate(c, M.BY_LABEL[PREP], cfg, sd=M.descriptor_sd()["sd"], **kw)


def _cross(xs, ys, level):
    for i in range(1, len(xs)):
        if (ys[i - 1] - level) * (ys[i] - level) <= 0 and ys[i - 1] != ys[i]:
            return round(float(xs[i - 1] + (level - ys[i - 1]) * (xs[i] - xs[i - 1]) / (ys[i] - ys[i - 1])), 3)
    return None


def run() -> dict:
    cfg = M.load_config()
    thr = cfg["literature_check"]
    grid = np.round(np.arange(-4.0, 9.01, 0.1), 2)
    sims = [_sim(h, cfg) for h in grid]
    med = [s["likelihood"] for s in sims]
    prof = pd.read_parquet(INTERIM / "m4" / "profiles_long.parquet")
    cw = prof[prof.preparation == PREP].drop_duplicates("inchikey")
    exact = cw[np.isclose(cw.likelihood, cw.driver_solvent)]
    exp = _exp_logp_artemisinin()
    w = cfg["solvent"]["water"]["upper"]
    k = cfg["mc"]["steepness"]
    art = {
        "crippenLogP": ART_CRIPPEN,
        "primaryAtCrippen": _sim(ART_CRIPPEN, cfg),
        "experimentalLogP": exp,
        "primaryAtExperimental": _sim(exp["value"], cfg) if exp["value"] is not None else None,
        "analytic": {"upperMedian": float(np.mean(w)), "kMedian": float(np.mean(k)),
                     "formula": "median ~= sigmoid(k_med * (upper_med - logP))",
                     "atCrippen": round(float(1 / (1 + np.exp(-np.mean(k) * (np.mean(w) - ART_CRIPPEN)))), 4)},
        "note": "Sensitivity numbers for the diagnosis only; the recorded artemisinin result is unchanged.",
    }
    out = {
        "preparation": PREP, "modelVersion": M.config_version(cfg),
        "waterWindow": {"upper": w, "k": k, "form": "f = sigmoid(k * (upper - logP)); no solubility, melting-point, dose or contact-time term"},
        "curve": [{"logP": float(h), "median": s["likelihood"], "p5": s["low"], "p95": s["high"]} for h, s in zip(grid, sims)],
        "crossings": {"median_eq_present_min": _cross(grid, med, thr["present_min"]),
                      "median_eq_absent_max": _cross(grid, med, thr["absent_max"]),
                      "median_eq_0.10": _cross(grid, med, 0.10)},
        "studySetCompounds": {
            "n": int(len(cw)),
            "likelihoodEqualsSolventFactor": int(len(exact)),
            "spearmanLogPvsLikelihood": round(float(cw[["lipophilicity", "likelihood"]].corr("spearman").iloc[0, 1]), 4),
            "medianAtLeastPresentMin": int((cw.likelihood >= thr["present_min"]).sum()),
            "medianBelowAbsentMax": int((cw.likelihood < thr["absent_max"]).sum()),
            "between": int(((cw.likelihood >= thr["absent_max"]) & (cw.likelihood < thr["present_min"])).sum()),
            "logPQuantiles": {q: round(float(cw.lipophilicity.quantile(q)), 3) for q in (0.05, 0.25, 0.5, 0.75, 0.95)},
        },
        "artemisinin": art,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2))
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(_svg(out, cw, thr))
    return {k2: out[k2] for k2 in ("crossings", "studySetCompounds", "artemisinin")}


# --- figure (hand-written SVG; no plotting dependency) -----------------------------------------

def _svg(out: dict, cw: pd.DataFrame, thr: dict) -> str:
    W, H = 760, 534
    L, R, T = 64, 24, 70
    PH, GAP, HH = 300, 34, 70           # plot height, gap, histogram height
    x0, x1 = -4.0, 9.0
    sx = lambda x: L + (min(max(x, x0), x1) - x0) / (x1 - x0) * (W - L - R)  # noqa: E731
    sy = lambda y: T + (1 - y) * PH  # noqa: E731
    ink, ink2, muted, grid, blue, band, surf = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#2a78d6", "#cfe0f6", "#fcfcfb"
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'font-family="system-ui, -apple-system, Segoe UI, sans-serif" role="img" '
         f'aria-label="Cold-water likelihood versus logP for study-set compounds">',
         f'<rect width="{W}" height="{H}" fill="{surf}"/>',
         f'<text x="{L}" y="24" font-size="15" font-weight="600" fill="{ink}">Cold water infusion: predicted likelihood vs logP</text>',
         f'<text x="{L}" y="40" font-size="12" fill="{ink2}">Primary model {out["modelVersion"]}. Dots: study-set compounds '
         f'(n = {out["studySetCompounds"]["n"]}); line: median; band: 5–95% range incl. descriptor error.</text>',
         f'<text x="{L}" y="54" font-size="12" fill="{ink2}">Model estimate, not a measurement.</text>']
    for y in (0, 0.25, 0.5, 0.75, 1.0):
        s.append(f'<line x1="{L}" x2="{W - R}" y1="{sy(y):.1f}" y2="{sy(y):.1f}" stroke="{grid}" stroke-width="1"/>')
        s.append(f'<text x="{L - 8}" y="{sy(y) + 4:.1f}" font-size="11" fill="{ink2}" text-anchor="end">{y:g}</text>')
    curve = out["curve"]
    top = " ".join(f"{sx(c['logP']):.1f},{sy(c['p95']):.1f}" for c in curve)
    bot = " ".join(f"{sx(c['logP']):.1f},{sy(c['p5']):.1f}" for c in reversed(curve))
    s.append(f'<polygon points="{top} {bot}" fill="{band}" opacity="0.8"/>')
    for lvl, name in ((thr["present_min"], "present ≥ 0.40"), (thr["absent_max"], "low &lt; 0.30")):
        s.append(f'<line x1="{L}" x2="{W - R}" y1="{sy(lvl):.1f}" y2="{sy(lvl):.1f}" stroke="{muted}" stroke-width="1" stroke-dasharray="4 4"/>')
        s.append(f'<text x="{L + 4}" y="{sy(lvl) - 5:.1f}" font-size="11" fill="{ink2}">{name} (agreement threshold)</text>')
    for r in cw.itertuples():
        s.append(f'<circle cx="{sx(r.lipophilicity):.1f}" cy="{sy(r.likelihood):.1f}" r="2.2" fill="{blue}" fill-opacity="0.35"/>')
    s.append('<polyline fill="none" stroke="{}" stroke-width="2" points="{}"/>'.format(
        blue, " ".join(f"{sx(c['logP']):.1f},{sy(c['median']):.1f}" for c in curve)))
    big = cw[~np.isclose(cw.likelihood, cw.driver_solvent)]
    if len(big):
        s.append(f'<text x="{L + 4}" y="{sy(float(big.likelihood.max())) + 24:.1f}" font-size="11" fill="{ink2}">'
                 f'below the curve: {len(big)} compounds with MW &gt; 1000 (size penalty, heuristic)</text>')
    a = out["artemisinin"]
    pts = [(a["crippenLogP"], a["primaryAtCrippen"]["likelihood"], "artemisinin, Crippen logP {:.2f} → {:.2f}")]
    if a["primaryAtExperimental"]:
        pts.append((a["experimentalLogP"]["value"], a["primaryAtExperimental"]["likelihood"], "experimental logP {:.1f} → {:.2f}"))
    for i, (x, y, fmt) in enumerate(pts):
        s.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="5" fill="{surf}" stroke="{ink}" stroke-width="2"/>')
        s.append(f'<text x="{sx(x) + 10:.1f}" y="{sy(y) + (-8 if i == 0 else 16):.1f}" font-size="11" fill="{ink}">{fmt.format(x, y)}</text>')
    # histogram of compound logP
    hb = T + PH + GAP
    edges = np.arange(x0, x1 + 0.5, 0.5)
    counts, _ = np.histogram(cw.lipophilicity.clip(x0, x1 - 1e-6), bins=edges)
    cmax = max(int(counts.max()), 1)
    for c, e in zip(counts, edges[:-1]):
        if c:
            hgt = c / cmax * HH
            s.append(f'<rect x="{sx(e) + 1:.1f}" y="{hb + HH - hgt:.1f}" width="{sx(e + 0.5) - sx(e) - 2:.1f}" height="{hgt:.1f}" '
                     f'rx="2" fill="{blue}" fill-opacity="0.55"><title>logP {e:g} to {e + 0.5:g}: {c} compounds</title></rect>')
    s.append(f'<line x1="{L}" x2="{W - R}" y1="{hb + HH}" y2="{hb + HH}" stroke="{muted}"/>')
    s.append(f'<text x="{L - 8}" y="{hb + 10}" font-size="11" fill="{ink2}" text-anchor="end">{cmax}</text>')
    s.append(f'<text x="{L}" y="{hb - 6}" font-size="11" fill="{ink2}">Study-set compounds per 0.5 logP (values outside −4…9 shown at the edge)</text>')
    for x in range(-4, 10, 1):
        s.append(f'<text x="{sx(x):.1f}" y="{hb + HH + 16}" font-size="11" fill="{ink2}" text-anchor="middle">{x}</text>')
    s.append(f'<text x="{(L + W - R) / 2:.1f}" y="{hb + HH + 34}" font-size="12" fill="{ink}" text-anchor="middle">'
             f'logP (RDKit Crippen; the model’s default descriptor)</text>')
    s.append(f'<text transform="translate(16 {T + PH / 2:.0f}) rotate(-90)" font-size="12" fill="{ink}" text-anchor="middle">'
             f'Predicted likelihood (median)</text>')
    s.append("</svg>")
    return "\n".join(s) + "\n"
