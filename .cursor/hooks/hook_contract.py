#!/usr/bin/env python3
"""Shared hook contract helpers for dry-run and structured envelopes."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Sequence, TextIO
from uuid import uuid4

from utils.mat_env_resolve import mat_env_flag, mat_env_get

PROJECT_DIR = (
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
)


class ContractArgv:
    def __init__(self, *, dry_run: bool, remaining_args: list[str]) -> None:
        self.dry_run = dry_run
        self.remaining_args = remaining_args


def parse_contract_argv(argv: Sequence[str] | None = None) -> ContractArgv:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    dry_run = False
    remaining_args: list[str] = []
    for arg in raw_args:
        if arg == "--dry-run":
            dry_run = True
            continue
        remaining_args.append(arg)
    return ContractArgv(dry_run=dry_run, remaining_args=remaining_args)


def make_contract_envelope(
    *,
    hook_event: str,
    script: str,
    kind: str,
    message: str,
    details: dict[str, Any] | None = None,
    retryable: bool,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "hook_event": hook_event,
        "script": script,
        "kind": kind,
        "message": message,
        "details": details or {},
        "retryable": retryable,
        "dry_run": dry_run,
    }


def _repo_root() -> Path:
    return Path(PROJECT_DIR).resolve()


def contract_error_observability_enabled() -> bool:
    return mat_env_flag(
        "CURSOR_HOOK_CONTRACT_EMIT_ERROR_OBSERVABILITY",
        default=False,
        root=_repo_root(),
    )


def observability_api_events_url() -> str:
    base = (
        mat_env_get(
            "OBSERVABILITY_SERVER_URL",
            default="http://localhost:3001/events",
            root=_repo_root(),
        )
        or "http://localhost:3001/events"
    ).strip()
    if not base:
        return "http://localhost:3001/api/events"
    normalized = base.rstrip("/")
    if normalized.endswith("/api/events"):
        return normalized
    if normalized.endswith("/events"):
        return f"{normalized[:-len('/events')]}/api/events"
    return f"{base.rstrip('/')}/api/events"


def should_emit_contract_error_observability(envelope: dict[str, Any]) -> bool:
    return (
        contract_error_observability_enabled()
        and envelope.get("kind") == "error"
        and envelope.get("dry_run") is False
    )


def build_contract_error_api_event(envelope: dict[str, Any]) -> dict[str, Any]:
    hook_event = str(envelope.get("hook_event") or "unknown")
    script = str(envelope.get("script") or "unknown")
    message = str(envelope.get("message") or f"{script} reported a structured hook error.")
    retryable = bool(envelope.get("retryable"))
    timestamp_ms = int(time.time() * 1000)
    session_id = (
        os.environ.get("CURSOR_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or "unknown"
    )
    agent_id = (
        os.environ.get("CURSOR_AGENT_ID")
        or os.environ.get("CLAUDE_AGENT_ID")
        or ""
    )
    return {
        "event_id": f"hook-contract-error-{timestamp_ms}-{uuid4().hex}",
        "timestamp_ms": timestamp_ms,
        "event_type": "HookContractError",
        "session_id": session_id,
        "agent_id": agent_id,
        "tool_name": script,
        "tool_type": "Hook",
        "project_dir": PROJECT_DIR,
        "summary": message,
        "payload": {
            "hook_event": hook_event,
            "script": script,
            "kind": "error",
            "message": message,
            "details": envelope.get("details") or {},
            "retryable": retryable,
            "dry_run": False,
        },
        "metadata": {
            "source": "hook_contract",
            "scope": "structured_hook_error_only",
            "fail_open": True,
        },
    }


def post_contract_error_observability(envelope: dict[str, Any]) -> bool:
    if not should_emit_contract_error_observability(envelope):
        return False
    try:
        payload = json.dumps(build_contract_error_api_event(envelope)).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        token = (mat_env_get("OBSERVABILITY_API_TOKEN", default="", root=_repo_root()) or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(
            observability_api_events_url(),
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            _ = resp.read()
        return True
    except Exception:
        return False


def emit_contract_envelope(
    envelope: dict[str, Any],
    *,
    stream: TextIO | None = None,
) -> None:
    target = stream or sys.stdout
    target.write(json.dumps(envelope))
    target.write("\n")
    target.flush()
    post_contract_error_observability(envelope)
