#!/usr/bin/env python3
"""Validate internal markdown links with layout-aware relative resolution.

Policy: docs/reference/doc-link-validation.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

LINK_RE = re.compile(
    r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)"
)

SKIP_PREFIXES = ("http://", "https://", "mailto:")
SKIP_EXACT = {"#"}

DEFAULT_PLANNED_PREFIXES: tuple[str, ...] = (
    "docs/planned/",
)

DEFAULT_OPTIONAL_GLOBS: tuple[str, ...] = (
    "artifacts/mao/gate.json",
    "artifacts/mao/*.jsonl",
)


@dataclass(frozen=True, slots=True)
class LinkIssue:
    source: Path
    target: str
    resolved: Path
    message: str


@dataclass
class ScanResult:
    files_scanned: int = 0
    links_checked: int = 0
    issues: list[LinkIssue] = field(default_factory=list)
    skipped_external: int = 0
    skipped_allowlisted: int = 0


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_allowlist(
    repo_root: Path, *, profile: str = "source"
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    config_path = repo_root / "scripts" / "doc_link_allowlist.json"
    planned = list(DEFAULT_PLANNED_PREFIXES)
    optional = list(DEFAULT_OPTIONAL_GLOBS)
    if config_path.is_file():
        data = json.loads(config_path.read_text(encoding="utf-8"))
        planned.extend(data.get("planned_paths", []))
        optional.extend(data.get("optional_globs", []))
        if profile == "adopted-sidecar":
            planned.extend(data.get("adopted_sidecar_planned_prefixes", []))
            optional.extend(data.get("adopted_sidecar_optional_globs", []))
    return tuple(planned), tuple(optional)


def _glob_match(rel_posix: str, pattern: str) -> bool:
    from fnmatch import fnmatch

    return fnmatch(rel_posix, pattern)


def _is_allowlisted(
    rel_posix: str,
    planned_prefixes: Sequence[str],
    optional_globs: Sequence[str],
) -> bool:
    for prefix in planned_prefixes:
        if rel_posix == prefix.rstrip("/") or rel_posix.startswith(prefix):
            return True
    for pattern in optional_globs:
        if _glob_match(rel_posix, pattern):
            return True
    return False


def _cursor_markdown_roots(repo_root: Path) -> list[Path]:
    return [
        repo_root / ".cursor" / "commands",
        repo_root / ".cursor" / "agents",
        repo_root / ".cursor" / "skills",
        repo_root / ".cursor" / "rules",
    ]


def _iter_markdown_files(repo_root: Path, profile: str) -> Iterable[Path]:
    if profile == "plugin":
        roots = [repo_root / "packages" / "mat-workflow"]
    elif profile == "adopted-fixture":
        roots = [repo_root]
    elif profile == "source-archive":
        roots = [repo_root / "docs" / "archive"]
    elif profile == "adopted-sidecar":
        roots = [repo_root / ".mat" / "docs", *_cursor_markdown_roots(repo_root)]
        mat_readme = repo_root / ".mat" / "README.md"
        if mat_readme.is_file():
            yield mat_readme
    else:
        roots = [
            repo_root / "docs",
            *_cursor_markdown_roots(repo_root),
            repo_root / "packages" / "mat-workflow",
        ]
    suffixes = {".md", ".mdc"}
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix in suffixes and path.is_file():
                if profile == "source":
                    rel = path.relative_to(repo_root)
                    if rel.parts[:2] == ("docs", "archive"):
                        continue
                    if rel.name.startswith("adopted-sidecar-") and rel.parts[:2] == (
                        "docs",
                        "templates",
                    ):
                        continue
                yield path


def _link_resolution_base(source: Path, repo_root: Path) -> Path:
    """Map packaged plugin paths to `.cursor/` for the same relative depth as source."""
    try:
        rel = source.relative_to(repo_root)
    except ValueError:
        return source
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "packages" and parts[1] == "mat-workflow":
        return repo_root / ".cursor" / Path(*parts[2:])
    return source


def _resolve_link(source: Path, raw_target: str, repo_root: Path) -> tuple[Path, str]:
    target = raw_target.strip()
    if not target or target in SKIP_EXACT:
        return repo_root, "skip"
    if any(target.startswith(p) for p in SKIP_PREFIXES):
        return repo_root, "external"
    if target.startswith("#"):
        return repo_root, "anchor"

    path_part, _frag = (target.split("#", 1) + [""])[:2]
    if not path_part:
        return repo_root, "anchor"

    if path_part.startswith("/"):
        resolved = (repo_root / path_part.lstrip("/")).resolve()
    else:
        base = _link_resolution_base(source, repo_root)
        resolved = (base.parent / path_part).resolve()

    return resolved, "internal"


def _adopted_link_rewrite_module():
    import importlib.util
    import sys

    mod_path = Path(__file__).resolve().parent / "adoption" / "adopted_link_rewrite.py"
    if not mod_path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("adopted_link_rewrite", mod_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_adopted_src_dest(repo_root: Path) -> dict[str, str]:
    layout = repo_root / "scripts" / "adoption" / "adoption-layout-v1.json"
    if not layout.is_file():
        return {}
    mod = _adopted_link_rewrite_module()
    if mod is None:
        return {}
    return mod.load_src_dest_map(layout)


def _target_exists(resolved: Path, *, repo_root: Path | None = None, profile: str = "") -> bool:
    if resolved.is_file():
        return True
    if resolved.is_dir():
        for name in ("README.md", "index.md"):
            if (resolved / name).is_file():
                return True
        if any(resolved.rglob("*.md")) or any(resolved.rglob("*.mdc")):
            return True
    if profile == "adopted-sidecar" and repo_root is not None:
        src_dest = _load_adopted_src_dest(repo_root)
        mod = _adopted_link_rewrite_module()
        if src_dest and mod is not None and mod.adopted_link_resolves(resolved, repo_root, src_dest):
            return True
    return False


def scan_repo(
    repo_root: Path,
    profile: str,
    *,
    planned_prefixes: Sequence[str],
    optional_globs: Sequence[str],
) -> ScanResult:
    repo_root = repo_root.resolve()
    result = ScanResult()
    for source in _iter_markdown_files(repo_root, profile):
        result.files_scanned += 1
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in LINK_RE.finditer(text):
            raw = match.group(1)
            resolved, kind = _resolve_link(source, raw, repo_root)
            if kind in {"skip", "external", "anchor"}:
                if kind == "external":
                    result.skipped_external += 1
                continue
            result.links_checked += 1
            rel = _repo_relative(resolved, repo_root)
            if _target_exists(resolved, repo_root=repo_root, profile=profile):
                continue
            if _is_allowlisted(rel, planned_prefixes, optional_globs):
                result.skipped_allowlisted += 1
                continue
            result.issues.append(
                LinkIssue(
                    source=source,
                    target=raw,
                    resolved=resolved,
                    message=f"broken internal link → {rel}",
                )
            )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate internal markdown links.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--profile",
        choices=(
            "source",
            "source-archive",
            "plugin",
            "adopted-fixture",
            "adopted-sidecar",
        ),
        default="source",
    )
    parser.add_argument("--report", action="store_true", help="Print JSON report to stdout")
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Reserved; treat allowlisted missing targets as failures",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = args.repo_root.resolve()
    planned, optional = _load_allowlist(repo_root, profile=args.profile)
    if args.fail_on_warn:
        optional = ()

    result = scan_repo(
        repo_root,
        args.profile,
        planned_prefixes=planned,
        optional_globs=optional,
    )

    if args.report:
        payload = {
            "profile": args.profile,
            "files_scanned": result.files_scanned,
            "links_checked": result.links_checked,
            "skipped_external": result.skipped_external,
            "skipped_allowlisted": result.skipped_allowlisted,
            "issue_count": len(result.issues),
            "issues": [
                {
                    "source": _repo_relative(i.source, repo_root),
                    "target": i.target,
                    "resolved": _repo_relative(i.resolved, repo_root),
                    "message": i.message,
                }
                for i in result.issues
            ],
        }
        print(json.dumps(payload, indent=2))

    for issue in result.issues:
        src = _repo_relative(issue.source, repo_root)
        print(f"{src}: {issue.message} ({issue.target})", file=sys.stderr)

    if result.issues:
        print(
            f"validate_doc_links: {len(result.issues)} broken link(s) "
            f"in {result.files_scanned} file(s)",
            file=sys.stderr,
        )
        return 1

    print(
        f"validate_doc_links: OK ({result.files_scanned} files, "
        f"{result.links_checked} internal links checked)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
