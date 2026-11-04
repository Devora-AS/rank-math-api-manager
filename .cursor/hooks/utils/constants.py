#!/usr/bin/env python3
"""Shared constants and helpers for Cursor hook scripts."""

import os
from pathlib import Path

PROJECT_DIR = Path(
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
)

LOG_BASE_DIR = os.environ.get("CURSOR_HOOKS_LOG_DIR", str(PROJECT_DIR / "logs"))


def get_session_log_dir(session_id: str) -> Path:
    return Path(LOG_BASE_DIR) / session_id


def ensure_session_log_dir(session_id: str) -> Path:
    log_dir = get_session_log_dir(session_id)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
