#!/usr/bin/env python3
"""Cursor Hook: afterFileEdit — Post-Edit Formatter & Logger

Fires on: afterFileEdit (after the agent edits a file)
Purpose:  Run formatters based on file extension and log the edit event.

This is a new hook for Cursor (no Claude equivalent).
Always exits 0 to avoid blocking the agent.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from session_id import extract_session_id
from utils.constants import PROJECT_DIR, ensure_session_log_dir

SCRIPT_NAME = "after_file_edit.py"


def read_stdin_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


FORMATTERS: dict[str, list[list[str]]] = {
    ".py": [["ruff", "format", "{file}"], ["ruff", "check", "--fix", "{file}"]],
    ".ts": [["prettier", "--write", "{file}"]],
    ".tsx": [["prettier", "--write", "{file}"]],
    ".js": [["prettier", "--write", "{file}"]],
    ".jsx": [["prettier", "--write", "{file}"]],
}


def run_formatter(file_path: str) -> None:
    """Run the appropriate formatter for the given file extension."""
    ext = Path(file_path).suffix
    commands = FORMATTERS.get(ext)
    if not commands:
        return

    for cmd_template in commands:
        cmd = [part.replace("{file}", file_path) for part in cmd_template]
        try:
            subprocess.run(
                cmd,
                cwd=str(PROJECT_DIR),
                capture_output=True,
                timeout=15,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass


def log_edit_event(session_id: str, file_path: str, edits: list) -> None:
    """Log the file edit event to the session log directory."""
    try:
        log_dir = ensure_session_log_dir(session_id)
        log_file = log_dir / "file_edits.json"

        log_data: list = []
        if log_file.exists():
            try:
                log_data = json.loads(log_file.read_text())
            except (json.JSONDecodeError, ValueError):
                log_data = []

        log_data.append({
            "file_path": file_path,
            "edit_count": len(edits),
            "logged_at": datetime.now().isoformat(),
        })

        log_file.write_text(json.dumps(log_data, indent=2))
    except OSError:
        pass


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        input_data = read_stdin_payload()

        session_id = extract_session_id(input_data)
        file_path = input_data.get("file_path") or input_data.get("filePath") or ""
        edits = input_data.get("edits", [])

        if args.dry_run:
            ext = Path(file_path).suffix
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="afterFileEdit",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: inspected formatter selection without running formatters or logging.",
                    details={
                        "session_id": session_id,
                        "file_path": file_path,
                        "edit_count": len(edits),
                        "formatter_supported": ext in FORMATTERS,
                        "formatter_commands": [
                            [part.replace("{file}", file_path) for part in cmd_template]
                            for cmd_template in FORMATTERS.get(ext, [])
                        ],
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        if file_path:
            run_formatter(file_path)

        log_edit_event(session_id, file_path, edits)

    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="afterFileEdit",
                script=SCRIPT_NAME,
                kind="error",
                message=f"after_file_edit failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
