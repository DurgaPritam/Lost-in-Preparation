"""Study-set proposal (for human approval): species with several attestations and good coverage.

Per species (top-1 M2 candidate, in WFO):
  attestations  ATTESTATION PROXY = recipe-scope passages of the name entries resolved to the
                species (1652 "Vertues and use" paragraphs; Pliny chapter body paragraphs divided by
                the number of plants named in the chapter). Not a count of extracted recipes.
  sources       how many of {Culpeper 1652, Pliny} attest the species
  compounds     distinct standardised compounds (M3); poor coverage flagged
Attestations count only name entries whose resolution is undisputed with confidence >= 0.6 (v2: a
disputed entry neither counts nor vetoes the species). Eligible: attestations >= 3, coverage not poor, and not removed by a recorded decision
(config/study_set_exclusions.csv: who decided, when, why).
Ranked by sources, then attestations, then compounds; the top `SIZE` are proposed.
Toxicity columns (proposed species only): hand-curated entries from m3/toxicity.py, one reputable source
each (EMA herbal documents or CC-licensed PMC articles) with a verbatim quote checked against the fetched
source; basis ai_drafted_unverified, verified_by empty. "unknown" / "no_toxicity_reported" are NOT
evidence of safety. (The Wikipedia list is still used only for M2's toxic-confusion screen.)
Nothing here is a claim about efficacy or safety.
"""
from __future__ import annotations

import pandas as pd

from ..paths import INTERIM, ROOT

OUT_CSV = INTERIM / "m3" / "study_set_proposal.csv"
EXCLUSIONS = ROOT / "config" / "study_set_exclusions.csv"  # species removed by a recorded human decision
NAME_EXCLUSIONS = ROOT / "config" / "name_entry_exclusions.csv"  # name entries a reviewer removed from a species
DECISIONS = ROOT / "config" / "study_set_review_decisions.csv"  # the project lead's review (approve / unsure / reject)
OUT_MD = ROOT / "docs" / "STUDY_SET_PROPOSAL.md"
SIZE = 40
MIN_ATTEST, MIN_CONF = 3, 0.6


def build() -> pd.DataFrame:
    inv = pd.read_parquet(INTERIM / "m2" / "name_inventory.parquet")
    cand = pd.read_parquet(INTERIM / "m2" / "name_candidates.parquet")
    cov = pd.read_csv(INTERIM / "m3" / "coverage.csv")
    top = cand[(cand["rank"] == 1) & cand.inWFO].merge(inv[["nameId", "passages", "namesInEntry"]], on="nameId")
    top["attest"] = top.passages / top.namesInEntry.clip(lower=1)
    # name entries a reviewer removed from a species (config/name_entry_exclusions.csv): neither count nor veto
    nx = pd.read_csv(NAME_EXCLUSIONS) if NAME_EXCLUSIONS.exists() else pd.DataFrame(columns=["nameId", "species"])
    drop = set(zip(nx.nameId, nx.species))
    top = top[[(n, a) not in drop for n, a in zip(top.nameId, top.acceptedName)]]
    # only undisputed, confident name resolutions count as attestations (disputed names neither count nor veto)
    top = top[(~top.disputed) & (top.confidence >= MIN_CONF)]
    g = top.groupby("acceptedName").agg(
        wfoId=("wfoId", "first"), family=("family", "first"),
        attestations=("attest", "sum"),
        sources=("source", lambda s: len(set(s))),
        sourceList=("source", lambda s: ", ".join(sorted(set(s)))),
        namesAsWritten=("nameAsWritten", lambda s: "; ".join(sorted(set(s))[:4])),
        minConfidence=("confidence", "min"),
        anyDisputed=("disputed", "max"),
    ).reset_index()
    g = g.merge(cov[["acceptedName", "nCompounds", "nReferences", "poorCoverage"]], on="acceptedName", how="left")
    g["nCompounds"] = g.nCompounds.fillna(0).astype(int)
    g["nReferences"] = g.nReferences.fillna(0).astype(int)
    g["poorCoverage"] = g.poorCoverage.fillna(True).astype(bool)
    g["attestations"] = g.attestations.round(1)
    if "toxicConfusion" in top:
        g = g.merge(top.groupby("acceptedName").toxicConfusion.max().rename("toxicConfusion").reset_index(), on="acceptedName", how="left")
    nx = pd.read_csv(NAME_EXCLUSIONS) if NAME_EXCLUSIONS.exists() else pd.DataFrame(columns=["nameId", "species", "nameAsWritten", "reviewerNote"])
    excl = pd.read_csv(EXCLUSIONS) if EXCLUSIONS.exists() else pd.DataFrame(columns=["acceptedName", "reason"])
    g["excludedByDecision"] = g.acceptedName.map(dict(zip(excl.acceptedName, excl.reason))).fillna("")
    g["eligible"] = (g.attestations >= MIN_ATTEST) & (~g.poorCoverage) & (g.excludedByDecision == "")
    g = g.sort_values(["eligible", "sources", "attestations", "nCompounds"], ascending=[False, False, False, False])
    g["proposed"] = False
    g.loc[g[g.eligible].index[:SIZE], "proposed"] = True
    from . import toxicity
    tx = toxicity.build(list(g[g.proposed].acceptedName)).set_index("acceptedName")
    for col, src in (("toxicity", "toxicity"), ("toxicityNote", "summary"), ("toxicitySource", "sourceName"),
                     ("toxicityUrl", "sourceUrl"), ("toxicityQuote", "quote"), ("toxicityBasis", "basis"),
                     ("toxicityVerifiedBy", "verified_by")):
        g[col] = g.acceptedName.map(tx[src]).fillna("")
    g.loc[~g.proposed, "toxicity"] = "not_curated"
    d = pd.read_csv(DECISIONS) if DECISIONS.exists() else pd.DataFrame(columns=["species", "decision"])
    dmap = dict(zip(d.species, d.decision))
    g["reviewDecision"] = g.acceptedName.map(dmap).fillna("")
    g["approved"] = g.reviewDecision.map({"approve": "yes", "unsure": "no", "reject": "no"}).fillna("")  # unsure counts as reject
    g["headline"] = g.proposed & (g.approved == "yes")
    fixed = set(nx.species)
    g["reReviewRequested"] = g.acceptedName.isin(fixed) & g.reviewDecision.isin(["unsure", "reject"])
    return g


def toxicity_path() -> str:
    from .toxicity import OUT
    return str(OUT.relative_to(ROOT))


def main() -> str:
    g = build()
    nx = pd.read_csv(NAME_EXCLUSIONS) if NAME_EXCLUSIONS.exists() else pd.DataFrame(columns=["nameId", "species", "nameAsWritten", "reviewerNote"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT_CSV, index=False)
    p = g[g.proposed]
    lines = [
        "# Study-set proposal (for approval)",
        "",
        f"Generated by `python -m lip m3 studyset` from `{OUT_CSV.relative_to(ROOT)}`. Do not edit the numbers by hand; "
        "mark decisions in the `approved` column of the CSV.",
        "",
        f"**{len(p)} species proposed** out of {int(g.eligible.sum())} eligible and {len(g)} resolved. "
        f"**Headline set: {int(g.headline.sum())} species approved** by the project lead (`config/study_set_review_decisions.csv`; unsure counts as reject).",
        *([f"Name entries removed by the reviewer (`config/name_entry_exclusions.csv`): "
           + "; ".join(f"{r.nameAsWritten} from *{r.species}* ({r.reviewerNote})" for r in nx.itertuples())] if len(nx) else []),
        "",
        *([f"Removed by a recorded decision (`config/study_set_exclusions.csv`): "
           + "; ".join(f"*{r.acceptedName}*: {r.excludedByDecision}" for r in g[g.excludedByDecision != ""].itertuples())]
          if (g.excludedByDecision != "").any() else []),
        "",
        "Eligibility:",
        "- an attestation proxy of ≥ 3 recipe-scope passages, counted only from name entries resolved without dispute and with confidence ≥ 0.6;",
        "- compound coverage that is not poor.",
        "",
        "Species are ranked by the number of sources attesting them, then attestations, then compounds.",
        "**Attestations are a passage-count proxy, not extracted recipes.**",
        "",
        "**Toxicity** entries are hand-curated per species and **AI-drafted, unverified** (`ai_drafted_unverified`; `verified_by` empty, for review). "
        "Each cites one reputable source opened in the pipeline run (EMA herbal documents, or a CC-licensed PMC article) and quotes one sentence of it, "
        f"re-checked against the fetched source every run; full entries in `{toxicity_path()}`. Categories describe what the source says, not a safety rating: "
        "`toxic_reported`, `concern_reported` (a specific risk, contraindication or warning), `no_toxicity_reported` and `unknown` (no source located) "
        "are **never evidence of safety**, and `data_lacking` means the source says the data are missing. "
        "Toxic plants stay in the proposal, because a lab may still re-test them under appropriate safety controls; the flag is for the lab's risk assessment.",
        "",
        "| # | Species (WFO) | Family | Names as written | Sources | Attest. | Compounds | Refs | Min conf. | Toxicity (AI-drafted, unverified) | Toxicity source | Review |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(p.itertuples(), 1):
        lines.append(f"| {i} | *{r.acceptedName}* ({r.wfoId}) | {r.family or ''} | {r.namesAsWritten} | {r.sourceList} | "
                     f"{r.attestations:g} | {r.nCompounds} | {r.nReferences} | {r.minConfidence:.2f} | "
                     f"{'**' + r.toxicity + '**' if r.toxicity == 'toxic_reported' else r.toxicity} | "
                     f"{f'[{r.toxicitySource}]({r.toxicityUrl})' if r.toxicityUrl else 'none located'} | "
                     f"{(r.reviewDecision or 'pending') + (' (re-review requested)' if r.reReviewRequested else '')} |")
    OUT_MD.write_text("\n".join(lines) + "\n")
    return OUT_MD.read_text()
