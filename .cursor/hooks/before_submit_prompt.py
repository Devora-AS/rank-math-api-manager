#!/usr/bin/env python3
"""Cursor Hook: beforeSubmitPrompt — Prompt Submission Handler

Fires on: beforeSubmitPrompt (replaces Claude's UserPromptSubmit)
Purpose:  Log user prompts, optionally validate them, and manage session data.
          Outputs JSON to stdout to control whether the prompt proceeds.

Output protocol:
  {"continue": true}                          — allow the prompt
  {"continue": false, "user_message": "..."}  — block with feedback

Always exits 0 to avoid blocking the agent.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv
from utils.context_budget import (
    append_prompt_lint_log,
    append_session_budget_advisory_note,
    build_prompt_lint_report,
)
from utils.routing_advisory import append_routing_advisory_jsonl, build_routing_advisory
from utils.routing_rollup import write_routing_rollup_json
from utils.constants import PROJECT_DIR, ensure_session_log_dir
from utils.mat_env_resolve import mat_env_flag
from session_id import extract_session_id

SCRIPT_NAME = "before_submit_prompt.py"


def read_stdin_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def log_user_prompt(session_id: str, input_data: dict, routing_advisory: dict | None = None) -> None:
    """Log the prompt to the session log directory."""
    try:
        log_dir = ensure_session_log_dir(session_id)
        log_file = log_dir / "user_prompts.json"

        log_data: list = []
        if log_file.exists():
            try:
                log_data = json.loads(log_file.read_text())
            except (json.JSONDecodeError, ValueError):
                log_data = []

        log_data.append({
            **input_data,
            **({"routing_advisory": routing_advisory} if routing_advisory else {}),
            "logged_at": datetime.now().isoformat(),
        })

        log_file.write_text(json.dumps(log_data, indent=2))
    except OSError:
        pass


def manage_session_data(session_id: str, prompt: str, name_agent: bool = False) -> None:
    """Store prompt in session data JSON, optionally generate an agent name."""
    try:
        sessions_dir = PROJECT_DIR / ".cursor" / "data" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        session_file = sessions_dir / f"{session_id}.json"

        if session_file.exists():
            try:
                session_data = json.loads(session_file.read_text())
            except (json.JSONDecodeError, ValueError):
                session_data = {"session_id": session_id, "prompts": []}
        else:
            session_data = {"session_id": session_id, "prompts": []}

        session_data["prompts"].append(prompt)

        if name_agent and "agent_name" not in session_data:
            try:
                result = subprocess.run(
                    [sys.executable, str(Path(__file__).parent / "utils" / "llm" / "anth.py"), "--agent-name"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    agent_name = result.stdout.strip()
                    if len(agent_name.split()) == 1 and agent_name.isalnum():
                        session_data["agent_name"] = agent_name
            except Exception:
                pass

        session_file.write_text(json.dumps(session_data, indent=2))
    except OSError:
        pass


def validate_prompt(prompt: str) -> tuple[bool, str | None]:
    """Validate the user prompt. Returns (is_valid, reason)."""
    blocked_patterns: list[tuple[str, str]] = [
        # Add patterns to block, e.g.:
        # ("rm -rf /", "Dangerous command detected"),
    ]

    prompt_lower = prompt.lower()
    for pattern, reason in blocked_patterns:
        if pattern.lower() in prompt_lower:
            return False, reason

    return True, None


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        input_data = read_stdin_payload()
        session_id = extract_session_id(input_data)
        prompt = input_data.get("prompt", "")
        routing_advisory = build_routing_advisory(
            input_data, "beforeSubmitPrompt", fallback_text=prompt
        )
        prompt_lint_report = build_prompt_lint_report(
            input_data,
            fallback_text=prompt,
            session_id=session_id,
            hook_event="beforeSubmitPrompt",
        )

        store_last = mat_env_flag("CURSOR_STORE_PROMPTS", default=False)
        name_agent = mat_env_flag("CURSOR_NAME_AGENT", default=False)
        do_validate = mat_env_flag("CURSOR_VALIDATE_PROMPTS", default=False)
        is_valid, reason = validate_prompt(prompt) if do_validate else (True, None)

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="beforeSubmitPrompt",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: evaluated prompt handling without writes or blocking output.",
                    details={
                        "session_id": session_id,
                        "prompt": prompt,
                        "routing_advisory": routing_advisory,
                        "prompt_lint": prompt_lint_report,
                        "would_store_prompt": store_last,
                        "would_name_agent": name_agent,
                        "would_validate": do_validate,
                        "would_continue": is_valid,
                        "blocked_reason": reason,
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            if prompt_lint_report.get("warnings"):
                for warning in prompt_lint_report["warnings"]:
                    print(f"[prompt_lint] {warning['message']}", file=sys.stderr)
            sys.exit(0)

        log_user_prompt(session_id, input_data, routing_advisory=routing_advisory)
        prompt_lint_log_path = append_prompt_lint_log(PROJECT_DIR, prompt_lint_report)
        if prompt_lint_report.get("warnings"):
            for warning in prompt_lint_report["warnings"]:
                print(f"[prompt_lint] {warning['message']}", file=sys.stderr)
            if prompt_lint_log_path is not None:
                print(f"[prompt_lint] log written to {prompt_lint_log_path}", file=sys.stderr)
        write_routing_rollup_json(PROJECT_DIR, routing_advisory, hook_event="beforeSubmitPrompt")
        append_routing_advisory_jsonl(PROJECT_DIR, routing_advisory, hook_event="beforeSubmitPrompt")
        append_session_budget_advisory_note(PROJECT_DIR, session_id)

        if store_last or name_agent:
            manage_session_data(session_id, prompt, name_agent=name_agent)

        if do_validate:
            if not is_valid:
                print(json.dumps({"continue": False, "user_message": f"Prompt blocked: {reason}"}))
                sys.exit(0)

        print(json.dumps({"continue": True}))
    except Exception as exc:
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="beforeSubmitPrompt",
                script=SCRIPT_NAME,
                kind="error",
                message=f"before_submit_prompt failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )
        print(json.dumps({"continue": True}))

    sys.exit(0)


if __name__ == "__main__":
    main()
