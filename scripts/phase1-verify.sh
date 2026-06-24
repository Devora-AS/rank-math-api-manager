#!/usr/bin/env bash
# Phase 1 automated verification (Python unit tests + optional Bun server/client smoke).
# Env skips: PHASE1_VERIFY_SKIP_UNITTEST=1, PHASE1_VERIFY_SKIP_BUN=1, PHASE1_VERIFY_SKIP_CLIENT=1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/ensure-bun-path.sh
. "$ROOT/scripts/lib/ensure-bun-path.sh"
cd "$ROOT"
mkdir -p artifacts/phase1

# MAT adopted sidecar repos (bootstrap) ship `.mat/README.md` and usually omit MAT-source-only trees.
MAT_ADOPTED_SIDECAR=0
if [ -f "$ROOT/.mat/README.md" ]; then
  MAT_ADOPTED_SIDECAR=1
fi

# Rolling local verification log. Dated sign-off logs under artifacts/phase1/ are the
# tracked distilled evidence; this file is local mutable runtime exhaust.
REPORT="$ROOT/artifacts/phase1/phase1-verify.log"
{
  echo "phase1-verify started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "repo: $ROOT"
  echo

   echo "=== workflow artifact validation ==="
   VA_ARGS=(--repo-root "$ROOT" --require-current-plan)
   if [ "$MAT_ADOPTED_SIDECAR" = "1" ]; then
     VA_ARGS+=(--optional-handoff-artifacts)
   fi
   python3 .cursor/scripts/validate_artifacts.py "${VA_ARGS[@]}"
   echo "workflow artifacts: OK"

  echo
  echo "=== closeout freshness and coherence ==="
  python3 scripts/validate_closeout_coherence.py --repo-root "$ROOT"
  echo "closeout coherence: OK"

  echo
  echo "=== cost & context hygiene pack ==="
  # MAT source repo: strict (no .mat/cost-hygiene-adoption.json) → fail-fast. Adopted repos
  # with warn_first may set CURSOR_MAT_COST_HYGIENE_ENFORCE=strict in CI to hard-fail until
  # the team merges the suggested ignore fragments, or pass --enforce strict via a forked verify step.
  python3 scripts/validate_cost_context_hygiene_pack.py --repo-root "$ROOT" --enforce auto
  echo "cost context hygiene pack: OK"

  echo "=== hooks.json parse (python) ==="
  python3 - <<'PY'
import json, pathlib
p = pathlib.Path(".cursor/hooks.json")
data = json.loads(p.read_text())
assert data.get("version") == 1
assert isinstance(data.get("hooks"), dict)
print("hooks.json: OK, events:", len(data["hooks"]))
PY

  echo
  echo "=== repo workflow surface checks ==="
  python3 - <<'PY'
import json
from pathlib import Path

required_paths = [
    Path(".cursor/agents/test-writer.md"),
    Path(".cursor/agents/style-reviewer.md"),
    Path(".cursor/commands/mat-wt-check.md"),
    Path(".cursor/commands/mat-doctor.md"),
    Path("scripts/check-worktrees.sh"),
    Path("scripts/doctor.sh"),
    Path("scripts/setup-dev.sh"),
]
missing = [str(p) for p in required_paths if not p.exists()]
if missing:
    raise SystemExit(f"Missing expected workflow surfaces: {missing}")

worktrees = json.loads(Path(".cursor/worktrees.json").read_text())
names = {entry.get("name") for entry in worktrees.get("worktrees", [])}
for required_name in ("builder-agent", "verifier-agent"):
    if required_name not in names:
        raise SystemExit(f"worktrees.json missing expected role: {required_name}")
if not isinstance(worktrees.get("optional_cloud_agent_templates", []), list):
    raise SystemExit("worktrees.json optional_cloud_agent_templates must be a list")
print("workflow surfaces: OK")
PY

  echo
  echo "=== script executability checks ==="
  for script in \
    scripts/phase1-verify.sh \
    scripts/start-system.sh \
    scripts/parallelism-gate.sh \
    scripts/check-worktrees.sh \
    scripts/doctor.sh \
    scripts/setup-dev.sh \
    scripts/adoption/apply_cost_hygiene_bootstrap.py \
    scripts/adoption/detect_cost_hygiene_template.py \
    .cursor/hooks/bootstrap_worktree.sh; do
    if [ ! -x "$script" ]; then
      echo "script not executable: $script" >&2
      exit 1
    fi
  done
  echo "script executability: OK"

  if [ "${PHASE1_VERIFY_SKIP_UNITTEST:-0}" = "1" ]; then
    echo
    echo "=== python unittest (tests/): SKIPPED via PHASE1_VERIFY_SKIP_UNITTEST=1 ==="
  elif [ "$MAT_ADOPTED_SIDECAR" = "1" ] && [ -d "$ROOT/.mat/tests" ]; then
    echo
    echo "=== python unittest (.mat/tests/) [MAT adopted sidecar profile] ==="
    python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v
  else
    echo
    echo "=== python unittest (tests/) ==="
    python3 -m unittest discover -s tests -p 'test_*.py' -v
  fi

  if [ "$MAT_ADOPTED_SIDECAR" = "0" ] && [ -f "$ROOT/scripts/adoption/mat-legacy-fingerprints.py" ]; then
    echo
    echo "=== mat legacy fingerprint verify-all ==="
    python3 "$ROOT/scripts/adoption/mat-legacy-fingerprints.py" --repo "$ROOT" --verify-all
    echo "mat legacy fingerprint verify-all: OK"
  fi

  echo
  echo "=== optional tooling gate (mcp.json) ==="
  python3 - <<'PY'
import json, pathlib
# Phase 1 baseline: committed MCP config must parse.
data = json.loads(pathlib.Path(".cursor/mcp.json").read_text())
assert isinstance(data, dict)
print("mcp.json: OK (valid JSON, Phase 1 baseline)")
PY

  if [ "${PHASE1_VERIFY_SKIP_BUN:-0}" = "1" ]; then
    echo
    echo "=== bun observability smoke: SKIPPED via PHASE1_VERIFY_SKIP_BUN=1 ==="
  elif [ ! -d "$ROOT/apps/server" ]; then
    echo
    echo "=== bun observability smoke: SKIPPED (apps/server not present; typical MAT adopted tree) ==="
  elif command -v bun >/dev/null 2>&1; then
    echo
    echo "=== bun observability smoke (apps/server) ==="
    export OBSERVABILITY_DB_PATH="$ROOT/artifacts/phase1/phase1-events.sqlite"
    export PORT="${PORT:-3011}"
    cd "$ROOT/apps/server"
    bun install
    bun run src/index.ts &
    PID=$!
    cleanup_server() {
      kill "$PID" >/dev/null 2>&1 || true
      wait "$PID" 2>/dev/null || true
    }
    trap cleanup_server EXIT
    sleep 1
    HEALTH_RESPONSE="$(curl -fsS "http://127.0.0.1:${PORT}/health")"
    printf '%s' "$HEALTH_RESPONSE" | python3 - <<'PY'
import sys
text = sys.stdin.read()
print(text[:200])
PY
    echo
    POST_RESPONSE="$(curl -fsS -X POST "http://127.0.0.1:${PORT}/events" \
      -H 'Content-Type: application/json' \
      -H 'X-Hook-Event: PostToolUse' \
      -d '{"session_id":"phase1","tool_name":"Read","tool_input":{},"tool_output":"ok"}' \
    )"
    printf '%s' "$POST_RESPONSE" | python3 - <<'PY'
import sys
text = sys.stdin.read()
print(text[:400])
PY
    echo
    cleanup_server
    trap - EXIT
    echo "bun smoke: OK"
  else
    echo
    echo "=== bun observability smoke: SKIPPED (bun not installed) ==="
  fi

  if [ "${PHASE1_VERIFY_SKIP_CLIENT:-0}" = "1" ]; then
    echo
    echo "=== bun observability client: SKIPPED via PHASE1_VERIFY_SKIP_CLIENT=1 ==="
  elif [ ! -d "$ROOT/apps/client" ]; then
    echo
    echo "=== bun observability client: SKIPPED (apps/client not present) ==="
  elif ! command -v bun >/dev/null 2>&1; then
    echo
    echo "=== bun observability client: SKIPPED (bun not installed) ==="
  else
    echo
    echo "=== bun observability client (apps/client) ==="
    if command -v node >/dev/null 2>&1; then
      node_ver="$(node -v)"
      node_major="${node_ver#v}"
      node_major="${node_major%%.*}"
      if [ -n "$node_major" ] && { [ "$node_major" -lt 20 ] 2>/dev/null || [ "$node_major" -ne 22 ] 2>/dev/null; }; then
        echo "phase1-verify: WARN — Node ${node_ver} detected; CI pins Node 22 for apps/client (Vite 8 requires 20.19+)." >&2
      fi
    fi
    cd "$ROOT/apps/client"
    bun install --frozen-lockfile
    bun run type-check
    bun run test:vitest
    bun run build
    cd "$ROOT"
    echo "bun observability client: OK"
  fi

  echo
  echo "phase1-verify finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} 2>&1 | tee "$REPORT"

echo "Wrote log: $REPORT"
