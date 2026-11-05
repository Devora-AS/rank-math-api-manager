#!/usr/bin/env python3
"""
mao_gate.py — MAO transition gate helpers (Phase 2 slice)

After `docs/current-plan.md` or `build-result.md` is written, `PostToolUse` invokes
`write_mao_gate_for_project()` from `post_tool_validate.py` to re-scan file handoffs
and emit `artifacts/mao/gate.json`.

`record_mao_todo_write_post_tool_observation()` (also from `post_tool_validate.py` on
`PostToolUse`) appends a reviewable line to `artifacts/mao/todo-write-events.jsonl` and
overwrites `artifacts/mao/last-todo-write-observation.json` when the tool is a todo write
(e.g. normalized `todo_write`). This is traceability only: no `TodoWrite`, no auto-spawn,
no parent decision bypass.

`capture_transition_decision()` appends to `artifacts/mao/transition-events.jsonl`, mirrors
supported `todo_mutations` on each event line, and overwrites gitignored
`artifacts/mao/suggested-todo-mutation.json` when the append succeeds (hook-assisted
unblock hint for the parent composer; not `TodoWrite` automation).

Opt-in PostToolUse (`CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE`): after a handoff write and
gate refresh, `maybe_hook_auto_capture_transition()` may call the same
`capture_transition_decision()` when the trusted positive gate is fresh and parent
mutations apply (deduped per transition + handoff mtimes; skipped when
`CURSOR_MAO_GATE=0`). `downstream-readiness.json` may use trigger
``hook_post_tool_use_auto_capture`` for those captures. Separate opt-in
`CURSOR_MAO_VERIFIER_AUTOSTART` may write gitignored
`artifacts/mao/verifier-autostart-intent.json` after a successful build→validate hook
capture; only the parent may spawn the verifier — the intent file does not schedule or
spawn agents — hooks never auto-start agents.

`write_mao_downstream_readiness_artifact()` overwrites gitignored
`artifacts/mao/downstream-readiness.json` after gate refresh or todo-write observation
with deterministic `unblock_semantic` per MAO edge (still no `TodoWrite`, no auto-spawn).

`evaluate_parent_downstream_readiness_advisory()` lets the parent read that artifact as
an optional hint: it always includes a **live** recompute, compares on-disk edges to
live for staleness, and sets `trusted_snapshot_for_hint` only when the artifact matches
live edge payloads (version + per-edge records). Missing, invalid, or divergent files
fall back to live-only guidance — never a substitute for explicit transition checks.

`evaluate_mao_parent_transition_bundle()` combines a single transition's
`evaluate_*_transition()` decision, `parent_owned_todo_mutations_for_transition()`,
the matching per-edge downstream readiness record (`unblock_semantic`), and
`interpret_unblock_semantic_for_parent()` so parents consume one structure instead of
recomposing helpers ad hoc. Optional embed of full downstream-readiness advisory.

After a successful `capture_transition_decision()` JSONL append, hooks may refresh
`downstream-readiness.json` with trigger ``transition_capture`` (fail-open; same
semantics as other DR writes — not auto-start).

`apply_parent_todo_mutations_to_cursor_todos()` maps those tag-prefix mutations onto a
Cursor todo list for parent-owned `TodoWrite merge`; hooks still never call `TodoWrite`.

Parent orchestrators can then use `read_parent_advisory_gate()` to consume that file
as advisory input and `evaluate_plan_to_build_transition()` /
`evaluate_build_to_validate_transition()` to make explicit parent-owned decisions from
canonical file handoffs. Each evaluation attaches an `advisory_pending` bundle: live
recompute from handoffs, optional on-disk snapshot, alignment, and deterministic
interpretation hints. The gate may also describe still-`pending` downstream MAO
work as `blocked` or `ready_for_parent_review`, but only the parent may advance
real Cursor todo state.

Files remain authoritative; the gate is a deterministic hint for orchestrators.
Disable with CURSOR_MAO_GATE=0 (or false/no/off).
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.request
import uuid
import sys
from datetime import datetime, timezone
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from artifact_contract import inspect_build_result_contract
from mao_worktree import collect_mao_worktree_metadata, mao_worktree_metadata_valid
from utils.mat_env_resolve import mat_env_flag, mat_env_get

GATE_VERSION = 2
GATE_REL = Path("artifacts") / "mao" / "gate.json"
TRANSITION_EVENT_VERSION = 1
TRANSITION_EVENTS_REL = Path("artifacts") / "mao" / "transition-events.jsonl"
SUGGESTED_TODO_MUTATION_REL = Path("artifacts") / "mao" / "suggested-todo-mutation.json"
SUGGESTED_MUTATION_FILE_VERSION = 1
TODO_WRITE_OBSERVATION_VERSION = 1
TODO_WRITE_EVENTS_REL = Path("artifacts") / "mao" / "todo-write-events.jsonl"
LAST_TODO_WRITE_OBSERVATION_REL = Path("artifacts") / "mao" / "last-todo-write-observation.json"
DOWNSTREAM_READINESS_VERSION = 1
DOWNSTREAM_READINESS_REL = Path("artifacts") / "mao" / "downstream-readiness.json"
VERIFIER_AUTOSTART_INTENT_REL = Path("artifacts") / "mao" / "verifier-autostart-intent.json"

# Downstream-readiness `trigger` values (including hook auto-capture)
DOWNSTREAM_TRIGGER_TRANSITION_CAPTURE = "transition_capture"
DOWNSTREAM_TRIGGER_HOOK_POST_TOOL_AUTO_CAPTURE = "hook_post_tool_use_auto_capture"

# unblock_semantic values (hook snapshot only; parent still owns TodoWrite / subagent starts)
UNBLOCK_SEMANTIC_BLOCKED = "downstream_blocked"
UNBLOCK_SEMANTIC_UNBLOCKED = "unblocked_for_parent_action"
UNBLOCK_SEMANTIC_MISALIGNED = "ready_canonical_files_advisory_misaligned"
UNBLOCK_SEMANTIC_UNCERTAIN = "transition_ready_uncertain_mutation_withheld"


def interpret_unblock_semantic_for_parent(semantic: str) -> dict:
    """
    Deterministic parent-facing text for one ``unblock_semantic`` string.

    This does not replace ``evaluate_*_transition()`` or canonical file checks; it
    explains how hook-written ``downstream-readiness.json`` edge labels relate to
    parent-owned ``TodoWrite`` and dispatch.
    """
    s = (semantic or "").strip()
    table = {
        UNBLOCK_SEMANTIC_BLOCKED: {
            "short_label": "blocked",
            "meaning": (
                "Canonical handoff checks for this edge are not satisfied "
                "(transition_ready is false). Downstream MAO todo stays pending; "
                "fix blockers in files before attempting transition capture or TodoWrite."
            ),
            "todo_mutations_expected": False,
            "parent_next": (
                "Repair handoffs (plan and/or build-result per edge); re-run explicit "
                "transition evaluation — do not apply helper todo_mutations."
            ),
        },
        UNBLOCK_SEMANTIC_UNBLOCKED: {
            "short_label": "unblocked_for_parent_action",
            "meaning": (
                "Transition is ready and ``parent_owned_todo_mutations_for_transition`` "
                "returns the supported tag map. Parent may apply TodoWrite merge after "
                "their explicit check, then dispatch the downstream subagent manually."
            ),
            "todo_mutations_expected": True,
            "parent_next": (
                "Run capture_transition_decision if auditing; validate todos; "
                "apply todo_mutations via apply_parent_todo_mutations_to_cursor_todos; "
                "then spawn builder or verifier — hooks never auto-start."
            ),
        },
        UNBLOCK_SEMANTIC_MISALIGNED: {
            "short_label": "advisory_misaligned",
            "meaning": (
                "Canonical files look transition-ready but gate_plus_files mode has "
                "on-disk advisory_pending disagreeing with live recompute. "
                "Helper mutations are withheld until gate refresh or manual review."
            ),
            "todo_mutations_expected": False,
            "parent_next": (
                "Re-save handoffs to refresh gate.json, or proceed with manual/file-only "
                "trust — do not apply helper todo_mutations until alignment is restored "
                "or you accept manual_file_check path semantics."
            ),
        },
        UNBLOCK_SEMANTIC_UNCERTAIN: {
            "short_label": "uncertain_mutation_withheld",
            "meaning": (
                "Transition reads ready but no helper mutation map applies "
                "(rare decision shape); treat as manual review before TodoWrite."
            ),
            "todo_mutations_expected": False,
            "parent_next": (
                "Inspect decision.decision_mode, advisory_pending, and "
                "todo_mutations_blocked_reasons; use explicit file checks only."
            ),
        },
    }
    if s in table:
        row = table[s]
        return {
            "semantic": s,
            "known": True,
            **row,
        }
    return {
        "semantic": s,
        "known": False,
        "short_label": "unknown",
        "meaning": (
            "Unrecognized unblock_semantic; ignore hook edge labels and use "
            "evaluate_mao_parent_transition_bundle() or evaluate_*_transition() live."
        ),
        "todo_mutations_expected": False,
        "parent_next": "Recompute from mao_gate helpers; refresh downstream-readiness artifact.",
    }


def evaluate_mao_parent_transition_bundle(
    repo_root: str | Path,
    transition: str,
    *,
    include_downstream_readiness_advisory: bool = False,
) -> dict:
    """
    Single parent-facing bundle for one MAO edge: decision, mutations, readiness edge,
    and semantic interpretation.

    Optional ``include_downstream_readiness_advisory`` adds the full-file advisory
    (live vs on-disk trust) for operators who want both edges in one call.
    """
    root = Path(repo_root).resolve()
    if transition == "plan_to_build":
        decision = evaluate_plan_to_build_transition(root)
        downstream_tag = "[mao:build]"
    elif transition == "build_to_validate":
        decision = evaluate_build_to_validate_transition(root)
        downstream_tag = "[mao:validate]"
    else:
        raise ValueError(f"unsupported transition: {transition}")

    mutations = parent_owned_todo_mutations_for_transition(decision)
    edge = _edge_downstream_readiness_record(decision, downstream_tag)
    semantic = str(edge.get("unblock_semantic") or "")
    blocked = _todo_mutations_blocked_reasons(decision, mutations)

    bundle: dict = {
        "transition": transition,
        "decision": decision,
        "todo_mutations": dict(mutations),
        "todo_mutations_blocked_reasons": blocked,
        "edge_readiness": edge,
        "unblock_semantic_interpretation": interpret_unblock_semantic_for_parent(semantic),
        "orchestration_flow_hint": _orchestration_flow_hint(decision, mutations, semantic),
    }
    if include_downstream_readiness_advisory:
        bundle["downstream_readiness_advisory"] = evaluate_parent_downstream_readiness_advisory(
            root
        )
    return bundle


def _orchestration_flow_hint(
    decision: dict, mutations: dict[str, str], unblock_semantic: str
) -> str:
    """One deterministic sentence tying transition outcome, semantic, and mutations."""
    ready = decision.get("transition_ready") is True
    mode = decision.get("decision_mode")
    if ready and mutations:
        return (
            f"MAO {decision.get('transition')}: transition_ready with decision_mode={mode!r}; "
            f"unblock_semantic={unblock_semantic!r}; apply todo_mutations after explicit "
            "parent check, then TodoWrite merge — no auto-start."
        )
    if ready and not mutations:
        return (
            f"MAO {decision.get('transition')}: transition_ready but helper todo_mutations "
            f"withheld (unblock_semantic={unblock_semantic!r}); see "
            "todo_mutations_blocked_reasons and advisory_pending before TodoWrite."
        )
    return (
        f"MAO {decision.get('transition')}: not transition_ready "
        f"(unblock_semantic={unblock_semantic!r}); repair canonical handoffs before "
        "capture or todo updates."
    )
PLAN_REL = Path("docs") / "current-plan.md"
BUILD_REL = Path("build-result.md")
TRANSITION_TODO_MUTATIONS = {
    "plan_to_build": {
        "[mao:plan]": "completed",
        "[mao:build]": "in_progress",
    },
    "build_to_validate": {
        "[mao:build]": "completed",
        "[mao:validate]": "in_progress",
    },
}

# Longest tag first so `[mao:validate]` wins over any shared-prefix mistake (none today).
_MAO_TODO_TAG_PREFIX_ORDER = ("[mao:validate]", "[mao:build]", "[mao:plan]")


def _mao_tag_prefix_for_todo_content(content: str) -> str | None:
    c = (content or "").strip()
    if not c:
        return None
    for tag in _MAO_TODO_TAG_PREFIX_ORDER:
        if c.startswith(tag):
            return tag
    return None


def apply_parent_todo_mutations_to_cursor_todos(
    todos: list[dict], mutations: dict[str, str]
) -> list[dict]:
    """
    Apply parent-owned MAO status mutations to a Cursor-style todo list for TodoWrite merge.

    Each todo dict should include at least ``content`` and ``status``; ``id`` and other
    keys are preserved. Matching is by MAO tag prefix at the start of ``content`` (the
    protocol allows an optional human suffix after the canonical line).

    Unknown todos are returned unchanged. Tags present in ``mutations`` but missing from
    ``todos`` are ignored here; use ``validate_mao_todo_mutations_against_todos`` first
    if the parent wants a hard check before calling TodoWrite.
    """
    if not mutations:
        return [dict(t) for t in todos]

    out: list[dict] = []
    for raw in todos:
        t = dict(raw)
        tag = _mao_tag_prefix_for_todo_content(str(t.get("content") or ""))
        if tag is not None and tag in mutations:
            t["status"] = mutations[tag]
        out.append(t)
    return out


def validate_mao_todo_mutations_against_todos(
    todos: list[dict], mutations: dict[str, str]
) -> tuple[bool, list[str]]:
    """
    Return (ok, reasons). When ``mutations`` is empty, returns (True, []).

    For non-empty ``mutations``, each tag key must match exactly one todo ``content``
    prefix; duplicate matches or missing todos yield ok=False with deterministic reasons.
    """
    if not mutations:
        return True, []

    matched: dict[str, int] = {tag: 0 for tag in mutations}
    for raw in todos:
        tag = _mao_tag_prefix_for_todo_content(str(raw.get("content") or ""))
        if tag is not None and tag in matched:
            matched[tag] += 1

    reasons: list[str] = []
    for tag, count in matched.items():
        if count == 0:
            reasons.append(f"missing_todo_for_mutation_tag:{tag}")
        elif count > 1:
            reasons.append(f"ambiguous_todo_for_mutation_tag:{tag}")
    return (len(reasons) == 0, reasons)


PLAN_PLACEHOLDER_PHRASE = "_No active orchestration plan._"
BUILD_PLACEHOLDER_PHRASE = "_No active build result._"
PENDING_TODO_STATUS = "pending"
ADVISORY_STATE_BLOCKED = "blocked"
ADVISORY_STATE_READY = "ready_for_parent_review"


def _mat_env_enabled_by_default(key: str, *, root: Path | None = None) -> bool:
    v = (mat_env_get(key, default="1", root=root) or "1").strip().lower()
    return v not in {"0", "false", "no", "off"}


def mao_gate_enabled() -> bool:
    return _mat_env_enabled_by_default("CURSOR_MAO_GATE")


def mao_todo_post_tool_use_enabled() -> bool:
    """Record MAO todo-write observations from PostToolUse (fail-open; disable with 0/false/no/off)."""
    return _mat_env_enabled_by_default("CURSOR_MAO_TODO_POST_TOOL_USE")


def mao_downstream_readiness_enabled() -> bool:
    """Persist downstream-readiness.json (fail-open; disable with 0/false/no/off)."""
    return _mat_env_enabled_by_default("CURSOR_MAO_DOWNSTREAM_READINESS")


def mao_hook_auto_transition_capture_enabled() -> bool:
    """
    Opt-in PostToolUse hook path that may call capture_transition_decision after
    handoff writes. Requires CURSOR_MAO_GATE on and a trusted positive gate
    (see maybe_hook_auto_capture_transition).
    """
    return mat_env_flag("CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE", default=False)


def mao_emit_transition_observability_enabled() -> bool:
    """
    Opt-in: when hook auto-capture calls capture_transition_decision(), also POST
    MaoTransition to the observability API (fail-open). Does not call TodoWrite
    or spawn agents.
    """
    return mat_env_flag("CURSOR_MAO_EMIT_TRANSITION_OBSERVABILITY", default=False)


def mao_emit_todo_observation_observability_enabled() -> bool:
    """
    Opt-in: after record_mao_todo_write_post_tool_observation() persists locally, also POST
    MaoTodoObservation to the observability API (fail-open). Same parsed payload as local
    observation — not Cursor's internal todo list; may be absent when todos change.
    """
    return mat_env_flag("CURSOR_MAO_EMIT_TODO_OBSERVATION_OBSERVABILITY", default=False)


def mao_verifier_autostart_enabled() -> bool:
    """Opt-in verifier dispatch intent artifact (parent-owned spawn only)."""
    return mat_env_flag("CURSOR_MAO_VERIFIER_AUTOSTART", default=False)


def mao_verifier_autostart_require_todo_observation() -> bool:
    """When set, verifier intent requires last todo-write observation parse_quality ok."""
    return mat_env_flag("CURSOR_MAO_VERIFIER_AUTOSTART_REQUIRE_TODO_OBSERVATION", default=False)


def _normalize_post_tool_use_tool_name(tool_name: str) -> str:
    """Match post_tool_validate.normalize_tool_name for todo / write tool detection."""
    if not isinstance(tool_name, str):
        return ""
    stripped = tool_name.strip()
    if not stripped:
        return ""
    lowered = stripped.replace("-", "_").replace(" ", "_")
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", lowered).lower()
    return snake


def is_mao_todo_write_tool(tool_name: str) -> bool:
    """True when PostToolUse names Cursor's todo write tool (e.g. TodoWrite -> todo_write)."""
    return _normalize_post_tool_use_tool_name(tool_name) == "todo_write"


def _coerce_post_tool_use_tool_input_dict(payload: dict) -> dict:
    raw = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return raw if isinstance(raw, dict) else {}


def _normalize_cursor_todo_status(raw: object) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    upper = s.upper().replace(" ", "_")
    upper_map = {
        "PENDING": "pending",
        "IN_PROGRESS": "in_progress",
        "COMPLETED": "completed",
        "CANCELLED": "cancelled",
        "CANCELED": "cancelled",
    }
    if upper in upper_map:
        return upper_map[upper]
    low = s.lower()
    low_map = {
        "pending": "pending",
        "in_progress": "in_progress",
        "inprogress": "in_progress",
        "completed": "completed",
        "complete": "completed",
        "cancelled": "cancelled",
        "canceled": "cancelled",
    }
    return low_map.get(low)


def interpret_mao_todo_write_from_post_tool_payload(payload: dict) -> dict:
    """
    Parse PostToolUse payload for MAO-tagged todo rows (advisory interpretation only).

    Returns keys: merge, todos_count, mao_rows, parse_quality, parse_notes.
    parse_quality: ok | no_mao_tags | empty_todos | invalid_input | ambiguous_duplicate_tags | partial
    """
    tool_input = _coerce_post_tool_use_tool_input_dict(payload)
    merge = tool_input.get("merge")
    if merge is not None and not isinstance(merge, bool):
        merge = None

    todos = tool_input.get("todos")
    if not isinstance(todos, list):
        return {
            "merge": merge,
            "todos_count": 0,
            "mao_rows": [],
            "parse_quality": "invalid_input",
            "parse_notes": ["todos_not_a_list_or_missing"],
        }
    if len(todos) == 0:
        return {
            "merge": merge,
            "todos_count": 0,
            "mao_rows": [],
            "parse_quality": "empty_todos",
            "parse_notes": [],
        }

    mao_rows: list[dict[str, str]] = []
    parse_notes: list[str] = []
    seen_tags: set[str] = set()
    dup = False

    for i, raw in enumerate(todos):
        if not isinstance(raw, dict):
            parse_notes.append(f"todo_index_{i}_not_object")
            continue
        content = raw.get("content")
        if content is None and raw.get("title") is not None:
            content = raw.get("title")
        tag = _mao_tag_prefix_for_todo_content(str(content or ""))
        if tag is None:
            continue
        status = _normalize_cursor_todo_status(raw.get("status"))
        if status is None:
            parse_notes.append(f"mao_tag_{tag}_unknown_status")
            continue
        if tag in seen_tags:
            parse_notes.append(f"duplicate_mao_tag:{tag}")
            dup = True
            continue
        seen_tags.add(tag)
        mao_rows.append({"tag": tag, "status": status})

    if dup:
        pq = "ambiguous_duplicate_tags"
    elif not mao_rows:
        pq = "no_mao_tags"
    elif parse_notes:
        pq = "partial"
    else:
        pq = "ok"

    return {
        "merge": merge,
        "todos_count": len(todos),
        "mao_rows": mao_rows,
        "parse_quality": pq,
        "parse_notes": parse_notes,
    }


def touches_build_result(changed_paths: list[str]) -> bool:
    for raw in changed_paths:
        if not raw or not isinstance(raw, str):
            continue
        norm = raw.replace("\\", "/")
        if norm.endswith("build-result.md") or norm.endswith("/mat-build-result.md"):
            return True
        if os.path.basename(norm) == "build-result.md":
            return True
    return False


def touches_current_plan(changed_paths: list[str]) -> bool:
    for raw in changed_paths:
        if not raw or not isinstance(raw, str):
            continue
        norm = raw.replace("\\", "/")
        if norm.endswith("docs/current-plan.md") or norm.endswith("/docs/current-plan.md"):
            return True
        if norm == "current-plan.md":
            return True
    return False


def _read_text(path: Path) -> tuple[str | None, float | None]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        mtime = path.stat().st_mtime
        return text, mtime
    except OSError:
        return None, None


def _plan_ready(text: str | None, reasons: list[str]) -> bool:
    if text is None:
        reasons.append("current_plan_missing")
        return False
    stripped = text.strip()
    if len(stripped) < 80:
        reasons.append("current_plan_too_short")
        return False
    if PLAN_PLACEHOLDER_PHRASE in stripped:
        reasons.append("current_plan_placeholder")
        return False
    return True


def _build_status_acceptable(text: str | None, reasons: list[str]) -> bool:
    if text is None:
        reasons.append("build_result_missing")
        return False
    if BUILD_PLACEHOLDER_PHRASE in text:
        reasons.append("build_result_placeholder")
        return False
    contract = inspect_build_result_contract(text)
    structural_invalid = _has_contract_structural_issues(contract)
    if structural_invalid:
        reasons.append("build_contract_invalid")
    if contract.status == "FAIL":
        reasons.append("build_status_fail")
        return False
    if structural_invalid:
        return False
    if contract.status in {"PASS", "PARTIAL"}:
        return True
    reasons.append("build_status_not_pass_or_partial")
    return False


def _has_contract_structural_issues(contract) -> bool:
    ignored_codes = {
        "status_value",
        "acceptance_criteria_format",
        "linting_type_check_value",
    }
    return any(issue.code not in ignored_codes for issue in contract.issues)


def _acceptance_criteria_ready(text: str | None, reasons: list[str]) -> bool:
    if text is None:
        if "build_result_missing" not in reasons:
            reasons.append("build_result_missing")
        return False

    contract = inspect_build_result_contract(text)
    issue_codes = {issue.code for issue in contract.issues}
    if "acceptance_criteria" in issue_codes:
        reasons.append("build_acceptance_section_missing")
        return False
    if "acceptance_criteria_format" in issue_codes:
        reasons.append("build_acceptance_criterion_unresolved")
        return False
    if not contract.acceptance_outcomes:
        reasons.append("build_acceptance_criteria_missing")
        return False
    if any(outcome == "FAIL" for outcome in contract.acceptance_outcomes):
        reasons.append("build_acceptance_criterion_fail")
        return False

    return True


def _lint_section_passed(text: str | None, reasons: list[str]) -> bool:
    if text is None:
        if "build_result_missing" not in reasons:
            reasons.append("build_result_missing")
        return False

    contract = inspect_build_result_contract(text)
    issue_codes = {issue.code for issue in contract.issues}
    if "linting_type_check" in issue_codes:
        reasons.append("build_lint_section_missing")
        return False
    if contract.lint_status == "PASS":
        return True

    reasons.append("build_lint_not_pass")
    return False


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    return deduped


def _pending_advisory_state(
    *,
    transition: str,
    primary_artifact: str,
    transition_ready: bool,
    blockers: list[str],
    ready_action: str,
    blocked_action: str,
) -> dict[str, object]:
    return {
        "todo_status": PENDING_TODO_STATUS,
        "advisory_state": (
            ADVISORY_STATE_READY if transition_ready else ADVISORY_STATE_BLOCKED
        ),
        "recommended_parent_action": ready_action if transition_ready else blocked_action,
        "transition": transition,
        "primary_artifact": primary_artifact,
        "blockers": [] if transition_ready else _dedupe_reasons(blockers),
    }


def _first_declared_build_status(text: str) -> str | None:
    status = inspect_build_result_contract(text).status
    if status is None:
        return None
    return status.lower()


def _explicit_status_fail(text: str) -> bool:
    return _first_declared_build_status(text) == "fail"


def _explicit_status_pass_or_partial(text: str) -> bool:
    return _first_declared_build_status(text) in {"pass", "partial"}


def evaluate_mao_gate(repo_root: Path) -> dict:
    """Return gate dict (not yet written)."""
    plan_path = repo_root / PLAN_REL
    build_path = repo_root / BUILD_REL

    plan_text, plan_mtime = _read_text(plan_path)
    build_text, build_mtime = _read_text(build_path)

    plan_present = plan_text is not None
    build_pending_blockers: list[str] = []
    plan_ok = _plan_ready(plan_text, build_pending_blockers)

    build_present = build_text is not None
    validate_pending_blockers = list(build_pending_blockers)
    build_ok = _build_status_acceptable(build_text, validate_pending_blockers)
    acceptance_ok = _acceptance_criteria_ready(build_text, validate_pending_blockers)
    lint_ok = _lint_section_passed(build_text, validate_pending_blockers)

    build_may_start = plan_ok
    validate_may_start = plan_ok and build_ok and acceptance_ok and lint_ok
    reasons = _dedupe_reasons(validate_pending_blockers)

    return {
        "version": GATE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "build_may_start": build_may_start,
        "validate_may_start": validate_may_start,
        "checks": {
            "plan_artifact_present": plan_present,
            "plan_ready": plan_ok,
            "build_artifact_present": build_present,
            "build_status_acceptable": build_ok,
            "acceptance_criteria_ready": acceptance_ok,
            "lint_passed": lint_ok,
        },
        "advisory_pending": {
            "[mao:build]": _pending_advisory_state(
                transition="plan_to_build",
                primary_artifact=str(PLAN_REL).replace("\\", "/"),
                transition_ready=build_may_start,
                blockers=build_pending_blockers,
                ready_action="review_plan_to_build",
                blocked_action="wait_for_plan_handoff",
            ),
            "[mao:validate]": _pending_advisory_state(
                transition="build_to_validate",
                primary_artifact=str(BUILD_REL).replace("\\", "/"),
                transition_ready=validate_may_start,
                blockers=validate_pending_blockers,
                ready_action="review_build_to_validate",
                blocked_action="wait_for_build_handoff",
            ),
        },
        "reasons": reasons,
        "inputs": {
            "plan_path": str(PLAN_REL).replace("\\", "/"),
            "build_path": str(BUILD_REL).replace("\\", "/"),
            "plan_mtime_epoch": plan_mtime,
            "build_mtime_epoch": build_mtime,
        },
        "mao_worktree": collect_mao_worktree_metadata(repo_root),
    }


def write_mao_gate_for_project(project_dir: str) -> Path | None:
    """Evaluate MAO handoffs and write gate.json under the repo root."""
    if not mao_gate_enabled():
        return None
    root = Path(project_dir).resolve()
    data = evaluate_mao_gate(root)
    out = root / GATE_REL
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        write_mao_downstream_readiness_artifact(root, trigger="handoff_gate_refresh")
        return out
    except OSError:
        return None


def _read_last_todo_write_observation_dict(repo_root: Path) -> dict | None:
    path = repo_root / LAST_TODO_WRITE_OBSERVATION_REL
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _todo_write_cross_check(repo_root: Path, live_gate: dict) -> dict:
    """
    Compare last todo-write observation file_handoff_signals to live evaluate_mao_gate.

    Missing, unreadable, or mismatched data is advisory only; it does not change
    unblock_semantic on the edge records.
    """
    obs = _read_last_todo_write_observation_dict(repo_root)
    if obs is None:
        return {
            "observation_present": False,
            "note": "No readable last-todo-write-observation.json",
        }
    fhs = obs.get("file_handoff_signals")
    live_bm = live_gate.get("build_may_start")
    live_vm = live_gate.get("validate_may_start")
    signals_match: bool | None = None
    if isinstance(fhs, dict) and "build_may_start" in fhs and "validate_may_start" in fhs:
        signals_match = fhs.get("build_may_start") == live_bm and fhs.get(
            "validate_may_start"
        ) == live_vm
    return {
        "observation_present": True,
        "observed_at": obs.get("observed_at"),
        "parse_quality": obs.get("parse_quality"),
        "file_handoff_signals_match_live_gate": signals_match,
        "note": (
            "Advisory cross-check only; stale or partial todo payloads do not override "
            "canonical files or edge unblock_semantic."
        ),
    }


def _edge_downstream_readiness_record(decision: dict, downstream_tag: str) -> dict:
    """One MAO edge: canonical transition + helper mutation applicability -> unblock_semantic."""
    mutations = parent_owned_todo_mutations_for_transition(decision)
    ready = decision.get("transition_ready") is True
    applicable = bool(mutations)
    mode = decision.get("decision_mode")
    bundle = decision.get("advisory_pending") or {}
    aligned = bundle.get("aligned_with_live")
    live_ap = bundle.get("live") or {}
    focus_live = live_ap.get(downstream_tag) if isinstance(live_ap, dict) else None
    if not isinstance(focus_live, dict):
        focus_live = {}
    advisory_state = focus_live.get("advisory_state")

    if not ready:
        semantic = UNBLOCK_SEMANTIC_BLOCKED
    elif applicable:
        semantic = UNBLOCK_SEMANTIC_UNBLOCKED
    elif mode == "gate_plus_files" and aligned is False:
        semantic = UNBLOCK_SEMANTIC_MISALIGNED
    else:
        semantic = UNBLOCK_SEMANTIC_UNCERTAIN

    return {
        "transition": decision.get("transition"),
        "downstream_tag": downstream_tag,
        "transition_ready": ready,
        "decision_mode": mode,
        "advisory_aligned_with_live": aligned,
        "live_advisory_state": advisory_state,
        "helper_todo_mutation_applicable": applicable,
        "unblock_semantic": semantic,
        "next_step": decision.get("next_step"),
    }


def compute_mao_downstream_readiness(repo_root: Path, *, trigger: str) -> dict:
    """
    Deterministic snapshot of downstream MAO unblock/readiness (advisory only).

    Uses the same transition and mutation rules as parent-owned helpers; does not
    call TodoWrite or spawn agents.
    """
    root = Path(repo_root).resolve()
    live_gate = evaluate_mao_gate(root)
    d_plan = evaluate_plan_to_build_transition(root)
    d_build = evaluate_build_to_validate_transition(root)
    return {
        "version": DOWNSTREAM_READINESS_VERSION,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "mao_worktree": collect_mao_worktree_metadata(root),
        "parent_owned_note": (
            "Hooks record this snapshot only. The parent must still run explicit "
            "transition checks, apply TodoWrite, and dispatch subagents manually. "
            "File handoffs remain canonical."
        ),
        "plan_to_build": _edge_downstream_readiness_record(d_plan, "[mao:build]"),
        "build_to_validate": _edge_downstream_readiness_record(d_build, "[mao:validate]"),
        "todo_write_cross_check": _todo_write_cross_check(root, live_gate),
        "live_gate_signals": {
            "build_may_start": live_gate.get("build_may_start"),
            "validate_may_start": live_gate.get("validate_may_start"),
            "gate_generated_at": live_gate.get("generated_at"),
        },
    }


def write_mao_downstream_readiness_artifact(
    project_dir: str | Path, *, trigger: str
) -> Path | None:
    """Write gitignored downstream-readiness.json (fail-open)."""
    if not mao_downstream_readiness_enabled():
        return None
    root = Path(project_dir).resolve()
    data = compute_mao_downstream_readiness(root, trigger=trigger)
    out = root / DOWNSTREAM_READINESS_REL
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return out
    except OSError:
        return None


def _downstream_readiness_edges_payload(snap: object) -> dict | None:
    """Return version + edge dicts for equality checks (volatile top-level fields ignored)."""
    if not isinstance(snap, dict):
        return None
    p = snap.get("plan_to_build")
    b = snap.get("build_to_validate")
    if not isinstance(p, dict) or not isinstance(b, dict):
        return None
    return {
        "version": snap.get("version"),
        "plan_to_build": p,
        "build_to_validate": b,
    }


def _interpret_parent_downstream_readiness_advisory(
    *,
    trusted: bool,
    live: dict,
    reasons: list[str],
    dr_enabled: bool,
) -> str:
    """Single deterministic sentence for parent-facing orchestration summaries."""
    if not dr_enabled:
        return (
            "Downstream readiness snapshots are disabled (CURSOR_MAO_DOWNSTREAM_READINESS); "
            "use live_snapshot in this bundle for current edge semantics only — advisory, "
            "never a substitute for explicit handoff checks."
        )
    if trusted:
        return (
            "On-disk downstream-readiness.json matches live edge semantics (version + "
            "plan_to_build/mat-build_to_validate); unblock_semantic is a trustworthy advisory "
            "hint only — still run explicit transition checks before TodoWrite or dispatch."
        )
    if "artifact_missing" in reasons:
        return (
            "No downstream-readiness.json on disk; use live_snapshot here and refresh "
            "via handoff or todo PostToolUse hooks when you want a persisted hint file."
        )
    if "artifact_unreadable_or_invalid_json" in reasons or "artifact_shape_invalid" in reasons:
        return (
            "Downstream readiness artifact is unreadable or malformed; ignore the file and "
            "use live_snapshot only until hooks rewrite a valid snapshot."
        )
    if "artifact_version_mismatch" in reasons:
        return (
            "Downstream readiness artifact version does not match this mao_gate build; "
            "ignore file semantics and use live_snapshot only."
        )
    if "artifact_stale_or_divergent_from_live_edges" in reasons:
        return (
            "Downstream readiness artifact is stale vs live handoffs; prefer live_snapshot "
            "unblock_semantic or refresh the file — do not treat the on-disk copy as current."
        )
    p = live.get("plan_to_build") if isinstance(live.get("plan_to_build"), dict) else {}
    b = live.get("build_to_validate") if isinstance(live.get("build_to_validate"), dict) else {}
    ps = p.get("unblock_semantic")
    bs = b.get("unblock_semantic")
    return (
        f"Live edge hints: plan_to_build={ps!r}, build_to_validate={bs!r} "
        "(advisory only; explicit file checks remain authoritative)."
    )


def evaluate_parent_downstream_readiness_advisory(project_dir: str | Path) -> dict:
    """
    Parent consumption helper for artifacts/mao/downstream-readiness.json.

    Always includes a fresh live_snapshot (same rules as hook-written file). The on-disk
    artifact is trusted for advisory hints only when version and edge payloads match live;
    otherwise fall back to live_snapshot and reasons. Never replaces canonical handoffs
    or parent-owned transition checks; does not call TodoWrite or spawn agents.
    """
    root = Path(project_dir).resolve()
    reasons: list[str] = []
    dr_enabled = mao_downstream_readiness_enabled()

    live = compute_mao_downstream_readiness(
        root, trigger="live_parent_downstream_readiness_advisory"
    )
    live_edges = _downstream_readiness_edges_payload(live)

    path = root / DOWNSTREAM_READINESS_REL
    from_artifact: dict | None = None
    shape_ok = False
    version_ok = False
    aligned: bool | None = None

    if not dr_enabled:
        reasons.append("downstream_readiness_disabled")

    if not path.is_file():
        if dr_enabled:
            reasons.append("artifact_missing")
    else:
        try:
            raw = path.read_text(encoding="utf-8")
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                from_artifact = parsed
            else:
                from_artifact = None
                reasons.append("artifact_shape_invalid")
        except (OSError, json.JSONDecodeError):
            from_artifact = None
            reasons.append("artifact_unreadable_or_invalid_json")

    if from_artifact is not None:
        if from_artifact.get("version") == DOWNSTREAM_READINESS_VERSION:
            version_ok = True
        else:
            reasons.append("artifact_version_mismatch")
        art_edges = _downstream_readiness_edges_payload(from_artifact)
        if art_edges is None:
            reasons.append("artifact_shape_invalid")
        else:
            shape_ok = True
            if version_ok and live_edges is not None:
                aligned = art_edges == live_edges
                if not aligned:
                    reasons.append("artifact_stale_or_divergent_from_live_edges")

    trusted = bool(
        dr_enabled
        and from_artifact is not None
        and shape_ok
        and version_ok
        and aligned is True
    )

    interpretation = _interpret_parent_downstream_readiness_advisory(
        trusted=trusted,
        live=live,
        reasons=reasons,
        dr_enabled=dr_enabled,
    )

    try:
        rel_path = path.relative_to(root)
    except ValueError:
        rel_path = path

    return {
        "downstream_readiness_enabled": dr_enabled,
        "artifact_path": str(rel_path).replace("\\", "/"),
        "artifact_present": path.is_file(),
        "artifact_shape_ok": shape_ok,
        "artifact_version_ok": version_ok,
        "artifact_aligned_with_live_edges": aligned,
        "trusted_snapshot_for_hint": trusted,
        "reasons": reasons,
        "from_artifact": from_artifact,
        "live_snapshot": live,
        "interpretation": interpretation,
    }


def record_mao_todo_write_post_tool_observation(
    project_dir: str | Path, payload: dict
) -> dict | None:
    """
    On PostToolUse after a todo-write tool call, record MAO interpretation (fail-open).

    Appends one JSON line to todo-write-events.jsonl and overwrites
    last-todo-write-observation.json. Does not call TodoWrite, spawn agents, or replace
    file handoffs. Optional CURSOR_MAO_TODO_POST_TOOL_REFRESH_GATE=1 refreshes gate.json
    after recording when CURSOR_MAO_GATE is enabled.
    Optional CURSOR_MAO_EMIT_TODO_OBSERVATION_OBSERVABILITY=1 POSTs MaoTodoObservation
    (fail-open). Returned dict includes observability_emitted when local write succeeded.
    """
    if not mao_todo_post_tool_use_enabled():
        return None
    tool_raw = payload.get("tool_name") or payload.get("tool") or ""
    if not is_mao_todo_write_tool(str(tool_raw)):
        return None

    root = Path(project_dir).resolve()
    interp = interpret_mao_todo_write_from_post_tool_payload(payload)
    event: dict[str, object] = {
        "event_version": TODO_WRITE_OBSERVATION_VERSION,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "tool_name_raw": str(tool_raw).strip(),
        "tool_name_normalized": _normalize_post_tool_use_tool_name(str(tool_raw)),
        **interp,
        "mao_worktree": collect_mao_worktree_metadata(root),
    }

    if mao_gate_enabled():
        ev = evaluate_mao_gate(root)
        event["file_handoff_signals"] = {
            "build_may_start": ev.get("build_may_start"),
            "validate_may_start": ev.get("validate_may_start"),
            "gate_generated_at": ev.get("generated_at"),
        }
    else:
        event["file_handoff_signals"] = {"skipped": "CURSOR_MAO_GATE disabled"}

    refresh = mat_env_flag("CURSOR_MAO_TODO_POST_TOOL_REFRESH_GATE", default=False, root=root)
    refreshed = False
    if refresh and mao_gate_enabled():
        try:
            refreshed = write_mao_gate_for_project(str(root)) is not None
        except Exception:  # noqa: BLE001 — never block the hook
            refreshed = False
    event["gate_refreshed_after_observation"] = refreshed

    jsonl_path = root / TODO_WRITE_EVENTS_REL
    snap_path = root / LAST_TODO_WRITE_OBSERVATION_REL
    line = json.dumps(event, ensure_ascii=False) + "\n"
    try:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
        snap_path.write_text(json.dumps(event, indent=2) + "\n", encoding="utf-8")
    except OSError:
        return None
    write_mao_downstream_readiness_artifact(root, trigger="todo_write_post_tool_use")
    observability_emitted = False
    if mao_emit_todo_observation_observability_enabled():
        try:
            observability_emitted = _emit_mao_todo_observation_to_observability(root, event)
        except Exception:  # noqa: BLE001 — never block the hook
            observability_emitted = False
    out = dict(event)
    out["observability_emitted"] = observability_emitted
    return out


def _extract_session_id_from_env() -> str:
    for key in ("CURSOR_SESSION_ID", "CURSOR_TRACE_ID", "SESSION_ID"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return "unknown"


def _transition_related_files(repo_root: Path, transition: str) -> list[dict]:
    rels = [PLAN_REL]
    if transition == "build_to_validate":
        rels.append(BUILD_REL)

    files: list[dict] = []
    for rel in rels:
        path = repo_root / rel
        exists = path.is_file()
        try:
            mtime = path.stat().st_mtime if exists else None
        except OSError:
            mtime = None
        files.append(
            {
                "path": str(rel).replace("\\", "/"),
                "exists": exists,
                "mtime_epoch": mtime,
            }
        )
    return files


def _observability_api_events_url(repo_root: Path) -> str:
    explicit = (mat_env_get("OBSERVABILITY_API_EVENTS_URL", default="", root=repo_root) or "").strip()
    if explicit:
        return explicit

    base = (
        mat_env_get("OBSERVABILITY_SERVER_URL", default="http://localhost:3001/events", root=repo_root)
        or "http://localhost:3001/events"
    ).strip()
    if base.endswith("/events"):
        return f"{base[:-len('/events')]}/api/events"
    return f"{base.rstrip('/')}/api/events"


def _todo_mutations_blocked_reasons(decision: dict, mutations: dict[str, str]) -> list[str]:
    """Deterministic reasons when `parent_owned_todo_mutations_for_transition` returns {}."""
    if mutations:
        return []
    if decision.get("transition_ready") is not True:
        return _dedupe_reasons(list(decision.get("reasons") or ["transition_not_ready"]))
    if decision.get("decision_mode") == "gate_plus_files":
        bundle = decision.get("advisory_pending") or {}
        if bundle.get("aligned_with_live") is False:
            return [
                "advisory_pending_misaligned_refresh_gate_or_manual_review_before_todo_mutation",
            ]
    return ["no_helper_mutation_for_decision_shape"]


def _build_transition_event(
    repo_root: Path, decision: dict, todo_mutations: dict[str, str]
) -> dict:
    captured_at = datetime.now(timezone.utc)
    gate = decision.get("gate") or {"usable": False, "reason": "gate_unavailable", "gate": None}
    blocked_reasons = _todo_mutations_blocked_reasons(decision, todo_mutations)
    return {
        "version": TRANSITION_EVENT_VERSION,
        "event_id": f"mao-transition-{uuid.uuid4()}",
        "captured_at": captured_at.isoformat(),
        "timestamp_ms": int(captured_at.timestamp() * 1000),
        "session_id": _extract_session_id_from_env(),
        "transition": decision["transition"],
        "allowed": bool(decision["transition_ready"]),
        "decision_owner": decision["decision_owner"],
        "decision_mode": decision["decision_mode"],
        "trigger_rule": decision["trigger_rule"],
        "next_step": decision["next_step"],
        "reasons": list(decision.get("reasons") or []),
        "manual_checks": dict(decision.get("manual_checks") or {}),
        "todo_mutations": dict(todo_mutations),
        "todo_mutations_applicable": bool(todo_mutations),
        "todo_mutations_blocked_reasons": blocked_reasons,
        "advisory": {
            "source": "artifacts/mao/gate.json",
            "usable": bool(gate.get("usable")),
            "reason": gate.get("reason", "gate_unavailable"),
            "gate": gate.get("gate"),
        },
        "files": _transition_related_files(repo_root, decision["transition"]),
        "advisory_pending": decision.get("advisory_pending"),
        "mao_worktree": collect_mao_worktree_metadata(repo_root),
        "capture": {
            "artifact_path": str(TRANSITION_EVENTS_REL).replace("\\", "/"),
            "suggested_todo_mutation_path": str(SUGGESTED_TODO_MUTATION_REL).replace("\\", "/"),
            "mode": "append_only_jsonl",
            "observability": {
                "enabled": False,
                "status": "not_requested",
                "event_type": "MaoTransition",
            },
        },
    }


def _append_transition_event(repo_root: Path, event: dict) -> Path | None:
    out = repo_root / TRANSITION_EVENTS_REL
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")
        return out
    except OSError:
        return None


def _last_transition_event_for(
    repo_root: Path, transition: str
) -> dict | None:
    path = repo_root / TRANSITION_EVENTS_REL
    if not path.is_file():
        return None
    try:
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return None
    for line in reversed(lines):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(ev, dict) and ev.get("transition") == transition:
            return ev
    return None


def _hook_transition_files_fingerprint_match(a: object, b: object) -> bool:
    if not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if not isinstance(x, dict) or not isinstance(y, dict):
            return False
        if x.get("path") != y.get("path"):
            return False
        if x.get("exists") != y.get("exists"):
            return False
        m1, m2 = x.get("mtime_epoch"), y.get("mtime_epoch")
        if m1 is None and m2 is None:
            continue
        if m1 is None or m2 is None:
            return False
        try:
            if abs(float(m1) - float(m2)) > 1e-6:
                return False
        except (TypeError, ValueError):
            return False
    return True


def _hook_auto_capture_should_dedupe(
    repo_root: Path, transition: str, current_files: list[dict]
) -> bool:
    prev = _last_transition_event_for(repo_root, transition)
    if prev is None:
        return False
    return _hook_transition_files_fingerprint_match(prev.get("files"), current_files)


def _trusted_gate_ok_for_hook_auto_capture(repo_root: Path, transition: str) -> bool:
    gate_advisory = read_parent_advisory_gate(repo_root, transition=transition)
    if not gate_advisory.get("usable"):
        return False
    gate = gate_advisory.get("gate")
    if not isinstance(gate, dict):
        return False
    require_build = transition == "build_to_validate"
    return gate_is_fresh_on_disk(repo_root, gate, require_build=require_build)


def maybe_hook_auto_capture_transition(
    project_dir: str | Path, changed_files: list[str]
) -> dict:
    """
    PostToolUse hook helper: optionally capture transition decisions when a write
    touches MAO handoffs. Fail-open; never calls TodoWrite.

    Requires CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE, CURSOR_MAO_GATE enabled,
    trusted positive fresh gate.json for the edge, passing transition evaluation,
    non-empty parent todo_mutations, and advisory alignment when in gate_plus_files
    mode. Dedupes against the last JSONL event for the same transition and file mtimes.
    """
    root = Path(project_dir).resolve()
    out: dict = {
        "captures": {},
        "skipped_reasons": [],
        "build_to_validate_hook_capture_succeeded": False,
    }
    if not mao_hook_auto_transition_capture_enabled():
        out["skipped_reasons"].append("hook_auto_transition_capture_disabled")
        return out
    if not mao_gate_enabled():
        out["skipped_reasons"].append("CURSOR_MAO_GATE_disabled_no_hook_auto_capture")
        return out

    def _attempt(transition: str) -> dict | None:
        if transition == "plan_to_build":
            if not touches_current_plan(changed_files):
                return None
        elif transition == "build_to_validate":
            if not touches_build_result(changed_files):
                return None
        else:
            return None

        if not _trusted_gate_ok_for_hook_auto_capture(root, transition):
            out["skipped_reasons"].append(
                f"{transition}:trusted_positive_fresh_gate_required"
            )
            return None

        if transition == "plan_to_build":
            decision = evaluate_plan_to_build_transition(root)
        else:
            decision = evaluate_build_to_validate_transition(root)

        current_snap = _transition_related_files(root, transition)
        if _hook_auto_capture_should_dedupe(root, transition, current_snap):
            out["skipped_reasons"].append(f"{transition}:deduped_same_handoff_mtimes")
            return None

        mutations = parent_owned_todo_mutations_for_transition(decision)
        if not decision.get("transition_ready") or not mutations:
            out["skipped_reasons"].append(f"{transition}:not_ready_or_empty_mutations")
            return None

        cap = capture_transition_decision(
            root,
            transition,
            emit_observability=mao_emit_transition_observability_enabled(),
            downstream_readiness_trigger=DOWNSTREAM_TRIGGER_HOOK_POST_TOOL_AUTO_CAPTURE,
        )
        out["captures"][transition] = cap
        if cap.get("artifact_written") and cap.get("decision", {}).get("transition_ready"):
            if cap.get("todo_mutations"):
                if transition == "build_to_validate":
                    out["build_to_validate_hook_capture_succeeded"] = True
        return cap

    try:
        _attempt("plan_to_build")
        _attempt("build_to_validate")
    except Exception as exc:  # noqa: BLE001 — hook must fail open
        out["skipped_reasons"].append(f"hook_auto_capture_exception:{exc!s}")
    return out


def write_verifier_autostart_intent_if_eligible(
    project_dir: str | Path, hook_summary: dict
) -> Path | None:
    """
    Write gitignored verifier-autostart-intent.json when hook auto-capture for
    build→validate succeeded in this PostToolUse chain and strict checks pass.

    Intent is advisory; the parent should evaluate with ``evaluate_build_to_validate_transition()``
    and ``evaluate_verifier_autostart_intent()`` before any dispatch decision.

    Parent must still confirm handoffs, apply TodoWrite if needed, spawn verifier,
    then delete or mark consumed — hooks never start subagents.
    """
    if not mao_verifier_autostart_enabled():
        return None
    if not hook_summary.get("build_to_validate_hook_capture_succeeded"):
        return None

    root = Path(project_dir).resolve()
    reasons: list[str] = ["hook_build_to_validate_capture_succeeded"]

    decision = evaluate_build_to_validate_transition(root)
    mutations = parent_owned_todo_mutations_for_transition(decision)
    if not decision.get("transition_ready") or not mutations:
        return None

    gate_advisory = read_parent_advisory_gate(root, transition="build_to_validate")
    if not gate_advisory.get("usable"):
        return None
    gate = gate_advisory.get("gate")
    if not isinstance(gate, dict):
        return None
    if not gate_is_fresh_on_disk(root, gate, require_build=True):
        return None

    if mao_verifier_autostart_require_todo_observation():
        obs_path = root / LAST_TODO_WRITE_OBSERVATION_REL
        if not obs_path.is_file():
            return None
        try:
            obs = json.loads(obs_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(obs, dict) or obs.get("parse_quality") != "ok":
            return None
        reasons.append("todo_write_observation_parse_quality_ok")

    plan_path = root / PLAN_REL
    build_path = root / BUILD_REL
    _, pm = _read_text(plan_path)
    _, bm = _read_text(build_path)
    if pm is None or bm is None:
        return None

    payload = {
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "transition": "build_to_validate",
        "repo_root": str(root.resolve()),
        "mao_worktree": collect_mao_worktree_metadata(root),
        "plan_mtime_epoch": pm,
        "build_mtime_epoch": bm,
        "reasons": reasons,
    }
    out = root / VERIFIER_AUTOSTART_INTENT_REL
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return out
    except OSError:
        return None


def _intent_mtime_matches_live(
    live: float | None,
    intent_val: object,
    *,
    role: str,
    blocked_reasons: list[str],
) -> bool:
    """Compare hook-recorded mtime to live ``_read_text`` mtime for one handoff file."""
    if live is None:
        blocked_reasons.append(f"live_{role}_mtime_unavailable")
        return False
    if intent_val is None:
        blocked_reasons.append(f"intent_{role}_mtime_missing")
        return False
    try:
        iv = float(intent_val)
    except (TypeError, ValueError):
        blocked_reasons.append(f"intent_{role}_mtime_invalid")
        return False
    if not math.isclose(live, iv, rel_tol=0.0, abs_tol=1e-6):
        blocked_reasons.append(f"intent_{role}_mtime_stale")
        return False
    return True


def evaluate_verifier_autostart_intent(repo_root: str | Path) -> dict:
    """
    Read and evaluate gitignored ``verifier-autostart-intent.json`` for parent-owned use.

    ``consumable`` is True only when the intent parses, records the expected transition,
    matches the resolved repo root and live plan/mat-build mtimes, and a live
    ``evaluate_build_to_validate_transition()`` is ready with non-empty
    ``parent_owned_todo_mutations_for_transition()`` — the same bar as hook capture.

    Non-authoritative: does not call ``TodoWrite``, spawn subprocesses, or delete the file.
    Safe to call repeatedly.
    """
    root = Path(repo_root).resolve()
    intent_path = root / VERIFIER_AUTOSTART_INTENT_REL
    rel_intent = str(VERIFIER_AUTOSTART_INTENT_REL).replace("\\", "/")

    plan_path = root / PLAN_REL
    build_path = root / BUILD_REL
    _, live_plan_mtime = _read_text(plan_path)
    _, live_build_mtime = _read_text(build_path)

    decision = evaluate_build_to_validate_transition(root)
    mutations = parent_owned_todo_mutations_for_transition(decision)

    base: dict = {
        "consumable": False,
        "blocked_reasons": [],
        "operator_summary": "",
        "intent_present": False,
        "parse_ok": False,
        "intent_path": rel_intent,
        "repo_root_resolved": str(root),
        "intent_repo_root": None,
        "repo_root_matches": None,
        "live_plan_mtime": live_plan_mtime,
        "live_build_mtime": live_build_mtime,
        "intent_plan_mtime_epoch": None,
        "intent_build_mtime_epoch": None,
        "plan_mtime_matches": False,
        "build_mtime_matches": False,
        "build_to_validate_decision": decision,
        "todo_mutations": dict(mutations),
    }

    if not intent_path.is_file():
        br = ["intent_file_absent"]
        base["blocked_reasons"] = br
        base["operator_summary"] = (
            "No verifier autostart intent on disk; advisory file was never written or "
            "was already removed. Non-authoritative hint only — use live transition "
            "evaluation for dispatch decisions."
        )
        return base

    base["intent_present"] = True

    try:
        raw = intent_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        base["blocked_reasons"] = ["intent_json_invalid"]
        base["operator_summary"] = (
            "Intent file is not valid JSON; remove it or fix contents. "
            "Non-authoritative — rely on canonical handoffs."
        )
        return base

    if not isinstance(data, dict):
        base["blocked_reasons"] = ["intent_payload_not_object"]
        base["operator_summary"] = "Intent JSON must be an object. Non-authoritative."
        return base

    base["parse_ok"] = True

    blocked: list[str] = []

    tr = data.get("transition")
    if tr != "build_to_validate":
        blocked.append("intent_transition_mismatch")

    intent_rr = data.get("repo_root")
    base["intent_repo_root"] = intent_rr if isinstance(intent_rr, str) else None
    repo_ok = False
    if not isinstance(intent_rr, str) or not intent_rr.strip():
        blocked.append("intent_repo_root_missing")
    else:
        try:
            repo_ok = Path(intent_rr).resolve() == root
        except OSError:
            blocked.append("intent_repo_root_unresolvable")
        else:
            if not repo_ok:
                blocked.append("intent_repo_root_mismatch")
    base["repo_root_matches"] = repo_ok

    ip = data.get("plan_mtime_epoch")
    ib = data.get("build_mtime_epoch")
    base["intent_plan_mtime_epoch"] = ip
    base["intent_build_mtime_epoch"] = ib

    pm_ok = _intent_mtime_matches_live(
        live_plan_mtime, ip, role="plan", blocked_reasons=blocked
    )
    bm_ok = _intent_mtime_matches_live(
        live_build_mtime, ib, role="build", blocked_reasons=blocked
    )
    base["plan_mtime_matches"] = pm_ok
    base["build_mtime_matches"] = bm_ok

    if not decision.get("transition_ready"):
        blocked.append("build_to_validate_transition_not_ready")
    if not mutations:
        blocked.append("parent_todo_mutations_empty")

    base["blocked_reasons"] = list(blocked)
    base["consumable"] = len(blocked) == 0
    base["todo_mutations"] = dict(mutations)

    if base["consumable"]:
        base["operator_summary"] = (
            "Intent file matches this repo and live handoff mtimes; build→validate is "
            "ready with non-empty helper todo_mutations. Non-authoritative — confirm "
            "explicit checks and Cursor state before dispatch; hooks never auto-start."
        )
    else:
        preview = ", ".join(blocked[:5])
        if len(blocked) > 5:
            preview += ", …"
        base["operator_summary"] = (
            f"Intent is not consumable ({preview}). Non-authoritative advisory only."
        )

    return base


def delete_verifier_autostart_intent(repo_root: str | Path) -> bool:
    """
    Remove ``verifier-autostart-intent.json`` if present. Parent/orchestrator use only.

    Returns True if a file existed and was removed. Returns False if the path was absent
    or if removal failed (for example permissions) — callers must not treat False as
    “already consumed” without rechecking ``intent_path.is_file()``.
    """
    root = Path(repo_root).resolve()
    path = root / VERIFIER_AUTOSTART_INTENT_REL
    if not path.is_file():
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def write_suggested_todo_mutation_artifact(repo_root: Path, event: dict) -> Path | None:
    """
    Overwrite gitignored suggested-todo-mutation.json with the latest capture slice.

    Advisory only: Cursor `TodoWrite` still runs in the parent composer session.
    """
    root = Path(repo_root).resolve()
    out = root / SUGGESTED_TODO_MUTATION_REL
    payload = {
        "file_version": SUGGESTED_MUTATION_FILE_VERSION,
        "event_id": event.get("event_id"),
        "captured_at": event.get("captured_at"),
        "transition": event.get("transition"),
        "allowed": event.get("allowed"),
        "decision_mode": event.get("decision_mode"),
        "next_step": event.get("next_step"),
        "todo_mutations": dict(event.get("todo_mutations") or {}),
        "todo_mutations_applicable": bool(event.get("todo_mutations_applicable")),
        "todo_mutations_blocked_reasons": list(event.get("todo_mutations_blocked_reasons") or []),
        "transition_events_path": str(TRANSITION_EVENTS_REL).replace("\\", "/"),
    }
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return out
    except OSError:
        return None


def _build_mao_todo_observation_api_inner(local_event: dict) -> dict:
    """Compact, non-authoritative payload for MaoTodoObservation API events."""
    notes = local_event.get("parse_notes") or []
    if not isinstance(notes, list):
        notes = []
    rows = local_event.get("mao_rows") or []
    if not isinstance(rows, list):
        rows = []
    parse_quality = local_event.get("parse_quality")
    return {
        "version": 1,
        "observation_kind": "mao_todo_post_tool_use",
        "non_authoritative": True,
        "source": "post_tool_use",
        "evidence_posture": "observed_optional_non_authoritative",
        "canonical_mao_truth": "file_handoffs_and_parent_checks",
        "row_state_policy": "clean_rows_only",
        "absence_semantics": "absence_does_not_imply_no_todo_change",
        "semantics": (
            "Observed todo hint (PostToolUse-derived). Not Cursor internal todo state. "
            "May be absent even when todos changed in the composer."
        ),
        "parse_quality": parse_quality,
        "todos_count": local_event.get("todos_count"),
        "merge": local_event.get("merge"),
        "mao_rows": list(rows),
        "parse_notes": [str(x) for x in notes[:16]],
        "tool_name_raw": local_event.get("tool_name_raw"),
        "tool_name_normalized": local_event.get("tool_name_normalized"),
        "observed_at": local_event.get("observed_at"),
        "mao_worktree": local_event.get("mao_worktree"),
        "session_id": _extract_session_id_from_env(),
    }


def _emit_mao_todo_observation_to_observability(repo_root: Path, local_event: dict) -> bool:
    """POST MaoTodoObservation to the observability API (fail-open)."""
    captured_at = datetime.now(timezone.utc)
    inner = _build_mao_todo_observation_api_inner(local_event)
    event_id = f"mao-todo-obs-{uuid.uuid4()}"
    ts_ms = int(captured_at.timestamp() * 1000)
    rows = inner.get("mao_rows") or []
    n_mao = len(rows) if isinstance(rows, list) else 0
    pq = inner.get("parse_quality", "?")
    if pq == "ok" and n_mao > 0:
        summary = f"MAO todo hint ({pq}) · {n_mao} parsed MAO row(s)"
    elif n_mao > 0:
        summary = f"MAO todo hint ({pq}) · row-level state withheld ({n_mao} row(s))"
    else:
        summary = f"MAO todo hint ({pq}) · partial evidence"
    payload = {
        "event_id": event_id,
        "timestamp_ms": ts_ms,
        "event_type": "MaoTodoObservation",
        "session_id": _extract_session_id_from_env(),
        "agent_id": "hook_post_tool_use",
        "tool_name": str(inner.get("tool_name_normalized") or "todo_write"),
        "tool_type": "mao_todo_observation",
        "project_dir": str(repo_root),
        "payload": inner,
        "summary": summary,
        "metadata": {
            "observation_kind": inner.get("observation_kind"),
            "parse_quality": pq,
            "non_authoritative": True,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = (mat_env_get("OBSERVABILITY_API_TOKEN", default="", root=repo_root) or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        _observability_api_events_url(repo_root),
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            _ = resp.read()
        return True
    except (urllib.error.URLError, OSError):
        return False


def _emit_transition_event_to_observability(repo_root: Path, event: dict) -> bool:
    payload = {
        "event_id": event["event_id"],
        "timestamp_ms": event["timestamp_ms"],
        "event_type": "MaoTransition",
        "session_id": event["session_id"],
        "agent_id": "parent_orchestrator",
        "tool_name": "mao_transition_capture",
        "tool_type": "mao_transition",
        "project_dir": str(repo_root),
        "payload": event,
        "summary": (
            f"MAO {event['transition']} transition "
            f"{'allowed' if event['allowed'] else 'blocked'} ({event['decision_mode']})"
        ),
        "metadata": {
            "allowed": event["allowed"],
            "transition": event["transition"],
            "decision_mode": event["decision_mode"],
            "gate_reason": event["advisory"]["reason"],
        },
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = (mat_env_get("OBSERVABILITY_API_TOKEN", default="", root=repo_root) or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        _observability_api_events_url(repo_root),
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            _ = resp.read()
        return True
    except (urllib.error.URLError, OSError):
        return False


def capture_transition_decision(
    repo_root: Path,
    transition: str,
    *,
    emit_observability: bool = False,
    downstream_readiness_trigger: str = DOWNSTREAM_TRIGGER_TRANSITION_CAPTURE,
) -> dict:
    root = Path(repo_root).resolve()
    if transition == "plan_to_build":
        decision = evaluate_plan_to_build_transition(root)
    elif transition == "build_to_validate":
        decision = evaluate_build_to_validate_transition(root)
    else:
        raise ValueError(f"unsupported transition: {transition}")

    todo_mutations = parent_owned_todo_mutations_for_transition(decision)
    event = _build_transition_event(root, decision, todo_mutations)
    event["capture"]["observability"]["enabled"] = emit_observability

    emitted = False
    if emit_observability:
        emitted = _emit_transition_event_to_observability(root, event)
        event["capture"]["observability"]["status"] = "emitted" if emitted else "failed_open"

    out = _append_transition_event(root, event)
    suggested_path: Path | None = None
    if out is not None:
        suggested_path = write_suggested_todo_mutation_artifact(root, event)
        # Narrow hook-aligned refresh: persist latest edge semantics after capture (fail-open).
        write_mao_downstream_readiness_artifact(
            root, trigger=downstream_readiness_trigger
        )
    return {
        "decision": decision,
        "event": event,
        "todo_mutations": dict(todo_mutations),
        "artifact_written": out is not None,
        "artifact_path": str(TRANSITION_EVENTS_REL).replace("\\", "/") if out is not None else None,
        "suggested_todo_mutation_path": (
            str(suggested_path).replace("\\", "/") if suggested_path is not None else None
        ),
        "observability_emitted": emitted,
    }


def gate_is_fresh_on_disk(repo_root: Path, gate: dict, *, require_build: bool = True) -> bool:
    """
    Return True if gate.json input mtimes still match files on disk.
    If False, orchestrators should re-read handoffs manually.
    """
    inputs = gate.get("inputs") or {}
    plan_path = repo_root / PLAN_REL
    build_path = repo_root / BUILD_REL
    pm = inputs.get("plan_mtime_epoch")
    bm = inputs.get("build_mtime_epoch")
    if pm is None:
        return False
    if not plan_path.is_file():
        return False
    try:
        if abs(plan_path.stat().st_mtime - float(pm)) > 1e-6:
            return False
        if require_build:
            if bm is None or not build_path.is_file():
                return False
            if abs(build_path.stat().st_mtime - float(bm)) > 1e-6:
                return False
    except OSError:
        return False
    except (TypeError, ValueError):
        return False
    return True


def _load_gate_json(gate_path: Path) -> dict | None:
    try:
        data = json.loads(gate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _gate_has_valid_shape(gate: dict) -> bool:
    if gate.get("version") != GATE_VERSION:
        return False
    generated_at = gate.get("generated_at")
    checks = gate.get("checks")
    advisory_pending = gate.get("advisory_pending")
    reasons = gate.get("reasons")
    inputs = gate.get("inputs")
    if not isinstance(generated_at, str):
        return False
    try:
        datetime.fromisoformat(generated_at)
    except ValueError:
        return False
    if (
        not isinstance(checks, dict)
        or not isinstance(advisory_pending, dict)
        or not isinstance(reasons, list)
        or not isinstance(inputs, dict)
    ):
        return False
    if inputs.get("plan_path") != str(PLAN_REL).replace("\\", "/"):
        return False
    if inputs.get("build_path") != str(BUILD_REL).replace("\\", "/"):
        return False
    if not isinstance(gate.get("validate_may_start"), bool):
        return False
    build_may_start = gate.get("build_may_start")
    if not isinstance(build_may_start, bool):
        return False
    plan_present = checks.get("plan_artifact_present")
    if plan_present is not None and not isinstance(plan_present, bool):
        return False
    for key in (
        "plan_ready",
        "build_artifact_present",
        "build_status_acceptable",
        "acceptance_criteria_ready",
        "lint_passed",
    ):
        if not isinstance(checks.get(key), bool):
            return False
    for tag, transition, primary_artifact in (
        ("[mao:build]", "plan_to_build", str(PLAN_REL).replace("\\", "/")),
        ("[mao:validate]", "build_to_validate", str(BUILD_REL).replace("\\", "/")),
    ):
        entry = advisory_pending.get(tag)
        if not isinstance(entry, dict):
            return False
        if entry.get("todo_status") != PENDING_TODO_STATUS:
            return False
        if entry.get("transition") != transition:
            return False
        if entry.get("primary_artifact") != primary_artifact:
            return False
        if entry.get("advisory_state") not in {
            ADVISORY_STATE_BLOCKED,
            ADVISORY_STATE_READY,
        }:
            return False
        if not isinstance(entry.get("recommended_parent_action"), str):
            return False
        if not isinstance(entry.get("blockers"), list):
            return False
    mw = gate.get("mao_worktree")
    if mw is not None and not mao_worktree_metadata_valid(mw):
        return False
    return True


def _plan_to_build_gate_is_internally_consistent(gate: dict) -> bool:
    checks = gate["checks"]
    advisory_pending = gate["advisory_pending"]["[mao:build]"]
    if gate.get("build_may_start") is not True:
        return False
    return (
        checks.get("plan_artifact_present", checks["plan_ready"])
        and checks["plan_ready"]
        and advisory_pending["advisory_state"] == ADVISORY_STATE_READY
        and advisory_pending["recommended_parent_action"] == "review_plan_to_build"
        and not advisory_pending["blockers"]
    )


def _build_to_validate_gate_is_internally_consistent(gate: dict) -> bool:
    checks = gate["checks"]
    advisory_pending = gate["advisory_pending"]["[mao:validate]"]
    if gate.get("validate_may_start") is not True:
        return False
    if gate.get("reasons"):
        return False
    return (
        checks.get("plan_artifact_present", checks["plan_ready"])
        and checks["plan_ready"]
        and checks["build_artifact_present"]
        and checks["build_status_acceptable"]
        and checks["acceptance_criteria_ready"]
        and checks["lint_passed"]
        and advisory_pending["advisory_state"] == ADVISORY_STATE_READY
        and advisory_pending["recommended_parent_action"] == "review_build_to_validate"
        and not advisory_pending["blockers"]
    )


def read_parent_advisory_gate(
    repo_root: Path, transition: str = "build_to_validate"
) -> dict:
    """
    Read artifacts/mao/gate.json as an advisory signal for the parent orchestrator.

    Only a fresh, valid, internally consistent, positive gate is usable.
    All other cases must fall back to manual file-based evaluation.
    """
    gate_path = repo_root / GATE_REL
    if not gate_path.is_file():
        return {"usable": False, "reason": "gate_missing", "gate": None}

    gate = _load_gate_json(gate_path)
    if gate is None:
        return {"usable": False, "reason": "gate_invalid", "gate": None}
    if not _gate_has_valid_shape(gate):
        return {"usable": False, "reason": "gate_invalid", "gate": gate}

    if transition == "plan_to_build":
        if gate.get("build_may_start") is not True:
            return {"usable": False, "reason": "gate_not_positive", "gate": gate}
        if not _plan_to_build_gate_is_internally_consistent(gate):
            return {"usable": False, "reason": "gate_inconsistent", "gate": gate}
        if not gate_is_fresh_on_disk(repo_root, gate, require_build=False):
            return {"usable": False, "reason": "gate_stale", "gate": gate}
    else:
        if gate.get("validate_may_start") is not True:
            return {"usable": False, "reason": "gate_not_positive", "gate": gate}
        if not _build_to_validate_gate_is_internally_consistent(gate):
            return {"usable": False, "reason": "gate_inconsistent", "gate": gate}
        if not gate_is_fresh_on_disk(repo_root, gate, require_build=True):
            return {"usable": False, "reason": "gate_stale", "gate": gate}

    return {"usable": True, "reason": "fresh_positive_gate", "gate": gate}


def _advisory_pending_aligned(file_ap: dict, live_ap: dict) -> bool:
    """True when on-disk gate advisory_pending matches a fresh live recompute."""
    for tag in ("[mao:build]", "[mao:validate]"):
        fe = file_ap.get(tag)
        le = live_ap.get(tag)
        if not isinstance(fe, dict) or not isinstance(le, dict):
            return False
        if fe.get("advisory_state") != le.get("advisory_state"):
            return False
        if fe.get("recommended_parent_action") != le.get("recommended_parent_action"):
            return False
        if fe.get("transition") != le.get("transition"):
            return False
        if fe.get("todo_status") != le.get("todo_status"):
            return False
        if fe.get("primary_artifact") != le.get("primary_artifact"):
            return False
        bf = sorted(fe.get("blockers") or [])
        bl = sorted(le.get("blockers") or [])
        if bf != bl:
            return False
    return True


def _interpret_advisory_pending_for_parent(
    *,
    transition: str,
    live_advisory: dict,
    aligned_with_live: bool | None,
    trusted_positive_gate: bool,
) -> dict:
    """
    Deterministic orchestration hints for the parent (not a substitute for file checks).

    The parent always re-runs canonical handoff checks; this summarizes how to treat
    advisory_pending alongside those checks.
    """
    focus = "[mao:build]" if transition == "plan_to_build" else "[mao:validate]"
    entry = live_advisory.get(focus)
    if not isinstance(entry, dict):
        entry = {}
    state = entry.get("advisory_state")
    action = entry.get("recommended_parent_action")
    blockers = list(entry.get("blockers") or [])

    gate_file_use: list[str] = []
    if trusted_positive_gate and aligned_with_live is True:
        gate_file_use.append(
            "Trusted positive gate matches live advisory_pending; still perform explicit "
            "canonical file checks before applying TodoWrite mutations."
        )
    elif trusted_positive_gate and aligned_with_live is False:
        gate_file_use.append(
            "Trusted-positive gate disagrees with live advisory_pending recompute — treat as "
            "contradictory metadata; refresh gate (e.g. re-save handoffs) or use manual/file checks only."
        )
    elif not trusted_positive_gate:
        gate_file_use.append(
            "Gate file is not a trusted positive preflight for this transition; drive "
            "orchestration from live advisory_pending + canonical files."
        )

    pending_summary: list[str] = []
    if state == ADVISORY_STATE_BLOCKED:
        pending_summary.append(
            f"{focus} stays Cursor-`pending`; advisory_pending labels it blocked "
            f"(blockers={blockers!r}). Do not advance that todo until canonical checks pass."
        )
    elif state == ADVISORY_STATE_READY:
        pending_summary.append(
            f"{focus} stays Cursor-`pending`; advisory_pending labels it ready_for_parent_review. "
            "Run the explicit parent transition check, then apply supported TodoWrite mutations."
        )

    return {
        "focus_tag": focus,
        "gate_file_use": gate_file_use,
        "pending_work_summary": pending_summary,
        "live_recommended_parent_action": action,
        "live_blockers": blockers,
    }


def _build_advisory_pending_bundle(
    repo_root: Path,
    *,
    transition: str,
    live_gate: dict,
    trusted_gate_for_transition: bool,
) -> dict:
    """Combine live handoff-derived advisory_pending with optional on-disk gate.json snapshot."""
    live = live_gate.get("advisory_pending")
    if not isinstance(live, dict):
        live = {}

    gate_path = repo_root / GATE_REL
    gate_raw = _load_gate_json(gate_path)
    file_snapshot: dict | None = None
    file_shape_ok = False
    if gate_raw is not None and _gate_has_valid_shape(gate_raw):
        file_shape_ok = True
        ap = gate_raw.get("advisory_pending")
        file_snapshot = ap if isinstance(ap, dict) else None

    aligned: bool | None = None
    if file_snapshot is not None:
        aligned = _advisory_pending_aligned(file_snapshot, live)

    interpretation = _interpret_advisory_pending_for_parent(
        transition=transition,
        live_advisory=live,
        aligned_with_live=aligned,
        trusted_positive_gate=trusted_gate_for_transition,
    )

    return {
        "live": live,
        "from_gate_file": file_snapshot,
        "gate_file_shape_valid": file_shape_ok,
        "aligned_with_live": aligned,
        "trusted_positive_gate_for_transition": trusted_gate_for_transition,
        "interpretation": interpretation,
    }


def plan_to_build_trigger_rule() -> str:
    return "current plan ready and not the repo placeholder"


def evaluate_plan_to_build_transition(repo_root: Path) -> dict:
    """
    Return the parent-owned MAO plan→build transition decision.

    The advisory gate may support the decision, but never replaces the canonical
    `docs/current-plan.md` check. If the gate is missing, stale, invalid, contradictory,
    or negative, the parent falls back to the manual/file-based path.
    """
    reasons: list[str] = []
    plan_path = repo_root / PLAN_REL
    gate_advisory = read_parent_advisory_gate(repo_root, transition="plan_to_build")
    live_gate = evaluate_mao_gate(repo_root)

    plan_text, _plan_mtime = _read_text(plan_path)

    plan_present = plan_text is not None
    if not plan_present and "current_plan_missing" not in reasons:
        reasons.append("current_plan_missing")
    plan_ok = _plan_ready(plan_text, reasons)
    transition_ready = plan_ok

    advisory_bundle = _build_advisory_pending_bundle(
        repo_root,
        transition="plan_to_build",
        live_gate=live_gate,
        trusted_gate_for_transition=bool(gate_advisory["usable"]),
    )

    return {
        "transition": "plan_to_build",
        "decision_owner": "parent_orchestrator",
        "trigger_rule": plan_to_build_trigger_rule(),
        "transition_ready": transition_ready,
        "decision_mode": "gate_plus_files" if gate_advisory["usable"] else "manual_file_check",
        "gate": gate_advisory,
        "advisory_pending": advisory_bundle,
        "manual_checks": {
            "plan_artifact_present": plan_present,
            "plan_ready": plan_ok,
        },
        "reasons": reasons,
        "next_step": (
            "parent_may_complete_plan_and_start_build"
            if transition_ready
            else "manual_review_required"
        ),
    }


def build_to_validate_trigger_rule() -> str:
    return (
        "current plan ready, build-result.md present, build status PASS or PARTIAL, "
        "Acceptance Criteria section contains only PASS/PARTIAL outcomes, and "
        "Linting / Type-Check is PASS"
    )


def parent_owned_todo_mutations_for_transition(decision: dict) -> dict[str, str]:
    """
    Return the exact MAO status mutations the parent may apply for a passing transition.

    This helper is intentionally conservative about ownership and transition readiness.
    A passing parent-owned transition may yield the exact MAO mutation whether the
    decision ran with a fresh positive advisory gate plus files or on the manual/file
    fallback path. For `gate_plus_files`, if on-disk `advisory_pending` disagrees with
    the live recompute (`aligned_with_live` is False), returns no mutation even when
    canonical file checks passed — refresh the gate or rely on manual mode. Unsupported,
    non-parent, or blocked decisions return no mutation.
    """
    if decision.get("decision_owner") != "parent_orchestrator":
        return {}
    if decision.get("decision_mode") not in {"gate_plus_files", "manual_file_check"}:
        return {}
    if decision.get("transition_ready") is not True:
        return {}

    if decision.get("decision_mode") == "gate_plus_files":
        bundle = decision.get("advisory_pending") or {}
        if bundle.get("aligned_with_live") is False:
            return {}

    transition = decision.get("transition")
    mutations = TRANSITION_TODO_MUTATIONS.get(transition)
    if mutations is None:
        return {}
    return dict(mutations)


def evaluate_build_to_validate_transition(repo_root: Path) -> dict:
    """
    Return the parent-owned MAO build→validate transition decision.

    The advisory gate may support the decision, but never replaces canonical file checks.
    If the gate is missing, disabled, stale, invalid, contradictory, or negative, the
    parent still falls back to the manual/file-based path.
    """
    reasons: list[str] = []
    plan_path = repo_root / PLAN_REL
    build_path = repo_root / BUILD_REL
    gate_advisory = read_parent_advisory_gate(repo_root, transition="build_to_validate")
    live_gate = evaluate_mao_gate(repo_root)

    plan_text, _plan_mtime = _read_text(plan_path)
    build_text, _build_mtime = _read_text(build_path)

    plan_present = plan_text is not None
    if not plan_present and "current_plan_missing" not in reasons:
        reasons.append("current_plan_missing")
    plan_ok = _plan_ready(plan_text, reasons)
    build_present = build_text is not None
    if not build_present and "build_result_missing" not in reasons:
        reasons.append("build_result_missing")
    build_status_ok = _build_status_acceptable(build_text, reasons)
    acceptance_ok = _acceptance_criteria_ready(build_text, reasons)
    lint_ok = _lint_section_passed(build_text, reasons)

    transition_ready = plan_ok and build_status_ok and acceptance_ok and lint_ok

    advisory_bundle = _build_advisory_pending_bundle(
        repo_root,
        transition="build_to_validate",
        live_gate=live_gate,
        trusted_gate_for_transition=bool(gate_advisory["usable"]),
    )

    return {
        "transition": "build_to_validate",
        "decision_owner": "parent_orchestrator",
        "trigger_rule": build_to_validate_trigger_rule(),
        "transition_ready": transition_ready,
        "decision_mode": "gate_plus_files" if gate_advisory["usable"] else "manual_file_check",
        "gate": gate_advisory,
        "advisory_pending": advisory_bundle,
        "manual_checks": {
            "plan_artifact_present": plan_present,
            "plan_ready": plan_ok,
            "build_artifact_present": build_present,
            "build_status_acceptable": build_status_ok,
            "acceptance_criteria_ready": acceptance_ok,
            "lint_passed": lint_ok,
        },
        "reasons": reasons,
        "next_step": (
            "parent_may_complete_build_and_move_validate_forward"
            if transition_ready
            else "manual_review_required"
        ),
    }
