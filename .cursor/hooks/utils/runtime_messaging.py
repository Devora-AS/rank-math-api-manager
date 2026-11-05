from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

UTILS_DIR = Path(__file__).resolve().parent
HOOKS_DIR = UTILS_DIR.parent
REPO_ROOT = HOOKS_DIR.parent.parent
SCHEMA_DIR = REPO_ROOT / "docs" / "runtime-messaging"
RUNTIME_DB_REL = Path("artifacts") / "mat-runtime" / "runtime.sqlite3"
RUNTIME_SCHEMA_VERSION = "1.0.0"

EVENT_SCHEMA_PATH = SCHEMA_DIR / "event-envelope.schema.json"
MAILBOX_SCHEMA_PATH = SCHEMA_DIR / "mailbox-item.schema.json"
DELIVERY_SCHEMA_PATH = SCHEMA_DIR / "delivery-record.schema.json"
SUMMARY_SCHEMA_PATH = REPO_ROOT / "docs" / "update-mat" / "advisor-task-session-summary.schema.json"
OUTBOX_SCHEMA_PATH = SCHEMA_DIR / "outbox-item.schema.json"
DELIVERY_ATTEMPT_SCHEMA_PATH = SCHEMA_DIR / "delivery-attempt.schema.json"

SESSION_KINDS = {"advisor", "task", "orchestrator", "subagent"}
TARGET_SELECTOR_TYPES = {"session_id", "same_run", "same_repo", "same_branch"}
MESSAGE_KINDS = {
    "session_start",
    "session_stop",
    "advisor_note",
    "task_update",
    "task_completed",
    "task_blocked",
    "followup_request",
    "approval_request",
    "approval_required",
    "approval_granted",
    "approval_rejected",
    "summary",
    "delivery_evidence",
}
EVENT_TYPES = {"message", "lifecycle", "delivery"}
APPROVAL_STATES = {"not_required", "pending", "approved", "rejected"}
DELIVERY_MODES = {"active_followup", "durable_mailbox"}
MAILBOX_STATUSES = {"queued", "delivered", "acked", "suppressed", "failed"}
DELIVERY_STATUSES = {"delivered", "queued", "suppressed", "failed", "acked"}
SUBSCRIPTION_POLICY_FIELDS = {
    "subscription_id",
    "session_id",
    "policy_name",
    "is_active",
    "priority",
    "run_id",
    "repo_root",
    "branch",
    "source_role",
    "target_role",
    "task_id",
    "correlation_id",
    "event_type",
    "message_kind",
    "route_status",
    "allow_active_followup",
    "allow_durable_mailbox",
    "notes",
}
OUTBOX_STATUSES = {
    "queued",
    "delivering",
    "retry_pending",
    "dispatched",
    "delivered",
    "acked",
    "suppressed",
    "failed",
    "awaiting_approval",
    "dead_letter",
    "retrying",
    "dead_lettered",
}

OUTBOX_STATUS_ALIASES = {
    "retrying": "retry_pending",
    "dead_lettered": "dead_letter",
}


def _canonical_outbox_status(status: str | None) -> str | None:
    if status is None:
        return None
    return OUTBOX_STATUS_ALIASES.get(status, status)


def _event_task_id(envelope: dict[str, Any]) -> str | None:
    payload = envelope.get("payload")
    if isinstance(payload, dict):
        task_id = _clean_text(payload.get("task_id"))
        if task_id:
            return task_id
    return _clean_text(envelope.get("task_id"))


def _event_correlation_id(envelope: dict[str, Any]) -> str | None:
    payload = envelope.get("payload")
    if isinstance(payload, dict):
        correlation_id = _clean_text(payload.get("correlation_id"))
        if correlation_id:
            return correlation_id
    return _clean_text(envelope.get("correlation_id"))


def _routing_profile(message_kind: str, *, requires_approval: bool, approval_state: str) -> str:
    if message_kind in {"approval_request", "approval_required"} or requires_approval:
        return "approval_required"
    if message_kind == "approval_granted" or approval_state == "approved":
        return "approval_granted"
    if message_kind == "approval_rejected" or approval_state == "rejected":
        return "approval_rejected"
    if message_kind == "task_completed":
        return "task_completed"
    if message_kind == "task_blocked":
        return "task_blocked"
    if message_kind == "delivery_evidence":
        return "delivery_evidence"
    return "scoped_notify"


def _default_subscription_templates(session: dict[str, Any]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = [
        {
            "policy_name": "scope_default",
            "priority": 100,
            "run_id": session.get("run_id") if session.get("subscribes_same_run") else None,
            "repo_root": session.get("repo_root") if session.get("subscribes_same_repo") else None,
            "branch": session.get("branch") if session.get("subscribes_same_branch") else None,
            "source_role": None,
            "target_role": session.get("role"),
            "task_id": None,
            "correlation_id": None,
            "event_type": None,
            "message_kind": None,
            "route_status": None,
            "allow_active_followup": True,
            "allow_durable_mailbox": True,
            "notes": "default same-run/repo/branch subscription",
        }
    ]
    role = _clean_text(session.get("role"))
    if role in {"advisor", "task", "orchestrator"}:
        for message_kind in ("task_update", "task_completed", "task_blocked", "followup_request"):
            templates.append(
                {
                    "policy_name": f"task_flow_{message_kind}",
                    "priority": 40,
                    "run_id": session.get("run_id") if session.get("subscribes_same_run") else None,
                    "repo_root": session.get("repo_root") if session.get("subscribes_same_repo") else None,
                    "branch": session.get("branch") if session.get("subscribes_same_branch") else None,
                    "source_role": None,
                    "target_role": session.get("role"),
                    "task_id": None,
                    "correlation_id": None,
                    "event_type": "message",
                    "message_kind": message_kind,
                    "route_status": None,
                    "allow_active_followup": True,
                    "allow_durable_mailbox": True,
                    "notes": "task flow notify policy",
                }
            )
    if role in {"advisor", "operator", "orchestrator"}:
        for message_kind in ("approval_request", "approval_required", "approval_granted", "approval_rejected"):
            templates.append(
                {
                    "policy_name": f"approval_flow_{message_kind}",
                    "priority": 20,
                    "run_id": session.get("run_id") if session.get("subscribes_same_run") else None,
                    "repo_root": session.get("repo_root") if session.get("subscribes_same_repo") else None,
                    "branch": session.get("branch") if session.get("subscribes_same_branch") else None,
                    "source_role": None,
                    "target_role": session.get("role"),
                    "task_id": None,
                    "correlation_id": None,
                    "event_type": "message",
                    "message_kind": message_kind,
                    "route_status": None,
                    "allow_active_followup": False,
                    "allow_durable_mailbox": True,
                    "notes": "approval queue policy",
                }
            )
    if role in {"operator", "orchestrator"}:
        templates.append(
            {
                "policy_name": "dlq_watch",
                "priority": 10,
                "run_id": session.get("run_id") if session.get("subscribes_same_run") else None,
                "repo_root": session.get("repo_root") if session.get("subscribes_same_repo") else None,
                "branch": session.get("branch") if session.get("subscribes_same_branch") else None,
                "source_role": None,
                "target_role": session.get("role"),
                "task_id": None,
                "correlation_id": None,
                "event_type": "delivery",
                "message_kind": "delivery_evidence",
                "route_status": "dead_letter",
                "allow_active_followup": False,
                "allow_durable_mailbox": True,
                "notes": "dead-letter notify policy",
            }
        )
    return templates


def _normalize_subscription_policy(
    raw: dict[str, Any],
    *,
    session: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = {
        "subscription_id": _clean_text(raw.get("subscription_id")) or f"sub-{uuid.uuid4().hex}",
        "session_id": _clean_text(raw.get("session_id"))
        or (session["session_id"] if session is not None else None),
        "policy_name": _clean_text(raw.get("policy_name")) or "scope_default",
        "is_active": _boolish(raw.get("is_active"), True),
        "priority": int(raw.get("priority") or 100),
        "run_id": _clean_text(raw.get("run_id"))
        or (session.get("run_id") if session is not None and _boolish(session.get("subscribes_same_run"), True) else None),
        "repo_root": _clean_text(raw.get("repo_root"))
        or (session.get("repo_root") if session is not None and _boolish(session.get("subscribes_same_repo"), True) else None),
        "branch": _clean_text(raw.get("branch"))
        or (session.get("branch") if session is not None and _boolish(session.get("subscribes_same_branch"), True) else None),
        "source_role": _clean_text(raw.get("source_role")),
        "target_role": _clean_text(raw.get("target_role"))
        or (session.get("role") if session is not None else None),
        "task_id": _clean_text(raw.get("task_id")),
        "correlation_id": _clean_text(raw.get("correlation_id")),
        "event_type": _clean_text(raw.get("event_type")),
        "message_kind": _clean_text(raw.get("message_kind")),
        "route_status": _clean_text(raw.get("route_status")),
        "allow_active_followup": _boolish(raw.get("allow_active_followup"), True),
        "allow_durable_mailbox": _boolish(raw.get("allow_durable_mailbox"), True),
        "notes": _clean_text(raw.get("notes")),
    }
    if policy["session_id"] is None:
        raise ValueError("session_id is required for subscription policies")
    if policy["priority"] < 0:
        raise ValueError("priority must be non-negative")
    if policy["event_type"] is not None and policy["event_type"] not in EVENT_TYPES:
        raise ValueError("unsupported subscription event_type")
    if policy["message_kind"] is not None and policy["message_kind"] not in MESSAGE_KINDS:
        raise ValueError("unsupported subscription message_kind")
    return policy


def _policy_matches_context(
    policy: dict[str, Any],
    *,
    source_session: dict[str, Any],
    recipient_session: dict[str, Any],
    event: dict[str, Any],
    route_status: str | None = None,
) -> bool:
    if not policy.get("is_active"):
        return False
    if policy.get("session_id") != recipient_session.get("session_id"):
        return False
    matches = {
        "run_id": source_session.get("run_id"),
        "repo_root": source_session.get("repo_root"),
        "branch": source_session.get("branch"),
        "source_role": source_session.get("role"),
        "target_role": recipient_session.get("role"),
        "task_id": _event_task_id(event),
        "correlation_id": _event_correlation_id(event),
        "event_type": event.get("event_type"),
        "message_kind": event.get("message_kind"),
        "route_status": route_status,
    }
    for key, expected in matches.items():
        policy_value = policy.get(key)
        if policy_value is not None and policy_value != expected:
            return False
    return True
RUNTIME_BACKENDS = {"sqlite", "postgres"}
RUNTIME_BACKEND_ENV = "MAT_RUNTIME_BACKEND"
RUNTIME_DATABASE_URL_ENV = "MAT_RUNTIME_DATABASE_URL"
RUNTIME_POSTGRES_DSN_ENV = "MAT_RUNTIME_POSTGRES_DSN"

_SCHEMA_CACHE: dict[Path, dict[str, Any]] = {}


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _boolish(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root(repo_root: str | Path) -> Path:
    return Path(repo_root).resolve()


def runtime_db_path(repo_root: str | Path) -> Path:
    return _repo_root(repo_root) / RUNTIME_DB_REL


def _schema_path(rel: Path) -> Path:
    return rel


def _load_schema(path: Path) -> dict[str, Any]:
    cached = _SCHEMA_CACHE.get(path)
    if cached is not None:
        return cached
    schema = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError(f"schema is not an object: {path}")
    _SCHEMA_CACHE[path] = schema
    return schema


def _schema_type_matches(value: Any, schema_type: str) -> bool:
    if schema_type == "object":
        return isinstance(value, dict)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "null":
        return value is None
    return True


def _validate_schema_node(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    schema_type = schema.get("type")
    if isinstance(schema_type, str) and not _schema_type_matches(value, schema_type):
        errors.append(f"{path}: expected {schema_type}")
        return errors

    if isinstance(schema_type, list) and not any(
        _schema_type_matches(value, item) for item in schema_type if isinstance(item, str)
    ):
        errors.append(f"{path}: expected one of {schema_type}")
        return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']}")
        return errors

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path}: minLength {min_length}")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: invalid date-time")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{path}: minimum {minimum}")

    if isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(value):
                errors.extend(_validate_schema_node(item, items, f"{path}[{index}]"))
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: minItems {min_items}")

    if isinstance(value, dict):
        required = schema.get("required") or []
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required key {key}")

        properties = schema.get("properties") or {}
        for key, subschema in properties.items():
            if key in value and isinstance(subschema, dict):
                errors.extend(_validate_schema_node(value[key], subschema, f"{path}.{key}"))

        additional = schema.get("additionalProperties")
        if additional is False:
            extras = [key for key in value.keys() if key not in properties]
            if extras:
                errors.append(f"{path}: unexpected keys {sorted(extras)}")
        elif isinstance(additional, dict):
            extras = [key for key in value.keys() if key not in properties]
            for key in extras:
                errors.extend(_validate_schema_node(value[key], additional, f"{path}.{key}"))

    return errors


def _validate_against_schema_file(payload: Any, schema_path: Path) -> tuple[bool, list[str]]:
    try:
        schema = _load_schema(schema_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return False, [f"schema_unavailable:{exc!s}"]
    errors = _validate_schema_node(payload, schema)
    return len(errors) == 0, errors


def _allow_new_message_kind(errors: list[str], message_kind: Any) -> list[str]:
    if not isinstance(message_kind, str) or message_kind not in MESSAGE_KINDS:
        return errors
    return [
        error
        for error in errors
        if not error.startswith("$.message_kind: expected one of")
    ]


def validate_event_envelope(envelope: dict[str, Any]) -> tuple[bool, list[str]]:
    public_envelope = dict(envelope)
    public_envelope.pop("route_approval_state", None)
    public_envelope.pop("approval_recorded_at_utc", None)
    ok, errors = _validate_against_schema_file(public_envelope, _schema_path(EVENT_SCHEMA_PATH))
    errors = _allow_new_message_kind(errors, public_envelope.get("message_kind"))
    ok = len(errors) == 0
    payload = public_envelope.get("payload")
    if isinstance(payload, dict):
        transcript_keys = {
            key
            for key in payload.keys()
            if key in {"transcript", "raw_transcript", "transcript_text", "transcript_path"}
        }
        if transcript_keys:
            errors.append(f"payload_contains_raw_transcript_keys:{sorted(transcript_keys)}")
            ok = False
    return len(errors) == 0 and ok, errors


def validate_mailbox_item(item: dict[str, Any]) -> tuple[bool, list[str]]:
    ok, errors = _validate_against_schema_file(item, _schema_path(MAILBOX_SCHEMA_PATH))
    errors = _allow_new_message_kind(errors, item.get("message_kind"))
    return len(errors) == 0, errors


def validate_delivery_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    return _validate_against_schema_file(record, _schema_path(DELIVERY_SCHEMA_PATH))


def validate_outbox_item(item: dict[str, Any]) -> tuple[bool, list[str]]:
    ok, errors = _validate_against_schema_file(item, _schema_path(OUTBOX_SCHEMA_PATH))
    errors = _allow_new_message_kind(errors, item.get("message_kind"))
    return len(errors) == 0, errors


def validate_delivery_attempt(attempt: dict[str, Any]) -> tuple[bool, list[str]]:
    return _validate_against_schema_file(attempt, _schema_path(DELIVERY_ATTEMPT_SCHEMA_PATH))


def _runtime_backend_request() -> str:
    requested = (_clean_text(os.environ.get(RUNTIME_BACKEND_ENV)) or "sqlite").lower()
    return requested if requested in RUNTIME_BACKENDS else "sqlite"


def runtime_storage_status(repo_root: str | Path) -> dict[str, Any]:
    db_path = runtime_db_path(repo_root)
    requested = _runtime_backend_request()
    postgres_url = _clean_text(os.environ.get(RUNTIME_DATABASE_URL_ENV))
    postgres_dsn = _clean_text(os.environ.get(RUNTIME_POSTGRES_DSN_ENV))
    backend_mode = "sqlite"
    backend_notes: list[str] = []
    backend_available = True
    if requested == "postgres":
        backend_available = False
        if postgres_url or postgres_dsn:
            backend_notes.append("postgres_requested_but_runtime_still_falls_back_to_sqlite")
            backend_notes.append("postgres_schema_artifact_present")
        else:
            backend_notes.append("postgres_requested_but_no_database_url")
        backend_notes.append("falling_back_to_sqlite_for_local_validation")
    schema_exists = db_path.exists()
    health = "healthy" if schema_exists else "missing_store"
    return {
        "ok": True,
        "requested_backend": requested,
        "backend_mode": backend_mode,
        "backend_available": backend_available,
        "store_path": str(db_path),
        "store_exists": schema_exists,
        "health": health,
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "notes": backend_notes,
    }


def validate_advisor_task_session_summary(summary: dict[str, Any]) -> tuple[bool, list[str]]:
    return _validate_against_schema_file(summary, _schema_path(SUMMARY_SCHEMA_PATH))


def _connect(repo_root: str | Path) -> sqlite3.Connection:
    db_path = runtime_db_path(repo_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_db(conn)
    return conn


def _ensure_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            session_kind TEXT NOT NULL,
            role TEXT NOT NULL,
            run_id TEXT,
            repo_root TEXT,
            branch TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            subscribes_same_run INTEGER NOT NULL DEFAULT 1,
            subscribes_same_repo INTEGER NOT NULL DEFAULT 1,
            subscribes_same_branch INTEGER NOT NULL DEFAULT 1,
            summary_schema_version TEXT,
            summary_json TEXT,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subscription_policies (
            subscription_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            policy_name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            priority INTEGER NOT NULL DEFAULT 100,
            run_id TEXT,
            repo_root TEXT,
            branch TEXT,
            source_role TEXT,
            target_role TEXT,
            task_id TEXT,
            correlation_id TEXT,
            event_type TEXT,
            message_kind TEXT,
            route_status TEXT,
            allow_active_followup INTEGER NOT NULL DEFAULT 1,
            allow_durable_mailbox INTEGER NOT NULL DEFAULT 1,
            notes TEXT,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            schema_version TEXT NOT NULL,
            event_type TEXT NOT NULL,
            message_kind TEXT NOT NULL,
            session_id TEXT NOT NULL,
            session_kind TEXT NOT NULL,
            role TEXT NOT NULL,
            run_id TEXT,
            repo_root TEXT,
            branch TEXT,
            target_selector_type TEXT NOT NULL,
            target_selector_value TEXT,
            target_allow_followup INTEGER NOT NULL DEFAULT 1,
            payload_json TEXT NOT NULL,
            requires_approval INTEGER NOT NULL DEFAULT 0,
            approval_state TEXT NOT NULL,
            delivery_mode TEXT NOT NULL,
            followup_message TEXT,
            created_at_utc TEXT NOT NULL,
            route_status TEXT,
            route_summary_json TEXT,
            raw_envelope_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS mailbox_items (
            mailbox_item_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            event_id TEXT NOT NULL,
            source_session_id TEXT NOT NULL,
            recipient_session_id TEXT NOT NULL,
            recipient_session_kind TEXT NOT NULL,
            recipient_role TEXT NOT NULL,
            run_id TEXT,
            repo_root TEXT,
            branch TEXT,
            event_type TEXT NOT NULL,
            message_kind TEXT NOT NULL,
            target_selector_type TEXT NOT NULL,
            target_selector_value TEXT,
            status TEXT NOT NULL,
            delivery_mode TEXT NOT NULL,
            approval_state TEXT NOT NULL,
            followup_message TEXT,
            route_reason TEXT,
            payload_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            approval_recorded_at_utc TEXT,
            delivered_at_utc TEXT,
            acked_at_utc TEXT,
            acked_by_session_id TEXT,
            ack_note TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS outbox_items (
            outbox_item_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            event_id TEXT NOT NULL,
            source_session_id TEXT NOT NULL,
            recipient_session_id TEXT NOT NULL,
            recipient_session_kind TEXT NOT NULL,
            recipient_role TEXT NOT NULL,
            run_id TEXT,
            repo_root TEXT,
            branch TEXT,
            event_type TEXT NOT NULL,
            message_kind TEXT NOT NULL,
            target_selector_type TEXT NOT NULL,
            target_selector_value TEXT,
            status TEXT NOT NULL,
            delivery_mode TEXT NOT NULL,
            approval_state TEXT NOT NULL,
            route_reason TEXT,
            payload_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            last_attempt_at_utc TEXT,
            next_attempt_at_utc TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_error_json TEXT,
            dead_letter_reason TEXT,
            dead_lettered_at_utc TEXT,
            approval_recorded_at_utc TEXT,
            settled_at_utc TEXT,
            FOREIGN KEY(event_id) REFERENCES events(event_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS delivery_records (
            delivery_record_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            mailbox_item_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            recipient_session_id TEXT NOT NULL,
            delivery_status TEXT NOT NULL,
            delivery_mode TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            detail_json TEXT NOT NULL,
            FOREIGN KEY(mailbox_item_id) REFERENCES mailbox_items(mailbox_item_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS delivery_attempts (
            delivery_attempt_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            outbox_item_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            recipient_session_id TEXT NOT NULL,
            mailbox_item_id TEXT,
            attempt_number INTEGER NOT NULL,
            delivery_status TEXT NOT NULL,
            delivery_mode TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            detail_json TEXT NOT NULL,
            error_json TEXT,
            FOREIGN KEY(outbox_item_id) REFERENCES outbox_items(outbox_item_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_events_session_created
            ON events(session_id, created_at_utc DESC);
        CREATE INDEX IF NOT EXISTS idx_subscription_policies_session_active_priority
            ON subscription_policies(session_id, is_active, priority DESC, created_at_utc DESC);
        CREATE INDEX IF NOT EXISTS idx_subscription_policies_lookup
            ON subscription_policies(run_id, repo_root, branch, source_role, target_role, event_type, message_kind, route_status);
        CREATE INDEX IF NOT EXISTS idx_mailbox_session_status
            ON mailbox_items(recipient_session_id, status, created_at_utc DESC);
        CREATE INDEX IF NOT EXISTS idx_outbox_session_status
            ON outbox_items(recipient_session_id, status, created_at_utc DESC);
        CREATE INDEX IF NOT EXISTS idx_delivery_attempts_session_created
            ON delivery_attempts(recipient_session_id, created_at_utc DESC);
        """
    )


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for key in (
        "is_active",
        "subscribes_same_run",
        "subscribes_same_repo",
        "subscribes_same_branch",
        "target_allow_followup",
        "requires_approval",
    ):
        if key in data and data[key] is not None:
            data[key] = bool(data[key])
    return data


def _current_branch(repo_root: str | Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=_repo_root(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    branch = proc.stdout.strip()
    return branch or None


def _resolve_trace_run_id(repo_root: str | Path) -> str | None:
    for key in ("CURSOR_AGENT_TRACE_RUN_ID", "CURSOR_ORCHESTRATION_TRACE_RUN_ID"):
        raw = _clean_text(os.environ.get(key))
        if raw:
            return raw
    try:
        mod_path = HOOKS_DIR / "utils" / "spawn_trace.py"
        spec = importlib.util.spec_from_file_location("runtime_messaging_spawn_trace", mod_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            resolver = getattr(mod, "resolve_trace_run_id", None)
            if callable(resolver):
                return resolver(_repo_root(repo_root))
    except Exception:
        pass
    return None


def _normalize_session(raw: dict[str, Any], *, repo_root: str | Path) -> dict[str, Any]:
    session_id = _clean_text(raw.get("session_id")) or _clean_text(raw.get("id"))
    if not session_id:
        raise ValueError("session_id is required")
    session_kind = _clean_text(raw.get("session_kind")) or "task"
    if session_kind not in SESSION_KINDS:
        raise ValueError("unsupported session_kind")
    role = _clean_text(raw.get("role")) or "unknown"
    run_id = _clean_text(raw.get("run_id")) or _resolve_trace_run_id(repo_root) or session_id
    repo = _clean_text(raw.get("repo_root")) or str(_repo_root(repo_root))
    branch = _clean_text(raw.get("branch")) or _current_branch(repo_root)
    return {
        "session_id": session_id,
        "session_kind": session_kind,
        "role": role,
        "run_id": run_id,
        "repo_root": repo,
        "branch": branch,
        "is_active": _boolish(raw.get("is_active"), True),
        "subscribes_same_run": _boolish(raw.get("subscribes_same_run"), True),
        "subscribes_same_repo": _boolish(raw.get("subscribes_same_repo"), True),
        "subscribes_same_branch": _boolish(raw.get("subscribes_same_branch"), True),
        "summary": raw.get("summary") if isinstance(raw.get("summary"), dict) else None,
    }


def _normalize_target(raw: dict[str, Any]) -> dict[str, Any]:
    selector_type = _clean_text(raw.get("selector_type")) or "same_run"
    if selector_type not in TARGET_SELECTOR_TYPES:
        raise ValueError("unsupported target selector_type")
    selector_value = _clean_text(raw.get("selector_value"))
    allow_followup = _boolish(raw.get("allow_followup"), True)
    return {
        "selector_type": selector_type,
        "selector_value": selector_value,
        "allow_followup": allow_followup,
    }


def _stable_idempotency_key(envelope: dict[str, Any]) -> str:
    payload = {
        "event_type": envelope["event_type"],
        "message_kind": envelope["message_kind"],
        "session": envelope["session"],
        "target": envelope["target"],
        "payload": envelope["payload"],
        "requires_approval": envelope["requires_approval"],
        "approval_state": envelope["approval_state"],
        "delivery_mode": envelope["delivery_mode"],
        "followup_message": envelope["followup_message"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _normalize_envelope(raw: dict[str, Any], *, repo_root: str | Path) -> dict[str, Any]:
    session = _normalize_session(raw.get("session") or raw.get("source_session") or raw, repo_root=repo_root)
    session.pop("summary", None)
    target = _normalize_target(raw.get("target") or {})
    payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
    event_type = _clean_text(raw.get("event_type")) or "message"
    if event_type not in EVENT_TYPES:
        raise ValueError("unsupported event_type")
    message_kind = _clean_text(raw.get("message_kind")) or (
        "delivery_evidence" if event_type == "delivery" else "summary"
    )
    if message_kind not in MESSAGE_KINDS:
        raise ValueError("unsupported message_kind")
    requires_approval = _boolish(raw.get("requires_approval"), False)
    approval_state = _clean_text(raw.get("approval_state")) or (
        "pending" if requires_approval else "not_required"
    )
    if approval_state not in APPROVAL_STATES:
        raise ValueError("unsupported approval_state")
    approval_recorded_at_utc = _clean_text(raw.get("approval_recorded_at_utc"))
    route_approval_state = approval_state
    if requires_approval:
        if approval_state == "rejected":
            route_approval_state = "rejected"
        elif approval_recorded_at_utc and approval_state == "approved":
            route_approval_state = "approved"
        else:
            route_approval_state = "pending"
    else:
        route_approval_state = "not_required"
    delivery_mode = _clean_text(raw.get("delivery_mode"))
    if not delivery_mode:
        delivery_mode = "durable_mailbox" if requires_approval else "active_followup"
    if delivery_mode not in DELIVERY_MODES:
        raise ValueError("unsupported delivery_mode")
    followup_message = _clean_text(raw.get("followup_message")) or _clean_text(
        payload.get("followup_message")
    ) or _clean_text(payload.get("summary"))
    envelope = {
        "schema_version": _clean_text(raw.get("schema_version")) or RUNTIME_SCHEMA_VERSION,
        "event_id": _clean_text(raw.get("event_id")) or f"runtime-{uuid.uuid4().hex}",
        "event_type": event_type,
        "message_kind": message_kind,
        "session": session,
        "target": target,
        "payload": payload,
        "created_at_utc": _clean_text(raw.get("created_at_utc")) or _now(),
        "idempotency_key": _clean_text(raw.get("idempotency_key")) or "",
        "requires_approval": requires_approval,
        "approval_state": approval_state,
        "route_approval_state": route_approval_state,
        "approval_recorded_at_utc": approval_recorded_at_utc,
        "delivery_mode": delivery_mode,
        "followup_message": followup_message,
    }
    if not envelope["idempotency_key"]:
        envelope["idempotency_key"] = _stable_idempotency_key(envelope)
    return envelope


def _session_row(conn: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
    return _row_to_dict(row)


def _subscription_row(conn: sqlite3.Connection, subscription_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM subscription_policies WHERE subscription_id = ?",
        (subscription_id,),
    ).fetchone()
    return _row_to_dict(row)


def _session_subscription_rows(conn: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM subscription_policies
        WHERE session_id = ?
        ORDER BY priority DESC, created_at_utc DESC
        """,
        (session_id,),
    ).fetchall()
    return [_row_to_dict(row) for row in rows if row is not None]


def upsert_subscription_policy(
    repo_root: str | Path,
    raw_policy: dict[str, Any],
    *,
    session: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        policy = _normalize_subscription_policy(raw_policy, session=session)
        existing = _subscription_row(conn, policy["subscription_id"])
        if existing is None:
            conn.execute(
                """
                INSERT INTO subscription_policies (
                    subscription_id, session_id, policy_name, is_active, priority,
                    run_id, repo_root, branch, source_role, target_role, task_id,
                    correlation_id, event_type, message_kind, route_status,
                    allow_active_followup, allow_durable_mailbox, notes,
                    created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    policy["subscription_id"],
                    policy["session_id"],
                    policy["policy_name"],
                    1 if policy["is_active"] else 0,
                    policy["priority"],
                    policy["run_id"],
                    policy["repo_root"],
                    policy["branch"],
                    policy["source_role"],
                    policy["target_role"],
                    policy["task_id"],
                    policy["correlation_id"],
                    policy["event_type"],
                    policy["message_kind"],
                    policy["route_status"],
                    1 if policy["allow_active_followup"] else 0,
                    1 if policy["allow_durable_mailbox"] else 0,
                    policy["notes"],
                    _now(),
                    _now(),
                ),
            )
        else:
            conn.execute(
                """
                UPDATE subscription_policies SET
                    session_id = ?,
                    policy_name = ?,
                    is_active = ?,
                    priority = ?,
                    run_id = ?,
                    repo_root = ?,
                    branch = ?,
                    source_role = ?,
                    target_role = ?,
                    task_id = ?,
                    correlation_id = ?,
                    event_type = ?,
                    message_kind = ?,
                    route_status = ?,
                    allow_active_followup = ?,
                    allow_durable_mailbox = ?,
                    notes = ?,
                    updated_at_utc = ?
                WHERE subscription_id = ?
                """,
                (
                    policy["session_id"],
                    policy["policy_name"],
                    1 if policy["is_active"] else 0,
                    policy["priority"],
                    policy["run_id"],
                    policy["repo_root"],
                    policy["branch"],
                    policy["source_role"],
                    policy["target_role"],
                    policy["task_id"],
                    policy["correlation_id"],
                    policy["event_type"],
                    policy["message_kind"],
                    policy["route_status"],
                    1 if policy["allow_active_followup"] else 0,
                    1 if policy["allow_durable_mailbox"] else 0,
                    policy["notes"],
                    _now(),
                    policy["subscription_id"],
                ),
            )
        conn.commit()
        return {"ok": True, "subscription_policy": _subscription_row(conn, policy["subscription_id"])}
    except (sqlite3.Error, ValueError) as exc:
        return {"ok": False, "errors": [f"subscription_policy_write_failed:{exc!s}"], "subscription_policy": None}
    finally:
        conn.close()


def sync_session_subscription_policies(repo_root: str | Path, session: dict[str, Any]) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        normalized = _normalize_session(session, repo_root=repo_root)
        session_row = _session_row(conn, normalized["session_id"])
        if session_row is None:
            return {"ok": False, "errors": ["session_not_found"], "session_id": normalized["session_id"]}
        templates = _default_subscription_templates(session_row)
        explicit = session.get("subscription_policies") or session.get("subscriptions") or []
        if isinstance(explicit, list):
            templates.extend(explicit)
        results = []
        for index, template in enumerate(templates):
            raw_policy = dict(template)
            raw_policy.setdefault("subscription_id", f"{normalized['session_id']}-policy-{index}")
            raw_policy.setdefault("session_id", normalized["session_id"])
            raw_policy.setdefault("target_role", normalized.get("role"))
            result = upsert_subscription_policy(repo_root, raw_policy, session=session_row)
            results.append(result)
        return {"ok": True, "results": results}
    finally:
        conn.close()


def list_subscription_policies(
    repo_root: str | Path,
    *,
    session_id: str | None = None,
    active_only: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if active_only:
            clauses.append("is_active = 1")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM subscription_policies {where} ORDER BY priority DESC, created_at_utc DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        items = [_row_to_dict(row) for row in rows if row is not None]
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def _merge_route_summary(
    repo_root: str | Path,
    event_id: str,
    patch: dict[str, Any],
    *,
    route_status: str | None = None,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        row = conn.execute(
            "SELECT route_status, route_summary_json FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            return {"ok": False, "errors": ["event_not_found"], "route_summary": None}
        current = row["route_summary_json"]
        summary = json.loads(current) if current else {}
        if not isinstance(summary, dict):
            summary = {}
        summary.update(patch)
        if route_status is not None:
            summary["route_status"] = route_status
        conn.execute(
            """
            UPDATE events
            SET route_status = COALESCE(?, route_status),
                route_summary_json = ?
            WHERE event_id = ?
            """,
            (route_status, json.dumps(summary, sort_keys=True), event_id),
        )
        conn.commit()
        return {"ok": True, "route_summary": summary}
    finally:
        conn.close()


def register_session(repo_root: str | Path, raw_session: dict[str, Any]) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        session = _normalize_session(raw_session, repo_root=repo_root)
        summary = session.pop("summary")
        summary_validation: tuple[bool, list[str]] | None = None
        summary_json = None
        summary_schema_version = None
        if summary is not None:
            summary_validation = validate_advisor_task_session_summary(summary)
            if summary_validation[0]:
                summary_json = json.dumps(summary, sort_keys=True)
                summary_schema_version = str(summary.get("schema_version") or "")
        existing = _session_row(conn, session["session_id"])
        if existing is None:
            conn.execute(
                """
                INSERT INTO sessions (
                    session_id, session_kind, role, run_id, repo_root, branch, is_active,
                    subscribes_same_run, subscribes_same_repo, subscribes_same_branch,
                    summary_schema_version, summary_json, created_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["session_id"],
                    session["session_kind"],
                    session["role"],
                    session["run_id"],
                    session["repo_root"],
                    session["branch"],
                    1 if session["is_active"] else 0,
                    1 if session["subscribes_same_run"] else 0,
                    1 if session["subscribes_same_repo"] else 0,
                    1 if session["subscribes_same_branch"] else 0,
                    summary_schema_version,
                    summary_json,
                    _now(),
                    _now(),
                ),
            )
        else:
            conn.execute(
                """
                UPDATE sessions SET
                    session_kind = ?,
                    role = ?,
                    run_id = ?,
                    repo_root = ?,
                    branch = ?,
                    is_active = ?,
                    subscribes_same_run = ?,
                    subscribes_same_repo = ?,
                    subscribes_same_branch = ?,
                    summary_schema_version = COALESCE(?, summary_schema_version),
                    summary_json = COALESCE(?, summary_json),
                    updated_at_utc = ?
                WHERE session_id = ?
                """,
                (
                    session["session_kind"],
                    session["role"],
                    session["run_id"],
                    session["repo_root"],
                    session["branch"],
                    1 if session["is_active"] else 0,
                    1 if session["subscribes_same_run"] else 0,
                    1 if session["subscribes_same_repo"] else 0,
                    1 if session["subscribes_same_branch"] else 0,
                    summary_schema_version,
                    summary_json,
                    _now(),
                    session["session_id"],
                ),
            )
        conn.commit()
        stored = _session_row(conn, session["session_id"])
        out = {"ok": True, "session": stored, "summary_validation": summary_validation}
        policy_sync_input = dict(raw_session)
        policy_sync_input.update(
            {
                "session_id": session["session_id"],
                "session_kind": session["session_kind"],
                "role": session["role"],
                "run_id": session["run_id"],
                "repo_root": session["repo_root"],
                "branch": session["branch"],
                "is_active": session["is_active"],
                "subscribes_same_run": session["subscribes_same_run"],
                "subscribes_same_repo": session["subscribes_same_repo"],
                "subscribes_same_branch": session["subscribes_same_branch"],
            }
        )
        policy_sync = sync_session_subscription_policies(repo_root, policy_sync_input)
        out["subscription_policy_sync"] = policy_sync
        return out
    finally:
        conn.close()


def _insert_event(conn: sqlite3.Connection, envelope: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    existing = conn.execute(
        "SELECT * FROM events WHERE idempotency_key = ?",
        (envelope["idempotency_key"],),
    ).fetchone()
    if existing is not None:
        return _row_to_dict(existing) or {}, False
    session = envelope["session"]
    conn.execute(
        """
        INSERT INTO events (
            event_id, idempotency_key, schema_version, event_type, message_kind, session_id,
            session_kind, role, run_id, repo_root, branch, target_selector_type,
            target_selector_value, target_allow_followup, payload_json, requires_approval,
            approval_state, delivery_mode, followup_message, created_at_utc, route_status,
            route_summary_json, raw_envelope_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            envelope["event_id"],
            envelope["idempotency_key"],
            envelope["schema_version"],
            envelope["event_type"],
            envelope["message_kind"],
            session["session_id"],
            session["session_kind"],
            session["role"],
            session["run_id"],
            session["repo_root"],
            session["branch"],
            envelope["target"]["selector_type"],
            envelope["target"]["selector_value"],
            1 if envelope["target"]["allow_followup"] else 0,
            json.dumps(envelope["payload"], sort_keys=True),
            1 if envelope["requires_approval"] else 0,
            envelope.get("route_approval_state", envelope["approval_state"]),
            envelope["delivery_mode"],
            envelope["followup_message"],
            envelope["created_at_utc"],
            None,
            None,
            json.dumps(envelope, sort_keys=True, default=str),
        ),
    )
    row = conn.execute("SELECT * FROM events WHERE event_id = ?", (envelope["event_id"],)).fetchone()
    return _row_to_dict(row) or {}, True


def publish_event(
    repo_root: str | Path,
    raw_envelope: dict[str, Any],
    *,
    route: bool = True,
) -> dict[str, Any]:
    try:
        envelope = _normalize_envelope(raw_envelope, repo_root=repo_root)
    except Exception as exc:  # noqa: BLE001 - fail open for callers
        return {
            "ok": False,
            "validation_ok": False,
            "validation_errors": [f"normalize_failed:{exc!s}"],
            "event_id": None,
            "route_ok": False,
            "route_warnings": [],
        }

    valid, validation_errors = validate_event_envelope(envelope)
    if not valid:
        return {
            "ok": False,
            "validation_ok": False,
            "validation_errors": validation_errors,
            "event_id": envelope["event_id"],
            "route_ok": False,
            "route_warnings": [],
        }

    conn = _connect(repo_root)
    try:
        register_session(repo_root, envelope["session"])
        event_row, inserted = _insert_event(conn, envelope)
        conn.commit()
    finally:
        conn.close()

    route_result = {"ok": True, "route_status": "not_requested", "warnings": [], "mailbox_item_ids": []}
    if route:
        route_result = route_event(repo_root, envelope["event_id"])
    return {
        "ok": True,
        "validation_ok": True,
        "validation_errors": [],
        "event_id": envelope["event_id"],
        "inserted": inserted,
        "event": event_row,
        "route_ok": bool(route_result.get("ok")),
        "route_result": route_result,
    }


def _candidate_sessions(
    conn: sqlite3.Connection, envelope: dict[str, Any]
) -> list[dict[str, Any]]:
    selector = envelope["target"]["selector_type"]
    value = envelope["target"]["selector_value"]
    source_session_id = envelope["session"]["session_id"]
    rows: list[dict[str, Any]] = []
    if selector == "session_id":
        row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (value,)).fetchone()
        if row is not None:
            rows.append(_row_to_dict(row) or {})
        return rows

    if selector == "same_run":
        query = "SELECT * FROM sessions WHERE run_id = ? AND subscribes_same_run = 1"
        params: Iterable[Any] = (envelope["session"]["run_id"],)
    elif selector == "same_repo":
        query = "SELECT * FROM sessions WHERE repo_root = ? AND subscribes_same_repo = 1"
        params = (envelope["session"]["repo_root"],)
    elif selector == "same_branch":
        query = "SELECT * FROM sessions WHERE branch = ? AND subscribes_same_branch = 1"
        params = (envelope["session"]["branch"],)
    else:
        return rows

    for row in conn.execute(query, params).fetchall():
        candidate = _row_to_dict(row)
        if candidate is None:
            continue
        if candidate["session_id"] == source_session_id and selector != "session_id":
            continue
        rows.append(candidate)
    return rows


def _legacy_subscription_policy(recipient: dict[str, Any], envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "subscription_id": f"legacy:{recipient['session_id']}",
        "session_id": recipient["session_id"],
        "policy_name": "legacy_scope_fallback",
        "is_active": True,
        "priority": 0,
        "run_id": envelope["session"].get("run_id") if recipient.get("subscribes_same_run") else None,
        "repo_root": envelope["session"].get("repo_root") if recipient.get("subscribes_same_repo") else None,
        "branch": envelope["session"].get("branch") if recipient.get("subscribes_same_branch") else None,
        "source_role": None,
        "target_role": recipient.get("role"),
        "task_id": _event_task_id(envelope),
        "correlation_id": _event_correlation_id(envelope),
        "event_type": envelope.get("event_type"),
        "message_kind": envelope.get("message_kind"),
        "route_status": None,
        "allow_active_followup": True,
        "allow_durable_mailbox": True,
        "notes": "legacy session scope fallback",
    }


def _matching_subscription_policies(
    conn: sqlite3.Connection,
    envelope: dict[str, Any],
    recipient: dict[str, Any],
    *,
    route_status: str | None = None,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM subscription_policies
        WHERE session_id = ? AND is_active = 1
        ORDER BY priority DESC, created_at_utc DESC
        """,
        (recipient["session_id"],),
    ).fetchall()
    policies = [_row_to_dict(row) for row in rows if row is not None]
    matched = [
        policy
        for policy in policies
        if policy is not None
        and _policy_matches_context(
            policy,
            source_session=envelope["session"],
            recipient_session=recipient,
            event=envelope,
            route_status=route_status,
        )
    ]
    if matched:
        return matched
    return [_legacy_subscription_policy(recipient, envelope)]


def _routing_match_summary(
    conn: sqlite3.Connection,
    envelope: dict[str, Any],
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for recipient in _candidate_sessions(conn, envelope):
        policies = _matching_subscription_policies(conn, envelope, recipient)
        if not policies:
            continue
        chosen = policies[0]
        delivery_mode = "active_followup" if bool(recipient.get("is_active")) and chosen.get("allow_active_followup") else "durable_mailbox"
        if envelope.get("route_approval_state") in {"pending", "rejected"}:
            delivery_mode = "durable_mailbox"
        if not chosen.get("allow_durable_mailbox") and delivery_mode == "durable_mailbox":
            delivery_mode = "suppressed"
        matches.append(
            {
                "recipient_session": recipient,
                "recipient_session_id": recipient["session_id"],
                "recipient_role": recipient.get("role"),
                "recipient_session_kind": recipient.get("session_kind"),
                "subscription_policy_ids": [policy["subscription_id"] for policy in policies],
                "subscription_policy_names": [policy["policy_name"] for policy in policies],
                "matched_subscription_policy": chosen,
                "delivery_mode": delivery_mode,
                "active_session": bool(recipient.get("is_active")),
                "source_role": envelope["session"].get("role"),
                "route_profile": _routing_profile(
                    envelope["message_kind"],
                    requires_approval=bool(envelope["requires_approval"]),
                    approval_state=str(envelope["approval_state"]),
                ),
                "task_id": _event_task_id(envelope),
                "correlation_id": _event_correlation_id(envelope),
                "event_type": envelope.get("event_type"),
                "message_kind": envelope.get("message_kind"),
            }
        )
    return matches


def _mailbox_payload(
    envelope: dict[str, Any],
    recipient: dict[str, Any],
    *,
    delivery_mode: str,
    status: str,
    route_reason: str,
) -> dict[str, Any]:
    followup = envelope["followup_message"]
    if not followup:
        followup = str(envelope["payload"].get("summary") or envelope["message_kind"])
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "mailbox_item_id": f"mailbox-{uuid.uuid4().hex}",
        "event_id": envelope["event_id"],
        "source_session_id": envelope["session"]["session_id"],
        "recipient_session_id": recipient["session_id"],
        "recipient_session_kind": recipient["session_kind"],
        "recipient_role": recipient["role"],
        "run_id": recipient.get("run_id"),
        "repo_root": recipient.get("repo_root"),
        "branch": recipient.get("branch"),
        "event_type": envelope["event_type"],
        "message_kind": envelope["message_kind"],
        "target_selector_type": envelope["target"]["selector_type"],
        "target_selector_value": envelope["target"]["selector_value"],
        "status": _canonical_outbox_status(status) or "queued",
        "delivery_mode": delivery_mode,
        "approval_state": envelope.get("route_approval_state", envelope["approval_state"]),
        "approval_recorded_at_utc": envelope.get("approval_recorded_at_utc"),
        "followup_message": followup if delivery_mode == "active_followup" else None,
        "route_reason": route_reason,
        "payload_json": json.dumps(envelope["payload"], sort_keys=True),
        "created_at_utc": _now(),
        "delivered_at_utc": _now() if delivery_mode == "active_followup" else None,
        "acked_at_utc": None,
        "acked_by_session_id": None,
        "ack_note": None,
        "idempotency_key": f"{envelope['event_id']}:{recipient['session_id']}:mailbox",
    }


def _delivery_payload(mailbox_item: dict[str, Any], delivery_status: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "delivery_record_id": f"delivery-{uuid.uuid4().hex}",
        "mailbox_item_id": mailbox_item["mailbox_item_id"],
        "event_id": mailbox_item["event_id"],
        "recipient_session_id": mailbox_item["recipient_session_id"],
        "delivery_status": delivery_status,
        "delivery_mode": mailbox_item["delivery_mode"],
        "created_at_utc": _now(),
        "detail_json": json.dumps(detail, sort_keys=True),
        "idempotency_key": f"{mailbox_item['mailbox_item_id']}:{delivery_status}",
    }


def _outbox_payload(
    envelope: dict[str, Any],
    recipient: dict[str, Any],
    *,
    delivery_mode: str,
    status: str,
    route_reason: str,
) -> dict[str, Any]:
    return {
        "outbox_item_id": f"outbox-{uuid.uuid4().hex}",
        "schema_version": RUNTIME_SCHEMA_VERSION,
        "event_id": envelope["event_id"],
        "source_session_id": envelope["session"]["session_id"],
        "recipient_session_id": recipient["session_id"],
        "recipient_session_kind": recipient["session_kind"],
        "recipient_role": recipient["role"],
        "run_id": recipient.get("run_id"),
        "repo_root": recipient.get("repo_root"),
        "branch": recipient.get("branch"),
        "event_type": envelope["event_type"],
        "message_kind": envelope["message_kind"],
        "target_selector_type": envelope["target"]["selector_type"],
        "target_selector_value": envelope["target"]["selector_value"],
        "status": status,
        "delivery_mode": delivery_mode,
        "approval_state": envelope.get("route_approval_state", envelope["approval_state"]),
        "approval_recorded_at_utc": envelope.get("approval_recorded_at_utc"),
        "route_reason": route_reason,
        "payload_json": json.dumps(envelope["payload"], sort_keys=True),
        "created_at_utc": _now(),
        "last_attempt_at_utc": None,
        "next_attempt_at_utc": None,
        "attempt_count": 0,
        "last_error_json": None,
        "dead_letter_reason": None,
        "dead_lettered_at_utc": None,
        "settled_at_utc": None,
        "idempotency_key": f"{envelope['event_id']}:{recipient['session_id']}:outbox",
    }


def _delivery_attempt_payload(
    outbox_item: dict[str, Any],
    *,
    mailbox_item_id: str | None,
    delivery_status: str,
    detail: dict[str, Any],
    attempt_number: int,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "delivery_attempt_id": f"attempt-{uuid.uuid4().hex}",
        "idempotency_key": f"{outbox_item['outbox_item_id']}:{attempt_number}:{delivery_status}",
        "outbox_item_id": outbox_item["outbox_item_id"],
        "event_id": outbox_item["event_id"],
        "recipient_session_id": outbox_item["recipient_session_id"],
        "mailbox_item_id": mailbox_item_id,
        "attempt_number": attempt_number,
        "delivery_status": delivery_status,
        "delivery_mode": outbox_item["delivery_mode"],
        "created_at_utc": _now(),
        "detail_json": json.dumps(detail, sort_keys=True),
        "error_json": error,
    }


def enqueue_mailbox_item(repo_root: str | Path, mailbox_item: dict[str, Any]) -> dict[str, Any]:
    valid, errors = validate_mailbox_item(mailbox_item)
    if not valid:
        return {"ok": False, "validation_errors": errors, "mailbox_item": mailbox_item}
    conn = _connect(repo_root)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO mailbox_items (
                mailbox_item_id, idempotency_key, event_id, source_session_id,
                recipient_session_id, recipient_session_kind, recipient_role, run_id,
                repo_root, branch, event_type, message_kind, target_selector_type,
                target_selector_value, status, delivery_mode, approval_state,
                approval_recorded_at_utc, followup_message, route_reason, payload_json,
                created_at_utc, delivered_at_utc, acked_at_utc, acked_by_session_id, ack_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mailbox_item["mailbox_item_id"],
                mailbox_item["idempotency_key"],
                mailbox_item["event_id"],
                mailbox_item["source_session_id"],
                mailbox_item["recipient_session_id"],
                mailbox_item["recipient_session_kind"],
                mailbox_item["recipient_role"],
                mailbox_item["run_id"],
                mailbox_item["repo_root"],
                mailbox_item["branch"],
                mailbox_item["event_type"],
                mailbox_item["message_kind"],
                mailbox_item["target_selector_type"],
                mailbox_item["target_selector_value"],
                mailbox_item["status"],
                mailbox_item["delivery_mode"],
                mailbox_item["approval_state"],
                mailbox_item["approval_recorded_at_utc"],
                mailbox_item["followup_message"],
                mailbox_item["route_reason"],
                mailbox_item["payload_json"],
                mailbox_item["created_at_utc"],
                mailbox_item["delivered_at_utc"],
                mailbox_item["acked_at_utc"],
                mailbox_item["acked_by_session_id"],
                mailbox_item["ack_note"],
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM mailbox_items WHERE idempotency_key = ?",
            (mailbox_item["idempotency_key"],),
        ).fetchone()
        stored = _row_to_dict(row) or mailbox_item
        return {"ok": True, "created": row is not None, "mailbox_item": stored}
    except sqlite3.Error as exc:
        return {"ok": False, "errors": [f"mailbox_write_failed:{exc!s}"], "mailbox_item": mailbox_item}
    finally:
        conn.close()


def enqueue_outbox_item(repo_root: str | Path, outbox_item: dict[str, Any]) -> dict[str, Any]:
    valid, errors = validate_outbox_item(outbox_item)
    if not valid:
        return {"ok": False, "validation_errors": errors, "outbox_item": outbox_item}
    conn = _connect(repo_root)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO outbox_items (
                outbox_item_id, idempotency_key, event_id, source_session_id,
                recipient_session_id, recipient_session_kind, recipient_role, run_id,
                repo_root, branch, event_type, message_kind, target_selector_type,
                target_selector_value, status, delivery_mode, approval_state,
                approval_recorded_at_utc, route_reason, payload_json, created_at_utc,
                last_attempt_at_utc, next_attempt_at_utc, attempt_count, last_error_json,
                dead_letter_reason, dead_lettered_at_utc, settled_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                outbox_item["outbox_item_id"],
                outbox_item["idempotency_key"],
                outbox_item["event_id"],
                outbox_item["source_session_id"],
                outbox_item["recipient_session_id"],
                outbox_item["recipient_session_kind"],
                outbox_item["recipient_role"],
                outbox_item["run_id"],
                outbox_item["repo_root"],
                outbox_item["branch"],
                outbox_item["event_type"],
                outbox_item["message_kind"],
                outbox_item["target_selector_type"],
                outbox_item["target_selector_value"],
                outbox_item["status"],
                outbox_item["delivery_mode"],
                outbox_item["approval_state"],
                outbox_item["approval_recorded_at_utc"],
                outbox_item["route_reason"],
                outbox_item["payload_json"],
                outbox_item["created_at_utc"],
                outbox_item["last_attempt_at_utc"],
                outbox_item["next_attempt_at_utc"],
                outbox_item["attempt_count"],
                outbox_item["last_error_json"],
                outbox_item["dead_letter_reason"],
                outbox_item["dead_lettered_at_utc"],
                outbox_item["settled_at_utc"],
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM outbox_items WHERE idempotency_key = ?",
            (outbox_item["idempotency_key"],),
        ).fetchone()
        stored = _row_to_dict(row) or outbox_item
        return {"ok": True, "created": row is not None, "outbox_item": stored}
    except sqlite3.Error as exc:
        return {"ok": False, "errors": [f"outbox_write_failed:{exc!s}"], "outbox_item": outbox_item}
    finally:
        conn.close()


def _insert_delivery_record(repo_root: str | Path, delivery_record: dict[str, Any]) -> dict[str, Any]:
    valid, errors = validate_delivery_record(delivery_record)
    if not valid:
        return {"ok": False, "validation_errors": errors, "delivery_record": delivery_record}
    conn = _connect(repo_root)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO delivery_records (
                delivery_record_id, idempotency_key, mailbox_item_id, event_id,
                recipient_session_id, delivery_status, delivery_mode, created_at_utc,
                detail_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                delivery_record["delivery_record_id"],
                delivery_record["idempotency_key"],
                delivery_record["mailbox_item_id"],
                delivery_record["event_id"],
                delivery_record["recipient_session_id"],
                delivery_record["delivery_status"],
                delivery_record["delivery_mode"],
                delivery_record["created_at_utc"],
                delivery_record["detail_json"],
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM delivery_records WHERE idempotency_key = ?",
            (delivery_record["idempotency_key"],),
        ).fetchone()
        return {"ok": True, "created": row is not None, "delivery_record": _row_to_dict(row)}
    except sqlite3.Error as exc:
        return {
            "ok": False,
            "errors": [f"delivery_write_failed:{exc!s}"],
            "delivery_record": delivery_record,
        }
    finally:
        conn.close()


def record_delivery_attempt(repo_root: str | Path, attempt: dict[str, Any]) -> dict[str, Any]:
    valid, errors = validate_delivery_attempt(attempt)
    if not valid:
        return {"ok": False, "validation_errors": errors, "delivery_attempt": attempt}
    conn = _connect(repo_root)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO delivery_attempts (
                delivery_attempt_id, idempotency_key, outbox_item_id, event_id,
                recipient_session_id, mailbox_item_id, attempt_number, delivery_status,
                delivery_mode, created_at_utc, detail_json, error_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt["delivery_attempt_id"],
                attempt["idempotency_key"],
                attempt["outbox_item_id"],
                attempt["event_id"],
                attempt["recipient_session_id"],
                attempt["mailbox_item_id"],
                attempt["attempt_number"],
                attempt["delivery_status"],
                attempt["delivery_mode"],
                attempt["created_at_utc"],
                attempt["detail_json"],
                attempt["error_json"],
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM delivery_attempts WHERE idempotency_key = ?",
            (attempt["idempotency_key"],),
        ).fetchone()
        stored = _row_to_dict(row) or attempt
        return {"ok": True, "created": row is not None, "delivery_attempt": stored}
    except sqlite3.Error as exc:
        return {"ok": False, "errors": [f"delivery_attempt_write_failed:{exc!s}"], "delivery_attempt": attempt}
    finally:
        conn.close()


def update_outbox_item(
    repo_root: str | Path,
    outbox_item_id: str,
    *,
    status: str | None = None,
    settled: bool = False,
    last_error_json: str | None = None,
    next_attempt_at_utc: str | None = None,
    dead_letter_reason: str | None = None,
    dead_lettered_at_utc: str | None = None,
    approval_recorded_at_utc: str | None = None,
    attempt_count_delta: int = 1,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        outbox = _row_to_dict(
            conn.execute("SELECT * FROM outbox_items WHERE outbox_item_id = ?", (outbox_item_id,)).fetchone()
        )
        if outbox is None:
            return {"ok": False, "errors": ["outbox_item_not_found"], "outbox_item": None}
        new_status = _canonical_outbox_status(status or outbox["status"])
        if new_status not in OUTBOX_STATUSES:
            return {"ok": False, "errors": ["invalid_outbox_status"], "outbox_item": outbox}
        conn.execute(
            """
            UPDATE outbox_items
            SET status = ?,
                last_attempt_at_utc = ?,
                next_attempt_at_utc = ?,
                attempt_count = attempt_count + ?,
                last_error_json = ?,
                dead_letter_reason = ?,
                dead_lettered_at_utc = ?,
                approval_recorded_at_utc = COALESCE(?, approval_recorded_at_utc),
                settled_at_utc = CASE WHEN ? = 1 THEN COALESCE(settled_at_utc, ?) ELSE settled_at_utc END
            WHERE outbox_item_id = ?
            """,
            (
                new_status,
                _now(),
                next_attempt_at_utc,
                attempt_count_delta,
                last_error_json,
                dead_letter_reason,
                dead_lettered_at_utc,
                approval_recorded_at_utc,
                1 if settled else 0,
                _now(),
                outbox_item_id,
            ),
        )
        conn.commit()
        updated = _row_to_dict(
            conn.execute(
                "SELECT * FROM outbox_items WHERE outbox_item_id = ?",
                (outbox_item_id,),
            ).fetchone()
        )
        return {"ok": True, "outbox_item": updated}
    except sqlite3.Error as exc:
        return {"ok": False, "errors": [f"outbox_update_failed:{exc!s}"], "outbox_item": None}
    finally:
        conn.close()


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    text = _clean_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _iso_timestamp(value: datetime | str | None = None) -> str:
    if value is None:
        return _now()
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    text = _clean_text(value)
    return text or _now()


def _retry_delay_seconds(attempt_number: int, *, base_delay_seconds: int, max_delay_seconds: int) -> int:
    exponent = max(0, attempt_number - 1)
    delay = base_delay_seconds * (2**exponent)
    return min(max_delay_seconds, max(base_delay_seconds, delay))


def _next_attempt_time(
    now_iso: str,
    attempt_number: int,
    *,
    base_delay_seconds: int,
    max_delay_seconds: int,
) -> str:
    now_dt = _parse_timestamp(now_iso) or datetime.now(timezone.utc)
    delay = _retry_delay_seconds(
        attempt_number,
        base_delay_seconds=base_delay_seconds,
        max_delay_seconds=max_delay_seconds,
    )
    return (now_dt + timedelta(seconds=delay)).astimezone(timezone.utc).isoformat()


def _outbox_row(repo_root: str | Path, outbox_item_id: str) -> dict[str, Any] | None:
    conn = _connect(repo_root)
    try:
        row = conn.execute("SELECT * FROM outbox_items WHERE outbox_item_id = ?", (outbox_item_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def _mailbox_row_for_outbox(repo_root: str | Path, outbox_item: dict[str, Any]) -> dict[str, Any] | None:
    conn = _connect(repo_root)
    try:
        row = conn.execute(
            """
            SELECT * FROM mailbox_items
            WHERE event_id = ? AND recipient_session_id = ?
            ORDER BY created_at_utc DESC
            LIMIT 1
            """,
            (outbox_item["event_id"], outbox_item["recipient_session_id"]),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def record_outbox_approval(
    repo_root: str | Path,
    outbox_item_id: str,
    *,
    approved_by_session_id: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        outbox = _row_to_dict(
            conn.execute("SELECT * FROM outbox_items WHERE outbox_item_id = ?", (outbox_item_id,)).fetchone()
        )
        if outbox is None:
            return {"ok": False, "errors": ["outbox_item_not_found"], "outbox_item": None}
        recorded_at = _now()
        conn.execute(
            """
            UPDATE outbox_items
            SET approval_state = 'approved',
                status = CASE WHEN status = 'awaiting_approval' THEN 'queued' ELSE status END,
                approval_recorded_at_utc = ?,
                last_error_json = NULL
            WHERE outbox_item_id = ?
            """,
            (recorded_at, outbox_item_id),
        )
        conn.execute(
            """
            UPDATE mailbox_items
            SET approval_state = 'approved',
                approval_recorded_at_utc = ?,
                ack_note = COALESCE(ack_note, ?)
            WHERE event_id = ? AND recipient_session_id = ?
            """,
            (
                recorded_at,
                note or f"approved_by:{approved_by_session_id or 'operator'}",
                outbox["event_id"],
                outbox["recipient_session_id"],
            ),
        )
        conn.commit()
        _merge_route_summary(
            repo_root,
            outbox["event_id"],
            {
                "approval_outcome": "approved",
                "approval_recorded_at_utc": recorded_at,
                "approved_by_session_id": approved_by_session_id,
                "route_profile": "approval_granted",
            },
            route_status="approved",
        )
        updated = _row_to_dict(
            conn.execute("SELECT * FROM outbox_items WHERE outbox_item_id = ?", (outbox_item_id,)).fetchone()
        )
        mailbox_rows = conn.execute(
            """
            SELECT * FROM mailbox_items
            WHERE event_id = ? AND recipient_session_id = ?
            ORDER BY created_at_utc DESC
            """,
            (outbox["event_id"], outbox["recipient_session_id"]),
        ).fetchall()
        return {
            "ok": True,
            "outbox_item": updated,
            "mailbox_items": [_row_to_dict(row) for row in mailbox_rows if row is not None],
        }
    except sqlite3.Error as exc:
        return {"ok": False, "errors": [f"approval_record_failed:{exc!s}"], "outbox_item": None}
    finally:
        conn.close()


def reject_outbox_approval(
    repo_root: str | Path,
    outbox_item_id: str,
    *,
    rejected_by_session_id: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        outbox = _row_to_dict(
            conn.execute("SELECT * FROM outbox_items WHERE outbox_item_id = ?", (outbox_item_id,)).fetchone()
        )
        if outbox is None:
            return {"ok": False, "errors": ["outbox_item_not_found"], "outbox_item": None}
        recorded_at = _now()
        conn.execute(
            """
            UPDATE outbox_items
            SET approval_state = 'rejected',
                status = 'dead_letter',
                approval_recorded_at_utc = ?,
                dead_letter_reason = 'approval_rejected',
                dead_lettered_at_utc = ?,
                last_error_json = COALESCE(last_error_json, ?)
            WHERE outbox_item_id = ?
            """,
            (
                recorded_at,
                recorded_at,
                json.dumps(
                    {
                        "approval_rejected_by": rejected_by_session_id,
                        "note": note,
                    },
                    sort_keys=True,
                ),
                outbox_item_id,
            ),
        )
        conn.execute(
            """
            UPDATE mailbox_items
            SET approval_state = 'rejected',
                approval_recorded_at_utc = ?,
                ack_note = COALESCE(ack_note, ?)
            WHERE event_id = ? AND recipient_session_id = ?
            """,
            (
                recorded_at,
                note or f"rejected_by:{rejected_by_session_id or 'operator'}",
                outbox["event_id"],
                outbox["recipient_session_id"],
            ),
        )
        conn.commit()
        _merge_route_summary(
            repo_root,
            outbox["event_id"],
            {
                "approval_outcome": "rejected",
                "approval_recorded_at_utc": recorded_at,
                "rejected_by_session_id": rejected_by_session_id,
                "route_profile": "approval_rejected",
                "rejection_note": note,
            },
            route_status="dead_letter",
        )
        updated = _row_to_dict(
            conn.execute("SELECT * FROM outbox_items WHERE outbox_item_id = ?", (outbox_item_id,)).fetchone()
        )
        mailbox_rows = conn.execute(
            """
            SELECT * FROM mailbox_items
            WHERE event_id = ? AND recipient_session_id = ?
            ORDER BY created_at_utc DESC
            """,
            (outbox["event_id"], outbox["recipient_session_id"]),
        ).fetchall()
        return {
            "ok": True,
            "outbox_item": updated,
            "mailbox_items": [_row_to_dict(row) for row in mailbox_rows if row is not None],
        }
    except sqlite3.Error as exc:
        return {"ok": False, "errors": [f"approval_reject_failed:{exc!s}"], "outbox_item": None}
    finally:
        conn.close()


def _worker_delivery_preview(repo_root: str | Path, outbox_item: dict[str, Any], now_iso: str) -> dict[str, Any]:
    mailbox = _mailbox_row_for_outbox(repo_root, outbox_item)
    if mailbox is None:
        return {
            "ok": False,
            "error": "mailbox_item_not_found",
            "detail": {
                "outbox_item_id": outbox_item["outbox_item_id"],
                "recipient_session_id": outbox_item["recipient_session_id"],
            },
        }
    if mailbox.get("approval_state") == "pending":
        return {
            "ok": False,
            "error": "approval_pending",
            "detail": {
                "mailbox_item_id": mailbox["mailbox_item_id"],
                "approval_state": mailbox.get("approval_state"),
            },
        }
    if mailbox.get("status") == "acked":
        return {
            "ok": True,
            "already_acked": True,
            "mailbox_item": mailbox,
            "detail": {
                "mailbox_item_id": mailbox["mailbox_item_id"],
                "delivery_mode": mailbox["delivery_mode"],
            },
        }
    return {
        "ok": True,
        "mailbox_item": mailbox,
        "detail": {
            "mailbox_item_id": mailbox["mailbox_item_id"],
            "delivery_mode": mailbox["delivery_mode"],
            "route_reason": mailbox.get("route_reason"),
            "attempt_seen_at_utc": now_iso,
        },
    }


def process_outbox_item(
    repo_root: str | Path,
    outbox_item_id: str,
    *,
    now: datetime | str | None = None,
    deliver: Callable[[str | Path, dict[str, Any], str], dict[str, Any]] | None = None,
    max_attempts: int = 3,
    base_delay_seconds: int = 30,
    max_delay_seconds: int = 3600,
) -> dict[str, Any]:
    now_iso = _iso_timestamp(now)
    outbox = _outbox_row(repo_root, outbox_item_id)
    if outbox is None:
        return {"ok": False, "errors": ["outbox_item_not_found"], "outbox_item": None}

    status = _canonical_outbox_status(outbox["status"]) or outbox["status"]
    if status == "dead_letter":
        return {"ok": True, "skipped": True, "reason": "already_dead_letter", "outbox_item": outbox}
    if status not in {"queued", "retry_pending", "awaiting_approval"}:
        return {"ok": True, "skipped": True, "reason": f"status_{outbox['status']}", "outbox_item": outbox}
    if outbox["approval_state"] == "pending":
        update_outbox_item(
            repo_root,
            outbox_item_id,
            status="awaiting_approval",
            settled=False,
            next_attempt_at_utc=None,
            attempt_count_delta=0,
        )
        _merge_route_summary(
            repo_root,
            outbox["event_id"],
            {
                "approval_outcome": "pending",
                "route_profile": "approval_required",
            },
            route_status="awaiting_approval",
        )
        return {"ok": True, "skipped": True, "reason": "awaiting_approval", "outbox_item": outbox}
    if outbox["approval_state"] == "rejected":
        updated = update_outbox_item(
            repo_root,
            outbox_item_id,
            status="dead_letter",
            settled=True,
            dead_letter_reason="approval_rejected",
            dead_lettered_at_utc=now_iso,
            attempt_count_delta=0,
        )
        _merge_route_summary(
            repo_root,
            outbox["event_id"],
            {
                "approval_outcome": "rejected",
                "route_profile": "approval_rejected",
                "dead_letter_reason": "approval_rejected",
            },
            route_status="dead_letter",
        )
        return {
            "ok": True,
            "skipped": True,
            "reason": "approval_rejected",
            "outbox_item": updated.get("outbox_item"),
        }
    if not _is_ready_for_attempt(outbox.get("next_attempt_at_utc"), now_iso):
        return {
            "ok": True,
            "skipped": True,
            "reason": "backoff_not_elapsed",
            "outbox_item": outbox,
        }

    claim_result = update_outbox_item(
        repo_root,
        outbox_item_id,
        status="delivering",
        settled=False,
        attempt_count_delta=0,
    )
    outbox = claim_result.get("outbox_item") or outbox
    attempt_number = int(outbox.get("attempt_count") or 0) + 1
    deliver_fn = deliver or _worker_delivery_preview
    try:
        delivery_result = deliver_fn(repo_root, outbox, now_iso)
    except Exception as exc:  # noqa: BLE001 - fail open for worker transport
        delivery_result = {
            "ok": False,
            "error": f"delivery_callback_failed:{exc!s}",
            "detail": {"exception": str(exc)},
        }

    detail = delivery_result.get("detail") if isinstance(delivery_result.get("detail"), dict) else {}
    if delivery_result.get("ok"):
        mailbox = delivery_result.get("mailbox_item")
        if mailbox is None:
            mailbox = _mailbox_row_for_outbox(repo_root, outbox)
        if mailbox is None:
            delivery_result = {
                "ok": False,
                "error": "mailbox_item_not_found",
                "detail": {"outbox_item_id": outbox_item_id},
            }
            detail = delivery_result["detail"]
        else:
            if mailbox.get("status") != "acked":
                conn = _connect(repo_root)
                try:
                    conn.execute(
                        """
                        UPDATE mailbox_items
                        SET status = 'delivered',
                            delivered_at_utc = COALESCE(delivered_at_utc, ?)
                        WHERE mailbox_item_id = ?
                        """,
                        (now_iso, mailbox["mailbox_item_id"]),
                    )
                    conn.commit()
                finally:
                    conn.close()
            delivery_record = _delivery_payload(mailbox, "delivered", detail)
            delivery_attempt = _delivery_attempt_payload(
                outbox,
                mailbox_item_id=mailbox["mailbox_item_id"],
                delivery_status="delivered",
                detail=detail,
                attempt_number=attempt_number,
            )
            _insert_delivery_record(repo_root, delivery_record)
            record_delivery_attempt(repo_root, delivery_attempt)
            updated = update_outbox_item(
                repo_root,
                outbox_item_id,
                status="delivered",
                settled=True,
                last_error_json=None,
                next_attempt_at_utc=None,
                dead_letter_reason=None,
                dead_lettered_at_utc=None,
                attempt_count_delta=1,
            )
            _merge_route_summary(
                repo_root,
                outbox["event_id"],
                {
                    "worker_delivery_status": "delivered",
                    "worker_attempt_number": attempt_number,
                    "delivery_mode": mailbox["delivery_mode"],
                },
                route_status="delivered",
            )
            return {
                "ok": True,
                "skipped": False,
                "status": "delivered",
                "attempt_number": attempt_number,
                "delivery_record": delivery_record,
                "delivery_attempt": delivery_attempt,
                "mailbox_item_id": mailbox["mailbox_item_id"],
                "outbox_item": updated.get("outbox_item"),
            }

    next_attempt_at_utc = None
    final_status = "retry_pending"
    dead_letter_reason = None
    dead_lettered_at_utc = None
    if attempt_number >= max_attempts:
        final_status = "dead_letter"
        dead_letter_reason = delivery_result.get("error") or "max_attempts_exhausted"
        dead_lettered_at_utc = now_iso
    else:
        next_attempt_at_utc = _next_attempt_time(
            now_iso,
            attempt_number,
            base_delay_seconds=base_delay_seconds,
            max_delay_seconds=max_delay_seconds,
        )

    error_text = delivery_result.get("error") or "worker_delivery_failed"
    error_json = json.dumps(
        {
            "error": error_text,
            "detail": detail,
            "attempt_number": attempt_number,
        },
        sort_keys=True,
    )
    delivery_attempt = _delivery_attempt_payload(
        outbox,
        mailbox_item_id=None,
        delivery_status="failed",
        detail={**detail, "error": error_text, "next_attempt_at_utc": next_attempt_at_utc},
        attempt_number=attempt_number,
        error=error_json,
    )
    record_delivery_attempt(repo_root, delivery_attempt)
    updated = update_outbox_item(
        repo_root,
        outbox_item_id,
        status=final_status,
        settled=final_status == "dead_letter",
        last_error_json=error_json,
        next_attempt_at_utc=next_attempt_at_utc,
        dead_letter_reason=dead_letter_reason,
        dead_lettered_at_utc=dead_lettered_at_utc,
        attempt_count_delta=1,
    )
    _merge_route_summary(
        repo_root,
        outbox["event_id"],
        {
            "worker_delivery_status": final_status,
            "worker_attempt_number": attempt_number,
            "dead_letter_reason": dead_letter_reason,
            "last_error": error_text,
        },
        route_status=final_status,
    )
    return {
        "ok": True,
        "skipped": False,
        "status": final_status,
        "attempt_number": attempt_number,
        "next_attempt_at_utc": next_attempt_at_utc,
        "dead_letter_reason": dead_letter_reason,
        "delivery_attempt": delivery_attempt,
        "outbox_item": updated.get("outbox_item"),
    }


def _is_ready_for_attempt(next_attempt_at_utc: str | None, now_iso: str) -> bool:
    next_attempt = _parse_timestamp(next_attempt_at_utc)
    if next_attempt is None:
        return True
    now_dt = _parse_timestamp(now_iso) or datetime.now(timezone.utc)
    return next_attempt <= now_dt


def list_outbox_work(
    repo_root: str | Path,
    *,
    status: str | None = None,
    approval_state: str | None = None,
    due_only: bool = False,
    limit: int = 25,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if approval_state:
            clauses.append("approval_state = ?")
            params.append(approval_state)
        if due_only:
            clauses.append("status IN ('queued', 'retry_pending')")
            clauses.append("approval_state IN ('not_required', 'approved')")
            clauses.append("(next_attempt_at_utc IS NULL OR next_attempt_at_utc <= ?)")
            params.append(_now())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM outbox_items {where} ORDER BY created_at_utc DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        items = [_row_to_dict(row) for row in rows if row is not None]
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def summarize_delivery_states(repo_root: str | Path) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        status_rows = conn.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM outbox_items
            GROUP BY status
            ORDER BY status
            """
        ).fetchall()
        approval_rows = conn.execute(
            """
            SELECT approval_state, COUNT(*) AS count
            FROM outbox_items
            GROUP BY approval_state
            ORDER BY approval_state
            """
        ).fetchall()
        status_counts = {row["status"]: int(row["count"]) for row in status_rows if row is not None}
        approval_counts = {row["approval_state"]: int(row["count"]) for row in approval_rows if row is not None}
        due_count = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM outbox_items
                WHERE status IN ('queued', 'retry_pending')
                  AND approval_state IN ('not_required', 'approved')
                  AND (next_attempt_at_utc IS NULL OR next_attempt_at_utc <= ?)
                """,
                (_now(),),
            ).fetchone()[0]
        )
        return {
            "ok": True,
            "status_counts": status_counts,
            "approval_counts": approval_counts,
            "queued_total": int(status_counts.get("queued", 0)),
            "delivering_total": int(status_counts.get("delivering", 0)),
            "retry_pending_total": int(status_counts.get("retry_pending", 0)),
            "dead_letter_total": int(status_counts.get("dead_letter", 0)),
            "delivered_total": int(status_counts.get("delivered", 0)),
            "pending_total": int(
                status_counts.get("queued", 0)
                + status_counts.get("delivering", 0)
                + status_counts.get("retry_pending", 0)
            ),
            "approval_pending_total": int(approval_counts.get("pending", 0)),
            "due_total": due_count,
        }
    finally:
        conn.close()


def run_delivery_worker(
    repo_root: str | Path,
    *,
    limit: int = 25,
    now: datetime | str | None = None,
    deliver: Callable[[str | Path, dict[str, Any], str], dict[str, Any]] | None = None,
    max_attempts: int = 3,
    base_delay_seconds: int = 30,
    max_delay_seconds: int = 3600,
) -> dict[str, Any]:
    now_iso = _iso_timestamp(now)
    queue = list_outbox_work(repo_root, due_only=True, limit=limit)
    if not queue.get("ok"):
        return queue
    results: list[dict[str, Any]] = []
    for item in queue["items"]:
        if item is None:
            continue
        result = process_outbox_item(
            repo_root,
            item["outbox_item_id"],
            now=now_iso,
            deliver=deliver,
            max_attempts=max_attempts,
            base_delay_seconds=base_delay_seconds,
            max_delay_seconds=max_delay_seconds,
        )
        results.append(result)
    return {
        "ok": True,
        "processed_count": sum(1 for item in results if not item.get("skipped")),
        "skipped_count": sum(1 for item in results if item.get("skipped")),
        "delivered_count": sum(1 for item in results if item.get("status") == "delivered"),
        "retry_pending_count": sum(1 for item in results if item.get("status") == "retry_pending"),
        "dead_letter_count": sum(1 for item in results if item.get("status") == "dead_letter"),
        "items": results,
        "queue": queue,
    }


def route_event(repo_root: str | Path, event: str | dict[str, Any]) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        if isinstance(event, dict):
            envelope = _normalize_envelope(event, repo_root=repo_root)
            valid, errors = validate_event_envelope(envelope)
            if not valid:
                return {"ok": False, "validation_errors": errors, "warnings": []}
            existing = conn.execute(
                "SELECT * FROM events WHERE idempotency_key = ?",
                (envelope["idempotency_key"],),
            ).fetchone()
            if existing is None:
                conn.close()
                return publish_event(repo_root, envelope, route=True)["route_result"]
            event_row = _row_to_dict(existing) or {}
        else:
            event_row = _row_to_dict(
                conn.execute("SELECT * FROM events WHERE event_id = ?", (event,)).fetchone()
            ) or {}
            if not event_row:
                return {"ok": False, "warnings": ["event_not_found"], "mailbox_item_ids": []}
            envelope = {
                "event_id": event_row["event_id"],
                "schema_version": event_row["schema_version"],
                "event_type": event_row["event_type"],
                "message_kind": event_row["message_kind"],
                "session": {
                    "session_id": event_row["session_id"],
                    "session_kind": event_row["session_kind"],
                    "role": event_row["role"],
                    "run_id": event_row["run_id"],
                    "repo_root": event_row["repo_root"],
                    "branch": event_row["branch"],
                    "is_active": True,
                    "subscribes_same_run": True,
                    "subscribes_same_repo": True,
                    "subscribes_same_branch": True,
                },
                "target": {
                    "selector_type": event_row["target_selector_type"],
                    "selector_value": event_row["target_selector_value"],
                    "allow_followup": bool(event_row["target_allow_followup"]),
                },
                "payload": json.loads(event_row["payload_json"]),
                "created_at_utc": event_row["created_at_utc"],
                "idempotency_key": event_row["idempotency_key"],
                "requires_approval": bool(event_row["requires_approval"]),
                "approval_state": event_row["approval_state"],
                "route_approval_state": event_row["approval_state"],
                "delivery_mode": event_row["delivery_mode"],
                "followup_message": event_row["followup_message"],
            }

        route_profile = _routing_profile(
            envelope["message_kind"],
            requires_approval=bool(envelope["requires_approval"]),
            approval_state=str(envelope["approval_state"]),
        )
        warnings: list[str] = []
        try:
            route_matches = _routing_match_summary(conn, envelope)
        except Exception as exc:  # noqa: BLE001 - routing must fail open
            warnings.append(f"subscription_policy_fallback:{exc!s}")
            route_matches = [
                {
                    "recipient_session": recipient,
                    "recipient_session_id": recipient["session_id"],
                    "recipient_role": recipient.get("role"),
                    "recipient_session_kind": recipient.get("session_kind"),
                    "subscription_policy_ids": [f"legacy:{recipient['session_id']}"],
                    "subscription_policy_names": ["legacy_scope_fallback"],
                    "matched_subscription_policy": _legacy_subscription_policy(recipient, envelope),
                    "delivery_mode": "active_followup"
                    if bool(recipient.get("is_active"))
                    and envelope["target"]["allow_followup"]
                    and not bool(envelope["requires_approval"])
                    else "durable_mailbox",
                    "active_session": bool(recipient.get("is_active")),
                    "source_role": envelope["session"].get("role"),
                    "route_profile": route_profile,
                    "task_id": _event_task_id(envelope),
                    "correlation_id": _event_correlation_id(envelope),
                    "event_type": envelope.get("event_type"),
                    "message_kind": envelope.get("message_kind"),
                }
                for recipient in _candidate_sessions(conn, envelope)
            ]
        outbox_item_ids: list[str] = []
        mailbox_item_ids: list[str] = []
        delivery_record_ids: list[str] = []
        delivery_attempt_ids: list[str] = []
        delivered = 0
        durable = 0

        if not route_matches:
            warnings.append("unknown_target_no_matching_sessions")
            _merge_route_summary(
                repo_root,
                envelope["event_id"],
                {
                    "route_profile": route_profile,
                    "warnings": warnings,
                    "mailbox_item_ids": [],
                    "outbox_item_ids": [],
                    "delivery_attempt_ids": [],
                    "notify_flows": [],
                },
                route_status="no_targets",
            )
            conn.commit()
            return {
                "ok": True,
                "route_status": "no_targets",
                "warnings": warnings,
                "mailbox_item_ids": [],
                "delivery_record_ids": [],
                "outbox_item_ids": [],
                "delivery_attempt_ids": [],
            }

        notify_flows: list[dict[str, Any]] = []
        for match in route_matches:
            recipient = match["recipient_session"]
            active = bool(recipient.get("is_active"))
            approval_blocked = envelope["requires_approval"] and envelope.get(
                "route_approval_state", envelope["approval_state"]
            ) != "approved"
            if route_profile == "approval_rejected":
                delivery_mode = "durable_mailbox"
                mailbox_status = "suppressed"
                delivery_status = "suppressed"
                outbox_status = "dead_letter"
            elif approval_blocked:
                delivery_mode = "durable_mailbox"
                mailbox_status = "queued"
                delivery_status = "queued"
                outbox_status = "awaiting_approval"
            elif active and not approval_blocked and envelope["target"]["allow_followup"] and match["delivery_mode"] == "active_followup":
                delivery_mode = "active_followup"
                mailbox_status = "delivered"
                delivery_status = "delivered"
                outbox_status = "dispatched"
                delivered += 1
            else:
                delivery_mode = "durable_mailbox"
                mailbox_status = "queued"
                delivery_status = "queued"
                outbox_status = "awaiting_approval" if approval_blocked else "queued"
                durable += 1
                if approval_blocked:
                    warnings.append(f"approval_required:{recipient['session_id']}")
            route_reason = (
                f"{route_profile}:{match['matched_subscription_policy']['policy_name']}"
                if match.get("matched_subscription_policy")
                else route_profile
            )
            notify_flows.append(
                {
                    "recipient_session_id": recipient["session_id"],
                    "recipient_role": recipient.get("role"),
                    "delivery_mode": delivery_mode,
                    "route_reason": route_reason,
                    "subscription_policy_ids": match["subscription_policy_ids"],
                    "subscription_policy_names": match["subscription_policy_names"],
                }
            )
            outbox_item = _outbox_payload(
                envelope,
                recipient,
                delivery_mode=delivery_mode,
                status=outbox_status,
                route_reason=route_reason,
            )
            outbox_result = enqueue_outbox_item(repo_root, outbox_item)
            if not outbox_result.get("ok"):
                warnings.extend(outbox_result.get("validation_errors") or outbox_result.get("errors") or [])
                conn.execute(
                    "UPDATE events SET route_status = ?, route_summary_json = ? WHERE event_id = ?",
                    (
                        "failed",
                        json.dumps(
                            {
                                "warnings": warnings,
                                "mailbox_item_ids": mailbox_item_ids,
                                "outbox_item_ids": outbox_item_ids,
                                "delivery_attempt_ids": delivery_attempt_ids,
                            },
                            sort_keys=True,
                        ),
                        envelope["event_id"],
                    ),
                )
                conn.commit()
                return {
                    "ok": False,
                    "route_status": "failed",
                    "warnings": warnings,
                    "mailbox_item_ids": mailbox_item_ids,
                    "delivery_record_ids": delivery_record_ids,
                    "outbox_item_ids": outbox_item_ids,
                    "delivery_attempt_ids": delivery_attempt_ids,
                }
            stored_outbox = outbox_result["outbox_item"]
            outbox_item_ids.append(stored_outbox["outbox_item_id"])
            mailbox_item = _mailbox_payload(
                envelope,
                recipient,
                delivery_mode=delivery_mode,
                status=mailbox_status,
                route_reason=route_reason,
            )
            mailbox_result = enqueue_mailbox_item(repo_root, mailbox_item)
            if not mailbox_result.get("ok"):
                warnings.extend(mailbox_result.get("validation_errors") or mailbox_result.get("errors") or [])
                conn.execute(
                    "UPDATE events SET route_status = ?, route_summary_json = ? WHERE event_id = ?",
                    (
                        "failed",
                        json.dumps(
                            {
                                "warnings": warnings,
                                "mailbox_item_ids": mailbox_item_ids,
                                "outbox_item_ids": outbox_item_ids,
                                "delivery_attempt_ids": delivery_attempt_ids,
                            },
                            sort_keys=True,
                        ),
                        envelope["event_id"],
                    ),
                )
                conn.commit()
                return {
                    "ok": False,
                    "route_status": "failed",
                    "warnings": warnings,
                    "mailbox_item_ids": mailbox_item_ids,
                    "delivery_record_ids": delivery_record_ids,
                    "outbox_item_ids": outbox_item_ids,
                    "delivery_attempt_ids": delivery_attempt_ids,
                }
            stored_mailbox = mailbox_result["mailbox_item"]
            mailbox_item_ids.append(stored_mailbox["mailbox_item_id"])
            delivery_record = _delivery_payload(
                stored_mailbox,
                delivery_status=delivery_status,
                detail={
                    "route_reason": stored_mailbox["route_reason"],
                    "active_session": active,
                    "approval_blocked": approval_blocked,
                    "outbox_item_id": stored_outbox["outbox_item_id"],
                },
            )
            delivery_result = _insert_delivery_record(repo_root, delivery_record)
            if not delivery_result.get("ok"):
                warnings.extend(delivery_result.get("errors") or [])
                conn.execute(
                    "UPDATE events SET route_status = ?, route_summary_json = ? WHERE event_id = ?",
                    (
                        "failed",
                        json.dumps(
                            {
                                "warnings": warnings,
                                "mailbox_item_ids": mailbox_item_ids,
                                "outbox_item_ids": outbox_item_ids,
                                "delivery_attempt_ids": delivery_attempt_ids,
                            },
                            sort_keys=True,
                        ),
                        envelope["event_id"],
                    ),
                )
                conn.commit()
                return {
                    "ok": False,
                    "route_status": "failed",
                    "warnings": warnings,
                    "mailbox_item_ids": mailbox_item_ids,
                    "delivery_record_ids": delivery_record_ids,
                    "outbox_item_ids": outbox_item_ids,
                    "delivery_attempt_ids": delivery_attempt_ids,
                }
            delivery_record_ids.append(delivery_result["delivery_record"]["delivery_record_id"])
            delivery_attempt = _delivery_attempt_payload(
                stored_outbox,
                mailbox_item_id=stored_mailbox["mailbox_item_id"],
                delivery_status=delivery_status,
                detail={
                    "route_reason": stored_mailbox["route_reason"],
                    "active_session": active,
                    "approval_blocked": approval_blocked,
                    "mailbox_item_id": stored_mailbox["mailbox_item_id"],
                },
                attempt_number=1,
            )
            attempt_result = record_delivery_attempt(repo_root, delivery_attempt)
            if not attempt_result.get("ok"):
                warnings.extend(attempt_result.get("errors") or [])
                conn.execute(
                    "UPDATE events SET route_status = ?, route_summary_json = ? WHERE event_id = ?",
                    (
                        "failed",
                        json.dumps(
                            {
                                "warnings": warnings,
                                "mailbox_item_ids": mailbox_item_ids,
                                "outbox_item_ids": outbox_item_ids,
                                "delivery_attempt_ids": delivery_attempt_ids,
                            },
                            sort_keys=True,
                        ),
                        envelope["event_id"],
                    ),
                )
                conn.commit()
                return {
                    "ok": False,
                    "route_status": "failed",
                    "warnings": warnings,
                    "mailbox_item_ids": mailbox_item_ids,
                    "delivery_record_ids": delivery_record_ids,
                    "outbox_item_ids": outbox_item_ids,
                    "delivery_attempt_ids": delivery_attempt_ids,
                }
            delivery_attempt_ids.append(attempt_result["delivery_attempt"]["delivery_attempt_id"])
            if attempt_result.get("created"):
                update_outbox_item(repo_root, stored_outbox["outbox_item_id"], status=outbox_status)

        route_status = "delivered" if delivered else "queued"
        _merge_route_summary(
            repo_root,
            envelope["event_id"],
            {
                "route_profile": route_profile,
                "warnings": warnings,
                "mailbox_item_ids": mailbox_item_ids,
                "delivery_record_ids": delivery_record_ids,
                "outbox_item_ids": outbox_item_ids,
                "delivery_attempt_ids": delivery_attempt_ids,
                "delivered_count": delivered,
                "durable_count": durable,
                "notify_flows": notify_flows,
                "matched_subscription_policy_ids": [
                    policy_id
                    for match in route_matches
                    for policy_id in match["subscription_policy_ids"]
                ],
                "matched_subscription_policy_names": [
                    policy_name
                    for match in route_matches
                    for policy_name in match["subscription_policy_names"]
                ],
            },
            route_status=route_status,
        )
        conn.commit()
        return {
            "ok": True,
            "route_status": route_status,
            "warnings": warnings,
            "mailbox_item_ids": mailbox_item_ids,
            "delivery_record_ids": delivery_record_ids,
            "outbox_item_ids": outbox_item_ids,
            "delivery_attempt_ids": delivery_attempt_ids,
            "delivered_count": delivered,
            "durable_count": durable,
        }
    except sqlite3.Error as exc:
        return {"ok": False, "warnings": [f"route_error:{exc!s}"], "mailbox_item_ids": []}
    finally:
        conn.close()


def list_events(
    repo_root: str | Path,
    *,
    session_id: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM events WHERE session_id = ? ORDER BY created_at_utc DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY created_at_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        items = [_row_to_dict(row) for row in rows if row is not None]
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def list_mailbox(
    repo_root: str | Path,
    session_id: str | None = None,
    *,
    status: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("recipient_session_id = ?")
            params.append(session_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM mailbox_items {where} ORDER BY created_at_utc DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        items = [_row_to_dict(row) for row in rows if row is not None]
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def list_inbox(
    repo_root: str | Path,
    session_id: str | None = None,
    *,
    status: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    return list_mailbox(repo_root, session_id, status=status, limit=limit)


def list_outbox(
    repo_root: str | Path,
    session_id: str | None = None,
    *,
    status: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("recipient_session_id = ?")
            params.append(session_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM outbox_items {where} ORDER BY created_at_utc DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        items = [_row_to_dict(row) for row in rows if row is not None]
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def list_delivery_attempts(
    repo_root: str | Path,
    session_id: str | None = None,
    *,
    status: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if session_id:
            clauses.append("recipient_session_id = ?")
            params.append(session_id)
        if status:
            clauses.append("delivery_status = ?")
            params.append(status)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM delivery_attempts {where} ORDER BY created_at_utc DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        items = [_row_to_dict(row) for row in rows if row is not None]
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def ack_mailbox_item(
    repo_root: str | Path,
    mailbox_item_id: str,
    *,
    acked_by_session_id: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        row = conn.execute(
            "SELECT * FROM mailbox_items WHERE mailbox_item_id = ?",
            (mailbox_item_id,),
        ).fetchone()
        if row is None:
            return {"ok": False, "errors": ["mailbox_item_not_found"], "mailbox_item": None}
        mailbox = _row_to_dict(row) or {}
        if mailbox.get("status") == "acked":
            return {"ok": True, "already_acked": True, "mailbox_item": mailbox}
        acked_at = _now()
        conn.execute(
            """
            UPDATE mailbox_items
            SET status = 'acked',
                acked_at_utc = ?,
                acked_by_session_id = ?,
                ack_note = ?
            WHERE mailbox_item_id = ?
            """,
            (acked_at, acked_by_session_id, note, mailbox_item_id),
        )
        conn.commit()
        outbox_row = conn.execute(
            """
            SELECT * FROM outbox_items
            WHERE event_id = ? AND recipient_session_id = ?
            ORDER BY created_at_utc DESC
            LIMIT 1
            """,
            (mailbox["event_id"], mailbox["recipient_session_id"]),
        ).fetchone()
        outbox = _row_to_dict(outbox_row)
        ack_delivery = {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "delivery_record_id": f"delivery-{uuid.uuid4().hex}",
            "mailbox_item_id": mailbox_item_id,
            "event_id": mailbox["event_id"],
            "recipient_session_id": mailbox["recipient_session_id"],
            "delivery_status": "acked",
            "delivery_mode": mailbox["delivery_mode"],
            "created_at_utc": acked_at,
            "detail_json": json.dumps(
                {
                    "ack_note": note,
                    "acked_by_session_id": acked_by_session_id,
                },
                sort_keys=True,
            ),
            "idempotency_key": f"{mailbox_item_id}:acked",
        }
        _insert_delivery_record(repo_root, ack_delivery)
        if outbox is not None:
            attempt_number = int(outbox.get("attempt_count") or 0) + 1
            ack_attempt = _delivery_attempt_payload(
                outbox,
                mailbox_item_id=mailbox_item_id,
                delivery_status="acked",
                detail={
                    "ack_note": note,
                    "acked_by_session_id": acked_by_session_id,
                },
                attempt_number=attempt_number,
            )
            record_delivery_attempt(repo_root, ack_attempt)
            update_outbox_item(repo_root, outbox["outbox_item_id"], status="acked", settled=True)
        conn.commit()
        updated = _row_to_dict(
            conn.execute(
                "SELECT * FROM mailbox_items WHERE mailbox_item_id = ?",
                (mailbox_item_id,),
            ).fetchone()
        )
        return {"ok": True, "already_acked": False, "mailbox_item": updated}
    except sqlite3.Error as exc:
        return {"ok": False, "errors": [f"ack_failed:{exc!s}"], "mailbox_item": None}
    finally:
        conn.close()


def render_followup_message(repo_root: str | Path, session_id: str, *, limit: int = 5) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        session = _session_row(conn, session_id)
        if session is None:
            return {"ok": False, "errors": ["session_not_found"], "followup_message": None}
        mailbox = list_mailbox(repo_root, session_id, limit=limit)
        items = mailbox["items"]
        pending = [item for item in items if item and item.get("status") in {"queued", "delivered"}]
        approval_blocked = [
            item
            for item in pending
            if item and item.get("approval_state") == "pending"
        ]
        active = bool(session.get("is_active"))
        if not pending:
            return {
                "ok": True,
                "active_session": active,
                "followup_message": None,
                "pending_count": 0,
                "approval_blocked_count": 0,
                "pending_items": [],
            }
        if not active or approval_blocked:
            return {
                "ok": True,
                "active_session": active,
                "followup_message": None,
                "pending_count": len(pending),
                "approval_blocked_count": len(approval_blocked),
                "pending_items": pending,
                "note": "durable inbox only; follow-up withheld until active and policy allows it",
            }
        top = pending[0]
        message = (
            f"{len(pending)} pending runtime message(s) for {session_id}; "
            f"next item: {top['message_kind']} from {top['source_session_id']} "
            f"({top['delivery_mode']})"
        )
        return {
            "ok": True,
            "active_session": active,
            "followup_message": message,
            "pending_count": len(pending),
            "approval_blocked_count": 0,
            "pending_items": pending,
        }
    finally:
        conn.close()


def summarize_flow(
    repo_root: str | Path,
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        event_query = "SELECT COUNT(*) FROM events"
        mailbox_query = "SELECT COUNT(*) FROM mailbox_items"
        outbox_query = "SELECT COUNT(*) FROM outbox_items"
        delivery_query = "SELECT COUNT(*) FROM delivery_records"
        delivery_attempt_query = "SELECT COUNT(*) FROM delivery_attempts"
        params: tuple[Any, ...] = ()
        if session_id:
            event_query += " WHERE session_id = ?"
            mailbox_query += " WHERE recipient_session_id = ?"
            outbox_query += " WHERE recipient_session_id = ?"
            delivery_query += " WHERE recipient_session_id = ?"
            delivery_attempt_query += " WHERE recipient_session_id = ?"
            params = (session_id,)
        events_total = int(conn.execute(event_query, params).fetchone()[0])
        mailbox_total = int(conn.execute(mailbox_query, params).fetchone()[0])
        outbox_total = int(conn.execute(outbox_query, params).fetchone()[0])
        delivery_total = int(conn.execute(delivery_query, params).fetchone()[0])
        delivery_attempt_total = int(conn.execute(delivery_attempt_query, params).fetchone()[0])
        pending_total = int(
            conn.execute(
                "SELECT COUNT(*) FROM mailbox_items WHERE status IN ('queued', 'delivered')"
                + (" AND recipient_session_id = ?" if session_id else ""),
                params,
            ).fetchone()[0]
        )
        active_followups = int(
            conn.execute(
                "SELECT COUNT(*) FROM mailbox_items WHERE delivery_mode = 'active_followup'"
                + (" AND recipient_session_id = ?" if session_id else ""),
                params,
            ).fetchone()[0]
        )
        durable_items = mailbox_total - active_followups
        acked = int(
            conn.execute(
                "SELECT COUNT(*) FROM mailbox_items WHERE status = 'acked'"
                + (" AND recipient_session_id = ?" if session_id else ""),
                params,
            ).fetchone()[0]
        )
        queued_outbox = int(
            conn.execute(
                "SELECT COUNT(*) FROM outbox_items WHERE status IN ('queued', 'retry_pending', 'dispatched')"
                + (" AND recipient_session_id = ?" if session_id else ""),
                params,
            ).fetchone()[0]
        )
        retry_pending_outbox = int(
            conn.execute(
                "SELECT COUNT(*) FROM outbox_items WHERE status = 'retry_pending'"
                + (" AND recipient_session_id = ?" if session_id else ""),
                params,
            ).fetchone()[0]
        )
        dead_letter_outbox = int(
            conn.execute(
                "SELECT COUNT(*) FROM outbox_items WHERE status = 'dead_letter'"
                + (" AND recipient_session_id = ?" if session_id else ""),
                params,
            ).fetchone()[0]
        )
        return {
            "ok": True,
            "session_id": session_id,
            "events_total": events_total,
            "mailbox_total": mailbox_total,
            "outbox_total": outbox_total,
            "delivery_total": delivery_total,
            "delivery_attempt_total": delivery_attempt_total,
            "pending_total": pending_total,
            "queued_outbox": queued_outbox,
            "retry_pending_outbox": retry_pending_outbox,
            "dead_letter_outbox": dead_letter_outbox,
            "acked_total": acked,
            "active_followups": active_followups,
            "durable_items": durable_items,
        }
    finally:
        conn.close()


def _parse_json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def list_routing_decisions(
    repo_root: str | Path,
    *,
    session_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM events WHERE session_id = ? ORDER BY created_at_utc DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY created_at_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            event = _row_to_dict(row)
            if event is None:
                continue
            summary = _parse_json_object(event.get("route_summary_json"))
            items.append(
                {
                    "event_id": event.get("event_id"),
                    "created_at_utc": event.get("created_at_utc"),
                    "session_id": event.get("session_id"),
                    "role": event.get("role"),
                    "message_kind": event.get("message_kind"),
                    "route_status": event.get("route_status"),
                    "route_profile": summary.get("route_profile"),
                    "notify_flows": summary.get("notify_flows", []),
                    "matched_subscription_policy_ids": summary.get("matched_subscription_policy_ids", []),
                    "matched_subscription_policy_names": summary.get("matched_subscription_policy_names", []),
                    "warnings": summary.get("warnings", []),
                    "approval_outcome": summary.get("approval_outcome"),
                    "approval_recorded_at_utc": summary.get("approval_recorded_at_utc"),
                    "rejection_note": summary.get("rejection_note"),
                    "dead_letter_reason": summary.get("dead_letter_reason"),
                }
            )
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def _approval_queue_row(
    event: dict[str, Any],
    outbox_item: dict[str, Any],
    *,
    session_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = _parse_json_object(event.get("payload_json"))
    summary = _parse_json_object(event.get("route_summary_json"))
    source_session = None
    target_session = None
    if session_lookup:
        source_session = session_lookup.get(event.get("session_id"))
        target_session = session_lookup.get(outbox_item.get("recipient_session_id"))
    return {
        "outbox_item_id": outbox_item.get("outbox_item_id"),
        "event_id": event.get("event_id"),
        "created_at_utc": outbox_item.get("created_at_utc"),
        "source_session_id": event.get("session_id"),
        "source_role": event.get("role"),
        "target_session_id": outbox_item.get("recipient_session_id"),
        "target_role": outbox_item.get("recipient_role"),
        "message_kind": event.get("message_kind"),
        "event_type": event.get("event_type"),
        "approval_state": outbox_item.get("approval_state"),
        "status": outbox_item.get("status"),
        "route_reason": outbox_item.get("route_reason"),
        "approval_recorded_at_utc": outbox_item.get("approval_recorded_at_utc"),
        "dead_letter_reason": outbox_item.get("dead_letter_reason"),
        "task_id": payload.get("task_id"),
        "correlation_id": payload.get("correlation_id"),
        "artifact_refs": payload.get("artifact_refs"),
        "risk_level": payload.get("risk_level"),
        "approval_outcome": summary.get("approval_outcome"),
        "route_profile": summary.get("route_profile"),
        "source_session": source_session,
        "target_session": target_session,
    }


def list_approval_queue(
    repo_root: str | Path,
    *,
    unresolved_only: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        session_rows = conn.execute("SELECT * FROM sessions").fetchall()
        session_lookup = {}
        for row in session_rows:
            session = _row_to_dict(row)
            if session is not None:
                session_lookup[session["session_id"]] = session
        clauses = ["(approval_state = 'pending' OR status = 'awaiting_approval' OR status = 'dead_letter')"]
        if unresolved_only:
            clauses = ["(approval_state = 'pending' OR status = 'awaiting_approval')"]
        rows = conn.execute(
            f"""
            SELECT *
            FROM outbox_items
            WHERE {' AND '.join(clauses)}
            ORDER BY COALESCE(approval_recorded_at_utc, created_at_utc) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        items = []
        for row in rows:
            outbox_item = _row_to_dict(row)
            if outbox_item is None:
                continue
            event_row = conn.execute(
                "SELECT * FROM events WHERE event_id = ?",
                (outbox_item["event_id"],),
            ).fetchone()
            event = _row_to_dict(event_row)
            if event is None:
                continue
            items.append(_approval_queue_row(event, outbox_item, session_lookup=session_lookup))
        return {"ok": True, "count": len(items), "items": items}
    finally:
        conn.close()


def summarize_approval_queue(repo_root: str | Path) -> dict[str, Any]:
    conn = _connect(repo_root)
    try:
        counts = {
            "pending": int(
                conn.execute(
                    "SELECT COUNT(*) FROM outbox_items WHERE approval_state = 'pending' OR status = 'awaiting_approval'"
                ).fetchone()[0]
            ),
            "rejected": int(
                conn.execute("SELECT COUNT(*) FROM outbox_items WHERE approval_state = 'rejected'").fetchone()[0]
            ),
            "approved": int(
                conn.execute("SELECT COUNT(*) FROM outbox_items WHERE approval_state = 'approved'").fetchone()[0]
            ),
            "dead_letter": int(
                conn.execute("SELECT COUNT(*) FROM outbox_items WHERE status = 'dead_letter'").fetchone()[0]
            ),
        }
        unresolved = int(
            conn.execute(
                "SELECT COUNT(*) FROM outbox_items WHERE approval_state = 'pending' OR status = 'awaiting_approval'"
            ).fetchone()[0]
        )
        return {"ok": True, "counts": counts, "unresolved_total": unresolved, "pending_total": counts["pending"]}
    finally:
        conn.close()


def record_hook_session_start(
    repo_root: str | Path,
    session: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = _normalize_session(session, repo_root=repo_root)
    register_session(repo_root, normalized)
    envelope = {
        "session": normalized,
        "event_type": "lifecycle",
        "message_kind": "session_start",
        "target": {"selector_type": "same_run", "allow_followup": True},
        "payload": payload or {"note": "subagent start observed"},
        "requires_approval": False,
        "delivery_mode": "active_followup",
        "followup_message": f"{normalized['role']} started",
    }
    return publish_event(repo_root, envelope, route=True)


def record_hook_session_stop(
    repo_root: str | Path,
    session: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = _normalize_session(session, repo_root=repo_root)
    normalized["is_active"] = False
    register_session(repo_root, normalized)
    envelope = {
        "session": normalized,
        "event_type": "lifecycle",
        "message_kind": "session_stop",
        "target": {"selector_type": "same_run", "allow_followup": True},
        "payload": payload or {"note": "subagent stop observed"},
        "requires_approval": False,
        "delivery_mode": "durable_mailbox",
        "followup_message": f"{normalized['role']} completed",
    }
    return publish_event(repo_root, envelope, route=True)
