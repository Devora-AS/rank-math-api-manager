"""MAT Self-Compact v2 — MCP tool handlers (stdio server calls these)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import mat_self_compact as msc
from mat_mcp_operator_tools import make_envelope

_CHECKPOINT_PROCEDURE = """MAT Self-Compact checkpoint (no native Cursor compaction API):

1. Write artifacts/context-handoff/note-to-self.md — intent, open decisions, next commands, MAO pointers.
2. Refresh docs/current-plan.md markers and build-result.md / verify-result.md when mid-slice.
3. Run python3 scripts/mat-context-gauge.py (or MCP view_context) for current pressure.
4. Update artifacts/context-handoff/context-state.json when coordinating pending_compact with hooks.
5. Ask the operator for manual Summarize when context is full; preCompact is observe-only.

MAO files remain authoritative: docs/current-plan.md, build-result.md, verify-result.md.
"""


def _relative_handoff_paths(root: Path) -> dict[str, str]:
    return {
        "note_to_self": msc.note_to_self_path(root).relative_to(root).as_posix(),
        "context_state": msc.context_state_path(root).relative_to(root).as_posix(),
        "last_gauge": msc.last_gauge_path(root).relative_to(root).as_posix(),
        "last_compact": msc.last_compact_path(root).relative_to(root).as_posix(),
        "pre_tool_context_usage_log": msc.pre_tool_context_usage_log_path(root)
        .relative_to(root)
        .as_posix(),
    }


def view_context(repo_root: Path) -> dict[str, Any]:
    """Pi-like gauge JSON from last hook snapshot and thresholds (advisory envelope)."""
    root = repo_root.resolve()
    gauge = msc.build_gauge_output(root)
    return make_envelope(
        "view_context",
        root,
        ok=True,
        data=gauge,
    )


def mat_self_compact_checkpoint(repo_root: Path) -> dict[str, Any]:
    """Checkpoint procedure, handoff paths, and current gauge (advisory envelope)."""
    root = repo_root.resolve()
    gauge = msc.build_gauge_output(root)
    payload = {
        "procedure": _CHECKPOINT_PROCEDURE.strip(),
        "handoff_paths": _relative_handoff_paths(root),
        "gauge": gauge,
        "skill": ".cursor/skills/mat-self-compact/SKILL.md",
        "spec": "specs/mat-self-compact-cursor.md",
    }
    return make_envelope(
        "mat_self_compact",
        root,
        ok=True,
        data=payload,
    )
