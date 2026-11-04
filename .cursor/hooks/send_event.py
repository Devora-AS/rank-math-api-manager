#!/usr/bin/env python3
"""
send_event.py — Cursor Hook: Observability Event Emitter

Fires on: PostToolUse, Stop, SubagentStop
Purpose:  Reads the Cursor hook payload from stdin and POSTs a normalized
          event to the local observability server (Bun + SQLite + Vue).

Translated from: disler/claude-code-hooks-multi-agent-observability
Original path:   .claude/hooks/send_event.py
Changes from original:
  - Replaced CLAUDE_PROJECT_DIR with CURSOR_PROJECT_DIR (with fallback to cwd)
  - Added Cursor-specific payload field normalization
  - Always exits 0 to avoid blocking the agent (failClosed: false)

Payload field verification status: BASELINE VERIFIED (Phase 1 + 2026-03-26 audit)
  Cursor passes a JSON object on stdin (see https://cursor.com/docs/hooks).
  This script reads common variants (session_id/sessionId, tool_name/tool/toolName,
  tool_output/toolOutput/result, subagent_id) and prefers CURSOR_HOOK_EVENT when
  set by the runtime. Golden lifecycle samples: artifacts/phase1/raw_payloads-final3/.
  Re-verify after Cursor hook contract changes — docs/archive/hook-payload-verification.md.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from utils.context_budget import append_session_budget_advisory_note
from payload_capture import (
    extract_hook_event_name as extract_hook_event_name_from_payload,
    maybe_capture_payload,
    read_payload_from_stdin,
)
from session_id import extract_session_id
from utils.routing_advisory import append_routing_advisory_jsonl, build_routing_advisory
from utils.routing_rollup import write_routing_rollup_json

from utils import runtime_messaging as runtime
from utils.mat_env_resolve import mat_env_get

try:
    from utils.spawn_trace import (
        append_trace_event,
        load_persisted_subagent_trace_context,
        resolve_repo_root_from_hook_payload,
    )
except ImportError:
    append_trace_event = None  # type: ignore[misc, assignment]
    load_persisted_subagent_trace_context = None  # type: ignore[misc, assignment]
    resolve_repo_root_from_hook_payload = None  # type: ignore[misc, assignment]

PROJECT_DIR = (
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")  # compatibility fallback
    or os.getcwd()
)
SCRIPT_NAME = "send_event.py"


def _observability_server_url(project_dir: str | Path) -> str:
    root = Path(project_dir).resolve()
    return (
        mat_env_get("OBSERVABILITY_SERVER_URL", default="http://localhost:3001/events", root=root)
        or "http://localhost:3001/events"
    )


def _observability_api_token(project_dir: str | Path) -> str:
    root = Path(project_dir).resolve()
    return (mat_env_get("OBSERVABILITY_API_TOKEN", default="", root=root) or "").strip()


def extract_project_dir(raw: dict) -> str:
    if resolve_repo_root_from_hook_payload is not None:
        return str(resolve_repo_root_from_hook_payload(raw))
    workspace_roots = raw.get("workspace_roots") or raw.get("workspaceRoots")
    if isinstance(workspace_roots, list):
        for item in workspace_roots:
            if item and str(item).strip():
                return str(Path(str(item).strip()).resolve())
    return PROJECT_DIR


def extract_hook_event_name(raw: dict) -> str | None:
    """Best-effort hook/event name from payload when env is unset."""
    return extract_hook_event_name_from_payload(raw)


def resolve_hook_event(raw: dict) -> str:
    hook_event = (
        os.environ.get("CURSOR_HOOK_EVENT")
        or os.environ.get("CLAUDE_HOOK_EVENT")  # compatibility
        or extract_hook_event_name(raw)
    )
    if hook_event:
        return hook_event
    if raw.get("subagent_id") or raw.get("subagentId"):
        return "SubagentStop"
    if raw.get("tool_name") or raw.get("tool") or raw.get("toolName"):
        return "PostToolUse"
    if raw.get("status") or raw.get("final_response") or raw.get("response"):
        return "Stop"
    return "unknown"


def normalize_event(raw: dict, hook_event: str) -> dict:
    """
    Normalize the Cursor hook payload into the observability server schema.

    Field names are aligned with Cursor docs and committed captures (see
    docs/archive/hook-payload-verification.md). Extend aliases here when new keys
    appear in stdin after a Cursor upgrade.

    Expected observability schema (apps/server/src/types.ts):
      { event_type, session_id, timestamp, project_dir, tool_name,
        tool_input, tool_output, summary, raw }
    """
    now = datetime.now(timezone.utc).isoformat()

    session_id = extract_session_id(raw)
    tool_name = raw.get("tool_name") or raw.get("tool") or raw.get("toolName") or ""
    if hook_event == "SubagentStop" and not tool_name:
        tool_name = raw.get("subagent_id") or raw.get("subagentId") or "subagent"
    tool_input = raw.get("tool_input") or raw.get("toolInput") or {}
    tool_output = raw.get("tool_output") or raw.get("toolOutput") or raw.get("result") or ""
    if hook_event == "SubagentStop" and not tool_output:
        tool_output = raw.get("status") or raw.get("output") or ""
    if hook_event == "Stop" and not tool_output:
        tool_output = (
            raw.get("final_response")
            or raw.get("response")
            or raw.get("message")
            or raw.get("status")
            or ""
        )

    return {
        "event_type": hook_event or raw.get("hook_event") or "unknown",
        "session_id": session_id,
        "timestamp": now,
        "project_dir": extract_project_dir(raw),
        "tool_name": tool_name,
        "tool_input": tool_input if isinstance(tool_input, str) else json.dumps(tool_input),
        "tool_output": tool_output if isinstance(tool_output, str) else json.dumps(tool_output),
        "summary": f"{hook_event}: {tool_name}".strip(": "),
        "raw": json.dumps(raw),
    }


def post_event(event: dict) -> None:
    """POST the normalized event to the observability server."""
    project_dir = event.get("project_dir") or PROJECT_DIR
    payload = json.dumps(event).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = _observability_api_token(project_dir)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        _observability_server_url(project_dir),
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            _ = resp.read()
    except urllib.error.URLError:
        # Server not running — fail silently, always exit 0
        pass
    except OSError:
        pass


def _runtime_session_from_payload(raw: dict, hook_event: str) -> dict[str, object]:
    session_kind = "subagent" if hook_event == "SubagentStop" else "task"
    role = raw.get("role") or raw.get("subagent_type") or raw.get("tool_name") or "task"
    return {
        "session_id": extract_session_id(raw),
        "session_kind": session_kind,
        "role": str(role),
        "run_id": raw.get("trace_run_id") or raw.get("run_id"),
        "repo_root": extract_project_dir(raw),
        "branch": raw.get("branch"),
        "is_active": hook_event != "SubagentStop",
    }


def main(argv: list[str] | None = None) -> None:
    # Determine which hook event triggered this script.
    # Cursor may pass the event name via env and/or stdin JSON.
    args = parse_contract_argv(argv)
    hook_event = "unknown"
    try:
        raw_payload, _ = read_payload_from_stdin()
        hook_event = resolve_hook_event(raw_payload)
        normalized = normalize_event(raw_payload, hook_event)
        routing_advisory = build_routing_advisory(raw_payload, hook_event)
        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event=hook_event,
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: skipped payload capture and observability POST.",
                    details={
                        "normalized_event": normalized,
                        "routing_advisory": routing_advisory,
                        "would_post_url": _observability_server_url(normalized["project_dir"]),
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        maybe_capture_payload(raw_payload, hook_event, PROJECT_DIR)
        write_routing_rollup_json(PROJECT_DIR, routing_advisory, hook_event=hook_event)
        append_routing_advisory_jsonl(PROJECT_DIR, routing_advisory, hook_event=hook_event)
        append_session_budget_advisory_note(PROJECT_DIR, extract_session_id(raw_payload))
        if hook_event in {"SubagentStop", "Stop"}:
            try:
                runtime.register_session(
                    extract_project_dir(raw_payload),
                    _runtime_session_from_payload(raw_payload, hook_event),
                )
                if hook_event == "SubagentStop":
                    runtime.record_hook_session_stop(
                        extract_project_dir(raw_payload),
                        _runtime_session_from_payload(raw_payload, hook_event),
                        payload={
                            "source": "hook:SubagentStop",
                            "status": raw_payload.get("status"),
                            "tool_output": normalized.get("tool_output"),
                        },
                    )
                else:
                    followup = runtime.render_followup_message(
                        extract_project_dir(raw_payload),
                        extract_session_id(raw_payload),
                    )
                    if followup.get("followup_message"):
                        normalized["summary"] = (
                            f"{normalized['summary']} | {followup['followup_message']}"
                        )
            except Exception:
                pass
        post_event(normalized)
        if append_trace_event and hook_event.strip().lower().replace(
            "_", ""
        ) == "subagentstop":
            try:
                root = Path(extract_project_dir(raw_payload))
                sid = extract_session_id(raw_payload)
                child = str(
                    raw_payload.get("subagent_id")
                    or raw_payload.get("subagentId")
                    or ""
                )
                persisted = (
                    load_persisted_subagent_trace_context(root, child)
                    if load_persisted_subagent_trace_context
                    else None
                ) or {}
                append_trace_event(
                    root,
                    event_kind="subagent_stop",
                    fields={
                        "source": "hook:SubagentStop",
                        "session_id": sid,
                        "parent_id": None,
                        "child_id": child,
                        "role": persisted.get("role"),
                        "model": raw_payload.get("model")
                        or raw_payload.get("cursor_model")
                        or persisted.get("model_source_label")
                        or persisted.get("model_label"),
                        "task_id": persisted.get("task_id")
                        or raw_payload.get("task_id")
                        or raw_payload.get("taskId"),
                        "spawn_correlation_id": persisted.get("spawn_correlation_id")
                        or raw_payload.get("spawn_correlation_id")
                        or raw_payload.get("spawnCorrelationId"),
                        "decision": "subagent_finished",
                        "reason": "SubagentStop hook fired",
                    },
                )
            except Exception:
                pass
    except Exception as exc:
        # Never block the agent — log and continue (failClosed: false)
        emit_contract_envelope(
            make_contract_envelope(
                hook_event=hook_event,
                script=SCRIPT_NAME,
                kind="error",
                message=f"send_event failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )

    # Always exit 0 — never block the agent due to observability failure
    sys.exit(0)


if __name__ == "__main__":
    main()
