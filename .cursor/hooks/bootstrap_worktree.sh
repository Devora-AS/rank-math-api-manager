#!/usr/bin/env bash
# bootstrap_worktree.sh — Worktree Environment Bootstrap
#
# Stage 5 — Parallel Runtime & Worktrees (E10 modes)
# Purpose: Initialize a Git worktree checkout after it already exists on disk.
#          Modes keep metadata setup cheap and make package/network work explicit.
#
# Cursor may create managed worktrees (Agents Window, /worktree, /best-of-n) or
# operators may use manual `git worktree add` / `/mat-wt-create`. This script is
# the MAT parity layer: same markers and runtime.env hints on every path.
#
# Called by: .cursor/worktrees.json (bootstrap / setup-worktree* keys)
# Also invoked manually for: local testing and worktree reset
#
# Usage:
#   .cursor/hooks/bootstrap_worktree.sh [OPTIONS] [worktree-name]
#
# Modes (exactly one; default --metadata-only):
#   --metadata-only   Write .cursor/worktree markers + runtime.env only.
#                     No .env/.mat.env copy, no package managers, no network.
#   --install         Print planned package commands, then execute installs.
#                     Env copy only with --copy-env.
#   --check           Validate markers / runtime.env; no installs, no env copy.
#
# Flags:
#   --copy-env        With --install: copy .env / .mat.env from project root when missing.
#   -h, --help        Show help and exit 0.
#
# Exit codes:
#   0 — success (or --check healthy)
#   1 — failure / --check unhealthy
#
# Note: Tmux is NOT used. Isolation is via git worktrees (Cursor-managed or
#       manual) plus this bootstrap — not implicit per-agent provisioning.

set -euo pipefail

MODE=""
COPY_ENV=0
WORKTREE_NAME=""
SHOW_HELP=0

usage() {
  cat <<'EOF'
Usage: bootstrap_worktree.sh [OPTIONS] [worktree-name]

Modes (default: --metadata-only):
  --metadata-only   Markers + runtime.env only (no package/network/env copy)
  --install         Print plan, then install deps (add --copy-env to copy secrets)
  --check           Validate existing markers; no mutations beyond lock

Flags:
  --copy-env        Allow copying .env / .mat.env when missing (--install only)
  -h, --help        Show this help

Examples:
  bootstrap_worktree.sh my-feature
  bootstrap_worktree.sh --metadata-only my-feature
  bootstrap_worktree.sh --install --copy-env my-feature
  bootstrap_worktree.sh --check my-feature
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --metadata-only)
      if [ -n "$MODE" ] && [ "$MODE" != "metadata-only" ]; then
        echo "[bootstrap_worktree] ERROR: conflicting modes" >&2
        exit 1
      fi
      MODE="metadata-only"
      shift
      ;;
    --install)
      if [ -n "$MODE" ] && [ "$MODE" != "install" ]; then
        echo "[bootstrap_worktree] ERROR: conflicting modes" >&2
        exit 1
      fi
      MODE="install"
      shift
      ;;
    --check)
      if [ -n "$MODE" ] && [ "$MODE" != "check" ]; then
        echo "[bootstrap_worktree] ERROR: conflicting modes" >&2
        exit 1
      fi
      MODE="check"
      shift
      ;;
    --copy-env)
      COPY_ENV=1
      shift
      ;;
    -h|--help)
      SHOW_HELP=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "[bootstrap_worktree] ERROR: unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [ -n "$WORKTREE_NAME" ]; then
        echo "[bootstrap_worktree] ERROR: unexpected argument: $1" >&2
        exit 1
      fi
      WORKTREE_NAME="$1"
      shift
      ;;
  esac
done

if [ "$SHOW_HELP" -eq 1 ]; then
  usage
  exit 0
fi

if [ -z "$MODE" ]; then
  MODE="metadata-only"
fi

if [ "$COPY_ENV" -eq 1 ] && [ "$MODE" != "install" ]; then
  echo "[bootstrap_worktree] ERROR: --copy-env requires --install" >&2
  exit 1
fi

WORKTREE_NAME="${WORKTREE_NAME:-unnamed}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PROJECT_DIR="${CURSOR_PROJECT_DIR:-$REPO_ROOT}"
ENV_SOURCE="${PROJECT_DIR}/.env"
ENV_TARGET=".env"
MAT_ENV_SOURCE="${PROJECT_DIR}/.mat.env"
MAT_ENV_TARGET=".mat.env"
LOCK_DIR=".cursor/worktree/.bootstrap-lock"
RUNTIME_ENV=".cursor/worktree/runtime.env"
MARKER_DIR=".cursor/worktree"

# shellcheck source=../../scripts/lib/ensure-bun-path.sh
. "$REPO_ROOT/scripts/lib/ensure-bun-path.sh"
# shellcheck source=../../scripts/lib/pick-free-port.sh
. "$REPO_ROOT/scripts/lib/pick-free-port.sh"

log() {
  echo "[bootstrap_worktree] [$WORKTREE_NAME] $*"
}

error() {
  echo "[bootstrap_worktree] [$WORKTREE_NAME] ERROR: $*" >&2
}

cleanup_lock() {
  rmdir "$LOCK_DIR" >/dev/null 2>&1 || true
}

detect_cursor_managed() {
  if [ -n "${ROOT_WORKTREE_PATH:-}" ]; then
    echo "env:ROOT_WORKTREE_PATH"
    return 0
  fi
  if [ -n "${CURSOR_WORKTREE:-}" ]; then
    echo "env:CURSOR_WORKTREE"
    return 0
  fi
  case "$REPO_ROOT" in
    */.cursor/worktrees/*|*/.cursor/worktrees)
      echo "path:.cursor/worktrees"
      return 0
      ;;
  esac
  echo ""
  return 1
}

write_runtime_env() {
  log "Resolving runtime port hints..."
  seed="$(printf "%s" "$WORKTREE_NAME" | cksum | awk '{print $1}')"
  offset=$((seed % 200))
  desired_api_port=$((3001 + offset))
  desired_client_port=$((5173 + offset))

  api_port="$(pick_free_port "$desired_api_port" "$((desired_api_port + 100))" || true)"
  client_port="$(pick_free_port "$desired_client_port" "$((desired_client_port + 100))" || true)"
  if [ -n "$api_port" ] && [ -n "$client_port" ]; then
    cat > "$RUNTIME_ENV" <<EOF
OBSERVABILITY_PORT=$api_port
OBSERVABILITY_CLIENT_PORT=$client_port
EOF
    log "  Runtime hints written to $RUNTIME_ENV (api=$api_port, client=$client_port)."
  else
    log "  Could not compute free runtime ports; continuing without runtime hints."
  fi
}

write_markers() {
  log "Writing worktree marker..."
  echo "$WORKTREE_NAME" > "$MARKER_DIR/name"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$MARKER_DIR/bootstrapped_at"
  echo "$REPO_ROOT" > "$MARKER_DIR/project_dir"
  managed_kind="$(detect_cursor_managed || true)"
  if [ -n "$managed_kind" ]; then
    echo "cursor-managed:$managed_kind" > "$MARKER_DIR/origin"
    log "  Detected Cursor-managed worktree ($managed_kind)."
  else
    echo "manual" > "$MARKER_DIR/origin"
    log "  Manual / non-managed worktree path."
  fi
  log "  Marker written to $MARKER_DIR/"
}

copy_env_files() {
  log "Copying environment files (--copy-env)..."
  if [ -f "$ENV_SOURCE" ] && [ ! -f "$ENV_TARGET" ]; then
    # Avoid no-op when source and target resolve to the same path.
    if [ "$(cd "$(dirname "$ENV_SOURCE")" && pwd)/$(basename "$ENV_SOURCE")" != \
         "$(pwd)/$ENV_TARGET" ]; then
      cp "$ENV_SOURCE" "$ENV_TARGET"
      log "  Copied .env from project root."
    else
      log "  .env source and target are the same path — skipping copy."
    fi
  elif [ -f "$ENV_TARGET" ]; then
    log "  .env already exists — skipping copy."
  else
    log "  No .env found at $ENV_SOURCE — skipping."
  fi

  if [ -f "$MAT_ENV_SOURCE" ] && [ ! -f "$MAT_ENV_TARGET" ]; then
    if [ "$(cd "$(dirname "$MAT_ENV_SOURCE")" && pwd)/$(basename "$MAT_ENV_SOURCE")" != \
         "$(pwd)/$MAT_ENV_TARGET" ]; then
      cp "$MAT_ENV_SOURCE" "$MAT_ENV_TARGET"
      log "  Copied .mat.env from project root."
    else
      log "  .mat.env source and target are the same path — skipping copy."
    fi
  elif [ -f "$MAT_ENV_TARGET" ]; then
    log "  .mat.env already exists — skipping copy."
  else
    log "  No .mat.env found at $MAT_ENV_SOURCE — skipping."
  fi
}

plan_install_commands() {
  PLANNED_CMDS=()
  if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    if command -v uv &>/dev/null; then
      PLANNED_CMDS+=("uv sync")
    elif command -v pip &>/dev/null && [ -f "requirements.txt" ]; then
      PLANNED_CMDS+=("pip install -r requirements.txt")
    fi
  fi
  if [ -f "package.json" ]; then
    if command -v bun &>/dev/null; then
      PLANNED_CMDS+=("bun install")
    elif command -v npm &>/dev/null; then
      PLANNED_CMDS+=("npm install")
    fi
  fi
  for app_rel in apps/server apps/client; do
    if [ -f "$app_rel/package.json" ]; then
      if command -v bun &>/dev/null; then
        PLANNED_CMDS+=("(cd $app_rel && bun install)")
      elif command -v npm &>/dev/null; then
        PLANNED_CMDS+=("(cd $app_rel && npm install)")
      fi
    fi
  done
}

run_install_commands() {
  log "Installing dependencies..."
  if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    if command -v uv &>/dev/null; then
      log "  Running: uv sync"
      uv sync || { error "uv sync failed"; exit 1; }
    elif command -v pip &>/dev/null; then
      if [ -f "requirements.txt" ]; then
        log "  Running: pip install -r requirements.txt"
        pip install -r requirements.txt || { error "pip install failed"; exit 1; }
      fi
    else
      log "  No Python package manager found — skipping Python dep install."
    fi
  fi

  if [ -f "package.json" ]; then
    if command -v bun &>/dev/null; then
      log "  Running: bun install"
      bun install || { error "bun install failed"; exit 1; }
    elif command -v npm &>/dev/null; then
      log "  Running: npm install"
      npm install || { error "npm install failed"; exit 1; }
    else
      log "  No Node package manager found — skipping JS dep install."
    fi
  fi

  for app_rel in apps/server apps/client; do
    if [ -f "$app_rel/package.json" ]; then
      if command -v bun &>/dev/null; then
        log "  Running: (cd $app_rel && bun install)"
        (cd "$app_rel" && bun install) || { error "bun install failed in $app_rel"; exit 1; }
      elif command -v npm &>/dev/null; then
        log "  Running: (cd $app_rel && npm install)"
        (cd "$app_rel" && npm install) || { error "npm install failed in $app_rel"; exit 1; }
      else
        log "  No Node package manager found — skipping JS dep install in $app_rel."
      fi
    fi
  done
}

validate_env_required() {
  if [ -f "$ENV_TARGET" ]; then
    # shellcheck disable=SC1090
    set -a; source "$ENV_TARGET"; set +a
  fi

  REQUIRED_VARS=()
  MISSING_VARS=()
  if [ ${#REQUIRED_VARS[@]} -gt 0 ]; then
    for var in "${REQUIRED_VARS[@]}"; do
      if [ -z "${!var:-}" ]; then
        MISSING_VARS+=("$var")
      fi
    done
  fi

  if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    error "Missing required environment variables: ${MISSING_VARS[*]}"
    error "Copy .env.sample to .env and fill in the required values."
    return 1
  fi
  return 0
}

emit_session_start_best_effort() {
  log "Emitting session-start event (best-effort)..."
  if command -v python3 &>/dev/null && [ -f ".cursor/hooks/session_start.py" ]; then
    echo '{"session_id":"'$WORKTREE_NAME'"}' | \
      CURSOR_HOOK_EVENT=SessionStart python3 .cursor/hooks/session_start.py || true
  fi
}

run_check() {
  local ok=1
  log "Mode: --check (read-only validation)"
  managed_kind="$(detect_cursor_managed || true)"
  if [ -n "$managed_kind" ]; then
    log "  Cursor-managed detection: $managed_kind"
  else
    log "  Cursor-managed detection: none (manual path)"
  fi

  if [ ! -f "$MARKER_DIR/name" ]; then
    error "Missing marker: $MARKER_DIR/name — run --metadata-only or --install first."
    ok=0
  else
    log "  Marker name: $(cat "$MARKER_DIR/name")"
  fi

  if [ ! -f "$RUNTIME_ENV" ]; then
    error "Missing $RUNTIME_ENV"
    ok=0
  else
    if ! grep -q '^OBSERVABILITY_PORT=' "$RUNTIME_ENV"; then
      error "$RUNTIME_ENV missing OBSERVABILITY_PORT"
      ok=0
    fi
    if ! grep -q '^OBSERVABILITY_CLIENT_PORT=' "$RUNTIME_ENV"; then
      error "$RUNTIME_ENV missing OBSERVABILITY_CLIENT_PORT"
      ok=0
    fi
    if [ "$ok" -eq 1 ]; then
      log "  runtime.env looks healthy"
    fi
  fi

  if ! validate_env_required; then
    ok=0
  fi

  if [ "$ok" -eq 1 ]; then
    log "Check PASS"
    return 0
  fi
  error "Check FAIL"
  return 1
}

cd "$REPO_ROOT"
mkdir -p "$MARKER_DIR"

# Avoid racey concurrent bootstrap runs in the same worktree.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  error "Another bootstrap run is active (lock: $LOCK_DIR)."
  exit 1
fi
trap cleanup_lock EXIT

log "Mode: --$MODE"

case "$MODE" in
  check)
    run_check
    exit $?
    ;;
  metadata-only)
    log "Mode: --metadata-only — Skipping dependency installs (zero package/network calls; no env copy)."
    log "metadata-only: skipping env copy and package installs (zero package/network calls)."
    write_runtime_env
    write_markers
    log "Bootstrap complete (metadata-only) for worktree: $WORKTREE_NAME"
    exit 0
    ;;
  install)
    if [ "$COPY_ENV" -eq 1 ]; then
      copy_env_files
    else
      log "Skipping env copy (pass --copy-env to copy .env / .mat.env when missing)."
    fi
    write_runtime_env
    plan_install_commands
    log "Planned install commands:"
    if [ ${#PLANNED_CMDS[@]} -eq 0 ]; then
      log "  (none — no matching manifests or package managers)"
    else
      for cmd in "${PLANNED_CMDS[@]}"; do
        log "  PLAN: $cmd"
      done
    fi
    run_install_commands
    validate_env_required || exit 1
    emit_session_start_best_effort
    write_markers
    log "Bootstrap complete (install) for worktree: $WORKTREE_NAME"
    exit 0
    ;;
  *)
    error "Unknown mode: $MODE"
    exit 1
    ;;
esac
