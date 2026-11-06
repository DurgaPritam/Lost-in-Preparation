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


def _review_status() -> str:
    import pandas as pd
    p = ROOT / "config" / "study_set_review_decisions.csv"
    if not p.exists():
        return "pending — human approval"
    d = pd.read_csv(p)
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    c = d.decision.value_counts()
    return (f"**human-reviewed** — {c.get('approve', 0)} approve, {c.get('unsure', 0)} unsure, {c.get('reject', 0)} reject; "
            f"headline set {int(ss.headline.sum()) if 'headline' in ss else 0} species (unsure counts as reject); "
            f"{int(ss.reReviewRequested.sum()) if 'reReviewRequested' in ss else 0} rows await re-review after reviewer fixes")


def _n_proposed() -> int:
    import pandas as pd
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    return int(ss.proposed.sum())


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
        ("Preparation model vs published reports — pre-registered v3 (paired, within plant)", "*provisional, inconclusive* — too few articles (n in RESULTS); rule pre-registered (docs/PREREGISTRATION_v3.md, one amendment before collection), AI-written rule and code", "`data/reference/prep_literature_prereg_v3_pairs.csv`"),
        ("Genus-signal audit (name resolution)", "*provisional* — AI-reviewed false friends with dictionary quotes, awaiting human review", "`docs/GENUS_SIGNAL_AUDIT.md`"),
        (f"Study-set toxicity entries ({_n_proposed()} species)", "*provisional* — AI-drafted from cited EMA / PMC sources, awaiting human review", "`data/reference/toxicity_curated.csv`"),
        (f"Study set ({_n_proposed()} proposed)", _review_status(), "`docs/STUDY_SET_PROPOSAL.md`"),
        ("**Modern-methods audit (M5): the planned headline result**", "not started", "—"),
        ("Hypothesis ranking (M6)", "rule implemented and stability-tested on model-only candidate pairs (not hypotheses)", "`data/interim/m6/ranking_stability.json`"),
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


def v3_section() -> list[str]:
    v3 = _j("data/interim/m4/literature_prereg_v3.json")
    if not v3:
        return []
    L = ["", "#### Pre-registered v3: paired, within-plant comparison", "",
         "Each scored pair is two compounds X, Y measured in two preparations P1, P2 of the same plant material in one table. The outcome is "
         "the sign of ln[(X/Y in P1) / (X/Y in P2)], which cancels plant content, preparation yield and units, and so tests the extraction "
         "fractions the model predicts, not detection. Source: `data/interim/m4/literature_prereg_v3.json`, "
         "`data/reference/prep_literature_prereg_v3_pairs.csv`.", ""]
    if not v3.get("articles"):
        return L + ["No article met the registered rule; nothing was scored."]
    pr, pc = v3["primary"], v3.get("pairCounts", {})
    ci = pr.get("ci95") or [None, None]
    L += [f"- Articles with an eligible table: {v3['articles']} ({v3['plants']} plants, {v3['tables']} tables); articles with at least one scored pair: {v3['articlesScored']}.",
          f"- Compound pairs: {pc.get('pairsConsidered', 0)} considered; {pc.get('skippedUninformative', 0)} uninformative (zero in both columns); "
          f"{pc.get('noClearDifference', 0)} excluded as no clear difference (|ln DR| < ln 1.25); {pc.get('noStructure', 0)} without a structure; "
          f"{v3['scored']} scored; {v3['abstained']} where the model abstained (|predicted ln DR| < ln 1.25)."]
    if pr.get("meanPerArticleAgreement") is not None:
        L += [f"- **Result: INCONCLUSIVE (n = {v3['articlesScored']} articles).** Mean per-article agreement {pr['meanPerArticleAgreement']:.0%} "
              f"(95% cluster-bootstrap CI {ci[0]:.0%}–{ci[1]:.0%}). The registered verdict is \"{pr['verdict']}\"; with so few articles the "
              "check can neither support nor reject the model.",
              f"- Pooled over pairs (descriptive; pairs within an article are not independent): {v3['pooledPairAgreement']['agree']}/"
              f"{v3['pooledPairAgreement']['scored']} ({v3['pooledPairAgreement']['rate']:.0%})."]
        L += ["", "| Contrast | Scored pairs | Agree | Rate | Articles |", "|---|---|---|---|---|"]
        L += [f"| {c} | {x['scored']} | {x['agree']} | {x['rate']:.0%} | {x['articles']} |" for c, x in v3["byContrast"].items()]
        L += ["", "| Article | Per-article agreement |", "|---|---|"] + [f"| {k} | {v:.0%} |" for k, v in v3["perArticle"].items()]
    sf = screening_finding()
    L += ["", "##### Screening finding: the literature rarely compares preparations of the same material", "",
          f"The v3 rule screened {sf['screened']} search results ({sf['unique']} distinct articles) across {sf['plants']} plants. Only "
          f"**{sf['eligible']}** directly compared two preparations of the same plant material in a usable table. That is {sf['eligible']} of the "
          f"{sf['tablesExamined']} articles whose tables were examined ({sf['eligible'] / max(sf['tablesExamined'], 1):.0%}); "
          "the others failed the licence or title check first:", "",
          "| Screening outcome | Articles |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(sf["reasons"].items(), key=lambda kv: -kv[1])] + [
          "", "Within this sample, this is evidence that modern studies rarely test or report preparation effects in a comparable form. "
              "That is the gap the modern-methods audit (Phase 5) is designed to measure. The rule set a cap of 3 articles per plant, which "
              "was never reached, and the rule was not relaxed.",
          "", "**Limits of the screen.**",
          "- It used only the first page of two PMC searches per plant.",
          "- It required a Creative Commons licence and the plant's name in the title.",
          "- It read only HTML tables: comparisons reported in text, figures, images or supplementary files count as \"no eligible table\".",
          "",
          "So the screen shows that usable comparisons are scarce. It does not show that none exist."]
    a = v3.get("postHocAudit") or {}
    if a:
        share = a.get("largestArticleShareOfScoredPairs")
        L += ["", f"**Post-hoc notes (not registered; `{a['basis']}`).**"]
        L += [f"- {n['pmcid']} ({n['pairs']} pair(s)): {n['note']}." for n in a["notes"]]
        if share is not None:
            L += [f"- The largest article supplies {share:.0%} of the scored pairs, which is why pooled pair agreement and the registered per-article mean differ."]
    return L


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
    L += v3_section()
    sv = v2["secondaryVariant"]
    L += ["", f"**Secondary variant `{sv['name']}`** (pre-registered; slope k = ln 10, descriptor noise SD {sv['h_sd']}; evaluated on v2 rows only): "
              f"overall {_rate(sv['overall'])}; `present` {_rate(sv['present'])}; `absent/low` {_rate(sv['low'])}. "
              "On these rows it gives no evidence for or against replacing the primary model, which stays the default."]
    return L


def artemisinin_section(art: dict, m4s: dict) -> list[str]:
    import pandas as pd
    de = m4s.get("rangeDescriptorError", {})
    L = ["### Artemisinin known case: a borderline result", "",
         f"Against the criteria fixed before the model was run, artemisinin is a **{art['result']}**. "
         "The criteria were: the heat flag fires, the cold-water median is below 0.30, and the low-temperature nonpolar median is above 0.60. "
         "All three hold for the medians. The result is *borderline*, not a clean pass, because the 5th–95th ranges cross the thresholds.",
         f"Since this version the ranges also include descriptor error (Normal SD {de.get('sd', 'unknown')} logP units, from the Crippen "
         f"MAE {de.get('mae', 'unknown')}), which widens them further. The medians are unchanged. "
         "Source: `data/interim/m4/artemisinin_check.json`.", "",
         "| Preparation | Median | 5th–95th (incl. descriptor error) | 5th–95th (model only) | Solvent | Heat | Filtration | Acidity |",
         "|---|---|---|---|---|---|---|---|"]
    for lab, r in art["predictions"].items():
        d, mo = r["drivers"], r.get("rangeModelOnly") or [r["low"], r["high"]]
        L.append(f"| {lab} | {r['likelihood']:.2f} | {r['low']:.2f}–{r['high']:.2f} | {mo[0]:.2f}–{mo[1]:.2f} | {d['solvent']:.2f} | "
                 f"{d['heat']:.2f} | {d['filtration']:.2f} | {d['acidity']:.2f} |")
    L += ["", "Drivers are the median per-factor multipliers. The cold-water infusion is filtered (filtration 1.00), so its value comes from "
              "the solvent factor alone; the unfiltered variant shows how much the suspension assumption would add."]
    v2 = pd.read_csv(ROOT / "data" / "reference" / "prep_literature_prereg_v2.csv")
    a = v2[v2.compound.str.lower() == "artemisinin"]
    if len(a):
        r = a.iloc[0]
        q = r.quote if len(r.quote) <= 420 else r.quote[:417].rsplit(" ", 1)[0] + " …"
        L += ["", "**Sweet wormwood tea: a disagreement explained by extraction vs detection.** The pre-registered v2 check found "
                  f"a report of artemisinin **{r.reported}** in *{r.plant}* ({r.modelPreparation}; {r.pmcid}, {r.licence}):", "",
              f"> {q}", "",
              f"The model's median for this preparation is **{r.predicted:.2f}** ({r.low:.2f}–{r.high:.2f}), below the 0.40 `present` "
              "threshold, so the row scores as a **disagreement**.",
              "",
              "The model and the paper answer different questions:",
              "- The model estimates the **fraction** of the plant's artemisinin that a hot-water infusion carries: a minority fraction, "
              "because artemisinin is fairly lipophilic and its endoperoxide is heat-sensitive.",
              "- The paper reports that artemisinin is **detected** in the tea at measurable concentrations. That depends on the fraction, "
              "but also on how much artemisinin the leaves contain and on the assay's detection limit.",
              "",
              "A minority fraction of a high-content plant can still give a clearly measurable tea. LOTUS has no abundance data, so the model "
              "cannot predict detection, and this row is not evidence that the predicted fraction is wrong (METHODS §9, 'Extraction is not "
              "detection'). It is also not evidence that the fraction is right. A test of the fraction needs a paired comparison within one "
              "plant and study, which is what v3 does."]
    v3p = ROOT / "data" / "reference" / "prep_literature_prereg_v3_pairs.csv"
    if v3p.exists():
        p3 = pd.read_csv(v3p)
        x = p3[(p3.compoundX.str.lower() == "artemisinin") | (p3.compoundY.str.lower() == "artemisinin")] if len(p3) else p3
        L += ["", (f"v3 contains {len(x)} paired comparisons involving artemisinin "
                   f"({int((x.agree == True).sum())} agree, {int((x.agree == False).sum())} disagree, {int(x.abstain.sum())} abstained)."  # noqa: E712
                   if len(x) else "v3 found no table with paired artemisinin measurements, so the paired test does not reach artemisinin.")]
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
            f"- The recorded artemisinin result and every threshold are unchanged. Separately, {art_txt}; see the artemisinin section above."]


def ranking_section() -> list[str]:
    r = _j("data/interim/m6/ranking_stability.json")
    if not r:
        return []
    rob, med = r["stability"]["robust (5th percentile of gap)"], r["stability"]["median gap only (comparison)"]
    top = r["top"][:5]
    return ["", "### Hypothesis ranking rule (M6): stability test (demonstration, not hypotheses)", "",
            f"Source: `data/interim/m6/ranking_stability.json`. Rule: {r['rule']}. {r['label']}", "",
            f"- Candidate pairs: {r['candidates']}; ranked: {r['ranked']}; not ranked (too few compounds with a usable range): {r['notRanked']}. "
            f"Compound entries excluded as too wide to drive a rank: {r['compoundsExcludedWideShare']:.0%}.", "",
            "| Ranking | MC reseed: Spearman | MC reseed: top-20 overlap | Compound bootstrap: mean Spearman | Compound bootstrap: mean top-20 overlap |",
            "|---|---|---|---|---|",
            f"| Robust (5th percentile of gap) | {rob['monteCarloReseed']['spearman']} | {rob['monteCarloReseed']['top20Overlap']:.0%} | "
            f"{rob['compoundBootstrap']['spearmanMean']} | {rob['compoundBootstrap']['top20OverlapMean']:.0%} |",
            f"| Median gap only (comparison) | {med['monteCarloReseed']['spearman']} | {med['monteCarloReseed']['top20Overlap']:.0%} | "
            f"{med['compoundBootstrap']['spearmanMean']} | {med['compoundBootstrap']['top20OverlapMean']:.0%} |",
            "", f"The two rankings broadly agree (Spearman {r['rankDisagreement']['spearmanRobustVsMedian']}; "
                f"{r['rankDisagreement']['top20Shared']} of the top 20 shared). The robust rule is slightly more stable under both perturbations "
                f"({rob['compoundBootstrap']['replicates']} compound-bootstrap replicates).",
            "", "**Caveat.** The top of this demonstration list is "
                + ("dominated by distilled-water vs solvent-extract pairs" if sum(t["faithful"] == "distilled water" for t in top) >= 4 else "mixed")
                + ". That contrast is driven by the volatility heuristic, so it says more about that heuristic than about real candidates. "
                "Real hypotheses need the Phase 5 audit, which supplies the modern preparations actually tested."]


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


def _audit_status() -> str:
    import pandas as pd
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    if "headline" in ss and ss.headline.any():
        return (f"The study set has been reviewed by the project lead: {int(ss.headline.sum())} species are approved for the headline "
                "analysis (`docs/STUDY_SET_REVIEW.md`). The audit itself has not started.")
    return "It has not started; it waits for the project lead's approval of the study set."


def screening_finding() -> dict | None:
    v3 = _j("data/interim/m4/literature_prereg_v3.json")
    if not v3:
        return None
    ev = [(pid, w) for v in v3["screening"].values() for pid, w in v["screened"]]
    reasons: dict[str, int] = {}
    for _, w in ev:
        k = "eligible (usable paired table)" if w.startswith("eligible") else w.replace("ineligible: ", "")
        reasons[k] = reasons.get(k, 0) + 1
    return {"screened": len(ev), "unique": len({p for p, _ in ev}), "plants": len(v3["screening"]),
            "eligible": sum(1 for _, w in ev if w.startswith("eligible")), "reasons": reasons,
            "tablesExamined": sum(1 for _, w in ev if w.startswith("eligible") or w == "ineligible: no eligible table")}


def positioning() -> list[str]:
    import pandas as pd
    v1 = pd.read_csv(ROOT / "data" / "reference" / "prep_literature_prereg_v1.csv")
    eo = v1[v1.modelPreparation == "distilled water"]
    v2 = _j("data/interim/m4/literature_prereg_v2.json")
    v3 = _j("data/interim/m4/literature_prereg_v3.json") or {}
    prof = pd.read_parquet(INTERIM / "m4" / "profiles_long.parquet")
    width = (prof.high - prof.low).groupby(prof.preparation).median()
    aq = ["cold water infusion", "hot water infusion (tea)", "decoction in water"]
    sf = screening_finding()
    L = ["## What the results support", "",
         "**Planned headline: the modern-methods audit (Phase 5).** For each study-set species, it will check how modern studies "
         "prepared the plant (solvent, temperature and filtration, each recorded separately) against how the historical recipes made it, "
         "and flag remedies that were never tested the way they were made. " + _audit_status(), "",
         "**The preparation model is a transparent hypothesis generator, not a validated predictor.** Every factor and assumption is "
         "inspectable, and every estimate carries a range. Its support differs by preparation:",
         f"- **Essential-oil compounds: best supported.** In the pre-registered v1 check, {int(eo.agree.sum())}/{len(eo)} essential-oil "
         "rows agree with the model. These rows test presence only; no essential-oil row reported a compound as absent.",
         f"- **Aqueous preparations (infusions, decoctions, juices): unvalidated.** The pre-registered v2 check found "
         f"{v2['found']['low']} `absent/low` rows against a quota of {v2['quota']['low']} (agreement "
         f"{v2['primary']['low']['agree']}/{v2['primary']['low']['n']}). The paired v3 check is **inconclusive** "
         f"({v3.get('articlesScored', 0)} articles). Single-row checks also measure detection, not the extraction fraction the model predicts (METHODS §9).",
         "- **Wide ranges.** With descriptor error included, the median width of the 5th–95th range across study-set compounds is "
         + ", ".join(f"{width[k]:.2f} for {k}" for k in aq if k in width) + " on a 0–1 scale.",
         "- **Ranking.** Hypotheses will be ranked only on profile gaps that hold across those ranges (METHODS §11). Compounds whose "
         "range spans most of the scale cannot drive a rank."]
    if sf:
        L += ["", f"**A finding from the screening itself.** Of {sf['screened']} article screenings ({sf['unique']} distinct articles) across "
                  f"{sf['plants']} plants, only **{sf['eligible']}** directly compared two preparations of the same plant material in a usable "
                  f"table: {sf['eligible']} of the {sf['tablesExamined']} articles whose tables were examined after the licence and title checks. "
                  "Within this sample, this is evidence that the literature rarely reports preparation effects in a form that can be "
                  "compared (details under the v3 results)."]
    return L


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
    L += positioning() + [""]
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
          ""]
    L += artemisinin_section(art, m4s)
    L += literature_sections() + water_section() + ranking_section() + toxicity_section()
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
    _update_readme(positioning() + [""] + validation_status(m) + [""] + by_source(m))
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
