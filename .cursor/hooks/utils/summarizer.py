#!/usr/bin/env python3
"""Event summary generator for Cursor hook observability.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Uses Anthropic Haiku to generate concise one-sentence event summaries.
"""

import json
from typing import Any

try:
    from .llm.anth import prompt_llm
except ImportError:
    prompt_llm = None  # type: ignore[assignment]


def generate_event_summary(event_data: dict[str, Any]) -> str | None:
    """Generate a concise one-sentence summary of a hook event for engineers.

    Returns None if the LLM is unavailable or generation fails.
    """
    if prompt_llm is None:
        return None

    event_type = event_data.get("hook_event_type", "Unknown")
    payload = event_data.get("payload", {})

    payload_str = json.dumps(payload, indent=2)
    if len(payload_str) > 1000:
        payload_str = payload_str[:1000] + "..."

    prompt = f"""Generate a one-sentence summary of this Cursor hook event payload for an engineer monitoring the system.

Event Type: {event_type}
Payload:
{payload_str}

Requirements:
- ONE sentence only (no period at the end)
- Focus on the key action or information in the payload
- Be specific and technical
- Keep under 15 words
- Use present tense
- No quotes or formatting
- Return ONLY the summary text

Examples:
- Reads configuration file from project root
- Executes npm install to update dependencies
- Searches web for React documentation
- Edits database schema to add user table
- Agent responds with implementation plan

Generate the summary based on the payload:"""

    summary = prompt_llm(prompt)

    if summary:
        summary = summary.strip().strip('"').strip("'").strip(".")
        summary = summary.split("\n")[0].strip()
        if len(summary) > 100:
            summary = summary[:97] + "..."

    return summary
