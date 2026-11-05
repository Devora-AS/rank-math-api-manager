#!/usr/bin/env python3
"""
session_start.py — Cursor Hook: SessionStart Environment Validation

Fires on: SessionStart (at the beginning of each new agent session)
Purpose:  Validate the environment before the agent starts working.
          This is the Cursor-native replacement for Claude's Setup frontmatter.

Replaces: Claude Code agent Setup frontmatter behavior
Source:   disler/claude-code-hooks-mastery (Setup behavior implied by agent defs)

Responsibilities:
  1. Verify required environment variables are set
  2. Emit a session-init event to the observability server
  3. Log session start to a local file for debugging

Exit codes:
  0 — environment is valid; agent may proceed
  1 — environment is invalid (only blocks if failClosed: true)

Note: failClosed: false in Phase 1 — exit 1 will not block the agent.
      Set failClosed: true in hooks.json to enforce hard environment checks.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from payload_capture import (
    extract_project_dir,
    maybe_capture_payload,
    read_payload_from_stdin,
)
from session_id import extract_session_id
from utils.context_pressure import emit_session_start_context, session_start_additional_context
from utils.mat_env_resolve import mat_env_get

PROJECT_DIR = Path(
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
)


def observability_server_url() -> str:
    return (
        mat_env_get(
            "OBSERVABILITY_SERVER_URL",
            default="http://localhost:3001/events",
            root=PROJECT_DIR,
        )
        or "http://localhost:3001/events"
    )

REQUIRED_ENV_VARS: list[str] = [
    # Add required env var names here as the project evolves.
    # Example: "OPENAI_API_KEY", "DATABASE_URL"
    # Leave empty in Phase 1 to avoid blocking agents on missing vars.
]

OPTIONAL_ENV_VARS: list[str] = [
    "OBSERVABILITY_SERVER_URL",
    "CURSOR_DESKTOP_NOTIFICATIONS",
]
SCRIPT_NAME = "session_start.py"


def check_env_vars() -> list[str]:
    """Return list of missing required env vars."""
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing.append(var)
    return missing


def emit_session_start_event(payload: dict, session_id: str, env_status: str) -> None:
    """POST a session-start event to the observability server."""
    event = {
        "event_type": "SessionStart",
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(extract_project_dir(payload, PROJECT_DIR)),
        "tool_name": "",
        "tool_input": "",
        "tool_output": "",
        "summary": f"Session started. Env status: {env_status}",
        "raw": json.dumps({**payload, "env_status": env_status}),
    }
    payload = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        observability_server_url(),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            _ = resp.read()
    except (urllib.error.URLError, OSError):
        pass  # Observability server not running — fail silently


def log_session_start(session_id: str, missing_vars: list[str]) -> None:
    """Write a log line to .cursor/hooks/session_start.log."""
    log_file = PROJECT_DIR / ".cursor" / "hooks" / "session_start.log"
    try:
        os.makedirs(log_file.parent, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        status = "OK" if not missing_vars else f"MISSING: {', '.join(missing_vars)}"
        with open(log_file, "a") as f:
            f.write(f"{now} | session={session_id} | env={status}\n")
    except OSError:
        pass


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        payload, _ = read_payload_from_stdin()
        session_id = extract_session_id(payload)
        missing_vars = check_env_vars()
        env_status = "OK" if not missing_vars else f"MISSING: {', '.join(missing_vars)}"

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="SessionStart",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: checked environment without capture, logging, or POST.",
                    details={
                        "session_id": session_id,
                        "missing_vars": missing_vars,
                        "env_status": env_status,
                        "project_dir": str(extract_project_dir(payload, PROJECT_DIR)),
                        "would_post_url": observability_server_url(),
                        "would_exit_code": 1 if missing_vars else 0,
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        maybe_capture_payload(payload, "sessionStart", PROJECT_DIR)
        log_session_start(session_id, missing_vars)
        emit_session_start_event(payload, session_id, env_status)

        handoff_context = session_start_additional_context(PROJECT_DIR)
        if handoff_context:
            emit_session_start_context(handoff_context)

        if missing_vars:
            for var in missing_vars:
                print(f"[session_start] Missing required env var: {var}", file=sys.stderr)
            # Exit 1 to flag the issue — will block if failClosed: true
            sys.exit(1)
    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="SessionStart",
                script=SCRIPT_NAME,
                kind="error",
                message=f"session_start failed: {exc}",
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
