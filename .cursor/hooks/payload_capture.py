"""Shared stdin reader and optional payload capture for Cursor hooks."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from utils.mat_env_resolve import mat_env_keys as _resolve_mat_env_keys_for_root

# Keys resolved via scripts/lib/mat_env.py (process → .mat.env → .env CURSOR_* fallback).
_CAPTURE_ENV_KEYS = (
    "CURSOR_HOOK_CAPTURE",
    "CURSOR_HOOK_CAPTURE_EVENTS",
    "CURSOR_HOOK_CAPTURE_DIR",
    "CURSOR_HOOK_CAPTURE_PER_SESSION",
)


def _resolve_capture_env(repo_root: Path) -> dict[str, str]:
    """
    Merge capture settings via mat_env loader (non-mutating).

    Hook subprocesses often do not inherit shell exports from the integrated terminal;
    repo-local `.mat.env` / `.env` CURSOR_* fallback is the reliable opt-in path.
    """
    return _resolve_mat_env_keys_for_root(_CAPTURE_ENV_KEYS, root=repo_root)


def _capture_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _per_session_capture_enabled(cfg: dict[str, str]) -> bool:
    """When true, writes go under CAPTURE_DIR/<sanitized-session-id>/ (see AGENTS.md)."""
    return _capture_enabled(cfg.get("CURSOR_HOOK_CAPTURE_PER_SESSION", ""))


def _sanitize_session_subdir(session_id: str) -> str:
    """Filesystem-safe single path segment for a session / conversation id."""
    out: list[str] = []
    for ch in session_id.strip()[:200]:
        if ch.isalnum() or ch in "._-":
            out.append(ch)
        else:
            out.append("_")
    segment = "".join(out).strip("._-") or "_empty"
    return segment


_LIFECYCLE_CAPTURE_EVENTS = {"sessionStart", "sessionEnd", "stop", "preCompact"}


def _resolve_capture_dir(override_dir: str, repo_root: Path) -> Path:
    """Resolve capture dir relative to the workspace root unless already absolute."""
    if not override_dir.strip():
        return repo_root / "artifacts" / "phase1" / "raw_payloads"

    candidate = Path(override_dir).expanduser()
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _extract_capture_session_id(raw: dict[str, Any]) -> str:
    """Best-effort stable session identifier from lifecycle payload keys."""
    for key in (
        "conversation_id",
        "conversationId",
        "session_id",
        "sessionId",
        "parent_conversation_id",
        "parentConversationId",
        "generation_id",
        "generationId",
    ):
        value = raw.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_session_start_capture_id(target_dir: Path) -> str:
    session_start = target_dir / "sessionStart.json"
    if not session_start.exists():
        return ""
    payload = _load_json_file(session_start)
    if not payload:
        return ""
    return _extract_capture_session_id(payload)


def _extract_status_from_stop(target_dir: Path, expected_session_id: str) -> str:
    stop_path = target_dir / "stop.json"
    stop_payload = _load_json_file(stop_path)
    if not stop_payload:
        return "unknown"
    if _extract_capture_session_id(stop_payload) != expected_session_id:
        return "unknown"
    status = stop_payload.get("status")
    if status is None:
        return "unknown"
    return str(status).strip() or "unknown"


def _read_matching_payload(target_dir: Path, name: str, expected_session_id: str) -> dict[str, Any] | None:
    payload = _load_json_file(target_dir / f"{name}.json")
    if not payload:
        return None
    if _extract_capture_session_id(payload) != expected_session_id:
        return None
    return payload


def _infer_pre_compact_payload(target_dir: Path, established_session_id: str) -> dict[str, Any] | None:
    """
    Build a best-effort `preCompact` payload when compaction never fired.

    The payload is explicitly tagged as inferred for audit transparency.
    """
    start_payload = _read_matching_payload(target_dir, "sessionStart", established_session_id)
    if not start_payload:
        return None
    stop_payload = _read_matching_payload(target_dir, "stop", established_session_id) or {}

    return {
        "conversation_id": established_session_id,
        "session_id": established_session_id,
        "generation_id": stop_payload.get("generation_id") or start_payload.get("generation_id"),
        "model": stop_payload.get("model") or start_payload.get("model"),
        "hook_event_name": "preCompact",
        "workspace_roots": stop_payload.get("workspace_roots") or start_payload.get("workspace_roots"),
        "transcript_path": stop_payload.get("transcript_path") or start_payload.get("transcript_path"),
        # Unknown at inference time; keep numeric placeholders explicit.
        "trigger": "inferred_on_next_session_start",
        "context_usage_percent": -1,
        "context_tokens": -1,
        "context_window_size": -1,
        "message_count": -1,
        "messages_to_compact": -1,
        "is_first_compaction": False,
        "_inferred_pre_compact": True,
        "_inferred_from": "sessionStart_rollover",
    }


def _infer_session_end_payload(target_dir: Path, established_session_id: str) -> dict[str, Any] | None:
    """
    Build a best-effort `sessionEnd` payload when Cursor never emits sessionEnd.

    This is only used during a new `sessionStart` rollover and is explicitly
    marked as inferred so downstream audits can distinguish it from live stdin.
    """
    session_start_path = target_dir / "sessionStart.json"
    start_payload = _load_json_file(session_start_path)
    if not start_payload:
        return None
    if _extract_capture_session_id(start_payload) != established_session_id:
        return None

    now_ms = int(time.time() * 1000)
    try:
        started_ms = int(session_start_path.stat().st_mtime * 1000)
    except OSError:
        started_ms = now_ms
    duration_ms = max(0, now_ms - started_ms)

    return {
        "session_id": established_session_id,
        "conversation_id": established_session_id,
        "generation_id": start_payload.get("generation_id"),
        "model": start_payload.get("model"),
        "hook_event_name": "sessionEnd",
        "workspace_roots": start_payload.get("workspace_roots"),
        "transcript_path": start_payload.get("transcript_path"),
        "reason": "inferred_on_next_session_start",
        "duration_ms": duration_ms,
        "final_status": _extract_status_from_stop(target_dir, established_session_id),
        "_inferred_session_end": True,
        "_inferred_from": "sessionStart_rollover",
    }


def _ensure_inferred_artifact(
    target_dir: Path,
    canonical_name: str,
    established_session_id: str,
    infer_builder,
) -> bool:
    existing = _read_matching_payload(target_dir, canonical_name, established_session_id)
    if existing:
        return True
    inferred = infer_builder(target_dir, established_session_id)
    if not inferred:
        return False
    try:
        path = target_dir / f"{canonical_name}.json"
        path.write_text(json.dumps(inferred, indent=2) + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


def _ensure_inferred_terminal_artifacts_for_rollover(
    target_dir: Path,
    established_session_id: str,
    next_session_id: str,
) -> bool:
    """
    On session rollover, ensure the previous session has terminal artifacts.

    Returns True when inference succeeded for all required inferred artifacts.
    """
    if not established_session_id:
        return True
    if not next_session_id:
        return False
    if established_session_id == next_session_id:
        return True

    end_ok = _ensure_inferred_artifact(
        target_dir,
        "sessionEnd",
        established_session_id,
        _infer_session_end_payload,
    )
    precompact_ok = _ensure_inferred_artifact(
        target_dir,
        "preCompact",
        established_session_id,
        _infer_pre_compact_payload,
    )
    return end_ok and precompact_ok


def _should_capture_lifecycle_event(
    canonical_event: str,
    raw: dict[str, Any],
    target_dir: Path,
) -> bool:
    """
    Keep one lifecycle capture directory bound to one session.

    - `sessionStart` establishes the session identity in `sessionStart.json`.
    - Other lifecycle events are ignored until `sessionStart.json` exists.
    - Once established, only matching-session lifecycle events are accepted.
    """
    if canonical_event not in _LIFECYCLE_CAPTURE_EVENTS:
        return True

    current_session_id = _extract_capture_session_id(raw)
    established_session_id = _read_session_start_capture_id(target_dir)

    if canonical_event == "sessionStart":
        if not established_session_id:
            return True
        if not current_session_id:
            return False
        # Preserve single-run provenance in one directory:
        # if a different session starts, do not overwrite the existing sessionStart.
        _ = _ensure_inferred_terminal_artifacts_for_rollover(
            target_dir,
            established_session_id,
            current_session_id,
        )
        return current_session_id == established_session_id

    if not established_session_id:
        return False
    if not current_session_id:
        return False
    return current_session_id == established_session_id


def read_payload_from_stdin() -> tuple[dict[str, Any], str]:
    """Read stdin once and return the parsed payload plus raw text."""
    try:
        raw_bytes = sys.stdin.buffer.read()
    except OSError as exc:
        print(f"[payload_capture] stdin read error: {exc}", file=sys.stderr)
        return {}, ""

    if not raw_bytes.strip():
        return {}, ""

    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"[payload_capture] stdin UTF-8 decode error: {exc}", file=sys.stderr)
        return {}, raw_bytes.decode("utf-8", errors="replace")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        print(f"[payload_capture] stdin JSON parse error: {exc}", file=sys.stderr)
        return {}, raw_text

    if not isinstance(parsed, dict):
        print(
            f"[payload_capture] stdin JSON root must be an object, got {type(parsed).__name__}",
            file=sys.stderr,
        )
        return {}, raw_text

    return parsed, raw_text


def extract_hook_event_name(raw: dict[str, Any]) -> str | None:
    for key in (
        "hook_event_name",
        "hookEventName",
        "hook_event",
        "hookEvent",
        "event",
        "cursor_hook_event",
    ):
        value = raw.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def extract_project_dir(raw: dict[str, Any], fallback: str | Path) -> Path:
    workspace_roots = raw.get("workspace_roots") or raw.get("workspaceRoots")
    if isinstance(workspace_roots, list):
        for item in workspace_roots:
            if item and str(item).strip():
                return Path(str(item).strip())
    return Path(fallback)


def canonicalize_hook_event_name(name: str | None) -> str:
    if not name:
        return "unknown"
    key = name.strip()
    lower = key.lower()
    mapping = {
        "sessionstart": "sessionStart",
        "sessionend": "sessionEnd",
        "stop": "stop",
        "precompact": "preCompact",
        "pretooluse": "preToolUse",
        "posttooluse": "postToolUse",
        "posttoolusefailure": "postToolUseFailure",
        "beforesubmitprompt": "beforeSubmitPrompt",
        "afterfileedit": "afterFileEdit",
        "subagentstart": "subagentStart",
        "subagentstop": "subagentStop",
    }
    return mapping.get(lower, key)


def maybe_capture_payload(
    raw: dict[str, Any],
    hook_event: str | None,
    project_dir: str | Path,
) -> Path | None:
    """
    Pretty-print hook stdin JSON when capture is explicitly enabled.

    Set CURSOR_HOOK_CAPTURE_PER_SESSION=1 to nest files under one subdirectory
    per session (from conversation_id / session_id keys), avoiding mixed sessions
    in a shared folder. Rollover-inferred terminal artifacts then apply only
    within that subdirectory (not across composer sessions).
    """
    repo_root = Path(extract_project_dir(raw, project_dir))
    cfg = _resolve_capture_env(repo_root)
    enabled = _capture_enabled(cfg.get("CURSOR_HOOK_CAPTURE", ""))
    if not enabled or not raw:
        return None

    canonical_event = canonicalize_hook_event_name(hook_event)
    configured_events = {
        canonicalize_hook_event_name(part)
        for part in cfg.get("CURSOR_HOOK_CAPTURE_EVENTS", "").split(",")
        if part.strip()
    }
    if configured_events and canonical_event not in configured_events:
        return None

    override_dir = cfg.get("CURSOR_HOOK_CAPTURE_DIR", "").strip()
    target_dir = _resolve_capture_dir(override_dir, repo_root)
    if _per_session_capture_enabled(cfg):
        sid = _extract_capture_session_id(raw)
        if sid:
            target_dir = target_dir / _sanitize_session_subdir(sid)
        else:
            print(
                "[payload_capture] CURSOR_HOOK_CAPTURE_PER_SESSION=1 but stdin "
                "has no session id; using _no_session_id/",
                file=sys.stderr,
            )
            target_dir = target_dir / "_no_session_id"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        if not _should_capture_lifecycle_event(canonical_event, raw, target_dir):
            return None
        target_path = target_dir / f"{canonical_event}.json"
        target_path.write_text(json.dumps(raw, indent=2) + "\n")
        return target_path
    except OSError:
        return None
