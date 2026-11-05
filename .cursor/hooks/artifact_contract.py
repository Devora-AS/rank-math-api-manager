from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from utils.mat_env_resolve import mat_env_flag


BUILD_RESULT_TITLE = "# Build Result"
VERIFY_RESULT_TITLE = "# Verify Result"
CANONICAL_CONTRACT_DOC = "docs/reference/workflow-artifact-contract.md"
MAT_PACKAGED_CONTRACT_DOC = ".mat/docs/workflow-artifact-contract.md"


def resolve_workflow_artifact_contract_doc(repo_root: Path) -> Path | None:
    """Human-readable workflow artifact contract; MAT source prefers root `docs/`, adopted repos ship a `.mat/docs/` copy."""
    root = repo_root.resolve()
    primary = root / "docs" / "reference" / "workflow-artifact-contract.md"
    if primary.is_file():
        return primary
    fallback = root / ".mat" / "docs" / "workflow-artifact-contract.md"
    if fallback.is_file():
        return fallback
    return None


def read_workflow_artifact_contract_text(repo_root: Path) -> str | None:
    path = resolve_workflow_artifact_contract_doc(repo_root)
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None

RESULT_STATUSES = ("PASS", "FAIL", "PARTIAL")
LINT_STATUSES = ("PASS", "FAIL")

TRACE_CORRELATION_HEADING = "Trace Correlation"
LOOP_ITERATION_LOG_HEADING = "Loop Iteration Log"
GATE_EVIDENCE_HEADING = "Gate Evidence"
TRACE_CORRELATION_KNOWN_KEYS = frozenset(
    {
        "session_id",
        "conversation_id",
        "trace_run_id",
        "subagent_id",
        "parent_session_note",
    }
)

_ATX_LEVEL2_SECTION_RE = re.compile(
    r"(?ims)^\s*##\s+(?P<heading>[^\n]+?)\s*$\s*(?P<body>.*?)(?=^\s*##\s+.+$|\Z)"
)
_CLOSEOUT_RE = re.compile(
    r"(?ims)^\s*##\s+Closeout\s+\((?P<date>\d{4}-\d{2}-\d{2})\)\s*$\s*(?P<body>.*?)(?=^\s*##\s+.+$|\Z)"
)
_CRITERION_BULLET_RE = re.compile(r"^[*-]\s+")
_CRITERION_OUTCOME_RE = re.compile(r"(?i):\s*(PASS|FAIL|PARTIAL)\b")
_VERIFY_RESULT_RE = re.compile(r"(?im)^\*\*Result:\*\*\s*(PASS|FAIL|PARTIAL)\b")
_VERIFY_EVIDENCE_RE = re.compile(r"(?im)^\*\*Evidence:\*\*\s*\S")
_VERIFY_CRITERION_RE = re.compile(
    r"(?ims)^\s*###\s+Criterion[^\n]*\n(?P<body>.*?)(?=^\s*###\s+Criterion|\Z)"
)
_AC_ID_BULLET_RE = re.compile(
    r"(?im)^\s*[*-]\s+(?:\[(?:| |x|wip|f)\]\s+)?(?:\*\*)?AC-(?P<number>\d+)(?:\*\*)?\s*:"
)
_VERIFY_CRITERION_ID_RE = re.compile(
    r"(?im)^\s*###\s+Criterion\s+(?P<criterion>\d+)\s*:"
    r"(?:\s*AC-(?P<explicit>\d+)\b)?"
)
_TRACE_CORRELATION_KEY_RE = re.compile(
    r"(?im)^\s*(?:[*-]\s+)?`?(?P<key>[A-Za-z][A-Za-z0-9_-]*)`?\s*:"
)
_LOOP_ITERATION_TABLE_DATA_ROW_RE = re.compile(
    r"^\s*\|\s*(?:\d+|[*-]\s+\d+)"
)


_LOOP_ITERATION_BULLET_RE = re.compile(r"^[*-]\s+")
_GATE_EVIDENCE_BULLET_RE = re.compile(r"^[*-]\s+")
_GATE_EVIDENCE_BULLET_ITEM_RE = re.compile(r"(?i)\bitem\s*:\s*\S")
_GATE_EVIDENCE_BULLET_OK_RE = re.compile(
    r"(?i)\bok\s*:\s*(?:true|false|pass|fail)\b"
)
_GATE_EVIDENCE_OK_VALUES = frozenset({"true", "false", "pass", "fail"})
_PLAN_TIER_LITE_RE = re.compile(r"(?im)^\*\*Tier:\*\*\s*lite\s*$")
_PLAN_SLICE_CLASS_DOCS_RE = re.compile(
    r"(?im)(?:^\*\*slice_class:\*\*\s*`?docs`?|slice_class:\s*`?docs`?)"
)


def env_loop_policy_enabled(repo_root: Path | None = None) -> bool:
    """True when CURSOR_MAT_LOOP_POLICY is opt-in enabled."""
    return mat_env_flag("CURSOR_MAT_LOOP_POLICY", default=False, root=repo_root)


def loop_iteration_log_optional_for_slice(
    plan_text: str | None = None,
    *,
    manifest_slice_class: str | None = None,
) -> bool:
    """Return True when lite/docs slice classes exempt strict iteration-log requirements."""
    if manifest_slice_class:
        if manifest_slice_class.strip().lower() in ("lite", "docs"):
            return True
    if not plan_text:
        return False
    header_region = "\n".join(plan_text.splitlines()[:40])
    if _PLAN_TIER_LITE_RE.search(header_region):
        return True
    if _PLAN_SLICE_CLASS_DOCS_RE.search(header_region):
        return True
    return False


def _is_loop_iteration_table_data_row(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    if re.match(r"^\|\s*[-:]+", stripped):
        return False
    return bool(_LOOP_ITERATION_TABLE_DATA_ROW_RE.match(stripped))


def _is_gate_evidence_table_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped.startswith("|") and re.match(r"^\|\s*[-:]+", stripped))


def _parse_gate_evidence_table_row(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or _is_gate_evidence_table_separator(stripped):
        return None
    parts = [part.strip() for part in stripped.strip("|").split("|")]
    if len(parts) < 2:
        return None
    item, ok_val = parts[0], parts[1]
    if not item or not ok_val:
        return None
    if item.lower() == "item" and ok_val.lower() == "ok":
        return None
    if ok_val.lower() not in _GATE_EVIDENCE_OK_VALUES:
        return None
    return item, ok_val


def _is_gate_evidence_bullet_row(line: str) -> bool:
    stripped = line.strip()
    if not _GATE_EVIDENCE_BULLET_RE.match(stripped):
        return False
    return bool(
        _GATE_EVIDENCE_BULLET_ITEM_RE.search(stripped)
        and _GATE_EVIDENCE_BULLET_OK_RE.search(stripped)
    )


@dataclass(frozen=True)
class ContractIssue:
    code: str
    message: str


@dataclass(frozen=True)
class BuildResultContract:
    issues: tuple[ContractIssue, ...]
    status: str | None
    lint_status: str | None
    acceptance_outcomes: tuple[str, ...]
    closeout_date: str | None


@dataclass(frozen=True)
class VerifyResultContract:
    issues: tuple[ContractIssue, ...]
    status: str | None
    criterion_results: tuple[str, ...]
    closeout_date: str | None


def extract_markdown_section(text: str, heading: str) -> str | None:
    for match in _ATX_LEVEL2_SECTION_RE.finditer(text):
        if match.group("heading").strip() == heading:
            return match.group("body").strip()
    return None


def _extract_markdown_section_with_prefix(
    text: str,
    heading_prefixes: tuple[str, ...],
) -> str | None:
    normalized_prefixes = tuple(prefix.casefold() for prefix in heading_prefixes)
    for match in _ATX_LEVEL2_SECTION_RE.finditer(text):
        heading = match.group("heading").strip().casefold()
        if heading.startswith(normalized_prefixes):
            return match.group("body").strip()
    return None


def _acceptance_ids(section: str | None) -> tuple[str, ...]:
    if not section:
        return ()
    return tuple(f"AC-{match.group('number')}" for match in _AC_ID_BULLET_RE.finditer(section))


def _verify_criterion_ids(section: str | None) -> tuple[str, ...]:
    if not section:
        return ()
    ids: list[str] = []
    for match in _VERIFY_CRITERION_ID_RE.finditer(section):
        number = match.group("explicit") or match.group("criterion")
        ids.append(f"AC-{number}")
    return tuple(ids)


def soft_inspect_typed_output_triad(
    plan_text: str,
    build_text: str | None = None,
    verify_text: str | None = None,
) -> list[ContractIssue]:
    """Align plan AC-N IDs with build bullets and verifier Criterion N headings.

    Plans without typed acceptance IDs are grandfathered. Build and verify
    artifacts are checked only when supplied, so in-progress handoff phases do
    not become a second workflow gate.
    """
    plan_section = _extract_markdown_section_with_prefix(
        plan_text,
        ("Binary acceptance criteria", "Acceptance Criteria"),
    )
    expected = _acceptance_ids(plan_section)
    if not expected:
        return []

    issues: list[ContractIssue] = []
    if len(set(expected)) != len(expected):
        issues.append(
            ContractIssue(
                "typed_triad_plan_ids",
                f"plan acceptance IDs must be unique and ordered; found {', '.join(expected)}",
            )
        )

    if build_text is not None:
        actual_build = _acceptance_ids(
            extract_markdown_section(build_text, "Acceptance Criteria")
        )
        if actual_build != expected:
            issues.append(
                ContractIssue(
                    "typed_triad_build_ids",
                    (
                        "build acceptance IDs must match the plan in order; "
                        f"expected {', '.join(expected)}, found "
                        f"{', '.join(actual_build) or 'none'}"
                    ),
                )
            )

    if verify_text is not None:
        actual_verify = _verify_criterion_ids(
            extract_markdown_section(verify_text, "Criteria Review")
        )
        if actual_verify != expected:
            issues.append(
                ContractIssue(
                    "typed_triad_verify_ids",
                    (
                        "verifier Criterion N headings must match plan AC-N IDs in order; "
                        f"expected {', '.join(expected)}, found "
                        f"{', '.join(actual_verify) or 'none'}"
                    ),
                )
            )

    return issues


def build_result_required_headings() -> tuple[str, ...]:
    return (
        "Task",
        "Status",
        "Changes Made",
        "Acceptance Criteria",
        "Linting / Type-Check",
        "Issues / Blockers",
        "Notes for Verifier",
    )


def verify_result_required_headings() -> tuple[str, ...]:
    return (
        "Plan",
        "Builder Result",
        "Status",
        "Criteria Review",
        "Issues Found",
        "Recommendations",
    )


def soft_inspect_trace_correlation(text: str) -> list[ContractIssue]:
    """Soft-check optional ``## Trace Correlation`` when present; absent → no issues.

    Never add this heading to required headings. Presence/absence must not affect
    MAO build→validate readiness beyond ordinary structural validation when the
    section is malformed.
    """
    section = extract_markdown_section(text, TRACE_CORRELATION_HEADING)
    if section is None:
        return []

    issues: list[ContractIssue] = []
    if not section.strip():
        issues.append(
            ContractIssue(
                "trace_correlation_entry",
                f"'## {TRACE_CORRELATION_HEADING}' subsection must not be empty when present",
            )
        )
        return issues

    keys: list[str] = []
    for line in section.splitlines():
        match = _TRACE_CORRELATION_KEY_RE.match(line.strip())
        if not match:
            continue
        keys.append(match.group("key").strip().lower())

    if keys:
        unknown = sorted({key for key in keys if key not in TRACE_CORRELATION_KNOWN_KEYS})
        if unknown:
            issues.append(
                ContractIssue(
                    "trace_correlation_keys",
                    (
                        f"'## {TRACE_CORRELATION_HEADING}' has unknown key(s): "
                        + ", ".join(unknown)
                        + "; expected subset of "
                        + ", ".join(sorted(TRACE_CORRELATION_KNOWN_KEYS))
                    ),
                )
            )
    else:
        known_mentioned = any(
            re.search(rf"(?i)\b{re.escape(key)}\b", section)
            for key in TRACE_CORRELATION_KNOWN_KEYS
        )
        if not known_mentioned:
            issues.append(
                ContractIssue(
                    "trace_correlation_keys",
                    (
                        f"'## {TRACE_CORRELATION_HEADING}' should name at least one known "
                        "field (session_id, conversation_id, trace_run_id, subagent_id, "
                        "parent_session_note) or use key: value lines"
                    ),
                )
            )

    return issues


def soft_inspect_loop_iteration_log(text: str) -> list[ContractIssue]:
    """Soft-check optional ``## Loop Iteration Log`` when present; absent → no issues."""
    section = extract_markdown_section(text, LOOP_ITERATION_LOG_HEADING)
    if section is None:
        return []

    issues: list[ContractIssue] = []
    if not section.strip():
        issues.append(
            ContractIssue(
                "loop_iteration_log_entry",
                f"'## {LOOP_ITERATION_LOG_HEADING}' subsection must not be empty when present",
            )
        )
        return issues

    has_entry = False
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|"):
            if _is_loop_iteration_table_data_row(stripped):
                has_entry = True
                break
        if _LOOP_ITERATION_BULLET_RE.match(stripped):
            has_entry = True
            break

    if not has_entry:
        issues.append(
            ContractIssue(
                "loop_iteration_log_entries",
                (
                    f"'## {LOOP_ITERATION_LOG_HEADING}' must contain at least one "
                    "table data row or bullet entry when present"
                ),
            )
        )

    return issues


def soft_inspect_gate_evidence(text: str) -> list[ContractIssue]:
    """Soft-check optional ``## Gate Evidence`` when present; absent → no issues."""
    section = extract_markdown_section(text, GATE_EVIDENCE_HEADING)
    if section is None:
        return []

    issues: list[ContractIssue] = []
    if not section.strip():
        issues.append(
            ContractIssue(
                "gate_evidence_entry",
                f"'## {GATE_EVIDENCE_HEADING}' subsection must not be empty when present",
            )
        )
        return issues

    has_entry = False
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _parse_gate_evidence_table_row(stripped):
            has_entry = True
            break
        if _is_gate_evidence_bullet_row(stripped):
            has_entry = True
            break

    if not has_entry:
        issues.append(
            ContractIssue(
                "gate_evidence_entries",
                (
                    f"'## {GATE_EVIDENCE_HEADING}' must contain at least one "
                    "table data row or bullet entry with item and ok fields when present"
                ),
            )
        )

    return issues


def _normalize_gate_evidence_ok(ok_val: str) -> bool | None:
    key = ok_val.strip().lower()
    if key not in _GATE_EVIDENCE_OK_VALUES:
        return None
    return key in ("true", "pass")


def _parse_gate_evidence_bullet_entry(line: str) -> dict[str, object] | None:
    """Extract ``{item, ok, note?}`` from a contract bullet row; None if invalid."""
    stripped = line.strip()
    if not _is_gate_evidence_bullet_row(stripped):
        return None
    item_match = re.search(r"(?i)\bitem\s*:\s*([^|]+?)(?:\s*\||\s*$)", stripped)
    ok_match = re.search(r"(?i)\bok\s*:\s*(true|false|pass|fail)\b", stripped)
    if not item_match or not ok_match:
        return None
    item = item_match.group(1).strip()
    ok = _normalize_gate_evidence_ok(ok_match.group(1))
    if not item or ok is None:
        return None
    entry: dict[str, object] = {"item": item, "ok": ok}
    note_match = re.search(r"(?i)\bnote\s*:\s*(.+)$", stripped)
    if note_match:
        note = note_match.group(1).strip()
        if note:
            entry["note"] = note
    return entry


def parse_gate_evidence_items(text: str) -> list[dict[str, object]]:
    """Parse optional ``## Gate Evidence`` into ``{item, ok, note?}`` rows.

    Missing or empty section → ``[]``. Used by observability B5 and stays aligned
    with soft-validation table/bullet rules above.
    """
    section = extract_markdown_section(text, GATE_EVIDENCE_HEADING)
    if section is None or not section.strip():
        return []

    items: list[dict[str, object]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        table = _parse_gate_evidence_table_row(stripped)
        if table is not None:
            item, ok_val = table
            ok = _normalize_gate_evidence_ok(ok_val)
            if ok is None:
                continue
            entry: dict[str, object] = {"item": item, "ok": ok}
            parts = [part.strip() for part in stripped.strip("|").split("|")]
            if len(parts) >= 3 and parts[2]:
                entry["note"] = parts[2]
            items.append(entry)
            continue
        bullet = _parse_gate_evidence_bullet_entry(stripped)
        if bullet is not None:
            items.append(bullet)
    return items


def strict_inspect_loop_iteration_log(text: str) -> list[ContractIssue]:
    """Require ``## Loop Iteration Log`` when loop policy strict mode applies."""
    section = extract_markdown_section(text, LOOP_ITERATION_LOG_HEADING)
    if section is None:
        return [
            ContractIssue(
                "loop_iteration_log_required",
                (
                    f"missing '## {LOOP_ITERATION_LOG_HEADING}' subsection "
                    "(required when CURSOR_MAT_LOOP_POLICY=1 for orchestrated non-lite/docs runs)"
                ),
            )
        ]
    return soft_inspect_loop_iteration_log(text)


def inspect_build_result_contract(
    text: str,
    *,
    loop_policy_strict: bool = False,
) -> BuildResultContract:
    issues: list[ContractIssue] = []
    if BUILD_RESULT_TITLE not in text:
        issues.append(
            ContractIssue("title", f"missing '{BUILD_RESULT_TITLE}' heading")
        )

    sections = {heading: extract_markdown_section(text, heading) for heading in build_result_required_headings()}
    for heading, code in (
        ("Task", "task"),
        ("Status", "status"),
        ("Changes Made", "changes_made"),
        ("Acceptance Criteria", "acceptance_criteria"),
        ("Linting / Type-Check", "linting_type_check"),
        ("Issues / Blockers", "issues_blockers"),
        ("Notes for Verifier", "notes_for_verifier"),
    ):
        section = sections[heading]
        if section is None:
            issues.append(ContractIssue(code, f"missing '## {heading}' subsection"))
        elif not section.strip():
            issues.append(ContractIssue(f"{code}_entry", f"'## {heading}' subsection must not be empty"))

    status = _parse_status_line(sections.get("Status"), RESULT_STATUSES, allow_status_label=True)
    if sections.get("Status") is not None and status is None:
        issues.append(
            ContractIssue("status_value", "Status must start with PASS, FAIL, or PARTIAL")
        )

    lint_status = _parse_status_line(
        sections.get("Linting / Type-Check"),
        LINT_STATUSES,
        allow_status_label=False,
    )
    if sections.get("Linting / Type-Check") is not None and lint_status is None:
        issues.append(
            ContractIssue(
                "linting_type_check_value",
                "Linting / Type-Check must start with PASS or FAIL",
            )
        )

    acceptance_outcomes: list[str] = []
    acceptance_section = sections.get("Acceptance Criteria")
    if acceptance_section is not None:
        criterion_lines = [
            line.strip()
            for line in acceptance_section.splitlines()
            if _CRITERION_BULLET_RE.match(line.strip())
        ]
        if not criterion_lines:
            issues.append(
                ContractIssue(
                    "acceptance_criteria",
                    "missing bullet entries in '## Acceptance Criteria'",
                )
            )
        else:
            for line in criterion_lines:
                match = _CRITERION_OUTCOME_RE.search(line)
                if not match:
                    issues.append(
                        ContractIssue(
                            "acceptance_criteria_format",
                            "Acceptance Criteria bullets must include PASS, FAIL, or PARTIAL",
                        )
                    )
                    acceptance_outcomes = []
                    break
                acceptance_outcomes.append(match.group(1).upper())

    closeout = _CLOSEOUT_RE.search(text)
    closeout_date: str | None = None
    if not closeout:
        issues.append(
            ContractIssue(
                "closeout_subsection",
                "missing '## Closeout (YYYY-MM-DD)' subsection",
            )
        )
    else:
        closeout_date = closeout.group("date")
        if not closeout.group("body").strip():
            issues.append(
                ContractIssue(
                    "closeout_entry",
                    "'## Closeout (YYYY-MM-DD)' subsection must not be empty",
                )
            )

    issues.extend(soft_inspect_trace_correlation(text))
    if loop_policy_strict:
        issues.extend(strict_inspect_loop_iteration_log(text))
    else:
        issues.extend(soft_inspect_loop_iteration_log(text))
    issues.extend(soft_inspect_gate_evidence(text))

    return BuildResultContract(
        issues=tuple(_dedupe_issues(issues)),
        status=status,
        lint_status=lint_status,
        acceptance_outcomes=tuple(acceptance_outcomes),
        closeout_date=closeout_date,
    )


def inspect_verify_result_contract(text: str) -> VerifyResultContract:
    issues: list[ContractIssue] = []
    if VERIFY_RESULT_TITLE not in text:
        issues.append(
            ContractIssue("title", f"missing '{VERIFY_RESULT_TITLE}' heading")
        )

    sections = {heading: extract_markdown_section(text, heading) for heading in verify_result_required_headings()}
    for heading, code in (
        ("Plan", "plan"),
        ("Builder Result", "builder_result"),
        ("Status", "status"),
        ("Criteria Review", "criteria_review"),
        ("Issues Found", "issues_found"),
        ("Recommendations", "recommendations"),
    ):
        section = sections[heading]
        if section is None:
            issues.append(ContractIssue(code, f"missing '## {heading}' subsection"))
        elif not section.strip():
            issues.append(ContractIssue(f"{code}_entry", f"'## {heading}' subsection must not be empty"))

    status = _parse_status_line(sections.get("Status"), RESULT_STATUSES, allow_status_label=True)
    if sections.get("Status") is not None and status is None:
        issues.append(
            ContractIssue("status_value", "Status must start with PASS, FAIL, or PARTIAL")
        )

    criterion_results: list[str] = []
    criteria_review = sections.get("Criteria Review")
    if criteria_review is not None:
        criterion_blocks = list(_VERIFY_CRITERION_RE.finditer(criteria_review))
        if not criterion_blocks:
            issues.append(
                ContractIssue(
                    "criteria_review_entry",
                    "'## Criteria Review' must contain at least one '### Criterion ...' block",
                )
            )
        else:
            for block in criterion_blocks:
                body = block.group("body").strip()
                result_match = _VERIFY_RESULT_RE.search(body)
                evidence_match = _VERIFY_EVIDENCE_RE.search(body)
                if not result_match:
                    issues.append(
                        ContractIssue(
                            "criteria_review_result",
                            "Each criterion block must include '**Result:** PASS, FAIL, or PARTIAL'",
                        )
                    )
                    break
                if not evidence_match:
                    issues.append(
                        ContractIssue(
                            "criteria_review_evidence",
                            "Each criterion block must include a non-empty '**Evidence:**' line",
                        )
                    )
                    break
                criterion_results.append(result_match.group(1).upper())

    closeout = _CLOSEOUT_RE.search(text)
    closeout_date: str | None = None
    if not closeout:
        issues.append(
            ContractIssue(
                "closeout_subsection",
                "missing '## Closeout (YYYY-MM-DD)' subsection",
            )
        )
    else:
        closeout_date = closeout.group("date")
        if not closeout.group("body").strip():
            issues.append(
                ContractIssue(
                    "closeout_entry",
                    "'## Closeout (YYYY-MM-DD)' subsection must not be empty",
                )
            )

    issues.extend(soft_inspect_trace_correlation(text))

    return VerifyResultContract(
        issues=tuple(_dedupe_issues(issues)),
        status=status,
        criterion_results=tuple(criterion_results),
        closeout_date=closeout_date,
    )


def _parse_status_line(
    section: str | None,
    allowed_values: tuple[str, ...],
    *,
    allow_status_label: bool,
) -> str | None:
    if section is None:
        return None
    first_nonempty = next((line.strip() for line in section.splitlines() if line.strip()), None)
    if not first_nonempty:
        return None
    normalized = first_nonempty.strip()
    if allow_status_label:
        normalized = re.sub(r"(?i)^\*+\s*status\s*:\s*", "", normalized)
        normalized = re.sub(r"(?i)^status\s*:\s*", "", normalized)
    normalized = normalized.strip()
    if normalized.startswith("**") and normalized.endswith("**") and len(normalized) > 4:
        normalized = normalized[2:-2].strip()
    elif normalized.startswith("*") and normalized.endswith("*") and len(normalized) > 2:
        normalized = normalized[1:-1].strip()
    match = re.match(r"^(PASS|FAIL|PARTIAL)\b", normalized, re.IGNORECASE)
    if not match:
        return None
    outcome = match.group(1).upper()
    if outcome not in allowed_values:
        return None
    return outcome


def _dedupe_issues(issues: list[ContractIssue]) -> list[ContractIssue]:
    deduped: list[ContractIssue] = []
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        key = (issue.code, issue.message)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped
