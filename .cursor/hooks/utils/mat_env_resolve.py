"""Hook-facing MAT env resolution (wraps scripts/lib/mat_env.py)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def repo_root() -> Path:
    """Workspace root from process env (not read from `.mat.env`)."""
    return Path(
        os.environ.get("CURSOR_PROJECT_DIR")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    ).resolve()


def _mat_env_module_root(workspace_root: Path) -> Path:
    """Directory whose `scripts/lib/mat_env.py` supplies the resolver module."""
    workspace = workspace_root.resolve()
    if (workspace / "scripts" / "lib" / "mat_env.py").is_file():
        return workspace
    bundled = Path(__file__).resolve().parents[3]
    if (bundled / "scripts" / "lib" / "mat_env.py").is_file():
        return bundled
    return workspace


def _ensure_mat_env_on_path(module_root: Path) -> None:
    lib_dir = module_root / "scripts" / "lib"
    lib_str = str(lib_dir)
    if lib_dir.is_dir() and lib_str not in sys.path:
        sys.path.insert(0, lib_str)


def mat_env_get(
    key: str,
    default: str | None = None,
    *,
    root: Path | None = None,
) -> str | None:
    workspace = (root if root is not None else repo_root()).resolve()
    _ensure_mat_env_on_path(_mat_env_module_root(workspace))
    from mat_env import resolve_mat_env

    return resolve_mat_env(key, workspace, default=default)


def mat_env_flag(
    key: str,
    default: bool = False,
    *,
    root: Path | None = None,
) -> bool:
    value = mat_env_get(key, default=None, root=root)
    if value is None:
        return default
    return value.strip().lower() in _TRUTHY


def mat_env_keys(
    keys: tuple[str, ...] | list[str],
    *,
    root: Path | None = None,
) -> dict[str, str]:
    workspace = (root if root is not None else repo_root()).resolve()
    _ensure_mat_env_on_path(_mat_env_module_root(workspace))
    from mat_env import resolve_mat_env_keys

    return resolve_mat_env_keys(keys, workspace)
