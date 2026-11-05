#!/usr/bin/env python3
"""
stop_validator.py — Cursor Hook: Stop Self-Validation

Fires on: Stop (when the agent finishes a turn)
Purpose:  Check that the agent produced expected output artifacts before
          the turn completes. If artifacts are missing, request continuation.
          Also serves as the replacement for Claude Notification hooks by
          optionally emitting a desktop notification on macOS.

Replaces: Claude Code Stop hook + Notification hook behavior
Source:   disler/claude-code-hooks-mastery .claude/commands/mat-plan-team.md
          (embedded Stop-hook validation instructions)

Exit codes:
  0 — validation passed; agent may stop (or opt-in followup_message continuation)
  1 — not used by default (fail-open per Cursor docs; do not rely on exit 1)

Opt-in (`CURSOR_MAT_STOP_VALIDATOR_FOLLOWUP=1`): when orchestrated handoffs look
incomplete, emit `{"followup_message": "…"}` on stdout and exit 0 (Cursor-documented
Stop continuation within `loop_limit`).

loop_limit: 2 — allows one retry before Cursor stops calling this hook.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from utils import runtime_messaging as runtime
from utils.context_pressure import (
    pending_compact_followup_message,
    self_compact_stop_followup_allowed,
)
from utils.mat_env_resolve import mat_env_flag

PROJECT_DIR = Path(
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
)

SCRIPT_NAME = "stop_validator.py"
PLAN_PLACEHOLDER_PHRASE = "_No active orchestration plan._"


def stop_validator_followup_enabled(*, root: Path | None = None) -> bool:
    return mat_env_flag(
        "CURSOR_MAT_STOP_VALIDATOR_FOLLOWUP",
        default=False,
        root=root or PROJECT_DIR,
    )


def desktop_notifications_enabled(*, root: Path | None = None) -> bool:
    return mat_env_flag(
        "CURSOR_DESKTOP_NOTIFICATIONS",
        default=False,
        root=root or PROJECT_DIR,
    )


def incomplete_orchestrated_handoff_message(project_dir: Path) -> str | None:
    """
    Return a follow-up message when an orchestrated session looks incomplete.

    Advisory only — matches the Phase 1 soft-warning heuristic (active plan, no results).
    """
    current_plan = project_dir / "docs" / "current-plan.md"
    if not current_plan.is_file():
        return None
    try:
        body = current_plan.read_text(encoding="utf-8")
    except OSError:
        return None
    if PLAN_PLACEHOLDER_PHRASE in body:
        return None

    build_result = project_dir / "build-result.md"
    verify_result = project_dir / "verify-result.md"
    if build_result.is_file() or verify_result.is_file():
        return None

    return (
        "MAT orchestrated handoff is incomplete: docs/current-plan.md exists but "
        "neither build-result.md nor verify-result.md was found. "
        "Complete the active slice handoff before stopping."
    )


def emit_stop_followup_message(message: str) -> None:
    """Emit Cursor Stop continuation JSON to stdout (caller must exit 0)."""
    print(json.dumps({"followup_message": message}, ensure_ascii=False))


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def check_required_artifacts(payload: dict) -> list[str]:
    """
    Check for artifacts that the current agent role should have produced.
    Returns a list of missing artifact descriptions.

    This is intentionally permissive in Phase 1 — only check for artifacts
    when we can reliably detect the agent context.
    """
    missing = []

    current_plan = PROJECT_DIR / "docs" / "current-plan.md"
    if not current_plan.exists():
        return missing  # Not an orchestrated session; no artifact requirements

    # Soft stderr warning when follow-up opt-in is off (Phase 1 permissive).
    followup_msg = incomplete_orchestrated_handoff_message(PROJECT_DIR)
    if followup_msg and not stop_validator_followup_enabled():
        print(f"[stop_validator] Warning: {followup_msg}", file=sys.stderr)

    return missing  # Phase 1: no hard artifact requirements


def send_desktop_notification(title: str, message: str) -> None:
    """
    Send a macOS desktop notification as a replacement for Claude Notification hooks.
    Only runs when CURSOR_DESKTOP_NOTIFICATIONS=true in environment.
    """
    if not desktop_notifications_enabled():
        return
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(
            ["osascript", "-e", script],
            timeout=5,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        payload = read_payload()

        # Perform artifact validation
        missing = check_required_artifacts(payload)

        followup_msg = incomplete_orchestrated_handoff_message(PROJECT_DIR)
        followup_enabled = stop_validator_followup_enabled()
        pending_compact_msg = pending_compact_followup_message(PROJECT_DIR)
        self_compact_followup = (
            self_compact_stop_followup_allowed(root=PROJECT_DIR) and pending_compact_msg
        )

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="Stop",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: checked artifact state without notifications or stop enforcement.",
                    details={
                        "missing_artifacts": missing,
                        "would_exit_code": 0,
                        "followup_enabled": followup_enabled,
                        "would_emit_followup_message": bool(
                            followup_enabled and followup_msg
                        )
                        or bool(self_compact_followup),
                        "followup_message_preview": followup_msg if followup_enabled else None,
                        "self_compact_pending_compact_preview": pending_compact_msg,
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        if followup_enabled and followup_msg:
            emit_stop_followup_message(followup_msg)
            sys.exit(0)

        if self_compact_followup and pending_compact_msg:
            emit_stop_followup_message(pending_compact_msg)
            sys.exit(0)

        if missing:
            for item in missing:
                print(f"[stop_validator] Missing: {item}", file=sys.stderr)

        try:
            followup = runtime.render_followup_message(PROJECT_DIR, payload.get("conversation_id") or payload.get("session_id") or "")
            message = followup.get("followup_message")
            if message:
                print(f"[stop_validator] follow-up: {message}", file=sys.stderr)
        except Exception:
            pass

        # Send desktop notification (Notification hook replacement)
        send_desktop_notification(
            title="Cursor Agent",
            message="Agent turn completed successfully.",
        )
    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="Stop",
                script=SCRIPT_NAME,
                kind="error",
                message=f"stop_validator failed: {exc}",
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
