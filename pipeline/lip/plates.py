"""Botanical plates for the site (contract v1.8, P39): public-domain 19th-century plates from Wikimedia Commons.

    python -m lip plates

For every species in site-data/profiles/index.json (the modelled species), the accepted name and its WFO synonyms are
looked up in three named plate series, in this order, by exact Commons file title:
  1. Köhler's Medizinal-Pflanzen (Gera, 1883-1914; plates 1887)   "<name> - Köhler–s Medizinal-Pflanzen-NNN.jpg"
  2. O. W. Thomé, Flora von Deutschland, Österreich und der Schweiz (Gera, 1885)   "Illustration <name>0.jpg"
  3. J. Sturm, Deutschlands Flora in Abbildungen (1796-1855)   "<name> Sturm<n>.jpg"
A file is accepted only if the Commons file description's licence (extmetadata LicenseShortName) is public domain;
its author, date and licence are recorded as Commons states them. A species with no accepted file gets no image (the
site shows the design's drawn empty state), never a doubtful one.

The image is downloaded once (no hotlinking; cached in data/cache/commons_files/) and written as AVIF and WebP at four
widths into site/public/plates/ (720 serves a 412 px phone at 1.75x without the 960 file). `retrievedAt` is the time the
file was downloaded (the cache file's modification time), so re-deriving the images does not move it. Every plate has status "sourced": the licence was read from Commons by this script;
"confirmed" is reserved for a person (design v2 DESIGN.md §11.8).

Writes site-data/plates.json, docs/IMAGE_CREDITS.md and data/interim/plates_summary.json.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

from contract import models as C

from .http import CACHE, HTTPError, USER_AGENT, get_json
from .paths import INTERIM, ROOT, SITE_DATA

API = "https://commons.wikimedia.org/w/api.php"
OUT_DIR = ROOT / "site" / "public" / "plates"
CREDITS = ROOT / "docs" / "IMAGE_CREDITS.md"
WIDTHS = (240, 480, 720, 960)
SERIES = [
    ("Köhler's Medizinal-Pflanzen (1887)", lambda n: f"File:{n} - Köhler–s Medizinal-Pflanzen-", r"\d+\.jpg"),
    ("Thomé, Flora von Deutschland, Österreich und der Schweiz (1885)", lambda n: f"File:Illustration {n}0", r"\.jpg"),
    ("Sturm, Deutschlands Flora in Abbildungen (1796–1855)", lambda n: f"File:{n} Sturm", r"\d+\.jpg"),
]
PD = re.compile(r"^(public domain|pd\b|pd-)", re.I)


def _clean(s: str | None) -> str | None:
    if not s:
        return None
    t = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", t).strip() or None


def _names(speciesId: str, accepted: str) -> list[str]:
    """Accepted name first, then the WFO synonyms recorded for the literature search (binomials only)."""
    out = [accepted]
    lit = INTERIM / "m5" / "literature" / f"{speciesId}.json"
    if lit.exists():
        for n in json.loads(lit.read_text()).get("names", []):
            b = " ".join(n.split()[:2])
            if re.fullmatch(r"[A-Z][a-z-]+ [a-z-]+", b) and b not in out:
                out.append(b)
    return out


def _find(name: str):
    for work, prefix, tail in SERIES:
        p = prefix(name)
        r = get_json("commons", API, {"action": "query", "list": "allpages", "apnamespace": 6, "apprefix": p[len("File:"):],
                                       "aplimit": 20, "format": "json"})
        titles = [x["title"] for x in r.get("query", {}).get("allpages", [])]
        hits = sorted(t for t in titles if re.fullmatch(re.escape(p) + tail, t))
        if hits:
            return work, hits[0]
    return None


def _info(title: str) -> dict:
    r = get_json("commons", API, {"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size|sha1|extmetadata",
                                   "iiurlwidth": 1200, "format": "json"})
    page = next(iter(r["query"]["pages"].values()))
    return page["imageinfo"][0]


def _download(url: str) -> tuple[bytes, str]:
    """The file's bytes and when it was downloaded (UTC, from the cache file)."""
    cp = CACHE / "commons_files" / f"{hashlib.sha256(url.encode()).hexdigest()[:32]}.bin"
    if cp.exists():
        return cp.read_bytes(), _mtime(cp)
    if os.environ.get("LIP_CACHE_ONLY", "").lower() in ("1", "true", "yes"):
        raise HTTPError(f"LIP_CACHE_ONLY=1: commons image not cached: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_bytes(data)
    return data, _mtime(cp)


def _mtime(p) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def _derive(slug: str, data: bytes) -> C.PlateImage:
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    # The fixed widths up to the original's, plus the original's own width when it is smaller than the largest and at
    # least 10% wider than the last fixed width (many Commons originals are about 480 px wide; never upscaled).
    widths = [w for w in WIDTHS if w <= im.width]
    if im.width < WIDTHS[-1] and im.width > 1.1 * (widths[-1] if widths else 0):
        widths.append(im.width)
    files = []
    for w in widths:
        h = round(im.height * w / im.width)
        r = im.resize((w, h), Image.LANCZOS)
        for fmt, ext, kw in (("AVIF", "avif", {"quality": 55}), ("WEBP", "webp", {"quality": 78, "method": 6})):
            r.save(OUT_DIR / f"{slug}-{w}.{ext}", fmt, **kw)
        files.append(w)
    top = files[-1]
    return C.PlateImage(
        avif=", ".join(f"/plates/{slug}-{w}.avif {w}w" for w in files),
        webp=", ".join(f"/plates/{slug}-{w}.webp {w}w" for w in files),
        src=f"/plates/{slug}-{top}.webp", width=top, height=round(im.height * top / im.width))


AI_CHECK = ROOT / "data" / "reference" / "plates_ai_check_v1.json"


def _ai_check(speciesId: str) -> "C.PlateAiCheck | None":
    """The AI-assisted licence check (pipeline/lip/plates_check.py), if run: provisional, never a confirmation."""
    if not AI_CHECK.exists():
        return None
    for x in json.loads(AI_CHECK.read_text())["plates"]:
        if x["speciesId"] == speciesId:
            pub = "; ".join(v for v in [x["sourceField"], ("categories: " + ", ".join(x["seriesCategories"])) if x["seriesCategories"] else None] if v)
            return C.PlateAiCheck(basis=x["basis"], statement=x["statement"], checkedOn=x["checkedOn"], checkedBy=x["checkedBy"],
                                  pageRevisionId=x["pageRevisionId"], licenceTemplates=x["licenceTemplates"], publication=pub or None,
                                  publicationDate=x["dateField"], flags=x["flags"])
    return None


def run() -> dict:
    idx = json.loads((SITE_DATA / "profiles" / "index.json").read_text())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.*"):
        old.unlink()
    plates, rows, skipped = [], [], []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for e in idx:
        sid, name = e["speciesId"], e["acceptedName"]
        found = None
        for n in _names(sid, name):
            f = _find(n)
            if f:
                found = (n, *f)
                break
        if not found:
            skipped.append({"speciesId": sid, "taxon": name, "reason": "no plate in the three series under the accepted name or a WFO synonym"})
            plates.append(C.PlateRecord(speciesId=sid, taxon=name, caption=f"{name}: no public-domain plate sourced", status="to_source"))
            continue
        matched, work, title = found
        ii = _info(title)
        md = ii.get("extmetadata", {})
        lic = _clean(md.get("LicenseShortName", {}).get("value"))
        if not lic or not PD.match(lic):
            skipped.append({"speciesId": sid, "taxon": name, "reason": f"{title}: licence on Commons is {lic!r}, not public domain"})
            plates.append(C.PlateRecord(speciesId=sid, taxon=name, caption=f"{name}: no public-domain plate sourced", status="to_source"))
            continue
        src = ii.get("thumburl") or ii["url"]
        data, retrieved = _download(src)
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        img = _derive(slug, data)
        author = _clean(md.get("Artist", {}).get("value"))
        date = _clean(md.get("DateTimeOriginal", {}).get("value"))
        date = re.sub(r"\s*date QS:\S+", "", date).strip() or None if date else None  # drop Wikidata QuickStatements markup
        rec = C.PlateRecord(
            speciesId=sid, taxon=name, caption=f"{name}, from {work}" + (f" (as {matched})" if matched != name else ""),
            status="sourced", licence=lic, licenceDetail=_clean(md.get("UsageTerms", {}).get("value")), host="Wikimedia Commons",
            fileUrl=ii["descriptionurl"], sourceUrl=src, author=author, date=date, work=work, matchedName=matched,
            sha256=hashlib.sha256(data).hexdigest(), retrievedAt=retrieved, image=img)
        rec.aiCheck = _ai_check(sid)
        plates.append(rec)
        rows.append(rec)
    (SITE_DATA / "plates.json").write_text(json.dumps([p.model_dump(mode="json") for p in plates], ensure_ascii=False, indent=1) + "\n")
    L = ["# Image credits", "",
         "Generated by `python -m lip plates`. Do not edit by hand.",
         "",
         "Botanical plates shown on the site. Each was found by its exact Wikimedia Commons file title in one of three named "
         "plate series (Sturm from 1796, Thomé 1885, Köhler 1887), and accepted only because the Commons file description gives a public-domain licence. "
         "Author, date and licence are as stated on Commons. The images were downloaded once and are served from this site, "
         "as resized AVIF and WebP copies; they are not hotlinked.",
         "",
         "**Status: sourced, not yet confirmed.** A script read each licence from Commons. The design requires a person to "
         "confirm each file before release (`status: confirmed`).",
         "",
         "| Plant | Plate series | Commons file | Author (as on Commons) | Date field on Commons (may be the upload date) | Licence (as on Commons) |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| *{r.taxon}*{f' (as *{r.matchedName}*)' if r.matchedName != r.taxon else ''} | {r.work} | [{r.fileUrl.rsplit('/', 1)[-1]}]({r.fileUrl}) | "
                 f"{r.author or 'not stated'} | {r.date or 'not stated'} | {r.licence}{f' ({r.licenceDetail})' if r.licenceDetail and r.licenceDetail != r.licence else ''} |")
    checked = [r for r in rows if r.aiCheck]
    if checked:
        L += ["", "## AI-assisted licence check (provisional)", "",
              f"An AI agent read each Commons file page (`python -m lip plates-check`, data/reference/plates_ai_check_v1.json) and "
              "recorded what the page states. This is **not** a human confirmation: every plate stays `sourced` until a person "
              "checks it. Flags are mechanical observations for that person.", "",
              "| Plant | Licence templates on the page | Original publication (Source field; categories) | Date field | Status | Flags |",
              "|---|---|---|---|---|---|"]
        for r in checked:
            a = r.aiCheck
            L.append(f"| *{r.taxon}* | {', '.join('`{{' + t.replace('|', chr(92) + '|') + '}}`' for t in a.licenceTemplates) or 'none found'} | {(a.publication or 'not stated').replace('|', '/')} | "
                     f"{a.publicationDate or 'not stated'} | {a.statement} (page revision {a.pageRevisionId}) | {'; '.join(a.flags) or 'none'} |")
    L += ["", f"## No plate ({len(skipped)})", "",
          "These plants show the design's drawn placeholder instead of an image:", ""]
    L += [f"- *{s['taxon']}*: {s['reason']}" for s in skipped]
    CREDITS.write_text("\n".join(L) + "\n")
    summary = {"species": len(idx), "sourced": len(rows), "noPlate": skipped, "generatedAt": now}
    (INTERIM / "plates_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary
