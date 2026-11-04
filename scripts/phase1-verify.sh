#!/usr/bin/env bash
# Phase 1 automated verification (Python unit tests + optional Bun server/client smoke).
#
# Profiles (E3):
#   --profile source-full|source-python-only|adopted-operational|adopted-contract
#   --manifest PATH (default: artifacts/phase1/verification-manifest.json)
#
# Env skips:
#   PHASE1_VERIFY_SKIP_BUN=1, PHASE1_VERIFY_SKIP_CLIENT=1
#   PHASE1_VERIFY_STATE_DIR=PATH — isolated manifest run state (tests / nested invocations)
#   PHASE1_VERIFY_SKIP_UNITTEST=1 — skip unittest on MAT source (tests/) or force skip on adopted
#     (.mat/tests/); deprecated for adopted repos (operational profile skips by default).
# Adopted sidecar (.mat/README.md) unittest profiles:
#   adopted_operational (default) — skip .mat/tests with visible banner
#   adopted_contract_tests — PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1 runs .mat/tests
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/ensure-bun-path.sh
. "$ROOT/scripts/lib/ensure-bun-path.sh"
cd "$ROOT"
mkdir -p artifacts/phase1


PROFILE=""
MANIFEST_PATH="$ROOT/artifacts/phase1/verification-manifest.json"
while [ $# -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --manifest)
      MANIFEST_PATH="${2:-}"
      case "$MANIFEST_PATH" in
        /*) ;;
        *) MANIFEST_PATH="$ROOT/$MANIFEST_PATH" ;;
      esac
      shift 2
      ;;
    -h|--help)
      echo "Usage: bash scripts/phase1-verify.sh [--profile NAME] [--manifest PATH]"
      exit 0
      ;;
    *)
      echo "phase1-verify: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

# MAT adopted sidecar repos (bootstrap) ship `.mat/README.md` and usually omit MAT-source-only trees.
MAT_ADOPTED_SIDECAR=0
if [ -f "$ROOT/.mat/README.md" ]; then
  MAT_ADOPTED_SIDECAR=1
fi

# Rolling local verification log. Dated sign-off logs under artifacts/phase1/ are the
# tracked distilled evidence; this file is local mutable runtime exhaust.

VP_PY=(python3 "$ROOT/scripts/verification_profiles.py")
if [ -z "$PROFILE" ]; then
  if [ -f "$ROOT/scripts/verification_profiles.py" ]; then
    PROFILE="$("${VP_PY[@]}" default-profile --repo-root "$ROOT")"
  elif [ "$MAT_ADOPTED_SIDECAR" = "1" ]; then
    PROFILE="adopted-operational"
  else
    PROFILE="source-full"
  fi
fi
case "$PROFILE" in
  source-full|source-python-only|adopted-operational|adopted-contract) ;;
  *)
    echo "phase1-verify: unknown profile '$PROFILE'" >&2
    exit 2
    ;;
esac

if [ "$PROFILE" = "source-python-only" ]; then
  : "${PHASE1_VERIFY_SKIP_BUN:=1}"
  : "${PHASE1_VERIFY_SKIP_CLIENT:=1}"
fi
if [ "$PROFILE" = "adopted-contract" ]; then
  : "${PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS:=1}"
fi

# Per-run state dir: nested phase1-verify (e.g. exit-trap unittest) must not rm -rf a
# fixed path while the parent run is still recording checks.
if [ -n "${PHASE1_VERIFY_STATE_DIR:-}" ]; then
  STATE_DIR="$PHASE1_VERIFY_STATE_DIR"
  case "$STATE_DIR" in
    /*) ;;
    *) STATE_DIR="$ROOT/$STATE_DIR" ;;
  esac
  rm -rf "$STATE_DIR"
  mkdir -p "$STATE_DIR"
else
  STATE_DIR="$(mktemp -d "$ROOT/artifacts/phase1/.verification-run.XXXXXX")"
fi
MANIFEST_ENABLED=0
if [ -f "$ROOT/scripts/verification_profiles.py" ]; then
  STATE_DIR="$("${VP_PY[@]}" init --repo-root "$ROOT" --profile "$PROFILE" --manifest "$MANIFEST_PATH" --state-dir "$STATE_DIR")"
  MANIFEST_ENABLED=1
else
  mkdir -p "$STATE_DIR"
fi

echo "phase1-verify profile: $PROFILE"
BUN_SERVER_PID=""
_MANIFEST_FINALIZED=0

_finalize_manifest() {
  local ec="${1:-0}"
  if [ "${MANIFEST_ENABLED:-0}" != "1" ]; then
    return 0
  fi
  if [ "$ec" -ne 0 ]; then
    _record_check phase1_verify_exit fail "phase1-verify exited with status ${ec} before clean completion" 0 || true
  fi
  "${VP_PY[@]}" finalize --state-dir "$STATE_DIR" --manifest "$MANIFEST_PATH" \
    --schema "$ROOT/artifacts/verification-manifest.schema.json" >/dev/null
}

_cleanup_bun_server() {
  if [ -n "${BUN_SERVER_PID:-}" ]; then
    kill "$BUN_SERVER_PID" >/dev/null 2>&1 || true
    wait "$BUN_SERVER_PID" 2>/dev/null || true
    BUN_SERVER_PID=""
  fi
}

_on_phase1_exit() {
  local ec=$?
  _cleanup_bun_server
  if [ "${MANIFEST_ENABLED:-0}" = "1" ] && [ "${_MANIFEST_FINALIZED:-0}" != "1" ]; then
    _MANIFEST_FINALIZED=1
    _finalize_manifest "$ec" || true
  fi
  exit "$ec"
}

trap '_on_phase1_exit' EXIT
echo "phase1-verify manifest: $MANIFEST_PATH"
echo "phase1-verify repo_layout: $([ "$MAT_ADOPTED_SIDECAR" = "1" ] && echo adopted || echo source)"

_now_ms() {
  python3 -c 'import time; print(int(time.time()*1000))'
}

_record_check() {
  local id="$1" status="$2" reason="$3" duration_ms="${4:-0}"
  if [ "$MANIFEST_ENABLED" != "1" ]; then
    return 0
  fi
  "${VP_PY[@]}" record \
    --state-dir "$STATE_DIR" \
    --id "$id" \
    --status "$status" \
    --reason "$reason" \
    --duration-ms "$duration_ms" \
    --verify-command "phase1-verify:${id}"
}

_skip_check() {
  local id="$1" reason="$2"
  echo "=== ${id}: SKIP — ${reason} ==="
  _record_check "$id" "skip" "$reason" 0
}

_fail_check() {
  local id="$1" reason="$2"
  echo "=== ${id}: FAIL — ${reason} ===" >&2
  _record_check "$id" "fail" "$reason" 0
  exit 1
}

_source_full_requires_bun() {
  [ "$PROFILE" = "source-full" ] && [ "$MAT_ADOPTED_SIDECAR" = "0" ]
}

REPORT="$ROOT/artifacts/phase1/phase1-verify.log"
{
  echo "phase1-verify started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "repo: $ROOT"
  echo "profile: $PROFILE"
  echo "manifest: $MANIFEST_PATH"
  echo

   echo "=== workflow artifact validation ==="
   VA_ARGS=(--repo-root "$ROOT" --require-current-plan)
   if [ "$MAT_ADOPTED_SIDECAR" = "1" ]; then
     VA_ARGS+=(--optional-handoff-artifacts)
   fi
   python3 .cursor/scripts/validate_artifacts.py "${VA_ARGS[@]}"
   echo "workflow artifacts: OK"
   _record_check workflow_artifacts pass "workflow artifacts validated" 0

  echo
  echo "=== closeout freshness and coherence ==="
  python3 scripts/validate_closeout_coherence.py --repo-root "$ROOT"
  _record_check closeout_coherence pass "closeout coherence validated" 0

  echo
  echo "=== planning artifacts validation ==="
  if [ "$MAT_ADOPTED_SIDECAR" = "1" ]; then
    _skip_check planning_artifacts "adopted sidecar omits source-only planning artifacts"
  else
    python3 scripts/validate_planning_artifacts.py --repo-root "$ROOT"
    echo "planning artifacts: OK"
    _record_check planning_artifacts pass "planning artifacts validated" 0
  fi

  echo
  echo "=== cost & context hygiene pack ==="
  # MAT source repo: strict (no .mat/cost-hygiene-adoption.json) → fail-fast. Adopted repos
  # with warn_first may set CURSOR_MAT_COST_HYGIENE_ENFORCE=strict in CI to hard-fail until
  # the team merges the suggested ignore fragments, or pass --enforce strict via a forked verify step.
  python3 scripts/validate_cost_context_hygiene_pack.py --repo-root "$ROOT" --enforce auto
  echo "cost context hygiene pack: OK"
  _record_check cost_context_hygiene pass "cost context hygiene pack validated" 0

  echo
  echo "=== internal markdown link validation ==="
  if [ "$MAT_ADOPTED_SIDECAR" = "1" ]; then
    if [ "$PROFILE" = "adopted-contract" ]; then
      python3 scripts/validate_doc_links.py --repo-root "$ROOT" --profile adopted-sidecar
      echo "doc link validation (adopted-sidecar): OK"
      _record_check doc_link_validation pass "adopted sidecar markdown links validated" 0
    else
      _skip_check doc_link_validation "adopted-operational skips doc link validator; use adopted-contract profile"
    fi
  else
    python3 scripts/validate_doc_links.py --repo-root "$ROOT" --profile source
    python3 scripts/validate_doc_links.py --repo-root "$ROOT" --profile source-archive
    echo "doc link validation: OK (source + source-archive)"
    _record_check doc_link_validation pass "internal markdown links validated (source + archive)" 0
  fi

  echo
  echo "=== cursor capability assets ==="
  if [ "$MAT_ADOPTED_SIDECAR" = "1" ]; then
    _skip_check cursor_capability_assets "adopted sidecar omits source-only cursor capability assets"
    _skip_check command_registry "adopted sidecar omits source-only command registry"
    _skip_check agent_roster "adopted sidecar omits source-only agent roster"
    _skip_check cursor_plugin_packaging "adopted sidecar omits source-only plugin packaging"
  else
    python3 scripts/validate_cursor_assets.py --strict --repo-root "$ROOT"
    echo "cursor capability assets: OK"
    _record_check cursor_capability_assets pass "cursor capability assets validated" 0
    python3 scripts/generate-command-index.py --check --repo-root "$ROOT"
    echo "command registry: OK"
    _record_check command_registry pass "mat-command-registry bijection validated" 0
    if [ -f "$ROOT/scripts/generate-agents.py" ]; then
      python3 scripts/generate-agents.py --check
      echo "agent roster: OK"
      _record_check agent_roster pass "mat-agents.yaml bijection validated" 0
    else
      _skip_check agent_roster "generate-agents.py not present"
    fi
    echo
    echo "=== cursor plugin packaging (D3a-private / N1) ==="
    python3 scripts/package-cursor-plugin.py --repo-root "$ROOT" --stage
    python3 scripts/package-cursor-plugin.py --repo-root "$ROOT" --validate-only
    python3 scripts/package-cursor-plugin.py --repo-root "$ROOT" --validate-committed
    python3 scripts/package-cursor-plugin.py --repo-root "$ROOT" --check-committed-sync
    python3 -m unittest tests.test_cursor_plugin_packaging -v
    echo "cursor plugin packaging: OK"
    _record_check cursor_plugin_packaging pass "plugin stage + packaging unittest validated" 0
  fi

  echo "=== hooks.json parse (python) ==="
  python3 - <<'PY'
import json, pathlib
p = pathlib.Path(".cursor/hooks.json")
data = json.loads(p.read_text())
assert data.get("version") == 1
assert isinstance(data.get("hooks"), dict)
print("hooks.json: OK, events:", len(data["hooks"]))
PY
  _record_check hooks_json_parse pass "hooks.json parsed" 0

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
  _record_check workflow_surfaces pass "workflow surfaces present" 0

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
  _record_check script_executability pass "required scripts are executable" 0

  if [ "$MAT_ADOPTED_SIDECAR" = "1" ] && [ -d "$ROOT/.mat/tests" ]; then
    RUN_ADOPTED_CONTRACT_TESTS=0
    if [ "${PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS:-0}" = "1" ]; then
      RUN_ADOPTED_CONTRACT_TESTS=1
    fi
    if [ "${PHASE1_VERIFY_SKIP_UNITTEST:-0}" = "1" ]; then
      if [ "${PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS:-0}" = "1" ]; then
        echo "phase1-verify: NOTE — PHASE1_VERIFY_SKIP_UNITTEST=1 wins over PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1 (deprecated skip alias)" >&2
      fi
      RUN_ADOPTED_CONTRACT_TESTS=0
      echo
      echo "=== python unittest (.mat/tests/): SKIPPED via PHASE1_VERIFY_SKIP_UNITTEST=1 (deprecated; default is adopted_operational skip) ==="
      _skip_check python_unittest "PHASE1_VERIFY_SKIP_UNITTEST=1"
    elif [ "$RUN_ADOPTED_CONTRACT_TESTS" = "0" ]; then
      echo
      echo "=== python unittest (.mat/tests/): SKIPPED [adopted_operational profile] ==="
      _skip_check python_unittest "adopted-operational profile skips .mat/tests by default"
      echo "Packaged MAT contract tests are opt-in. Set PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1 to run .mat/tests."
    fi
    if [ "$RUN_ADOPTED_CONTRACT_TESTS" = "1" ]; then
      echo
      echo "=== python unittest (.mat/tests/) [adopted_contract_tests profile] ==="
      set +e
      python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v
      ut_rc=$?
      set -e
      if [ "$ut_rc" -eq 0 ]; then
        _record_check python_unittest pass "adopted contract unittest passed" 0
      else
        _record_check python_unittest fail "adopted contract unittest failed (exit ${ut_rc})" 0
        exit "$ut_rc"
      fi
    fi
  elif [ "${PHASE1_VERIFY_SKIP_UNITTEST:-0}" = "1" ]; then
    echo
    echo "=== python unittest (tests/): SKIPPED via PHASE1_VERIFY_SKIP_UNITTEST=1 ==="
    _skip_check python_unittest "PHASE1_VERIFY_SKIP_UNITTEST=1"
  else
    echo
    echo "=== python unittest (tests/) ==="
    set +e
    python3 -m unittest discover -s tests -p 'test_*.py' -v
    ut_rc=$?
    set -e
    if [ "$ut_rc" -eq 0 ]; then
      _record_check python_unittest pass "source unittest suite passed" 0
    else
      _record_check python_unittest fail "source unittest suite failed (exit ${ut_rc})" 0
      exit "$ut_rc"
    fi
  fi

  if [ "$MAT_ADOPTED_SIDECAR" = "0" ] && [ -f "$ROOT/scripts/adoption/mat-legacy-fingerprints.py" ]; then
    echo
    echo "=== mat legacy fingerprint verify-all ==="
    python3 "$ROOT/scripts/adoption/mat-legacy-fingerprints.py" --repo "$ROOT" --verify-all
    echo "mat legacy fingerprint verify-all: OK"
    _record_check legacy_fingerprints pass "legacy fingerprints verified" 0
  else
    _skip_check legacy_fingerprints "legacy fingerprint verifier not applicable on this tree"
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
  _record_check mcp_json pass "mcp.json parsed" 0

  if [ "$MAT_ADOPTED_SIDECAR" = "0" ] && [ -f "$ROOT/scripts/mat-scope-audit.py" ]; then
    echo
    echo "=== mat scope audit self-test ==="
    python3 "$ROOT/scripts/mat-scope-audit.py" check --self-test
    echo "mat scope audit self-test: OK"
    _record_check scope_audit pass "mat-scope-audit check --self-test passed" 0
  else
    _skip_check scope_audit "scope audit self-check not applicable on this tree"
  fi

  if [ "${PHASE1_VERIFY_SKIP_BUN:-0}" = "1" ]; then
    echo
    if _source_full_requires_bun; then
      _fail_check bun_server_smoke "PHASE1_VERIFY_SKIP_BUN=1 incompatible with source-full (use source-python-only)"
    fi
    echo "=== bun observability smoke: SKIPPED via PHASE1_VERIFY_SKIP_BUN=1 ==="
    _skip_check bun_server_smoke "PHASE1_VERIFY_SKIP_BUN=1 or source-python-only profile"
  elif [ ! -d "$ROOT/apps/server" ]; then
    echo
    if _source_full_requires_bun; then
      _fail_check bun_server_smoke "apps/server missing; source-full requires Bun server smoke"
    fi
    echo "=== bun observability smoke: SKIPPED (apps/server not present; typical MAT adopted tree) ==="
    _skip_check bun_server_smoke "apps/server not present"
  elif command -v bun >/dev/null 2>&1; then
    echo
    echo "=== bun observability smoke (apps/server) ==="
    export OBSERVABILITY_DB_PATH="$ROOT/artifacts/phase1/phase1-events.sqlite"
    export PORT="${PORT:-3011}"
    cd "$ROOT/apps/server"
    bun install
    bun run src/index.ts &
    BUN_SERVER_PID=$!
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
    _cleanup_bun_server
    echo "bun smoke: OK"
    _record_check bun_server_smoke pass "bun server smoke passed" 0
  else
    echo
    if _source_full_requires_bun; then
      _fail_check bun_server_smoke "bun not installed; source-full requires Bun (use source-python-only for Bun-free)"
    fi
    echo "=== bun observability smoke: SKIPPED (bun not installed) ==="
    _skip_check bun_server_smoke "bun not installed"
  fi

  if [ "${PHASE1_VERIFY_SKIP_CLIENT:-0}" = "1" ]; then
    echo
    if _source_full_requires_bun; then
      _fail_check bun_client "PHASE1_VERIFY_SKIP_CLIENT=1 incompatible with source-full (use source-python-only)"
    fi
    echo "=== bun observability client: SKIPPED via PHASE1_VERIFY_SKIP_CLIENT=1 ==="
    _skip_check bun_client "PHASE1_VERIFY_SKIP_CLIENT=1 or source-python-only profile"
  elif [ ! -d "$ROOT/apps/client" ]; then
    echo
    if _source_full_requires_bun; then
      _fail_check bun_client "apps/client missing; source-full requires Bun client checks"
    fi
    echo "=== bun observability client: SKIPPED (apps/client not present) ==="
    _skip_check bun_client "apps/client not present"
  elif ! command -v bun >/dev/null 2>&1; then
    echo
    if _source_full_requires_bun; then
      _fail_check bun_client "bun not installed; source-full requires Bun (use source-python-only for Bun-free)"
    fi
    echo "=== bun observability client: SKIPPED (bun not installed) ==="
    _skip_check bun_client "bun not installed"
  else
    echo
    if [ "${PHASE1_VERIFY_TEST_FORCE_CLIENT_FAIL:-0}" = "1" ]; then
      _fail_check bun_client "PHASE1_VERIFY_TEST_FORCE_CLIENT_FAIL regression hook (forced failure after bun server)"
    fi
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
    _record_check bun_client pass "bun client checks passed" 0
  fi

  echo
  echo "phase1-verify finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} 2>&1 | tee "$REPORT"

echo "Wrote log: $REPORT"

if [ "${MANIFEST_ENABLED:-0}" = "1" ]; then
  if [ "${_MANIFEST_FINALIZED:-0}" != "1" ]; then
    _MANIFEST_FINALIZED=1
    _finalize_manifest 0
  fi
  echo "Wrote manifest: $MANIFEST_PATH"
else
  echo "phase1-verify: manifest recording skipped (verification_profiles.py not packaged)"
fi
