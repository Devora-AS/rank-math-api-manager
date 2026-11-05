from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.proof_tiers import PROOF_TIER_CORRELATED, PROOF_TIER_TYPED
from utils.spawn_trace import resolve_trace_run_id, sanitize_run_id

PARENT_OWNED_PATHS = {
    "docs/current-plan.md",
    "docs/session-summary.md",
}
DIRECT_SUBAGENT_PATHS = {
    "build-result.md",
    "verify-result.md",
}
SOURCE_PARENT = "parent"
SOURCE_DIRECT = "direct_subagent"
SOURCE_DESCENDANT = "descendant_subagent"
SOURCE_UNKNOWN = "unknown"
CERTAIN = "certain"
PROBABLE = "probable"
UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class TraceWindow:
    child_id: str
    role: str | None
    start: datetime | None
    stop: datetime | None
    task_id: str | None
    spawn_correlation_id: str | None
    proof_tier: str | None


@dataclass(frozen=True)
class FileAttribution:
    path: str
    source: str
    certainty: str
    confidence: float
    evidence: tuple[str, ...]
    recommended_action: str
    blocker: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "source": self.source,
            "certainty": self.certainty,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "recommended_action": self.recommended_action,
            "blocker": self.blocker,
        }


@dataclass(frozen=True)
class WorktreeAttributionReport:
    repo_root: str
    run_id: str | None
    changed_files: list[str]
    files: list[dict[str, Any]]
    counts: dict[str, int]
    safe_to_continue: bool
    recommendation: str
    evidence_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "run_id": self.run_id,
            "changed_files": self.changed_files,
            "files": self.files,
            "counts": self.counts,
            "safe_to_continue": self.safe_to_continue,
            "recommendation": self.recommendation,
            "evidence_mode": self.evidence_mode,
        }


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
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


def _git_status_changed_files(repo_root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    changed: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            changed.append(path)
    return changed


def _file_mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _load_build_result_changed_files(repo_root: Path) -> set[str]:
    path = repo_root / "build-result.md"
    if not path.is_file():
        return set()
    changed: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- `"):
            continue
        end = stripped.find("`", 3)
        if end == -1:
            continue
        candidate = stripped[3:end]
        if candidate:
            changed.add(candidate)
    return changed


def _load_windows(repo_root: Path, run_id: str) -> list[TraceWindow]:
    rows = _load_jsonl_rows(repo_root / "artifacts" / "agent-traces" / run_id / "events.jsonl")
    by_child: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        kind = _clean_text(row.get("event_kind")) or ""
        child_id = _clean_text(row.get("child_id") or row.get("subagent_id"))
        if not child_id:
            continue
        entry = by_child.setdefault(
            child_id,
            {
                "child_id": child_id,
                "role": _clean_text(row.get("role")),
                "start": None,
                "stop": None,
                "task_id": _clean_text(row.get("task_id")),
                "spawn_correlation_id": _clean_text(row.get("spawn_correlation_id")),
                "proof_tier": _clean_text(row.get("proof_tier")),
            },
        )
        if child_id not in order:
            order.append(child_id)
        if kind in {"subagent_started", "spawn_success"}:
            timestamp = _parse_timestamp(row.get("timestamp"))
            if timestamp is not None and entry["start"] is None:
                entry["start"] = timestamp
            if entry["role"] is None:
                entry["role"] = _clean_text(row.get("role"))
            if entry["task_id"] is None:
                entry["task_id"] = _clean_text(row.get("task_id"))
            if entry["spawn_correlation_id"] is None:
                entry["spawn_correlation_id"] = _clean_text(row.get("spawn_correlation_id"))
            if entry["proof_tier"] is None:
                entry["proof_tier"] = _clean_text(row.get("proof_tier"))
        elif kind in {"subagent_completed", "subagent_stop"}:
            timestamp = _parse_timestamp(row.get("timestamp"))
            if timestamp is not None:
                entry["stop"] = timestamp
            if entry["role"] is None:
                entry["role"] = _clean_text(row.get("role"))
            if entry["task_id"] is None:
                entry["task_id"] = _clean_text(row.get("task_id"))
            if entry["spawn_correlation_id"] is None:
                entry["spawn_correlation_id"] = _clean_text(row.get("spawn_correlation_id"))
            if entry["proof_tier"] is None:
                entry["proof_tier"] = _clean_text(row.get("proof_tier"))
    windows: list[TraceWindow] = []
    for child_id in order:
        entry = by_child[child_id]
        windows.append(
            TraceWindow(
                child_id=child_id,
                role=_clean_text(entry.get("role")),
                start=entry.get("start"),
                stop=entry.get("stop"),
                task_id=_clean_text(entry.get("task_id")),
                spawn_correlation_id=_clean_text(entry.get("spawn_correlation_id")),
                proof_tier=_clean_text(entry.get("proof_tier")),
            )
        )
    return windows


def _window_lineage_tokens(window: TraceWindow) -> set[str]:
    tokens: set[str] = set()
    for value in (window.task_id, window.spawn_correlation_id):
        cleaned = _clean_text(value)
        if cleaned:
            tokens.add(cleaned)
    return tokens


def _strong_lineage_tier(window: TraceWindow) -> bool:
    return window.proof_tier in {PROOF_TIER_CORRELATED, PROOF_TIER_TYPED}


def _direct_windows(windows: list[TraceWindow]) -> list[TraceWindow]:
    return [window for window in windows if window.role in {"builder", "verifier"} and window.start is not None]


def _direct_lineage_tokens(windows: list[TraceWindow]) -> set[str]:
    tokens: set[str] = set()
    for window in windows:
        tokens.update(_window_lineage_tokens(window))
    return tokens


def _window_contains(window: TraceWindow, mtime_epoch: float | None) -> bool:
    if mtime_epoch is None or window.start is None:
        return False
    if mtime_epoch < window.start.timestamp():
        return False
    if window.stop is None:
        return True
    return mtime_epoch <= window.stop.timestamp()


def _root_anchor(windows: list[TraceWindow]) -> datetime | None:
    anchors = [window.start for window in windows if window.start is not None and window.role in {"builder", "verifier"}]
    if not anchors:
        anchors = [window.start for window in windows if window.start is not None]
    if not anchors:
        return None
    return min(anchors)


def _descendant_window_candidates(
    windows: list[TraceWindow],
    *,
    direct_windows: list[TraceWindow],
    direct_lineage_tokens: set[str],
) -> list[TraceWindow]:
    roots = [window for window in direct_windows if window.start is not None]
    if not roots:
        return []
    root_start = min(window.start for window in roots if window.start is not None)
    root_stop_candidates = [window.stop for window in roots if window.stop is not None]
    root_stop = max(root_stop_candidates) if root_stop_candidates else None
    descendants: list[TraceWindow] = []
    for window in windows:
        if window.role in {"builder", "verifier"}:
            continue
        if window.start is None:
            continue
        if not _strong_lineage_tier(window):
            continue
        if not _window_lineage_tokens(window) & direct_lineage_tokens:
            continue
        if window.start < root_start:
            continue
        if root_stop is not None and window.start > root_stop:
            continue
        descendants.append(window)
    return descendants


def _classify_file(
    *,
    repo_root: Path,
    changed_file: str,
    build_result_changes: set[str],
    windows: list[TraceWindow],
    root_anchor: datetime | None,
) -> FileAttribution:
    path = repo_root / changed_file
    mtime = _file_mtime(path)
    evidence: list[str] = []
    certainty = UNCERTAIN
    confidence = 0.2
    source = SOURCE_UNKNOWN
    blocker = True
    recommendation = "investigate"

    if changed_file in PARENT_OWNED_PATHS:
        evidence.append("path_is_parent_owned")
        if root_anchor is not None and (mtime is None or mtime <= root_anchor.timestamp()):
            source = SOURCE_PARENT
            certainty = PROBABLE
            confidence = 0.85
            blocker = False
            recommendation = "continue"
            evidence.append("mtime_precedes_or_matches_active_subagent_start")
            return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)

    if changed_file in build_result_changes:
        evidence.append("listed_in_build_result")
        source = SOURCE_DIRECT
        certainty = CERTAIN
        confidence = 0.98
        blocker = False
        recommendation = "continue"

    direct_windows = _direct_windows(windows)
    direct_lineage_tokens = _direct_lineage_tokens(direct_windows)
    nested_windows = _descendant_window_candidates(
        windows,
        direct_windows=direct_windows,
        direct_lineage_tokens=direct_lineage_tokens,
    )
    for window in nested_windows:
        if _window_contains(window, mtime):
            evidence.append(f"mtime_within_descendant_window:{window.child_id}")
            source = SOURCE_DESCENDANT
            if window.proof_tier in {PROOF_TIER_TYPED, PROOF_TIER_CORRELATED}:
                certainty = PROBABLE
                confidence = 0.9
            else:
                certainty = UNCERTAIN
                confidence = 0.7
            blocker = False
            recommendation = "continue"
            return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)

    for window in direct_windows:
        if _window_contains(window, mtime):
            evidence.append(f"mtime_within_direct_window:{window.child_id}")
            if changed_file in DIRECT_SUBAGENT_PATHS or changed_file in build_result_changes:
                source = SOURCE_DIRECT
                certainty = CERTAIN
                confidence = 0.98
                blocker = False
                recommendation = "continue"
                return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)
            source = SOURCE_DIRECT
            certainty = PROBABLE if _strong_lineage_tier(window) else UNCERTAIN
            confidence = 0.88 if _strong_lineage_tier(window) else 0.6
            blocker = False
            recommendation = "continue"
            if not _strong_lineage_tier(window):
                evidence.append("mtime_within_direct_window_without_strong_lineage_tier")
            return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)

    for window in windows:
        if window.role in {"builder", "verifier"}:
            continue
        if _window_contains(window, mtime):
            evidence.append(f"mtime_within_non_direct_window_without_lineage:{window.child_id}")
            source = SOURCE_UNKNOWN
            certainty = UNCERTAIN
            confidence = 0.25
            blocker = True
            recommendation = "investigate"
            evidence.append("insufficient_lineage_evidence")
            return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)

    if source == SOURCE_DIRECT:
        return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)

    if root_anchor is not None and mtime is not None and mtime <= root_anchor.timestamp() and changed_file in PARENT_OWNED_PATHS:
        evidence.append("mtime_precedes_root_anchor")
        source = SOURCE_PARENT
        certainty = PROBABLE
        confidence = 0.8
        blocker = False
        recommendation = "continue"
        return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)

    if root_anchor is not None and mtime is not None and mtime > root_anchor.timestamp():
        evidence.append("mtime_after_root_anchor_without_trace_evidence")
        source = SOURCE_UNKNOWN
        certainty = UNCERTAIN
        confidence = 0.25
        blocker = True
        recommendation = "investigate"
    elif mtime is None:
        evidence.append("file_missing_or_unreadable")
        source = SOURCE_UNKNOWN
        certainty = UNCERTAIN
        confidence = 0.1
        blocker = True
        recommendation = "investigate"
    else:
        evidence.append("insufficient_trace_evidence")
        source = SOURCE_UNKNOWN
        certainty = UNCERTAIN
        confidence = 0.3
        blocker = True
        recommendation = "investigate"

    return FileAttribution(changed_file, source, certainty, confidence, tuple(evidence), recommendation, blocker)


def classify_worktree_attribution(
    repo_root: Path | str,
    *,
    changed_files: list[str] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    resolved_run_id = sanitize_run_id(run_id or resolve_trace_run_id(root) or "") or None
    changed = changed_files if changed_files is not None else _git_status_changed_files(root)
    windows = _load_windows(root, resolved_run_id) if resolved_run_id else []
    build_result_changes = _load_build_result_changed_files(root)
    anchor = _root_anchor(windows)
    findings = [
        _classify_file(
            repo_root=root,
            changed_file=changed_file,
            build_result_changes=build_result_changes,
            windows=windows,
            root_anchor=anchor,
        )
        for changed_file in changed
    ]
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.source] = counts.get(finding.source, 0) + 1
    safe_to_continue = not any(finding.blocker for finding in findings)
    recommendation = "continue" if safe_to_continue else "investigate"
    evidence_mode = "trace_and_mtime"
    if not resolved_run_id:
        evidence_mode = "mtime_only"
    elif not windows:
        evidence_mode = "trace_id_only"
    return WorktreeAttributionReport(
        repo_root=str(root),
        run_id=resolved_run_id,
        changed_files=changed,
        files=[finding.to_dict() for finding in findings],
        counts=counts,
        safe_to_continue=safe_to_continue,
        recommendation=recommendation,
        evidence_mode=evidence_mode,
    ).to_dict()
