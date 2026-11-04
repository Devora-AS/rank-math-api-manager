#!/usr/bin/env python3
"""MAT source resolution: v1/v2 config parse, precedence, provenance."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path("~/.cache/mat-source")
SIBLING_DIR_NAMES = ("multi-agent-teams", "multi-agent-workflow")
UPDATE_MAT_REL = Path("scripts/adoption/update-mat.py")
MATERIALIZE_SCRIPT = Path(__file__).resolve().parent / "mat_source_materialize.sh"


class MatSourceResolutionError(Exception):
    """Raised when MAT source cannot be resolved."""


def expand_user_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def repository_slug(repository: str) -> str:
    return repository.replace("/", "-")


def default_cache_dir() -> Path:
    return expand_user_path(DEFAULT_CACHE_DIR)


def cache_path_for_repository(cache_dir: Path, repository: str) -> Path:
    return cache_dir / repository_slug(repository)


def is_mat_source_tree(candidate: Path) -> bool:
    return (candidate / UPDATE_MAT_REL).is_file()


def load_source_config(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        raise MatSourceResolutionError(f"source config not found: {config_path}")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MatSourceResolutionError(f"invalid JSON in {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise MatSourceResolutionError(f"source config must be a JSON object: {config_path}")
    return data


def parse_source_config_v1(data: dict[str, Any]) -> str | None:
    schema_version = data.get("schema_version")
    if schema_version is not None and schema_version not in (1, "1", "1.0", "1.0.0"):
        return None
    mat_source = data.get("mat_source")
    if isinstance(mat_source, str) and mat_source.strip():
        return mat_source.strip()
    return None


def parse_source_config_v2(data: dict[str, Any]) -> dict[str, str] | None:
    schema_version = data.get("schema_version")
    if schema_version not in (2, "2", "2.0", "2.0.0"):
        return None
    repository = data.get("repository")
    ref = data.get("ref")
    if not isinstance(repository, str) or not repository.strip():
        raise MatSourceResolutionError("v2 source config requires non-empty repository")
    if not isinstance(ref, str) or not ref.strip():
        raise MatSourceResolutionError("v2 source config requires non-empty ref")
    cache_dir = data.get("cache_dir", str(DEFAULT_CACHE_DIR))
    if not isinstance(cache_dir, str) or not cache_dir.strip():
        raise MatSourceResolutionError("v2 source config cache_dir must be a non-empty string")
    return {
        "repository": repository.strip(),
        "ref": ref.strip(),
        "cache_dir": cache_dir.strip(),
    }


def resolve_local_path(
    raw_path: str,
    *,
    base_for_relative: Path | None = None,
) -> Path:
    path = Path(raw_path)
    if not path.is_absolute() and base_for_relative is not None:
        path = (base_for_relative / path).resolve()
    else:
        path = path.expanduser().resolve()
    if not is_mat_source_tree(path):
        raise MatSourceResolutionError(
            f"invalid MAT source tree (missing {UPDATE_MAT_REL}): {path}"
        )
    return path


def resolve_sibling_heuristic(target_root: Path) -> Path | None:
    parent = target_root.parent.resolve()
    for name in SIBLING_DIR_NAMES:
        sibling = parent / name
        if is_mat_source_tree(sibling):
            return sibling.resolve()
    return None


def run_materialize(
    *,
    repository: str,
    ref: str,
    cache_dir: Path,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not MATERIALIZE_SCRIPT.is_file():
        raise MatSourceResolutionError(f"materialize helper missing: {MATERIALIZE_SCRIPT}")

    cmd = [
        "bash",
        str(MATERIALIZE_SCRIPT),
        "--repository",
        repository,
        "--ref",
        ref,
        "--cache-dir",
        str(cache_dir),
        "--json",
    ]
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise MatSourceResolutionError(
            f"materialize failed for {repository}@{ref}: {detail or 'unknown error'}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise MatSourceResolutionError(
            f"materialize returned invalid JSON: {proc.stdout!r}"
        ) from exc
    if not isinstance(payload, dict):
        raise MatSourceResolutionError("materialize JSON must be an object")
    mat_source = payload.get("mat_source")
    if not isinstance(mat_source, str) or not mat_source:
        raise MatSourceResolutionError("materialize JSON missing mat_source")
    return payload


def _local_result(
    mat_source: Path,
    *,
    resolution_method: str,
) -> dict[str, Any]:
    return {
        "mat_source": str(mat_source),
        "source_kind": "local_path",
        "provenance": {
            "source_kind": "local_path",
            "resolved_path": str(mat_source),
            "resolution_method": resolution_method,
        },
    }


def _github_result(materialize_payload: dict[str, Any]) -> dict[str, Any]:
    mat_source = Path(str(materialize_payload["mat_source"])).resolve()
    provenance = {
        "source_kind": "github_materialized",
        "repository": materialize_payload.get("repository"),
        "requested_ref": materialize_payload.get("requested_ref"),
        "resolved_sha": materialize_payload.get("resolved_sha"),
        "cache_path": materialize_payload.get("cache_path"),
        "materialized_at": materialize_payload.get("materialized_at"),
    }
    return {
        "mat_source": str(mat_source),
        "source_kind": "github_materialized",
        "provenance": provenance,
    }


def resolve_mat_source(
    *,
    target_root: Path,
    source_path: str | None = None,
    repository: str | None = None,
    ref: str | None = None,
    mat_source_env: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve MAT source using documented precedence (first match wins)."""
    target_root = target_root.resolve()
    config_path = target_root / ".mat" / "source-config.json"

    if source_path:
        path = resolve_local_path(source_path, base_for_relative=target_root)
        return _local_result(path, resolution_method="cli_source")

    if repository and ref:
        cache_dir = default_cache_dir()
        payload = run_materialize(
            repository=repository.strip(),
            ref=ref.strip(),
            cache_dir=cache_dir,
            extra_env=extra_env,
        )
        return _github_result(payload)

    if config_path.is_file():
        data = load_source_config(config_path)
        v2 = parse_source_config_v2(data)
        if v2 is not None:
            cache_dir = expand_user_path(v2["cache_dir"])
            payload = run_materialize(
                repository=v2["repository"],
                ref=v2["ref"],
                cache_dir=cache_dir,
                extra_env=extra_env,
            )
            return _github_result(payload)

        v1_path = parse_source_config_v1(data)
        if v1_path is not None:
            path = resolve_local_path(v1_path, base_for_relative=target_root)
            return _local_result(path, resolution_method="config_v1")

    sibling = resolve_sibling_heuristic(target_root)
    if sibling is not None:
        return _local_result(sibling, resolution_method="sibling_heuristic")

    env_value = mat_source_env if mat_source_env is not None else os.environ.get("MAT_SOURCE")
    if env_value:
        path = resolve_local_path(env_value, base_for_relative=target_root)
        return _local_result(path, resolution_method="mat_source_env")

    raise MatSourceResolutionError(
        "MAT source not found — set --source, --repository/--ref, "
        ".mat/source-config.json, sibling checkout, or MAT_SOURCE"
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve MAT upstream source.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve", help="Resolve MAT source for a target repo")
    resolve_parser.add_argument(
        "--repo-root",
        required=True,
        help="Adopted or target repository root",
    )
    resolve_parser.add_argument(
        "--source",
        dest="source_path",
        default=None,
        help="Local MAT source checkout (dev override)",
    )
    resolve_parser.add_argument(
        "--repository",
        default=None,
        help="GitHub repository OWNER/REPO for materialized source",
    )
    resolve_parser.add_argument(
        "--ref",
        default=None,
        help="Git ref (branch, tag, or SHA) with --repository",
    )
    resolve_parser.add_argument(
        "--json",
        action="store_true",
        help="Print resolution JSON on stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command != "resolve":
        parser.error(f"unsupported command: {args.command}")

    if (args.repository is None) ^ (args.ref is None):
        parser.error("--repository and --ref must be provided together")

    try:
        result = resolve_mat_source(
            target_root=Path(args.repo_root),
            source_path=args.source_path,
            repository=args.repository,
            ref=args.ref,
        )
    except MatSourceResolutionError as exc:
        print(f"mat_source_config: error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result["mat_source"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
