"""Shared session id extraction for Cursor hook scripts."""

from __future__ import annotations

import os
from typing import Any


def extract_session_id(raw: dict[str, Any]) -> str:
    """Prefer stdin JSON keys, then hook process env (see docs/archive/hook-payload-verification.md)."""
    raw_keys = (
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "parent_conversation_id",
        "parentConversationId",
        "generation_id",
        "generationId",
        "workspace_id",
        "workspaceId",
        "trace_id",
        "traceId",
        "chat_id",
        "chatId",
        "thread_id",
        "threadId",
    )
    for key in raw_keys:
        val = raw.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    for key in ("CURSOR_SESSION_ID", "CURSOR_TRACE_ID", "SESSION_ID"):
        val = os.environ.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return "unknown"
