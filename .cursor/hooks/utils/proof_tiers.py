"""Shared proof-tier vocabulary for orchestration evidence."""

from __future__ import annotations

from typing import Any

PROOF_TIER_POLICY_REQUIRED = "policy_required_delegation"
PROOF_TIER_SPAWN_REQUESTED = "spawn_requested"
PROOF_TIER_GENERIC_RUNTIME = "generic_runtime_spawn_observed"
PROOF_TIER_CORRELATED = "correlated_role_attribution"
PROOF_TIER_TYPED = "typed_role_proved"

PROOF_TIERS_IN_ASCENDING_STRENGTH = (
    PROOF_TIER_POLICY_REQUIRED,
    PROOF_TIER_SPAWN_REQUESTED,
    PROOF_TIER_GENERIC_RUNTIME,
    PROOF_TIER_CORRELATED,
    PROOF_TIER_TYPED,
)

PROOF_TIER_DISPLAY = {
    PROOF_TIER_POLICY_REQUIRED: "policy-required delegation",
    PROOF_TIER_SPAWN_REQUESTED: "spawn requested",
    PROOF_TIER_GENERIC_RUNTIME: "generic runtime spawn observed",
    PROOF_TIER_CORRELATED: "correlated role attribution",
    PROOF_TIER_TYPED: "typed role proved",
}

_TYPED_RUNTIME_SUBAGENTS = {"builder", "verifier"}
_CORRELATED_LIFECYCLE_STATUSES = {
    "matched_pending_spawn_request",
    "matched_from_persisted_start_context",
    "start_context_without_pending_request",
}


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def display_proof_tier(value: str | None) -> str:
    if not value:
        return "unknown"
    return PROOF_TIER_DISPLAY.get(value, value.replace("_", " "))


def strongest_proof_tier(tiers: list[str] | tuple[str, ...]) -> str:
    tier_set = {tier for tier in tiers if tier}
    for tier in reversed(PROOF_TIERS_IN_ASCENDING_STRENGTH):
        if tier in tier_set:
            return tier
    return PROOF_TIER_POLICY_REQUIRED


def classify_subagent_proof_tier(row: dict[str, Any]) -> str:
    raw_subagent_type = _clean_text(row.get("raw_subagent_type") or row.get("subagent_type"))
    role = _clean_text(row.get("role"))
    lifecycle_match_status = _clean_text(row.get("lifecycle_match_status"))
    spawn_correlation_id = _clean_text(row.get("spawn_correlation_id"))
    task_id = _clean_text(row.get("task_id"))

    if raw_subagent_type in _TYPED_RUNTIME_SUBAGENTS and (
        role is None or role == raw_subagent_type
    ):
        return PROOF_TIER_TYPED

    if role and (
        spawn_correlation_id
        or task_id
        or lifecycle_match_status in _CORRELATED_LIFECYCLE_STATUSES
    ):
        return PROOF_TIER_CORRELATED

    return PROOF_TIER_GENERIC_RUNTIME
