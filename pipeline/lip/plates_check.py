"""AI-assisted licence check of the botanical plates (basis "ai_assisted_check"; never human confirmation).

For each sourced plate in site-data/plates.json, read its Wikimedia Commons file page (the page's current wikitext and
revision id, through the Commons API) and record what the page itself states:
  - the licence templates ({{PD-old-100}}, {{PD-scan|...}}, ...), copied as written;
  - the original publication: the {{Information}} Source field, plus the page's plate-series categories;
  - the Date and Author fields, as written.
Flags are mechanical (no judgement): a Date that looks like an upload timestamp, no licence template, a template that
is not a public-domain one, a Source that is only a website.

Every record says "checked by AI agent on <date>; awaiting human confirmation". Plate `status` is never changed:
only a person can make it "confirmed". Writes data/reference/plates_ai_check_v1.json; `python -m lip plates` then
copies the summary into site-data/plates.json (aiCheck) and docs/IMAGE_CREDITS.md.
"""
import json
import re
from datetime import date

from .http import get_json
from .paths import ROOT, SITE_DATA
from .plates import API

OUT = ROOT / "data" / "reference" / "plates_ai_check_v1.json"
BASIS = "ai_assisted_check"
CHECKED_BY = "AI agent (Claude, claude-opus-5-5, in Claude Code), using pipeline/lip/plates_check.py"
PD_TEMPLATE = re.compile(r"^(PD-|Licensed-PD|PD$|Public domain)", re.I)
LICENCE_HINT = re.compile(r"^(PD|Licensed-PD|Public domain|CC-|Cc-|GFDL|Copyrighted|Attribution|Self)", re.I)


def _templates(wikitext: str) -> list[str]:
    """Top-level licence-like templates as written, e.g. 'PD-scan|PD-old-auto-expired|deathyear=1925'."""
    out = []
    for m in re.finditer(r"\{\{\s*([^{}]+?)\s*\}\}", wikitext):
        body = m.group(1).strip()
        name = body.split("|")[0].strip()
        if LICENCE_HINT.match(name):
            out.append(body)
    return list(dict.fromkeys(out))


def _field(wikitext: str, name: str) -> str | None:
    m = re.search(r"^\s*\|\s*" + name + r"\s*=(.*?)(?=^\s*\||^\}\})", wikitext, re.I | re.M | re.S)
    if not m:
        return None
    v = re.sub(r"\s+", " ", m.group(1)).strip()
    return v or None


def _plain(v: str | None) -> str | None:
    if not v:
        return v
    v = re.sub(r"\[(https?://\S+)\s+([^\]]+)\]", r"\2 (\1)", v)   # [url label] -> label (url)
    v = re.sub(r"\[\[:?(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", v)       # [[target|label]] -> label
    v = re.sub(r"'{2,}", "", v)
    return v.strip()


def run(today: str | None = None) -> dict:
    today = today or date.today().isoformat()
    plates = json.loads((SITE_DATA / "plates.json").read_text())
    records = []
    for p in plates:
        if p["status"] == "to_source" or not p.get("fileUrl"):
            continue
        title = "File:" + __import__("urllib.parse").parse.unquote(p["fileUrl"].split("/wiki/File:")[1]).replace("_", " ")
        r = get_json("commons", API, {"action": "query", "titles": title, "prop": "revisions|categories",
                                      "rvprop": "content|ids|timestamp", "rvslots": "main", "cllimit": "max",
                                      "format": "json", "formatversion": 2})
        page = r["query"]["pages"][0]
        rev = page["revisions"][0]
        wt = rev["slots"]["main"]["content"]
        tpl = _templates(wt)
        permission = _field(wt, "Permission")
        tpl += [t for t in _templates(permission or "") if t not in tpl]
        src, dt, author = _plain(_field(wt, "Source")), _plain(_field(wt, "Date")), _plain(_field(wt, "Author"))
        cats = [c["title"].removeprefix("Category:") for c in page.get("categories", [])]
        series = [c for c in cats if re.search(r"Köhler|Koehler|Thomé|Thome|Sturm|Deutschlands Flora|Flora von Deutschland", c, re.I)]
        flags = []
        if not tpl:
            flags.append("no licence template found on the page")
        elif not any(PD_TEMPLATE.match(t.split("|")[0].strip()) for t in tpl):
            flags.append("no public-domain template among the licence templates")
        if dt and re.search(r"\b(19[5-9]\d|20\d\d)\b", dt):
            flags.append("the Date field gives a modern date (likely the scan or upload date, not the plate's)")
        if not dt:
            flags.append("no Date field")
        if not author:
            flags.append("no Author field")
        if src and re.fullmatch(r"(?:https?://)?(?:www\.)?[\w.-]+\.\w+/?", src.strip()):
            flags.append("the Source field names only a website, not the printed work")
        records.append({
            "speciesId": p["speciesId"], "taxon": p["taxon"], "fileTitle": title, "fileUrl": p["fileUrl"],
            "pageRevisionId": rev["revid"], "pageRevisionTimestamp": rev["timestamp"],
            "licenceTemplates": tpl, "permissionField": _plain(permission),
            "sourceField": src, "seriesCategories": series, "dateField": dt, "authorField": author,
            "flags": flags,
            "basis": BASIS, "checkedBy": CHECKED_BY, "checkedOn": today,
            "statement": f"checked by AI agent on {today}; awaiting human confirmation",
        })
    # Same plate series, different author death years in the licence templates: a person must resolve it.
    work = {x["speciesId"]: x["work"] for x in plates}
    years: dict[str, set[str]] = {}
    for x in records:
        for t in x["licenceTemplates"]:
            for y in re.findall(r"deathyear\s*=\s*(\d{4})", t):
                years.setdefault(work[x["speciesId"]], set()).add(y)
    for x in records:
        ys = years.get(work[x["speciesId"]], set())
        if len(ys) > 1:
            mine = sorted({y for t in x["licenceTemplates"] for y in re.findall(r"deathyear\s*=\s*(\d{4})", t)})
            x["flags"].append(f"plates of this series state different author death years ({', '.join(sorted(ys))}); this page states {', '.join(mine) or 'none'}")
    out = {"basis": BASIS, "label": "AI-assisted check of the plate licences (provisional)",
           "method": "Commons API: current wikitext, revision id and categories of each file page; fields copied as written.",
           "checkedOn": today, "plates": records}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    return {"checked": len(records), "flagged": sum(1 for x in records if x["flags"]), "out": str(OUT.relative_to(ROOT))}
