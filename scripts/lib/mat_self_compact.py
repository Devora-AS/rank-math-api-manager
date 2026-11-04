"""MAT Self-Compact v1 — thresholds, gauge snapshots, and handoff paths."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

PressureLevel = Literal["ok", "notice", "warning", "force"]

HANDOFF_REL = Path("artifacts") / "context-handoff"
NOTE_TO_SELF_NAME = "note-to-self.md"
CONTEXT_STATE_NAME = "context-state.json"
LAST_GAUGE_NAME = "last-gauge.json"
LAST_COMPACT_NAME = "last-compact.json"
PRE_TOOL_CONTEXT_USAGE_LOG_NAME = "pre-tool-context-usage.jsonl"

DEFAULT_NOTICE_PCT = 55
DEFAULT_WARNING_PCT = 70
DEFAULT_FORCE_PCT = 85

# Rough token budget for tokens_until_warning (advisory; not billing truth).
DEFAULT_CONTEXT_TOKEN_BUDGET = 200_000


@dataclass(frozen=True)
class Thresholds:
    notice: int
    warning: int
    force: int


def handoff_dir(root: Path) -> Path:
    return root / HANDOFF_REL


def note_to_self_path(root: Path) -> Path:
    return handoff_dir(root) / NOTE_TO_SELF_NAME


def context_state_path(root: Path) -> Path:
    return handoff_dir(root) / CONTEXT_STATE_NAME


def last_gauge_path(root: Path) -> Path:
    return handoff_dir(root) / LAST_GAUGE_NAME


def last_compact_path(root: Path) -> Path:
    return handoff_dir(root) / LAST_COMPACT_NAME


def pre_tool_context_usage_log_path(root: Path) -> Path:
    return handoff_dir(root) / PRE_TOOL_CONTEXT_USAGE_LOG_NAME


def _int_from_env(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        return default


def load_thresholds(root: Path | None = None) -> Thresholds:
    """Load notice/warning/force percent thresholds (env overrides, then defaults)."""
    _ = root  # reserved for future .mat.env file reads via mat_env
    return Thresholds(
        notice=_int_from_env("CURSOR_MAT_SELF_COMPACT_NOTICE_PCT", DEFAULT_NOTICE_PCT),
        warning=_int_from_env("CURSOR_MAT_SELF_COMPACT_WARNING_PCT", DEFAULT_WARNING_PCT),
        force=_int_from_env("CURSOR_MAT_SELF_COMPACT_FORCE_PCT", DEFAULT_FORCE_PCT),
    )


def evaluate_pressure_level(
    percent: int | float | None,
    *,
    notice: int = DEFAULT_NOTICE_PCT,
    warning: int = DEFAULT_WARNING_PCT,
    force: int = DEFAULT_FORCE_PCT,
) -> PressureLevel:
    if percent is None:
        return "ok"
    try:
        value = float(percent)
    except (TypeError, ValueError):
        return "ok"
    if value >= force:
        return "force"
    if value >= warning:
        return "warning"
    if value >= notice:
        return "notice"
    return "ok"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_gauge_snapshot(root: Path) -> dict[str, Any]:
    return _read_json(last_gauge_path(root))


def write_gauge_snapshot(root: Path, snapshot: dict[str, Any]) -> None:
    path = last_gauge_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**snapshot, "updated_at": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_context_state(root: Path) -> dict[str, Any]:
    return _read_json(context_state_path(root))


def write_context_state(root: Path, state: dict[str, Any]) -> None:
    path = context_state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def context_usage_from_payload(raw: dict[str, Any]) -> int | None:
    for key in (
        "context_usage_percent",
        "contextUsagePercent",
        "context_usage",
        "contextUsage",
    ):
        val = raw.get(key)
        if val is None:
            continue
        try:
            return int(val)
        except (TypeError, ValueError):
            continue
    return None


def effective_percent(root: Path, payload: dict[str, Any] | None = None) -> int | None:
    if payload:
        from_payload = context_usage_from_payload(payload)
        if from_payload is not None:
            return from_payload
    snap = read_gauge_snapshot(root)
    val = snap.get("context_usage_percent")
    if val is None:
        val = snap.get("percent")
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def tokens_until_warning(percent: int | None, warning_at: int, token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET) -> int | None:
    if percent is None:
        return None
    remaining_pct = max(0, warning_at - percent)
    return int(token_budget * remaining_pct / 100)


def build_gauge_output(root: Path, *, token_budget: int = DEFAULT_CONTEXT_TOKEN_BUDGET) -> dict[str, Any]:
    thresholds = load_thresholds(root)
    snap = read_gauge_snapshot(root)
    state = read_context_state(root)
    percent = effective_percent(root, None)
    used_tokens = snap.get("used_tokens")
    try:
        used_tokens_int = int(used_tokens) if used_tokens is not None else None
    except (TypeError, ValueError):
        used_tokens_int = None

    level = evaluate_pressure_level(
        percent,
        notice=thresholds.notice,
        warning=thresholds.warning,
        force=thresholds.force,
    )
    pending = bool(state.get("pending_compact") or snap.get("pending_compact"))

    return {
        "used_tokens": used_tokens_int,
        "percent": percent,
        "notice_at": thresholds.notice,
        "warning_at": thresholds.warning,
        "force_at": thresholds.force,
        "tokens_until_warning": tokens_until_warning(
            percent, thresholds.warning, token_budget=token_budget
        ),
        "level": level,
        "pending_compact": pending,
    }


def update_gauge_from_payload(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    percent = context_usage_from_payload(payload)
    snap = read_gauge_snapshot(root)
    if percent is not None:
        snap["context_usage_percent"] = percent
        snap["percent"] = percent
    for key in ("used_tokens", "messages_to_compact", "messagesToCompact"):
        if key in payload and payload[key] is not None:
            snap[key] = payload[key]
    write_gauge_snapshot(root, snap)
    return build_gauge_output(root)
