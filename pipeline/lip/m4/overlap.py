"""Training-overlap check for the logP comparison.

RDKit's Crippen logP implements Wildman & Crippen, J. Chem. Inf. Comput. Sci. 39, 868–873 (1999)
(cited in the RDKit Crippen module docstring). Its training molecules are not distributed with
RDKit, so exact overlap with our test set is NOT determinable. Proxy used here: the publication
year of every source the SangsterLogP record cites (Crossref, by DOI). A compound whose measured
values were all first published in 2000 or later cannot have entered a 1999 training set through
those sources (it could still have an older, unrecorded measurement). Metrics are recomputed on
that post-1999 subset.
"""
from __future__ import annotations

import json
import re

import pandas as pd

from ..http import HTTPError, get_json, pmap
from ..paths import INTERIM
from .validate_logp import metrics

OUT = INTERIM / "m4"
CROSSREF = "https://api.crossref.org/works/{}"
DOI = re.compile(r"10\.\d{4,9}/[^\s|;]+", re.I)


def doi_year(doi: str) -> int | None:
    try:
        r = get_json("crossref", CROSSREF.format(doi))
    except HTTPError:
        return None
    msg = r.get("message", {})
    for k in ("published-print", "published-online", "issued", "created"):
        parts = msg.get(k, {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def run() -> dict:
    s = pd.read_csv(OUT / "logp_validation.csv")
    s["dois"] = s.source.fillna("").map(lambda x: sorted({d.rstrip(".,") for d in DOI.findall(x)}))
    dois = sorted({d for ds in s.dois for d in ds})
    year = dict(zip(dois, pmap(doi_year, dois, 4)))
    s["sourceYears"] = s.dois.map(lambda ds: [year.get(d) for d in ds])
    s["earliestYear"] = s.sourceYears.map(lambda ys: min([y for y in ys if y], default=None))
    s["yearKnown"] = s.sourceYears.map(lambda ys: bool(ys) and all(y is not None for y in ys))
    post = s[s.yearKnown & (s.earliestYear >= 2000) & (s.xtb_status == "ok")]
    pre = s[s.yearKnown & (s.earliestYear < 2000) & (s.xtb_status == "ok")]
    out = {
        "crippenReference": "Wildman & Crippen, J. Chem. Inf. Comput. Sci. 39, 868-873 (1999), per RDKit Crippen docstring",
        "trainingSetAvailable": False,
        "compounds": int(len(s)), "withAllSourceYearsKnown": int(s.yearKnown.sum()),
        "post1999": int(len(post)), "pre2000": int(len(pre)),
        "unknownYear": int((~s.yearKnown).sum()),
        "rdkit_post1999": metrics(post.logP_exp, post.logP_rdkit) if len(post) >= 10 else None,
        "xtb_post1999": metrics(post.logP_exp, post.logP_xtb) if len(post) >= 10 else None,
        "rdkit_pre2000": metrics(pre.logP_exp, pre.logP_rdkit) if len(pre) >= 10 else None,
        "xtb_pre2000": metrics(pre.logP_exp, pre.logP_xtb) if len(pre) >= 10 else None,
    }
    s.drop(columns=["dois"]).to_csv(OUT / "logp_validation_years.csv", index=False)
    (OUT / "logp_overlap.json").write_text(json.dumps(out, indent=2))
    return out
