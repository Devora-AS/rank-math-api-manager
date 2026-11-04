from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.mat_env_resolve import mat_env_flag, repo_root
from utils.routing_advisory import routing_advisory_jsonl_path

ROUTING_ROLLUP_VERSION = 1
ROUTING_ROLLUP_ENV = "CURSOR_MAT_ROUTING_ADVISORY_ROLLUP"
ROUTING_ROLLUP_REL = Path("artifacts") / "mao"
ROUTING_ROLLUP_PREFIX = "routing_rollup_"

_KNOWN_COMPLETENESS_FIELDS = (
    "provider",
    "model",
    "input_tokens",
    "output_tokens",
    "estimated_cost_usd",
)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def routing_rollup_enabled() -> bool:
    return mat_env_flag(ROUTING_ROLLUP_ENV, default=True, root=repo_root())


def _sanitize_component(value: Any) -> str:
    text = _clean_text(value) or "unknown"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    safe = safe.strip("._-")
    return safe or "unknown"


def routing_rollup_path(project_dir: str | Path, session_id: str | None) -> Path:
    root = Path(project_dir).resolve()
    safe_session_id = _sanitize_component(session_id)
    return root / ROUTING_ROLLUP_REL / f"{ROUTING_ROLLUP_PREFIX}{safe_session_id}.json"


def _float_value(raw: Any) -> float | None:
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _int_value(raw: Any) -> int | None:
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _extract_record(raw: dict[str, Any]) -> dict[str, Any] | None:
    record = raw.get("advisory")
    if isinstance(record, dict):
        normalized = dict(record)
        for key in ("recorded_at", "project_dir", "source_hook"):
            value = raw.get(key)
            if value is not None and normalized.get(key) is None:
                normalized[key] = value
        if normalized.get("session_id") is None:
            normalized["session_id"] = _clean_text(raw.get("session_id"))
        return normalized
    return dict(raw)


def load_routing_advisory_report(
    project_dir: str | Path,
    *,
    jsonl_path: str | Path | None = None,
    session_id: str | None = None,
    last: int | None = None,
) -> dict[str, Any]:
    source_path = Path(jsonl_path) if jsonl_path else routing_advisory_jsonl_path(project_dir)
    records: list[dict[str, Any]] = []
    malformed_record_count = 0

    try:
        raw_lines = source_path.read_text(encoding="utf-8").splitlines() if source_path.is_file() else []
    except OSError:
        raw_lines = []

    for line in raw_lines:
        text = line.strip()
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            malformed_record_count += 1
            continue
        if not isinstance(parsed, dict):
            malformed_record_count += 1
            continue
        record = _extract_record(parsed)
        if not isinstance(record, dict):
            malformed_record_count += 1
            continue
        records.append(record)

    if session_id is not None:
        wanted = _clean_text(session_id)
        records = [record for record in records if _clean_text(record.get("session_id")) == wanted]

    if last is not None and last >= 0:
        records = records[-last:] if last else []

    return {
        "source_path": str(source_path),
        "records": records,
        "malformed_record_count": malformed_record_count,
    }


def load_routing_rollup_files(project_dir: str | Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    root = Path(project_dir).resolve()
    rollup_dir = root / ROUTING_ROLLUP_REL
    if not rollup_dir.is_dir():
        return []

    files = sorted(
        rollup_dir.glob(f"{ROUTING_ROLLUP_PREFIX}*.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )
    if limit is not None and limit >= 0:
        files = files[:limit]

    loaded: list[dict[str, Any]] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            loaded.append({"path": str(path), "rollup": payload})
    return loaded


def _count_by_field(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = _clean_text(record.get(field)) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _field_present(record: dict[str, Any], field: str) -> bool:
    value = record.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _field_completeness(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    total = len(records)
    present = sum(1 for record in records if _field_present(record, field))
    ratio = round(present / total, 4) if total else None
    return {
        "present": present,
        "missing": total - present,
        "total": total,
        "ratio": ratio,
    }


def _estimated_cost_total(records: list[dict[str, Any]]) -> float | None:
    total = 0.0
    found = False
    for record in records:
        cost = _float_value(record.get("estimated_cost_usd"))
        if cost is None:
            continue
        total += cost
        found = True
    return round(total, 6) if found else None


def summarize_routing_advisories(
    records: list[dict[str, Any]],
    *,
    session_id: str | None = None,
    generated_at: str | None = None,
    source_path: str | None = None,
    malformed_record_count: int = 0,
) -> dict[str, Any]:
    normalized_session_id = _clean_text(session_id)
    if normalized_session_id is None:
        for record in records:
            normalized_session_id = _clean_text(record.get("session_id"))
            if normalized_session_id is not None:
                break

    selected_records = [
        dict(record)
        for record in records
        if normalized_session_id is None or _clean_text(record.get("session_id")) == normalized_session_id
    ]

    counts_by_tier = _count_by_field(selected_records, "routing_tier")
    counts_by_reason = _count_by_field(selected_records, "routing_reason")
    context_pressure_count = sum(1 for record in selected_records if bool(record.get("context_pressure")))
    retry_escalation_count = sum(
        1
        for record in selected_records
        if bool(record.get("recommended_escalation"))
        or _clean_text(record.get("routing_reason")) == "retry_escalation"
        or (_int_value(record.get("retry_count")) or 0) >= 2
    )

    field_completeness = {
        field: _field_completeness(selected_records, field) for field in _KNOWN_COMPLETENESS_FIELDS
    }

    return {
        "rollup_version": ROUTING_ROLLUP_VERSION,
        "session_id": normalized_session_id,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "source_path": source_path,
        "record_count": len(selected_records),
        "malformed_record_count": malformed_record_count,
        "counts_by_tier": counts_by_tier,
        "counts_by_reason": counts_by_reason,
        "context_pressure_count": context_pressure_count,
        "retry_escalation_count": retry_escalation_count,
        "field_completeness": field_completeness,
        "estimated_cost_usd_total": _estimated_cost_total(selected_records),
    }


def write_routing_rollup_json(
    project_dir: str | Path,
    advisory: dict[str, Any],
    *,
    hook_event: str | None = None,
    jsonl_path: str | Path | None = None,
) -> Path | None:
    if not routing_rollup_enabled():
        return None

    root = Path(project_dir).resolve()
    session_id = _clean_text(advisory.get("session_id"))
    report = load_routing_advisory_report(
        root,
        jsonl_path=jsonl_path,
        session_id=session_id,
    )
    records = list(report["records"])

    current = dict(advisory)
    if session_id is None:
        session_id = _clean_text(current.get("session_id")) or "unknown"
    if current.get("session_id") is None:
        current["session_id"] = session_id
    records.append(current)

    summary = summarize_routing_advisories(
        records,
        session_id=session_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_path=report["source_path"],
        malformed_record_count=int(report["malformed_record_count"] or 0),
    )
    summary["source_hook"] = hook_event or advisory.get("source_hook") or "unknown"
    summary["current_session_record_count"] = len(records)

    out = routing_rollup_path(root, session_id)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return out
    except (OSError, ValueError, TypeError):
        return None


def routing_rollup_summary_for_path(path: str | Path) -> dict[str, Any] | None:
    candidate = Path(path)
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict):
        return payload
    return None
