"""Tests that read git-ignored download caches (data/cache/, tiktoken's cache) skip, with the cache named and the
command that fetches it, when the cache is missing: a fresh clone has none (docs/PHASE9_CHECKLIST.md)."""
from __future__ import annotations

import hashlib
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from lip.http import HTTPError


@contextmanager
def needs_cache(what: str, command: str):
    """Run the body with cached HTTP only (lip.http fails at once on a cache miss) and turn a miss into a skip."""
    old = os.environ.get("LIP_CACHE_ONLY")
    os.environ["LIP_CACHE_ONLY"] = "1"
    try:
        yield
    except HTTPError as e:
        if "LIP_CACHE_ONLY" in str(e):
            pytest.skip(f"needs the git-ignored cache {what}, which is missing ({str(e)[:120]}); fetch it with: {command}")
        raise
    finally:
        if old is None:
            os.environ.pop("LIP_CACHE_ONLY", None)
        else:
            os.environ["LIP_CACHE_ONLY"] = old


def require_tiktoken(encoding: str = "o200k_base") -> None:
    """tiktoken downloads its encoding files on first use; skip if this one is not cached."""
    url = f"https://openaipublic.blob.core.windows.net/encodings/{encoding}.tiktoken"
    base = os.environ.get("TIKTOKEN_CACHE_DIR") or os.environ.get("DATA_GYM_CACHE_DIR") or os.path.join(tempfile.gettempdir(), "data-gym-cache")
    if not (Path(base) / hashlib.sha1(url.encode()).hexdigest()).exists():
        pytest.skip(f"needs tiktoken's cached {encoding} file in {base}, which is missing; fetch it with: "
                    f"python -c \"import tiktoken; tiktoken.get_encoding('{encoding}')\"")


def require_dir(rel: str, what: str, command: str) -> None:
    """Skip when a git-ignored cache directory is missing or empty: for code that tolerates cache misses quietly
    (for example by leaving a compound unresolved) instead of raising."""
    from lip.paths import ROOT
    d = ROOT / rel
    if not d.is_dir() or not any(d.iterdir()):
        pytest.skip(f"needs the git-ignored cache {what} ({rel}), which is missing or empty; fetch it with: {command}")
