"""LIP_CACHE_ONLY=1 refuses every network connection (Phase 9 fresh-clone reproducibility), while cached reads work."""
import os
import subprocess
import sys

from lip.paths import ROOT

ENV = {**os.environ, "LIP_CACHE_ONLY": "1", "PYTHONPATH": f"{ROOT / 'pipeline'}{os.pathsep}{ROOT}"}


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], env=ENV, capture_output=True, text=True, timeout=60)


def test_network_is_refused_in_cache_only_mode():
    r = _run("import lip, urllib.request\n"
             "try:\n    urllib.request.urlopen('http://127.0.0.1:9/', timeout=2)\nexcept Exception as e:\n    print(type(e).__name__, e)\n")
    assert "LIP_CACHE_ONLY=1: network access refused" in r.stdout, r.stdout + r.stderr


def test_http_client_cache_miss_fails_loudly():
    r = _run("import lip\nfrom lip import http\n"
             "try:\n    http.get_json('cache_only_test', 'https://example.invalid/never-cached')\n"
             "except Exception as e:\n    print('refused' if 'LIP_CACHE_ONLY' in str(e) or 'LIP_CACHE_ONLY' in str(e.__cause__) else repr(e))\n")
    assert "refused" in r.stdout, r.stdout + r.stderr


def test_not_active_without_the_variable():
    env = {k: v for k, v in ENV.items() if k != "LIP_CACHE_ONLY"}
    r = subprocess.run([sys.executable, "-c", "import lip, socket; print(socket.create_connection.__module__)"],
                       env=env, capture_output=True, text=True, timeout=60)
    assert r.stdout.strip() == "socket", r.stdout + r.stderr
