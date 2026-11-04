"""Detect-only preflight report for mat-sync bootstrap/update plan JSON."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_adoption_dir = Path(__file__).resolve().parent
if str(_adoption_dir) not in sys.path:
    sys.path.insert(0, str(_adoption_dir))

from mat_gitignore_merge import (
    _detect_omniroute_class_blocker,
    classify_broad_cursor_ignore,
    verify_workflow_paths_trackable,
)

PREFLIGHT_KEYS: tuple[str, ...] = (
    "gitignore_blockers",
    "gitignore_workflow_untrackable",
    "env_sample_blocked_by",
    "custom_skills",
    "custom_agents",
    "custom_commands",
    "scripts_path_overlap",
    "policy_flags",
    "sidecar_present",
)

_NEGATION_SUFFICIENT_BLOCKER_MESSAGE = (
    "broad .cursor/* ignore without MAT workflow negations "
    "(!.cursor/agents/, !.cursor/commands/, !.cursor/hooks/) — "
    "append negations on approve"
)

_REWRITE_REQUIRED_BLOCKER_MESSAGE = (
    "directory ignore .cursor/ (or .cursor/**, **/.cursor/) without MAT workflow negations "
    "(!.cursor/agents/, !.cursor/commands/, !.cursor/hooks/) — "
    "approve rewrites to .cursor/* then appends negations"
)

_ENV_SAMPLE_PATH = ".env.sample"


def _list_custom_agents(mat_source: Path, repo_root: Path) -> list[str]:
    baseline_dir = mat_source / ".cursor" / "agents"
    target_dir = repo_root / ".cursor" / "agents"
    baseline = {path.name for path in baseline_dir.glob("*.md")} if baseline_dir.is_dir() else set()
    custom: list[str] = []
    if target_dir.is_dir():
        for path in sorted(target_dir.glob("*.md")):
            if path.name not in baseline:
                custom.append(path.name)
    return custom


def _list_custom_skills(mat_source: Path, repo_root: Path) -> list[str]:
    baseline_dir = mat_source / ".cursor" / "skills"
    target_dir = repo_root / ".cursor" / "skills"
    baseline: set[str] = set()
    if baseline_dir.is_dir():
        for path in baseline_dir.iterdir():
            if path.is_dir():
                baseline.add(path.name)
    custom: list[str] = []
    if target_dir.is_dir():
        for path in sorted(target_dir.iterdir()):
            if path.is_dir() and path.name not in baseline:
                custom.append(path.name)
    return custom


def _list_custom_commands(mat_source: Path, repo_root: Path) -> list[str]:
    baseline_dir = mat_source / ".cursor" / "commands"
    target_dir = repo_root / ".cursor" / "commands"
    baseline = {path.name for path in baseline_dir.glob("*.md")} if baseline_dir.is_dir() else set()
    custom: list[str] = []
    if target_dir.is_dir():
        for path in sorted(target_dir.glob("*.md")):
            if path.name not in baseline:
                custom.append(path.name)
    return custom


def _gitignore_blockers(repo_root: Path) -> list[str]:
    ignore_path = repo_root / ".gitignore"
    if not ignore_path.is_file():
        return []
    root_text = ignore_path.read_text(encoding="utf-8")
    if not _detect_omniroute_class_blocker(root_text):
        return []
    classified = classify_broad_cursor_ignore(root_text)
    blockers: list[str] = []
    if classified["rewrite_required"]:
        blockers.append(_REWRITE_REQUIRED_BLOCKER_MESSAGE)
    if classified["negation_sufficient"]:
        blockers.append(_NEGATION_SUFFICIENT_BLOCKER_MESSAGE)
    return blockers


def _gitignore_workflow_untrackable(repo_root: Path) -> list[str]:
    result = verify_workflow_paths_trackable(repo_root)
    if not result.get("git_available"):
        return []
    still_ignored = result.get("still_ignored")
    if not isinstance(still_ignored, list):
        return []
    paths: list[str] = []
    for item in still_ignored:
        if isinstance(item, dict) and item.get("path"):
            paths.append(str(item["path"]))
    return paths


def _gitignore_pattern_matches(pattern: str, path: str) -> bool:
    pat = pattern.strip()
    if not pat:
        return False
    if pat.startswith("**/"):
        pat = pat[3:]
    name = Path(path).name
    if pat.endswith("*"):
        prefix = pat[:-1]
        return name.startswith(prefix) or path.startswith(prefix)
    if "/" in pat:
        return path == pat or path.endswith("/" + pat)
    return name == pat


def _simulate_env_sample_blocked_by(repo_root: Path) -> list[str]:
    ignore_path = repo_root / ".gitignore"
    if not ignore_path.is_file():
        return []
    lines = ignore_path.read_text(encoding="utf-8").splitlines()
    matched_rule: str | None = None
    for raw in reversed(lines):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            pattern = line[1:].strip()
            if _gitignore_pattern_matches(pattern, _ENV_SAMPLE_PATH):
                return []
            continue
        if _gitignore_pattern_matches(line, _ENV_SAMPLE_PATH):
            matched_rule = line
            break
    return [matched_rule] if matched_rule else []


def _env_sample_blocked_by(repo_root: Path) -> list[str]:
    env_sample = repo_root / _ENV_SAMPLE_PATH
    if not env_sample.is_file():
        return []
    if (repo_root / ".git").exists():
        proc = subprocess.run(
            ["git", "check-ignore", "-v", _ENV_SAMPLE_PATH],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            detail = proc.stdout.strip() or _ENV_SAMPLE_PATH
            return [detail]
        return []
    return _simulate_env_sample_blocked_by(repo_root)


def _adoption_profile_builder_verify_empty(repo_root: Path) -> bool:
    profile_path = repo_root / ".mat" / "adoption-profile.json"
    if not profile_path.is_file():
        return True
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    if not isinstance(data, dict):
        return True
    validation = data.get("validation_commands")
    if not isinstance(validation, dict):
        return True
    builder_verify = validation.get("builder_verify")
    if builder_verify is None:
        return True
    if not isinstance(builder_verify, list):
        return True
    return len(builder_verify) == 0


def _policy_flags(repo_root: Path) -> list[str]:
    flags: list[str] = []
    if _adoption_profile_builder_verify_empty(repo_root):
        flags.append("builder_verify_empty")
    return flags


def _scripts_path_overlap(repo_root: Path, mat_source: Path) -> list[str]:
    layout_path = mat_source / "scripts" / "adoption" / "adoption-layout-v1.json"
    if not layout_path.is_file():
        return []
    try:
        layout = json.loads(layout_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    overlaps: list[str] = []
    for rel in layout.get("root_scripts_copy", []):
        if not isinstance(rel, str):
            continue
        product_path = repo_root / rel
        if product_path.is_file():
            overlaps.append(rel)
    return sorted(overlaps)


def compute_preflight(repo_root: Path, mat_source: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    mat_source = mat_source.resolve()

    return {
        "gitignore_blockers": _gitignore_blockers(repo_root),
        "gitignore_workflow_untrackable": _gitignore_workflow_untrackable(repo_root),
        "env_sample_blocked_by": _env_sample_blocked_by(repo_root),
        "custom_skills": _list_custom_skills(mat_source, repo_root),
        "custom_agents": _list_custom_agents(mat_source, repo_root),
        "custom_commands": _list_custom_commands(mat_source, repo_root),
        "scripts_path_overlap": _scripts_path_overlap(repo_root, mat_source),
        "policy_flags": _policy_flags(repo_root),
        "sidecar_present": (repo_root / ".mat" / "AGENTS.mat.md").is_file(),
    }
