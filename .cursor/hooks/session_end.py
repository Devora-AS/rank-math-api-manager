#!/usr/bin/env python3
"""Cursor Hook: SessionEnd — Session End Handler

Fires on: SessionEnd (or equivalent Cursor lifecycle event)
Purpose:  Log session end, save statistics, and optionally announce via TTS.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Always exits 0 to avoid blocking the agent.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from payload_capture import maybe_capture_payload, read_payload_from_stdin
from utils.constants import PROJECT_DIR, ensure_session_log_dir
from utils.mat_env_resolve import mat_env_flag
from session_id import extract_session_id

SCRIPT_NAME = "session_end.py"


def session_save_stats_enabled(root: Path) -> bool:
    return mat_env_flag("CURSOR_SAVE_SESSION_STATS", default=True, root=root)


def tts_announce_enabled(root: Path) -> bool:
    return mat_env_flag("CURSOR_TTS_ANNOUNCE", default=False, root=root)


def log_session_end(input_data: dict, reason: str) -> None:
    """Log session end event to session log directory."""
    try:
        session_id = extract_session_id(input_data)
        log_dir = ensure_session_log_dir(session_id)
        log_file = log_dir / "session_end.json"

        log_data: list = []
        if log_file.exists():
            try:
                log_data = json.loads(log_file.read_text())
            except (json.JSONDecodeError, ValueError):
                log_data = []

        log_data.append({
            "session_id": session_id,
            "hook_event_name": input_data.get("hook_event_name", "SessionEnd"),
            "reason": reason,
            "logged_at": datetime.now().isoformat(),
        })

        log_file.write_text(json.dumps(log_data, indent=2))
    except OSError:
        pass


def save_session_statistics(input_data: dict) -> None:
    """Save session statistics for analytics."""
    try:
        session_id = extract_session_id(input_data)
        reason = input_data.get("reason", "other")
        transcript_path = input_data.get("transcript_path", "")

        message_count = 0
        if transcript_path and Path(transcript_path).exists():
            try:
                with open(transcript_path) as f:
                    message_count = sum(1 for _ in f)
            except OSError:
                pass

        stats_dir = ensure_session_log_dir(session_id)
        stats_file = stats_dir / "session_statistics.json"

        stats: list = []
        if stats_file.exists():
            try:
                stats = json.loads(stats_file.read_text())
            except (json.JSONDecodeError, ValueError):
                stats = []

        stats.append({
            "session_id": session_id,
            "ended_at": datetime.now().isoformat(),
            "reason": reason,
            "message_count": message_count,
        })

        stats_file.write_text(json.dumps(stats, indent=2))
    except OSError:
        pass


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        input_data, _ = read_payload_from_stdin()
        reason = input_data.get("reason", "other")
        save_stats = session_save_stats_enabled(PROJECT_DIR)
        announce = tts_announce_enabled(PROJECT_DIR)

        session_id = extract_session_id(input_data)

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="SessionEnd",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: inspected session shutdown without capture, logs, stats, or TTS.",
                    details={
                        "session_id": session_id,
                        "reason": reason,
                        "save_stats": save_stats,
                        "announce_tts": announce,
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        maybe_capture_payload(input_data, "sessionEnd", PROJECT_DIR)

        log_session_end(input_data, reason)

        if save_stats:
            save_session_statistics(input_data)

        if announce:
            try:
                script_dir = Path(__file__).parent
                tts_script = script_dir / "utils" / "tts" / "pyttsx3_tts.py"
                if tts_script.exists():
                    messages = {
                        "clear": "Session cleared",
                        "logout": "Logging out",
                        "prompt_input_exit": "Session ended",
                        "bypass_permissions_disabled": "Bypass permissions disabled",
                        "other": "Session ended",
                    }
                    message = messages.get(reason, "Session ended")
                    subprocess.run(
                        [sys.executable, str(tts_script), message],
                        capture_output=True,
                        timeout=5,
                    )
            except Exception:
                pass
    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="SessionEnd",
                script=SCRIPT_NAME,
                kind="error",
                message=f"session_end failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
