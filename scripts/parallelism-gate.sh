#!/usr/bin/env bash
# Parallelism gate helper: create two git worktrees and run bootstrap_worktree.sh in each.
# Requires: git, a clean working tree (commit any changes first).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $ROOT" >&2
  exit 1
fi

WT_BASE="${PARALLELISM_WT_BASE:-$ROOT/../.phase1-worktrees}"
mkdir -p "$WT_BASE"

BR1="phase1-parallel-a"
BR2="phase1-parallel-b"
P1="$WT_BASE/$BR1"
P2="$WT_BASE/$BR2"

cleanup() {
  git worktree remove -f "$P1" 2>/dev/null || true
  git worktree remove -f "$P2" 2>/dev/null || true
  git branch -D "$BR1" 2>/dev/null || true
  git branch -D "$BR2" 2>/dev/null || true
}

if [ "${PARALLELISM_CLEAN:-1}" = "1" ]; then
  trap cleanup EXIT
fi

git worktree add "$P1" -b "$BR1"
git worktree add "$P2" -b "$BR2"

(
  cd "$P1"
  bash .cursor/hooks/bootstrap_worktree.sh builder-agent
)

(
  cd "$P2"
  bash .cursor/hooks/bootstrap_worktree.sh verifier-agent
)

echo "parallelism gate: OK (bootstrap ran in two worktrees)"
echo "worktrees: $P1 , $P2"
