#!/usr/bin/env bash
# Operator diagnostics for local workflow readiness.
set -euo pipefail

RUN_FULL=0
COST_HYGIENE=0
LEGACY_CLEANUP_REPORT=0
if [ "${1:-}" = "--full" ]; then
  RUN_FULL=1
elif [ "${1:-}" = "--cost-hygiene" ] || [ "${1:-}" = "cost-hygiene" ]; then
  COST_HYGIENE=1
elif [ "${1:-}" = "--legacy-cleanup" ] || [ "${1:-}" = "legacy-cleanup" ]; then
  LEGACY_CLEANUP_REPORT=1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/ensure-bun-path.sh
. "$ROOT/scripts/lib/ensure-bun-path.sh"
cd "$ROOT"

if [ "$COST_HYGIENE" = "1" ]; then
  echo "doctor: cost & context hygiene (non-fatal diagnostic)"
  set +e
  python3 "$ROOT/scripts/validate_cost_context_hygiene_pack.py" \
    --repo-root "$ROOT" \
    --report \
    --no-fail
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "doctor: unexpected validator exit: $rc" >&2
    exit 1
  fi
  echo "doctor: cost-hygiene section complete (see artifacts/cost-hygiene/ for JSON)"
  exit 0
fi

if [ "$LEGACY_CLEANUP_REPORT" = "1" ]; then
  echo "doctor: MAT legacy cleanup audit summary (artifacts/update-mat/legacy-cleanup.jsonl)"
  python3 "$ROOT/scripts/adoption/apply_mat_legacy_cleanup.py" --repo-root "$ROOT" --report
  exit 0
fi

echo "doctor: repo=$ROOT"

check_file() {
  local path="$1"
  if [ -e "$path" ]; then
    echo "OK   $path"
  else
    echo "FAIL $path"
    return 1
  fi
}

FAILED=0

for path in \
  ".cursor/hooks.json" \
  ".cursor/worktrees.json" \
  ".cursor/mcp.json" \
  ".cursor/commands/mat-doctor.md" \
  ".cursor/commands/mat-wt-check.md" \
  ".cursor/agents/test-writer.md" \
  ".cursor/agents/style-reviewer.md" \
  "scripts/setup-dev.sh" \
  "scripts/check-worktrees.sh" \
  "scripts/phase1-verify.sh"; do
  check_file "$path" || FAILED=1
done

if command -v python3 >/dev/null 2>&1; then
  echo "OK   python3=$(python3 --version 2>&1)"
else
  echo "FAIL python3 missing"
  FAILED=1
fi

if command -v bun >/dev/null 2>&1; then
  echo "OK   bun=$(bun --version 2>&1)"
else
  echo "WARN bun missing (required for observability apps)"
fi

python3 - <<'PY' || FAILED=1
import json
from pathlib import Path

for path in [".cursor/hooks.json", ".cursor/worktrees.json", ".cursor/mcp.json"]:
    json.loads(Path(path).read_text())
print("OK   core JSON files parse")
PY

bash scripts/check-worktrees.sh --strict || FAILED=1

if [ "$RUN_FULL" -eq 1 ]; then
  echo "Running full verification via scripts/phase1-verify.sh ..."
  bash scripts/phase1-verify.sh || FAILED=1
fi

if [ "$FAILED" -eq 0 ]; then
  echo "doctor result: PASS"
  exit 0
fi

echo "doctor result: FAIL"
exit 1
