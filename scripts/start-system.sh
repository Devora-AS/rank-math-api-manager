#!/usr/bin/env bash
# Start observability Bun API (apps/server) and Vite dashboard (apps/client).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/ensure-bun-path.sh
. "$SCRIPT_DIR/lib/ensure-bun-path.sh"
# shellcheck source=lib/pick-free-port.sh
. "$SCRIPT_DIR/lib/pick-free-port.sh"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if ! command -v bun >/dev/null 2>&1; then
  echo "bun is not installed or not on PATH." >&2
  echo "Install Bun: https://bun.sh/docs/installation" >&2
  exit 1
fi

if [ ! -f "$ROOT/apps/server/package.json" ] || [ ! -f "$ROOT/apps/client/package.json" ]; then
  echo "Missing apps/server or apps/client package.json" >&2
  exit 1
fi

DESIRED_API_PORT="${OBSERVABILITY_PORT:-${PORT:-3001}}"
DESIRED_CLIENT_PORT="${OBSERVABILITY_CLIENT_PORT:-5173}"

SERVER_PID=""
CLIENT_PID=""

cleanup() {
  if [ -n "${CLIENT_PID:-}" ]; then kill "$CLIENT_PID" 2>/dev/null || true; fi
  if [ -n "${SERVER_PID:-}" ]; then kill "$SERVER_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

if ! API_PORT="$(pick_free_port "$DESIRED_API_PORT")"; then
  echo "Could not find a free TCP port for the observability API starting at ${DESIRED_API_PORT}." >&2
  exit 1
fi
if [ "$API_PORT" != "$DESIRED_API_PORT" ]; then
  echo "Note: port ${DESIRED_API_PORT} was in use; using ${API_PORT} for the observability API." >&2
fi

if ! CLIENT_PORT="$(pick_free_port "$DESIRED_CLIENT_PORT")"; then
  echo "Could not find a free TCP port for the dashboard starting at ${DESIRED_CLIENT_PORT}." >&2
  exit 1
fi
if [ "$CLIENT_PORT" != "$DESIRED_CLIENT_PORT" ]; then
  echo "Note: port ${DESIRED_CLIENT_PORT} was in use; using ${CLIENT_PORT} for the dashboard." >&2
fi

export PORT="$API_PORT"
export OBSERVABILITY_PORT="$API_PORT"
export OBSERVABILITY_CLIENT_PORT="$CLIENT_PORT"

if [ -z "${OBSERVABILITY_CORS_ORIGINS:-}" ]; then
  export OBSERVABILITY_CORS_ORIGINS="http://127.0.0.1:${CLIENT_PORT},http://localhost:${CLIENT_PORT},http://127.0.0.1:${API_PORT},http://localhost:${API_PORT}"
fi

cd "$ROOT/apps/server"
bun install
bun run dev &
SERVER_PID=$!

sleep 0.3
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
  echo "Observability server exited immediately (is port ${API_PORT} already in use? Stop the other process or set PORT / OBSERVABILITY_PORT.)" >&2
  exit 1
fi

_ok=0
for _ in $(seq 1 100); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1; then
    _ok=1
    break
  fi
  sleep 0.2
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "Observability server died while starting (check port ${API_PORT} and logs above)." >&2
    exit 1
  fi
done
if [ "$_ok" != 1 ]; then
  echo "Observability server did not become ready on :${API_PORT}" >&2
  exit 1
fi
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
  echo "Observability server is not running after health check." >&2
  exit 1
fi

cd "$ROOT/apps/client"
export OBSERVABILITY_API_ORIGIN="http://127.0.0.1:${API_PORT}"
bun install
bun run dev &
CLIENT_PID=$!

sleep 0.5
if ! kill -0 "$CLIENT_PID" 2>/dev/null; then
  echo "Dashboard (Vite) exited immediately (see errors above)." >&2
  exit 1
fi

_ok_client=0
for _ in $(seq 1 80); do
  if curl -fsS "http://127.0.0.1:${CLIENT_PORT}/" >/dev/null 2>&1; then
    _ok_client=1
    break
  fi
  sleep 0.15
  if ! kill -0 "$CLIENT_PID" 2>/dev/null; then
    echo "Dashboard (Vite) died while starting." >&2
    exit 1
  fi
done
if [ "$_ok_client" != 1 ]; then
  echo "Dashboard did not respond on http://127.0.0.1:${CLIENT_PORT}/ in time." >&2
  exit 1
fi

echo ""
echo "Observability API: http://127.0.0.1:${API_PORT} (POST /events, GET /events, GET /health)"
echo "Dashboard (Vite):  http://127.0.0.1:${CLIENT_PORT}"
echo "Press Ctrl+C to stop both."
echo ""

wait
