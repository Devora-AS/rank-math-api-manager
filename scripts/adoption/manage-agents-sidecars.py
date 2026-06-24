#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path


POINTER_START = "<!-- MAT_WORKFLOW_POINTER -->"
POINTER_END = "<!-- /MAT_WORKFLOW_POINTER -->"
INLINE_START = "<!-- MAT_WORKFLOW_INLINE_FALLBACK -->"
INLINE_END = "<!-- /MAT_WORKFLOW_INLINE_FALLBACK -->"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".mat",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply non-destructive MAT sidecar pointers to AGENTS.md files."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root containing product-owned AGENTS.md files.",
    )
    parser.add_argument(
        "--inline-fallback",
        "--merge-agents",
        action="store_true",
        dest="inline_fallback",
        help="Write the explicit inline MAT fallback block instead of the pointer note.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without writing files.",
    )
    parser.add_argument(
        "--backup-dir",
        help="Optional directory where pre-edit file backups are written.",
    )
    return parser


def _repo_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"repository root does not exist: {root}")
    return root


def _sidecar_path(repo_root: Path) -> Path:
    return repo_root / ".mat" / "AGENTS.mat.md"


def _relative_sidecar_path(agents_path: Path, sidecar_path: Path) -> str:
    rel = os.path.relpath(sidecar_path, start=agents_path.parent)
    return Path(rel).as_posix()


def _pointer_block(relative_sidecar: str) -> str:
    return (
        f"{POINTER_START}\n"
        "## Multi-agent workflow (MAT)\n\n"
        "This file stays product-owned. The canonical MAT reference lives in "
        f"`{relative_sidecar}`.\n"
        "Use the adoption helper's `--inline-fallback` flag only when you need the "
        "explicit inline MAT section here.\n"
        f"{POINTER_END}\n"
    )


def _inline_block(relative_sidecar: str) -> str:
    return (
        f"{INLINE_START}\n"
        "## Multi-agent workflow (MAT)\n\n"
        "This file stays product-owned. The canonical MAT reference lives in "
        f"`{relative_sidecar}`.\n"
        "This inline fallback is only present because the adoption helper was asked "
        "to write it explicitly.\n"
        f"{INLINE_END}\n"
    )


def _block_for_mode(relative_sidecar: str, inline_fallback: bool) -> str:
    return _inline_block(relative_sidecar) if inline_fallback else _pointer_block(relative_sidecar)


def _find_block_span(text: str, start_marker: str, end_marker: str) -> tuple[int, int] | None:
    start = text.find(start_marker)
    if start == -1:
        return None
    end = text.find(end_marker, start)
    if end == -1:
        return start, len(text)
    return start, end + len(end_marker)


def _replace_named_block(text: str, start_marker: str, end_marker: str, replacement: str) -> tuple[str, bool]:
    span = _find_block_span(text, start_marker, end_marker)
    if span is None:
        return text, False

    start, end = span
    updated = text[:start].rstrip() + "\n\n" + replacement
    if end < len(text):
        trailing = text[end:]
        if not trailing.startswith("\n"):
            updated += "\n"
        updated += trailing.lstrip("\n")
    return updated, updated != text


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def _append_block(text: str, block: str) -> str:
    base = _ensure_trailing_newline(text).rstrip("\n")
    return f"{base}\n\n{block}"


def _apply_desired_block(text: str, desired_block: str, desired_start: str, desired_end: str, alternate_start: str, alternate_end: str) -> tuple[str, bool]:
    updated, changed = _replace_named_block(text, desired_start, desired_end, desired_block)
    if changed:
        return _ensure_trailing_newline(updated), True

    updated, changed = _replace_named_block(text, alternate_start, alternate_end, desired_block)
    if changed:
        return _ensure_trailing_newline(updated), True

    if desired_start in text:
        return text, False

    return _append_block(text, desired_block), True


def _iter_agents_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("AGENTS.md"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.relative_to(repo_root).parts):
            continue
        files.append(path)
    return sorted(files)


def _backup_file(file_path: Path, backup_dir: Path, repo_root: Path) -> Path:
    relative = file_path.relative_to(repo_root)
    backup_path = backup_dir / relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, backup_path)
    return backup_path


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _report(message: str) -> None:
    print(f"manage-agents-sidecars: {message}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repo_root = _repo_root(args.repo_root)
    except ValueError as exc:
        _report(str(exc))
        return 2

    sidecar_path = _sidecar_path(repo_root)
    if not sidecar_path.is_file():
        _report(f"missing canonical sidecar: {sidecar_path}")
        return 2

    agents_files = _iter_agents_files(repo_root)
    if not agents_files:
        _report("no AGENTS.md files found")
        return 0

    if args.backup_dir:
        backup_dir = Path(args.backup_dir).expanduser().resolve()
        if not args.dry_run:
            backup_dir.mkdir(parents=True, exist_ok=True)
    elif args.dry_run:
        backup_dir = None
    else:
        backup_dir = Path(tempfile.mkdtemp(prefix="mat-agents-backup-"))

    if args.dry_run:
        _report("dry-run=yes")
    else:
        _report(f"backup-dir={backup_dir}")

    changed_files: list[Path] = []
    backed_up_files: list[Path] = []

    for agents_path in agents_files:
        current = _load_text(agents_path)
        relative_sidecar = _relative_sidecar_path(agents_path, sidecar_path)
        desired_block = _block_for_mode(relative_sidecar, args.inline_fallback)

        updated, changed = _apply_desired_block(
            current,
            desired_block,
            INLINE_START if args.inline_fallback else POINTER_START,
            INLINE_END if args.inline_fallback else POINTER_END,
            POINTER_START if args.inline_fallback else INLINE_START,
            POINTER_END if args.inline_fallback else INLINE_END,
        )

        if not changed:
            _report(f"unchanged {agents_path.relative_to(repo_root)}")
            continue

        changed_files.append(agents_path.relative_to(repo_root))
        if args.dry_run:
            _report(f"would update {agents_path.relative_to(repo_root)}")
            continue

        assert backup_dir is not None
        backed_up = _backup_file(agents_path, backup_dir, repo_root)
        backed_up_files.append(backed_up)
        _write_text(agents_path, updated)
        _report(f"updated {agents_path.relative_to(repo_root)}")

    if changed_files:
        _report("changed files:")
        for rel in changed_files:
            _report(f"  - {rel.as_posix()}")
    else:
        _report("no changes needed")

    if not args.dry_run and backed_up_files:
        _report("backups:")
        for backup_path in backed_up_files:
            _report(f"  - {backup_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
