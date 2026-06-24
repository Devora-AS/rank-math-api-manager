#!/usr/bin/env python3
"""Validate closeout summaries against tracked comparison artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

STATUS_NAMES = ("observed", "manual_required", "runtime_blocked")
WORD_TO_INT = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}
COUNT_TOKEN = r"(?P<count>\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)"
STATUS_TOKEN = r"(?P<status>observed|manual_required|runtime_blocked)"
ALL_CASES_PATTERN = re.compile(
    rf"all\s+{COUNT_TOKEN}\s+(?:tracked|required|matrix)(?:\s+matrix)?\s+cases?\s+as\s+`{STATUS_TOKEN}`",
    re.IGNORECASE,
)
STATUS_PAIR_PATTERN = re.compile(
    rf"{COUNT_TOKEN}\s+`{STATUS_TOKEN}`\s+cases?",
    re.IGNORECASE,
)
CLOSEOUT_SECTION_PATTERN = re.compile(
    r"(?ims)^##\s+Closeout(?:\s+\(\d{4}-\d{2}-\d{2}\))?\s*$\s*(?P<body>.*?)(?=^##\s+.+$|\Z)"
)
POSTURE_HINT_PATTERN = re.compile(
    r"(?i)\b(posture|summary|comparison|matrix|tracked\s+.*cases?|required\s+.*cases?)\b"
)


def _count_from_token(raw: str) -> int | None:
    raw = raw.strip().lower()
    if raw.isdigit():
        return int(raw)
    return WORD_TO_INT.get(raw)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_counts(counts: dict[str, int]) -> dict[str, int]:
    return {status: int(counts.get(status, 0)) for status in STATUS_NAMES}


def _extract_status_counts(text: str) -> tuple[dict[str, int], bool]:
    claims: dict[str, int] = {}
    saw_all_cases_pattern = False

    for match in ALL_CASES_PATTERN.finditer(text):
        count = _count_from_token(match.group("count"))
        status = match.group("status").lower()
        if count is None:
            continue
        saw_all_cases_pattern = True
        claims = {name: 0 for name in STATUS_NAMES}
        claims[status] = count

    for match in STATUS_PAIR_PATTERN.finditer(text):
        count = _count_from_token(match.group("count"))
        status = match.group("status").lower()
        if count is None:
            continue
        claims[status] = count

    return _normalize_counts(claims), saw_all_cases_pattern


def _closeout_body(text: str) -> str:
    match = CLOSEOUT_SECTION_PATTERN.search(text)
    if not match:
        return ""
    return match.group("body").strip()


def _extract_posture_claim(text: str, *, surface: str) -> dict[str, int] | None:
    claim_text = text if surface == "session_summary" else _closeout_body(text)
    if not claim_text:
        return None

    counts, saw_all_cases_pattern = _extract_status_counts(claim_text)
    if not any(counts.values()):
        return None

    non_zero_statuses = [status for status, count in counts.items() if count]
    is_posture_claim = (
        surface == "session_summary"
        or saw_all_cases_pattern
        or len(non_zero_statuses) >= 2
        or bool(POSTURE_HINT_PATTERN.search(claim_text))
    )
    if not is_posture_claim:
        return None
    return counts


def _status_counts_from_comparison(path: Path) -> dict[str, int]:
    payload = _read_json(path)
    raw_counts = payload.get("status_counts")
    if not isinstance(raw_counts, dict):
        return {}
    return _normalize_counts(
        {status: int(raw_counts.get(status, 0)) for status in STATUS_NAMES}
    )


def _is_mat_adopted_sidecar_layout(root: Path) -> bool:
    """True when this tree looks like a MAT bootstrap sidecar (not the full MAT source repo)."""
    marker = root / ".mat" / "README.md"
    if not marker.is_file():
        return False
    try:
        head = marker.read_text(encoding="utf-8")[:4000]
    except OSError:
        return False
    return "MAT" in head and "sidecar" in head.lower()


def validate_closeout_coherence(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    comparison_json = root / "artifacts" / "agent-traces" / "comparison.json"
    issues: list[dict[str, str]] = []

    if not comparison_json.is_file():
        if _is_mat_adopted_sidecar_layout(root):
            print(
                "closeout coherence: SKIPPED (no artifacts/agent-traces/comparison.json in this "
                "adopted tree; nothing to cross-check until you add a tracked comparison matrix)"
            )
            return {"ok": True, "issues": [], "skipped": True}
        issues.append(
            {
                "path": str(comparison_json),
                "code": "comparison_json_missing",
                "message": "tracked comparison.json is required for closeout coherence checks",
            }
        )
        return {"ok": False, "issues": issues}

    source_counts = _status_counts_from_comparison(comparison_json)
    for candidate, surface in (
        (root / "build-result.md", "build_result"),
        (root / "verify-result.md", "verify_result"),
        (root / "docs" / "session-summary.md", "session_summary"),
    ):
        if not candidate.is_file():
            continue
        claims = _extract_posture_claim(
            candidate.read_text(encoding="utf-8"), surface=surface
        )
        if claims is None:
            continue
        if claims != source_counts:
            issues.append(
                {
                    "path": str(candidate),
                    "code": "status_claim_mismatch",
                    "message": "status claim does not match artifacts/agent-traces/comparison.json",
                }
            )

    return {"ok": not issues, "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    args = parser.parse_args(argv)
    result = validate_closeout_coherence(args.repo_root)
    if result["ok"]:
        print("closeout coherence: OK")
        return 0
    for issue in result["issues"]:
        print(f"{issue['code']}: {issue['path']} - {issue['message']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
