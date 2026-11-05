#!/usr/bin/env python3
"""Cursor Hook: PreCompact — Pre-Compaction Handler

Fires on: PreCompact (before context window compaction)
Purpose:  Log the pre-compact event and optionally backup the transcript
          before compaction occurs. Records trigger type, context usage,
          and message counts.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Always exits 0 to avoid blocking the agent.
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from utils.context_budget import append_session_budget_advisory_note
from payload_capture import maybe_capture_payload, read_payload_from_stdin
from session_id import extract_session_id
from utils.constants import PROJECT_DIR, ensure_session_log_dir
from utils.mat_env_resolve import mat_env_flag
from utils.context_pressure import record_pre_compact_handoff
from utils.routing_advisory import append_routing_advisory_jsonl, build_routing_advisory
from utils.routing_rollup import write_routing_rollup_json

SCRIPT_NAME = "pre_compact.py"


def log_pre_compact(
    input_data: dict, custom_instructions: str, routing_advisory: dict | None = None
) -> None:
    """Log pre-compact event to session log directory."""
    try:
        session_id = extract_session_id(input_data)
        log_dir = ensure_session_log_dir(session_id)
        log_file = log_dir / "pre_compact.json"

        log_data: list = []
        if log_file.exists():
            try:
                log_data = json.loads(log_file.read_text())
            except (json.JSONDecodeError, ValueError):
                log_data = []

        log_data.append({
            "session_id": session_id,
            "hook_event_name": input_data.get("hook_event_name", "PreCompact"),
            "trigger": input_data.get("trigger", "unknown"),
            "custom_instructions": custom_instructions,
            **({"routing_advisory": routing_advisory} if routing_advisory else {}),
            "logged_at": datetime.now().isoformat(),
        })

        log_file.write_text(json.dumps(log_data, indent=2))
    except OSError:
        pass


def backup_transcript(transcript_path: str, trigger: str, custom_instructions: str = "") -> str | None:
    """Create a backup of the transcript before compaction."""
    try:
        if not os.path.exists(transcript_path):
            return None

        backup_dir = PROJECT_DIR / "logs" / "transcript_backups"  # flat — shared across sessions
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = Path(transcript_path).stem

        suffix = ""
        if custom_instructions:
            sanitized = re.sub(r"[^a-zA-Z0-9]", "_", custom_instructions[:30]).strip("_")
            if sanitized:
                suffix = f"_{sanitized}"

        backup_name = f"{session_name}_pre_compact_{trigger}{suffix}_{timestamp}.jsonl"
        backup_path = backup_dir / backup_name

        shutil.copy2(transcript_path, backup_path)
        return str(backup_path)
    except Exception:
        return None


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        input_data, _ = read_payload_from_stdin()
        transcript_path = input_data.get("transcript_path", "")
        trigger = input_data.get("trigger", "unknown")
        custom_instructions = input_data.get("custom_instructions", "")
        routing_advisory = build_routing_advisory(
            input_data, "preCompact", fallback_text=custom_instructions
        )
        do_backup = mat_env_flag("CURSOR_BACKUP_TRANSCRIPTS", default=False)

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="PreCompact",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: inspected compaction handling without capture, logging, or transcript backup.",
                    details={
                        "session_id": extract_session_id(input_data),
                        "trigger": trigger,
                        "custom_instructions": custom_instructions,
                        "routing_advisory": routing_advisory,
                        "transcript_path": transcript_path,
                        "backup_enabled": do_backup,
                        "would_backup": bool(do_backup and transcript_path),
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        maybe_capture_payload(input_data, "preCompact", PROJECT_DIR)

        session_id = extract_session_id(input_data)

        log_pre_compact(input_data, custom_instructions, routing_advisory=routing_advisory)
        write_routing_rollup_json(PROJECT_DIR, routing_advisory, hook_event="preCompact")
        append_routing_advisory_jsonl(PROJECT_DIR, routing_advisory, hook_event="preCompact")
        append_session_budget_advisory_note(PROJECT_DIR, extract_session_id(input_data))

        if do_backup and transcript_path:
            backup_transcript(transcript_path, trigger, custom_instructions)

        record_pre_compact_handoff(PROJECT_DIR, input_data)

    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="PreCompact",
                script=SCRIPT_NAME,
                kind="error",
                message=f"pre_compact failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
