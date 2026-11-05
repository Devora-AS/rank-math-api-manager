"""Best-effort advisory routing and budget telemetry helpers."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.mat_env_resolve import mat_env_flag, mat_env_get, repo_root

ROUTING_ADVISORY_VERSION = 1
ROUTING_ADVISORY_JSONL_ENV = "CURSOR_MAT_ROUTING_ADVISORY_JSONL"
ROUTING_ADVISORY_PATH_ENV = "CURSOR_MAT_ROUTING_ADVISORY_PATH"
ROUTING_ADVISORY_REL = Path("artifacts") / "mao" / "routing-advisory.jsonl"

ROUTING_REASON_BOUNDED_LOW_RISK = "bounded_low_risk"
ROUTING_REASON_CROSS_FILE_COMPLEXITY = "cross_file_complexity"
ROUTING_REASON_RETRY_ESCALATION = "retry_escalation"
ROUTING_REASON_SAFETY_IMPACT = "safety_impact"
ROUTING_REASON_CONTEXT_PRESSURE = "context_pressure"
ROUTING_REASON_INSUFFICIENT_SIGNAL = "insufficient_signal"

ROUTING_TIER_CHEAP = "cheap"
ROUTING_TIER_STANDARD = "standard"
ROUTING_TIER_STRONG = "strong"

_BOUNDARY_CONTEXT_USAGE_PERCENT = 70
_BOUNDARY_PAYLOAD_CHARS = 6000
_BOUNDARY_MESSAGES_TO_COMPACT = 25

_ACTIONABLE_HINTS = (
    "add",
    "build",
    "debug",
    "docs",
    "fix",
    "implement",
    "migrate",
    "plan",
    "patch",
    "read",
    "refactor",
    "review",
    "ship",
    "test",
    "update",
    "verify",
    "write",
)

_ROUTING_REASON_CODES = {
    ROUTING_REASON_BOUNDED_LOW_RISK,
    ROUTING_REASON_CROSS_FILE_COMPLEXITY,
    ROUTING_REASON_RETRY_ESCALATION,
    ROUTING_REASON_SAFETY_IMPACT,
    ROUTING_REASON_CONTEXT_PRESSURE,
    ROUTING_REASON_INSUFFICIENT_SIGNAL,
}

_SAFETY_KEYWORDS = (
    "security",
    "safety",
    "secrets",
    "secret",
    "auth",
    "oauth",
    "permission",
    "policy",
    "migration",
    "hook",
    "mao",
)

_RETRY_KEYWORDS = (
    "retry",
    "failed",
    "failure",
    "again",
    "re-run",
    "rerun",
    "escalat",
)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_present(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        text = _clean_text(raw.get(key))
        if text is not None:
            return text
    return None


def _session_id_from_raw(raw: dict[str, Any]) -> str | None:
    return _first_present(
        raw,
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "parent_conversation_id",
        "parentConversationId",
        "generation_id",
        "generationId",
        "workspace_id",
        "workspaceId",
        "trace_id",
        "traceId",
        "chat_id",
        "chatId",
        "thread_id",
        "threadId",
    )


def _int_value(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _retry_count_from_raw(raw: dict[str, Any]) -> int | None:
    for key in ("slice_retry_count", "retry_count", "sliceRetryCount", "retryCount"):
        retry_count = _int_value(raw.get(key))
        if retry_count is not None:
            return max(retry_count, 0)

    for key in ("attempt_count", "attemptCount", "attempts", "slice_attempts", "sliceAttempts"):
        attempts = _int_value(raw.get(key))
        if attempts is not None:
            return max(attempts - 1, 0)

    return None


def _context_usage_percent(raw: dict[str, Any]) -> int | None:
    return _int_value(
        raw.get("context_usage_percent")
        or raw.get("contextUsagePercent")
        or raw.get("context_usage")
        or raw.get("contextUsage")
    )


def _messages_to_compact(raw: dict[str, Any]) -> int | None:
    return _int_value(raw.get("messages_to_compact") or raw.get("messagesToCompact"))


def _payload_size_chars(payload_text: str) -> int:
    return len(payload_text.strip())


def _payload_size_bytes(payload_text: str) -> int:
    return len(payload_text.strip().encode("utf-8"))


def _actionable_signal_present(payload_text: str, raw: dict[str, Any]) -> bool:
    lowered = payload_text.lower()
    if any(keyword in lowered for keyword in _ACTIONABLE_HINTS):
        return True

    tool_input = raw.get("tool_input") or raw.get("toolInput")
    if isinstance(tool_input, list):
        return any(_clean_text(item) for item in tool_input)
    if isinstance(tool_input, dict):
        for key in ("path", "paths", "file", "files", "changed_files", "changedFiles"):
            value = tool_input.get(key)
            if isinstance(value, list) and any(_clean_text(item) for item in value):
                return True
            if _clean_text(value):
                return True

    return False


def _multi_file_signal_present(raw: dict[str, Any], payload_text: str) -> bool:
    tool_input = raw.get("tool_input") or raw.get("toolInput")
    if isinstance(tool_input, list):
        return len([item for item in tool_input if _clean_text(item)]) > 1
    if isinstance(tool_input, dict):
        for key in ("files", "paths", "changed_files", "changedFiles"):
            value = tool_input.get(key)
            if isinstance(value, list) and len([item for item in value if _clean_text(item)]) > 1:
                return True
        file_like_values = 0
        for key in ("path", "file_path", "filePath", "selected_file", "selectedFile"):
            if _clean_text(tool_input.get(key)):
                file_like_values += 1
        if file_like_values > 1:
            return True
        if len(tool_input) > 1 and any(
            isinstance(value, list) and len([item for item in value if _clean_text(item)]) > 1
            for value in tool_input.values()
        ):
            return True

    lowered = payload_text.lower()
    file_markers = sum(lowered.count(marker) for marker in (".py", ".md", ".ts", ".tsx", ".json"))
    return file_markers > 1


def _safety_signal_present(payload_text: str) -> bool:
    lowered = payload_text.lower()
    return any(keyword in lowered for keyword in _SAFETY_KEYWORDS)


def _retry_signal_present(payload_text: str, retry_count: int | None) -> bool:
    if retry_count is not None and retry_count >= 2:
        return True
    lowered = payload_text.lower()
    return any(keyword in lowered for keyword in _RETRY_KEYWORDS)


def _next_stronger_tier(tier: str) -> str:
    if tier == ROUTING_TIER_CHEAP:
        return ROUTING_TIER_STANDARD
    if tier == ROUTING_TIER_STANDARD:
        return ROUTING_TIER_STRONG
    return ROUTING_TIER_STRONG


def _build_boundary_signals(
    raw: dict[str, Any],
    payload_text: str,
    *,
    context_usage_percent: int | None,
    messages_to_compact: int | None,
    context_pressure: bool,
) -> dict[str, Any]:
    payload_chars = _payload_size_chars(payload_text)
    payload_bytes = _payload_size_bytes(payload_text)
    return {
        "context_pressure": context_pressure,
        "context_usage_percent": context_usage_percent,
        "messages_to_compact": messages_to_compact,
        "payload_size_chars": payload_chars,
        "payload_size_bytes": payload_bytes,
        "near_context_threshold": context_usage_percent is not None
        and context_usage_percent >= _BOUNDARY_CONTEXT_USAGE_PERCENT,
        "near_messages_threshold": messages_to_compact is not None
        and messages_to_compact >= _BOUNDARY_MESSAGES_TO_COMPACT,
        "near_payload_threshold": payload_chars >= _BOUNDARY_PAYLOAD_CHARS,
        "retry_count": _retry_count_from_raw(raw),
        "multi_file_signal": _multi_file_signal_present(raw, payload_text),
        "safety_signal": _safety_signal_present(payload_text),
    }


def _has_actionable_but_bounded_signal(payload_text: str, raw: dict[str, Any]) -> bool:
    if not payload_text.strip():
        return False
    return len(payload_text.strip()) <= 500 and _actionable_signal_present(payload_text, raw)


def _float_value(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _coerce_text_blob(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(value)


def _payload_text(raw: dict[str, Any], fallback_text: str | None) -> str:
    if fallback_text and fallback_text.strip():
        return fallback_text.strip()
    for key in (
        "prompt",
        "custom_instructions",
        "tool_output",
        "tool_input",
        "toolInput",
        "message",
        "response",
        "final_response",
    ):
        value = raw.get(key)
        if value is None:
            continue
        text = _coerce_text_blob(value).strip()
        if text:
            return text
    return ""


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _context_pressure_from_payload(
    raw: dict[str, Any], payload_text: str, hook_event: str
) -> bool:
    if hook_event == "preCompact":
        return True

    context_usage = _context_usage_percent(raw)
    if context_usage is not None and context_usage >= 70:
        return True

    text_len = _payload_size_chars(payload_text)
    if text_len >= _BOUNDARY_PAYLOAD_CHARS:
        return True

    messages_to_compact = _messages_to_compact(raw)
    if messages_to_compact is not None and messages_to_compact >= _BOUNDARY_MESSAGES_TO_COMPACT:
        return True

    trigger = _clean_text(raw.get("trigger"))
    if trigger and "compact" in trigger.lower():
        return True

    return False


def _derive_routing_reason(raw: dict[str, Any], payload_text: str, context_pressure: bool) -> str:
    if context_pressure:
        return ROUTING_REASON_CONTEXT_PRESSURE

    retry_count = _retry_count_from_raw(raw)
    if _retry_signal_present(payload_text, retry_count):
        return ROUTING_REASON_RETRY_ESCALATION

    if _safety_signal_present(payload_text):
        return ROUTING_REASON_SAFETY_IMPACT

    if _multi_file_signal_present(raw, payload_text):
        return ROUTING_REASON_CROSS_FILE_COMPLEXITY

    if _has_actionable_but_bounded_signal(payload_text, raw):
        return ROUTING_REASON_BOUNDED_LOW_RISK

    return ROUTING_REASON_INSUFFICIENT_SIGNAL


def _derive_routing_tier(reason: str) -> str:
    if reason == ROUTING_REASON_BOUNDED_LOW_RISK:
        return ROUTING_TIER_CHEAP
    if reason == ROUTING_REASON_SAFETY_IMPACT:
        return ROUTING_TIER_STRONG
    return ROUTING_TIER_STANDARD


def build_routing_advisory(
    raw: dict[str, Any],
    hook_event: str,
    *,
    fallback_text: str | None = None,
) -> dict[str, Any]:
    """Build a minimal best-effort routing advisory record.

    The shape is advisory only. Missing fields are normal and remain ``None``.
    """
    payload_text = _payload_text(raw, fallback_text)
    context_pressure = _context_pressure_from_payload(raw, payload_text, hook_event)
    routing_reason = _derive_routing_reason(raw, payload_text, context_pressure)
    routing_tier = _derive_routing_tier(routing_reason)
    context_usage_percent = _context_usage_percent(raw)
    messages_to_compact = _messages_to_compact(raw)
    retry_count = _retry_count_from_raw(raw)
    recommended_escalation = bool(retry_count is not None and retry_count >= 2)
    suggested_tier = _next_stronger_tier(routing_tier) if recommended_escalation else routing_tier
    boundary_signals = _build_boundary_signals(
        raw,
        payload_text,
        context_usage_percent=context_usage_percent,
        messages_to_compact=messages_to_compact,
        context_pressure=context_pressure,
    )

    advisory: dict[str, Any] = {
        "mat_routing_advisory_version": ROUTING_ADVISORY_VERSION,
        "signal_class": "advisory",
        "non_authoritative": True,
        "timestamp": _timestamp_now(),
        "session_id": _session_id_from_raw(raw),
        "source_hook": hook_event,
        "provider": _first_present(raw, "provider", "model_provider", "cursor_provider"),
        "model": _first_present(raw, "model", "cursor_model", "model_name"),
        "routing_tier": routing_tier,
        "routing_reason": routing_reason if routing_reason in _ROUTING_REASON_CODES else ROUTING_REASON_INSUFFICIENT_SIGNAL,
        "suggested_tier": suggested_tier,
        "recommended_escalation": recommended_escalation,
        "budget_note": _budget_note_for(
            hook_event=hook_event,
            context_pressure=context_pressure,
            routing_reason=routing_reason,
            payload_text=payload_text,
        ),
        "context_pressure": context_pressure,
        "context_usage_percent": context_usage_percent,
        "messages_to_compact": messages_to_compact,
        "payload_size_chars": boundary_signals["payload_size_chars"],
        "payload_size_bytes": boundary_signals["payload_size_bytes"],
        "retry_count": retry_count,
        "boundary_signals": boundary_signals,
        "input_tokens": _int_value(
            raw.get("input_tokens")
            or raw.get("inputTokens")
            or raw.get("prompt_tokens")
            or raw.get("promptTokens")
        ),
        "output_tokens": _int_value(
            raw.get("output_tokens")
            or raw.get("outputTokens")
            or raw.get("completion_tokens")
            or raw.get("completionTokens")
        ),
        "cached_tokens": _int_value(raw.get("cached_tokens") or raw.get("cachedTokens")),
        "estimated_cost_usd": _float_value(
            raw.get("estimated_cost_usd")
            or raw.get("estimatedCostUsd")
            or raw.get("cost_usd")
            or raw.get("costUsd")
        ),
    }
    return advisory


def _budget_note_for(
    *,
    hook_event: str,
    context_pressure: bool,
    routing_reason: str,
    payload_text: str,
) -> str | None:
    if context_pressure:
        if hook_event == "preCompact":
            return "Compaction pressure detected; prefer artifact-first handoffs and short excerpts."
        if _payload_size_chars(payload_text) >= _BOUNDARY_PAYLOAD_CHARS:
            return "Large prompt or payload; keep the next turn file-scoped and compact."
        return "Context pressure detected; prefer smaller handoffs and targeted reads."

    if routing_reason == ROUTING_REASON_BOUNDED_LOW_RISK:
        return "Small bounded slice; cheapest honest tier is usually enough."
    if routing_reason == ROUTING_REASON_CROSS_FILE_COMPLEXITY:
        return "Multiple files or cross-cutting scope; keep prompts focused and reviewable."
    if routing_reason == ROUTING_REASON_RETRY_ESCALATION:
        return "Retry surfaced; a stronger advisory tier may be justified."
    if routing_reason == ROUTING_REASON_SAFETY_IMPACT:
        return "Safety-sensitive work; prefer the stronger honest tier and explicit review."
    if len(payload_text) > 0:
        return "Advisory only; exact token and cost data may be absent."
    return "Advisory only; exact token and cost data may be absent."


def routing_advisory_jsonl_path(project_dir: str | Path) -> Path:
    root = Path(project_dir).resolve()
    override = _clean_text(mat_env_get(ROUTING_ADVISORY_PATH_ENV, root=root))
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_absolute():
            return candidate
        return root / candidate
    return root / ROUTING_ADVISORY_REL


def routing_advisory_jsonl_enabled(project_dir: str | Path | None = None) -> bool:
    root = Path(project_dir).resolve() if project_dir is not None else repo_root()
    return mat_env_flag(ROUTING_ADVISORY_JSONL_ENV, default=False, root=root)


def append_routing_advisory_jsonl(
    project_dir: str | Path,
    advisory: dict[str, Any],
    *,
    hook_event: str | None = None,
) -> Path | None:
    """Append the advisory record as JSONL when opt-in is enabled.

    The helper is fail-open: missing env, IO errors, and malformed paths all return
    ``None`` without raising.
    """
    if not routing_advisory_jsonl_enabled(project_dir):
        return None

    root = Path(project_dir).resolve()
    out = routing_advisory_jsonl_path(root)
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(root),
        "source_hook": hook_event or advisory.get("source_hook") or "unknown",
        "advisory": dict(advisory),
    }
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return out
    except (OSError, ValueError):
        return None


def routing_pressure_note(advisory: dict[str, Any]) -> str | None:
    if advisory.get("routing_reason") == ROUTING_REASON_CONTEXT_PRESSURE:
        note = _clean_text(advisory.get("budget_note"))
        if note:
            return note
    return None
