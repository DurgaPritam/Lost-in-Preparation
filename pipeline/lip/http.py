"""Cached HTTP JSON client for external services (GBIF, WFO, Wikidata).

Every response is cached on disk (data/cache/<service>/<sha>.json) together with the request
and retrieval time, so results are reproducible and services are not queried twice.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
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
LIMITS = {"gbif": 6, "wfo": 4, "wikidata": 2, "ncbi": 1, "wfo_gql": 2}
# minimum seconds between NETWORK requests per service (cached responses are never throttled).
# NCBI E-utilities: at most 3 requests per second without an API key.
MIN_INTERVAL = {"ncbi": 0.4}
_last_call: dict[str, float] = {}
_throttle_lock = threading.Lock()


def _throttle(service: str) -> None:
    gap = MIN_INTERVAL.get(service)
    if not gap:
        return
    with _throttle_lock:
        wait = _last_call.get(service, 0.0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[service] = time.monotonic()


class HTTPError(RuntimeError):
    pass


def _cache_only(service: str, key: str) -> None:
    """LIP_CACHE_ONLY=1 (see lip/__init__.py): a cache miss fails at once, without retries or a network attempt."""
    if os.environ.get("LIP_CACHE_ONLY", "").lower() in ("1", "true", "yes"):
        raise HTTPError(f"LIP_CACHE_ONLY=1: {service} response not cached: {key[:200]}")


def _path(service: str, key: str):
    return CACHE / service / f"{hashlib.sha256(key.encode()).hexdigest()[:32]}.json"


def get_json(service: str, url: str, params: dict | None = None, data: dict | None = None,
             headers: dict | None = None, retries: int = 4, json_body: dict | None = None) -> dict:
    """GET, form POST (`data`) or JSON POST (`json_body`), cached on disk."""
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    key = full + ("|POST|" + json.dumps(data, sort_keys=True) if data else "") + \
        ("|JSON|" + json.dumps(json_body, sort_keys=True) if json_body is not None else "")
    cp = _path(service, key)
    if cp.exists():
        return json.loads(cp.read_text())["response"]
    _cache_only(service, key)
    sem = _locks.setdefault(service, threading.Semaphore(LIMITS.get(service, 2)))
    body = urllib.parse.urlencode(data).encode() if data else None
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    if json_body is not None:
        body = json.dumps(json_body).encode()
        hdrs["Content-Type"] = "application/json"
    delay = 2.0
    for attempt in range(retries + 1):
        with sem:
            try:
                _throttle(service)
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
            except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError, json.JSONDecodeError) as e:
                if attempt < retries:  # dropped connections and truncated responses are retried
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
    _cache_only(service, url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries + 1):
        try:
            _throttle(service)
            with urllib.request.urlopen(req, timeout=300, context=SSL_CONTEXT) as r:
                raw = r.read()
            break
        except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError) as e:
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


def get_pdf_text(service: str, url: str, retries: int = 5) -> tuple[str, str, str]:
    """GET a PDF (cached as raw bytes) and return (extracted text, sha256 of the PDF, retrievedAt).

    Text is extracted with pypdf; whitespace is left as extracted (callers normalise before
    matching quotes). Backs off on HTTP 429 (rate limiting).
    """
    cp = _path(service, url)
    pdf = cp.with_suffix(".pdf")
    if cp.exists() and pdf.exists():
        meta = json.loads(cp.read_text())
        raw = pdf.read_bytes()
    else:
        _cache_only(service, url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        last = None
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=300, context=SSL_CONTEXT) as r:
                    raw = r.read()
                break
            except urllib.error.HTTPError as e:
                last = e
                time.sleep((20 if e.code == 429 else 2) * (attempt + 1))
            except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError) as e:
                last = e
                time.sleep(2 * (attempt + 1))
        else:
            raise HTTPError(f"{service} unreachable: {last}")
        if not raw.startswith(b"%PDF"):
            raise HTTPError(f"{service}: not a PDF: {url}")
        meta = {"request": url, "retrievedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "sha256": hashlib.sha256(raw).hexdigest()}
        cp.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(raw)
        cp.write_text(json.dumps(meta))
    import io

    from pypdf import PdfReader
    text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
    return text, meta["sha256"], meta["retrievedAt"]
