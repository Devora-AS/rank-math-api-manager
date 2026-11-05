"""Shared MAT Self-Compact hook helpers (opt-in via CURSOR_MAT_SELF_COMPACT)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.mat_env_resolve import mat_env_flag, repo_root

_LIB = repo_root() / "scripts" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

import mat_self_compact as msc  # noqa: E402


def self_compact_enabled(*, root: Path | None = None) -> bool:
    return mat_env_flag("CURSOR_MAT_SELF_COMPACT", default=False, root=root or repo_root())


def force_lane_enabled(*, root: Path | None = None) -> bool:
    return mat_env_flag("CURSOR_MAT_SELF_COMPACT_FORCE", default=False, root=root or repo_root())


def pre_tool_context_log_enabled(*, root: Path | None = None) -> bool:
    r = root or repo_root()
    return self_compact_enabled(root=r) and mat_env_flag(
        "CURSOR_MAT_SELF_COMPACT_LOG_PRETOOL",
        default=False,
        root=r,
    )


def append_pre_tool_context_usage_log(root: Path, payload: dict[str, Any]) -> None:
    """Opt-in spike: one JSONL line per PreToolUse when context_usage_percent is present."""
    if not pre_tool_context_log_enabled(root=root):
        return
    percent = msc.context_usage_from_payload(payload)
    if percent is None:
        return
    record = {
        "context_usage_percent": percent,
        "tool_name": _normalize_tool_name(payload),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    path = msc.pre_tool_context_usage_log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _coerce_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return raw if isinstance(raw, dict) else {}


def _normalize_tool_name(payload: dict[str, Any]) -> str:
    for key in ("tool_name", "tool"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _handoff_relative_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip()
    return normalized.startswith("artifacts/context-handoff/")


def is_force_lane_allowlisted(payload: dict[str, Any]) -> bool:
    tool = _normalize_tool_name(payload).lower()
    tool_input = _coerce_tool_input(payload)

    write_tools = {
        "write",
        "edit",
        "apply_patch",
        "strreplace",
        "search_replace",
    }
    if tool in write_tools or "write" in tool or "edit" in tool:
        for key in ("path", "file_path", "filePath", "target_file", "targetFile"):
            val = tool_input.get(key)
            if isinstance(val, str) and _handoff_relative_path(val):
                return True
        for key in ("paths", "files"):
            val = tool_input.get(key)
            if isinstance(val, list):
                if any(isinstance(p, str) and _handoff_relative_path(p) for p in val):
                    return True

    shell_tools = {"shell", "run_terminal_cmd", "run_terminal_command", "bash"}
    if tool in shell_tools or "shell" in tool or "terminal" in tool:
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        if isinstance(command, str) and "mat-context-gauge.py" in command:
            return True

    return False


def evaluate_pre_tool_use(root: Path, payload: dict[str, Any]) -> dict[str, Any] | None:
    """
    Return PreToolUse stdout JSON when notice/warning/force applies, else None (allow).
    Force lane deny requires CURSOR_MAT_SELF_COMPACT_FORCE=1.
    """
    if not self_compact_enabled(root=root):
        return None

    msc.update_gauge_from_payload(root, payload)
    append_pre_tool_context_usage_log(root, payload)
    thresholds = msc.load_thresholds(root)
    percent = msc.effective_percent(root, payload)
    level = msc.evaluate_pressure_level(
        percent,
        notice=thresholds.notice,
        warning=thresholds.warning,
        force=thresholds.force,
    )

    if level == "force" and force_lane_enabled(root=root):
        if is_force_lane_allowlisted(payload):
            return None
        return {
            "permission": "deny",
            "agent_message": (
                "MAT Self-Compact force lane (≥ "
                f"{thresholds.force}%): write handoff files under "
                "artifacts/context-handoff/ or run "
                "python3 scripts/mat-context-gauge.py before other tools."
            ),
        }

    if level == "warning":
        return {
            "agent_message": (
                f"Context pressure warning (≥ {thresholds.warning}%): run the "
                "mat-self-compact skill — update note-to-self.md and MAO handoffs."
            ),
        }

    if level == "notice":
        return {
            "agent_message": (
                f"Context pressure notice (≥ {thresholds.notice}%): consider a "
                "self-compact checkpoint soon."
            ),
        }

    return None


def pre_tool_use_dry_run_details(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if not self_compact_enabled(root=root):
        return {"self_compact_enabled": False, "self_compact_would_deny": False}
    response = evaluate_pre_tool_use(root, payload)
    would_deny = bool(response and response.get("permission") == "deny")
    return {
        "self_compact_enabled": True,
        "self_compact_force_lane": force_lane_enabled(root=root),
        "self_compact_would_deny": would_deny,
        "self_compact_response_preview": response,
    }


def record_pre_compact_handoff(root: Path, payload: dict[str, Any]) -> None:
    if not self_compact_enabled(root=root):
        return
    msc.update_gauge_from_payload(root, payload)
    compact_path = msc.last_compact_path(root)
    compact_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "trigger": payload.get("trigger", "unknown"),
        "context_usage_percent": msc.context_usage_from_payload(payload),
        "session_id": payload.get("session_id") or payload.get("conversation_id"),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    compact_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    state = msc.read_context_state(root)
    state["pending_compact"] = True
    state["last_compact_at"] = record["recorded_at"]
    msc.write_context_state(root, state)


def session_start_additional_context(root: Path) -> str | None:
    if not self_compact_enabled(root=root):
        return None
    note_path = msc.note_to_self_path(root)
    if not note_path.is_file():
        return None
    try:
        body = note_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not body:
        return None
    excerpt = body if len(body) <= 4000 else body[:4000] + "\n… (truncated)"
    return (
        "MAT Self-Compact handoff (artifacts/context-handoff/note-to-self.md):\n"
        f"{excerpt}\n\n"
        "MAO files remain authoritative: docs/current-plan.md, build-result.md, verify-result.md."
    )


def emit_session_start_context(message: str) -> None:
    print(json.dumps({"additional_context": message}, ensure_ascii=False))


def pending_compact_followup_message(root: Path) -> str | None:
    if not self_compact_enabled(root=root):
        return None
    gauge = msc.build_gauge_output(root)
    if not gauge.get("pending_compact"):
        return None
    return (
        "MAT Self-Compact: pending_compact is set after preCompact. "
        "Run the mat-self-compact skill (note-to-self + gauge), refresh MAO handoffs, "
        "then clear pending_compact in artifacts/context-handoff/context-state.json "
        "or complete the checkpoint procedure."
    )


def self_compact_stop_followup_allowed(*, root: Path | None = None) -> bool:
    """Pending-compact Stop followup requires self-compact and Stop followup opt-in."""
    r = root or repo_root()
    return self_compact_enabled(root=r) and mat_env_flag(
        "CURSOR_MAT_STOP_VALIDATOR_FOLLOWUP",
        default=False,
        root=r,
    )
