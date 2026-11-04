#!/usr/bin/env python3
"""Cursor Hook: SubagentStart — Subagent Start Logger.

Fires on: SubagentStart (when a subagent is spawned)
Purpose:  Log subagent start events and emit observability event.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Always exits 0 to avoid blocking the agent.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from mao_worktree import collect_mao_worktree_metadata
from utils import runtime_messaging as runtime
from session_id import extract_session_id
from utils.constants import ensure_session_log_dir
from utils.proof_tiers import classify_subagent_proof_tier
from utils.spawn_trace import append_trace_event, resolve_repo_root_from_hook_payload

MAO_TASK_CONTEXT_MARKER = "MAO_TASK_CONTEXT_JSON:"
_MAO_ROLE_BY_TAG = {
    "[mao:build]": "builder",
    "[mao:validate]": "verifier",
}
_MAO_ARTIFACT_BY_TAG = {
    "[mao:build]": "build-result.md",
    "[mao:validate]": "verify-result.md",
}
_MAO_DEPENDENCY_BY_TAG = {
    "[mao:build]": "plan",
    "[mao:validate]": "build",
}
SCRIPT_NAME = "subagent_start.py"
_SCOPE_AUDIT_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "mat-scope-audit.py"


def _load_scope_audit_module():
    """Load mat-scope-audit helpers (fail-open if missing)."""
    if not _SCOPE_AUDIT_SCRIPT.is_file():
        return None
    spec = importlib.util.spec_from_file_location(
        "mat_scope_audit_from_start", _SCOPE_AUDIT_SCRIPT
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


def maybe_write_scope_start_snapshot(input_data: dict[str, Any]) -> Path | None:
    """Write advisory start porcelain snapshot under artifacts/mao/scope-audit/."""
    try:
        mod = _load_scope_audit_module()
        if mod is None:
            return None
        root = repo_root_from_hook_payload(input_data)
        ctx = input_data.get("mao_task_context")
        role = "builder"
        if isinstance(ctx, dict) and isinstance(ctx.get("role"), str) and ctx["role"].strip():
            role = ctx["role"].strip()
        else:
            raw_type = str(input_data.get("subagent_type") or "").strip().lower()
            if "verif" in raw_type:
                role = "verifier"
            elif "parent" in raw_type or "orchestr" in raw_type:
                role = "parent-orchestrator"
        run_payload = {
            **input_data,
            "run_id": input_data.get("CURSOR_AGENT_TRACE_RUN_ID")
            or input_data.get("trace_run_id")
            or input_data.get("run_id")
            or input_data.get("subagent_id")
            or input_data.get("subagentId"),
        }
        return mod.write_start_snapshot(root, role=role, payload=run_payload)
    except Exception:
        return None


def repo_root_from_hook_payload(raw: dict[str, Any]) -> Path:
    """
    Resolve repo root for MAO worktree metadata (fail-open).

    Prefer ``CURSOR_PROJECT_DIR`` / ``CLAUDE_PROJECT_DIR`` when set so SubagentStart
    matches ``post_tool_validate.PROJECT_DIR`` and gate/todo observation hooks. When
    those env vars are unset, use the first non-empty ``workspace_roots`` entry from
    the hook payload, then ``cwd``.
    """
    return resolve_repo_root_from_hook_payload(raw)


def read_stdin_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def extract_mao_task_context(task_text: Any) -> dict[str, Any] | None:
    if not isinstance(task_text, str):
        return None

    for line in task_text.splitlines():
        if MAO_TASK_CONTEXT_MARKER not in line:
            continue

        _, raw_context = line.split(MAO_TASK_CONTEXT_MARKER, 1)
        try:
            parsed = json.loads(raw_context.strip())
        except json.JSONDecodeError:
            return None

        return validate_mao_task_context(parsed)

    return None


def validate_mao_task_context(raw_context: Any) -> dict[str, Any] | None:
    if not isinstance(raw_context, dict):
        return None

    tag = raw_context.get("tag")
    role = raw_context.get("role")
    primary_artifact = raw_context.get("primary_artifact")
    handoff_inputs = raw_context.get("handoff_inputs")
    depends_on = raw_context.get("depends_on")

    if tag not in _MAO_ROLE_BY_TAG:
        return None
    if role != _MAO_ROLE_BY_TAG[tag]:
        return None
    if primary_artifact != _MAO_ARTIFACT_BY_TAG[tag]:
        return None
    if not isinstance(handoff_inputs, list) or not handoff_inputs:
        return None
    if any(not isinstance(path, str) or not path.strip() for path in handoff_inputs):
        return None

    normalized: dict[str, Any] = {
        "tag": tag,
        "role": role,
        "primary_artifact": primary_artifact,
        "handoff_inputs": handoff_inputs,
    }

    expected_dependency = _MAO_DEPENDENCY_BY_TAG[tag]
    if depends_on is not None:
        if depends_on != expected_dependency:
            return None
        normalized["depends_on"] = depends_on

    task_id = raw_context.get("task_id")
    if task_id is not None:
        task_id_text = str(task_id).strip()
        if not task_id_text:
            return None
        normalized["task_id"] = task_id_text

    spawn_correlation_id = raw_context.get("spawn_correlation_id")
    if spawn_correlation_id is not None:
        correlation_text = str(spawn_correlation_id).strip()
        if not correlation_text:
            return None
        normalized["spawn_correlation_id"] = correlation_text

    wt = raw_context.get("mao_worktree")
    if wt is not None and isinstance(wt, dict):
        lbl = wt.get("label")
        if isinstance(lbl, str):
            stripped = lbl.strip()
            if stripped:
                normalized["mao_worktree"] = {
                    "label": stripped,
                    "source": "parent_prompt",
                }

    return normalized


def enrich_subagent_payload(input_data: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(input_data)
    root = repo_root_from_hook_payload(input_data)
    enriched["mao_worktree"] = collect_mao_worktree_metadata(root)
    mao_task_context = extract_mao_task_context(input_data.get("task"))
    if mao_task_context is not None:
        enriched["mao_task_context"] = mao_task_context
    raw_subagent_type = str(input_data.get("subagent_type") or "").strip() or "unknown"
    enriched["runtime_evidence"] = {
        "raw_subagent_type": raw_subagent_type,
        "raw_task_present": isinstance(input_data.get("task"), str),
    }
    return enriched


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        input_data = read_stdin_payload()
        enriched_input = enrich_subagent_payload(input_data)
        session_id = extract_session_id(enriched_input)

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="SubagentStart",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: parsed payload without log writes or nested emit.",
                    details={
                        "session_id": session_id,
                        "mao_task_context_present": "mao_task_context" in enriched_input,
                        "mao_worktree": enriched_input.get("mao_worktree"),
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / "subagent_start.json"

        log_data: list = []
        if log_path.exists():
            try:
                log_data = json.loads(log_path.read_text())
            except (json.JSONDecodeError, ValueError):
                log_data = []

        log_data.append(enriched_input)
        log_path.write_text(json.dumps(log_data, indent=2))

        try:
            maybe_write_scope_start_snapshot(enriched_input)
        except Exception:
            pass

        try:
            root = repo_root_from_hook_payload(enriched_input)
            child_id = str(
                enriched_input.get("subagent_id") or enriched_input.get("subagentId") or ""
            )
            session_payload = {
                "session_id": session_id,
                "session_kind": "subagent",
                "role": str(
                    enriched_input.get("mao_task_context", {}).get("role")
                    or enriched_input.get("subagent_type")
                    or "subagent"
                ),
                "run_id": enriched_input.get("CURSOR_AGENT_TRACE_RUN_ID")
                or enriched_input.get("trace_run_id")
                or enriched_input.get("run_id"),
                "repo_root": str(root),
                "branch": enriched_input.get("branch"),
                "is_active": True,
            }
            runtime.record_hook_session_start(
                root,
                session_payload,
                payload={
                    "source": "hook:SubagentStart",
                    "subagent_id": child_id,
                    "task_present": isinstance(enriched_input.get("task"), str),
                },
            )
            ctx = enriched_input.get("mao_task_context") or {}
            trace_fields = {
                "source": "hook:SubagentStart",
                "session_id": session_id,
                "parent_id": None,
                "child_id": child_id,
                "role": ctx.get("role"),
                "model": enriched_input.get("model") or enriched_input.get("cursor_model"),
                "task_id": ctx.get("task_id")
                or enriched_input.get("task_id")
                or enriched_input.get("taskId"),
                "spawn_correlation_id": ctx.get("spawn_correlation_id"),
                "role_attribution_source": "mao_task_context" if ctx.get("role") else None,
                "decision": "spawn_observed",
                "reason": "SubagentStart hook fired (actual Task spawn is Cursor-controlled)",
                "raw_subagent_type": (
                    enriched_input.get("runtime_evidence", {}).get("raw_subagent_type")
                ),
            }
            trace_fields["proof_tier"] = classify_subagent_proof_tier(trace_fields)
            append_trace_event(
                root,
                event_kind="spawn_success",
                fields=trace_fields,
            )
        except Exception:
            pass

        # Emit observability event via send_event.py
        try:
            send_event_script = Path(__file__).parent / "send_event.py"
            if send_event_script.exists():
                subprocess.run(
                    [sys.executable, str(send_event_script)],
                    input=json.dumps(enriched_input),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
        except Exception:
            pass

    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="SubagentStart",
                script=SCRIPT_NAME,
                kind="error",
                message=f"subagent_start failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
