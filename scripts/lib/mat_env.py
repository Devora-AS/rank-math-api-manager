"""Shared MAT environment resolution (non-mutating reads)."""

from __future__ import annotations

import os
from pathlib import Path

_MAT_ENV_REL = ".mat.env"
_ENV_REL = ".env"
_MAT_ENV_FALLBACK_PREFIXES = ("CURSOR_", "OBSERVABILITY_")


def is_mat_env_fallback_key(key: str) -> bool:
    return key.startswith(_MAT_ENV_FALLBACK_PREFIXES)


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, rest = stripped.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        value = rest.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key] = value
    return out


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        from dotenv import dotenv_values

        raw = dotenv_values(path)
        return {k: "" if v is None else str(v) for k, v in raw.items()}
    except ImportError:
        return _parse_env_file(path)


def resolve_mat_env(
    key: str,
    repo_root: Path,
    *,
    default: str | None = None,
) -> str | None:
    """
    Resolve one key with precedence:
    1. process os.environ
    2. `.mat.env` at repo root
    3. `.env` — only CURSOR_* / OBSERVABILITY_* keys
    4. caller default
    """
    if key in os.environ:
        return os.environ[key]

    mat_vals = _read_env_file(repo_root / _MAT_ENV_REL)
    if key in mat_vals:
        return mat_vals[key]

    if is_mat_env_fallback_key(key):
        env_vals = _read_env_file(repo_root / _ENV_REL)
        if key in env_vals:
            return env_vals[key]

    return default


def resolve_mat_env_keys(
    keys: tuple[str, ...] | list[str],
    repo_root: Path,
) -> dict[str, str]:
    """Resolve multiple keys; missing values become empty strings."""
    out: dict[str, str] = {}
    for key in keys:
        value = resolve_mat_env(key, repo_root)
        out[key] = "" if value is None else value
    return out
