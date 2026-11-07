"""Review pass v1 over four open checks (basis "ai_assisted_check"; provisional, never human validation).

Inputs, hand-written in data/reference/review_v1/ by an AI reviewer (Claude, claude-opus-5-5, in Claude Code):
  toxicity_review.csv      each study-set toxicity entry judged against the cached source text around its quote
                           (the quote itself is verified word for word by m3/toxicity.py on every run)
  genus_audit_review.csv   a second look at the 32 genus-signal findings (docs/GENUS_SIGNAL_AUDIT.md)
  study_set_rationale.csv  a rationale per study-set decision whose reason was never received, written from the
                           proposal's evidence; NOT the project lead's own words
  plate_series_facts.csv   per plate series: the latest relevant death year considered, its source, the publication
                           years

Computed here: plate_licence_review.csv, each plate's licence template (as read from the Commons page by
plates_check.py) tested against the latest death year considered for its series, and US publication before 1931.

Checks: basis is ai_assisted_check everywhere, no verified_by / gold column exists, every row matches the record it
reviews, and every corrected toxicity summary is the one now in toxicity_curated.csv. Nothing here writes to gold
fields, fills verified_by, or changes a plate status. Writes data/reference/review_v1.json.
"""
from __future__ import annotations

import csv
import json
import re

from .paths import INTERIM, ROOT

DIR = ROOT / "data" / "reference" / "review_v1"
OUT = ROOT / "data" / "reference" / "review_v1.json"
BASIS = "ai_assisted_check"
YEAR = 2026            # the year the review was made (licence terms are tested against it)
US_CUTOFF = 1931       # works published before 1 January 1931 are in the US public domain in 2026


class ReviewError(ValueError):
    pass


def _rows(name: str) -> list[dict]:
    with open(DIR / name, newline="") as f:
        rows = list(csv.DictReader(f))
    cols = set(rows[0]) if rows else set()
    if cols & {"verified_by", "verifiedBy", "gold"}:
        raise ReviewError(f"{name}: a verification/gold column must not exist in an AI review file")
    bad = [r for r in rows if r.get("basis") != BASIS]
    if bad:
        raise ReviewError(f"{name}: {len(bad)} rows without basis {BASIS!r}")
    return rows


def _term(template: str, deathyear: int) -> tuple[bool, str]:
    """Does the template's own term hold for an author who died in `deathyear`? (Templates as written on Commons.)"""
    name = template.split("|")[0].strip()
    m = re.search(r"deathyear\s*=\s*(\d{4})", template)
    if name.startswith("PD-old-auto") and m:
        # the template computes its term from its own deathyear; test the later of the two years against 70 years
        y = max(int(m.group(1)), deathyear)
        return y + 70 < YEAR, f"{name} (deathyear {m.group(1)}): {y} + 70 = {y + 70}"
    if name.startswith("PD-scan"):
        rest = [t for t in template.split("|")[1:] if t.startswith("PD-")]
        return _term("|".join(rest + [p for p in template.split("|") if "deathyear" in p]), deathyear) if rest else (False, f"{name} without an underlying term")
    terms = {"PD-old": 70, "PD-old-70": 70, "PD-old-80-expired": 80, "PD-old-100": 100}
    if name in terms:
        n = terms[name]
        return deathyear + n < YEAR, f"{name}: {deathyear} + {n} = {deathyear + n}"
    return False, f"{name}: term not recognised by this check"


def plates() -> list[dict]:
    facts = {r["work"]: r for r in _rows("plate_series_facts.csv")}
    check = json.loads((ROOT / "data" / "reference" / "plates_ai_check_v1.json").read_text())
    work = {p["speciesId"]: p["work"] for p in json.loads((ROOT / "site-data" / "plates.json").read_text())}
    out = []
    for p in check["plates"]:
        w = work[p["speciesId"]]
        f = facts.get(w)
        if f is None:
            raise ReviewError(f"no series facts for {w!r}")
        dy, pub_last = int(f["latestDeathYearConsidered"]), int(f["publishedLastYear"])
        held = [_term(t, dy) for t in p["licenceTemplates"]]
        ok_term = bool(held) and all(h for h, _ in held)
        us = pub_last < US_CUTOFF
        notes = [x for x in p["flags"]] + ([f["note"]] if f.get("note") else [])
        out.append({"taxon": p["taxon"], "fileUrl": p["fileUrl"], "pageRevisionId": p["pageRevisionId"], "work": w,
                    "licenceTemplates": " ; ".join(p["licenceTemplates"]),
                    "latestDeathYearConsidered": dy, "deathYearSource": f["deathYearSource"],
                    "termTest": " ; ".join(t for _, t in held), "termHolds": "yes" if ok_term else "no",
                    "publishedBefore1931": "yes" if us else "no",
                    "consistentWithPublicDomain": "yes" if (ok_term and us) else "unsure",
                    "notes": " | ".join(notes), "basis": BASIS, "reviewedBy": f["reviewedBy"], "reviewedOn": f["reviewedOn"]})
    with open(DIR / "plate_licence_review.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(out[0]))
        wr.writeheader()
        wr.writerows(out)
    return out


def run() -> dict:
    tox = _rows("toxicity_review.csv")
    cur = {r["acceptedName"]: r for r in csv.DictReader(open(ROOT / "data" / "reference" / "toxicity_curated.csv", newline=""))}
    for r in tox:
        c = cur.get(r["acceptedName"])
        if c is None:
            raise ReviewError(f"toxicity review: {r['acceptedName']} has no curated entry")
        if c["toxicity"] != r["categoryAsDrafted"]:
            raise ReviewError(f"toxicity review: {r['acceptedName']} category is {c['toxicity']}, review says {r['categoryAsDrafted']}")
        if r["correctedSummary"] and c["summary"] != r["correctedSummary"]:
            raise ReviewError(f"toxicity review: corrected summary for {r['acceptedName']} is not applied in m3/toxicity.py")
        if c.get("verified_by"):
            raise ReviewError(f"toxicity: verified_by is set for {r['acceptedName']}; only a person may set it")

    genus = _rows("genus_audit_review.csv")
    audit = {r["nameId"] for r in csv.DictReader(open(INTERIM / "m2" / "genus_signal_audit.csv", newline=""))}
    missing = [r["nameId"] for r in genus if r["nameId"] not in audit]
    if missing:
        raise ReviewError(f"genus review: {len(missing)} nameIds not in the genus-signal audit: {missing[:3]}")

    ss = _rows("study_set_rationale.csv")
    dec = {r["species"]: r for r in csv.DictReader(open(ROOT / "config" / "study_set_review_decisions.csv", newline=""))}
    for r in ss:
        d = dec.get(r["species"])
        if d is None or d["decision"] != r["decision"]:
            raise ReviewError(f"study-set rationale: {r['species']} decision does not match config/study_set_review_decisions.csv")
        if "not the project lead's own words" not in r["rationaleKind"]:
            raise ReviewError(f"study-set rationale: {r['species']} must say it is not the project lead's own words")

    pl = plates()

    def count(rows, key):
        c: dict[str, int] = {}
        for r in rows:
            c[r[key]] = c.get(r[key], 0) + 1
        return dict(sorted(c.items()))

    out = {
        "basis": BASIS, "label": "Review pass v1 (provisional; not human validation)",
        "reviewer": "Claude (claude-opus-5-5) in Claude Code", "reviewedOn": "2026-11-08",
        "toxicity": {"n": len(tox), "summaryFaithful": count(tox, "summaryFaithful"),
                     "categoryDisagreements": [r["acceptedName"] for r in tox if r["categoryReviewerWouldGive"] != r["categoryAsDrafted"]],
                     "summariesCorrected": [r["acceptedName"] for r in tox if r["correctedSummary"]],
                     "file": "data/reference/review_v1/toxicity_review.csv"},
        "plates": {"n": len(pl), "consistentWithPublicDomain": count(pl, "consistentWithPublicDomain"),
                   "withNotes": sum(1 for r in pl if r["notes"]), "file": "data/reference/review_v1/plate_licence_review.csv"},
        "genusAudit": {"n": len(genus), "agree": count(genus, "agree"),
                       "lewisShortAsQuotedInAudit": sum(1 for r in genus if r["sourceChecked"].startswith("Lewis & Short entry as quoted")),
                       "generalKnowledgeOnly": sum(1 for r in genus if r["sourceChecked"].startswith("general knowledge only")),
                       "sourceReopened": 0,
                       "file": "data/reference/review_v1/genus_audit_review.csv"},
        "studySetRationale": {"n": len(ss), "kind": "rationale from the proposal's evidence; not the project lead's own words",
                              "file": "data/reference/review_v1/study_set_rationale.csv"},
        "notMeasured": ["M1 extraction accuracy vs a human gold set", "annotator self-consistency (re-annotation)",
                        "human hand-check of the M5 extractor", "M2 name resolution vs human-checked identifications"],
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return out
