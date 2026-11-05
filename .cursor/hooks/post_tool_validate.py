#!/usr/bin/env python3
"""
post_tool_validate.py — Cursor Hook: PostToolUse Linting & Type-Check

Fires on: PostToolUse (after every tool execution)
Purpose:  Run linting and type-checking after file-writing tool calls.
          Matches the builder agent's self-validation behavior described
          in disler/claude-code-hooks-mastery .claude/agents/team/mat-builder.md.

Supported validators (auto-detected):
  - Python: ruff check
  - Python type-check: ty check (or pyright if ty not available)
  - TypeScript: tsc --noEmit

MAO: when a WRITE_TOOLS call touches docs/current-plan.md or build-result.md,
mao_gate.py refreshes artifacts/mao/gate.json (parent advisory input for the
plan→build and build→validate transitions, including pending-state hints such as
blocked vs ready_for_parent_review; disable with CURSOR_MAO_GATE=0) before lint.
When the gate is disabled, the same handoff touches still refresh
artifacts/mao/downstream-readiness.json (deterministic unblock_semantic per edge;
disable with CURSOR_MAO_DOWNSTREAM_READINESS=0).

Opt-in after gate refresh: CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE may append
transition-events via capture_transition_decision when the trusted gate is fresh
and parent todo_mutations apply; CURSOR_MAO_VERIFIER_AUTOSTART may write
artifacts/mao/verifier-autostart-intent.json after a successful build→validate hook
capture. Hooks never call TodoWrite or spawn agents.

MAO / Cursor To-dos: only tools in WRITE_TOOLS (file writes) trigger validation.
TodoWrite and similar tools exit early — no full-project lint pass on todo updates.

MAO todo observation: on PostToolUse for normalized todo_write, mao_gate records
artifacts/mao/todo-write-events.jsonl + last-todo-write-observation.json (traceability
only; disable with CURSOR_MAO_TODO_POST_TOOL_USE=0), then refreshes
downstream-readiness.json when enabled. Optional gate refresh:
CURSOR_MAO_TODO_POST_TOOL_REFRESH_GATE=1 when CURSOR_MAO_GATE is on.

Loop events (opt-in): when CURSOR_MAT_LOOP_EVENTS=1, append one JSONL line to
artifacts/loop/events.jsonl on docs/current-plan.md or build-result.md writes
(fail-open; disable by default).

Scoped validation (default on): when CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE is not
`0`, prefer ruff/ty on changed `.py` files and `tsc -p` when all changed `.ts`/`.tsx`
share one package (`apps/client`, `apps/server`, or repo-root `tsconfig.json`).
Fall back to broader project checks when the change list is empty, paths are outside
the repo, TypeScript packages are mixed, scoped mode is disabled, or a package
tsconfig is missing. Full quality gate remains `bash scripts/phase1-verify.sh`.

Exit codes:
  0 — validation passed (or no relevant files changed)
  1 — validation failed (non-blocking in Phase 1; failClosed: false)

loop_limit: 3 — after 3 consecutive failures, Cursor stops calling this hook.
"""

import json
import os
import re
import subprocess
import sys

from hook_contract import emit_contract_envelope, make_contract_envelope, parse_contract_argv

_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from utils.mat_env_resolve import mat_env_flag  # noqa: E402

PROJECT_DIR = (
    os.environ.get("CURSOR_PROJECT_DIR")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
)
SCRIPT_NAME = "post_tool_validate.py"

WRITE_TOOLS = {
    "write_file", "create_file", "edit_file", "str_replace",
    "apply_patch", "write", "create", "edit",
}

# Structured tool_input keys that often carry a single file path (Cursor / IDE variants).
_PATH_SCALAR_KEYS = frozenset(
    {
        "path",
        "file_path",
        "target_file",
        "filename",
        "file",
        "filepath",
        "relative_path",
        "absolute_path",
        "target_path",
        "targetPath",
        "local_path",
        "old_path",
        "new_path",
        "source_path",
        "destination_path",
    }
)
# List-valued containers whose elements may be paths or nested path objects.
_LIST_PATH_KEYS = frozenset(
    {
        "paths",
        "files",
        "edited_files",
        "edited_paths",
        "changed_files",
        "updates",
    }
)
# Nested dicts to recurse into (tool-specific wrappers).
_NEST_DICT_KEYS = frozenset(
    {
        "args",
        "arguments",
        "params",
        "parameters",
        "input",
        "tool_input",
        "toolInput",
        "payload",
        "data",
    }
)
_MAX_PATH_RECURSION_DEPTH = 8

# Unified diff / V4A patch headers — only used as fallback when structured paths are absent.
_PATCH_DIFF_PATH_RE = re.compile(r"^\+\+\+\s+(?:b/)?([^\t\n\r]+)", re.MULTILINE)
_PATCH_V4A_FILE_RE = re.compile(
    r"^\*{3}\s*(?:Update|Add)\s+File:\s*(.+)$", re.MULTILINE | re.IGNORECASE
)
_PATCH_BLOB_MAX_SCAN = 65536
_PATCH_FALLBACK_TOOLS = frozenset({"apply_patch"})

_TS_PACKAGE_PREFIXES: tuple[tuple[str, str], ...] = (
    ("apps/client/", "apps/client/tsconfig.json"),
    ("apps/server/", "apps/server/tsconfig.json"),
)
_ROOT_TSCONFIG = "tsconfig.json"


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def get_tool_name(payload: dict) -> str:
    return payload.get("tool_name") or payload.get("tool") or ""


def normalize_tool_name(tool_name: str) -> str:
    if not isinstance(tool_name, str):
        return ""
    stripped = tool_name.strip()
    if not stripped:
        return ""
    lowered = stripped.replace("-", "_").replace(" ", "_")
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", lowered).lower()
    return snake


def is_write_tool(tool_name: str) -> bool:
    return normalize_tool_name(tool_name) in WRITE_TOOLS


def _coerce_tool_input_dict(payload: dict) -> dict:
    """Normalize tool_input / toolInput to a dict (JSON string allowed)."""
    raw = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return raw if isinstance(raw, dict) else {}


def _append_unique_path(files: list[str], candidate: str) -> None:
    text = candidate.strip()
    if text and text not in files:
        files.append(text)


def _collect_paths_from_mapping(obj: dict, files: list[str], depth_remaining: int) -> None:
    if depth_remaining < 0 or not isinstance(obj, dict):
        return
    for key in _PATH_SCALAR_KEYS:
        val = obj.get(key)
        if isinstance(val, str) and val.strip():
            _append_unique_path(files, val)
    for key in _LIST_PATH_KEYS:
        val = obj.get(key)
        if not isinstance(val, list):
            continue
        for item in val:
            if isinstance(item, str) and item.strip():
                _append_unique_path(files, item)
            elif isinstance(item, dict):
                _collect_paths_from_mapping(item, files, depth_remaining - 1)
    for key in _NEST_DICT_KEYS:
        nested = obj.get(key)
        if isinstance(nested, dict):
            _collect_paths_from_mapping(nested, files, depth_remaining - 1)


def _paths_from_patch_blob(text: str) -> list[str]:
    """Extract file paths from unified-diff or V4A-style patch text (bounded scan)."""
    if not isinstance(text, str) or not text.strip():
        return []
    chunk = text if len(text) <= _PATCH_BLOB_MAX_SCAN else text[:_PATCH_BLOB_MAX_SCAN]
    found: list[str] = []
    for pattern in (_PATCH_DIFF_PATH_RE, _PATCH_V4A_FILE_RE):
        for m in pattern.finditer(chunk):
            p = m.group(1).strip().strip('"')
            if p and p not in found:
                found.append(p)
    return found


def _maybe_collect_paths_from_tool_output_json(payload: dict, files: list[str]) -> None:
    """Some write tools echo the target path only in tool_output JSON."""
    for key in ("tool_output", "toolOutput"):
        raw = payload.get(key)
        if not isinstance(raw, str) or not raw.strip():
            continue
        head = raw.lstrip()
        if not head.startswith("{"):
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            _collect_paths_from_mapping(parsed, files, _MAX_PATH_RECURSION_DEPTH)


def get_changed_files(payload: dict) -> list[str]:
    """
    Extract changed file paths from the PostToolUse payload for lint targeting and MAO
    handoff detection. Covers common Cursor key variants, nested args, path lists, JSON
    tool_output echoes, and a narrow apply_patch diff-header fallback when no structured
    paths were found.
    """
    files: list[str] = []
    tool_input = _coerce_tool_input_dict(payload)
    _collect_paths_from_mapping(tool_input, files, _MAX_PATH_RECURSION_DEPTH)
    _maybe_collect_paths_from_tool_output_json(payload, files)

    tool_norm = normalize_tool_name(get_tool_name(payload))
    if not files and tool_norm in _PATCH_FALLBACK_TOOLS:
        for blob_key in ("patch", "diff", "unified_diff"):
            blob = tool_input.get(blob_key)
            if isinstance(blob, str):
                for p in _paths_from_patch_blob(blob):
                    _append_unique_path(files, p)

    return files


def post_tool_scoped_validate_enabled() -> bool:
    """Scoped PostToolUse lint/type-check (default on; set CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE=0 to disable)."""
    try:
        return mat_env_flag("CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE", default=True)
    except Exception:  # noqa: BLE001 — fail-open to env default
        raw = (os.environ.get("CURSOR_MAT_POST_TOOL_SCOPED_VALIDATE") or "1").strip().lower()
        return raw in {"1", "true", "yes", "on"}


def _normalize_repo_relative_path(path: str) -> str:
    text = path.strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _repo_relative_path(path: str) -> str | None:
    """Return a repo-relative path when `path` resolves under PROJECT_DIR."""
    if not isinstance(path, str) or not path.strip():
        return None
    project = os.path.normpath(PROJECT_DIR)
    candidate = path.strip()
    if os.path.isabs(candidate):
        abs_path = os.path.normpath(candidate)
    else:
        abs_path = os.path.normpath(os.path.join(project, _normalize_repo_relative_path(candidate)))
    if abs_path != project and not abs_path.startswith(project + os.sep):
        return None
    rel = os.path.relpath(abs_path, project).replace("\\", "/")
    if rel.startswith("../"):
        return None
    return rel


def _trusted_changed_files(changed_files: list[str]) -> list[str]:
    trusted: list[str] = []
    for raw in changed_files:
        rel = _repo_relative_path(raw)
        if rel is None:
            return []
        trusted.append(rel)
    return trusted


def should_use_broad_validation(changed_files: list[str]) -> bool:
    """True when scoped validators must fall back to project-wide commands."""
    if not post_tool_scoped_validate_enabled():
        return True
    if not changed_files:
        return True
    return not _trusted_changed_files(changed_files)


def scoped_python_targets(changed_files: list[str]) -> list[str] | None:
    """
    Return changed `.py` paths for scoped ruff/ty, or None to use project-wide checks.
    """
    if should_use_broad_validation(changed_files):
        return None
    trusted = _trusted_changed_files(changed_files)
    py_files = [f for f in trusted if f.endswith(".py")]
    if not py_files:
        return None
    return py_files


def resolve_typescript_validation_scope(
    changed_files: list[str],
) -> tuple[str | None, bool]:
    """
    Choose TypeScript validation scope.

    Returns `(tsconfig_relative, use_broad_fallback)`.
    When `use_broad_fallback` is True, run legacy project-root `tsc --noEmit`.
    When `tsconfig_relative` is set and broad is False, run `tsc --noEmit -p <path>`.
    When both are false/None, skip TS validation for this write (no TS files changed).
    """
    if should_use_broad_validation(changed_files):
        return None, True
    trusted = _trusted_changed_files(changed_files)
    ts_files = [f for f in trusted if f.endswith((".ts", ".tsx"))]
    if not ts_files:
        return None, False
    packages: set[str] = set()
    for path in ts_files:
        for prefix, _cfg in _TS_PACKAGE_PREFIXES:
            if path.startswith(prefix):
                packages.add(prefix)
                break
        else:
            packages.add("__root__")
    if len(packages) != 1:
        return None, True
    if "__root__" in packages:
        tsconfig_rel = _ROOT_TSCONFIG
    else:
        prefix = next(iter(packages))
        tsconfig_rel = dict(_TS_PACKAGE_PREFIXES)[prefix]
    if not os.path.isfile(os.path.join(PROJECT_DIR, tsconfig_rel)):
        return None, True
    return tsconfig_rel, False


def run_python_lint(scoped_py_files: list[str] | None = None) -> tuple[bool, str]:
    """Run ruff on scoped files or the whole project. Returns (passed, output)."""
    targets = scoped_py_files if scoped_py_files else ["."]
    try:
        result = subprocess.run(
            ["ruff", "check", *targets],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output
    except FileNotFoundError:
        return True, "(ruff not installed — skipped)"
    except subprocess.TimeoutExpired:
        return True, "(ruff timed out — skipped)"


def run_python_typecheck(scoped_py_files: list[str] | None = None) -> tuple[bool, str]:
    """Run ty or pyright on scoped files or the project. Returns (passed, output)."""
    for tool in ["ty", "pyright"]:
        try:
            if tool == "ty":
                cmd = ["ty", "check", *(scoped_py_files or ["."])]
            else:
                cmd = [tool, *(scoped_py_files or [])]
            result = subprocess.run(
                cmd,
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=60,
            )
            passed = result.returncode == 0
            return passed, result.stdout + result.stderr
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return True, f"({tool} timed out — skipped)"
    return True, "(no Python type-checker installed — skipped)"


def run_ts_typecheck(
    tsconfig_relative: str | None = None,
    *,
    broad_fallback: bool = False,
) -> tuple[bool, str]:
    """Run tsc --noEmit (optionally `-p` for a package tsconfig). Returns (passed, output)."""
    if broad_fallback or not tsconfig_relative:
        tsconfig = os.path.join(PROJECT_DIR, _ROOT_TSCONFIG)
        if not os.path.exists(tsconfig):
            return True, "(no tsconfig.json — skipped)"
        cmd = ["tsc", "--noEmit"]
    else:
        tsconfig = os.path.join(PROJECT_DIR, tsconfig_relative)
        if not os.path.exists(tsconfig):
            return True, f"(no {tsconfig_relative} — skipped)"
        cmd = ["tsc", "--noEmit", "-p", tsconfig_relative]
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except FileNotFoundError:
        return True, "(tsc not installed — skipped)"
    except subprocess.TimeoutExpired:
        return True, "(tsc timed out — skipped)"


def _maybe_refresh_mao_gate(payload: dict) -> None:
    """After MAO handoff writes, refresh artifacts/mao/gate.json (Phase 2 MAO slice)."""
    if _HOOKS_DIR not in sys.path:
        sys.path.insert(0, _HOOKS_DIR)
    try:
        from mao_gate import (
            mao_gate_enabled,
            maybe_hook_auto_capture_transition,
            touches_build_result,
            touches_current_plan,
            write_mao_downstream_readiness_artifact,
            write_mao_gate_for_project,
            write_verifier_autostart_intent_if_eligible,
        )
    except ImportError:
        return
    tool_name = get_tool_name(payload)
    if not is_write_tool(tool_name):
        return
    changed = get_changed_files(payload)
    if not (touches_current_plan(changed) or touches_build_result(changed)):
        return
    try:
        if mao_gate_enabled():
            write_mao_gate_for_project(PROJECT_DIR)
        else:
            write_mao_downstream_readiness_artifact(
                PROJECT_DIR, trigger="handoff_post_tool_use_gate_disabled"
            )
        # Opt-in: auto-capture + verifier intent (fail-open; after gate refresh).
        summary = maybe_hook_auto_capture_transition(PROJECT_DIR, changed)
        write_verifier_autostart_intent_if_eligible(PROJECT_DIR, summary)
    except Exception as exc:  # noqa: BLE001 — never block the agent
        print(f"[mao_gate] {exc}", file=sys.stderr)


def _maybe_append_loop_handoff_event(payload: dict) -> None:
    """Append loop policy handoff event (fail-open; CURSOR_MAT_LOOP_EVENTS=1)."""
    if _HOOKS_DIR not in sys.path:
        sys.path.insert(0, _HOOKS_DIR)
    try:
        from loop_events import append_loop_handoff_event
    except ImportError:
        return
    tool_name = get_tool_name(payload)
    if not is_write_tool(tool_name):
        return
    changed = get_changed_files(payload)
    try:
        append_loop_handoff_event(PROJECT_DIR, changed, trigger="post_tool_use")
    except Exception as exc:  # noqa: BLE001 — never block PostToolUse
        print(f"[loop_events] {exc}", file=sys.stderr)


def _maybe_record_mao_todo_write_observation(payload: dict) -> None:
    """Record MAO todo-write hook observation (fail-open; never blocks)."""
    if _HOOKS_DIR not in sys.path:
        sys.path.insert(0, _HOOKS_DIR)
    try:
        from mao_gate import record_mao_todo_write_post_tool_observation
    except ImportError:
        return
    try:
        record_mao_todo_write_post_tool_observation(PROJECT_DIR, payload)
    except Exception as exc:  # noqa: BLE001 — never block PostToolUse
        print(f"[mao_todo_write_obs] {exc}", file=sys.stderr)


def detect_project_type(files: list[str]) -> set[str]:
    """Determine which validators to run based on changed files."""
    types: set[str] = set()
    for f in files:
        if f.endswith(".py"):
            types.add("python")
        if f.endswith((".ts", ".tsx")):
            types.add("typescript")
    # Also detect by presence of config files in project root
    if not types:
        if any(
            os.path.exists(os.path.join(PROJECT_DIR, f))
            for f in ["setup.py", "pyproject.toml", "requirements.txt"]
        ):
            types.add("python")
        if os.path.exists(os.path.join(PROJECT_DIR, "tsconfig.json")):
            types.add("typescript")
    return types


def main(argv: list[str] | None = None) -> None:
    args = parse_contract_argv(argv)
    try:
        payload = read_payload()
        tool_name = get_tool_name(payload)
        changed_files = get_changed_files(payload)
        project_types = sorted(detect_project_type(changed_files))

        if args.dry_run:
            emit_contract_envelope(
                make_contract_envelope(
                    hook_event="PostToolUse",
                    script=SCRIPT_NAME,
                    kind="result",
                    message="Dry run: inspected payload without MAO writes or validators.",
                    details={
                        "tool_name": tool_name,
                        "is_write_tool": is_write_tool(tool_name),
                        "changed_files": changed_files,
                        "project_types": project_types,
                    },
                    retryable=False,
                    dry_run=True,
                )
            )
            sys.exit(0)

        _maybe_record_mao_todo_write_observation(payload)
        _maybe_refresh_mao_gate(payload)
        _maybe_append_loop_handoff_event(payload)

        # Only validate after file-writing tool calls
        if not is_write_tool(tool_name):
            sys.exit(0)

        failures = []
        py_scope = scoped_python_targets(changed_files)
        tsconfig_scope, ts_broad = resolve_typescript_validation_scope(changed_files)

        if "python" in project_types:
            lint_ok, lint_out = run_python_lint(py_scope)
            if lint_ok and "skipped" in lint_out.lower():
                reason = lint_out.strip().strip("()")
                print(
                    "[mat-quality-honesty] advisory: lint skipped "
                    f"({reason}); build-result should not claim real lint PASS "
                    "without noting skip",
                    file=sys.stderr,
                )
            if not lint_ok:
                failures.append(f"Ruff lint failed:\n{lint_out}")
            typecheck_ok, typecheck_out = run_python_typecheck(py_scope)
            if not typecheck_ok:
                failures.append(f"Python type-check failed:\n{typecheck_out}")

        if "typescript" in project_types:
            if ts_broad:
                ts_ok, ts_out = run_ts_typecheck(None, broad_fallback=True)
            elif tsconfig_scope:
                ts_ok, ts_out = run_ts_typecheck(tsconfig_scope, broad_fallback=False)
            else:
                ts_ok, ts_out = True, ""
            if not ts_ok:
                failures.append(f"TypeScript type-check failed:\n{ts_out}")

        if failures:
            for msg in failures:
                print(msg, file=sys.stderr)
            sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - hook must fail open on unexpected errors
        emit_contract_envelope(
            make_contract_envelope(
                hook_event="PostToolUse",
                script=SCRIPT_NAME,
                kind="error",
                message=f"post_tool_validate failed: {exc}",
                details={},
                retryable=True,
                dry_run=args.dry_run,
            ),
            stream=sys.stderr,
        )
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
