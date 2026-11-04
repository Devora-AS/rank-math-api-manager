"""Safe append-only `.gitignore` fragment merge for mat-sync (existing-project adoptions)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BEGIN_MARKER = "# BEGIN MAT git tracking"
END_MARKER = "# END MAT git tracking"

TEMPLATE_BASENAME = "gitignore-mat-existing-project.fragment"

# Minimum negation proving MAT workflow trackability is already patched.
_MAT_WORKFLOW_NEGATION_MARKERS: tuple[str, ...] = (
    "!.cursor/agents/",
    "!.cursor/commands/",
    "!.cursor/hooks/",
)

_NEGATION_SUFFICIENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*\.cursor/\*\s*$"),
)

_REWRITE_REQUIRED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*\.cursor/?\s*$"),
    re.compile(r"^\s*\.cursor/\*\*\s*$"),
    re.compile(r"^\s*\*\*/\.cursor/?\s*$"),
    re.compile(r"^\s*\*\*/\.cursor/\*\*\s*$"),
)

_BROAD_CURSOR_IGNORE_PATTERNS: tuple[re.Pattern[str], ...] = (
    *_NEGATION_SUFFICIENT_PATTERNS,
    *_REWRITE_REQUIRED_PATTERNS,
)

CANONICAL_WORKFLOW_PROBE_PATHS: tuple[str, ...] = (
    ".cursor/hooks.json",
    ".cursor/agents/builder.md",
    ".cursor/commands/mat-sync.md",
    ".cursor/rules/",
)


@dataclass(frozen=True, slots=True)
class GitignoreMergePreview:
    eligible: bool
    lines: list[str]
    skip_reason: str | None
    omniroute_class_blocker: bool = False

    def as_plan_field(self) -> list[str] | None:
        if not self.eligible:
            return None
        return list(self.lines)

    def as_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "lines": list(self.lines),
            "skip_reason": self.skip_reason,
            "omniroute_class_blocker": self.omniroute_class_blocker,
        }


@dataclass(frozen=True, slots=True)
class GitignoreRewritePreview:
    eligible: bool
    mappings: list[dict[str, Any]]
    skip_reason: str | None

    def as_plan_field(self) -> list[dict[str, Any]] | None:
        if not self.eligible or not self.mappings:
            return None
        return [dict(mapping) for mapping in self.mappings]

    def as_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "mappings": [dict(mapping) for mapping in self.mappings],
            "skip_reason": self.skip_reason,
        }


def _resolve_template_path(repo_root: Path) -> Path | None:
    sidecar = repo_root / ".mat" / "docs" / "templates" / TEMPLATE_BASENAME
    if sidecar.is_file():
        return sidecar
    primary = repo_root / "docs" / "templates" / TEMPLATE_BASENAME
    if primary.is_file():
        return primary
    script_primary = Path(__file__).resolve().parents[2] / "docs" / "templates" / TEMPLATE_BASENAME
    if script_primary.is_file():
        return script_primary
    return None


def _meaningful_ignore_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _line_present(root_text: str, pattern: str) -> bool:
    needle = pattern.strip()
    if not needle:
        return True
    if needle in root_text:
        return True
    bare = needle.rstrip("/")
    if bare and bare in root_text:
        return True
    return False


def _has_mat_marker_block(text: str) -> bool:
    return BEGIN_MARKER in text and END_MARKER in text


def _line_in_mat_marker_block(line_index: int, lines: list[str]) -> bool:
    begin_idx: int | None = None
    end_idx: int | None = None
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped == BEGIN_MARKER:
            begin_idx = idx
        elif stripped == END_MARKER:
            end_idx = idx
    if begin_idx is None or end_idx is None or begin_idx >= end_idx:
        return False
    return begin_idx <= line_index <= end_idx


def _match_rewrite_pattern(line: str) -> re.Pattern[str] | None:
    for pattern in _REWRITE_REQUIRED_PATTERNS:
        if pattern.match(line):
            return pattern
    return None


def _rewrite_target_for_line(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("**/"):
        return "**/.cursor/*"
    return ".cursor/*"


def classify_broad_cursor_ignore(text: str) -> dict[str, list[str]]:
    negation_sufficient: list[str] = []
    rewrite_required: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        for pattern in _NEGATION_SUFFICIENT_PATTERNS:
            if pattern.match(line):
                negation_sufficient.append(line)
                break
        else:
            for pattern in _REWRITE_REQUIRED_PATTERNS:
                if pattern.match(line):
                    rewrite_required.append(line)
                    break
    return {
        "negation_sufficient": negation_sufficient,
        "rewrite_required": rewrite_required,
    }


def _has_broad_cursor_ignore(text: str) -> bool:
    classified = classify_broad_cursor_ignore(text)
    return bool(classified["negation_sufficient"] or classified["rewrite_required"])


def _has_mat_workflow_negations(text: str) -> bool:
    return all(_line_present(text, marker) for marker in _MAT_WORKFLOW_NEGATION_MARKERS)


def _detect_omniroute_class_blocker(text: str) -> bool:
    return _has_broad_cursor_ignore(text) and not _has_mat_workflow_negations(text)


def _missing_template_lines(template_text: str, root_text: str) -> list[str]:
    missing: list[str] = []
    for line in _meaningful_ignore_lines(template_text):
        if not _line_present(root_text, line):
            missing.append(line)
    return missing


def compute_gitignore_rewrite_preview(repo_root: Path) -> GitignoreRewritePreview:
    repo_root = repo_root.resolve()
    ignore_path = repo_root / ".gitignore"
    if not ignore_path.is_file():
        return GitignoreRewritePreview(
            eligible=False,
            mappings=[],
            skip_reason="missing_root_gitignore",
        )

    root_lines = ignore_path.read_text(encoding="utf-8").splitlines()
    if _has_mat_marker_block("\n".join(root_lines)):
        return GitignoreRewritePreview(
            eligible=False,
            mappings=[],
            skip_reason="mat_marker_block_present",
        )

    mappings: list[dict[str, Any]] = []
    for line_no, raw in enumerate(root_lines, start=1):
        if _line_in_mat_marker_block(line_no - 1, root_lines):
            continue
        if _match_rewrite_pattern(raw) is None:
            continue
        target = _rewrite_target_for_line(raw)
        current = raw.strip()
        if current == target:
            continue
        mappings.append(
            {
                "line_no": line_no,
                "from": raw,
                "to": _preserve_line_whitespace(raw, target),
            }
        )

    if not mappings:
        return GitignoreRewritePreview(
            eligible=False,
            mappings=[],
            skip_reason="no_rewrite_required_lines",
        )

    return GitignoreRewritePreview(
        eligible=True,
        mappings=mappings,
        skip_reason=None,
    )


def _preserve_line_whitespace(original: str, target: str) -> str:
    leading = original[: len(original) - len(original.lstrip())]
    trailing = original[len(original.rstrip()) :]
    return f"{leading}{target}{trailing}"


def apply_gitignore_rewrite(repo_root: Path, mappings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    preview = compute_gitignore_rewrite_preview(repo_root)
    rewrite_map = mappings if mappings is not None else list(preview.mappings)

    ignore_path = repo_root / ".gitignore"
    if not ignore_path.is_file():
        return {"applied": False, "reason": "missing_root_gitignore", "rewritten_lines": []}

    if not rewrite_map:
        reason = preview.skip_reason or "no_rewrite_required_lines"
        return {"applied": False, "reason": reason, "rewritten_lines": []}

    root_lines = ignore_path.read_text(encoding="utf-8").splitlines(keepends=True)
    plain_lines = [line.rstrip("\n\r") for line in root_lines]
    line_targets: dict[int, str] = {}
    for item in rewrite_map:
        line_no = int(item["line_no"])
        to_value = str(item["to"])
        line_targets[line_no] = to_value

    rewritten: list[str] = []
    new_lines: list[str] = []
    for line_no, raw in enumerate(plain_lines, start=1):
        if line_no in line_targets:
            if _line_in_mat_marker_block(line_no - 1, plain_lines):
                new_lines.append(raw)
                continue
            desired = line_targets[line_no]
            if raw != desired:
                rewritten.append(f"{raw} -> {desired}")
                new_lines.append(desired)
            else:
                new_lines.append(raw)
        else:
            new_lines.append(raw)

    if not rewritten:
        return {"applied": False, "reason": "already_rewritten", "rewritten_lines": []}

    text = "\n".join(new_lines)
    if root_lines and root_lines[-1].endswith("\n"):
        text += "\n"
    ignore_path.write_text(text, encoding="utf-8")
    return {"applied": True, "reason": None, "rewritten_lines": rewritten}


def _parse_check_ignore_match(stdout: str) -> tuple[str, bool]:
    """Return (pattern, is_ignored). Negation patterns (!…) match but do not ignore."""
    line = stdout.strip().split("\n", 1)[0] if stdout.strip() else ""
    if not line:
        return "unknown", True
    pattern = line
    if "\t" in line:
        pattern = line.split("\t", 1)[0].strip()
    if ":" in pattern:
        segments = pattern.split(":")
        if len(segments) >= 3:
            pattern = segments[-1].strip()
    ignored = not pattern.startswith("!")
    return pattern, ignored


def verify_workflow_paths_trackable(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return {
            "trackable": True,
            "still_ignored": [],
            "checked": list(CANONICAL_WORKFLOW_PROBE_PATHS),
            "git_available": False,
        }

    try:
        subprocess.run(
            ["git", "--version"],
            cwd=repo_root,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {
            "trackable": True,
            "still_ignored": [],
            "checked": list(CANONICAL_WORKFLOW_PROBE_PATHS),
            "git_available": False,
        }

    still_ignored: list[dict[str, str]] = []
    checked: list[str] = []
    for probe in CANONICAL_WORKFLOW_PROBE_PATHS:
        checked.append(probe)
        proc = subprocess.run(
            ["git", "check-ignore", "-v", probe],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            rule, ignored = _parse_check_ignore_match(proc.stdout or proc.stderr)
            if ignored:
                still_ignored.append(
                    {
                        "path": probe,
                        "rule": rule,
                    }
                )

    return {
        "trackable": len(still_ignored) == 0,
        "still_ignored": still_ignored,
        "checked": checked,
        "git_available": True,
    }


def compute_gitignore_merge_preview(repo_root: Path) -> GitignoreMergePreview:
    repo_root = repo_root.resolve()
    ignore_path = repo_root / ".gitignore"
    if not ignore_path.is_file():
        return GitignoreMergePreview(
            eligible=False,
            lines=[],
            skip_reason="missing_root_gitignore",
        )

    root_text = ignore_path.read_text(encoding="utf-8")
    omniroute_blocker = _detect_omniroute_class_blocker(root_text)

    if _has_mat_marker_block(root_text):
        return GitignoreMergePreview(
            eligible=True,
            lines=[],
            skip_reason="mat_marker_block_present",
            omniroute_class_blocker=omniroute_blocker,
        )

    template_path = _resolve_template_path(repo_root)
    if template_path is None:
        if not omniroute_blocker:
            return GitignoreMergePreview(
                eligible=False,
                lines=[],
                skip_reason="missing_template_fragment",
            )
        return GitignoreMergePreview(
            eligible=True,
            lines=list(_MAT_WORKFLOW_NEGATION_MARKERS),
            skip_reason=None,
            omniroute_class_blocker=True,
        )

    template_text = template_path.read_text(encoding="utf-8")
    missing = _missing_template_lines(template_text, root_text)
    if not missing:
        return GitignoreMergePreview(
            eligible=True,
            lines=[],
            skip_reason="all_template_fragments_present",
            omniroute_class_blocker=omniroute_blocker,
        )

    return GitignoreMergePreview(
        eligible=True,
        lines=missing,
        skip_reason=None,
        omniroute_class_blocker=omniroute_blocker,
    )


def apply_gitignore_merge(repo_root: Path, lines: list[str] | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    preview = compute_gitignore_merge_preview(repo_root)
    to_append = list(lines) if lines is not None else list(preview.lines)

    ignore_path = repo_root / ".gitignore"
    if not ignore_path.is_file():
        return {"applied": False, "reason": "missing_root_gitignore", "appended_lines": []}

    root_text = ignore_path.read_text(encoding="utf-8")
    if _has_mat_marker_block(root_text):
        return {"applied": False, "reason": "mat_marker_block_present", "appended_lines": []}

    if not preview.eligible:
        return {"applied": False, "reason": preview.skip_reason or "not_eligible", "appended_lines": []}

    if not to_append:
        return {"applied": False, "reason": preview.skip_reason or "nothing_to_append", "appended_lines": []}

    filtered: list[str] = []
    for line in to_append:
        stripped = line.strip()
        if not stripped or _line_present(root_text, stripped):
            continue
        filtered.append(stripped)

    if not filtered:
        return {"applied": False, "reason": "all_lines_already_present", "appended_lines": []}

    block_lines = [BEGIN_MARKER, *filtered, END_MARKER]
    suffix = "\n".join(block_lines)
    if root_text and not root_text.endswith("\n"):
        root_text += "\n"
    if root_text and not root_text.endswith("\n\n"):
        root_text += "\n"
    new_text = root_text + suffix + "\n"
    ignore_path.write_text(new_text, encoding="utf-8")
    return {"applied": True, "reason": None, "appended_lines": filtered}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    preview_cmd = sub.add_parser("preview", help="Emit merge preview JSON")
    preview_cmd.add_argument("--as-plan-field", action="store_true")

    apply_cmd = sub.add_parser("apply", help="Append marked MAT git tracking block")
    apply_cmd.add_argument(
        "--lines-json",
        help="JSON array of lines from plan gitignore_merge_preview (optional)",
    )

    rewrite_preview_cmd = sub.add_parser("rewrite-preview", help="Emit directory-ignore rewrite preview JSON")
    rewrite_preview_cmd.add_argument("--as-plan-field", action="store_true")

    sub.add_parser("rewrite-apply", help="Apply directory-ignore rewrite mappings")

    verify_cmd = sub.add_parser("verify-trackable", help="Verify MAT workflow paths are git-trackable")

    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    if args.command == "preview":
        preview = compute_gitignore_merge_preview(repo_root)
        if args.as_plan_field:
            payload: Any = preview.as_plan_field()
        else:
            payload = preview.as_dict()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "apply":
        lines: list[str] | None = None
        if args.lines_json:
            parsed = json.loads(args.lines_json)
            if not isinstance(parsed, list):
                print("mat_gitignore_merge: --lines-json must be a JSON array", file=sys.stderr)
                return 2
            lines = [str(item) for item in parsed]
        result = apply_gitignore_merge(repo_root, lines=lines)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("applied") or result.get("reason") in {
            "mat_marker_block_present",
            "nothing_to_append",
            "all_lines_already_present",
            "all_template_fragments_present",
        } else 1

    if args.command == "rewrite-preview":
        rewrite_preview = compute_gitignore_rewrite_preview(repo_root)
        if args.as_plan_field:
            rewrite_payload: Any = rewrite_preview.as_plan_field()
        else:
            rewrite_payload = rewrite_preview.as_dict()
        print(json.dumps(rewrite_payload, indent=2, sort_keys=True))
        return 0

    if args.command == "rewrite-apply":
        result = apply_gitignore_rewrite(repo_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("applied") or result.get("reason") in {
            "no_rewrite_required_lines",
            "already_rewritten",
            "mat_marker_block_present",
        } else 1

    if args.command == "verify-trackable":
        result = verify_workflow_paths_trackable(repo_root)
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result.get("git_available"):
            return 0
        if result.get("still_ignored"):
            return 1
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
