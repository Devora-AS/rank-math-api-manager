#!/usr/bin/env python3
"""
MAO worktree metadata — minimal, deterministic, fail-open.

Reads optional Cursor worktree bootstrap markers under .cursor/worktree/
(written by bootstrap_worktree.sh). Never raises; missing data yields
source 'absent' and null optional fields.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

WORKTREE_NAME_REL = Path(".cursor") / "worktree" / "name"
WORKTREE_BOOTSTRAPPED_REL = Path(".cursor") / "worktree" / "bootstrapped_at"


def collect_mao_worktree_metadata(repo_root: Path) -> dict[str, Any]:
    """Return the canonical mao_worktree dict for a resolved repo root."""
    root = Path(repo_root).resolve()
    out: dict[str, Any] = {
        "project_dir": str(root),
        "label": None,
        "bootstrapped_at": None,
        "source": "absent",
    }

    name_path = root / WORKTREE_NAME_REL
    try:
        if name_path.is_file():
            label = name_path.read_text(encoding="utf-8", errors="replace").strip()
            if label:
                out["label"] = label
                out["source"] = "cursor_worktree_marker"
    except OSError:
        pass

    boot_path = root / WORKTREE_BOOTSTRAPPED_REL
    try:
        if boot_path.is_file():
            raw = boot_path.read_text(encoding="utf-8", errors="replace").strip()
            if raw:
                out["bootstrapped_at"] = raw
    except OSError:
        pass

    return out


def mao_worktree_metadata_valid(obj: Any) -> bool:
    """True if obj matches the shape produced by collect_mao_worktree_metadata."""
    if not isinstance(obj, dict):
        return False
    pd = obj.get("project_dir")
    if not isinstance(pd, str) or not pd.strip():
        return False
    src = obj.get("source")
    if src not in {"cursor_worktree_marker", "absent"}:
        return False
    lab = obj.get("label")
    if lab is not None and not isinstance(lab, str):
        return False
    boot = obj.get("bootstrapped_at")
    if boot is not None and not isinstance(boot, str):
        return False
    return True
