"""Observability security helpers: redaction patterns + bind policy (E6-baseline).

Mirrors apps/server/src/security.ts redaction semantics for purge tooling and
Python regression tests. Server ingest remains the authoritative write path.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

# Default max POST body size (bytes) — keep in sync with security.ts
DEFAULT_MAX_PAYLOAD_BYTES = 262_144

# Credential / secret-like patterns
_CREDENTIAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\b(api[_-]?key|secret|password|token|authorization)\s*[:=]\s*['\"]?[^\s'\"]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer [REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "sk-[REDACTED]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AKIA[REDACTED]"),
    (re.compile(r"(?i)\bxox[baprs]-[0-9A-Za-z-]{10,}"), "xox[REDACTED]"),
]

# Absolute home / user path fragments
_HOME_PATH_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"/Users/[^/\s\"']+"), "/Users/[REDACTED]"),
    (re.compile(r"/home/[^/\s\"']+"), "/home/[REDACTED]"),
    (re.compile(r"(?i)\bC:\\Users\\[^\\\s\"']+"), r"C:\\Users\\[REDACTED]"),
]

# PII / prompt fragments
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
]

_ALL_PATTERNS = _CREDENTIAL_PATTERNS + _HOME_PATH_PATTERNS + _PII_PATTERNS

# Fields that often carry prompts / transcripts — truncate aggressively
_PROMPT_FIELD_KEYS = frozenset(
    {
        "prompt",
        "user_prompt",
        "system_prompt",
        "transcript",
        "message",
        "content",
        "tool_output",
        "tool_input",
        "raw",
        "legacy_normalized_raw",
    }
)

_PROMPT_MAX_CHARS = 500


def redact_string(value: str) -> str:
    out = value
    for pattern, repl in _ALL_PATTERNS:
        if "\\" in repl and any(ch.isdigit() for ch in repl):
            # Backreference-style replacements (e.g. \1=…)
            out = pattern.sub(repl, out)
        else:
            # Literal replacements — avoid re.sub interpreting \U etc.
            out = pattern.sub(lambda m, r=repl: r, out)
    return out


def _truncate_promptish(key: str, value: str) -> str:
    if key.lower() in _PROMPT_FIELD_KEYS and len(value) > _PROMPT_MAX_CHARS:
        return value[:_PROMPT_MAX_CHARS] + "…[REDACTED_TRUNCATED]"
    return value


def redact_event_payload(payload: Any) -> Any:
    """Deep-redact secrets, home paths, emails; truncate prompt-like fields."""
    if isinstance(payload, str):
        return redact_string(payload)
    if isinstance(payload, list):
        return [redact_event_payload(item) for item in payload]
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for key, val in payload.items():
            if isinstance(val, str):
                out[key] = redact_string(_truncate_promptish(str(key), val))
            else:
                out[key] = redact_event_payload(val)
        return out
    return payload


def max_payload_bytes(env: dict[str, str] | None = None) -> int:
    source = env if env is not None else os.environ
    raw = (source.get("OBSERVABILITY_MAX_PAYLOAD_BYTES") or str(DEFAULT_MAX_PAYLOAD_BYTES)).strip()
    try:
        n = int(raw)
    except ValueError:
        return DEFAULT_MAX_PAYLOAD_BYTES
    return n if n > 0 else DEFAULT_MAX_PAYLOAD_BYTES


def payload_byte_size(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def assert_payload_size(
    payload: Any, env: dict[str, str] | None = None
) -> tuple[bool, str | None]:
    limit = max_payload_bytes(env)
    size = payload_byte_size(payload)
    if size > limit:
        return False, f"payload too large ({size} > {limit} bytes)"
    return True, None


def is_loopback_host(host: str) -> bool:
    h = host.strip().lower()
    return h in {"127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1"}


def auth_token(env: dict[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    return (
        source.get("OBSERVABILITY_AUTH_TOKEN") or source.get("OBSERVABILITY_API_TOKEN") or ""
    ).strip()


def resolve_bind_hostname(env: dict[str, str] | None = None) -> str:
    """Return bind host or raise ValueError when remote bind is fail-closed."""
    source = env if env is not None else os.environ
    host = (source.get("OBSERVABILITY_HOST") or source.get("HOST") or "127.0.0.1").strip()
    if not host:
        host = "127.0.0.1"
    if is_loopback_host(host):
        return host
    allow = (source.get("OBSERVABILITY_ALLOW_REMOTE") or "").strip()
    if allow != "1":
        raise ValueError(
            "Remote bind refused: set OBSERVABILITY_ALLOW_REMOTE=1 and OBSERVABILITY_AUTH_TOKEN"
        )
    if not auth_token(source):
        raise ValueError(
            "Remote bind refused: OBSERVABILITY_AUTH_TOKEN required when OBSERVABILITY_ALLOW_REMOTE=1"
        )
    return host
