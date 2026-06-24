#!/usr/bin/env bash
# Check health and collisions across local git worktrees.
set -euo pipefail

STRICT=0
if [ "${1:-}" = "--strict" ]; then
  STRICT=1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not inside a git repository." >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

declare -a WORKTREE_PATHS=()
declare -a WORKTREE_BRANCHES=()

current_path=""
while IFS= read -r line; do
  case "$line" in
    worktree\ *)
      current_path="${line#worktree }"
      WORKTREE_PATHS+=("$current_path")
      WORKTREE_BRANCHES+=("detached")
      ;;
    branch\ refs/heads/*)
      if [ ${#WORKTREE_BRANCHES[@]} -gt 0 ]; then
        WORKTREE_BRANCHES[$((${#WORKTREE_BRANCHES[@]} - 1))]="${line#branch refs/heads/}"
      fi
      ;;
  esac
done < <(git worktree list --porcelain)

if [ ${#WORKTREE_PATHS[@]} -eq 0 ]; then
  echo "No worktrees found."
  exit 1
fi

declare -a API_PORTS=()
declare -a API_PORT_OWNERS=()
declare -a CLIENT_PORTS=()
declare -a CLIENT_PORT_OWNERS=()
ISSUES=0

echo "Worktree health report"
echo "repo: $ROOT"
echo ""

for idx in "${!WORKTREE_PATHS[@]}"; do
  path="${WORKTREE_PATHS[$idx]}"
  branch="${WORKTREE_BRANCHES[$idx]}"
  status="OK"
  notes=()

  if [ ! -d "$path" ]; then
    status="STALE"
    notes+=("path missing on disk")
    ISSUES=$((ISSUES + 1))
  else
    if [ ! -f "$path/.env" ]; then
      notes+=(".env missing")
    fi
    if [ ! -f "$path/.cursor/worktree/bootstrapped_at" ]; then
      if [ "$path" = "$ROOT" ]; then
        notes+=("bootstrap marker missing (main worktree, informational)")
      else
        status="WARN"
        notes+=("bootstrap marker missing")
        ISSUES=$((ISSUES + 1))
      fi
    fi

    runtime_env="$path/.cursor/worktree/runtime.env"
    api_port=""
    client_port=""
    if [ -f "$runtime_env" ]; then
      api_port="$(awk -F= '/^OBSERVABILITY_PORT=/{print $2}' "$runtime_env" | tail -n1)"
      client_port="$(awk -F= '/^OBSERVABILITY_CLIENT_PORT=/{print $2}' "$runtime_env" | tail -n1)"
    fi

    if [ -n "$api_port" ]; then
      owner=""
      j=0
      while [ "$j" -lt "${#API_PORTS[@]}" ]; do
        if [ "${API_PORTS[$j]}" = "$api_port" ]; then
          owner="${API_PORT_OWNERS[$j]}"
          break
        fi
        j=$((j + 1))
      done
      if [ -n "$owner" ]; then
        status="WARN"
        notes+=("api port collision with $owner")
        ISSUES=$((ISSUES + 1))
      else
        API_PORTS+=("$api_port")
        API_PORT_OWNERS+=("$path")
      fi
    fi

    if [ -n "$client_port" ]; then
      owner=""
      j=0
      while [ "$j" -lt "${#CLIENT_PORTS[@]}" ]; do
        if [ "${CLIENT_PORTS[$j]}" = "$client_port" ]; then
          owner="${CLIENT_PORT_OWNERS[$j]}"
          break
        fi
        j=$((j + 1))
      done
      if [ -n "$owner" ]; then
        status="WARN"
        notes+=("client port collision with $owner")
        ISSUES=$((ISSUES + 1))
      else
        CLIENT_PORTS+=("$client_port")
        CLIENT_PORT_OWNERS+=("$path")
      fi
    fi
  fi

  echo "- branch: $branch"
  echo "  path: $path"
  echo "  status: $status"
  if [ ${#notes[@]} -gt 0 ]; then
    echo "  notes: ${notes[*]}"
  fi
done

echo ""
if [ "$ISSUES" -eq 0 ]; then
  echo "Result: PASS (no collisions or stale worktrees detected)."
  exit 0
fi

echo "Result: WARN (${ISSUES} issue(s) detected)."
if [ "$STRICT" -eq 1 ]; then
  exit 1
fi
exit 0
