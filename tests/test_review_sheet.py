"""Study-set review sheet: complete, empty decision columns, riskiest rows first, fields traceable."""
from __future__ import annotations

import pandas as pd


def test_review_sheet():
    d = pd.read_csv("docs/STUDY_SET_REVIEW.csv", dtype={"decision": str, "reason": str})
    ss = pd.read_csv("data/interim/m3/study_set_proposal.csv")
    assert sorted(d.species) == sorted(ss[ss.proposed].acceptedName)
    assert d.decision.isna().all() and d.reason.isna().all()  # left for the reviewer
    assert list(d.reviewOrder) == list(range(1, len(d) + 1))
    key = list(zip(-d.disputedEntries, -d.genusLevel.astype(int), d.minCountedConfidence.fillna(0), d.countedEntries))
    assert key == sorted(key)  # disputed, then genus-level, then low confidence first
    assert d.wfoUrl.str.startswith("https://www.worldfloraonline.org/taxon/wfo-").all()
    assert d.descriptionExcerpt.notna().all() and d.descriptionSource.notna().all()
    tox = pd.read_csv("data/reference/toxicity_curated.csv").set_index("acceptedName")
    assert all(tox.loc[r.species, "toxicity"] == r.toxicity for r in d.itertuples())
    p = pd.read_parquet("data/interim/passages.parquet").set_index("passage_id")
    for r in d.itertuples():  # every excerpt is cut from the cited passage(s)
        src = r.descriptionSource.rsplit(": ", 1)[1]
        assert r.descriptionExcerpt.replace(" …", "")[:60] in " ".join(p.loc[src:].text_clean.head(5))
    md = open("docs/STUDY_SET_REVIEW.md").read()
    assert "heuristic proxy" in md and "AI-drafted and unverified" in md
