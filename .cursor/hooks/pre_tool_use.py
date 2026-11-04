#!/usr/bin/env python3
"""
pre_tool_use.py — Cursor Hook: PreToolUse Validation

Fires on: PreToolUse (before every tool execution)
Purpose:  Validate or block tool calls before they execute.
          In Phase 1, this is a permissive pass-through with optional logging.
          Extend with blocking logic for security-sensitive use cases.

False-positive audit (repo): `is_blocked_tool` is empty by default — no accidental
blocks. When adding rules, use `resolve_tool_name()` for stdin payloads so
`tool_name` vs `tool` aliases match tests in `tests/test_phase1_hooks.py`.

Exit codes:
  0 — allow the tool call to proceed
  1 — block the tool call (only effective when failClosed: true in hooks.json)

Note: hooks.json currently uses failClosed: false, so exit 1 will not block
the tool in Phase 1. Set failClosed: true to enable blocking behavior.
"""

import json
import os
import sys
from pathlib import Path

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from utils.context_pressure import evaluate_pre_tool_use, pre_tool_use_dry_run_details

PROJECT_DIR = Path(
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
).resolve()

LOG_FILE = os.path.join(PROJECT_DIR, ".cursor", "hooks", "pre_tool_use.log")
SCRIPT_NAME = "pre_tool_use.py"


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def resolve_tool_name(payload: dict) -> str:
    """
    Cursor stdin may use `tool_name` or `tool`. Prefer a non-empty string from either.
    Used by blocking rules so names stay consistent with tests.
    """
    for key in ("tool_name", "tool"):
        raw = payload.get(key)
        if isinstance(raw, str):
            stripped = raw.strip()
            if stripped:
                return stripped
        elif raw is not None and not isinstance(raw, (dict, list)):
            s = str(raw).strip()
            if s:
                return s
    return ""


def is_blocked_tool(tool_name: str) -> bool:
    """
    Define tool blocking rules here for Phase 2+.
    Currently empty — extend as needed.

    Examples (not active):
      - Block shell commands containing 'rm -rf'
      - Block writes to credential files
    """
    blocked = []  # e.g. ["delete_file", "run_terminal_command"]
    return tool_name in blocked


def log_event(payload: dict) -> None:
    """Append a log line for debugging. Remove or rotate in production."""
    try:
        tool = resolve_tool_name(payload) or "unknown"
        line = f"PreToolUse | tool={tool}\n"
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except OSError:
        pass


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        payload = read_payload()
        tool_name = resolve_tool_name(payload)
        blocked = is_blocked_tool(tool_name)

        compact_details = pre_tool_use_dry_run_details(PROJECT_DIR, payload)

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="PreToolUse",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: evaluated tool decision without logging or blocking.",
                    details={
                        "tool_name": tool_name,
                        "would_block": blocked,
                        "would_exit_code": 1 if blocked else 0,
                        **compact_details,
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        log_event(payload)

        if blocked:
            print(f"[pre_tool_use] Blocked: {tool_name}", file=sys.stderr)
            sys.exit(1)

        compact_response = evaluate_pre_tool_use(PROJECT_DIR, payload)
        if compact_response:
            print(json.dumps(compact_response, ensure_ascii=False))
            sys.exit(0)
    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="PreToolUse",
                script=SCRIPT_NAME,
                kind="error",
                message=f"pre_tool_use failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
