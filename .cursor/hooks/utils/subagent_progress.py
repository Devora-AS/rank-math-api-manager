from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.spawn_trace import resolve_trace_run_id, sanitize_run_id

PROGRESS_STATUS_NOT_STARTED = "not_started"
PROGRESS_STATUS_SPAWN_OBSERVED = "spawn_observed"
PROGRESS_STATUS_PREPARING = "preparing"
PROGRESS_STATUS_ACTIVE = "active"
PROGRESS_STATUS_COMPLETED = "completed"
PROGRESS_STATUS_STALLED = "stalled"
PROGRESS_STATUS_FAILED = "failed"

DEFAULT_STARTUP_PATIENCE_SECONDS = 30
DEFAULT_STALL_SECONDS = 120
FRESH_SPAWN_GRACE_SECONDS = 10

_COMPLETED_STOP_STATUSES = {
    "completed",
    "complete",
    "done",
    "pass",
    "passed",
    "success",
    "succeeded",
    "ok",
}
_FAILED_STOP_STATUSES = {
    "aborted",
    "cancelled",
    "canceled",
    "error",
    "failed",
    "failure",
}
_STRONG_PROGRESS_SIGNALS = {"artifact_written", "file_changes"}
_PREPARING_PROGRESS_SIGNALS = {
    "hook_activity",
    "repo_reads",
    "searches",
    "setup",
    "transcript_activity",
    "validation_output",
}


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                rows.append(parsed)
    except (OSError, json.JSONDecodeError):
        return []
    return rows


def _parse_timestamp(value: Any) -> datetime | None:
    text = _clean_text(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _latest_row(rows: list[dict[str, Any]], child_id: str | None, kinds: set[str]) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    latest_timestamp: datetime | None = None
    for row in rows:
        kind = _clean_text(row.get("event_kind")) or ""
        if kind not in kinds:
            continue
        row_child = _clean_text(row.get("child_id") or row.get("subagent_id"))
        if child_id and row_child != child_id:
            continue
        timestamp = _parse_timestamp(row.get("timestamp"))
        if latest is None:
            latest = row
            latest_timestamp = timestamp
            continue
        if timestamp is None:
            continue
        if latest_timestamp is None or timestamp >= latest_timestamp:
            latest = row
            latest_timestamp = timestamp
    return latest


def _status_from_stop_row(row: dict[str, Any] | None) -> str | None:
    if not row:
        return None
    return _clean_text(row.get("status") or row.get("decision"))


def _child_id_from_rows(rows: list[dict[str, Any]]) -> str | None:
    for row in reversed(rows):
        child_id = _clean_text(row.get("child_id") or row.get("subagent_id"))
        if child_id:
            return child_id
    return None


def _spawn_timestamp(rows: list[dict[str, Any]], child_id: str | None) -> datetime | None:
    row = _latest_row(rows, child_id, {"subagent_started", "spawn_success"})
    return _parse_timestamp(row.get("timestamp")) if row else None


def _path_mtime_and_size(path: Path) -> tuple[float | None, int | None, bool]:
    if not path.exists():
        return None, None, False
    if path.is_dir():
        latest_mtime: float | None = None
        total_size = 0
        for item in path.rglob("*"):
            if not item.is_file():
                continue
            try:
                stat = item.stat()
            except OSError:
                continue
            total_size += stat.st_size
            latest_mtime = stat.st_mtime if latest_mtime is None else max(latest_mtime, stat.st_mtime)
        return latest_mtime, total_size, True
    try:
        stat = path.stat()
    except OSError:
        return None, None, False
    return stat.st_mtime, stat.st_size, True


def _resolve_candidate_path(repo_root: Path, candidate: str | None) -> Path | None:
    text = _clean_text(candidate)
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    return repo_root / path


def _normalize_progress_signals(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    signals: list[str] = []
    for value in values:
        signal = _clean_text(value)
        if signal:
            signals.append(signal)
    return signals


def _status_decision(
    *,
    spawn_observed: bool,
    stop_status: str | None,
    progress_signals: set[str],
    elapsed_seconds: int | None,
    startup_patience_seconds: int,
    stall_after_seconds: int,
    resume_attempts: int,
) -> tuple[str, str, bool]:
    if not spawn_observed:
        return PROGRESS_STATUS_NOT_STARTED, "No subagent spawn observed yet.", False

    if stop_status in _COMPLETED_STOP_STATUSES:
        return PROGRESS_STATUS_COMPLETED, "Subagent stop reported completion.", False

    if stop_status in _FAILED_STOP_STATUSES:
        return PROGRESS_STATUS_FAILED, "Subagent stop reported a failure or abort.", False

    if progress_signals & _STRONG_PROGRESS_SIGNALS:
        return (
            PROGRESS_STATUS_ACTIVE,
            "File changes or artifact writes show the subagent is actively progressing.",
            True,
        )

    if progress_signals & _PREPARING_PROGRESS_SIGNALS:
        if resume_attempts > 0 and elapsed_seconds is not None and elapsed_seconds >= stall_after_seconds:
            return (
                PROGRESS_STATUS_STALLED,
                "Repeated non-progress after a resume attempt crossed the stall threshold.",
                False,
            )
        return (
            PROGRESS_STATUS_PREPARING,
            "Startup evidence is present, so the subagent should be treated as preparing.",
            True,
        )

    if elapsed_seconds is None:
        return (
            PROGRESS_STATUS_SPAWN_OBSERVED,
            "Spawn was observed, but elapsed time is unknown and no stronger signals exist.",
            True,
        )

    if elapsed_seconds < FRESH_SPAWN_GRACE_SECONDS:
        return (
            PROGRESS_STATUS_SPAWN_OBSERVED,
            "Spawn was just observed; give the subagent time to bootstrap.",
            True,
        )

    if elapsed_seconds < startup_patience_seconds:
        return (
            PROGRESS_STATUS_PREPARING,
            "The subagent is still within the startup patience window.",
            True,
        )

    if resume_attempts > 0 and elapsed_seconds >= stall_after_seconds:
        return (
            PROGRESS_STATUS_STALLED,
            "The subagent still shows no progress after a resume attempt and the stall window expired.",
            False,
        )

    return (
        PROGRESS_STATUS_PREPARING,
        "No hard evidence of stall yet; resume the same subagent before superseding it.",
        True,
    )


def classify_subagent_progress(evidence: dict[str, Any]) -> str:
    status, _, _ = _status_decision(
        spawn_observed=bool(evidence.get("spawn_observed")),
        stop_status=_clean_text(evidence.get("stop_status")),
        progress_signals=set(_normalize_progress_signals(evidence.get("progress_signals"))),
        elapsed_seconds=(
            int(evidence["elapsed_seconds"])
            if evidence.get("elapsed_seconds") is not None
            else None
        ),
        startup_patience_seconds=int(
            evidence.get("startup_patience_seconds", DEFAULT_STARTUP_PATIENCE_SECONDS)
        ),
        stall_after_seconds=int(evidence.get("stall_after_seconds", DEFAULT_STALL_SECONDS)),
        resume_attempts=int(evidence.get("resume_attempts", 0) or 0),
    )
    return status


def _parent_action_for_status(status: str) -> str:
    if status == PROGRESS_STATUS_COMPLETED:
        return "proceed"
    if status == PROGRESS_STATUS_FAILED:
        return "retry_or_stop"
    if status == PROGRESS_STATUS_STALLED:
        return "consider_replace_or_stop"
    if status == PROGRESS_STATUS_ACTIVE:
        return "keep_waiting"
    if status in {PROGRESS_STATUS_SPAWN_OBSERVED, PROGRESS_STATUS_PREPARING}:
        return "resume_same_subagent"
    return "wait_for_spawn"


def inspect_subagent_progress(
    repo_root: Path | str,
    *,
    run_id: str | None = None,
    child_id: str | None = None,
    role: str | None = None,
    primary_artifact: str | None = None,
    transcript_path: str | None = None,
    resume_attempts: int = 0,
    startup_patience_seconds: int = DEFAULT_STARTUP_PATIENCE_SECONDS,
    stall_after_seconds: int = DEFAULT_STALL_SECONDS,
    now: datetime | None = None,
) -> dict[str, Any]:
    repo_root = Path(repo_root).resolve()
    run_id = sanitize_run_id(run_id or resolve_trace_run_id(repo_root) or "")
    if not run_id:
        return {
            "status": PROGRESS_STATUS_NOT_STARTED,
            "next_action": "wait_for_spawn",
            "should_hold_parent_work": False,
            "summary_text": "No trace run id is available, so progress cannot be summarized.",
            "evidence": {"reason": "missing_run_id"},
        }

    run_dir = repo_root / "artifacts" / "agent-traces" / run_id
    events_path = run_dir / "events.jsonl"
    rows = _load_jsonl_rows(events_path)
    if child_id is None:
        child_id = _child_id_from_rows(rows)

    spawn_row = _latest_row(rows, child_id, {"subagent_started", "spawn_success"})
    stop_row = _latest_row(rows, child_id, {"subagent_completed", "subagent_stop"})
    spawn_time = _parse_timestamp(spawn_row.get("timestamp")) if spawn_row else None
    stop_status = _status_from_stop_row(stop_row)
    latest_row = stop_row or spawn_row
    latest_row_time = _parse_timestamp(latest_row.get("timestamp")) if latest_row else None
    latest_event_kind = _clean_text(latest_row.get("event_kind")) if latest_row else None

    inferred_signals: list[str] = []
    transcript_candidate = _clean_text(
        transcript_path
        or (stop_row or {}).get("agent_transcript_path")
        or (stop_row or {}).get("transcript_path")
        or (spawn_row or {}).get("transcript_path")
    )
    artifact_candidate = _clean_text(
        primary_artifact
        or (
            "build-result.md" if role == "builder" else "verify-result.md" if role == "verifier" else None
        )
    )

    transcript_details: dict[str, Any] = {"path": transcript_candidate, "exists": False}
    artifact_details: dict[str, Any] = {"path": artifact_candidate, "exists": False}
    modified_files = _normalize_progress_signals((stop_row or {}).get("modified_files"))
    if modified_files:
        inferred_signals.append("file_changes")

    if transcript_candidate:
        transcript_path_obj = _resolve_candidate_path(repo_root, transcript_candidate)
        if transcript_path_obj is not None:
            transcript_mtime, transcript_size, transcript_exists = _path_mtime_and_size(transcript_path_obj)
            transcript_details.update(
                {
                    "exists": transcript_exists,
                    "mtime_epoch": transcript_mtime,
                    "size_bytes": transcript_size,
                }
            )
            if transcript_exists:
                inferred_signals.append("transcript_activity")
                if spawn_time is not None and transcript_mtime is not None:
                    transcript_stamp = datetime.fromtimestamp(transcript_mtime, tz=timezone.utc)
                    if transcript_stamp >= spawn_time:
                        inferred_signals.append("hook_activity")

    if artifact_candidate:
        artifact_path_obj = _resolve_candidate_path(repo_root, artifact_candidate)
        if artifact_path_obj is not None:
            artifact_mtime, artifact_size, artifact_exists = _path_mtime_and_size(artifact_path_obj)
            artifact_details.update(
                {
                    "exists": artifact_exists,
                    "mtime_epoch": artifact_mtime,
                    "size_bytes": artifact_size,
                }
            )
            if artifact_exists:
                inferred_signals.append("artifact_written")

    if stop_row is not None and latest_event_kind in {"subagent_completed", "subagent_stop"}:
        inferred_signals.append("hook_activity")

    if stop_row is not None:
        message_count = stop_row.get("message_count")
        try:
            if int(message_count or 0) > 0:
                inferred_signals.append("validation_output")
        except (TypeError, ValueError):
            pass

    if latest_row_time is not None and spawn_time is not None and latest_row_time > spawn_time:
        inferred_signals.append("hook_activity")

    inferred_signals = list(dict.fromkeys(inferred_signals))

    if now is None:
        now = datetime.now(timezone.utc)

    elapsed_seconds: int | None = None
    if spawn_time is not None:
        elapsed_seconds = max(0, int((now - spawn_time).total_seconds()))

    evidence = {
        "repo_root": str(repo_root),
        "run_id": run_id,
        "child_id": child_id,
        "role": role,
        "spawn_observed": bool(spawn_row),
        "spawn_timestamp": spawn_time.isoformat() if spawn_time else None,
        "latest_event_timestamp": latest_row_time.isoformat() if latest_row_time else None,
        "latest_event_kind": latest_event_kind,
        "stop_status": stop_status,
        "resume_attempts": int(resume_attempts),
        "startup_patience_seconds": int(startup_patience_seconds),
        "stall_after_seconds": int(stall_after_seconds),
        "elapsed_seconds": elapsed_seconds,
        "progress_signals": inferred_signals,
        "modified_files": modified_files,
        "transcript": transcript_details,
        "primary_artifact": artifact_details,
        "spawn_row": spawn_row,
        "stop_row": stop_row,
    }

    status, status_reason, should_hold_parent_work = _status_decision(
        spawn_observed=evidence["spawn_observed"],
        stop_status=stop_status,
        progress_signals=set(inferred_signals),
        elapsed_seconds=elapsed_seconds,
        startup_patience_seconds=int(startup_patience_seconds),
        stall_after_seconds=int(stall_after_seconds),
        resume_attempts=int(resume_attempts),
    )
    next_action = _parent_action_for_status(status)
    if status in {PROGRESS_STATUS_SPAWN_OBSERVED, PROGRESS_STATUS_PREPARING}:
        if elapsed_seconds is not None and elapsed_seconds >= startup_patience_seconds and not modified_files and "artifact_written" not in inferred_signals:
            next_action = "resume_same_subagent"

    summary_text = status_reason
    if status in {PROGRESS_STATUS_PREPARING, PROGRESS_STATUS_SPAWN_OBSERVED} and transcript_details.get("exists"):
        summary_text = f"{summary_text} Transcript or hook activity is visible, so the subagent is still preparing."
    if status == PROGRESS_STATUS_ACTIVE and artifact_details.get("exists"):
        summary_text = f"{summary_text} Primary artifact evidence is present."

    return {
        "status": status,
        "next_action": next_action,
        "should_hold_parent_work": should_hold_parent_work,
        "summary_text": summary_text,
        "evidence": evidence,
    }

