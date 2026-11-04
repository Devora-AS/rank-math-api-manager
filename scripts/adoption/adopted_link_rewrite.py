"""Rewrite and resolve markdown links for adopted MAT sidecar layouts."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Mapping
from urllib.parse import urldefrag, urlsplit

LINK_RE = re.compile(r"(!?\[[^\]]*\]\()([^)\s]+)([^)]*\))")

_STANDALONE_ROOT_DOCS = re.compile(r"(?<!\.mat/)docs/workflow-artifact-contract\.md")


def load_src_dest_map(layout_path: Path) -> dict[str, str]:
    """Return posix src path (e.g. docs/reference/foo.md) -> dest (.mat/docs/foo.md)."""
    data = json.loads(layout_path.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for key in ("mat_docs", "mat_loop"):
        for item in data.get(key, []):
            if not isinstance(item, dict):
                continue
            src = item.get("src")
            dest = item.get("dest")
            if isinstance(src, str) and isinstance(dest, str):
                mapping[src.replace("\\", "/")] = dest.replace("\\", "/")
    return mapping


def _posix_relpath(from_dir: Path, to_file: Path) -> str:
    return os.path.relpath(to_file, from_dir).replace("\\", "/")


def _map_link_path(
    path_part: str,
    src_dest: Mapping[str, str],
    *,
    source_file: Path,
    repo_root: Path,
) -> str:
    if not path_part or path_part.startswith(("http://", "https://", "mailto:", "#")):
        return path_part

    split = urlsplit(path_part)
    frag = split.fragment
    path_only = split.path
    if not path_only:
        return path_part

    rest = path_only.replace("\\", "/")
    while rest.startswith("../"):
        rest = rest[3:]
    if rest.startswith(".mat/docs/.mat/docs/"):
        rest = rest.replace(".mat/docs/.mat/docs/", ".mat/docs/", 1)
    if rest.startswith(".mat/docs/"):
        candidate = (source_file.parent / path_only).resolve()
        if candidate.is_file():
            return path_part

    mapped_dest: str | None = None
    if rest in src_dest:
        mapped_dest = src_dest[rest]
    else:
        for src, dest in sorted(src_dest.items(), key=lambda kv: len(kv[0]), reverse=True):
            if rest == src or rest.endswith("/" + src):
                mapped_dest = dest
                break

    if mapped_dest is None:
        if path_only == "../../docs/workflow-artifact-contract.md":
            mapped_dest = ".mat/docs/workflow-artifact-contract.md"
        elif _STANDALONE_ROOT_DOCS.fullmatch(path_only.strip("/")):
            mapped_dest = ".mat/docs/workflow-artifact-contract.md"
        else:
            return path_part

    target = (repo_root / mapped_dest).resolve()
    new_path = _posix_relpath(source_file.parent.resolve(), target)
    if frag:
        new_path = f"{new_path}#{frag}"
    return new_path


def rewrite_markdown_for_adoption(
    text: str,
    src_dest: Mapping[str, str],
    *,
    source_file: Path,
    repo_root: Path,
) -> str:
    """Rewrite markdown link targets from MAT source paths to sidecar dest paths."""

    def repl(match: re.Match[str]) -> str:
        prefix, target, suffix = match.group(1), match.group(2), match.group(3)
        new_target = _map_link_path(
            target, src_dest, source_file=source_file, repo_root=repo_root
        )
        return f"{prefix}{new_target}{suffix}"

    return LINK_RE.sub(repl, text)


def rewrite_tree(
    root: Path,
    src_dest: Mapping[str, str],
    *,
    repo_root: Path,
    suffixes: set[str],
) -> int:
    changed = 0
    if not root.is_dir():
        return 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new = rewrite_markdown_for_adoption(
            raw, src_dest, source_file=path, repo_root=repo_root
        )
        if new != raw:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def flatten_mat_docs_root_sibling_links(
    text: str, source_file: Path, repo_root: Path, src_dest: Mapping[str, str]
) -> str:
    """From `.mat/docs/*.md`, `../foo.md` wrongly resolves to `.mat/foo.md`; use same-dir `foo.md`."""
    try:
        rel_parts = source_file.relative_to(repo_root).parts
    except ValueError:
        return text
    if len(rel_parts) != 3 or rel_parts[0] != ".mat" or rel_parts[1] != "docs":
        return text
    flat_basenames = {
        Path(dest).name
        for dest in src_dest.values()
        if dest.startswith(".mat/docs/") and "/" not in dest[len(".mat/docs/") :]
    }
    for base in sorted(flat_basenames):
        text = text.replace(f"](../{base}", f"]({base}")
        text = text.replace(f"](../{base}#", f"]({base}#")
    text = text.replace("](../update-mat/", "](update-mat/")
    text = text.replace("](../index.md", "](README.md")
    text = text.replace("](adoption-safe-defaults.md)", "](guides/adoption-safe-defaults.md)")
    for bare, target in (
        ("mat-sync-team-runbook.md", "guides/mat-sync-team-runbook.md"),
        ("mat-operator-playbook.md", "guides/mat-operator-playbook.md"),
        ("todo-orchestration.md", "todo-orchestration-protocol.md"),
    ):
        text = text.replace(f"]({bare})", f"]({target})")
        text = text.replace(f"]({bare}#", f"]({target}#")
    return text


def normalize_sidecar_doc_links(text: str, src_dest: Mapping[str, str]) -> str:
    """Fix common ../reference/ and ../architecture/ links after flat .mat/docs packaging."""
    for src, dest in src_dest.items():
        if not dest.startswith(".mat/docs/"):
            continue
        basename = Path(dest).name
        if "/reference/" in src:
            text = text.replace(f"../reference/{Path(src).name}", f"../{basename}")
            text = text.replace(f"../../reference/{Path(src).name}", f"../../{basename}")
        if "/architecture/" in src:
            text = text.replace(f"../architecture/{Path(src).name}", f"../{basename}")
            text = text.replace(f"../../architecture/{Path(src).name}", f"../../{basename}")
        if "/guides/" in src:
            text = text.replace(f"../guides/{Path(src).name}", f"../guides/{basename}")
    return text


def normalize_sidecar_docs_tree(
    mat_docs_root: Path, src_dest: Mapping[str, str], *, repo_root: Path
) -> int:
    changed = 0
    if not mat_docs_root.is_dir():
        return changed
    for path in sorted(mat_docs_root.rglob("*")):
        if path.suffix not in {".md", ".mdc"}:
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new = normalize_sidecar_doc_links(raw, src_dest)
        new = flatten_mat_docs_root_sibling_links(new, path, repo_root, src_dest)
        new = rewrite_markdown_for_adoption(
            new, src_dest, source_file=path, repo_root=repo_root
        )
        if new != raw:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def _basename_dest_index(src_dest: Mapping[str, str]) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = {}
    for src, dest in src_dest.items():
        for name in {Path(src).name, Path(dest).name}:
            idx.setdefault(name, []).append(dest)
    return idx


def _collapse_sidecar_rel(rel: str) -> str:
    while ".mat/.mat/" in rel:
        rel = rel.replace(".mat/.mat/", ".mat/")
    while ".mat/docs/.mat/docs/" in rel:
        rel = rel.replace(".mat/docs/.mat/docs/", ".mat/docs/", 1)
    return rel


def adopted_link_resolves(resolved: Path, repo_root: Path, src_dest: Mapping[str, str]) -> bool:
    """True when resolved path exists or matches a packaged sidecar mapping."""
    if resolved.is_file():
        return True
    if resolved.is_dir():
        return True

    try:
        rel = _collapse_sidecar_rel(resolved.relative_to(repo_root).as_posix())
    except ValueError:
        return False

    candidates = {rel}
    if rel.startswith(".mat/.cursor/"):
        candidates.add(".cursor/" + rel[len(".mat/.cursor/") :])

    for cand in candidates:
        path = repo_root / cand
        if path.is_file() or path.is_dir():
            return True

    if rel.startswith(".mat/"):
        stripped = rel[len(".mat/") :]
        root_alias = repo_root / stripped
        if root_alias.is_file() or root_alias.is_dir():
            return True
        if stripped == ".cursorignore" and (repo_root / ".cursorignore").is_file():
            return True
        if rel == ".mat/.cursorignore" and (repo_root / ".cursorignore").is_file():
            return True
        if stripped == "mat-agents.yaml" and (repo_root / "mat-agents.yaml").is_file():
            return True
        docs_alias = repo_root / ".mat" / "docs" / stripped
        if docs_alias.is_file() or docs_alias.is_dir():
            return True
        if rel in {".mat/index.md", ".mat/docs/index.md"} and (repo_root / ".mat/docs/README.md").is_file():
            return True

    if rel in src_dest.values() and (repo_root / rel).is_file():
        return True

    mapped = src_dest.get(rel)
    if mapped and (repo_root / mapped).is_file():
        return True

    if rel.startswith("docs/"):
        mapped = src_dest.get(rel)
        if mapped and (repo_root / mapped).is_file():
            return True

    name = Path(rel).name
    packaged_dests = [d for d in _basename_dest_index(src_dest).get(name, []) if (repo_root / d).is_file()]
    if not packaged_dests:
        return False

    if rel in packaged_dests:
        return True

    # Source-tree path shapes that flatten into `.mat/docs/` on adopt.
    legacy_prefixes = (
        ".mat/reference/",
        ".mat/architecture/",
        ".mat/guides/",
        ".mat/templates/",
        ".mat/docs/reference/",
        ".mat/docs/architecture/",
        ".mat/docs/guides/",
        "docs/reference/",
        "docs/architecture/",
        "docs/guides/",
        "specs/",
    )
    for prefix in legacy_prefixes:
        if rel == f"{prefix}{name}":
            return True
    if rel == f".mat/{name}":
        return True

    if rel.endswith(f"/{name}") and rel not in packaged_dests:
        return True

    if name == "todo-orchestration.md":
        return (repo_root / ".mat/docs/todo-orchestration-protocol.md").is_file()

    if name == "ROADMAP.md":
        return True

    return False
