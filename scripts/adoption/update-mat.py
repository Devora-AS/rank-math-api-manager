#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from apply_mat_legacy_cleanup import apply_legacy_cleanup  # noqa: E402
from update_mat_contracts import (  # noqa: E402
    build_compatibility_snapshot,
    load_footprint_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).with_name("adoption-layout-v1.json")
DEFAULT_FOOTPRINT = Path(__file__).with_name("mat-footprint-v1.json")
AGENTS_HELPER = Path(__file__).with_name("manage-agents-sidecars.py")
DEFAULT_AUDIT_DIR = "artifacts/update-mat"


@dataclass(slots=True)
class MappingItem:
    kind: str
    source: str | None
    target: str
    managed: str


@dataclass(slots=True)
class FileDiff:
    source: str
    target: str
    change_type: str
    source_sha256: str | None
    target_sha256: str | None
    preview: str | None = None


@dataclass(slots=True)
class UpdatePlan:
    upstream_source: str
    upstream_ref: str
    upstream_commit: str
    target_root: str
    target_baseline: str | None
    dry_run: bool
    stage_mode: str
    changed_files: list[FileDiff]
    agents_reconciliation_needed: bool
    agents_preview: str
    conflicts: list[str]
    preserved_paths: list[str]
    rollback_hint: str
    compatibility_snapshot: dict[str, Any]
    staging_path: str | None = None
    staging_branch: str | None = None
    backup_dir: str | None = None
    legacy_cleanup_preview: list[dict[str, Any]] = field(default_factory=list)


def _legacy_cleanup_preview_payload(target_root: Path, audit_dir_rel: str) -> list[dict[str, Any]]:
    """Run legacy migration engine against the target tree without mutations (no JSONL/quarantine writes)."""
    manifest = target_root / "scripts" / "adoption" / "mat-legacy-migrations-v1.json"
    footprint = target_root / "scripts" / "adoption" / "mat-footprint-v1.json"
    script = target_root / "scripts" / "adoption" / "apply_mat_legacy_cleanup.py"
    if not manifest.is_file() or not footprint.is_file() or not script.is_file():
        return []
    decisions = apply_legacy_cleanup(
        repo_root=target_root,
        migration_manifest_path=manifest,
        footprint_manifest_path=footprint,
        audit_dir_rel=audit_dir_rel,
        dry_run=True,
    )
    return [
        {
            "path": d.path,
            "action": d.action,
            "reason": d.reason,
            "successor": d.successor,
            "handling": d.handling,
            "sha256": d.sha256,
            "dry_run": d.dry_run,
        }
        for d in decisions
    ]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safely preview or stage MAT updates for an adopted repository.")
    parser.add_argument("--source", "--source-root", dest="source", required=True, help="Upstream MAT source repository path or Git URL.")
    parser.add_argument("--ref", default="HEAD", help="Upstream ref to compare against (default: HEAD).")
    parser.add_argument("--target", "--repo-root", dest="target", default=".", help="Target adopted repository root (default: current directory).")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to the MAT layout manifest.")
    parser.add_argument("--footprint", default=str(DEFAULT_FOOTPRINT), help="Path to the target-repo MAT footprint manifest.")
    parser.add_argument("--apply", action="store_true", help="Stage the update in an isolated worktree before stopping for review.")
    parser.add_argument("--stage-mode", choices=("worktree", "branch"), default="worktree", help="How to stage apply-mode changes.")
    parser.add_argument("--plan-file", help="Existing dry-run plan file to validate before applying.")
    parser.add_argument("--approved", action="store_true", help="Explicitly approve apply-mode staging and review handoff.")
    parser.add_argument("--show-patch", action="store_true", help="Print the patch preview and write a patch file.")
    parser.add_argument("--backup-dir", help="Optional backup directory for apply-mode file snapshots.")
    parser.add_argument("--inline-fallback", action="store_true", help="Run the AGENTS helper in inline-fallback mode while staging.")
    parser.add_argument("--audit-dir", default=DEFAULT_AUDIT_DIR, help="Directory for audit JSONL output relative to the target repo.")
    return parser


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _git(args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)


def _git_commit(path: Path) -> str | None:
    completed = _git(["rev-parse", "HEAD"], cwd=path, check=False)
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _git_status_clean(path: Path) -> bool:
    completed = _git(["status", "--porcelain"], cwd=path, check=False)
    return completed.returncode == 0 and not completed.stdout.strip()


def _is_git_repo(path: Path) -> bool:
    return _git(["rev-parse", "--is-inside-work-tree"], cwd=path, check=False).returncode == 0


def _load_layout_manifest(manifest_path: Path) -> dict:
    layout = _load_json(manifest_path)
    if layout.get("schema_version") not in {"1", "1.0.0"}:
        raise ValueError(f"unsupported manifest schema version: {layout.get('schema_version')}")
    return layout


def _load_footprint_manifest(manifest_path: Path) -> dict:
    return load_footprint_manifest(manifest_path)


def _layout_mappings(layout: dict) -> list[MappingItem]:
    items: list[MappingItem] = []

    items.append(MappingItem(kind="generated", source=None, target=".mat/README.md", managed="mat-readme"))
    for item in layout.get("mat_docs", []):
        items.append(MappingItem(kind="file", source=item["src"], target=item["dest"], managed="mat-doc"))
    for rel in layout.get("mat_tests", []):
        items.append(MappingItem(kind="file", source=rel, target=f".mat/tests/{Path(rel).name}", managed="mat-test"))
    items.append(MappingItem(kind="file", source=layout.get("source_agents_for_mat", "AGENTS.md"), target=layout["mat_sidecar"]["agents_mat"], managed="mat-agents"))
    items.append(MappingItem(kind="file", source=layout.get("source_readme_for_vendor", "README.md"), target=layout["mat_sidecar"]["vendor_readme_mat"], managed="vendor-readme"))
    for rel in layout.get("cursor_copy", {}).get("files", []):
        items.append(MappingItem(kind="file", source=rel, target=rel, managed="cursor-file"))
    for rel_dir in layout.get("cursor_copy", {}).get("dir_contents", []):
        items.append(MappingItem(kind="dir", source=rel_dir, target=rel_dir, managed="cursor-dir"))
    for rel in layout.get("root_scripts_copy", []):
        items.append(MappingItem(kind="file", source=rel, target=rel, managed="root-script"))
    return items


def _repo_paths_from_dir(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not root.exists():
        return files
    for current in root.rglob("*"):
        rel = current.relative_to(root).as_posix()
        if "__pycache__" in rel or rel.endswith(".pyc") or rel.endswith(".log") or "continual-learning" in rel:
            continue
        if current.is_file():
            files[current.relative_to(root).as_posix()] = current
    return files


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _render_mat_readme() -> str:
    return """
# `.mat/` — Multi-agent workflow (MAT) sidecar

This directory holds **MAT-packaged** material for this repository: reference documentation and workflow contract tests copied from the MAT source repo. It keeps product documentation at the repo root separate from workflow manuals.

- **`.mat/docs/`** — packaged workflow documentation (components, getting started, MAO protocol, etc.).
- **`.mat/tests/`** — workflow contract tests (`unittest`); run with `python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v`.
- **`.mat/AGENTS.mat.md`** — full MAT operator reference from the source `AGENTS.md`.
- **`.mat/vendor/README-MAT.md`** — optional attribution copy of the MAT source `README.md`.

Entrypoints at repo root: **`scripts/phase1-verify.sh`**, **`.cursor/`** (hooks, commands, agents).

`phase1-verify.sh` treats this sidecar as present when this file exists: it may skip missing `build-result.md` / `verify-result.md`, skip closeout matrix checks until `artifacts/agent-traces/comparison.json` exists, run **`unittest`** under **`.mat/tests/`**, and skip Bun smoke when `apps/server` is absent.

For product narrative, use the root **`README.md`** and your application docs — not this tree.
""".strip() + "\n"


def _source_tree(source: str, ref: str) -> tuple[Path, str]:
    source_path = Path(source).expanduser().resolve()
    if source_path.exists() and source_path.is_dir() and ref in {"", "HEAD"}:
        return source_path, _git_commit(source_path) or "unknown"

    clone_root = Path(tempfile.mkdtemp(prefix="mat-update-source-"))
    clone_dir = clone_root / "source"
    completed = _git(["clone", "--no-tags", "--quiet", source, str(clone_dir)], cwd=REPO_ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout or "failed to clone source repository")
    checkout = _git(["checkout", "--quiet", ref], cwd=clone_dir, check=False)
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stderr or checkout.stdout or f"failed to checkout {ref}")
    return clone_dir, _git_commit(clone_dir) or "unknown"


def _normalize_manifest(layout: dict) -> dict:
    for key in ("mat_docs", "mat_tests", "cursor_copy", "root_scripts_copy", "modes"):
        if key not in layout:
            raise ValueError(f"layout manifest is missing required section: {key}")
    if "source_agents_for_mat" not in layout:
        layout["source_agents_for_mat"] = "AGENTS.md"
    if "source_readme_for_vendor" not in layout:
        layout["source_readme_for_vendor"] = "README.md"
    if "mat_sidecar" not in layout:
        raise ValueError("layout manifest is missing required section: mat_sidecar")
    return layout


def _compare_file(source: Path, target: Path, source_root: Path, target_root: Path) -> FileDiff | None:
    source_rel = source.relative_to(source_root).as_posix()
    target_rel = target.relative_to(target_root).as_posix()

    if not source.exists():
        return FileDiff(source=source_rel, target=target_rel, change_type="conflict", source_sha256=None, target_sha256=None, preview="source file is missing")
    if target.exists() and target.is_dir():
        return FileDiff(source=source_rel, target=target_rel, change_type="conflict", source_sha256=_sha256_bytes(source.read_bytes()), target_sha256=None, preview="target path is a directory")

    source_sha = _sha256_bytes(source.read_bytes())
    if not target.exists():
        return FileDiff(source=source_rel, target=target_rel, change_type="added", source_sha256=source_sha, target_sha256=None)

    target_sha = _sha256_bytes(target.read_bytes())
    if source_sha == target_sha:
        return None

    preview = ""
    try:
        preview = "\n".join(
            difflib.unified_diff(
                _read_text(target).splitlines(),
                _read_text(source).splitlines(),
                fromfile=f"target/{target_rel}",
                tofile=f"source/{source_rel}",
                lineterm="",
            )
        )
    except UnicodeDecodeError:
        preview = ""

    return FileDiff(source=source_rel, target=target_rel, change_type="modified", source_sha256=source_sha, target_sha256=target_sha, preview=preview or None)


def _legacy_migration_extra_paths(repo_root: Path) -> set[str]:
    """Paths listed in mat-legacy-migrations (obsolete MAT surfaces) may exist on target without matching upstream."""
    manifest = repo_root / "scripts" / "adoption" / "mat-legacy-migrations-v1.json"
    if not manifest.is_file():
        return set()
    data = _load_json(manifest)
    out: set[str] = set()
    for entry in data.get("entries", []):
        if not isinstance(entry, dict):
            continue
        raw = entry.get("path")
        if not isinstance(raw, str) or not raw.strip():
            continue
        rel = raw.replace("\\", "/").strip()
        while rel.startswith("./"):
            rel = rel[2:]
        out.add(rel)
    return out


def _compare_dir(
    source_dir: Path,
    target_dir: Path,
    source_root: Path,
    target_root: Path,
    *,
    legacy_allowed_extras: set[str] | None = None,
) -> tuple[list[FileDiff], list[str]]:
    diffs: list[FileDiff] = []
    conflicts: list[str] = []

    if not source_dir.exists():
        conflicts.append(f"missing source directory: {source_dir.relative_to(source_root).as_posix()}")
        return diffs, conflicts

    source_files = _repo_paths_from_dir(source_dir)
    target_files = _repo_paths_from_dir(target_dir)
    source_rel = source_dir.relative_to(source_root).as_posix()
    target_rel = target_dir.relative_to(target_root).as_posix()
    allowed = legacy_allowed_extras or set()

    for rel in sorted(set(target_files) - set(source_files)):
        full = f"{target_rel}/{rel}" if target_rel else rel
        if full in allowed:
            continue
        conflicts.append(f"target contains unmanaged file inside owned directory {target_rel}: {rel}")

    for rel, source_path in source_files.items():
        target_path = target_dir / rel
        if target_path.exists() and target_path.is_dir():
            conflicts.append(f"target path is a directory inside owned directory {target_rel}/{rel}")
            continue
        diff = _compare_file(source_path, target_path, source_root, target_root)
        if diff is not None:
            diffs.append(diff)

    return diffs, conflicts


def _run_agents_helper(repo_root: Path, *, dry_run: bool, inline_fallback: bool, backup_dir: Path | None) -> tuple[bool, str]:
    cmd = [os.environ.get("PYTHON", "python3"), str(AGENTS_HELPER), "--repo-root", str(repo_root)]
    if dry_run:
        cmd.append("--dry-run")
    if inline_fallback:
        cmd.append("--inline-fallback")
    if backup_dir is not None:
        cmd.extend(["--backup-dir", str(backup_dir)])
    completed = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(f"AGENTS helper failed: {output}")
    needs = any(marker in output for marker in ("would update", "changed files:", "updated "))
    return needs, output.strip()


def _stage_target(target_root: Path, *, stage_mode: str) -> tuple[Path, str | None]:
    if not _is_git_repo(target_root):
        staging_root = Path(tempfile.mkdtemp(prefix="mat-update-stage-"))
        shutil.copytree(target_root, staging_root, dirs_exist_ok=True)
        return staging_root, f"mat/update-{target_root.name}-{staging_root.name[-8:]}"

    staging_root = Path(tempfile.mkdtemp(prefix="mat-update-worktree-"))
    branch_name = f"mat/update-{target_root.name}-{staging_root.name[-8:]}"
    if not _git_status_clean(target_root):
        shutil.copytree(target_root, staging_root, dirs_exist_ok=True)
        return staging_root, branch_name

    if stage_mode == "branch":
        _git(["worktree", "add", "-b", branch_name, str(staging_root), "HEAD"], cwd=target_root)
        return staging_root, branch_name

    _git(["worktree", "add", "--detach", str(staging_root), "HEAD"], cwd=target_root)
    return staging_root, branch_name


def _run_legacy_cleanup_repo(repo_root: Path, *, dry_run: bool) -> None:
    """Remove/quarantine obsolete MAT paths after staged layout copy (manifest-driven)."""
    script = repo_root / "scripts" / "adoption" / "apply_mat_legacy_cleanup.py"
    manifest = repo_root / "scripts" / "adoption" / "mat-legacy-migrations-v1.json"
    footprint = repo_root / "scripts" / "adoption" / "mat-footprint-v1.json"
    if not script.is_file() or not manifest.is_file() or not footprint.is_file():
        return
    cmd = [
        os.environ.get("PYTHON", "python3"),
        str(script),
        "--repo-root",
        str(repo_root),
        "--manifest",
        str(manifest),
        "--footprint",
        str(footprint),
    ]
    if dry_run:
        cmd.append("--dry-run")
    subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=False)


def _apply_mapping_set(
    source_root: Path,
    staging_root: Path,
    items: list[MappingItem],
    *,
    inline_fallback: bool,
    backup_dir: Path | None,
    legacy_allowed_extras: set[str] | None = None,
) -> tuple[list[FileDiff], list[str], bool, str]:
    diffs: list[FileDiff] = []
    conflicts: list[str] = []
    agents_needed, agents_preview = _run_agents_helper(staging_root, dry_run=False, inline_fallback=inline_fallback, backup_dir=backup_dir)

    for item in items:
        source = source_root / item.source if item.source else None
        target = staging_root / item.target
        if item.kind == "generated":
            if backup_dir is not None and target.exists():
                backup = backup_dir / item.target
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            _write_text(target, _render_mat_readme())
            diffs.append(FileDiff(source="<generated>", target=item.target, change_type="generated", source_sha256=_sha256_text(_render_mat_readme()), target_sha256=_sha256_text(target.read_text(encoding="utf-8"))))
            continue
        assert source is not None
        if item.kind == "file":
            diff = _compare_file(source, target, source_root, staging_root)
            if diff is None:
                continue
            if diff.change_type == "conflict":
                conflicts.append(f"{diff.source} -> {diff.target}: {diff.preview}")
                continue
            if target.exists() and backup_dir is not None:
                backup = backup_dir / item.target
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            diffs.append(diff)
            continue

        dir_diffs, dir_conflicts = _compare_dir(source, target, source_root, staging_root, legacy_allowed_extras=legacy_allowed_extras)
        conflicts.extend(dir_conflicts)
        for diff in dir_diffs:
            source_file = source_root / diff.source
            target_file = staging_root / diff.target
            if target_file.exists() and backup_dir is not None:
                backup = backup_dir / diff.target
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target_file, backup)
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            diffs.append(diff)

    if agents_needed:
        helper = [os.environ.get("PYTHON", "python3"), str(AGENTS_HELPER), "--repo-root", str(staging_root)]
        if inline_fallback:
            helper.append("--inline-fallback")
        if backup_dir is not None:
            helper.extend(["--backup-dir", str(backup_dir)])
        completed = subprocess.run(helper, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
        output = (completed.stdout or "") + (completed.stderr or "")
        if completed.returncode != 0:
            raise RuntimeError(f"AGENTS helper apply failed: {output}")
        agents_preview = output.strip()

    return diffs, conflicts, agents_needed, agents_preview


def _audit_path(target_root: Path, audit_dir: str) -> Path:
    audit_root = target_root / audit_dir
    audit_root.mkdir(parents=True, exist_ok=True)
    return audit_root / "update-mat-audit.jsonl"


def _append_audit_record(target_root: Path, audit_dir: str, record: dict) -> Path:
    audit_path = _audit_path(target_root, audit_dir)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True))
        handle.write("\n")
    return audit_path


def _plan_artifact_paths(target_root: Path, audit_dir: str) -> tuple[Path, Path]:
    audit_root = target_root / audit_dir
    audit_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    plan_path = audit_root / f"plan-update-{stamp}.json"
    patch_path = audit_root / f"patch-update-{stamp}.patch"
    return plan_path, patch_path


def _plan_payload(*, plan: UpdatePlan, total_mappings: int, plan_path: Path, patch_path: Path) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(plan_path),
        "patch_file": str(patch_path),
        "total_mappings": total_mappings,
        "compatibility_snapshot": plan.compatibility_snapshot,
        "plan": {
            "upstream_source": plan.upstream_source,
            "upstream_ref": plan.upstream_ref,
            "upstream_commit": plan.upstream_commit,
            "target_root": plan.target_root,
            "target_baseline": plan.target_baseline,
            "dry_run": plan.dry_run,
            "stage_mode": plan.stage_mode,
            "changed_files": [asdict(change) for change in plan.changed_files],
            "agents_reconciliation_needed": plan.agents_reconciliation_needed,
            "agents_preview": plan.agents_preview,
            "conflicts": plan.conflicts,
            "preserved_paths": plan.preserved_paths,
            "rollback_hint": plan.rollback_hint,
            "compatibility_snapshot": plan.compatibility_snapshot,
            "staging_path": plan.staging_path,
            "staging_branch": plan.staging_branch,
            "backup_dir": plan.backup_dir,
            "legacy_cleanup_preview": plan.legacy_cleanup_preview,
        },
    }


def _write_plan_artifacts(*, plan: UpdatePlan, total_mappings: int, target_root: Path, audit_dir: str) -> tuple[Path, Path]:
    plan_path, patch_path = _plan_artifact_paths(target_root, audit_dir)
    payload = _plan_payload(plan=plan, total_mappings=total_mappings, plan_path=plan_path, patch_path=patch_path)
    plan_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    patch_path.write_text(_render_stdout(plan, total_mappings), encoding="utf-8")
    return plan_path, patch_path


def _load_plan_file(plan_path: Path) -> dict:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def _ensure_plan_current(plan_payload: dict, target_root: Path) -> None:
    plan = plan_payload.get("plan", {})
    if Path(plan.get("target_root", "")).resolve() != target_root.resolve():
        raise RuntimeError(f"plan target mismatch: {plan.get('target_root')}")
    for change in plan.get("changed_files", []):
        target_rel = change["target"]
        current = target_root / target_rel
        target_sha = change.get("target_sha256")
        if target_sha is None:
            if current.exists():
                raise RuntimeError(f"target drifted for {target_rel}")
            continue
        if not current.exists():
            raise RuntimeError(f"target drifted for {target_rel}")
        if current.is_dir():
            raise RuntimeError(f"target drifted for {target_rel}")
        if _sha256_bytes(current.read_bytes()) != target_sha:
            raise RuntimeError(f"target drifted for {target_rel}")


def _preview_lines(changes: list[FileDiff], max_lines: int = 120) -> list[str]:
    lines: list[str] = []
    for change in changes:
        lines.append(f"{change.change_type.upper()}: {change.target}")
        if change.preview:
            lines.extend(change.preview.splitlines())
        if len(lines) >= max_lines:
            lines.append("... preview truncated ...")
            break
    return lines


def _collect_plan(*, source_root: Path, target_root: Path, layout: dict, footprint: dict, source_input: str, source_ref: str, dry_run: bool, stage_mode: str, inline_fallback: bool, backup_dir: Path | None, audit_dir: str) -> UpdatePlan:
    items = _layout_mappings(layout)
    legacy_allowed_extras = _legacy_migration_extra_paths(target_root)
    compatibility_snapshot = build_compatibility_snapshot(layout_manifest=layout, footprint_manifest=footprint)
    preserved = list(footprint.get("target_repo", {}).get("preserve_paths", []))
    for extra in layout.get("modes", {}).get("existing-project", {}).get("never_overwrite_root", []):
        if extra not in preserved:
            preserved.append(extra)
    for extra in ("docs/current-plan.md", "docs/long-run-state.md", "build-result.md", "verify-result.md"):
        if extra not in preserved:
            preserved.append(extra)

    conflicts: list[str] = []
    diffs: list[FileDiff] = []

    for item in items:
        if item.target in preserved:
            conflicts.append(f"manifest incorrectly includes preserved path: {item.target}")

    agents_needed, agents_preview = _run_agents_helper(target_root, dry_run=True, inline_fallback=inline_fallback, backup_dir=backup_dir)

    for item in items:
        source_path = source_root / item.source if item.source else None
        target_path = target_root / item.target
        if item.kind == "generated":
            generated = _render_mat_readme()
            target_text = target_path.read_text(encoding="utf-8") if target_path.exists() else None
            if target_text != generated:
                diffs.append(FileDiff(source="<generated>", target=item.target, change_type="generated", source_sha256=_sha256_text(generated), target_sha256=_sha256_text(target_text) if target_text is not None else None, preview=None if target_text is None else "generated file differs"))
            continue
        assert source_path is not None
        if item.kind == "file":
            diff = _compare_file(source_path, target_path, source_root, target_root)
            if diff is not None:
                if diff.change_type == "conflict":
                    conflicts.append(f"{diff.source} -> {diff.target}: {diff.preview}")
                else:
                    diffs.append(diff)
            continue
        dir_diffs, dir_conflicts = _compare_dir(
            source_path, target_path, source_root, target_root, legacy_allowed_extras=legacy_allowed_extras
        )
        diffs.extend(dir_diffs)
        conflicts.extend(dir_conflicts)

    staging_path: str | None = None
    staging_branch: str | None = None
    final_backup_dir: str | None = None
    if not dry_run and not conflicts:
        staged_root, staging_branch = _stage_target(target_root, stage_mode=stage_mode)
        staging_path = str(staged_root)
        if backup_dir is not None:
            final_backup_dir = str(backup_dir)
        else:
            final_backup_dir = str(staged_root / ".mat-update-backups")
            backup_dir = Path(final_backup_dir)
        applied_diffs, apply_conflicts, agents_needed_apply, agents_preview_apply = _apply_mapping_set(
            source_root,
            staged_root,
            items,
            inline_fallback=inline_fallback,
            backup_dir=backup_dir,
            legacy_allowed_extras=legacy_allowed_extras,
        )
        diffs = applied_diffs
        conflicts.extend(apply_conflicts)
        agents_needed = agents_needed or agents_needed_apply
        if agents_preview_apply:
            agents_preview = agents_preview_apply

        if staging_path:
            _run_legacy_cleanup_repo(Path(staging_path), dry_run=False)

    legacy_cleanup_preview = _legacy_cleanup_preview_payload(target_root, audit_dir) if dry_run else []

    rollback_hint = f"remove staging worktree at {staging_path}" if staging_path else f"restore from backups under {final_backup_dir or (target_root / audit_dir)}"
    return UpdatePlan(
        upstream_source=source_input,
        upstream_ref=source_ref,
        upstream_commit=_git_commit(source_root) or "unknown",
        target_root=str(target_root),
        target_baseline=_git_commit(target_root),
        dry_run=dry_run,
        stage_mode=stage_mode,
        changed_files=diffs,
        agents_reconciliation_needed=agents_needed,
        agents_preview=agents_preview,
        conflicts=conflicts,
        preserved_paths=preserved,
        rollback_hint=rollback_hint,
        compatibility_snapshot=compatibility_snapshot,
        staging_path=staging_path,
        staging_branch=staging_branch,
        backup_dir=final_backup_dir,
        legacy_cleanup_preview=legacy_cleanup_preview,
    )


def _render_stdout(plan: UpdatePlan, total_mappings: int) -> str:
    lines = ["MAT update dry-run" if plan.dry_run else "MAT update apply stage"]
    lines.extend([
        f"source: {plan.upstream_source}@{plan.upstream_ref} ({plan.upstream_commit})",
        f"target: {plan.target_root}",
        f"stage mode: {plan.stage_mode}",
        f"dry-run: {str(plan.dry_run).lower()}",
        f"mappings considered: {total_mappings}",
        f"changes detected: {len(plan.changed_files)}",
        f"AGENTS reconciliation needed: {str(plan.agents_reconciliation_needed).lower()}",
        f"conflicts: {len(plan.conflicts)}",
    ])
    if plan.compatibility_snapshot:
        lines.append(f"footprint manifest: {plan.compatibility_snapshot.get('manifest_name')}")
        lines.append(f"compatibility paths: {plan.compatibility_snapshot.get('managed_path_count')}")
    if plan.staging_path:
        lines.append(f"staging path: {plan.staging_path}")
    if plan.staging_branch:
        lines.append(f"staging branch: {plan.staging_branch}")
    if plan.backup_dir:
        lines.append(f"backup dir: {plan.backup_dir}")
    lines.append("")
    lines.append("Legacy cleanup preview (target tree, non-mutating):")
    if plan.legacy_cleanup_preview:
        for row in plan.legacy_cleanup_preview:
            succ = row.get("successor") or "n/a"
            lines.append(f"  [{row['action']}] {row['path']} (handling={row['handling']}, successor={succ})")
    else:
        lines.append("  (no legacy migration tools/manifest on target, or no decisions)")
    lines.append("")
    lines.append("Patch preview:")
    lines.extend(_preview_lines(plan.changed_files))
    lines.append("")
    lines.append("AGENTS reconciliation:")
    lines.extend(plan.agents_preview.splitlines() if plan.agents_preview else ["no AGENTS helper output"])
    lines.append("")
    lines.append("Preserved paths:")
    lines.extend(f"- {path}" for path in plan.preserved_paths)
    lines.append("")
    lines.append("Rollback hint:")
    lines.append(plan.rollback_hint)
    if plan.conflicts:
        lines.append("")
        lines.append("Conflicts:")
        lines.extend(f"- {item}" for item in plan.conflicts)
    return "\n".join(lines).rstrip() + "\n"


def _audit_record(*, plan: UpdatePlan, total_mappings: int, source_ref: str, operator: str | None, author: str | None, audit_path: Path) -> dict:
    changed_summary = [f"{change.change_type}:{change.target}" for change in plan.changed_files]
    approval_state = "dry-run" if plan.dry_run else "apply-staged"
    if plan.conflicts:
        approval_state = "blocked"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "upstream_source": plan.upstream_source,
        "source_repo": plan.upstream_source,
        "upstream_ref": source_ref,
        "upstream_commit": plan.upstream_commit,
        "target_root": plan.target_root,
        "target_baseline": plan.target_baseline,
        "final_target_reference": plan.staging_path or plan.target_baseline,
        "final_commit_or_pr_reference": None,
        "operator": operator,
        "author": author,
        "mode": "dry-run" if plan.dry_run else "apply",
        "stage_mode": plan.stage_mode if not plan.dry_run else None,
        "approval_state": approval_state,
        "conflict_state": "blocked" if plan.conflicts else "clear",
        "agents_reconciliation_needed": plan.agents_reconciliation_needed,
        "changed_file_count": len(plan.changed_files),
        "mappings_considered": total_mappings,
        "diff_summary": changed_summary,
        "agents_preview": plan.agents_preview,
        "rollback_hint": plan.rollback_hint,
        "compatibility_snapshot": plan.compatibility_snapshot,
        "backup_dir": plan.backup_dir,
        "staging_path": plan.staging_path,
        "staging_branch": plan.staging_branch,
        "stdout_preview": _preview_lines(plan.changed_files),
        "audit_path": str(audit_path),
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    target_root = _repo_root(args.target)
    manifest_path = Path(args.manifest).expanduser().resolve()
    footprint_path = Path(args.footprint).expanduser().resolve()
    layout = _normalize_manifest(_load_layout_manifest(manifest_path))
    footprint = _load_footprint_manifest(footprint_path)

    try:
        source_root, _ = _source_tree(args.source, args.ref)
    except Exception as exc:
        print(f"update-mat: failed to prepare source tree: {exc}", file=os.sys.stderr)
        return 1

    plan_path: Path | None = None
    patch_path: Path | None = None
    try:
        if args.apply and not args.approved:
            raise RuntimeError("approval required before commit or PR creation")

        if args.apply and not args.plan_file:
            raise RuntimeError("apply mode requires --plan-file from a prior dry-run")

        if args.apply:
            loaded_plan = _load_plan_file(Path(args.plan_file).expanduser().resolve())
            _ensure_plan_current(loaded_plan, target_root)

        plan = _collect_plan(
            source_root=source_root,
            target_root=target_root,
            layout=layout,
            footprint=footprint,
            source_input=args.source,
            source_ref=args.ref,
            dry_run=not args.apply,
            stage_mode=args.stage_mode,
            inline_fallback=args.inline_fallback,
            backup_dir=Path(args.backup_dir).expanduser().resolve() if args.backup_dir else None,
            audit_dir=args.audit_dir,
        )
        if not args.apply:
            plan_path, patch_path = _write_plan_artifacts(plan=plan, total_mappings=len(_layout_mappings(layout)), target_root=target_root, audit_dir=args.audit_dir)
    except Exception as exc:
        print(f"update-mat: {exc}", file=os.sys.stderr)
        return 1

    total_mappings = len(_layout_mappings(layout))
    audit_path = _audit_path(target_root, args.audit_dir)
    record = _audit_record(
        plan=plan,
        total_mappings=total_mappings,
        source_ref=args.ref,
        operator=os.environ.get("USER") or os.environ.get("USERNAME"),
        author=os.environ.get("GIT_AUTHOR_NAME"),
        audit_path=audit_path,
    )
    _append_audit_record(target_root, args.audit_dir, record)

    if args.apply:
        print("update-mat: dry-run=no")
        if plan.staging_path:
            print(f"staging-worktree={plan.staging_path}")
        if plan.staging_branch:
            print(f"branch={plan.staging_branch}")
        print(f"footprint-file={footprint_path}")
        print("approval required before commit or PR creation")
    else:
        print("update-mat: dry-run=yes")
        if plan_path is not None:
            print(f"plan-file={plan_path}")
        if patch_path is not None:
            print(f"patch-file={patch_path}")
        print(f"footprint-file={footprint_path}")
        print(f"audit-file={audit_path}")
        print(f"agents_reconciliation_needed: {plan.agents_reconciliation_needed}")

    print(_render_stdout(plan, total_mappings), end="")

    if plan.conflicts:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
