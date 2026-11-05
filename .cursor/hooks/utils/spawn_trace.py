"""Append structured orchestration trace events to artifacts/agent-traces/<run_id>/.

Hook scripts call this when CURSOR_AGENT_TRACE_RUN_ID (or
CURSOR_ORCHESTRATION_TRACE_RUN_ID) resolves from process env or repo-local `.env`.
The Composer parent session cannot be forced to spawn subagents from repository
code; traces record observable hook events and optional operator-recorded parent
decisions with conservative canonical event kinds.
"""

from __future__ import annotations

import json
import importlib.util
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _load_proof_tiers():
    mod_path = Path(__file__).resolve().parent / "proof_tiers.py"
    spec = importlib.util.spec_from_file_location("spawn_trace_proof_tiers", mod_path)
    if not spec or not spec.loader:
        raise RuntimeError("could not load proof tier helpers")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

TRACE_RUN_ENV_KEYS = ("CURSOR_AGENT_TRACE_RUN_ID", "CURSOR_ORCHESTRATION_TRACE_RUN_ID")
LIFECYCLE_EVENT_KINDS = frozenset({"subagent_started", "subagent_completed"})
MODEL_LABEL_ALIASES = {
    "composer_2": "composer-2-model",
    "composer_2_model": "composer-2-model",
    "gpt_5.4": "gpt-5.4",
    "gpt_5_4": "gpt-5.4",
    "gpt_5.4_medium": "gpt-5.4",
    "gpt_5_4_medium": "gpt-5.4",
    "gpt_5.4_mini": "gpt-5.4-mini",
    "gpt_5_4_mini": "gpt-5.4-mini",
    "gpt_5.4_mini_medium": "gpt-5.4-mini",
    "gpt_5_4_mini_medium": "gpt-5.4-mini",
}
_EVENT_KIND_ALIASES = {
    "plan_created": "plan_created",
    "task_assigned": "task_assigned",
    "spawn_requested": "spawn_requested",
    "spawn_failure": "spawn_failure",
    "spawn_failed": "spawn_failure",
    "spawn_success": "subagent_started",
    "subagent_started": "subagent_started",
    "subagent_start": "subagent_started",
    "subagent_completed": "subagent_completed",
    "subagent_complete": "subagent_completed",
    "subagent_stop": "subagent_completed",
    "parent_resume": "parent_resume",
    "inline_absorption_fallback": "inline_absorption_fallback",
    "inline_absorption": "inline_absorption_fallback",
    "inline_fallback": "inline_absorption_fallback",
    "fallback_inline": "inline_absorption_fallback",
    "parent_decision": "parent_decision",
}
_DECISION_KIND_ALIASES = {
    "plan_created": "plan_created",
    "task_assigned": "task_assigned",
    "spawn_requested": "spawn_requested",
    "spawn_failure": "spawn_failure",
    "spawn_failed": "spawn_failure",
    "parent_resume": "parent_resume",
    "inline_absorption_fallback": "inline_absorption_fallback",
    "inline_absorption": "inline_absorption_fallback",
    "inline_fallback": "inline_absorption_fallback",
    "fallback_inline": "inline_absorption_fallback",
}
_DERIVED_COVERAGE_KINDS = {
    "subagent_started": ("spawn_success",),
}


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _default_repo_root() -> Path:
    return Path(
        os.environ.get("CURSOR_PROJECT_DIR")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    ).resolve()


def resolve_repo_root_from_hook_payload(raw: dict[str, Any] | None = None) -> Path:
    """
    Resolve the repo root for hook-side trace artifacts.

    Prefer ``CURSOR_PROJECT_DIR`` / ``CLAUDE_PROJECT_DIR`` when set so hook writers
    share the same root even in multi-root sessions. Otherwise fall back to the first
    non-empty workspace root from the payload, then the current working directory.
    """
    env = (
        os.environ.get("CURSOR_PROJECT_DIR")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or ""
    ).strip()
    if env:
        return Path(env).resolve()

    workspace_roots = (raw or {}).get("workspace_roots") or (raw or {}).get("workspaceRoots")
    if isinstance(workspace_roots, list):
        for item in workspace_roots:
            if item and str(item).strip():
                return Path(str(item).strip()).resolve()
    return Path.cwd().resolve()


def _parse_dotenv_file(path: Path) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, rest = stripped.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        value = rest.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value
    return out


def _read_dotenv_values(path: Path) -> dict[str, str | None]:
    if not path.is_file():
        return {}
    try:
        from dotenv import dotenv_values

        return dict(dotenv_values(path))
    except ImportError:
        return _parse_dotenv_file(path)


def sanitize_run_id(run_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in run_id)[:200]


def resolve_trace_run_id(repo_root: Path | None = None) -> str | None:
    for key in TRACE_RUN_ENV_KEYS:
        raw = os.environ.get(key, "").strip()
        if raw:
            return raw
    env_path = (repo_root or _default_repo_root()) / ".env"
    file_vals = _read_dotenv_values(env_path)
    for key in TRACE_RUN_ENV_KEYS:
        raw = str(file_vals.get(key) or "").strip()
        if raw:
            return raw
    return None


def trace_events_path(repo_root: Path, run_id: str) -> Path:
    safe = sanitize_run_id(run_id)
    return repo_root / "artifacts" / "agent-traces" / safe / "events.jsonl"


def trace_run_dir(repo_root: Path, run_id: str) -> Path:
    return trace_events_path(repo_root, run_id).parent


def normalize_model_label(value: Any) -> str | None:
    raw = _clean_text(value)
    if not raw:
        return None
    return MODEL_LABEL_ALIASES.get(_normalize_key(raw), raw)


def normalize_model_fields(fields: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(fields)
    source_label = (
        _clean_text(normalized.get("model_source_label"))
        or _clean_text(normalized.get("model"))
        or _clean_text(normalized.get("cursor_model"))
    )
    explicit_label = _clean_text(normalized.get("model_label"))
    model_label = normalize_model_label(explicit_label or source_label)
    if model_label:
        normalized["model_label"] = model_label
    else:
        normalized.pop("model_label", None)
    if source_label:
        normalized["model_source_label"] = source_label
    else:
        normalized.pop("model_source_label", None)
    normalized.pop("model", None)
    normalized.pop("cursor_model", None)
    return normalized


def _classify_subagent_proof_tier(row: dict[str, Any]) -> str:
    return _load_proof_tiers().classify_subagent_proof_tier(row)


def lifecycle_pair_key_for_row(row: dict[str, Any]) -> str | None:
    canonical = normalize_trace_event_kind(row.get("event_kind"), row)
    if canonical not in LIFECYCLE_EVENT_KINDS:
        return None
    parts: list[str] = []
    for label, key in (
        ("child", "child_id"),
        ("corr", "spawn_correlation_id"),
        ("task", "task_id"),
        ("role", "role"),
        ("model", "model_label"),
    ):
        value = _clean_text(row.get(key))
        if value:
            parts.append(f"{label}:{value}")
    return "|".join(parts) if parts else None


def _refresh_lifecycle_pair_key(
    event_kind: str, fields: dict[str, Any]
) -> dict[str, Any]:
    pair_key = lifecycle_pair_key_for_row({"event_kind": event_kind, **fields})
    if pair_key:
        fields["lifecycle_pair_key"] = pair_key
    else:
        fields.pop("lifecycle_pair_key", None)
    return fields


def normalize_trace_row_fields(
    event_kind: Any, fields: dict[str, Any] | None = None
) -> tuple[str, dict[str, Any]]:
    row_fields = normalize_model_fields(fields or {})
    normalized_kind = normalize_trace_event_kind(event_kind, row_fields)
    if normalized_kind == "spawn_requested" and not _clean_text(
        row_fields.get("spawn_correlation_id")
    ):
        row_fields["spawn_correlation_id"] = f"spawn-{uuid4().hex[:12]}"
    pair_key = lifecycle_pair_key_for_row(
        {"event_kind": normalized_kind, **row_fields}
    )
    if pair_key:
        row_fields["lifecycle_pair_key"] = pair_key
    else:
        row_fields.pop("lifecycle_pair_key", None)
    return normalized_kind, row_fields


def _subagent_context_path(repo_root: Path, run_id: str, child_id: str) -> Path:
    return (
        trace_run_dir(repo_root, run_id)
        / "_trace-state"
        / "subagents"
        / f"{sanitize_run_id(child_id)}.json"
    )


def _pending_spawn_requests_path(repo_root: Path, run_id: str) -> Path:
    return trace_run_dir(repo_root, run_id) / "_trace-state" / "pending-spawn-requests.json"


def _load_pending_spawn_requests(repo_root: Path, run_id: str) -> list[dict[str, Any]]:
    path = _pending_spawn_requests_path(repo_root, run_id)
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _write_pending_spawn_requests(
    repo_root: Path, run_id: str, items: list[dict[str, Any]]
) -> None:
    path = _pending_spawn_requests_path(repo_root, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


def _trace_context_subset(fields: dict[str, Any]) -> dict[str, Any]:
    subset: dict[str, Any] = {}
    for key in (
        "role",
        "task_id",
        "spawn_correlation_id",
        "role_attribution_source",
        "model_label",
        "model_source_label",
        "lifecycle_match_status",
        "raw_subagent_type",
        "proof_tier",
    ):
        value = fields.get(key)
        if _clean_text(value) is not None:
            subset[key] = value
    return subset


def _has_explicit_start_context(fields: dict[str, Any]) -> bool:
    return any(
        _clean_text(fields.get(key)) is not None
        for key in ("role", "task_id", "spawn_correlation_id")
    )


def _register_pending_spawn_request(
    repo_root: Path, run_id: str, fields: dict[str, Any]
) -> None:
    pending = _load_pending_spawn_requests(repo_root, run_id)
    pending.append(_trace_context_subset(fields))
    _write_pending_spawn_requests(repo_root, run_id, pending)


def _claim_pending_spawn_request(
    repo_root: Path, run_id: str, *, spawn_correlation_id: str | None = None
) -> dict[str, Any] | None:
    pending = _load_pending_spawn_requests(repo_root, run_id)
    if not pending:
        return None
    match_index = 0
    if spawn_correlation_id:
        for idx, item in enumerate(pending):
            if _clean_text(item.get("spawn_correlation_id")) == spawn_correlation_id:
                match_index = idx
                break
    match = pending.pop(match_index)
    _write_pending_spawn_requests(repo_root, run_id, pending)
    return match


def _merge_trace_context(
    fields: dict[str, Any], context: dict[str, Any] | None
) -> dict[str, Any]:
    merged = dict(fields)
    if not context:
        return merged
    for key in (
        "role",
        "task_id",
        "spawn_correlation_id",
        "role_attribution_source",
        "model_label",
        "model_source_label",
        "lifecycle_match_status",
        "raw_subagent_type",
        "proof_tier",
    ):
        if _clean_text(merged.get(key)) is None and _clean_text(context.get(key)) is not None:
            merged[key] = context[key]
    return merged


def persist_subagent_trace_context(
    repo_root: Path, child_id: Any, context: dict[str, Any]
) -> Path | None:
    run_id = resolve_trace_run_id(repo_root)
    child = _clean_text(child_id)
    if not run_id or not child:
        return None
    _, payload = normalize_trace_row_fields("subagent_started", dict(context))
    payload["child_id"] = child
    path = _subagent_context_path(repo_root, run_id, child)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_persisted_subagent_trace_context(
    repo_root: Path, child_id: Any
) -> dict[str, Any] | None:
    run_id = resolve_trace_run_id(repo_root)
    child = _clean_text(child_id)
    if not run_id or not child:
        return None
    path = _subagent_context_path(repo_root, run_id, child)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def ensure_trace_artifact_completeness(repo_root: Path, run_id: str) -> dict[str, str]:
    run_dir = trace_run_dir(repo_root, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        events_path.write_text("", encoding="utf-8")
    transcripts_dir = run_dir / "transcripts"
    transcript_note = run_dir / "transcripts-not-available.txt"
    if transcripts_dir.is_dir():
        if transcript_note.exists():
            try:
                transcript_note.unlink()
            except OSError:
                pass
        transcript_mode = "transcripts_dir"
        transcript_path = str(transcripts_dir)
    else:
        transcript_note.write_text(
            "No transcripts directory was captured for this summarized run.\n",
            encoding="utf-8",
        )
        transcript_mode = "transcripts_not_available"
        transcript_path = str(transcript_note)
    return {
        "run_dir": str(run_dir),
        "events_path": str(events_path),
        "transcript_mode": transcript_mode,
        "transcript_artifact_path": transcript_path,
    }


def append_trace_event_for_run(
    repo_root: Path,
    run_id: str,
    *,
    event_kind: str,
    fields: dict[str, Any],
) -> Path:
    completeness = ensure_trace_artifact_completeness(repo_root, run_id)
    path = Path(completeness["events_path"])
    normalized_kind, normalized_fields = normalize_trace_row_fields(event_kind, fields)

    if normalized_kind == "spawn_requested":
        _register_pending_spawn_request(repo_root, run_id, normalized_fields)
    elif normalized_kind == "subagent_started":
        requested_correlation_id = _clean_text(normalized_fields.get("spawn_correlation_id"))
        pending_context = _claim_pending_spawn_request(
            repo_root, run_id, spawn_correlation_id=requested_correlation_id
        )
        if pending_context:
            normalized_fields = _merge_trace_context(normalized_fields, pending_context)
            normalized_fields["lifecycle_match_status"] = "matched_pending_spawn_request"
        elif _has_explicit_start_context(normalized_fields):
            normalized_fields.setdefault(
                "lifecycle_match_status", "start_context_without_pending_request"
            )
        else:
            normalized_fields["lifecycle_match_status"] = (
                "unmatched_no_pending_spawn_request"
            )
        normalized_fields["proof_tier"] = _classify_subagent_proof_tier(normalized_fields)
        persist_subagent_trace_context(
            repo_root, normalized_fields.get("child_id"), normalized_fields
        )
    elif normalized_kind == "subagent_completed":
        persisted_context = load_persisted_subagent_trace_context(
            repo_root, normalized_fields.get("child_id")
        )
        if persisted_context:
            normalized_fields = _merge_trace_context(normalized_fields, persisted_context)
            normalized_fields.setdefault(
                "lifecycle_match_status",
                persisted_context.get("lifecycle_match_status")
                or "matched_from_persisted_start_context",
            )
        else:
            normalized_fields.setdefault(
                "lifecycle_match_status", "missing_start_context"
            )
        normalized_fields.setdefault("proof_tier", _classify_subagent_proof_tier(normalized_fields))

    if normalized_kind in LIFECYCLE_EVENT_KINDS:
        normalized_fields = _refresh_lifecycle_pair_key(
            normalized_kind, normalized_fields
        )

    row: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_kind": normalized_kind,
        **normalized_fields,
    }
    if normalized_kind != str(event_kind):
        row["source_event_kind"] = str(event_kind)
    coverage_kinds = coverage_event_kinds_for_row(row)
    if coverage_kinds != [normalized_kind]:
        row["coverage_event_kinds"] = coverage_kinds
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def normalize_trace_decision_kind(decision: Any) -> str | None:
    normalized = _DECISION_KIND_ALIASES.get(_normalize_key(decision), "")
    return normalized or None


def normalize_trace_event_kind(
    event_kind: Any, fields: dict[str, Any] | None = None
) -> str:
    raw_key = _normalize_key(event_kind)
    if raw_key == "parent_decision":
        decision_kind = normalize_trace_decision_kind((fields or {}).get("decision"))
        if decision_kind:
            return decision_kind
        return "parent_decision"
    return _EVENT_KIND_ALIASES.get(raw_key, str(event_kind or "unknown").strip() or "unknown")


def coverage_event_kinds_for_row(row: dict[str, Any]) -> list[str]:
    canonical = normalize_trace_event_kind(row.get("event_kind"), row)
    kinds = [canonical]
    for derived in _DERIVED_COVERAGE_KINDS.get(canonical, ()):
        if derived not in kinds:
            kinds.append(derived)
    return kinds


def append_trace_event(
    repo_root: Path,
    *,
    event_kind: str,
    fields: dict[str, Any],
) -> Path | None:
    """Write one JSON line to events.jsonl. Returns path if written, else None."""
    run_id = resolve_trace_run_id(repo_root)
    if not run_id:
        return None
    return append_trace_event_for_run(
        repo_root,
        run_id,
        event_kind=event_kind,
        fields=fields,
    )


def summarize_trace(repo_root: Path, run_id: str) -> dict[str, Any]:
    """Deterministic accounting for contract tests and run summaries."""
    path = trace_events_path(repo_root, run_id)
    counts: dict[str, int] = {}
    coverage_counts: dict[str, int] = {}
    raw_counts: dict[str, int] = {}
    lifecycle_match_counts: dict[str, int] = {}
    model_label_counts: dict[str, int] = {}
    proof_tier_counts: dict[str, int] = {}
    lines = 0
    if not path.exists():
        return {
            "run_id": run_id,
            "lines": 0,
            "counts": counts,
            "coverage_counts": coverage_counts,
            "raw_counts": raw_counts,
            "lifecycle_match_counts": lifecycle_match_counts,
            "model_label_counts": model_label_counts,
            "path": str(path),
        }
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        lines += 1
        try:
            obj = json.loads(line)
            raw_kind = str(obj.get("event_kind", "unknown"))
            kind = normalize_trace_event_kind(raw_kind, obj)
            row_coverage = coverage_event_kinds_for_row(obj)
            lifecycle_match_status = _clean_text(obj.get("lifecycle_match_status"))
            model_label = normalize_model_label(
                obj.get("model_label") or obj.get("model") or obj.get("model_source_label")
            )
            proof_tier = _clean_text(obj.get("proof_tier"))
            if kind == "subagent_started":
                proof_tier = proof_tier or _classify_subagent_proof_tier(obj)
        except json.JSONDecodeError:
            raw_kind = "invalid_json"
            kind = "invalid_json"
            row_coverage = [kind]
            lifecycle_match_status = None
            model_label = None
            proof_tier = None
        raw_counts[raw_kind] = raw_counts.get(raw_kind, 0) + 1
        counts[kind] = counts.get(kind, 0) + 1
        for coverage_kind in row_coverage:
            coverage_counts[coverage_kind] = coverage_counts.get(coverage_kind, 0) + 1
        if lifecycle_match_status:
            lifecycle_match_counts[lifecycle_match_status] = (
                lifecycle_match_counts.get(lifecycle_match_status, 0) + 1
            )
        if model_label:
            model_label_counts[model_label] = model_label_counts.get(model_label, 0) + 1
        if proof_tier:
            proof_tier_counts[proof_tier] = proof_tier_counts.get(proof_tier, 0) + 1
    return {
        "run_id": run_id,
        "lines": lines,
        "counts": counts,
        "coverage_counts": coverage_counts,
        "raw_counts": raw_counts,
        "lifecycle_match_counts": lifecycle_match_counts,
        "model_label_counts": model_label_counts,
        "proof_tier_counts": proof_tier_counts,
        "path": str(path),
    }
