#!/usr/bin/env bash
# Lightweight local setup helper for operators.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/ensure-bun-path.sh
. "$ROOT/scripts/lib/ensure-bun-path.sh"
cd "$ROOT"

echo "setup-dev: repo=$ROOT"

if [ ! -f ".env" ] && [ -f ".env.sample" ]; then
  cp ".env.sample" ".env"
  echo "Created .env from .env.sample"
else
  echo ".env already present (or .env.sample missing) — skipped copy"
fi

if command -v python3 >/dev/null 2>&1; then
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Created Python virtualenv at .venv"
  else
    echo ".venv already exists — skipped"
  fi
else
  echo "python3 not found — skipped virtualenv setup"
fi

if command -v bun >/dev/null 2>&1; then
  (
    cd apps/server
    bun install
  )
  (
    cd apps/client
    bun install
  )
  echo "Installed Bun dependencies for apps/server and apps/client"
else
  echo "bun not found — skipped Bun installs"
fi

echo "Next steps:"
echo "  1) source .venv/bin/activate  # if using Python venv"
echo "  2) bash scripts/doctor.sh"
echo "  3) bash scripts/start-system.sh"
