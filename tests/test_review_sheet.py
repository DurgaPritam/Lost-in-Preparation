"""Study-set review sheet: complete, empty decision columns, riskiest rows first, fields traceable."""
from __future__ import annotations

import pandas as pd


def test_review_sheet():
    d = pd.read_csv("docs/STUDY_SET_REVIEW.csv", dtype={"decision": str, "reason": str})
    ss = pd.read_csv("data/interim/m3/study_set_proposal.csv")
    dec = pd.read_csv("config/study_set_review_decisions.csv").set_index("species")
    assert set(ss[ss.proposed].acceptedName) <= set(d.species) and set(dec.index) <= set(d.species)
    assert all(dec.loc[r.species, "decision"] == r.decision for r in d.itertuples() if r.species in dec.index)
    assert set(ss[ss.headline].acceptedName) == set(dec[dec.decision == "approve"].index) & set(ss[ss.proposed].acceptedName)
    nx = pd.read_csv("config/name_entry_exclusions.csv")
    assert d[d.species.isin(nx.species)].reReviewRequested.all()
    assert list(d.reviewOrder) == list(range(1, len(d) + 1))
    key = list(zip(-d.disputedEntries, -d.genusLevel.astype(int), d.minCountedConfidence.fillna(0), d.countedEntries))
    assert key == sorted(key)  # disputed, then genus-level, then low confidence first
    for r in d.itertuples():  # passage IDs are de-duplicated
        for col in (r.culpeperPassageIds, r.plinyPassageIds):
            ids = str(col).split() if isinstance(col, str) else []
            assert len(ids) == len(set(ids))
    assert d.wfoUrl.str.startswith("https://www.worldfloraonline.org/taxon/wfo-").all()
    assert d.descriptionExcerpt.notna().all() and d.descriptionSource.notna().all()
    tox = pd.read_csv("data/reference/toxicity_curated.csv").set_index("acceptedName")
    assert all(tox.loc[r.species, "toxicity"] == r.toxicity for r in d.itertuples() if r.species in tox.index)
    assert tox.loc["Euphorbia antiquorum", "toxicity"] == "toxic_reported" and "genus" in tox.loc["Euphorbia antiquorum", "evidenceScope"]
    assert "animals only" in tox.loc["Allium cepa", "evidenceScope"]
    p = pd.read_parquet("data/interim/passages.parquet").set_index("passage_id")
    for r in d.itertuples():  # every excerpt is cut from the cited passage(s)
        src = r.descriptionSource.rsplit(": ", 1)[1]
        assert r.descriptionExcerpt.replace(" …", "")[:60] in " ".join(p.loc[src:].text_clean.head(5))
    md = open("docs/STUDY_SET_REVIEW.md").read()
    assert "heuristic proxy" in md and "AI-drafted and unverified" in md
