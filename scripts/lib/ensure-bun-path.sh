#!/usr/bin/env bash
# Prepend the default Bun install directory when `bun` is not on PATH.
# Interactive shells usually load ~/.zshrc; Cursor agent terminals, CI-like shells,
# and automation often do not — this keeps `bun run dev` and phase1-verify reliable.
#
# shellcheck shell=bash
# Source from other scripts: . "$ROOT/scripts/lib/ensure-bun-path.sh"

if ! command -v bun >/dev/null 2>&1; then
  _bun_home="${BUN_INSTALL:-$HOME/.bun}"
  for _d in "${_bun_home}/bin" "${HOME}/.bun/bin"; do
    if [ -x "${_d}/bun" ]; then
      export PATH="${_d}:${PATH}"
      break
    fi
  done
  unset _d _bun_home
fi
