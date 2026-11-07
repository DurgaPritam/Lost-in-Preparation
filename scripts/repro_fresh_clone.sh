#!/usr/bin/env bash
# Phase 9: fresh-clone reproducibility test, cache-only mode, no keys.
#
#   scripts/repro_fresh_clone.sh [REPO=.] [REF=HEAD]
#
# 1. Clones REF into a temporary directory: only committed files, with no .env, data/cache/ or data/raw/ texts.
# 2. Runs every step with LIP_CACHE_ONLY=1 (lip/__init__.py refuses all network connections) in a clean environment:
#    no GROQ/ANTHROPIC keys, an empty HOME (so no ~/.config/anthropic), no inherited variables.
#    The only network use is installing packages (PyPI for requirements.txt, npm for site/), which is outside the
#    pipeline.
# 3. Records each step's status, then compares every regenerated file with the committed one. A file whose only
#    differences are timestamps (generatedAt, retrievedAt, ...) counts as reproduced.
#
# Writes <tmp>/repro_report.md and prints its path. Exit 0 when every step expected to reproduce from committed files
# passes and no committed output changes beyond timestamps.
set -uo pipefail

SRC="$(cd "${1:-.}" && git rev-parse --show-toplevel)"
REF="${2:-HEAD}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/lip-repro.XXXXXX")"
REPO="$WORK/repo"
REPORT="$WORK/repro_report.md"
LOG="$WORK/logs"
mkdir -p "$LOG" "$WORK/home"

git clone -q --no-local "$SRC" "$REPO" && git -C "$REPO" checkout -q "$REF"
COMMIT="$(git -C "$REPO" rev-parse --short HEAD)"
PY="${PYTHON:-python3.11}"

declare -a ROWS=()
FAIL=0
# run <name> <expect: reproduce|needs-download> <command...>
run() {
  local name="$1" expect="$2"; shift 2
  local start=$SECONDS
  ( cd "$REPO" && env -i HOME="$WORK/home" PATH="$REPO/.venv/bin:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin" \
      LANG=en_US.UTF-8 PYTHONPATH="$REPO/pipeline:$REPO" LIP_CACHE_ONLY=1 "$@" ) > "$LOG/$name.log" 2>&1
  local rc=$? status
  if [ $rc -eq 0 ]; then status="pass"
  elif grep -q "LIP_CACHE_ONLY=1" "$LOG/$name.log"; then status="needs download (cache-only refused the network)"
  elif grep -q "passages.parquet\|data/raw/" "$LOG/$name.log"; then status="needs the raw texts (before fetch --verify)"
  else status="FAIL (exit $rc)"; fi
  if [ "$expect" = reproduce ] && [ $rc -ne 0 ]; then FAIL=1; fi
  ROWS+=("| \`$name\` | $expect | $status | $((SECONDS - start)) s | \`logs/$name.log\` |")
  echo "[repro] $name: $status"
}

echo "[repro] clone of $COMMIT in $REPO"
( cd "$REPO" && "$PY" -m venv .venv && .venv/bin/pip install -q -r requirements.txt -r requirements-quantum.txt ) > "$LOG/install-python.log" 2>&1 \
  && ROWS+=("| install Python deps (PyPI; requirements.txt + requirements-quantum.txt) | setup | pass | | \`logs/install-python.log\` |") \
  || { ROWS+=("| install Python deps (PyPI; requirements.txt + requirements-quantum.txt) | setup | FAIL | | \`logs/install-python.log\` |"); FAIL=1; }

# Expected to reproduce from committed files alone.
run contract        reproduce   python -m lip contract
run m6-hypotheses   reproduce   python -m lip m6 hypotheses
run results         reproduce   python -m lip results
run review-merge    reproduce   python -m lip review-merge
# AI-assisted checks and Phase 8, from committed inputs. The full QAOA benchmark (lip m8 bench, ~45 min) is not re-run
# here; its committed outputs are exported and validated instead.
run gap-sensitivity reproduce   python -m lip m5 gap-sensitivity
run review-priority reproduce   python -m lip m1 review-priority
run m8-pool         reproduce   python -m lip m8 pool
run m8-export       reproduce   python -m lip m8 export
# Needs the git-ignored study texts to re-verify every quote; in cache-only mode it must refuse.
run m5-ai-check     needs-download python -m lip m5 ai-check
# Before the raw texts are downloaded these need data/interim/passages.parquet (built by ingest), so they fail loudly.
run site-data       needs-download python -m lip site
run pytest          needs-download python -m pytest -q -p no:cacheprovider
# The raw historical texts are not committed: download them once, checking each against the SHA-256 pinned in
# data/raw/manifest.json (the only pipeline network step; keyless). Everything after it runs cache-only again.
( cd "$REPO" && env -i HOME="$WORK/home" PATH="$REPO/.venv/bin:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin" \
    PYTHONPATH="$REPO/pipeline:$REPO" python -m lip fetch --verify ) > "$LOG/fetch-verify.log" 2>&1 \
  && ROWS+=("| \`fetch --verify\` (4 raw texts, checksums pinned) | setup | pass | | \`logs/fetch-verify.log\` |") \
  || { ROWS+=("| \`fetch --verify\` (4 raw texts, checksums pinned) | setup | FAIL | | \`logs/fetch-verify.log\` |"); FAIL=1; }
run ingest          reproduce   python -m lip ingest
run site-data-2     reproduce   python -m lip site
run pytest-2        reproduce   python -m pytest -q -p no:cacheprovider -rs
# Needs the git-ignored literature caches (abstracts and open-access texts); in cache-only mode it must fail loudly.
run m5-audit-v2     needs-download python -m lip m5 audit-v2

# The website: install, then the same gates as CI (minus Lighthouse, which needs a browser).
run site-install    reproduce   bash -c 'cd site && npm ci --no-audit --no-fund'
run site-typecheck  reproduce   bash -c 'cd site && npm run typecheck'
run site-lint       reproduce   bash -c 'cd site && npm run lint'
run site-test       reproduce   bash -c 'cd site && npm test'
run site-build      reproduce   bash -c 'cd site && npm run build'

# Compare regenerated outputs with the committed ones.
( cd "$REPO" && git checkout -q -- data/silver/silver_v1.json 2>/dev/null; true )
CHANGED="$(cd "$REPO" && git status --porcelain --untracked-files=all -- . ':!site/node_modules' ':!site/.next' ':!site/out' ':!site/public/data' ':!site/lib/data/generated' ':!.venv' ':!site/next-env.d.ts' ':!site/tsconfig.tsbuildinfo' | sed 's/^...//')"
DIFF_ROWS=""
for f in $CHANGED; do
  verdict="$(cd "$REPO" && "$REPO/.venv/bin/python" - "$f" <<'PY'
import json, re, subprocess, sys
f = sys.argv[1]
TS = re.compile(r'(generatedAt|retrievedAt|generated_at|retrieved_at|"date"|timestamp|Generated on|generated on)', re.I)
try:
    old = subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, text=True, check=True).stdout
except subprocess.CalledProcessError:
    print("new file (not committed)"); sys.exit()
new = open(f, encoding="utf-8").read()
if f.endswith(".json"):
    def strip(o):
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if not TS.search(f'"{k}"')}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o
    try:
        print("timestamps only" if strip(json.loads(old)) == strip(json.loads(new)) else "CONTENT CHANGED"); sys.exit()
    except json.JSONDecodeError:
        pass
d = [l for l in subprocess.run(["git", "diff", "-U0", "--", f], capture_output=True, text=True).stdout.splitlines()
     if l[:1] in "+-" and not l.startswith(("+++", "---"))]
print("timestamps only" if d and all(TS.search(l) for l in d) else "CONTENT CHANGED")
PY
)"
  case "$verdict" in *CHANGED*|new*) FAIL=1;; esac
  DIFF_ROWS+="| \`$f\` | $verdict |"$'\n'
done

{
  echo "# Fresh-clone reproducibility report"
  echo
  echo "- Commit: \`$COMMIT\`, cloned with \`git clone --no-local\`; mode \`LIP_CACHE_ONLY=1\`; no API keys; empty HOME."
  echo "- Python: $("$REPO/.venv/bin/python" --version 2>&1); Node: $(node --version 2>/dev/null)"
  echo
  echo "| Step | Expected | Result | Time | Log |"
  echo "|---|---|---|---|---|"
  printf '%s\n' "${ROWS[@]}"
  echo
  echo "## Regenerated files that differ from the commit"
  echo
  if [ -z "$DIFF_ROWS" ]; then echo "None: every committed output was reproduced byte for byte."; else
    echo "| File | Difference |"; echo "|---|---|"; printf '%s' "$DIFF_ROWS"; fi
  echo
  echo "Overall: $([ $FAIL -eq 0 ] && echo PASS || echo FAIL)"
} > "$REPORT"
echo "[repro] report: $REPORT"
exit $FAIL
