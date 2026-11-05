from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT_EXTENSION_OWNED_DIRS = (
    ".cursor/agents",
    ".cursor/commands",
    ".cursor/skills",
    ".cursor/rules",
)
DRIFT_OWNED_DIRS = (".cursor/hooks",)
KIND_TO_OWNED_DIR = {
    "agents": ".cursor/agents",
    "commands": ".cursor/commands",
    "skills": ".cursor/skills",
    "rules": ".cursor/rules",
}

_STALE_LAYOUT_MARKERS = (
    "source file is missing",
    "missing source directory:",
)

_UNMANAGED_RE = re.compile(
    r"^target contains unmanaged file inside owned directory ([^:]+): (.+)$"
)

_SCHEMA_VERSION = 3
_EXTENSION_KINDS = ("agents", "commands", "skills", "rules")


def product_extensions_path(target_root: Path) -> Path:
    return target_root / ".mat" / "product-extensions.json"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extension_entry(path: Path, *, source: str) -> dict[str, str]:
    return {
        "name": path.name,
        "sha256": _sha256_file(path),
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }


def _skill_extension_entry(skill_dir: Path, *, source: str) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "name": skill_dir.name,
        "source": source,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_file():
        entry["sha256"] = _sha256_file(skill_md)
    return entry


def _disk_path_for_extension(target_root: Path, kind: str, name: str) -> Path:
    owned_dir = KIND_TO_OWNED_DIR[kind]
    if kind == "skills":
        return target_root / owned_dir / name / "SKILL.md"
    return target_root / owned_dir / name


def _extension_exists_on_disk(target_root: Path, kind: str, name: str) -> bool:
    path = _disk_path_for_extension(target_root, kind, name)
    return path.is_file()


def _upstream_extension_baselines(source_root: Path) -> dict[str, set[str]]:
    agents: set[str] = set()
    commands: set[str] = set()
    skills: set[str] = set()
    rules: set[str] = set()

    source_agents = source_root / ".cursor" / "agents"
    source_commands = source_root / ".cursor" / "commands"
    source_skills = source_root / ".cursor" / "skills"
    source_rules = source_root / ".cursor" / "rules"

    if source_agents.is_dir():
        agents = {p.name for p in source_agents.glob("*.md")}
    if source_commands.is_dir():
        commands = {p.name for p in source_commands.glob("*.md")}
    if source_skills.is_dir():
        skills = {p.name for p in source_skills.iterdir() if p.is_dir()}
    if source_rules.is_dir():
        rules = {p.name for p in source_rules.iterdir() if p.is_file()}

    return {
        "agents": agents,
        "commands": commands,
        "skills": skills,
        "rules": rules,
    }


def _upstream_basenames(source_root: Path) -> tuple[set[str], set[str]]:
    baselines = _upstream_extension_baselines(source_root)
    return baselines["agents"], baselines["commands"]


def _empty_extensions_payload() -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "agents": [],
        "commands": [],
        "skills": [],
        "rules": [],
    }


def _normalize_entry(
    item: Any,
    *,
    target_root: Path,
    kind: str,
    default_source: str = "reconcile",
) -> dict[str, Any]:
    owned_dir = KIND_TO_OWNED_DIR[kind]
    if isinstance(item, dict) and isinstance(item.get("name"), str):
        name = item["name"]
        entry: dict[str, Any] = {
            "name": name,
            "source": str(item.get("source") or default_source),
        }
        if isinstance(item.get("sha256"), str):
            entry["sha256"] = item["sha256"]
        if isinstance(item.get("detected_at"), str):
            entry["detected_at"] = item["detected_at"]
        disk_path = _disk_path_for_extension(target_root, kind, name)
        if disk_path.is_file() and "sha256" not in entry:
            entry["sha256"] = _sha256_file(disk_path)
        if "detected_at" not in entry:
            entry["detected_at"] = datetime.now(timezone.utc).isoformat()
        return entry

    name = str(item)
    entry = {
        "name": name,
        "source": default_source,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }
    disk_path = _disk_path_for_extension(target_root, kind, name)
    if disk_path.is_file():
        entry["sha256"] = _sha256_file(disk_path)
    return entry


def load_product_extensions(target_root: Path) -> dict[str, Any]:
    path = product_extensions_path(target_root)
    if not path.is_file():
        return _empty_extensions_payload()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return _empty_extensions_payload()

    schema_version = data.get("schema_version", 1)
    default_source = "reconcile" if schema_version >= 2 else "reconcile"

    payload: dict[str, Any] = {"schema_version": _SCHEMA_VERSION}
    for kind in _EXTENSION_KINDS:
        raw = data.get(kind) if isinstance(data.get(kind), list) else []
        payload[kind] = [
            _normalize_entry(item, target_root=target_root, kind=kind, default_source=default_source)
            for item in raw
        ]
    return payload


def detect_custom_extensions(
    source_root: Path,
    target_root: Path,
    *,
    source: str = "live_scan",
) -> dict[str, Any]:
    """List custom agents/commands/skills/rules on target not in upstream MAT bundle."""
    baselines = _upstream_extension_baselines(source_root)

    custom_agents: list[dict[str, Any]] = []
    custom_commands: list[dict[str, Any]] = []
    custom_skills: list[dict[str, Any]] = []
    custom_rules: list[dict[str, Any]] = []

    target_agents = target_root / ".cursor" / "agents"
    target_commands = target_root / ".cursor" / "commands"
    target_skills = target_root / ".cursor" / "skills"
    target_rules = target_root / ".cursor" / "rules"

    if target_agents.is_dir():
        for path in sorted(target_agents.glob("*.md")):
            if path.name not in baselines["agents"]:
                custom_agents.append(_extension_entry(path, source=source))
    if target_commands.is_dir():
        for path in sorted(target_commands.glob("*.md")):
            if path.name not in baselines["commands"]:
                custom_commands.append(_extension_entry(path, source=source))
    if target_skills.is_dir():
        for path in sorted(target_skills.iterdir()):
            if path.is_dir() and path.name not in baselines["skills"]:
                custom_skills.append(_skill_extension_entry(path, source=source))
    if target_rules.is_dir():
        for path in sorted(target_rules.iterdir()):
            if path.is_file() and path.name not in baselines["rules"]:
                custom_rules.append(_extension_entry(path, source=source))

    return {
        "schema_version": _SCHEMA_VERSION,
        "agents": custom_agents,
        "commands": custom_commands,
        "skills": custom_skills,
        "rules": custom_rules,
    }


def reconcile_product_extensions(
    source_root: Path,
    target_root: Path,
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge live scan with registry without dropping verified registry rows."""
    live = detect_custom_extensions(source_root, target_root, source="live_scan")
    reg = registry if registry is not None else load_product_extensions(target_root)

    def _merge(kind: str) -> list[dict[str, Any]]:
        live_by_name = {entry["name"]: entry for entry in live.get(kind, []) if isinstance(entry, dict)}
        merged: dict[str, dict[str, Any]] = {}
        for item in reg.get(kind, []):
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not isinstance(name, str):
                continue
            if not _extension_exists_on_disk(target_root, kind, name):
                continue
            merged[name] = dict(item)
        for name, live_entry in live_by_name.items():
            existing = merged.get(name)
            if existing is None:
                merged[name] = dict(live_entry)
                continue
            if existing.get("sha256") == live_entry.get("sha256"):
                continue
            merged[name] = {
                **existing,
                "sha256": live_entry["sha256"],
                "detected_at": live_entry["detected_at"],
                "source": "reconcile",
            }
        return [merged[name] for name in sorted(merged)]

    return {
        "schema_version": _SCHEMA_VERSION,
        "agents": _merge("agents"),
        "commands": _merge("commands"),
        "skills": _merge("skills"),
        "rules": _merge("rules"),
    }


def persist_product_extensions(target_root: Path, payload: dict[str, Any]) -> Path:
    out = product_extensions_path(target_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    normalized = {
        "schema_version": _SCHEMA_VERSION,
        "agents": payload.get("agents", []),
        "commands": payload.get("commands", []),
        "skills": payload.get("skills", []),
        "rules": payload.get("rules", []),
    }
    out.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def product_extensions_needs_reconcile(target_root: Path, source_root: Path) -> bool:
    path = product_extensions_path(target_root)
    if not path.is_file():
        return True

    registry = load_product_extensions(target_root)
    stale, _integrity = _audit_registry_entries(
        target_root=target_root,
        source_root=source_root,
        registry=registry,
    )
    if stale:
        return True

    live = detect_custom_extensions(source_root, target_root, source="live_scan")
    for kind in _EXTENSION_KINDS:
        reg_names = set(_registry_by_name(registry, kind))
        for name in _live_by_name(live, kind):
            if name not in reg_names:
                return True
    return False


def maybe_reconcile_product_extensions(source_root: Path, target_root: Path) -> Path | None:
    """Reconcile and persist v3 registry when missing or stale. Returns path if written."""
    if not product_extensions_needs_reconcile(target_root, source_root):
        return None
    payload = reconcile_product_extensions(source_root, target_root)
    return persist_product_extensions(target_root, payload)


def write_product_extensions(source_root: Path, target_root: Path) -> Path:
    payload = detect_custom_extensions(source_root, target_root, source="bootstrap")
    return persist_product_extensions(target_root, payload)


def _registered_extension_paths(registry: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for kind, owned_dir in KIND_TO_OWNED_DIR.items():
        for item in registry.get(kind, []):
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                name = item["name"]
                if kind == "skills":
                    paths.add(f"{owned_dir}/{name}/")
                else:
                    paths.add(f"{owned_dir}/{name}")
            elif isinstance(item, str):
                paths.add(f"{owned_dir}/{item}")
    return paths


def _registry_by_name(registry: dict[str, Any], kind: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in registry.get(kind, []):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            out[item["name"]] = item
    return out


def _live_by_name(live: dict[str, Any], kind: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in live.get(kind, []):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            out[item["name"]] = item
    return out


def _kind_for_owned_dir(owned_dir: str) -> str | None:
    for kind, path in KIND_TO_OWNED_DIR.items():
        if owned_dir == path:
            return kind
    return None


def _audit_registry_entries(
    *,
    target_root: Path,
    source_root: Path,
    registry: dict[str, Any],
) -> tuple[list[str], list[str]]:
    stale: list[str] = []
    integrity: list[str] = []
    baselines = _upstream_extension_baselines(source_root)

    for kind, owned_dir in KIND_TO_OWNED_DIR.items():
        for name, entry in _registry_by_name(registry, kind).items():
            label = f"{owned_dir}/{name}"
            if not _extension_exists_on_disk(target_root, kind, name):
                stale.append(f"registry entry missing on disk: {label}")
                continue
            if name in baselines[kind]:
                integrity.append(f"registry entry shadows upstream baseline: {label}")
                continue
            reg_hash = entry.get("sha256")
            if not isinstance(reg_hash, str):
                integrity.append(f"registry entry missing sha256: {label}")
                continue
            disk_hash = _sha256_file(_disk_path_for_extension(target_root, kind, name))
            if reg_hash != disk_hash:
                integrity.append(f"registry sha256 mismatch: {label}")
    return stale, integrity


def _is_stale_layout_conflict(line: str) -> bool:
    if any(marker in line for marker in _STALE_LAYOUT_MARKERS):
        return True
    match = _UNMANAGED_RE.match(line)
    if not match:
        return False
    owned_dir = match.group(1).strip()
    return owned_dir.startswith(".mat/") or owned_dir == ".mat"


def _classify_skill_conflict(
    *,
    rel: str,
    target_root: Path,
    source_root: Path,
    live_extensions: dict[str, Any],
    registry: dict[str, Any],
) -> str:
    skill_name = rel.split("/")[0]
    baselines = _upstream_extension_baselines(source_root)
    if skill_name in baselines["skills"]:
        return "true_drift"

    skill_md = target_root / ".cursor" / "skills" / skill_name / "SKILL.md"
    if not skill_md.is_file():
        return "true_drift"

    disk_hash = _sha256_file(skill_md)
    live_entry = _live_by_name(live_extensions, "skills").get(skill_name)
    reg_entry = _registry_by_name(registry, "skills").get(skill_name)

    if reg_entry and isinstance(reg_entry.get("sha256"), str) and reg_entry.get("sha256") != disk_hash:
        return "registry_integrity"
    if live_entry and live_entry.get("sha256") == disk_hash:
        return "product_extensions"
    if reg_entry and reg_entry.get("sha256") == disk_hash:
        return "product_extensions"
    return "true_drift"


def _classify_file_extension_conflict(
    *,
    kind: str,
    rel: str,
    target_root: Path,
    source_root: Path,
    live_extensions: dict[str, Any],
    registry: dict[str, Any],
) -> str:
    baselines = _upstream_extension_baselines(source_root)
    if rel in baselines[kind]:
        return "true_drift"

    disk_path = target_root / KIND_TO_OWNED_DIR[kind] / rel
    if not disk_path.is_file():
        return "true_drift"

    disk_hash = _sha256_file(disk_path)
    live_entry = _live_by_name(live_extensions, kind).get(rel)
    reg_entry = _registry_by_name(registry, kind).get(rel)

    if reg_entry and isinstance(reg_entry.get("sha256"), str) and reg_entry.get("sha256") != disk_hash:
        return "registry_integrity"
    if live_entry and live_entry.get("sha256") == disk_hash:
        return "product_extensions"
    if reg_entry and reg_entry.get("sha256") == disk_hash:
        return "product_extensions"
    return "true_drift"


def classify_conflict_line(
    line: str,
    *,
    target_root: Path,
    source_root: Path,
    live_extensions: dict[str, Any],
    registry: dict[str, Any],
) -> str:
    if _is_stale_layout_conflict(line):
        return "stale_layout_manifest"

    match = _UNMANAGED_RE.match(line)
    if not match:
        return "true_drift"

    owned_dir, rel = match.group(1).strip(), match.group(2).strip()
    if owned_dir in DRIFT_OWNED_DIRS or owned_dir.startswith(".cursor/hooks/"):
        return "true_drift"

    kind = _kind_for_owned_dir(owned_dir)
    if kind is None:
        return "true_drift"

    if kind == "skills":
        return _classify_skill_conflict(
            rel=rel,
            target_root=target_root,
            source_root=source_root,
            live_extensions=live_extensions,
            registry=registry,
        )

    if kind in ("agents", "commands", "rules"):
        return _classify_file_extension_conflict(
            kind=kind,
            rel=rel,
            target_root=target_root,
            source_root=source_root,
            live_extensions=live_extensions,
            registry=registry,
        )

    return "true_drift"


def bucket_conflicts(
    conflicts: list[str],
    *,
    target_root: Path,
    source_root: Path,
) -> dict[str, Any]:
    registry = load_product_extensions(target_root)
    live_extensions = detect_custom_extensions(source_root, target_root, source="live_scan")
    stale_registry, registry_integrity = _audit_registry_entries(
        target_root=target_root,
        source_root=source_root,
        registry=registry,
    )

    buckets: dict[str, list[str]] = {
        "stale_layout_manifest": [],
        "product_extensions": [],
        "stale_registry": list(stale_registry),
        "registry_integrity": list(registry_integrity),
        "true_drift": [],
    }
    for line in conflicts:
        bucket = classify_conflict_line(
            line,
            target_root=target_root,
            source_root=source_root,
            live_extensions=live_extensions,
            registry=registry,
        )
        buckets[bucket].append(line)

    counts = {name: len(items) for name, items in buckets.items()}
    recommendation, rationale = routing_recommendation(counts)
    return {
        "conflict_buckets": buckets,
        "conflict_bucket_counts": counts,
        "routing_recommendation": recommendation,
        "routing_rationale": rationale,
    }


def routing_recommendation(counts: dict[str, int]) -> tuple[str, str]:
    total = sum(counts.values())
    if total == 0:
        return "incremental", "no updater conflicts — incremental refresh is appropriate"
    if counts.get("true_drift", 0) > 0 or counts.get("registry_integrity", 0) > 0:
        return (
            "stop",
            "true drift or registry integrity failure on MAT-managed paths — resolve manually before apply or re-bootstrap",
        )
    if counts.get("stale_layout_manifest", 0) > 0 or counts.get("product_extensions", 0) > 0:
        return (
            "rebootstrap",
            "stale layout footprint and/or verified product extensions — prefer bootstrap-workflow re-bootstrap",
        )
    if counts.get("stale_registry", 0) > 0:
        return (
            "incremental",
            "stale registry entries only — reconcile product-extensions.json before apply",
        )
    return "stop", "unclassified updater conflicts — operator review required"


def format_routing_stdout(routing: dict[str, Any]) -> list[str]:
    counts = routing["conflict_bucket_counts"]
    lines = [
        "Conflict buckets:",
        f"  stale_layout_manifest: {counts.get('stale_layout_manifest', 0)}",
        f"  product_extensions: {counts.get('product_extensions', 0)}",
        f"  stale_registry: {counts.get('stale_registry', 0)}",
        f"  registry_integrity: {counts.get('registry_integrity', 0)}",
        f"  true_drift: {counts.get('true_drift', 0)}",
        f"routing_recommendation: {routing['routing_recommendation']}",
        f"routing_rationale: {routing['routing_rationale']}",
    ]
    return lines


def has_fail_closed_drift(routing: dict[str, Any]) -> bool:
    counts = routing["conflict_bucket_counts"]
    return counts.get("true_drift", 0) > 0 or counts.get("registry_integrity", 0) > 0
