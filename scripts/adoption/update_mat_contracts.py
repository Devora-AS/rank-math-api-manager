#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EXPECTED_ROLE_NAMES = (
    "updater",
    "watcher",
    "scanner",
    "analyzer",
    "architect",
    "generator",
    "test",
    "ci",
    "reviewer",
    "security",
    "rollback",
)

REQUIRED_HANDOFF_PATHS = (
    "docs/current-plan.md",
    "build-result.md",
    "verify-result.md",
)


@dataclass(slots=True)
class AdvisorTaskSessionSummary:
    schema_version: str
    session_kind: str
    role: str
    session_id: str
    task_id: str
    primary_artifact: str
    input_artifacts: list[str]
    decision: str
    status: str
    summary: str
    risks: list[str]
    follow_ups: list[str]
    approvals: list[str]
    timestamp_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_footprint_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    validate_footprint_manifest(manifest)
    return manifest


def _require_list_of_strings(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must be a list of non-empty strings")
    return [item.strip() for item in value]


def validate_footprint_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") not in {"1", "1.0.0"}:
        raise ValueError(f"unsupported footprint schema version: {manifest.get('schema_version')}")

    target_repo = manifest.get("target_repo")
    if not isinstance(target_repo, dict):
        raise ValueError("footprint manifest is missing target_repo")

    preserve_paths = _require_list_of_strings(target_repo.get("preserve_paths"), field="target_repo.preserve_paths")
    protected_handoffs = _require_list_of_strings(
        target_repo.get("protected_handoff_paths"),
        field="target_repo.protected_handoff_paths",
    )
    roles = _require_list_of_strings(target_repo.get("roles"), field="target_repo.roles")

    if tuple(roles) != EXPECTED_ROLE_NAMES:
        raise ValueError("footprint manifest roles do not match the updater role contract")

    if not preserve_paths:
        raise ValueError("footprint manifest must preserve at least one path")
    if not protected_handoffs:
        raise ValueError("footprint manifest must define protected handoff paths")

    required_doc_keys = {
        "documentation_index",
        "architecture_doc",
        "role_prompt_template",
        "summary_schema",
        "summary_examples",
    }
    docs = target_repo.get("docs")
    if not isinstance(docs, dict):
        raise ValueError("footprint manifest is missing target_repo.docs")
    missing_doc_keys = sorted(required_doc_keys - set(docs))
    if missing_doc_keys:
        raise ValueError(f"footprint manifest is missing target_repo.docs keys: {', '.join(missing_doc_keys)}")

    for key in required_doc_keys:
        value = docs.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"footprint manifest target_repo.docs.{key} must be a non-empty string")

    allow = target_repo.get("allow")
    if not isinstance(allow, dict):
        raise ValueError("footprint manifest is missing target_repo.allow")

    if allow.get("dry_run_default") is not True:
        raise ValueError("footprint manifest must keep dry-run as the default")
    if allow.get("apply_requires_approval") is not True:
        raise ValueError("footprint manifest must require approval before apply")
    if allow.get("auto_commit") is not False:
        raise ValueError("footprint manifest must forbid auto-commit")
    if allow.get("auto_pr") is not False:
        raise ValueError("footprint manifest must forbid auto-PR creation")
    if allow.get("preserve_product_agents") is not True:
        raise ValueError("footprint manifest must preserve product-owned AGENTS.md content")


def build_compatibility_snapshot(*, layout_manifest: dict[str, Any], footprint_manifest: dict[str, Any]) -> dict[str, Any]:
    validate_footprint_manifest(footprint_manifest)

    target_repo = footprint_manifest["target_repo"]
    preserve_paths = _require_list_of_strings(target_repo["preserve_paths"], field="target_repo.preserve_paths")
    protected_handoffs = _require_list_of_strings(
        target_repo["protected_handoff_paths"],
        field="target_repo.protected_handoff_paths",
    )
    role_names = _require_list_of_strings(target_repo["roles"], field="target_repo.roles")

    layout_sources = sorted(
        {item.get("src") for item in layout_manifest.get("mat_docs", []) if isinstance(item, dict) and isinstance(item.get("src"), str)}
    )
    layout_sources.extend(rel for rel in layout_manifest.get("mat_tests", []) if isinstance(rel, str))

    managed_paths = sorted(
        {
            *layout_sources,
            *preserve_paths,
            *protected_handoffs,
        }
    )

    return {
        "manifest_name": footprint_manifest.get("name"),
        "schema_version": footprint_manifest.get("schema_version"),
        "documentation_index": target_repo["docs"]["documentation_index"],
        "architecture_doc": target_repo["docs"]["architecture_doc"],
        "role_prompt_template": target_repo["docs"]["role_prompt_template"],
        "summary_schema": target_repo["docs"]["summary_schema"],
        "summary_examples": target_repo["docs"]["summary_examples"],
        "preserve_paths": preserve_paths,
        "protected_handoff_paths": protected_handoffs,
        "role_names": role_names,
        "allow": target_repo["allow"],
        "layout_source_count": len(layout_manifest.get("mat_docs", [])),
        "layout_test_count": len(layout_manifest.get("mat_tests", [])),
        "managed_paths": managed_paths,
        "managed_path_count": len(managed_paths),
        "protected_handoff_count": len(protected_handoffs),
        "contract_health": {
            "ready": True,
            "reasons": [],
        },
    }


def serialize_summary(summary: AdvisorTaskSessionSummary) -> str:
    return json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n"

