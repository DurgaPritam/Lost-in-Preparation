"""Download raw source texts and record URL, SHA-256 and retrieval date in data/raw/manifest.json."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone

from .paths import RAW_MANIFEST, ROOT, load_sources

USER_AGENT = "lost-in-preparation-research-pipeline/0.1 (hackathon research; python-urllib)"


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if RAW_MANIFEST.exists():
        return json.loads(RAW_MANIFEST.read_text())
    return {"files": []}


def fetch(refresh: bool = False) -> dict:
    manifest = load_manifest()
    by_id = {f["source_id"]: f for f in manifest["files"]}
    for src in load_sources():
        dest = ROOT / src["raw_path"]
        if dest.exists() and src["id"] in by_id and not refresh:
            print(f"[fetch] {src['id']}: present, not re-downloaded")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(src["download_url"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        by_id[src["id"]] = {
            "source_id": src["id"],
            "url": src["download_url"],
            "catalogue_url": src["url"],
            "path": src["raw_path"],
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"[fetch] {src['id']}: {len(data):,} bytes sha256={by_id[src['id']]['sha256'][:12]}…")
    manifest["files"] = sorted(by_id.values(), key=lambda f: f["source_id"])
    RAW_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    RAW_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def verify(source: dict) -> None:
    """Raise if the raw file is missing or its checksum differs from the manifest."""
    manifest = {f["source_id"]: f for f in load_manifest()["files"]}
    entry = manifest.get(source["id"])
    if entry is None:
        raise RuntimeError(f"{source['id']} not in manifest; run `python -m lip fetch`")
    actual = sha256_file(ROOT / source["raw_path"])
    if actual != entry["sha256"]:
        raise RuntimeError(f"{source['id']}: checksum mismatch ({actual} != {entry['sha256']})")
