"""
loop_events.py — opt-in append of loop handoff events to artifacts/loop/events.jsonl.

Enabled with CURSOR_MAT_LOOP_EVENTS=1. Fail-open; never blocks PostToolUse.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from mao_gate import touches_build_result, touches_current_plan
from utils.mat_env_resolve import mat_env_flag

LOOP_EVENTS_VERSION = "1"
EVENTS_JSONL_REL = Path("artifacts") / "loop" / "events.jsonl"


def loop_events_enabled() -> bool:
    return mat_env_flag("CURSOR_MAT_LOOP_EVENTS", default=False)


def _handoff_kind(changed_paths: list[str]) -> str | None:
    if touches_build_result(changed_paths):
        return "build_result"
    if touches_current_plan(changed_paths):
        return "current_plan"
    return None


def append_loop_handoff_event(
    project_dir: str | Path,
    changed_paths: list[str],
    *,
    trigger: str = "post_tool_use",
) -> dict[str, Any] | None:
    """
    Append one JSONL row when a policy-relevant handoff file was written.

    Returns the event dict on success, else None (disabled, irrelevant path, or I/O error).
    """
    if not loop_events_enabled():
        return None

    handoff = _handoff_kind(changed_paths)
    if handoff is None:
        return None

    root = Path(project_dir).resolve()
    event: dict[str, Any] = {
        "event_version": LOOP_EVENTS_VERSION,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "handoff": handoff,
        "changed_paths": [p for p in changed_paths if isinstance(p, str) and p.strip()],
    }

    jsonl_path = root / EVENTS_JSONL_REL
    line = json.dumps(event, ensure_ascii=False) + "\n"
    try:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        return None
    return event
