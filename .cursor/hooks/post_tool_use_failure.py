#!/usr/bin/env python3
"""Cursor Hook: PostToolUseFailure — Tool Failure Logger

Fires on: PostToolUse (failure case)
Purpose:  Log tool failure events (tool_name, error_message, failure_type,
          duration) to the session log directory.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Always exits 0 to avoid blocking the agent.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from session_id import extract_session_id
from utils.constants import ensure_session_log_dir

PROJECT_DIR = (
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
)
SCRIPT_NAME = "post_tool_use_failure.py"


def read_stdin_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        input_data = read_stdin_payload()
        tool_name = input_data.get("tool_name") or input_data.get("tool") or ""

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="PostToolUseFailure",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: inspected failed tool payload without writing session logs.",
                    details={
                        "session_id": extract_session_id(input_data),
                        "tool_name": tool_name,
                        "project_dir": PROJECT_DIR,
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        session_id = extract_session_id(input_data)

        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "post_tool_use_failure.json"

        log_data: list = []
        if log_path.exists():
            try:
                log_data = json.loads(log_path.read_text())
            except (json.JSONDecodeError, ValueError):
                log_data = []

        log_data.append(input_data)
        log_path.write_text(json.dumps(log_data, indent=2))

    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="PostToolUseFailure",
                script=SCRIPT_NAME,
                kind="error",
                message=f"post_tool_use_failure failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
