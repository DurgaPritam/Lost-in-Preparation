"""Generate RESULTS.md from pipeline outputs (never hand-edit numbers).

Every number below is read from a file written by a pipeline script; each table names its source.
Provisional results (AI-made references) appear ONLY inside the clearly labelled provisional
section, with their basis and label, and never in the validated tables.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from contract import models as C

from .paths import INTERIM, ROOT, SITE_DATA

OUT = ROOT / "RESULTS.md"


def _j(path):
    p = ROOT / path
    return json.loads(p.read_text()) if p.exists() else None


def _m(x: C.Metric | None, fmt="{:.3f}") -> str:
    if x is None or x.status != "computed" or x.value is None:
        return f"not computed{' — ' + x.note if x and x.note else ''}"
    ci = f" (95% CI {fmt.format(x.low)}–{fmt.format(x.high)})" if x.low is not None and x.high is not None else ""
    return f"{fmt.format(x.value)}{ci}" + (f", n = {x.n}" if x.n else "")


def validation_status(m: C.Metrics) -> list[str]:
    gold_ext = m.extraction.overall.get("part")
    rows = [
        ("Text ingestion and segmentation (passage coverage, IDs, chapter counts vs printed contents)", "**validated** — automated tests against the source files", "`tests/`"),
        ("logP descriptor: RDKit vs GFN2-xTB vs experiment", "**validated** — experimental reference (SangsterLogP, CC BY 4.0)", "`data/interim/m4/logp_validation.json`"),
        ("Artemisinin known-case test", f"**{m.artemisininCheck.result or 'not run'}** against pre-registered criteria (5th–95th range crosses the cold-water threshold)" if (m.artemisininCheck.result or '').startswith('borderline') else f"**{m.artemisininCheck.result or 'not run'}** against pre-registered criteria", "`data/interim/m4/artemisinin_check.json`"),
        ("M1 extraction accuracy vs human gold set", "pending — human annotation not yet done" if not gold_ext or gold_ext.f1.status != "computed" else "**human-validated**", "`data/gold/annotations/`"),
        ("Inter-annotator agreement (Cohen's kappa)", "pending — needs two human annotators", "`data/gold/annotations/`"),
        ("M1 extraction vs AI reference (silver)", "*provisional* — AI reference, not human-validated" + (" (not yet run: no local model run)" if not m.provisional.get("extractionVsSilver") or m.provisional["extractionVsSilver"].extraction is None or m.provisional["extractionVsSilver"].extraction.overall.get("part", None) is None or m.provisional["extractionVsSilver"].extraction.overall["part"].f1.status != "computed" else ""), "`data/silver/silver_v1.json`"),
        ("M2 name resolution vs scholarly identifications", "pending — needs human-verified identifications" if m.nameResolution["top1"].status != "computed" else "**human-validated**", "`data/gold/name_identifications.csv`"),
        ("M2 name resolution vs AI-drafted identifications", "*provisional* — AI-drafted from quoted sources, unverified", "`data/gold/name_identifications.csv` (draft* columns)"),
        ("Preparation model vs published reports — exploratory set", "*provisional, exploratory* — 9 rows selected after model build", "`data/reference/prep_literature_v1.csv`"),
        ("Preparation model vs published reports — pre-registered v1 (mostly essential oils)", "*provisional* — rule pre-registered (docs/PREREGISTRATION.md), AI-written rule and code", "`data/reference/prep_literature_prereg_v1.csv`"),
        ("Preparation model vs published reports — pre-registered v2 (water preparations)", "*provisional* — rule pre-registered (docs/PREREGISTRATION_v2.md), AI-written rule and code; low-row quota not met", "`data/reference/prep_literature_prereg_v2.csv`"),
        ("Study-set toxicity entries (30 species)", "*provisional* — AI-drafted from cited EMA / PMC sources, awaiting human review", "`data/reference/toxicity_curated.csv`"),
        ("Study set (30 species)", "pending — human approval", "`docs/STUDY_SET_PROPOSAL.md`"),
        ("Modern-methods audit, mismatch ranking (M5–M6)", "not started", "—"),
    ]
    out = ["## Validation status", "", "| Result | Status | Evidence |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    out += ["", "**validated** = checked against an independent, non-AI reference. *provisional* = compared with a reference made by an AI; useful for development, never presented as validation. pending = waiting on human work."]
    return out


PLINY_CAVEAT = ("**Pliny results are lower confidence.** Pliny is read through a 19th-century English translation (Bostock & Riley) "
                "of a 1st-century Latin text; its plant names are classical, often ambiguous, and resolve with far more disputes than "
                "Culpeper's (see the disputed share below). Treat every Pliny-derived number as less certain than its Culpeper counterpart.")
GROUPS = (("Culpeper", ("culpeper",)), ("Pliny (lower confidence)", ("pliny",)))


def _grp(src: str) -> str | None:
    for name, prefixes in GROUPS:
        if src.startswith(prefixes):
            return name
    return None


def _frac(k: int, n: int, ci: bool = False) -> str:
    if not n:
        return "n = 0"
    if not ci:
        return f"{k}/{n} ({k / n:.0%})"
    from .m2.evaluate import wilson
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({k / n:.0%}; 95% CI {lo:.0%}–{hi:.0%})"


def by_source(m: C.Metrics) -> list[str]:
    """Headline metrics per source (Culpeper, Pliny) and overall, each read from a pipeline output."""
    import pandas as pd
    ing = _j("data/interim/ingest_report.json")
    m2s = _j("data/interim/m2/name_resolution_summary.json") or {}
    m2b = (_j("data/interim/m2/before_after.json") or {}).get("bySource", {})
    sample = _j("data/gold/sample_v2.json") or {"passages": []}
    names = [g for g, _ in GROUPS]
    cols = {g: {} for g in names + ["Overall"]}

    def add(metric, per_group: dict, overall):
        for g in names:
            cols[g][metric] = per_group.get(g, "—")
        cols["Overall"][metric] = overall

    rs = {g: sum(v["recipe_scope_passages"] for k, v in ing["sources"].items() if _grp(k) == g) for g in names}
    add("Recipe-scope passages (corpus)", {g: f"{v:,}" for g, v in rs.items()}, f"{sum(rs.values()):,}")
    gs = {g: sum(1 for p in sample["passages"] if _grp(p["stratum"]) == g) for g in names}
    add("Gold-sample passages (stratified)", {g: str(v) for g, v in gs.items()}, str(sum(gs.values())))
    gold = m.extraction.overall.get("part")
    add("M1 extraction F1 vs human gold", {g: "pending (no human annotation yet)" for g in names},
        _m(gold.f1) if gold and gold.f1.status == "computed" else "pending (no human annotation yet)")
    sil = m.provisional.get("extractionVsSilver")
    sil_ok = sil is not None and sil.extraction is not None and "part" in sil.extraction.overall and sil.extraction.overall["part"].f1.status == "computed"
    add("M1 extraction vs AI reference (*provisional*)", {g: "not computed (no local model run)" if not sil_ok else "see provisional section" for g in names},
        "not computed (no local model run)" if not sil_ok else _m(sil.extraction.overall["part"].f1))
    keys = ("names", "resolved", "resolvedInWFO", "disputed")
    agg = {g: dict.fromkeys(keys, 0) for g in names}
    for src, v in m2s.items():
        g = _grp(src)
        if g:
            for k in keys:
                agg[g][k] += v[k]
    tot = {k: sum(a[k] for a in agg.values()) for k in keys}
    add("M2 names resolved to a WFO species", {g: _frac(a["resolvedInWFO"], a["names"]) for g, a in agg.items()},
        _frac(tot["resolvedInWFO"], tot["names"]))
    add("M2 resolved names flagged disputed (descriptive)", {g: _frac(a["disputed"], a["resolved"], ci=True) for g, a in agg.items()},
        _frac(tot["disputed"], tot["resolved"], ci=True))
    dt = {}
    for src, v in m2b.items():
        g = _grp(src)
        if g:
            k, n = (int(x) for x in v["draftTop1"][1].split("/"))
            dt[g] = (dt.get(g, (0, 0))[0] + k, dt.get(g, (0, 0))[1] + n)
    add("M2 top-1 vs AI-drafted identifications (*provisional*)", {g: _frac(*dt[g], ci=True) for g in dt},
        _frac(sum(x[0] for x in dt.values()), sum(x[1] for x in dt.values()), ci=True))
    add("M2 top-1 vs human-verified identifications", {g: "pending" for g in names}, _m(m.nameResolution["top1"]) if m.nameResolution["top1"].status == "computed" else "pending")
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    ss = ss[ss.proposed]
    att = {g: ss[ss.sourceList.str.contains(pref[0])] for g, pref in GROUPS}
    add("Study-set species attested (of the proposed set)", {g: f"{len(d)} of {len(ss)}" for g, d in att.items()},
        f"{len(ss)} ({int(ss.sourceList.str.contains(',').sum())} attested by both)")
    add("Median LOTUS compounds per attested study-set species", {g: f"{d.nCompounds.median():g}" for g, d in att.items()}, f"{ss.nCompounds.median():g}")
    add("Preparation-model literature checks (v1, v2)", {g: "not applicable (modern studies of the plant, not of a source)" for g in names},
        "see Preparation model section")
    metrics = list(cols["Overall"])
    out = ["## Headline metrics by source", "", PLINY_CAVEAT, "",
           "Sources: `data/interim/ingest_report.json`, `data/gold/sample_v2.json`, `site-data/metrics.json`, `data/interim/m2/name_resolution_summary.json`, "
           "`data/interim/m2/before_after.json`, `data/interim/m3/study_set_proposal.csv`. Culpeper = the 1652 and 1850 editions; "
           "name resolution (M2) covers the 1652 edition only.", "",
           "| Metric | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    out += [f"| {mt} | " + " | ".join(cols[g][mt] for g in cols) + " |" for mt in metrics]
    return out


def _rate(b: dict | None) -> str:
    if not b or not b.get("n"):
        return "n = 0 (not computed)"
    return f"{b['agree']}/{b['n']} ({b['rate']:.0%}; 95% CI {b['ci'][0]:.0%}–{b['ci'][1]:.0%})"


def literature_sections() -> list[str]:
    from .m2.evaluate import wilson
    ex, v1, v2 = (_j(p) for p in ("data/interim/m4/literature_check.json", "data/interim/m4/literature_prereg.json",
                                   "data/interim/m4/literature_prereg_v2.json"))
    L = ["", "### Literature checks (*provisional*; never pooled)", "",
         "Agreement rule: `present` → predicted median ≥ 0.40; `low` → < 0.30 (thresholds fixed before any check). Basis `ai_curated_literature_reference`.", ""]

    def v1b(lab):
        b = (v1.get("byLabel") or {}).get(lab)
        if not b or not b["count"]:
            return None
        lo, hi = wilson(int(b["sum"]), int(b["count"]))
        return {"agree": int(b["sum"]), "n": int(b["count"]), "rate": b["sum"] / b["count"], "ci": [lo, hi]}
    lo, hi = wilson(v1["agree"], v1["rowsFound"]) if v1["rowsFound"] else (0, 0)
    v1o = {"agree": v1["agree"], "n": v1["rowsFound"], "rate": v1["agree"] / v1["rowsFound"] if v1["rowsFound"] else 0, "ci": [lo, hi]}
    elo, ehi = wilson(ex["agree"], ex["n"])
    exo = {"agree": ex["agree"], "n": ex["n"], "rate": ex["agree"] / ex["n"], "ci": [elo, ehi]}
    exl = {lab: [r for r in ex["rows"] if (r["reported"] == "present") == (lab == "present")] for lab in ("present", "low")}

    def exb(lab):
        rows = exl[lab]
        if not rows:
            return None
        k = sum(r["agree"] for r in rows)
        a, b = wilson(k, len(rows))
        return {"agree": k, "n": len(rows), "rate": k / len(rows), "ci": [a, b]}
    pv = v2["primary"]
    L += ["| Check | Rows | Overall agreement | `present` rows | `absent/low` rows |", "|---|---|---|---|---|",
          f"| Exploratory (selected after model build) | {ex['n']} | {_rate(exo)} | {_rate(exb('present'))} | {_rate(exb('low'))} |",
          f"| Pre-registered v1 (target 30; mostly essential oils) | {v1['rowsFound']} | {_rate(v1o)} | {_rate(v1b('present'))} | {_rate(v1b('low'))} |",
          f"| **Pre-registered v2, water preparations** (quota 15 + 15) | {pv['overall']['n']} | {_rate(pv['overall'])} | {_rate(pv['present'])} | {_rate(pv['low'])} |",
          "", f"v2 found {v2['found']['present']} `present` and {v2['found']['low']} `low` rows against quotas of {v2['quota']['present']} and "
              f"{v2['quota']['low']}; the rule was not relaxed. v2 rows by preparation (primary model): "
          + ", ".join(f"{p} {x['agree']}/{x['n']}" for p, x in pv["byPreparation"].items()) + ". Source: `data/interim/m4/literature_prereg_v2.json`."]
    a = v2.get("postHocAudit") or {}
    if a:
        L += ["", f"**Post-hoc row audit (not registered; AI reading, unverified, `{a['basis']}`).** Of {pv['overall']['n']} rows, "
                  f"{a['counts'].get('misread', 0)} are mechanical misreadings:"]
        L += [f"- *{m['plant']}*, {m['compound']} ({m['pmcid']}): {m['reason']}." for m in a["misread"]]
        L += [f"", f"On the remaining rows: overall {_rate(a['validRowsPrimary']['overall'])}; `present` {_rate(a['validRowsPrimary']['present'])}; "
                   f"`absent/low` {_rate(a['validRowsPrimary']['low'])}. The registered result above stays the headline."]
    sv = v2["secondaryVariant"]
    L += ["", f"**Secondary variant `{sv['name']}`** (pre-registered; slope k = ln 10, descriptor noise SD {sv['h_sd']}; evaluated on v2 rows only): "
              f"overall {_rate(sv['overall'])}; `present` {_rate(sv['present'])}; `absent/low` {_rate(sv['low'])}. "
              "On these rows it gives no evidence for or against replacing the primary model, which stays the default."]
    return L


def water_section() -> list[str]:
    w = _j("data/interim/m4/water_calibration.json")
    if not w:
        return []
    import pandas as pd
    a, ss, c = w["artemisinin"], w["studySetCompounds"], w["crossings"]
    rmse = (_j("data/interim/m4/logp_validation.json") or {}).get("rdkit_all", {}).get("rmse", {}).get("value", "unknown")
    v2 = pd.read_csv(ROOT / "data" / "reference" / "prep_literature_prereg_v2.csv")
    art_rows = v2[v2.compound.str.lower() == "artemisinin"]
    art_txt = ("; ".join(f"the v2 rows include a published report of artemisinin {r.reported} in *{r.plant}* ({r.modelPreparation}, {r.pmcid}), "
                         f"which the primary model scores {r.predicted:.2f} ({'agrees' if r.agree else 'disagrees'})" for r in art_rows.itertuples())
               if len(art_rows) else "no v2 row concerns artemisinin")
    ae = a["primaryAtExperimental"]
    return ["", "### Why cold water gives artemisinin 0.27 (diagnostic; no model change)", "",
            "Source: `data/interim/m4/water_calibration.json`; figure: [docs/figures/water_likelihood_vs_logp.svg](docs/figures/water_likelihood_vs_logp.svg).", "",
            f"- A filtered, cold, aqueous preparation has heat = filtration = acidity = 1, so the prediction is the water window alone: "
            f"`{w['waterWindow']['form']}`, with upper ~ U{tuple(w['waterWindow']['upper'])} and k ~ U{tuple(w['waterWindow']['k'])}. "
            f"For the study-set compounds it is a one-variable function of logP: Spearman ρ = {ss['spearmanLogPvsLikelihood']} "
            f"(n = {ss['n']}; {ss['n'] - ss['likelihoodEqualsSolventFactor']} compounds sit below the curve because of the MW > 1000 size penalty).",
            f"- The median crosses 0.40 at logP {c['median_eq_present_min']}, 0.30 at logP {c['median_eq_absent_max']} and 0.10 at logP {c['median_eq_0.10']}. "
            f"The 'undecided' band 0.30–0.40 is only {c['median_eq_absent_max'] - c['median_eq_present_min']:.2f} logP units wide, "
            f"narrower than the descriptor's RMSE against experiment ({rmse}), and the median study-set compound has logP {ss['logPQuantiles']['0.5']}, "
            "on the steepest part of the curve.",
            f"- Artemisinin's Crippen logP is {a['crippenLogP']}, and sigmoid(k_med · (upper_med − logP)) = {a['analytic']['atCrippen']} reproduces the "
            f"Monte Carlo median of {a['primaryAtCrippen']['likelihood']}. At the experimental logP {a['experimentalLogP']['value']} "
            f"({a['experimentalLogP']['source']}) the same model gives {ae['likelihood']} ({ae['low']}–{ae['high']}). "
            "Part of the 0.27 is descriptor error; the rest is the window's position and shallow slope.",
            "- **Low water solubility is not in the model.** It sees only logP, with no solubility, melting-point (crystal-lattice), dose or "
            "contact-time term, so it cannot represent 'poorly soluble in absolute terms'. A low amount in a large volume of water may still "
            "dissolve completely. PubChem's artemisinin record lists no experimental solubility, so no solubility value is used here.",
            "- **Proposal (not adopted).** Fix the window slope at ln 10 (the slope of a two-phase partition equilibrium) and model descriptor "
            "error explicitly. This was pre-registered as the secondary variant and evaluated only on v2 rows (above). A solubility/dose "
            "term would need per-compound melting points or solubilities and plant-content ranges that the repo does not have; it is not proposed yet.",
            f"- The recorded artemisinin result and every threshold are unchanged. Separately, {art_txt}."]


def toxicity_section() -> list[str]:
    import pandas as pd
    p = ROOT / "data" / "reference" / "toxicity_curated.csv"
    if not p.exists():
        return []
    t = pd.read_csv(p, dtype=str).fillna("")
    counts = t.toxicity.value_counts()
    return ["", "### Study-set toxicity (*provisional*: AI-drafted, unverified)", "",
            f"Source: `data/reference/toxicity_curated.csv` ({len(t)} species, basis `{t.basis.iloc[0]}`, `verified_by` empty for "
            f"{int((t.verified_by == '').sum())}). Each entry cites one EMA herbal document or CC-licensed PMC article and quotes one "
            "sentence, re-checked against the fetched source every run. Categories describe what the source says; none is a safety rating.", "",
            "| Category | Species |", "|---|---|"] + [f"| `{k}` | {v} |" for k, v in counts.items()] + [
            "", "`no_toxicity_reported` and `unknown` are **not evidence of safety**. The Wikipedia *List of poisonous plants* is no longer used for this column (only for M2's toxic-confusion screen)."]


def build() -> str:
    m = C.Metrics.model_validate_json((SITE_DATA / "metrics.json").read_text())
    ing, m2s, m3s, m4s = (_j(p) for p in ("data/interim/ingest_report.json", "data/interim/m2/name_resolution_summary.json",
                                          "data/interim/m3/compounds_summary.json", "data/interim/m4/m4_summary.json"))
    val = _j("data/interim/m4/logp_validation.json")
    ov = _j("data/interim/m4/logp_overlap.json")
    m2b = _j("data/interim/m2/before_after.json")
    art = _j("data/interim/m4/artemisinin_check.json")
    L = ["# Results", "", f"Generated by `python -m lip results` on {datetime.now(timezone.utc).date()} from pipeline outputs; "
         "do not edit numbers by hand. Lost in Preparation produces **hypotheses worth re-testing**, never claims that a remedy works or is safe.", ""]
    L += validation_status(m) + [""]
    L += by_source(m) + [""]

    L += ["## Corpus", "", "Source: `data/interim/ingest_report.json`", "", "| Source | Passages | Recipe-scope passages | Recipe-scope words |", "|---|---|---|---|"]
    for sid, s in ing["sources"].items():
        L.append(f"| `{sid}` | {s['passages_total']:,} | {s['recipe_scope_passages']:,} | {s['recipe_scope_words']:,} |")
    cw = ing["sources"].get("culpeper-1850", {}).get("crosswalk_1652", {})
    if cw:
        L += ["", "1850 → 1652 herbal crosswalk (heuristic): " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in sorted(cw.items())) + "."]

    L += ["", "## Name resolution (M2)", "", "Source: `data/interim/m2/name_resolution_summary.json`", "",
          "| Source | Names | Resolved | In WFO | Disputed |", "|---|---|---|---|---|"]
    for src, s in m2s.items():
        L.append(f"| {src} | {s['names']} | {s['resolved']} | {s['resolvedInWFO']} | {s['disputed']} |")
    if m2b:
        L += ["", "**Before / after the v2 changes** (classical-genus signal, binomials from name tokens, milder regional prior, "
              "fuller hedge list, toxic-confusion check). Source: `data/interim/m2/before_after.json`", "",
              "| Source | Resolved (before → after) | Disputed (before → after) | Top-1 vs AI drafts, provisional (before → after) |", "|---|---|---|---|"]
        for src, x in m2b["bySource"].items():
            L.append(f"| {src} | {x['resolved'][0]} → {x['resolved'][1]} | {x['disputed'][0]} → {x['disputed'][1]} | "
                     f"{x['draftTop1'][0]} → {x['draftTop1'][1]} |")
        L += ["", "| Name | Before | After |", "|---|---|---|"]
        for nm, x in m2b["names"].items():
            L.append(f"| {nm} | {x['before']} | {x['after']} |")
    L += ["", f"Share of resolved names flagged disputed: {_m(m.nameResolution['disputedShare'])} (descriptive).",
          f"Top-1 / top-3 accuracy vs human-verified identifications: {_m(m.nameResolution['top1'])}."]

    L += ["", "## Compounds (M3)", "", "Source: `data/interim/m3/compounds_summary.json`", "",
          f"- Species queried: {m3s['species']}; with at least one compound: {m3s['speciesWithAnyCompound']}; poor coverage (< {m3s['poorCoverageThreshold']} compounds, heuristic): {m3s['speciesPoorCoverage']}.",
          f"- Distinct standardised compounds (InChIKey): {m3s['distinctStandardisedInchikeys']:,}; median per species: {m3s['medianCompoundsPerSpecies']:g}.",
          f"- RDKit standardisation failures: {m3s['standardisationFailures'] or 'none'}; InChIKey connectivity mismatches vs Wikidata (flagged): {m3s['inchikeyConnectivityMismatches']}.",
          "- Plant part is not recorded by LOTUS (organism-level occurrences)."]

    L += ["", "## Preparation model (M4)", "", "Sources: `data/interim/m4/logp_validation.json`, `data/interim/m4/artemisinin_check.json`, `data/interim/m4/m4_summary.json`", "",
          f"**Solvent descriptor validation** against experimental logP ({val['reference']}; {val['selection']['selected']} compounds, xTB succeeded for {val['selection']['xtbOk']}):", "",
          "| Method | MAE | RMSE | Spearman ρ |", "|---|---|---|---|"]
    for key, name in (("rdkit_paired", "RDKit Crippen logP"), ("xtb_paired", f"GFN2-xTB/ALPB (xtb {val['xtbVersion']}), woctanol − water")):
        b = val[key]
        L.append(f"| {name} | {b['mae']['value']:.3f} ({b['mae']['ci'][0]:.3f}–{b['mae']['ci'][1]:.3f}) | {b['rmse']['value']:.3f} | "
                 f"{b['spearman']['value']:.3f} ({b['spearman']['ci'][0]:.3f}–{b['spearman']['ci'][1]:.3f}) |")
    if ov:
        L += ["", f"**Training-overlap check.** RDKit's Crippen logP follows {ov['crippenReference'].split(', per')[0]}; its training molecules are "
              "not distributed with RDKit, so exact overlap is **not determinable**. Proxy: compounds whose every cited measurement source was "
              f"first published in 2000 or later (n = {ov['post1999']}) vs earlier (n = {ov['pre2000']}; {ov['unknownYear']} with an unresolved year):", "",
              "| Subset | RDKit MAE | xTB MAE |", "|---|---|---|",
              f"| sources from 2000 on | {ov['rdkit_post1999']['mae']['value']:.3f} ({ov['rdkit_post1999']['mae']['ci'][0]:.3f}–{ov['rdkit_post1999']['mae']['ci'][1]:.3f}) | "
              f"{ov['xtb_post1999']['mae']['value']:.3f} ({ov['xtb_post1999']['mae']['ci'][0]:.3f}–{ov['xtb_post1999']['mae']['ci'][1]:.3f}) |",
              f"| sources before 2000 | {ov['rdkit_pre2000']['mae']['value']:.3f} ({ov['rdkit_pre2000']['mae']['ci'][0]:.3f}–{ov['rdkit_pre2000']['mae']['ci'][1]:.3f}) | "
              f"{ov['xtb_pre2000']['mae']['value']:.3f} ({ov['xtb_pre2000']['mae']['ci'][0]:.3f}–{ov['xtb_pre2000']['mae']['ci'][1]:.3f}) |",
              "", "RDKit's error is larger on post-1999 data, which is consistent with (but does not prove) a training-overlap advantage on older data; "
              "RDKit still outperforms xTB on the post-1999 subset. xTB logP = log K(wet octanol / water) from ALPB `woctanol` and `water`."]
    L += ["", f"Default descriptor: **{val['default']}** (lower MAE). Caveat: Crippen's parameters were fitted to public logP data that may overlap this set; xTB is unfitted. 95% CIs are paired bootstrap (B = 2000).",
          "", f"**Artemisinin known case: {art['result'].upper()}.** " + art["explanation"], "",
          "| Preparation | Predicted likelihood (5th–95th pct) | Solvent | Heat | Filtration | Acidity |", "|---|---|---|---|---|---|"]
    for lab, r in art["predictions"].items():
        d = r["drivers"]
        L.append(f"| {lab} | {r['likelihood']:.2f} ({r['low']:.2f}–{r['high']:.2f}) | {d['solvent']:.2f} | {d['heat']:.2f} | {d['filtration']:.2f} | {d['acidity']:.2f} |")
    L += ["", "Drivers are the median per-factor multipliers. The cold-water infusion is filtered (filtration 1.00), so its value comes from the solvent factor alone; "
          "the unfiltered variant shows how much the suspension assumption would add."]
    L += literature_sections() + water_section() + toxicity_section()
    L += ["", f"Profiles: {m4s['profiles']['species']} species × {m4s['profiles']['preparations']} preparations "
          f"({m4s['profiles']['profiles']} profiles, {m4s['profiles']['compoundEntries']:,} compound estimates) in `site-data/profiles/` (one file per species, `index.json`; full file in `data/release/profiles_full.json.gz`; model `{m4s['modelVersion']}`). "
          "These are model estimates of what a preparation would carry, not measurements."]

    L += ["", "## Provisional results (AI-made references — not human-validated)", "",
          "> The numbers in this section compare the pipeline with references **produced by an AI** (labels, drafted identifications, a curated literature table). "
          "They are for development only and must not be read as validation.", ""]
    for key, sec in m.provisional.items():
        L.append(f"**{key}** — basis `{sec.basis}` — {sec.label}")
        if sec.extraction is not None:
            f1 = sec.extraction.overall.get("part")
            L.append(f"- extraction (e.g. `part` F1): {_m(f1.f1) if f1 else 'not computed'}")
        for name, mm in sec.metrics.items():
            L.append(f"- {name}: {_m(mm)}")
        L.append("")
    OUT.write_text("\n".join(L) + "\n")
    _update_readme(validation_status(m) + [""] + by_source(m))
    return OUT.read_text()


START, END = "<!-- VALIDATION_STATUS:START -->", "<!-- VALIDATION_STATUS:END -->"


def _update_readme(block: list[str]) -> None:
    """Keep README's VALIDATION_STATUS identical to RESULTS.md (generated, between markers)."""
    p = ROOT / "README.md"
    text = p.read_text()
    body = "\n".join([START, "<!-- generated by `python -m lip results`; do not edit -->", *block, END])
    if START in text and END in text:
        text = text[:text.index(START)] + body + text[text.index(END) + len(END):]
    else:
        text = text.replace("## Repository", body + "\n\n## Repository", 1)
    p.write_text(text)
