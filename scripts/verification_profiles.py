#!/usr/bin/env python3
"""Verification profile registry, check IDs, and verification-manifest helpers (E3)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_REL = Path("artifacts") / "verification-manifest.schema.json"
DEFAULT_MANIFEST_REL = Path("artifacts") / "phase1" / "verification-manifest.json"

PROFILE_IDS: tuple[str, ...] = (
    "source-full",
    "source-python-only",
    "adopted-operational",
    "adopted-contract",
)

CHECK_IDS: tuple[str, ...] = (
    "workflow_artifacts",
    "closeout_coherence",
    "planning_artifacts",
    "cost_context_hygiene",
    "doc_link_validation",
    "cursor_capability_assets",
    "command_registry",
    "agent_roster",
    "hooks_json_parse",
    "workflow_surfaces",
    "script_executability",
    "python_unittest",
    "legacy_fingerprints",
    "mcp_json",
    "scope_audit",
    "bun_server_smoke",
    "bun_client",
)

# Recorded only on abnormal phase1-verify exit; not required for overall pass manifests.
EARLY_EXIT_CHECK_IDS: tuple[str, ...] = ("phase1_verify_exit",)

_STATUS_VALUES = frozenset({"pass", "fail", "skip"})
_OVERALL_VALUES = frozenset({"pass", "fail"})
_LAYOUT_VALUES = frozenset({"source", "adopted"})

_SKIP_REASON_HINTS = re.compile(
    r"\b(skip|skipped|skipping|omitted|not\s+run|profile\s+excludes)\b",
    re.IGNORECASE,
)

_PLACEHOLDER_COMMANDS = frozenset(
    {
        "",
        "true",
        ":",
        "true;",
        "/usr/bin/true",
        "/bin/true",
    }
)


class VerificationProfileError(ValueError):
    """Invalid verification profile / manifest / check recording."""


def list_profiles() -> list[str]:
    return list(PROFILE_IDS)


def detect_repo_layout(repo_root: str | Path) -> str:
    root = Path(repo_root).resolve()
    if (root / ".mat" / "README.md").is_file():
        return "adopted"
    return "source"


def default_profile_for_repo(repo_root: str | Path) -> str:
    if detect_repo_layout(repo_root) == "adopted":
        return "adopted-operational"
    return "source-full"


def profile_meta(profile: str) -> dict[str, Any]:
    if profile not in PROFILE_IDS:
        raise VerificationProfileError(f"unknown profile: {profile}")
    descriptions = {
        "source-full": "MAT source tree: all Phase 1 checks including Bun server/client.",
        "source-python-only": "MAT source tree: Python/docs checks only; Bun sections explicit skip.",
        "adopted-operational": "Adopted sidecar: operational skips; contract tests opt-in.",
        "adopted-contract": "Adopted sidecar: runs packaged .mat/tests contract suite.",
    }
    return {
        "id": profile,
        "description": descriptions[profile],
        "repo_layout": "adopted" if profile.startswith("adopted-") else "source",
    }


def planned_checks_for_profile(profile: str) -> list[dict[str, str]]:
    """Return planned check rows for a profile (status run|skip)."""
    if profile not in PROFILE_IDS:
        raise VerificationProfileError(f"unknown profile: {profile}")

    rows: list[dict[str, str]] = []
    for check_id in CHECK_IDS:
        status = "run"
        reason = ""
        if profile == "source-python-only" and check_id in {
            "bun_server_smoke",
            "bun_client",
        }:
            status = "skip"
            reason = "source-python-only profile excludes Bun checks"
        elif profile == "adopted-operational" and check_id == "doc_link_validation":
            status = "skip"
            reason = (
                "adopted-operational skips doc link validator; "
                "use adopted-contract profile"
            )
        elif profile in {"adopted-operational", "adopted-contract"} and check_id in {
            "planning_artifacts",
            "cursor_capability_assets",
            "command_registry",
            "agent_roster",
            "legacy_fingerprints",
            "bun_server_smoke",
            "bun_client",
        }:
            status = "skip"
            if check_id in {"bun_server_smoke", "bun_client"}:
                reason = f"{profile} skips Bun checks on typical adopted sidecar trees"
            else:
                reason = f"{profile} skips source-only check {check_id}"
        elif profile == "adopted-operational" and check_id == "python_unittest":
            status = "skip"
            reason = (
                "adopted-operational skips .mat/tests by default; "
                "use adopted-contract or PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1"
            )
        elif profile in {"adopted-operational", "adopted-contract"} and check_id == "scope_audit":
            status = "skip"
            reason = f"{profile} skips source-only scope_audit self-check"
        rows.append({"id": check_id, "status": status, "reason": reason})
    return rows


def checks_must_pass_for_profile(profile: str) -> frozenset[str]:
    """Check ids that must record pass (not skip) when overall is pass."""
    if profile not in PROFILE_IDS:
        raise VerificationProfileError(f"unknown profile: {profile}")
    return frozenset(
        row["id"]
        for row in planned_checks_for_profile(profile)
        if row["status"] == "run"
    )


def assert_profile_layout_compatible(profile: str, repo_layout: str) -> None:
    if profile not in PROFILE_IDS:
        raise VerificationProfileError(f"unknown profile: {profile}")
    if repo_layout not in _LAYOUT_VALUES:
        raise VerificationProfileError(f"invalid repo_layout: {repo_layout}")
    expected = profile_meta(profile)["repo_layout"]
    if repo_layout != expected:
        raise VerificationProfileError(
            f"profile {profile!r} requires repo_layout {expected!r} (got {repo_layout!r})"
        )


def is_placeholder_verify_command(command: str | None) -> bool:
    if command is None:
        return True
    normalized = " ".join(str(command).strip().split())
    if not normalized:
        return True
    lowered = normalized.lower()
    if lowered in _PLACEHOLDER_COMMANDS:
        return True
    if lowered.replace(" ", "") in {"true", "true&&true", ":"}:
        return True
    return False


def assert_verify_command_allows_pass(command: str | None) -> None:
    if is_placeholder_verify_command(command):
        raise VerificationProfileError(
            "placeholder/empty verify command cannot record status=pass "
            f"(command={command!r})"
        )


def record_check(check: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize and validate a single check row before it is stored."""
    if not isinstance(check, Mapping):
        raise VerificationProfileError("check must be an object")
    check_id = check.get("id")
    status = check.get("status")
    reason = check.get("reason", "")
    duration_ms = check.get("duration_ms", 0)

    if not isinstance(check_id, str) or not check_id.strip():
        raise VerificationProfileError("check.id must be a non-empty string")
    if status not in _STATUS_VALUES:
        raise VerificationProfileError(
            f"check.status must be one of {sorted(_STATUS_VALUES)} (got {status!r})"
        )
    if not isinstance(reason, str):
        raise VerificationProfileError("check.reason must be a string")
    if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or duration_ms < 0:
        raise VerificationProfileError("check.duration_ms must be a non-negative integer")

    if status == "skip" and not reason.strip():
        raise VerificationProfileError("skip status requires a non-empty reason")

    # Hard guard: skip semantics must never be labeled pass.
    if status == "pass" and _SKIP_REASON_HINTS.search(reason or ""):
        raise VerificationProfileError(
            "skip≠pass: reason indicates skip but status is pass "
            f"(id={check_id!r}, reason={reason!r})"
        )

    return {
        "id": check_id,
        "status": status,
        "reason": reason,
        "duration_ms": duration_ms,
    }


def compute_overall(checks: Sequence[Mapping[str, Any]]) -> str:
    for check in checks:
        if check.get("status") == "fail":
            return "fail"
    return "pass"


def build_manifest(
    *,
    profile: str,
    repo_layout: str,
    started_at: str,
    finished_at: str,
    checks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if profile not in PROFILE_IDS:
        raise VerificationProfileError(f"unknown profile: {profile}")
    if repo_layout not in _LAYOUT_VALUES:
        raise VerificationProfileError(f"invalid repo_layout: {repo_layout}")

    normalized = [record_check(c) for c in checks]
    return {
        "profile": profile,
        "repo_layout": repo_layout,
        "started_at": started_at,
        "finished_at": finished_at,
        "overall": compute_overall(normalized),
        "checks": normalized,
    }


def _validate_against_schema(manifest: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    """Minimal JSON-Schema subset validator; prefers jsonschema when installed."""
    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(schema)
        return [
            f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
            for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
        ]
    except Exception:
        pass

    errors: list[str] = []
    required = schema.get("required") or []
    for key in required:
        if key not in manifest:
            errors.append(f"missing required field: {key}")

    props = schema.get("properties") or {}
    for key, value in manifest.items():
        if key not in props and schema.get("additionalProperties") is False:
            errors.append(f"additional property not allowed: {key}")
            continue
        prop_schema = props.get(key)
        if not isinstance(prop_schema, Mapping):
            continue
        expected_type = prop_schema.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"{key} must be a string")
        elif expected_type == "array" and not isinstance(value, list):
            errors.append(f"{key} must be an array")
        enum = prop_schema.get("enum")
        if enum is not None and value not in enum:
            errors.append(f"{key} must be one of {enum}")

    checks = manifest.get("checks")
    item_schema = ((props.get("checks") or {}).get("items")) or {}
    item_required = item_schema.get("required") or []
    item_props = item_schema.get("properties") or {}
    if isinstance(checks, list):
        for idx, check in enumerate(checks):
            if not isinstance(check, Mapping):
                errors.append(f"checks[{idx}] must be an object")
                continue
            for key in item_required:
                if key not in check:
                    errors.append(f"checks[{idx}] missing {key}")
            status = check.get("status")
            status_enum = (item_props.get("status") or {}).get("enum")
            if status_enum and status not in status_enum:
                errors.append(f"checks[{idx}].status invalid: {status!r}")
            duration = check.get("duration_ms")
            if "duration_ms" in check and (
                not isinstance(duration, int) or isinstance(duration, bool) or duration < 0
            ):
                errors.append(f"checks[{idx}].duration_ms must be a non-negative integer")
    return errors


def validate_manifest(
    manifest: Mapping[str, Any],
    *,
    schema_path: str | Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, Mapping):
        return ["manifest must be an object"]

    profile = manifest.get("profile")
    if profile not in PROFILE_IDS:
        errors.append(f"invalid profile: {profile!r}")
    layout = manifest.get("repo_layout")
    if layout not in _LAYOUT_VALUES:
        errors.append(f"invalid repo_layout: {layout!r}")
    overall = manifest.get("overall")
    if overall not in _OVERALL_VALUES:
        errors.append(f"invalid overall: {overall!r}")

    checks = manifest.get("checks")
    if not isinstance(checks, list):
        errors.append("checks must be an array")
        checks = []

    normalized_statuses: list[str] = []
    for idx, raw in enumerate(checks):
        try:
            normalized = record_check(raw)
            normalized_statuses.append(normalized["status"])
        except VerificationProfileError as exc:
            errors.append(f"checks[{idx}]: {exc}")
            continue
        reason = str(raw.get("reason", ""))
        if raw.get("status") == "pass" and _SKIP_REASON_HINTS.search(reason):
            errors.append(
                f"checks[{idx}]: skip≠pass — status pass with skip-like reason {reason!r}"
            )

    expected_overall = "fail" if "fail" in normalized_statuses else "pass"
    if overall in _OVERALL_VALUES and overall != expected_overall:
        errors.append(
            f"overall mismatch: declared {overall!r} but checks imply {expected_overall!r}"
        )

    if profile in PROFILE_IDS and layout in _LAYOUT_VALUES:
        try:
            assert_profile_layout_compatible(str(profile), str(layout))
        except VerificationProfileError as exc:
            errors.append(str(exc))

    if overall == "pass" and profile in PROFILE_IDS:
        observed_ids: list[str] = []
        id_to_status: dict[str, str] = {}
        for idx, raw in enumerate(checks):
            if not isinstance(raw, Mapping):
                continue
            cid = raw.get("id")
            if isinstance(cid, str):
                observed_ids.append(cid)
                status = raw.get("status")
                if isinstance(status, str):
                    id_to_status[cid] = status

        for early_id in EARLY_EXIT_CHECK_IDS:
            if early_id in observed_ids:
                errors.append(
                    f"overall pass must not include early-exit check {early_id!r}"
                )

        for check_id in CHECK_IDS:
            count = observed_ids.count(check_id)
            if count != 1:
                errors.append(
                    f"overall pass requires exactly one {check_id!r} check (found {count})"
                )

        must_pass = checks_must_pass_for_profile(str(profile))
        for check_id in sorted(must_pass):
            status = id_to_status.get(check_id)
            if status != "pass":
                errors.append(
                    f"overall pass requires {check_id!r} status pass (got {status!r})"
                )

    if schema_path is not None:
        path = Path(schema_path)
        if path.is_file():
            try:
                schema = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"schema unreadable: {exc}")
            else:
                errors.extend(_validate_against_schema(manifest, schema))

    return errors


def write_manifest(path: str | Path, manifest: Mapping[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    errors = validate_manifest(manifest)
    if errors:
        raise VerificationProfileError(
            "refusing to write invalid manifest: " + "; ".join(errors)
        )
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def doctor_hint(repo_root: str | Path) -> str:
    layout = detect_repo_layout(repo_root)
    default = default_profile_for_repo(repo_root)
    lines = [
        f"verification profiles: repo_layout={layout}",
        f"default profile: {default}",
        "available profiles: " + ", ".join(PROFILE_IDS),
        "run: bash scripts/phase1-verify.sh --profile <name> [--manifest PATH]",
        "docs: docs/reference/verification-profiles.md",
    ]
    for profile in PROFILE_IDS:
        meta = profile_meta(profile)
        lines.append(f"  - {profile}: {meta['description']}")
    return "\n".join(lines)


def _append_check_file(path: Path, check: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record_check(check), sort_keys=True) + "\n")


def _finalize_from_partial(
    *,
    profile: str,
    repo_layout: str,
    started_at: str,
    checks_path: Path,
    manifest_path: Path,
    schema_path: Path | None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    if checks_path.is_file():
        for line in checks_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            checks.append(json.loads(line))
    manifest = build_manifest(
        profile=profile,
        repo_layout=repo_layout,
        started_at=started_at,
        finished_at=utc_now_iso(),
        checks=checks,
    )
    errors = validate_manifest(manifest, schema_path=schema_path)
    if errors:
        raise VerificationProfileError("finalize validation failed: " + "; ".join(errors))
    write_manifest(manifest_path, manifest)
    return manifest


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MAT verification profile helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-profiles", help="Print profile ids")
    p_list.add_argument("--json", action="store_true")

    p_default = sub.add_parser("default-profile", help="Print default profile for a repo")
    p_default.add_argument("--repo-root", type=Path, default=Path.cwd())

    p_doctor = sub.add_parser("doctor-hint", help="Print operator profile guidance")
    p_doctor.add_argument("--repo-root", type=Path, default=Path.cwd())

    p_init = sub.add_parser("init", help="Start a manifest run (writes partial state)")
    p_init.add_argument("--repo-root", type=Path, default=Path.cwd())
    p_init.add_argument("--profile", required=True)
    p_init.add_argument("--manifest", type=Path, required=True)
    p_init.add_argument("--state-dir", type=Path, default=None)

    p_record = sub.add_parser("record", help="Append one check result to run state")
    p_record.add_argument("--state-dir", type=Path, required=True)
    p_record.add_argument("--id", required=True)
    p_record.add_argument("--status", required=True, choices=sorted(_STATUS_VALUES))
    p_record.add_argument("--reason", default="")
    p_record.add_argument("--duration-ms", type=int, default=0)
    p_record.add_argument(
        "--verify-command",
        default=None,
        help="When status=pass, reject placeholder commands",
    )

    p_final = sub.add_parser("finalize", help="Write verification-manifest.json")
    p_final.add_argument("--state-dir", type=Path, required=True)
    p_final.add_argument("--manifest", type=Path, required=True)
    p_final.add_argument("--schema", type=Path, default=None)

    p_validate = sub.add_parser("validate", help="Validate an existing manifest file")
    p_validate.add_argument("--manifest", type=Path, required=True)
    p_validate.add_argument("--schema", type=Path, default=None)

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "list-profiles":
        if args.json:
            print(json.dumps(list_profiles()))
        else:
            print("\n".join(list_profiles()))
        return 0

    if args.command == "default-profile":
        print(default_profile_for_repo(args.repo_root))
        return 0

    if args.command == "doctor-hint":
        print(doctor_hint(args.repo_root))
        return 0

    if args.command == "init":
        if args.profile not in PROFILE_IDS:
            print(f"error: unknown profile {args.profile!r}", file=sys.stderr)
            return 2
        state_dir = args.state_dir or (args.manifest.parent / ".verification-run")
        state_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "profile": args.profile,
            "repo_layout": detect_repo_layout(args.repo_root),
            "started_at": utc_now_iso(),
            "manifest": str(args.manifest),
        }
        (state_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        checks_path = state_dir / "checks.jsonl"
        checks_path.write_text("", encoding="utf-8")
        print(str(state_dir))
        return 0

    if args.command == "record":
        if args.status == "pass":
            assert_verify_command_allows_pass(args.verify_command or "python3 -m unittest")
        check = {
            "id": args.id,
            "status": args.status,
            "reason": args.reason,
            "duration_ms": args.duration_ms,
        }
        _append_check_file(args.state_dir / "checks.jsonl", check)
        return 0

    if args.command == "finalize":
        meta = json.loads((args.state_dir / "meta.json").read_text(encoding="utf-8"))
        schema = args.schema
        if schema is None:
            repo_schema = Path(args.manifest).resolve().parents[2] / SCHEMA_REL
            schema = repo_schema if repo_schema.is_file() else None
        try:
            manifest = _finalize_from_partial(
                profile=meta["profile"],
                repo_layout=meta["repo_layout"],
                started_at=meta["started_at"],
                checks_path=args.state_dir / "checks.jsonl",
                manifest_path=args.manifest,
                schema_path=Path(schema) if schema else None,
            )
        except VerificationProfileError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"manifest": str(args.manifest), "overall": manifest["overall"]}))
        return 0 if manifest["overall"] == "pass" else 1

    if args.command == "validate":
        schema = args.schema
        if schema is None:
            repo_schema = Path(args.manifest).resolve().parents[2] / SCHEMA_REL
            schema = repo_schema if repo_schema.is_file() else None
        manifest = load_manifest(args.manifest)
        errors = validate_manifest(manifest, schema_path=schema)
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print("OK")
        return 0

    print(f"error: unknown command {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
