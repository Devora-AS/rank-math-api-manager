from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.mat_env_resolve import mat_env_get, repo_root
from utils.routing_rollup import load_routing_advisory_report, summarize_routing_advisories

PROMPT_LINT_VERSION = 1
PROMPT_SIZE_WARNING_THRESHOLD = 6000
INCLUDED_FILES_WARNING_THRESHOLD = 10
PROMPT_LINT_REL = Path("artifacts") / "mao"
PROMPT_LINT_PREFIX = "prompt_lint_"

_AVOID_LIST_TERMS = ("README.md", "ROADMAP.md", "AGENTS.md")
_BROAD_DOCS_MARKERS = ("docs/*", "docs/**", "full docs", "docs tree", "whole docs", "broad docs")
_RATIONALE_MARKERS = (
    "artifact-first",
    "artifact first",
    "artifact-first rationale",
    "touched paths",
    "bounded context",
    "current-plan.md",
    "build-result.md",
    "verify-result.md",
    "plan + artifacts",
    "plan, build, verify",
)
_FILE_REF_RE = re.compile(
    r"(?<!\w)(?:[\w.-]+/)*[\w.-]+\.(?:md|py|ts|tsx|json|ya?ml|sh|txt)(?!\w)"
)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sanitize_component(value: Any) -> str:
    text = _clean_text(value) or "unknown"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", text)
    safe = safe.strip("._-")
    return safe or "unknown"


def _iter_string_values(value: Any) -> list[str]:
    strings: list[str] = []
    if value is None:
        return strings
    if isinstance(value, str):
        strings.append(value)
        return strings
    if isinstance(value, dict):
        for item in value.values():
            strings.extend(_iter_string_values(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        for item in value:
            strings.extend(_iter_string_values(item))
        return strings
    try:
        strings.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
    except TypeError:
        strings.append(str(value))
    return strings


def _combined_prompt_text(raw: dict[str, Any], fallback_text: str | None = None) -> str:
    if fallback_text and fallback_text.strip():
        return fallback_text.strip()
    for key in (
        "prompt",
        "custom_instructions",
        "tool_output",
        "tool_output_text",
        "toolOutput",
        "tool_input",
        "toolInput",
        "message",
        "response",
        "final_response",
    ):
        value = raw.get(key)
        if value is None:
            continue
        strings = _iter_string_values(value)
        text = "\n".join(part for part in strings if part.strip()).strip()
        if text:
            return text
    return ""


def _collect_file_references(raw: dict[str, Any], prompt_text: str) -> list[str]:
    refs: set[str] = set()
    for candidate in _iter_string_values(raw):
        for match in _FILE_REF_RE.findall(candidate):
            refs.add(match)
    for match in _FILE_REF_RE.findall(prompt_text):
        refs.add(match)
    return sorted(refs)


def _has_rationale(raw: dict[str, Any], prompt_text: str) -> bool:
    if raw.get("artifact_first_rationale") is True or raw.get("artifactFirstRationale") is True:
        return True
    lowered = prompt_text.lower()
    return any(marker in lowered for marker in _RATIONALE_MARKERS)


def _avoid_list_hits(raw: dict[str, Any], prompt_text: str) -> list[str]:
    lowered = prompt_text.lower()
    hits: list[str] = []
    for term in _AVOID_LIST_TERMS:
        if term.lower() in lowered:
            hits.append(term)
    for marker in _BROAD_DOCS_MARKERS:
        if marker in lowered:
            hits.append(marker)
    if not hits:
        return []
    if _has_rationale(raw, prompt_text):
        return []
    return sorted(set(hits))


def build_prompt_lint_report(
    raw: dict[str, Any],
    *,
    fallback_text: str | None = None,
    session_id: str | None = None,
    hook_event: str | None = None,
) -> dict[str, Any]:
    prompt_text = _combined_prompt_text(raw, fallback_text)
    prompt_size_chars = len(prompt_text.strip())
    file_refs = _collect_file_references(raw, prompt_text)
    avoid_hits = _avoid_list_hits(raw, prompt_text)
    warnings: list[dict[str, Any]] = []

    if prompt_size_chars >= PROMPT_SIZE_WARNING_THRESHOLD:
        warnings.append(
            {
                "code": "prompt_too_large",
                "message": (
                    f"Combined prompt size {prompt_size_chars} exceeds advisory threshold "
                    f"{PROMPT_SIZE_WARNING_THRESHOLD}."
                ),
            }
        )

    if len(file_refs) > INCLUDED_FILES_WARNING_THRESHOLD:
        warnings.append(
            {
                "code": "too_many_files",
                "message": (
                    f"Included file references {len(file_refs)} exceeds advisory threshold "
                    f"{INCLUDED_FILES_WARNING_THRESHOLD}."
                ),
            }
        )

    if avoid_hits:
        warnings.append(
            {
                "code": "avoid_list_docs_without_rationale",
                "message": (
                    "Avoid-list docs or broad docs reads were detected without an explicit "
                    f"artifact-first rationale: {', '.join(avoid_hits)}."
                ),
            }
        )

    return {
        "prompt_lint_version": PROMPT_LINT_VERSION,
        "signal_class": "advisory",
        "non_authoritative": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": _clean_text(session_id),
        "source_hook": hook_event,
        "prompt_size_chars": prompt_size_chars,
        "included_files_count": len(file_refs),
        "included_files": file_refs,
        "avoid_list_hits": avoid_hits,
        "artifact_first_rationale": _has_rationale(raw, prompt_text),
        "warning_count": len(warnings),
        "warnings": warnings,
    }


def prompt_lint_log_path(project_dir: str | Path, session_id: str | None) -> Path:
    root = Path(project_dir).resolve()
    safe_session_id = _sanitize_component(session_id)
    return root / PROMPT_LINT_REL / f"{PROMPT_LINT_PREFIX}{safe_session_id}.log"


def append_prompt_lint_log(project_dir: str | Path, report: dict[str, Any]) -> Path | None:
    warnings = report.get("warnings") or []
    if not isinstance(warnings, list) or not warnings:
        return None

    root = Path(project_dir).resolve()
    out = prompt_lint_log_path(root, report.get("session_id"))
    payload = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(root),
        "source_hook": report.get("source_hook") or "unknown",
        "prompt_lint": dict(report),
    }
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return out
    except (OSError, ValueError, TypeError):
        return None


def _session_budget_threshold_usd(project_dir: str | Path | None = None) -> float | None:
    root = Path(project_dir).resolve() if project_dir is not None else repo_root()
    raw = _clean_text(mat_env_get("CURSOR_MAT_SESSION_BUDGET_USD", root=root))
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


def append_session_budget_advisory_note(
    project_dir: str | Path,
    session_id: str | None,
    *,
    jsonl_path: str | Path | None = None,
    threshold_usd: float | None = None,
) -> dict[str, Any]:
    threshold = (
        threshold_usd
        if threshold_usd is not None
        else _session_budget_threshold_usd(project_dir)
    )
    session_id_text = _clean_text(session_id)
    if threshold is None or session_id_text is None:
        return {
            "note_written": False,
            "reason": "threshold_unset" if threshold is None else "missing_session_id",
            "session_id": session_id_text,
            "threshold_usd": threshold,
        }

    root = Path(project_dir).resolve()
    report = load_routing_advisory_report(root, jsonl_path=jsonl_path, session_id=session_id_text)
    summary = summarize_routing_advisories(
        report["records"],
        session_id=session_id_text,
        source_path=report["source_path"],
        malformed_record_count=int(report["malformed_record_count"] or 0),
    )
    total_estimated_cost = summary.get("estimated_cost_usd_total")
    cost_completeness = summary.get("field_completeness", {}).get("estimated_cost_usd", {})
    present_cost_count = int(cost_completeness.get("present") or 0)
    total_records = int(summary.get("record_count") or 0)

    if total_estimated_cost is None or total_estimated_cost <= threshold:
        return {
            "note_written": False,
            "reason": "missing_or_below_threshold",
            "session_id": session_id_text,
            "threshold_usd": threshold,
            "estimated_cost_usd_total": total_estimated_cost,
            "present_cost_count": present_cost_count,
            "record_count": total_records,
        }

    budget_note = [
        "## Advisory Session Budget Note",
        f"- Advisory only: best-effort estimated routing cost for session `{session_id_text}` is about "
        f"`${total_estimated_cost:.2f}` based on {present_cost_count} of {total_records} routing advisories "
        f"with `estimated_cost_usd` present.",
        f"- This approximate estimate exceeds the advisory threshold of `${threshold:.2f}` and may be incomplete "
        "because some routing advisories omit cost fields; it does not enforce a budget or imply routing failure.",
    ]
    note_text = "\n".join(budget_note) + "\n"
    summary_path = root / "docs" / "session-summary.md"

    try:
        existing = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
    except OSError:
        existing = ""

    if session_id_text in existing and "Advisory Session Budget Note" in existing:
        return {
            "note_written": False,
            "reason": "already_present",
            "session_id": session_id_text,
            "threshold_usd": threshold,
            "estimated_cost_usd_total": total_estimated_cost,
            "present_cost_count": present_cost_count,
            "record_count": total_records,
            "summary_path": str(summary_path),
        }

    try:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        new_text = existing.rstrip()
        if new_text:
            new_text += "\n\n"
        new_text += note_text
        summary_path.write_text(new_text, encoding="utf-8")
        return {
            "note_written": True,
            "reason": "threshold_exceeded",
            "session_id": session_id_text,
            "threshold_usd": threshold,
            "estimated_cost_usd_total": total_estimated_cost,
            "present_cost_count": present_cost_count,
            "record_count": total_records,
            "summary_path": str(summary_path),
            "note_text": note_text,
        }
    except (OSError, ValueError, TypeError):
        return {
            "note_written": False,
            "reason": "write_failed",
            "session_id": session_id_text,
            "threshold_usd": threshold,
            "estimated_cost_usd_total": total_estimated_cost,
            "present_cost_count": present_cost_count,
            "record_count": total_records,
            "summary_path": str(summary_path),
        }
