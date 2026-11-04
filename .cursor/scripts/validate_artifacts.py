#!/usr/bin/env python3
"""
Validate workflow handoff artifacts used by the repo's multi-agent flow.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[1] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from artifact_contract import (
    env_loop_policy_enabled,
    inspect_build_result_contract,
    inspect_verify_result_contract,
    loop_iteration_log_optional_for_slice,
    soft_inspect_typed_output_triad,
)


ATX_HEADING_RE = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)
LAST_UPDATED_RE = re.compile(
    r"^\*\*Last updated:\*\*\s+(\d{4}-\d{2}-\d{2})\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    code: str
    message: str


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, path: Path | str, code: str, message: str) -> None:
        self.issues.append(ValidationIssue(path=str(path), code=code, message=message))

    def ok(self) -> bool:
        return not self.issues


def _read_text(path: Path, result: ValidationResult) -> str | None:
    if not path.exists():
        result.add(path, "missing", "file does not exist")
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        result.add(path, "unreadable", "file could not be read")
        return None
    if b"\x00" in raw:
        result.add(path, "null_byte", "file contains null bytes")
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        result.add(path, "encoding", "file is not valid UTF-8")
        return None


def _validate_generic_markdown(path: Path, result: ValidationResult) -> str | None:
    text = _read_text(path, result)
    if text is None:
        return None
    if not text.strip():
        result.add(path, "empty", "markdown file is empty")
        return text
    if not ATX_HEADING_RE.search(text):
        result.add(path, "structure", "markdown must contain at least one ATX heading")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.rstrip(" \t") != line:
            result.add(
                path,
                "trailing_whitespace",
                f"line {line_no}: trailing whitespace",
            )
    return text


def _extract_section(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group("body")


def _extract_heading_prefix_section(text: str, heading_prefix: str) -> str | None:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading_prefix)}[^\n]*\n(?P<body>.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group("body")


def _validate_json_fences(path: Path, text: str, result: ValidationResult) -> None:
    in_json_fence = False
    fence_start_line = 0
    fence_lines: list[str] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        if not in_json_fence and re.fullmatch(r"```json\s*", line):
            in_json_fence = True
            fence_start_line = line_no
            fence_lines = []
            continue
        if in_json_fence and re.fullmatch(r"```\s*", line):
            payload = "\n".join(fence_lines).strip()
            if payload:
                try:
                    json.loads(payload)
                except json.JSONDecodeError as exc:
                    result.add(
                        path,
                        "json_parse",
                        (
                            "JSON fence starting at "
                            f"line {fence_start_line} is invalid: {exc.msg} "
                            f"(line {exc.lineno}, column {exc.colno})"
                        ),
                    )
            in_json_fence = False
            fence_start_line = 0
            fence_lines = []
            continue
        if in_json_fence:
            fence_lines.append(line)

    if in_json_fence:
        result.add(
            path,
            "json_fence_unclosed",
            f"JSON fence starting at line {fence_start_line} is not closed",
        )


def validate_current_plan(
    path: Path,
    result: ValidationResult,
    *,
    require_closeout: bool = False,
) -> None:
    text = _validate_generic_markdown(path, result)
    if text is None:
        return
    _validate_json_fences(path, text, result)

    if _extract_section(text, "Non-goals") is None:
        result.add(path, "non_goals", "missing '## Non-goals' subsection")

    if require_closeout and _extract_section(text, "Closeout") is None:
        result.add(path, "closeout_section", "missing '## Closeout' subsection")


def validate_long_run_state(
    path: Path,
    result: ValidationResult,
    *,
    today: date | None = None,
    enforce_fresh_last_updated: bool = False,
) -> None:
    text = _validate_generic_markdown(path, result)
    if text is None:
        return
    _validate_json_fences(path, text, result)

    mission_section = _extract_section(text, "Mission")
    if mission_section is None:
        result.add(path, "mission_section", "missing '## Mission' section")
    elif not re.search(
        r"^\s*-\s+\*\*execution_mode:\*\*\s+`(short-run|long-run)`\s*$",
        mission_section,
        re.MULTILINE,
    ):
        result.add(
            path,
            "execution_mode",
            "missing mission-level **execution_mode:** `short-run` or `long-run`",
        )

    mission_gate_section = _extract_heading_prefix_section(
        text,
        "Parent mission gate compliance",
    )
    if mission_gate_section is None:
        result.add(
            path,
            "mission_gate",
            "missing '## Parent mission gate compliance' section",
        )
    elif not mission_gate_section.strip():
        result.add(
            path,
            "mission_gate_entry",
            "'## Parent mission gate compliance' section must not be empty",
        )

    last_updated_match = LAST_UPDATED_RE.search(text)
    if not last_updated_match:
        result.add(
            path,
            "last_updated",
            "missing '**Last updated:** YYYY-MM-DD' line",
        )
    else:
        try:
            parsed = datetime.strptime(last_updated_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            result.add(
                path,
                "last_updated_parse",
                "Last updated must be an ISO date in YYYY-MM-DD format",
            )
        else:
            effective_today = today or date.today()
            if enforce_fresh_last_updated and parsed < effective_today - timedelta(days=30):
                result.add(
                    path,
                    "last_updated_stale",
                    "Last updated is older than 30 days",
                )


def _load_manifest_slice_class(repo_root: Path | None) -> str | None:
    if repo_root is None:
        return None
    manifest_path = repo_root / "artifacts" / "loop" / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    slice_class = data.get("slice_class") if isinstance(data, dict) else None
    if isinstance(slice_class, str) and slice_class.strip():
        return slice_class.strip()
    return None


def _read_plan_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _infer_repo_root_from_paths(paths: dict[str, Path]) -> Path | None:
    current_plan = paths.get("current_plan")
    if current_plan is not None and current_plan.name == "current-plan.md":
        parent = current_plan.parent
        if parent.name == "docs":
            return parent.parent
    build_result = paths.get("build_result")
    if build_result is not None and build_result.name == "build-result.md":
        return build_result.parent
    return None


def validate_build_result(
    path: Path,
    result: ValidationResult,
    *,
    plan_text: str | None = None,
    manifest_slice_class: str | None = None,
    loop_policy_enabled: bool | None = None,
    repo_root: Path | None = None,
) -> None:
    text = _validate_generic_markdown(path, result)
    if text is None:
        return
    _validate_json_fences(path, text, result)
    if loop_policy_enabled is None:
        policy_on = env_loop_policy_enabled(repo_root)
    else:
        policy_on = loop_policy_enabled
    iteration_log_optional = loop_iteration_log_optional_for_slice(
        plan_text,
        manifest_slice_class=manifest_slice_class,
    )
    loop_policy_strict = (
        policy_on
        and plan_text is not None
        and not iteration_log_optional
    )
    for issue in inspect_build_result_contract(
        text,
        loop_policy_strict=loop_policy_strict,
    ).issues:
        result.add(path, issue.code, issue.message)


def validate_verify_result(path: Path, result: ValidationResult) -> None:
    text = _validate_generic_markdown(path, result)
    if text is None:
        return
    _validate_json_fences(path, text, result)
    for issue in inspect_verify_result_contract(text).issues:
        result.add(path, issue.code, issue.message)


def validate_paths(
    paths: dict[str, Path],
    *,
    repo_root: Path | None = None,
    today: date | None = None,
    enforce_fresh_last_updated: bool = False,
    require_current_plan_closeout: bool = False,
    loop_policy_enabled: bool | None = None,
) -> ValidationResult:
    result = ValidationResult()
    effective_repo_root = repo_root or _infer_repo_root_from_paths(paths)
    plan_text: str | None = None
    if "current_plan" in paths:
        validate_current_plan(
            paths["current_plan"],
            result,
            require_closeout=require_current_plan_closeout,
        )
        plan_text = _read_plan_text(paths["current_plan"])
    manifest_slice_class = _load_manifest_slice_class(effective_repo_root)
    if "build_result" in paths:
        validate_build_result(
            paths["build_result"],
            result,
            plan_text=plan_text,
            manifest_slice_class=manifest_slice_class,
            loop_policy_enabled=loop_policy_enabled,
            repo_root=effective_repo_root,
        )
    if "verify_result" in paths:
        validate_verify_result(paths["verify_result"], result)
    if plan_text is not None:
        build_text = (
            _read_plan_text(paths["build_result"])
            if "build_result" in paths
            else None
        )
        verify_text = (
            _read_plan_text(paths["verify_result"])
            if "verify_result" in paths
            else None
        )
        for issue in soft_inspect_typed_output_triad(
            plan_text,
            build_text,
            verify_text,
        ):
            path_key = {
                "typed_triad_plan_ids": "current_plan",
                "typed_triad_build_ids": "build_result",
                "typed_triad_verify_ids": "verify_result",
            }.get(issue.code, "current_plan")
            issue_path = paths.get(path_key, paths["current_plan"])
            result.add(issue_path, issue.code, issue.message)
    if "long_run_state" in paths:
        validate_long_run_state(
            paths["long_run_state"],
            result,
            today=today,
            enforce_fresh_last_updated=enforce_fresh_last_updated,
        )
    return result


def default_repo_paths(repo_root: Path) -> dict[str, Path]:
    return {
        "current_plan": repo_root / "docs" / "current-plan.md",
        "build_result": repo_root / "build-result.md",
        "verify_result": repo_root / "verify-result.md",
        "long_run_state": repo_root / "docs" / "architecture" / "long-run-state.md",
    }


def format_issues(result: ValidationResult) -> str:
    return "\n".join(
        f"{issue.path}: [{issue.code}] {issue.message}" for issue in result.issues
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate workflow markdown artifacts.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to validate",
    )
    parser.add_argument(
        "--strict-long-run-date",
        action="store_true",
        help="Fail when docs/architecture/long-run-state.md is older than 30 days",
    )
    parser.add_argument(
        "--skip-current-plan",
        action="store_true",
        help="Skip docs/current-plan.md validation",
    )
    parser.add_argument(
        "--require-current-plan",
        action="store_true",
        help="Fail early when docs/current-plan.md is missing",
    )
    parser.add_argument(
        "--require-current-plan-closeout",
        action="store_true",
        help="Require '## Closeout' in docs/current-plan.md",
    )
    parser.add_argument(
        "--optional-handoff-artifacts",
        action="store_true",
        help=(
            "When build-result.md or verify-result.md is missing, skip validating those files "
            "(MAT adopted profile: handoffs appear only while a slice is active)."
        ),
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    paths = default_repo_paths(repo_root)

    if args.optional_handoff_artifacts:
        for key, label in (("build_result", "build-result.md"), ("verify_result", "verify-result.md")):
            p = paths[key]
            if not p.is_file():
                paths.pop(key, None)
                print(
                    f"validate_artifacts: optional handoff skip ({label} missing at {p})",
                    file=sys.stderr,
                )

    if args.skip_current_plan:
        paths.pop("current_plan", None)
    elif args.require_current_plan and not paths["current_plan"].exists():
        print(
            f"{paths['current_plan']}: [missing] file does not exist",
            file=sys.stderr,
        )
        return 1

    result = validate_paths(
        paths,
        repo_root=repo_root,
        today=date.today(),
        enforce_fresh_last_updated=args.strict_long_run_date,
        require_current_plan_closeout=args.require_current_plan_closeout,
    )
    if result.ok():
        return 0

    print(format_issues(result), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
