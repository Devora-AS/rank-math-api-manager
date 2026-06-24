#!/usr/bin/env python3
"""List or verify SHA256 content fingerprints for MAT legacy migration paths from git history."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_DEFAULT_BOUNDARY = "aefa9f7^"
_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _git_text(
    repo: Path,
    args: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
    )


def _git_show_bytes(repo: Path, rev: str, rel_path: str) -> bytes | None:
    completed = subprocess.run(
        ["git", "show", f"{rev}:{rel_path}"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def git_content_fingerprints_for_path(repo: Path, rel_path: str, boundary: str) -> list[str]:
    """SHA256 of exact bytes at `rel_path` for each commit touching the path since `boundary`, unique sorted."""
    log = _git_text(
        repo,
        ["log", boundary, "--format=%H", "--", rel_path],
        check=False,
    )
    if log.returncode != 0:
        raise RuntimeError((log.stderr or log.stdout or "git log failed").strip())
    commits = [ln.strip() for ln in log.stdout.splitlines() if ln.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for rev in commits:
        body = _git_show_bytes(repo, rev, rel_path)
        if body is None:
            continue
        h = hashlib.sha256(body).hexdigest()
        if h not in seen:
            seen.add(h)
            out.append(h)
    out.sort()
    return out


def _normalize_path_seg(p: str) -> str:
    n = p.replace("\\", "/").strip()
    while n.startswith("./"):
        n = n[2:]
    return n


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _load_manifest_entry(manifest_path: Path, rel_path: str) -> dict[str, Any] | None:
    data = _load_manifest(manifest_path)
    want = _normalize_path_seg(rel_path)
    for entry in data.get("entries", []):
        if isinstance(entry, dict) and _normalize_path_seg(str(entry.get("path", ""))) == want:
            return entry
    return None


def _entry_boundary(entry: dict[str, Any], default: str) -> str:
    prov = entry.get("fingerprint_provenance")
    if isinstance(prov, dict):
        boundary = prov.get("boundary")
        if isinstance(boundary, str) and boundary.strip():
            return boundary.strip()
    return default


def verify_manifest_fingerprints(
    repo: Path,
    manifest: Path,
    rel_path: str,
    boundary: str,
    *,
    strict: bool = False,
) -> tuple[bool, str]:
    """Return (ok, message). Set equality when manifest lists fingerprints; lenient when list is empty."""
    git_fps = set(git_content_fingerprints_for_path(repo, rel_path, boundary))
    entry = _load_manifest_entry(manifest, rel_path)
    if entry is None:
        return False, f"no manifest entry for path {rel_path!r}"
    raw_fps = entry.get("fingerprints")
    if not isinstance(raw_fps, list):
        return False, "entry fingerprints is not a list"
    man_fps = {str(x).lower() for x in raw_fps if isinstance(x, str) and _HEX64.match(str(x))}
    # Non-hex entries are a manifest bug; validate_mat_legacy_migrations catches that separately.
    handling = str(entry.get("handling", ""))
    if not man_fps:
        if git_fps and handling in {"backup_then_remove", "auto_remove"}:
            return (
                False,
                f"manifest has no fingerprints but git history has {len(git_fps)} distinct blob(s); "
                "add fingerprints or use warn_only",
            )
        if git_fps:
            return True, f"no manifest fingerprints (git has {len(git_fps)} historical blob(s); not a drift check)"
        return True, "no manifest fingerprints and no git history for path"

    missing_in_manifest = git_fps - man_fps
    if missing_in_manifest:
        return False, f"git-derived blobs missing from manifest (add fingerprints): {sorted(missing_in_manifest)}"
    extra_in_manifest = man_fps - git_fps
    if extra_in_manifest and strict:
        return False, f"manifest-only fingerprints not seen in git history (--strict): {sorted(extra_in_manifest)}"
    if extra_in_manifest:
        return (
            True,
            "ok: every git-derived blob is listed; manifest has extra documented fingerprints "
            f"(not in git log for this path): {sorted(extra_in_manifest)}",
        )
    return True, "manifest fingerprints match git-derived union"


def verify_all_manifest_fingerprints(
    repo: Path,
    manifest: Path,
    *,
    default_boundary: str = _DEFAULT_BOUNDARY,
    strict: bool = False,
) -> tuple[bool, list[tuple[str, bool, str]]]:
    """Verify every manifest entry with non-empty fingerprints. Returns (all_ok, per-entry results)."""
    data = _load_manifest(manifest)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("manifest missing entries array")

    results: list[tuple[str, bool, str]] = []
    all_ok = True
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw_fps = entry.get("fingerprints")
        if not isinstance(raw_fps, list) or not raw_fps:
            continue
        rel = _normalize_path_seg(str(entry.get("path", "")))
        if not rel:
            continue
        boundary = _entry_boundary(entry, default_boundary)
        ok, msg = verify_manifest_fingerprints(
            repo,
            manifest,
            rel,
            boundary,
            strict=strict,
        )
        results.append((rel, ok, msg))
        if not ok:
            all_ok = False
    return all_ok, results


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Print sorted SHA256 fingerprints of every distinct file body for --path across git history "
            f"(default boundary {_DEFAULT_BOUNDARY!r}: last revision before mat-* rename slice), "
            "or --verify / --verify-all against mat-legacy-migrations-v1.json."
        ),
    )
    p.add_argument("--repo", default=".", type=Path, help="Git repository root (default: cwd).")
    p.add_argument(
        "--path",
        help="Repository-relative path (posix-style). Optional when --verify-all is set.",
    )
    p.add_argument(
        "--boundary",
        default=_DEFAULT_BOUNDARY,
        help=f"Passed to `git log <boundary> -- <path>` (default: {_DEFAULT_BOUNDARY!r}).",
    )
    p.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("mat-legacy-migrations-v1.json"),
        help="Legacy migrations manifest (for --verify / --verify-all).",
    )
    p.add_argument(
        "--verify",
        action="store_true",
        help="Ensure every git-derived blob for --path is listed in the manifest (default allows manifest-only extras such as test stubs).",
    )
    p.add_argument(
        "--verify-all",
        action="store_true",
        help="Verify every manifest entry with non-empty fingerprints (per-entry boundary from fingerprint_provenance when set).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="With --verify or --verify-all, also fail when the manifest lists fingerprints not found in git history for the path.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo = args.repo.expanduser().resolve()
    manifest = args.manifest.expanduser().resolve()

    if args.verify_all:
        try:
            all_ok, results = verify_all_manifest_fingerprints(
                repo,
                manifest,
                default_boundary=args.boundary,
                strict=args.strict,
            )
        except Exception as exc:
            print(f"mat-legacy-fingerprints: {exc}", file=sys.stderr)
            return 1
        if not results:
            print("verify-all: no fingerprinted manifest entries")
            return 0
        failed = [(rel, msg) for rel, ok, msg in results if not ok]
        passed = len(results) - len(failed)
        print(f"verify-all: {passed}/{len(results)} entries passed")
        for rel, ok, msg in results:
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {rel}: {msg}")
        return 0 if all_ok else 2

    if not args.path:
        print("mat-legacy-fingerprints: --path is required unless --verify-all is set", file=sys.stderr)
        return 1

    rel = _normalize_path_seg(args.path)
    try:
        if args.verify:
            entry = _load_manifest_entry(manifest, rel)
            boundary = _entry_boundary(entry, args.boundary) if entry else args.boundary
            ok, msg = verify_manifest_fingerprints(
                repo,
                manifest,
                rel,
                boundary,
                strict=args.strict,
            )
            print(msg)
            return 0 if ok else 2
        fps = git_content_fingerprints_for_path(repo, rel, args.boundary)
        for h in fps:
            print(h)
        return 0
    except Exception as exc:
        print(f"mat-legacy-fingerprints: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
