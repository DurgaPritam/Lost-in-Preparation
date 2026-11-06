"""Effect of the v3 footnote rule on the approved study-set species (before -> after).

Compares data/interim/m2/before_footnote_rule/name_candidates.parquet (snapshot taken just before the rule)
with the current candidates. For each species the project lead approved, the COUNTED name entries
(top-1 = the species, undisputed, confidence >= 0.6, not removed by the reviewer) are computed on both sides
with the same reviewer exclusions, so only changes made by the resolver show. A species whose counted
entries, or whose eligibility, changes is flagged for the project lead's re-review; the rest stay approved.
Writes data/interim/m2/footnote_rule_changes.json and config-independent CSV detail.
"""
from __future__ import annotations

import json

import pandas as pd

from ..paths import INTERIM, ROOT

BEFORE = INTERIM / "m2" / "before_footnote_rule" / "name_candidates.parquet"
OUT = INTERIM / "m2" / "footnote_rule_changes.json"
MIN_CONF, MIN_ATTEST = 0.6, 3


def _counted(cand: pd.DataFrame, species: str, removed: set, inv: pd.DataFrame) -> pd.DataFrame:
    t = cand[(cand["rank"] == 1) & (cand.acceptedName == species)]
    keep = pd.Series([(n, species) not in removed for n in t.nameId], index=t.index, dtype=bool)
    t = t[(~t.disputed) & (t.confidence >= MIN_CONF) & keep]
    return t.merge(inv[["nameId", "passages", "namesInEntry"]], on="nameId", how="left")


def flagged_species() -> set[str]:
    """Approved species whose counted name entries changed under the footnote rule (pending re-review)."""
    if not BEFORE.exists():
        return set()
    dec = pd.read_csv(ROOT / "config" / "study_set_review_decisions.csv")
    nx = pd.read_csv(ROOT / "config" / "name_entry_exclusions.csv")
    removed = set(zip(nx.nameId, nx.species))
    inv = pd.read_parquet(INTERIM / "m2" / "name_inventory.parquet")
    b, a = pd.read_parquet(BEFORE), pd.read_parquet(INTERIM / "m2" / "name_candidates.parquet")
    return {sp for sp in dec[dec.decision == "approve"].species
            if set(_counted(b, sp, removed, inv).nameId) != set(_counted(a, sp, removed, inv).nameId)}


def run() -> dict:
    dec = pd.read_csv(ROOT / "config" / "study_set_review_decisions.csv")
    approved = list(dec[dec.decision == "approve"].species)
    nx = pd.read_csv(ROOT / "config" / "name_entry_exclusions.csv")
    removed = set(zip(nx.nameId, nx.species))
    inv = pd.read_parquet(INTERIM / "m2" / "name_inventory.parquet")
    b, a = pd.read_parquet(BEFORE), pd.read_parquet(INTERIM / "m2" / "name_candidates.parquet")
    ss = pd.read_csv(INTERIM / "m3" / "study_set_proposal.csv").set_index("acceptedName")
    out = {"rule": "resolver v3 footnote rule (hedged / contradicted / competing-authority footnote binomials are not "
                   "used as identifications; the name is disputed)", "approvedBefore": approved, "species": {}}
    for sp in approved:
        cb, ca = _counted(b, sp, removed, inv), _counted(a, sp, removed, inv)
        lost = sorted(set(cb.nameId) - set(ca.nameId))
        gained = sorted(set(ca.nameId) - set(cb.nameId))
        att_a = round(float((ca.passages / ca.namesInEntry.clip(lower=1)).sum()), 1) if len(ca) else 0.0
        conf = {n: (round(float(cb.set_index("nameId").confidence[n]), 3), round(float(ca.set_index("nameId").confidence[n]), 3))
                for n in set(cb.nameId) & set(ca.nameId)
                if abs(cb.set_index("nameId").confidence[n] - ca.set_index("nameId").confidence[n]) > 0.005}
        why = {}
        for n in lost:
            r = a[(a.nameId == n) & (a["rank"] == 1)].iloc[0]
            trig = json.loads(r.footnoteTriggers) if isinstance(r.footnoteTriggers, str) else []
            why[n] = {"nameAsWritten": r.nameAsWritten, "nowTop1": r.acceptedName, "nowDisputed": bool(r.disputed),
                      "nowConfidence": round(float(r.confidence), 3), "triggers": trig}
        changed = bool(lost or gained)
        out["species"][sp] = {"countedBefore": sorted(cb.nameId), "countedAfter": sorted(ca.nameId), "lost": why,
                              "gained": gained, "confidenceShifts": conf, "attestationAfter": att_a,
                              "eligibleAfter": bool(ss.loc[sp, "eligible"]) if sp in ss.index else False,
                              "resolutionChanged": changed, "flagForReReview": changed}
    out["flagged"] = [s for s, v in out["species"].items() if v["flagForReReview"]]
    out["unchanged"] = [s for s, v in out["species"].items() if not v["flagForReReview"]]
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return out
