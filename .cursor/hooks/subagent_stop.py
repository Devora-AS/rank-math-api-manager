#!/usr/bin/env python3
"""Cursor Hook: SubagentStop — advisory role scope audit at stop.

Fires on: SubagentStop
Purpose:  Diff worktree vs start snapshot; write advisory scope-audit JSON.
Always exits 0 (fail-open). Does not block the agent.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from session_id import extract_session_id
from utils.spawn_trace import resolve_repo_root_from_hook_payload

SCRIPT_NAME = "subagent_stop.py"
REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_AUDIT_SCRIPT = REPO_ROOT / "scripts" / "mat-scope-audit.py"


def _load_scope_audit():
    if not SCOPE_AUDIT_SCRIPT.is_file():
        return None
    spec = importlib.util.spec_from_file_location("mat_scope_audit_hook", SCOPE_AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_stdin_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def repo_root_from_hook_payload(raw: dict[str, Any]) -> Path:
    return resolve_repo_root_from_hook_payload(raw)


def resolve_role(input_data: dict[str, Any]) -> str:
    ctx = input_data.get("mao_task_context")
    if isinstance(ctx, dict):
        role = ctx.get("role")
        if isinstance(role, str) and role.strip():
            return role.strip()
    for key in ("role", "subagent_type", "agent"):
        value = input_data.get(key)
        if isinstance(value, str) and value.strip():
            text = value.strip()
            if text in {"builder", "verifier", "parent-orchestrator"}:
                return text
            lowered = text.lower()
            if "verif" in lowered:
                return "verifier"
            if "build" in lowered:
                return "builder"
            if "parent" in lowered or "orchestr" in lowered:
                return "parent-orchestrator"
    return "builder"


def maybe_run_scope_stop_audit(input_data: dict[str, Any]) -> dict[str, Any] | None:
    """Compute stop snapshot + advisory audit; never raises to caller."""
    try:
        mod = _load_scope_audit()
        if mod is None:
            return None
        root = repo_root_from_hook_payload(input_data)
        role = resolve_role(input_data)
        run_id = mod.default_run_id(
            {
                **input_data,
                "run_id": input_data.get("CURSOR_AGENT_TRACE_RUN_ID")
                or input_data.get("trace_run_id")
                or input_data.get("run_id")
                or input_data.get("subagent_id")
                or input_data.get("subagentId"),
            }
        )
        extra: list[str] = []
        ctx = input_data.get("mao_task_context")
        if isinstance(ctx, dict):
            handoffs = ctx.get("handoff_inputs")
            if isinstance(handoffs, list):
                extra.extend(str(p) for p in handoffs if isinstance(p, str))
            primary = ctx.get("primary_artifact")
            if isinstance(primary, str) and primary.strip():
                extra.append(primary.strip())
        # D2b: project active-plan Relevant Files / implementation paths for builder.
        # Protected paths still breach even if listed (check_role_scope). Fail-open on IO/parse.
        if role == "builder":
            try:
                plan_path = mod.resolve_active_plan_path(root, input_data)
                if hasattr(mod, "load_plan_listed_paths"):
                    extra.extend(mod.load_plan_listed_paths(plan_path))
                elif plan_path.is_file():
                    extra.extend(mod.plan_listed_paths(plan_path.read_text(encoding="utf-8")))
            except Exception:
                pass
        audit_path = mod.write_stop_audit(
            root,
            role=role,
            run_id=run_id,
            extra_allow=extra,
            payload=input_data,
        )
        return {"audit_path": str(audit_path), "role": role, "run_id": run_id}
    except Exception as exc:
        return {"error": str(exc), "advisory": True}


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        input_data = read_stdin_payload()
        session_id = extract_session_id(input_data)

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="SubagentStop",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: parsed payload without scope audit writes.",
                    details={"session_id": session_id},
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        maybe_run_scope_stop_audit(input_data)
    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="SubagentStop",
                script=SCRIPT_NAME,
                kind="error",
                message=f"subagent_stop failed: {exc}",
                details={},
                retryable=True,
                dry_run=getattr(args, "dry_run", False),
            ),
            stream=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
