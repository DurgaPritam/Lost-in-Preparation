"""Cached HTTP JSON client for external services (GBIF, WFO, Wikidata).

Every response is cached on disk (data/cache/<service>/<sha>.json) together with the request
and retrieval time, so results are reproducible and services are not queried twice.
"""
from __future__ import annotations

import hashlib
import json
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from .paths import ROOT

CACHE = ROOT / "data" / "cache"
USER_AGENT = "LostInPreparation/0.3 (https://github.com/DurgaPritam/Lost-in-Preperation) python-urllib"
_locks: dict[str, threading.Semaphore] = {}

# Some servers (WFO) omit their intermediate certificate. Published intermediates are shipped in
# config/certs/ and ADDED to the default trust store; certificate verification stays fully on.
SSL_CONTEXT = ssl.create_default_context()
for _pem in sorted((ROOT / "config" / "certs").glob("*.pem")):
    SSL_CONTEXT.load_verify_locations(cafile=str(_pem))
LIMITS = {"gbif": 6, "wfo": 4, "wikidata": 2}


class HTTPError(RuntimeError):
    pass


def _path(service: str, key: str):
    return CACHE / service / f"{hashlib.sha256(key.encode()).hexdigest()[:32]}.json"


def get_json(service: str, url: str, params: dict | None = None, data: dict | None = None,
             headers: dict | None = None, retries: int = 4) -> dict:
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    key = full + ("|POST|" + json.dumps(data, sort_keys=True) if data else "")
    cp = _path(service, key)
    if cp.exists():
        return json.loads(cp.read_text())["response"]
    sem = _locks.setdefault(service, threading.Semaphore(LIMITS.get(service, 2)))
    body = urllib.parse.urlencode(data).encode() if data else None
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    delay = 2.0
    for attempt in range(retries + 1):
        with sem:
            try:
                req = urllib.request.Request(full, data=body, headers=hdrs, method="POST" if body else "GET")
                with urllib.request.urlopen(req, timeout=45, context=SSL_CONTEXT) as r:
                    resp = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                    retry_after = e.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else delay)
                    delay *= 2
                    continue
                raise HTTPError(f"{service} HTTP {e.code} for {full[:200]}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise HTTPError(f"{service} unreachable: {e}") from e
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"request": key, "retrievedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                              "response": resp}, ensure_ascii=False))
    return resp


def pmap(fn, items, workers: int = 6):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))


def get_text(service: str, url: str, retries: int = 3) -> tuple[str, str, str]:
    """GET a text resource with the same on-disk cache. Returns (text, sha256, retrievedAt)."""
    cp = _path(service, url)
    if cp.exists():
        d = json.loads(cp.read_text())
        return d["text"], d["sha256"], d["retrievedAt"]
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=300, context=SSL_CONTEXT) as r:
                raw = r.read()
            break
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(2 * (attempt + 1))
    else:
        raise HTTPError(f"{service} unreachable: {last}")
    text = raw.decode("utf-8")
    meta = {"request": url, "retrievedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sha256": hashlib.sha256(raw).hexdigest(), "text": text}
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps(meta, ensure_ascii=False))
    return text, meta["sha256"], meta["retrievedAt"]
