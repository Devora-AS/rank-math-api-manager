#!/usr/bin/env python3
"""Apply manifest-driven cleanup of obsolete MAT-managed paths (legacy slash commands, etc.)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ADOPTION_DIR = Path(__file__).resolve().parent
if str(_ADOPTION_DIR) not in sys.path:
    sys.path.insert(0, str(_ADOPTION_DIR))

from update_mat_contracts import load_footprint_manifest  # noqa: E402

DEFAULT_MANIFEST = Path(__file__).with_name("mat-legacy-migrations-v1.json")
DEFAULT_FOOTPRINT = Path(__file__).with_name("mat-footprint-v1.json")
DEFAULT_AUDIT_DIR = "artifacts/update-mat"
JSONL_NAME = "legacy-cleanup.jsonl"
QUARANTINE_ROOT = "legacy-quarantine"
JSONL_RECORD_SCHEMA = "1.0.0"

_ALLOWED_HANDLING = frozenset({"auto_remove", "backup_then_remove", "warn_only"})
_ALLOWED_FP_SOURCES = frozenset({"git_log_union", "manual", "git_log_union_plus_stub"})
_PRODUCT_ROOT_NAMES = frozenset({"README.md", "CHANGELOG.md", "AGENTS.md", "ROADMAP.md"})
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(slots=True)
class CleanupDecision:
    path: str
    action: str
    reason: str
    successor: str | None
    handling: str
    sha256: str | None
    dry_run: bool


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_rel(p: str) -> str:
    """Normalize manifest path segments; keep leading `.cursor/` (do not use lstrip on '.')."""
    n = p.replace("\\", "/").strip()
    while n.startswith("./"):
        n = n[2:]
    return n


def _protected_paths(footprint: dict[str, Any]) -> set[str]:
    tr = footprint.get("target_repo", {})
    out: set[str] = set()
    for key in ("preserve_paths", "protected_handoff_paths"):
        raw = tr.get(key)
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str) and item.strip():
                    out.add(_normalize_rel(item.strip()))
    return out


def load_migration_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0.0":
        raise ValueError(f"unsupported mat-legacy-migrations schema: {data.get('schema_version')}")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError("migration manifest missing entries array")
    return data


def validate_mat_legacy_migrations(migration: dict[str, Any], *, footprint: dict[str, Any]) -> None:
    """Validate manifest shape, fingerprints, handling modes, and blocked product / footprint paths."""
    if migration.get("schema_version") != "1.0.0":
        raise ValueError(f"unsupported mat-legacy-migrations schema: {migration.get('schema_version')}")
    entries = migration.get("entries")
    if not isinstance(entries, list):
        raise ValueError("migration manifest missing entries array")
    protected = _protected_paths(footprint)
    seen_paths: set[str] = set()
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"entries[{i}] must be a JSON object")
        path_raw = entry.get("path")
        if not isinstance(path_raw, str) or not path_raw.strip():
            raise ValueError(f"entries[{i}] missing non-empty string path")
        rel = _normalize_rel(path_raw)
        if rel in seen_paths:
            raise ValueError(f"entries[{i}] duplicate path {rel!r}")
        seen_paths.add(rel)
        if rel in protected:
            raise ValueError(
                f"entries[{i}] path {rel!r} is blocked: overlaps mat-footprint "
                "preserve_paths or protected_handoff_paths",
            )
        if "/" not in rel and rel in _PRODUCT_ROOT_NAMES:
            raise ValueError(
                f"entries[{i}] path {rel!r} is blocked: enumerated product-owned root filename",
            )
        handling = entry.get("handling", "warn_only")
        if not isinstance(handling, str) or handling not in _ALLOWED_HANDLING:
            raise ValueError(
                f"entries[{i}] handling must be one of {sorted(_ALLOWED_HANDLING)}; got {handling!r}",
            )
        fps_raw = entry.get("fingerprints")
        if fps_raw is None:
            raise ValueError(f"entries[{i}] missing fingerprints array (use [] for warn_only)")
        if not isinstance(fps_raw, list):
            raise ValueError(f"entries[{i}] fingerprints must be a JSON array")
        for j, fp in enumerate(fps_raw):
            if not isinstance(fp, str) or not _FP_RE.match(fp):
                raise ValueError(
                    f"entries[{i}] fingerprints[{j}] must be a 64-character lowercase hexadecimal sha256 string",
                )
        if handling in {"auto_remove", "backup_then_remove"} and len(fps_raw) == 0:
            raise ValueError(
                f"entries[{i}] handling={handling!r} requires at least one fingerprint "
                "(use warn_only when canonical bytes are unknown)",
            )
        if "successor" in entry and entry["successor"] is not None:
            succ = entry["successor"]
            if not isinstance(succ, str) or not succ.strip():
                raise ValueError(f"entries[{i}] successor must be a non-empty string when set")
            s = _normalize_rel(succ)
            if s.startswith("/"):
                raise ValueError(f"entries[{i}] successor must be a relative repository path")
            if "\\" in succ:
                raise ValueError(f"entries[{i}] successor must use forward slashes only")
            if ".." in Path(s).parts:
                raise ValueError(f"entries[{i}] successor must not contain parent-directory segments")
        prov_raw = entry.get("fingerprint_provenance")
        needs_provenance = handling in {"auto_remove", "backup_then_remove"} and len(fps_raw) > 0
        if needs_provenance and prov_raw is None:
            raise ValueError(
                f"entries[{i}] with handling={handling!r} and non-empty fingerprints "
                "requires fingerprint_provenance",
            )
        if prov_raw is not None:
            if not isinstance(prov_raw, dict):
                raise ValueError(f"entries[{i}] fingerprint_provenance must be a JSON object")
            source = prov_raw.get("source")
            if not isinstance(source, str) or source not in _ALLOWED_FP_SOURCES:
                raise ValueError(
                    f"entries[{i}] fingerprint_provenance.source must be one of "
                    f"{sorted(_ALLOWED_FP_SOURCES)}; got {source!r}",
                )
            boundary = prov_raw.get("boundary")
            if not isinstance(boundary, str) or not boundary.strip():
                raise ValueError(f"entries[{i}] fingerprint_provenance.boundary must be a non-empty string")
            generated_at = prov_raw.get("generated_at")
            if not isinstance(generated_at, str) or not _ISO_DATE_RE.match(generated_at):
                raise ValueError(
                    f"entries[{i}] fingerprint_provenance.generated_at must be ISO date YYYY-MM-DD",
                )
            if "note" in prov_raw and prov_raw["note"] is not None:
                if not isinstance(prov_raw["note"], str):
                    raise ValueError(f"entries[{i}] fingerprint_provenance.note must be a string when set")


def apply_legacy_cleanup(
    *,
    repo_root: Path,
    migration_manifest_path: Path,
    footprint_manifest_path: Path,
    audit_dir_rel: str = DEFAULT_AUDIT_DIR,
    dry_run: bool = False,
    run_id: str | None = None,
) -> list[CleanupDecision]:
    repo_root = repo_root.resolve()
    migration = load_migration_manifest(migration_manifest_path)
    footprint = load_footprint_manifest(footprint_manifest_path)
    validate_mat_legacy_migrations(migration, footprint=footprint)

    stamp = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    audit_root = repo_root / audit_dir_rel
    jsonl_path = audit_root / JSONL_NAME
    quarantine_base = audit_root / QUARANTINE_ROOT / stamp
    if not dry_run:
        audit_root.mkdir(parents=True, exist_ok=True)

    decisions: list[CleanupDecision] = []
    manifest_schema = str(migration.get("schema_version", ""))

    def append_jsonl(d: CleanupDecision) -> None:
        record = {
            "action": d.action,
            "dry_run": d.dry_run,
            "handling": d.handling,
            "legacy_cleanup_jsonl_schema": JSONL_RECORD_SCHEMA,
            "manifest_schema_version": manifest_schema,
            "path": d.path,
            "reason": d.reason,
            "run_id": stamp,
            "sha256": d.sha256,
            "successor": d.successor,
        }
        line = json.dumps(record, sort_keys=True)
        if not dry_run:
            with jsonl_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    for entry in migration["entries"]:
        rel = _normalize_rel(str(entry["path"]))
        successor = entry.get("successor")
        successor_s = str(successor).strip() if isinstance(successor, str) else None
        handling = str(entry.get("handling", "warn_only"))
        fps_raw = entry.get("fingerprints")
        fingerprints: set[str] = set()
        if isinstance(fps_raw, list):
            fingerprints.update(str(x).lower() for x in fps_raw if isinstance(x, str) and _FP_RE.match(str(x)))

        target = repo_root / rel

        if target.exists() and not target.is_file():
            d = CleanupDecision(
                path=rel,
                action="skipped_not_file",
                reason="path exists but is not a regular file",
                successor=successor_s,
                handling=handling,
                sha256=None,
                dry_run=dry_run,
            )
            decisions.append(d)
            append_jsonl(d)
            continue

        if not target.is_file():
            d = CleanupDecision(
                path=rel,
                action="skipped_absent",
                reason="file does not exist",
                successor=successor_s,
                handling=handling,
                sha256=None,
                dry_run=dry_run,
            )
            decisions.append(d)
            append_jsonl(d)
            continue

        sha = _sha256_file(target)
        matched = sha.lower() in fingerprints

        if handling == "warn_only":
            msg = f"[mat-legacy-cleanup] obsolete path present: {rel} (successor: {successor_s or 'n/a'}) — review manually; not removed (warn_only)."
            print(msg, file=sys.stderr)
            d = CleanupDecision(
                path=rel,
                action="warn_only",
                reason="handling mode is warn_only",
                successor=successor_s,
                handling=handling,
                sha256=sha,
                dry_run=dry_run,
            )
            decisions.append(d)
            append_jsonl(d)
            continue

        if handling == "auto_remove":
            if not matched:
                d = CleanupDecision(
                    path=rel,
                    action="skipped_customized",
                    reason="content does not match any fingerprint; auto_remove refuses without proof",
                    successor=successor_s,
                    handling=handling,
                    sha256=sha,
                    dry_run=dry_run,
                )
                decisions.append(d)
                append_jsonl(d)
                continue
            if dry_run:
                d = CleanupDecision(
                    path=rel,
                    action="would_remove",
                    reason="fingerprint matched; dry_run",
                    successor=successor_s,
                    handling=handling,
                    sha256=sha,
                    dry_run=True,
                )
            else:
                target.unlink()
                d = CleanupDecision(
                    path=rel,
                    action="removed",
                    reason="fingerprint matched auto_remove",
                    successor=successor_s,
                    handling=handling,
                    sha256=sha,
                    dry_run=False,
                )
            decisions.append(d)
            append_jsonl(d)
            continue

        if handling == "backup_then_remove":
            if matched:
                dest = quarantine_base / rel
                if dry_run:
                    d = CleanupDecision(
                        path=rel,
                        action="would_quarantine_and_remove",
                        reason="fingerprint matched; dry_run",
                        successor=successor_s,
                        handling=handling,
                        sha256=sha,
                        dry_run=True,
                    )
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, dest)
                    target.unlink()
                    d = CleanupDecision(
                        path=rel,
                        action="quarantined_and_removed",
                        reason=f"matched fingerprint; backup at {(dest.relative_to(repo_root)).as_posix()}",
                        successor=successor_s,
                        handling=handling,
                        sha256=sha,
                        dry_run=False,
                    )
                decisions.append(d)
                append_jsonl(d)
                continue

            dest = quarantine_base / f"customized-{Path(rel).name}"
            if dry_run:
                d = CleanupDecision(
                    path=rel,
                    action="would_quarantine_customized",
                    reason="content differs from fingerprints; would copy to quarantine only (original kept)",
                    successor=successor_s,
                    handling=handling,
                    sha256=sha,
                    dry_run=True,
                )
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, dest)
                print(
                    f"[mat-legacy-cleanup] customized legacy file left in place: {rel} "
                    f"(review copy under {dest.relative_to(repo_root).as_posix()})",
                    file=sys.stderr,
                )
                d = CleanupDecision(
                    path=rel,
                    action="quarantined_customized_left_in_place",
                    reason="content differs from fingerprints; original retained",
                    successor=successor_s,
                    handling=handling,
                    sha256=sha,
                    dry_run=False,
                )
            decisions.append(d)
            append_jsonl(d)
            continue

        d = CleanupDecision(
            path=rel,
            action="skipped_unknown_handling",
            reason=f"unknown handling mode: {handling}",
            successor=successor_s,
            handling=handling,
            sha256=sha,
            dry_run=dry_run,
        )
        decisions.append(d)
        append_jsonl(d)

    return decisions


def print_legacy_cleanup_report(*, repo_root: Path, audit_dir_rel: str) -> None:
    """Summarize the latest run_id slice in legacy-cleanup.jsonl (stdout)."""
    jsonl_path = repo_root / audit_dir_rel / JSONL_NAME
    if not jsonl_path.is_file():
        print(f"No audit file at {jsonl_path}")
        return
    lines = [ln for ln in jsonl_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        print("legacy-cleanup.jsonl is empty")
        return
    rows: list[dict[str, Any]] = []
    for ln in lines:
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            print(f"legacy-cleanup.jsonl contains invalid JSON line (skipped): {ln[:120]!r}")
    if not rows:
        return
    last_id = rows[-1].get("run_id", "(legacy records without run_id)")
    scoped = [r for r in rows if r.get("run_id") == last_id] or rows
    actions = Counter(str(r.get("action")) for r in scoped)
    print(f"legacy cleanup report: last run_id={last_id!r} (lines={len(scoped)})")
    for act, n in sorted(actions.items()):
        print(f"  {act}: {n}")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Remove or quarantine obsolete MAT legacy paths per mat-legacy-migrations manifest.")
    p.add_argument("--repo-root", default=".", help="Adopted repository root.")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="mat-legacy-migrations JSON path.")
    p.add_argument("--footprint", default=str(DEFAULT_FOOTPRINT), help="mat-footprint-v1.json path.")
    p.add_argument("--audit-dir", default=DEFAULT_AUDIT_DIR, help="Audit directory relative to repo root.")
    p.add_argument("--dry-run", action="store_true", help="Log decisions only; no file mutations.")
    p.add_argument(
        "--report",
        action="store_true",
        help="Print a summary of legacy-cleanup.jsonl under --audit-dir (no cleanup).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo = Path(args.repo_root).expanduser().resolve()
    if args.report:
        print_legacy_cleanup_report(repo_root=repo, audit_dir_rel=args.audit_dir)
        return 0
    manifest = Path(args.manifest).expanduser().resolve()
    footprint = Path(args.footprint).expanduser().resolve()
    try:
        apply_legacy_cleanup(
            repo_root=repo,
            migration_manifest_path=manifest,
            footprint_manifest_path=footprint,
            audit_dir_rel=args.audit_dir,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"apply_mat_legacy_cleanup: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
