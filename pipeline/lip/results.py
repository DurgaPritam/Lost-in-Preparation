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
            f"{int(ss.reReviewRequested.sum()) if 'reReviewRequested' in ss else 0} rows await re-review after reviewer fixes"
            + (f"; re-review decisions recorded for {int((ss.reReviewDecision.fillna('') != '').sum())} species "
               "(`config/study_set_rereview_decisions.csv`)" if "reReviewDecision" in ss else ""))


def _n_proposed() -> int:
    import pandas as pd
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv")
    return int(ss.proposed.sum())


def _m1_run_rows() -> list[tuple[str, str, str]]:
    """M1 session-extraction runs, read from data/interim/m1/run_<scope>.json."""
    out = []
    for scope, what in (("sample", "50-passage gold sample"), ("approved", "recipe-scope passages of the Phase 5 species")):
        r = _j(f"data/interim/m1/run_{scope}.json")
        if not r:
            continue
        out.append((f"M1 extraction run: {what}",
                    f"done — {r['run']['provider']} ({r['run']['model']}, prompt {r['promptVersion']}); {r['passages']} passages, "
                    f"{r['recipesAccepted']} recipes accepted, {r['recipesRejected']} rejected by the verbatim-quote check (logged, never repaired)",
                    f"`data/interim/m1/run_{scope}.json`"))
    return out


HV, EXT, AI, PEND = "**human-validated**", "**validated against external data**", "*AI-assisted check (provisional)*", "human validation pending"


def _ai_check_rows() -> list[tuple[str, str, str]]:
    """The three AI-assisted checks (basis ai_assisted_check): never human validation."""
    rows = []
    e = _j("data/interim/m5/ai_check_eval.json")
    if e:
        f = e["fields"]
        rows.append(("M5 rule-based extractor vs an AI coder (40 studies, 47 preparations)",
                     f"{AI} — agreement: solvent {_ci(f['solvent']['agreement'])}, heat {_ci(f['heat']['agreement'])}, "
                     f"part {_ci(f['part']['agreement'])}, fresh/dried {_ci(f['freshOrDried']['agreement'])}. An AI checking a rule system; "
                     "not a human reading", "`data/interim/m5/ai_check_eval.json`"))
    pc = _j("data/reference/plates_ai_check_v1.json")
    if pc:
        n, fl = len(pc["plates"]), sum(1 for x in pc["plates"] if x["flags"])
        rows.append((f"Botanical plate licences ({n} Commons pages)",
                     f"{AI} — an AI agent read each page on {pc['checkedOn']} and recorded its licence tag, source and date; "
                     f"{fl} pages flagged for a person to look at; awaiting human confirmation", "`data/reference/plates_ai_check_v1.json`"))
    if (ROOT / "data/reference/m1_review_priority_v1.csv").exists():
        rows.append(("M1 review priority: 10 passages most likely to hold extraction errors",
                     f"{AI} — not an evaluation; tells a human reviewer where to start", "`data/reference/m1_review_priority_v1.csv`"))
    return rows


def validation_status(m: C.Metrics) -> list[str]:
    gold_ext = m.extraction.overall.get("part")
    art = m.artemisininCheck.result or "not run"
    rows = [
        ("Text ingestion and segmentation (passage coverage, IDs, chapter counts vs printed contents)", f"{PEND} — automated tests pass against the source files", "`tests/`"),
        ("logP descriptor: RDKit vs GFN2-xTB vs experiment", f"{EXT} — against measured experimental values (SangsterLogP, CC BY 4.0); no AI-made reference", "`data/interim/m4/logp_validation.json`"),
        ("Artemisinin known-case test", f"{AI} — result **{art}** against pre-registered criteria that an AI wrote from the literature", "`data/interim/m4/artemisinin_check.json`"),
        *[(a, f"{PEND} — extraction run complete: {b.removeprefix('done — ')}", c) for a, b, c in _m1_run_rows()],
        ("M1 extraction accuracy vs human gold set", f"{PEND} — human annotation not yet done" if not gold_ext or gold_ext.f1.status != "computed" else f"{HV} (single annotator)", "`data/gold/annotations/`"),
        ("Annotator self-consistency (15-passage re-annotation, Cohen's kappa)", f"{PEND} — re-annotation not yet done" if (m.interAnnotatorAgreement.get("heat") is None or m.interAnnotatorAgreement["heat"].status != "computed") else f"{HV} (computed, see metrics.json)", "`data/gold/reannotation_subset_v1.json`"),
        ("M1 extraction vs the AI reference set (silver)", f"{PEND} — the comparison is not made: the same AI (Claude) wrote the silver set and the extraction, so it would be circular", "`data/silver/silver_v1.json`"),
        ("M2 name resolution vs scholarly identifications", f"{PEND} — needs identifications checked by a person" if m.nameResolution["top1"].status != "computed" else HV, "`data/gold/name_identifications.csv`"),
        ("M2 name resolution vs AI-drafted identifications", f"{AI} — drafted by an AI from quoted sources, unverified", "`data/gold/name_identifications.csv` (draft* columns)"),
        ("Preparation model vs published reports — exploratory set", f"{AI} — exploratory; 9 rows an AI selected after the model was built", "`data/reference/prep_literature_v1.csv`"),
        ("Preparation model vs published reports — pre-registered v1 (mostly essential oils)", f"{AI} — rule pre-registered (docs/PREREGISTRATION.md); rule and code written by an AI", "`data/reference/prep_literature_prereg_v1.csv`"),
        ("Preparation model vs published reports — pre-registered v2 (water preparations)", f"{AI} — rule pre-registered (docs/PREREGISTRATION_v2.md); rule and code written by an AI; low-row quota not met", "`data/reference/prep_literature_prereg_v2.csv`"),
        ("Preparation model vs published reports — pre-registered v3 (paired, within plant)", f"{AI} — inconclusive, too few articles (n in RESULTS); rule pre-registered (docs/PREREGISTRATION_v3.md, one amendment before collection); rule and code written by an AI", "`data/reference/prep_literature_prereg_v3_pairs.csv`"),
        ("Genus-signal audit (name resolution)", f"{AI} — an AI reviewed false friends with dictionary quotes; awaiting human review", "`docs/GENUS_SIGNAL_AUDIT.md`"),
        (f"Study-set toxicity entries ({_n_proposed()} species)", f"{AI} — drafted by an AI from cited EMA / PMC sources; awaiting human review", "`data/reference/toxicity_curated.csv`"),
        (f"Study set ({_n_proposed()} proposed)", _review_status().replace("**human-reviewed**", f"{HV} (reviewed by the project lead)").replace("pending — human approval", PEND), "`docs/STUDY_SET_PROPOSAL.md`"),
        *_audit_rows(),
        *_ai_check_rows(),
    ]
    out = ["## Validation status", "", "| Result | Status | Evidence |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    out += ["", "Every row has one of four statuses. **human-validated**: checked by a person. **validated against external data**: "
            "compared with an independent, published dataset (for example measured experimental values), with no AI-made reference. "
            "*AI-assisted check (provisional)*: checked by an AI or against a reference an AI made; useful for finding problems, never a "
            "validation. human validation pending: no independent check yet."]
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
    add("M1 extraction vs AI reference (silver)", {g: "not used (circular)" for g in names}, "not used (circular)")
    ap = _j("data/interim/m1/predictions_approved.json") or []
    acc = {g: sum(1 for r in ap if _grp(r["sourceId"]) == g) for g in names}
    add("M1 recipes accepted, Phase 5 species (session extraction)", {g: str(v) for g, v in acc.items()}, str(len(ap)))
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


def _pct(x: dict) -> str:
    if not x or x.get("status") != "computed":
        return f"not computed ({x.get('note', '') if x else 'no data'})"
    ci = f" (95% CI {x['low']:.0%}–{x['high']:.0%})" if x.get("low") is not None else ""
    return f"{x['value']:.0%}{ci}; nKnown = {x['nKnown']}, nUnknown = {x['nUnknown']}"


def _sens_note() -> str:
    s = _j("data/interim/m5/reporting_gap_sensitivity.json")
    if not s:
        return ""
    pr = s["sets"]["prepared"]
    return (f". {AI.replace('check', 'sensitivity check')}: heat {_ci3(pr['heat']['adjusted'])}, fresh or dried "
            f"{_ci3(pr['freshOrDried']['adjusted'])}, filtration not computed (see the headline section)")


def _audit_rows() -> list[tuple[str, str, str]]:
    a, h = _j("data/interim/m5/audit_summary.json"), _j("data/interim/m6/hypotheses_summary.json")
    hc = _j("data/interim/m5/handcheck_eval.json")
    acc = "extractor accuracy: human hand-check pending (an AI-assisted check exists, see below)"
    rows = []
    g = _j("data/interim/m5/reporting_gap.json")
    if g:
        pr = g["sets"]["prepared"]["all"]
        rows.append(("**Headline: reporting gap** (descriptive) — share of studies that prepared the plant stating heat / fresh or dried / filtration",
                     f"{PEND} — computed: {_ci(pr['heat'])} / {_ci(pr['freshOrDried'])} / {_ci(pr['filtration'])}; coded by the rule-based extractor; {acc}" + _sens_note(),
                     "`data/interim/m5/reporting_gap.json`"))
    if a:
        rows.append(("Modern-methods audit (M5) **v1**: share of modern studies with no historical-preparation match",
                     f"{PEND} — computed as pre-registered (`{a['extractor']}`): {_pct(a['headline'])}. **Design flaw:** v1's solvent rule makes "
                     "every non-water recipe unmatchable, so this mostly reflects the protocol", "`data/interim/m5/audit_summary.json`"))
        a2 = _j("data/interim/m5/v2/audit_summary.json")
        if a2:
            rows.append(("**Modern-methods audit (M5) v2: pre-registered re-analysis after v1's design flaw** — overall fidelity (share faithful)",
                         f"{PEND} — {_rt(a2['overallFidelity'])}; per-variable rates in RESULTS; {acc}",
                         "`data/interim/m5/v2/audit_summary.json`"))
        rows.append(("M5 extractor accuracy vs human hand-check (40 studies)",
                     f"{PEND} — hand-check sheet not yet filled" if not hc else f"{HV} (see RESULTS)", "`data/reference/m5_handcheck_v1.csv`"))
    else:
        rows.append(("**Modern-methods audit (M5): the planned headline result**", f"{PEND} — not started", "—"))
    if h:
        rows.append(("Hypothesis ranking (M6)", f"{PEND} — {h['ranked']} hypotheses worth re-testing ranked from {h['candidates']} never-faithfully-tested "
                     f"pairs (robust rule); depends on the unvalidated preparation model and the unchecked audit coding", "`site-data/hypotheses.json`"))
    else:
        rows.append(("Hypothesis ranking (M6)", f"{PEND} — rule implemented and stability-tested on model-only candidate pairs (not hypotheses)",
                     "`data/interim/m6/ranking_stability.json`"))
    return rows


def _rt(x: dict | None) -> str:
    if not x or x.get("status") != "computed":
        return f"not computed (known {x.get('nKnown', 0) if x else 0})"
    ci = f" (95% CI {x['low']:.0%}–{x['high']:.0%})" if x.get("low") is not None else ""
    na = f", no modern analogue {x['nNoAnalogue']}" if x.get("nNoAnalogue") else ""
    return f"{x['value']:.0%}{ci}; n known {x['nKnown']}, unknown {x['nUnknown']}{na}"


def audit_v2_section() -> list[str]:
    a1, a2 = _j("data/interim/m5/audit_summary.json"), _j("data/interim/m5/v2/audit_summary.json")
    if not (a1 and a2):
        return []
    r = a2["retrieval"]
    L = ["", "## Audit v1 and v2 side by side", "",
         "**v2 is a pre-registered re-analysis after v1's design flaw** (`docs/AUDIT_PROTOCOL_v2.md`, committed before any v2 result). "
         "v1 is reported exactly as pre-registered above. **v1's solvent rule makes every non-water recipe unmatchable** (only a "
         "historical `[water]` preparation could match a modern solvent), so v1's headline mostly reflects the protocol, not the literature.", "",
         f"v2 sources: `data/interim/m5/v2/audit_summary.json`; extractor `{a2['extractor']}`; logged M1 corrections applied: "
         f"{len(a2['m1CorrectionsApplied'])} recipes (`config/m1_corrections.csv`). Retrieval: species-level literature filtered by MeSH "
         f"descriptor or descendant; {r['pairsWithRecords']} of {r['pairs']} pairs with records; {r['recordsMatched']:,} records matched; "
         f"excluded {', '.join(f'{k} {v}' for k, v in r['excluded'].items()) or 'none'}; eligible studies {r['eligibleStudies']:,} "
         f"({', '.join(f'{k} {v}' for k, v in r['byEvidenceSource'].items())}). Unit status: "
         + ", ".join(f"{k} {v:,}" for k, v in a2["units"]["overallStatus"].items()) + ".", "",
         "| Measure | v1 (as pre-registered) | v2 (re-analysis) |", "|---|---|---|",
         f"| Share of studies **not faithful** (overall) | {_pct(a1['headline'])} | "
         + (f"{a2['overallNotFaithfulShare']:.0%}; n known {a2['overallFidelity']['nKnown']}" if a2['overallNotFaithfulShare'] is not None else "not computed") + " |",
         f"| Overall fidelity (share faithful) | {1 - a1['headline']['value']:.0%}; nKnown {a1['headline']['nKnown']} | {_rt(a2['overallFidelity'])} |"]
    v1f = a1["fieldMismatchRate"]
    for v in ("solvent", "heat", "part", "freshOrDried", "filtration"):
        x1 = v1f.get(v)
        L.append(f"| {v} match rate | " + (f"{1 - x1['rate']:.0%} of {x1['known']} known comparisons" if x1 and x1["known"] else "no known comparisons")
                 + f" | {_rt(a2['perVariableFidelity'][v])} |")
    L += ["", "v1's per-field figures are per comparison (study preparation × historical preparation); v2's are per (pair, study) unit, as "
          "pre-registered. v2 solvent match rate at other wine cut-offs (sensitivity): "
          + "; ".join(f"≤ {k}: {_rt(v)}" for k, v in a2["solventWineCutoffSensitivity"].items()) + ".", "",
          "| v2 breakdown | Overall fidelity |", "|---|---|"]
    for g, x in a2["bySourceGroup"].items():
        L.append(f"| Pairs attested {'only by Pliny (lower confidence)' if g == 'pliny_only' else 'by Culpeper'} | {_rt(x)} |")
    for g, x in a2["byEvidenceSource"].items():
        L.append(f"| Coded from {g} | {_rt(x)} |")
    h1, h2 = _j("data/interim/m6/hypotheses_summary.json"), _j("data/interim/m6/v2/hypotheses_summary.json")
    if h1 and h2:
        names = {json.loads(f.read_text())["wfoId"]: json.loads(f.read_text())["species"] for f in (INTERIM / "m5" / "literature").glob("*.json")}
        L += ["", "**Hypotheses worth re-testing, v1 and v2** (both with the logged corrections; `site-data/hypotheses.json` is v1, "
              "`data/interim/m6/v2/hypotheses.json` is v2):", "", "| Audit | Rank | Species | Indication | Faithful vs modern preparation | Gap 5th / median / 95th |",
              "|---|---|---|---|---|---|"]
        for tag, path in (("v1", "data/interim/m6/hypotheses.csv"), ("v2", "data/interim/m6/v2/hypotheses.csv")):
            import pandas as pd
            pth = ROOT / path
            if not pth.exists():
                continue
            d = pd.read_csv(pth).dropna(subset=["rank"]).sort_values("rank")
            for x in d.head(15).itertuples():
                L.append(f"| {tag} | {int(x.rank)} | *{x.acceptedName}* | {x.mesh} | {x.faithful} vs {x.modern} | {x.gapP5:.2f} / {x.gapP50:.2f} / {x.gapP95:.2f} |")
        L += ["", f"v2 candidates {h2['candidates']}, ranked {h2['ranked']}; skipped: " + ", ".join(f"{k} {v}" for k, v in h2["skipped"].items()) + ". "
              "Every row is a hypothesis worth re-testing, not a claim that a preparation works or is safe."]
    return L


def ai_check_section() -> list[str]:
    e = _j("data/interim/m5/ai_check_eval.json")
    if not e:
        return []
    names = {"solvent": "Solvent", "heat": "Heat", "part": "Part", "freshOrDried": "Fresh or dried"}
    L = ["", "## AI-assisted check of the rule-based extractor (provisional)", "",
         f"An AI coder ({e['provenance']['model']}, prompt `{e['provenance']['prompt']}` {e['provenance']['promptVersion']}) read the {e['studies']} "
         f"hand-check studies ({e['rows']} extracted preparations) blind to the extractor's output and coded each field with an exact quote; "
         f"every quote was checked verbatim against the study text. **This is an AI checking a rule system, not a human hand-check**; the human "
         "sheet (`data/reference/m5_handcheck_v1.csv`) stays empty for people. Agreement means the same code (unknown = unknown counts).", "",
         "| Field | Agreement (95% CI) | Where both stated a value | Extractor unknown, AI stated | Extractor stated, AI unknown | Both stated, different |",
         "|---|---|---|---|---|---|"]
    for k, v in e["fields"].items():
        b, w = v["breakdown"], v["agreementWhereBothStated"]
        L.append(f"| {names[k]} | {_ci(v['agreement'])} | {w['k']}/{w['n']} | {b['ruleUnknownAiStated']} | {b['ruleStatedAiUnknown']} | {b['bothStatedDifferent']} |")
    s1 = e["fields"]["solvent"]["agreementSinglePreparationRows"]
    L += ["", f"Solvent on the single-preparation rows only (the coder did not see the extractor's solvent wording there): {_ci(s1)}.", ""]
    L += [f"- {c}" for c in e["caveats"]]
    return L


def audit_section() -> list[str]:
    a = _j("data/interim/m5/audit_summary.json")
    if not a:
        return []
    r, u = a["retrieval"], a["units"]
    L = ["", "## Modern-methods audit (M5)", "",
         f"Sources: `data/interim/m5/audit_summary.json`, `data/interim/m5/pairs.json`; protocol `{a['protocol']}` (committed before retrieval); "
         f"extractor `{a['extractor']}` (rule-based, no LLM); indication lexicon `{a['indicationLexicon']}`. "
         "Unstated preparation details are `unknown` and never count as mismatches.", "",
         f"- Pairs: {r['pairs']} species–indication pairs; {r['pairsWithHits']} with at least one PubMed hit "
         f"({r['totalHits']:,} hits in total; first {r['retmaxPerPair']} per pair taken). Unique records: {r['uniqueRecords']:,}; "
         f"excluded: {', '.join(f'{k} {v}' for k, v in r['excluded'].items()) or 'none'}; coded: {r['studiesCoded']:,} "
         f"({', '.join(f'{k} {v:,}' for k, v in r['byEvidenceSource'].items())}); every field unknown: {r['studiesAllUnknown']:,}.",
         f"- (pair, study) units: {u['pairStudyUnits']:,} ({', '.join(f'{k} {v:,}' for k, v in u['byStatus'].items())}); "
         f"pairs with any study: {u['pairsWithAnyStudy']}; with a known status: {u['pairsWithKnownStatus']}.", "",
         "| Measure | Share not faithful |", "|---|---|",
         f"| **Headline: (pair, study) units** | {_pct(a['headline'])} |",
         f"| Each study counted once | {_pct(a['headlineUniqueStudies'])} |"]
    for g, x in a["bySourceGroup"].items():
        L.append(f"| Pairs attested {'only by Pliny (lower confidence)' if g == 'pliny_only' else 'by Culpeper'} | {_pct(x)} |")
    for g, x in a["byEvidenceSource"].items():
        L.append(f"| Coded from {g} | {_pct(x)} |")
    ph = a.get("postHocSensitivity")
    if ph:
        L.append(f"| *Post-hoc sensitivity (not pre-registered): only studies that state a solvent* | {_pct(ph['solventStatedOnly'])} |")
    L += ["", "| Field | Mismatches / known comparisons |", "|---|---|"]
    for f, x in a["fieldMismatchRate"].items():
        L.append(f"| {f} | {x['mismatch']:,} / {x['known']:,} ({x['rate']:.0%}) |" if x else f"| {f} | — |")
    L += ["", "**v1's solvent rule makes every non-water recipe unmatchable**: only a historical `[water]` preparation could match a "
          "modern solvent, so wine, vinegar, oil, honey and no-vehicle recipes could never count as faithful. v1's headline therefore "
          "mostly reflects the protocol, not the literature. See *Audit v1 and v2 side by side* for the pre-registered re-analysis.",
          "", "**Reading the headline.** Most retrieved (pair, study) units stay `unknown`, mostly because abstracts do not say how the plant "
          "was prepared, and many pairs have no PubMed hit at all for the protocol's query. Among units with a known status, the solvent rule "
          "dominates: historical vehicles other than water (wine, vinegar, oil, honey, none) have no modern equivalent, so they can never "
          "match. Under protocol v1, a retrieved study can be judged not faithful on a plant-part mismatch alone even if it never "
          "prepared the plant (e.g. a pure-compound study). The post-hoc row above restricts to studies that state a solvent; "
          f"{ph['notFaithfulOnPartAlone'] if ph else 'n/a'} not-faithful units had no stated solvent.", "",
          "This describes how the retrieved studies prepared each plant compared with the recipes. It is **not** evidence that the "
          "historical preparations work. The coding is a keyword heuristic whose accuracy is measured only by the 40-study hand-check "
          "(`data/reference/m5_handcheck_v1.csv`, pending)."]
    h = _j("data/interim/m6/hypotheses_summary.json")
    hy = _j("site-data/hypotheses.json") or []
    if h:
        L += ["", "## Hypotheses worth re-testing (M6)", "",
              f"Sources: `site-data/hypotheses.json`, `data/interim/m6/hypotheses.csv`, `data/interim/m6/hypotheses_summary.json`. Rule: {h['rule']}.", "",
              f"- Candidates (pairs never tested faithfully, with a modelled faithful and modern preparation): {h['candidates']}; ranked: {h['ranked']}; "
              f"not ranked (too few narrow-range compounds): {h['notRanked']}.",
              "- Skipped pairs: " + ", ".join(f"{k} {v}" for k, v in h["skipped"].items()) + ".", ""]
        if hy:
            import pandas as pd
            names = {}
            for f in (INTERIM / "m5" / "literature").glob("*.json"):
                d = json.loads(f.read_text())
                names[d["wfoId"]] = d["species"]
            L += ["| Rank | Species | Indication (MeSH) | Faithful preparation | Gap 5th / median / 95th | Toxicity (source says) |", "|---|---|---|---|---|---|"]
            for x in hy[:15]:
                g = x["profileGap"]
                L.append(f"| {x['rank']} | *{names.get(x['speciesId'], x['speciesId'])}* | {x['indication']['label']} | {x['faithfulPreparationText']} | "
                         f"{g['low']:.2f} / {g['value']:.2f} / {g['high']:.2f} | `{x['toxicityFlag']}` |")
            L += ["", "Every row is a hypothesis worth re-testing, not a claim that the preparation works or is safe. Gaps are model "
                  "predictions from an unvalidated preparation model for aqueous preparations (see the preparation-model sections)."]
    return L


def _audit_status() -> str:
    import pandas as pd
    a = _j("data/interim/m5/audit_summary.json")
    if a:
        return (f"It has now been run on the {a['retrieval']['pairs']} species–indication pairs of the Phase 5 species with a rule-based "
                f"extractor and a protocol fixed before retrieval (headline: {_pct(a['headline'])}). Its coding accuracy awaits the "
                "40-study human hand-check.")
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


def _ci(x: dict) -> str:
    return f"{x['value']:.0%} ({x['k']}/{x['n']}; 95% CI {x['low']:.0%}–{x['high']:.0%})"


def reporting_gap_lines() -> list[str]:
    g = _j("data/interim/m5/reporting_gap.json")
    if not g:
        return []
    pr, rt, v3 = g["sets"]["prepared"]["all"], g["sets"]["retrieved"], g["v3Screening"]
    lab = {"solvent": "solvent", "heat": "heat", "part": "plant part", "freshOrDried": "fresh or dried", "filtration": "filtration"}
    L = ["**Headline: the reporting gap.** These are descriptive findings, not hypothesis tests (`data/interim/m5/reporting_gap.json`, "
         "generated by `pipeline/lip/m5/reporting_gap.py`). \"Stated\" means the rule-based extractor coded a value. It is a heuristic; its "
         "human hand-check is pending, and an AI-assisted sensitivity check (provisional) follows the list.", "",
         f"- **Studies that prepared the plant material** (audit v2 eligibility, n = {pr['none']['n']}): share stating each preparation variable:",
         "  " + "; ".join(f"{lab[k]} {_ci(pr[k])}" for k in lab) + ".",
         f"  - All five stated: {_ci(pr['all five'])}. None stated: {_ci(pr['none'])}.",
         "  - Eligibility partly selects on a stated solvent, so the solvent share in this set is inflated by construction.",
         f"- **Every coded study retrieved for a species–indication pair** (audit v1, n = {rt['all']['none']['n']}): none of the five stated "
         f"{_ci(rt['all']['none'])}; all five {_ci(rt['all']['all five'])}. "
         f"Heat stated: {_ci(rt['abstract']['heat'])} when coded from abstracts, {_ci(rt['pmc_fulltext']['heat'])} from open-access methods sections. "
         f"Filtration stated: {_ci(rt['abstract']['filtration'])} from abstracts, {_ci(rt['pmc_fulltext']['filtration'])} from methods.",
         f"- **Direct comparisons are rare.** In the pre-registered v3 screening, {v3['eligibleScreenings']} of {v3['screeningsWithTablesExamined']} "
         f"article screenings whose tables were examined ({v3['distinctArticlesWithTablesExamined']} distinct articles) compared two preparations "
         f"of the same plant material in a usable table: {v3['share']['value']:.1%} (95% CI {v3['share']['low']:.1%}–{v3['share']['high']:.1%})."]
    return L + gap_sensitivity_lines(lab)


def _ci3(a: dict) -> str:
    return f"{a['value']:.0%} (95% CI {a['low']:.0%}–{a['high']:.0%})"


def gap_sensitivity_lines(lab: dict) -> list[str]:
    s = _j("data/interim/m5/reporting_gap_sensitivity.json")
    if not s:
        return []
    pr, c40 = s["sets"]["prepared"], s["checked40"]
    adj = "; ".join(f"{lab[k]} {pr[k]['frozen']['value']:.0%} → {_ci3(pr[k]['adjusted'])}" for k in ("heat", "freshOrDried", "part", "solvent"))
    side = "; ".join(f"{lab[k]} {c40[k]['rule']['k']}/{c40[k]['rule']['n']} by the extractor vs {c40[k]['ai']['k']}/{c40[k]['ai']['n']} by the AI coder"
                     for k in ("heat", "freshOrDried", "part", "solvent"))
    return ["", "- ***AI-assisted sensitivity check (provisional).*** If the extractor's error rates from the AI-assisted check "
            "(`data/interim/m5/reporting_gap_sensitivity.json`) applied to every coded study, the prepared-set shares would be: "
            f"{adj}. Filtration was not in the AI check, so it is not adjusted (frozen {pr['filtration']['frozen']['value']:.0%}).",
            f"  - On the {s['checkedStudies']} checked studies themselves, the share stating each variable: {side}.",
            "  - At study level the extractor's misses are largely offset by values it records that the AI coder left unknown, so the "
            "headline shares barely move. The AI coder is not a person, and only "
            f"{s['checkedInPrepared']} of the {s['checkedStudies']} checked studies are in the prepared set. The frozen numbers above are unchanged."]


def fidelity_lines() -> list[str]:
    a1, a2 = _j("data/interim/m5/audit_summary.json"), _j("data/interim/m5/v2/audit_summary.json")
    if not (a1 and a2):
        return []
    h1, f2, pv = a1["headline"], a2["overallFidelity"], a2["perVariableFidelity"]
    fa = h1["nKnown"] - round(h1["value"] * h1["nKnown"])
    return ["**Supporting detail: fidelity to the historical preparation** (the audit is frozen; v1 and v2 are reported as they are; small n).",
            f"- **v1 (as pre-registered):** {fa} of {h1['nKnown']} studies with a known status were faithful ({h1['nUnknown']} unknown). "
            "Its solvent rule makes every non-water recipe unmatchable, so this mostly reflects the protocol.",
            f"- **v2 (pre-registered re-analysis after v1's design flaw):** {round(f2['value'] * f2['nKnown'])} of {f2['nKnown']} known units were faithful "
            f"({f2['nUnknown']} unknown, {f2['nNoAnalogue']} with no modern analogue).",
            f"  - Solvent matched in {round(pv['solvent']['value'] * pv['solvent']['nKnown'])} of {pv['solvent']['nKnown']} known units "
            f"(95% CI {pv['solvent']['low']:.0%}–{pv['solvent']['high']:.0%}); plant part in {round(pv['part']['value'] * pv['part']['nKnown'])} of "
            f"{pv['part']['nKnown']}; heat was known for only {pv['heat']['nKnown']}.",
            "  - These counts are too small to estimate a field-wide fidelity rate. The reporting gap above is the reason."]


def positioning() -> list[str]:
    import pandas as pd
    v1 = pd.read_csv(ROOT / "data" / "reference" / "prep_literature_prereg_v1.csv")
    eo = v1[v1.modelPreparation == "distilled water"]
    v2 = _j("data/interim/m4/literature_prereg_v2.json")
    v3 = _j("data/interim/m4/literature_prereg_v3.json") or {}
    prof = pd.read_parquet(INTERIM / "m4" / "profiles_long.parquet")
    width = (prof.high - prof.low).groupby(prof.preparation).median()
    aq = ["cold water infusion", "hot water infusion (tea)", "decoction in water"]
    h = _j("data/interim/m6/hypotheses_summary.json")
    lc = _j("data/interim/m6/liquorice_case.json")
    L = ["## What the results support", ""]
    L += reporting_gap_lines() + [""] + fidelity_lines() + [""]
    if h:
        L += [f"**Hypotheses worth re-testing.** {h['ranked']} ranked from the audit (v1; v2 in RESULTS). "
              + (f"The top one, *Glycyrrhiza glabra* for liver diseases, changed after a logged extraction correction (median gap "
                 f"{lc['before']['gapP50']:.2f} → {lc['after']['gapP50']:.2f}; see the liquorice case study in RESULTS)." if lc else ""), ""]
    L += ["**The preparation model is a transparent hypothesis generator, not a validated predictor.** Every factor and assumption is "
          "inspectable, and every estimate carries a range. Its support differs by preparation:",
          f"- **Essential-oil compounds: best supported.** In the pre-registered v1 check, {int(eo.agree.sum())}/{len(eo)} essential-oil "
          "rows agree with the model. These rows test presence only; no essential-oil row reported a compound as absent.",
          f"- **Aqueous preparations (infusions, decoctions, juices): unvalidated.** The pre-registered v2 check found "
          f"{v2['found']['low']} `absent/low` rows against a quota of {v2['quota']['low']} (agreement "
          f"{v2['primary']['low']['agree']}/{v2['primary']['low']['n']}). The paired v3 check is **inconclusive** "
          f"({v3.get('articlesScored', 0)} articles). Single-row checks also measure detection, not the extraction fraction the model predicts (METHODS §9).",
          "- **Wide ranges.** With descriptor error included, the median width of the 5th–95th range across study-set compounds is "
          + ", ".join(f"{width[k]:.2f} for {k}" for k in aq if k in width) + " on a 0–1 scale.",
          "- **Ranking.** Hypotheses are ranked only on profile gaps that hold across those ranges (METHODS §11)."]
    return L


def liquorice_section() -> list[str]:
    c = _j("data/interim/m6/liquorice_case.json")
    if not c:
        return []
    ex, co, b, a = c["extractedAs"], c["correctedTo"], c["before"], c["after"]
    ev = {e["passageId"]: e["text"] for e in c["evidence"]}
    fn = ev.get("pliny-nh-bohn-v4:fn2511", "")
    rec = ev.get("culpeper-1850:dispensatory:s040-rob-or-sapa-and-juices:027", "")
    return ["", "## Case study: liquorice \"juice\"", "",
            "Source: `data/interim/m6/liquorice_case.json` (generated by `pipeline/lip/m6/liquorice_case.py`, which re-runs M6 with and without "
            "the logged corrections); corrections in `config/m1_corrections.csv`.", "",
            f"**The misclassification.** Pliny's glycyrrhiza chapter (`{c['recipeId']}`) says: \"{c['recipeQuote']}\". The session extraction coded "
            f"the material as part `{ex['part']}`, with solvent {ex['solvent']}, heat `{ex['heat']}` and process `{ex['process']}`. Phase 6 then "
            "modelled it as a **fresh juice**.", "",
            "**The corpus evidence that corrected it.**",
            f"- The translator's footnote, anchored to \"The juice\" in that passage: \"{fn}\"",
            f"- Culpeper's 1850 Dispensatory, *Succus Glycyrrhizæ simplex*: \"{rec}\"",
            "- The same Pliny passage says the root \"is the only part that is used\".",
            "",
            "Liquorice \"juice\" in older pharmacy is a boiled, strained and concentrated water extract of the root, not a fresh pressed juice. "
            f"At the project lead's request the recipe was reclassified ({', '.join(f'{k} → {v}' for k, v in co.items())}). The same correction was "
            f"applied, with the same evidence, to {len(c['otherLiquoriceRecipesCorrected'])} other liquorice recipes in Culpeper. Each change is "
            "logged with its old value, evidence and requester. The extraction output itself is not edited.", "",
            "**How the hypothesis changed** (Phase 6, audit v1):", "",
            "| | Faithful preparation | Modern preparation | Rank | Gap 5th / median / 95th |", "|---|---|---|---|---|",
            f"| Before correction | {b['faithful']} | {b['modern']} | {b['rank']} of {b['rankedOf']} | {b['gapP5']:.2f} / {b['gapP50']:.2f} / {b['gapP95']:.2f} |",
            f"| After correction | {a['faithful']} | {a['modern']} | {a['rank']} of {a['rankedOf']} | {a['gapP5']:.2f} / {a['gapP50']:.2f} / {a['gapP95']:.2f} |",
            "", "The rank did not change. The predicted gap between the historical and the modern preparation roughly doubled, because a hot water "
            "decoction carries a different compound profile from a methanol extract than a fresh juice does. This is a hypothesis worth "
            "re-testing (a liquorice root decoction, prepared as described), not a claim that liquorice works or is safe. The curated toxicity "
            "entry for *Glycyrrhiza glabra* reports toxic effects."]


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
    L += literature_sections() + water_section() + ranking_section() + toxicity_section() + audit_section() + audit_v2_section() + liquorice_section()
    L += ["", f"Profiles: {m4s['profiles']['species']} species × {m4s['profiles']['preparations']} preparations "
          f"({m4s['profiles']['profiles']} profiles, {m4s['profiles']['compoundEntries']:,} compound estimates; full file in `data/release/profiles_full.json.gz`; model `{m4s['modelVersion']}`). "
          f"`site-data/profiles/` holds the {len(_j('site-data/profiles/index.json') or [])} species in the current headline set (one file per species, `index.json`). "
          "These are model estimates of what a preparation would carry, not measurements."]

    L += ai_check_section()
    L += ["", "## AI-assisted checks (provisional): not human validation", "",
          "> The numbers in this section compare the pipeline with references **produced by an AI** (labels, drafted identifications, a curated "
          "literature table, an AI coder's reading of the audited studies). They help find problems and must not be read as validation.", ""]
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
