from __future__ import annotations

from typing import Any, Iterable, Sequence

MAX_LEARNED_BULLETS = 12


def _normalize_bullet(text: object) -> str:
    return " ".join(str(text).split()).strip()


def dedupe_learned_bullets(
    bullets: Sequence[object],
    *,
    max_items: int = MAX_LEARNED_BULLETS,
) -> list[str]:
    """Return bullet text with whitespace-normalized semantic duplicates removed."""
    seen: set[str] = set()
    deduped: list[str] = []
    for bullet in bullets:
        normalized = _normalize_bullet(bullet)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
        if len(deduped) >= max_items:
            break
    return deduped


def assess_agents_change_intent(
    changed_files: Iterable[str],
    *,
    audit_trail_present: bool,
) -> dict[str, Any]:
    """Classify whether an AGENTS change should be treated as intentional maintenance."""
    normalized_files = [str(path).replace("\\", "/") for path in changed_files]
    agents_changed = any(path.endswith("/AGENTS.md") or path == "AGENTS.md" for path in normalized_files)
    intentional = bool(agents_changed and audit_trail_present)
    return {
        "agents_changed": agents_changed,
        "audit_trail_present": audit_trail_present,
        "intentional": intentional,
        "should_block_as_dirty_worktree": bool(agents_changed and not intentional),
        "recommended_action": "fresh_session" if intentional else "queue_or_review",
    }


def build_continual_learning_summary(
    *,
    audit_trail_present: bool,
    active_session: bool,
    changed_files: Iterable[str],
) -> dict[str, Any]:
    """Summarize the safest action for a continual-learning run."""
    intent = assess_agents_change_intent(changed_files, audit_trail_present=audit_trail_present)
    if active_session and intent["intentional"]:
        mode = "queue_and_defer"
    elif active_session:
        mode = "queue"
    elif intent["intentional"]:
        mode = "fresh_session"
    else:
        mode = "defer"
    return {
        "mode": mode,
        "intent": intent,
        "active_session": active_session,
        "audit_trail_present": audit_trail_present,
        "contamination_risk": mode in {"queue", "queue_and_defer"},
    }
