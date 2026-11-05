"""Safe append-only `.cursorignore` fragment merge for mat-sync (warn_first adoptions)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from detect_cost_hygiene_template import detect_cursorignore_template_key  # noqa: E402

BEGIN_MARKER = "# BEGIN MAT runtime fragments"
END_MARKER = "# END MAT runtime fragments"

# Canonical runtime noise lines (shared.inc); used when template parse yields none.
MAT_RUNTIME_FALLBACK_LINES: tuple[str, ...] = (
    "__pycache__/",
    ".cursor/hooks/state/",
    ".cursor/settings.json",
    "artifacts/",
)


@dataclass(frozen=True, slots=True)
class CursorignoreMergePreview:
    eligible: bool
    lines: list[str]
    skip_reason: str | None
    template_key: str | None = None

    def as_plan_field(self) -> list[str] | None:
        if not self.eligible:
            return None
        return list(self.lines)

    def as_dict(self) -> dict[str, Any]:
        return {
            "eligible": self.eligible,
            "lines": list(self.lines),
            "skip_reason": self.skip_reason,
            "template_key": self.template_key,
        }


def _load_adoption(repo_root: Path) -> dict[str, Any] | None:
    path = repo_root / ".mat" / "cost-hygiene-adoption.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _warn_first_preserved(adoption: dict[str, Any] | None) -> bool:
    if not adoption:
        return False
    return (
        adoption.get("enforcement") == "warn_first"
        and adoption.get("bootstrap_mode") == "existing-project"
        and bool(adoption.get("root_cursorignore_preserved"))
    )


def _template_key(repo_root: Path, adoption: dict[str, Any] | None) -> str:
    if adoption and adoption.get("selected_template"):
        return str(adoption["selected_template"])
    return detect_cursorignore_template_key(repo_root).key


def _resolve_template_path(repo_root: Path, template_key: str) -> Path | None:
    basename = f"cursorignore-mat-{template_key}"
    sidecar = repo_root / ".mat" / "docs" / "templates" / basename
    if sidecar.is_file():
        return sidecar
    primary = repo_root / "docs" / "templates" / basename
    if primary.is_file():
        return primary
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


def _missing_template_lines(template_text: str, root_text: str) -> list[str]:
    missing: list[str] = []
    for line in _meaningful_ignore_lines(template_text):
        if not _line_present(root_text, line):
            missing.append(line)
    return missing


def compute_cursorignore_merge_preview(repo_root: Path) -> CursorignoreMergePreview:
    repo_root = repo_root.resolve()
    adoption = _load_adoption(repo_root)
    if not _warn_first_preserved(adoption):
        return CursorignoreMergePreview(
            eligible=False,
            lines=[],
            skip_reason="not_warn_first_preserved",
        )

    ignore_path = repo_root / ".cursorignore"
    if not ignore_path.is_file():
        return CursorignoreMergePreview(
            eligible=False,
            lines=[],
            skip_reason="missing_root_cursorignore",
        )

    root_text = ignore_path.read_text(encoding="utf-8")
    if _has_mat_marker_block(root_text):
        return CursorignoreMergePreview(
            eligible=True,
            lines=[],
            skip_reason="mat_marker_block_present",
            template_key=_template_key(repo_root, adoption),
        )

    key = _template_key(repo_root, adoption)
    template_path = _resolve_template_path(repo_root, key)
    if template_path is None:
        missing = [line for line in MAT_RUNTIME_FALLBACK_LINES if not _line_present(root_text, line)]
        return CursorignoreMergePreview(
            eligible=True,
            lines=missing,
            skip_reason=None if missing else "all_runtime_fragments_present",
            template_key=key,
        )

    template_text = template_path.read_text(encoding="utf-8")
    missing = _missing_template_lines(template_text, root_text)
    if not missing:
        runtime_only = [
            line for line in MAT_RUNTIME_FALLBACK_LINES if not _line_present(root_text, line)
        ]
        return CursorignoreMergePreview(
            eligible=True,
            lines=runtime_only,
            skip_reason=None if runtime_only else "all_template_fragments_present",
            template_key=key,
        )

    return CursorignoreMergePreview(
        eligible=True,
        lines=missing,
        skip_reason=None,
        template_key=key,
    )


def apply_cursorignore_merge(repo_root: Path, lines: list[str] | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    preview = compute_cursorignore_merge_preview(repo_root)
    to_append = list(lines) if lines is not None else list(preview.lines)

    ignore_path = repo_root / ".cursorignore"
    if not ignore_path.is_file():
        return {"applied": False, "reason": "missing_root_cursorignore", "appended_lines": []}

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

    apply_cmd = sub.add_parser("apply", help="Append marked MAT fragment block")
    apply_cmd.add_argument(
        "--lines-json",
        help="JSON array of lines from plan cursorignore_merge_preview (optional)",
    )

    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    if args.command == "preview":
        preview = compute_cursorignore_merge_preview(repo_root)
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
                print("mat_cursorignore_merge: --lines-json must be a JSON array", file=sys.stderr)
                return 2
            lines = [str(item) for item in parsed]
        result = apply_cursorignore_merge(repo_root, lines=lines)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("applied") or result.get("reason") in {
            "mat_marker_block_present",
            "nothing_to_append",
            "all_lines_already_present",
            "all_template_fragments_present",
            "all_runtime_fragments_present",
        } else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
