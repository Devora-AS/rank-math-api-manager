"""Read-only MAT Workflow MCP operator tool handlers (advisory JSON envelopes)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

TransitionName = Literal["plan_to_build", "build_to_validate"]
HandoffTarget = Literal["current_plan", "build_result", "verify_result"]

CANONICAL_HANDOFFS = [
    "docs/current-plan.md",
    "build-result.md",
    "verify-result.md",
]
PROTOCOL_DOC = "docs/reference/todo-orchestration.md"
SECURITY_DOC = "docs/security/mcp.md"

DOCTOR_PROFILES = frozenset(
    {
        "mcp",
        "mao",
        "plugin",
        "cost-hygiene",
        "loop-policy",
        "worktree",
        "verification-profile",
        "adoption",
        "commands",
    }
)

_STDOUT_CAP = 8192


def ensure_hooks_path(root: Path) -> None:
    hooks = root / ".cursor" / "hooks"
    scripts = root / ".cursor" / "scripts"
    for path in (hooks, scripts):
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def make_envelope(
    tool: str,
    root: Path,
    *,
    ok: bool,
    data: dict[str, Any],
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "authority": "advisory",
        "canonical_handoffs": list(CANONICAL_HANDOFFS),
        "protocol_doc": PROTOCOL_DOC,
        "security_doc": SECURITY_DOC,
        "tool": tool,
        "workspace_root": str(root.resolve()),
        "ok": ok,
        "data": data,
        "errors": errors or [],
    }


def _cap_text(text: str, limit: int = _STDOUT_CAP) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _run_subprocess(
    cmd: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    return proc.returncode, _cap_text(proc.stdout), _cap_text(proc.stderr)


def mao_transition_evaluate(root: Path, transition: str) -> dict[str, Any]:
    tool = "mao_transition_evaluate"
    errors: list[str] = []
    if transition not in ("plan_to_build", "build_to_validate"):
        return make_envelope(
            tool,
            root,
            ok=False,
            data={},
            errors=[f"invalid transition: {transition!r}"],
        )
    try:
        ensure_hooks_path(root)
        from mao_gate import (  # noqa: WPS433
            evaluate_build_to_validate_transition,
            evaluate_mao_parent_transition_bundle,
            evaluate_plan_to_build_transition,
        )

        if transition == "plan_to_build":
            decision = evaluate_plan_to_build_transition(root)
        else:
            decision = evaluate_build_to_validate_transition(root)
        bundle = evaluate_mao_parent_transition_bundle(root, transition)
        data = {
            "transition": transition,
            "decision": decision,
            "parent_transition_bundle": bundle,
            "human_summary": (
                "Advisory only — parent must run explicit transition checks per "
                f"{PROTOCOL_DOC}; MCP does not capture transition-events.jsonl."
            ),
            "capture_side_effects": False,
        }
        return make_envelope(tool, root, ok=True, data=data, errors=errors)
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        return make_envelope(tool, root, ok=False, data={"transition": transition}, errors=errors)


def mao_downstream_readiness(root: Path, interpret_edges: bool = True) -> dict[str, Any]:
    tool = "mao_downstream_readiness"
    try:
        ensure_hooks_path(root)
        from mao_gate import (  # noqa: WPS433
            evaluate_parent_downstream_readiness_advisory,
            interpret_unblock_semantic_for_parent,
        )

        out = evaluate_parent_downstream_readiness_advisory(root)
        if interpret_edges:
            live = out.get("live_snapshot") or {}
            edges: dict[str, Any] = {}
            for key in ("plan_to_build", "build_to_validate"):
                edge = live.get(key)
                if isinstance(edge, dict):
                    sem = str(edge.get("unblock_semantic") or "")
                    edges[key] = {
                        "edge_readiness": edge,
                        "interpretation": interpret_unblock_semantic_for_parent(sem),
                    }
            out = dict(out)
            out["unblock_semantic_interpretation"] = edges
        return make_envelope(tool, root, ok=True, data=out)
    except Exception as exc:  # noqa: BLE001
        return make_envelope(tool, root, ok=False, data={}, errors=[str(exc)])


def _doctor_mcp(root: Path) -> tuple[int, list[str]]:
    script = root / "scripts" / "mat_mcp_doctor.py"
    if not script.is_file():
        return 1, [f"missing {script.relative_to(root)}"]
    rc, out, err = _run_subprocess(
        [sys.executable, str(script), "--repo-root", str(root)],
        root,
    )
    lines = [line for line in (out + err).splitlines() if line.strip()]
    return rc, lines


def _doctor_profile_command(root: Path, profile: str) -> list[str] | None:
    py = sys.executable
    if profile == "mcp":
        return None
    if profile == "mao":
        return [py, str(root / "scripts" / "mao_artifact_status.py"), "--repo-root", str(root)]
    if profile == "adoption":
        return [py, str(root / "scripts" / "adoption" / "adoption_provenance.py"), str(root)]
    if profile == "commands":
        return [
            py,
            str(root / "scripts" / "generate-command-index.py"),
            "--print-primary",
            "--repo-root",
            str(root),
        ]
    if profile == "cost-hygiene":
        return [
            py,
            str(root / "scripts" / "validate_cost_context_hygiene_pack.py"),
            "--repo-root",
            str(root),
            "--report",
            "--no-fail",
        ]
    if profile == "verification-profile":
        return [py, str(root / "scripts" / "verification_profiles.py"), "default-profile", "--repo-root", str(root)]
    if profile == "worktree":
        return ["bash", str(root / "scripts" / "check-worktrees.sh")]
    if profile == "plugin":
        return ["bash", str(root / "scripts" / "doctor.sh"), "--plugin"]
    if profile == "loop-policy":
        return ["bash", str(root / "scripts" / "doctor.sh"), "--loop-policy"]
    return None


def mat_doctor_subset(root: Path, profile: str) -> dict[str, Any]:
    tool = "mat_doctor_subset"
    if profile not in DOCTOR_PROFILES:
        return make_envelope(
            tool,
            root,
            ok=False,
            data={"profile": profile, "allowed": sorted(DOCTOR_PROFILES)},
            errors=[f"unknown profile: {profile!r}"],
        )
    try:
        if profile == "mcp":
            exit_code, report = _doctor_mcp(root)
        else:
            cmd = _doctor_profile_command(root, profile)
            if cmd is None:
                return make_envelope(
                    tool,
                    root,
                    ok=False,
                    data={"profile": profile},
                    errors=["no command mapping for profile"],
                )
            exit_code, out, err = _run_subprocess(cmd, root)
            report = [line for line in (out + err).splitlines() if line.strip()]
        healthy = exit_code == 0
        return make_envelope(
            tool,
            root,
            ok=True,
            data={
                "profile": profile,
                "exit_code": exit_code,
                "healthy": healthy,
                "report": report,
                "disclaimer": "Doctor warnings do not imply MCP ok=False unless internal error.",
            },
        )
    except Exception as exc:  # noqa: BLE001
        return make_envelope(
            tool,
            root,
            ok=False,
            data={"profile": profile},
            errors=[str(exc)],
        )


def mat_worktree_check(root: Path, strict: bool = False) -> dict[str, Any]:
    tool = "mat_worktree_check"
    script = root / "scripts" / "check-worktrees.sh"
    if not script.is_file():
        return make_envelope(
            tool,
            root,
            ok=False,
            data={},
            errors=[f"missing {script.relative_to(root)}"],
        )
    cmd = ["bash", str(script)]
    if strict:
        cmd.append("--strict")
    try:
        exit_code, out, err = _run_subprocess(cmd, root)
        return make_envelope(
            tool,
            root,
            ok=True,
            data={
                "strict": strict,
                "exit_code": exit_code,
                "healthy": exit_code == 0,
                "stdout_tail": out,
                "stderr_tail": err,
            },
        )
    except Exception as exc:  # noqa: BLE001
        return make_envelope(tool, root, ok=False, data={"strict": strict}, errors=[str(exc)])


def _issues_from_contract(issues: tuple[Any, ...]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for issue in issues:
        code = getattr(issue, "code", "unknown")
        message = getattr(issue, "message", str(issue))
        rows.append({"severity": "error", "code": str(code), "message": str(message)})
    return rows


def mat_handoff_contract_check(
    root: Path,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    tool = "mat_handoff_contract_check"
    allowed = ("current_plan", "build_result", "verify_result")
    chosen = list(targets) if targets else list(allowed)
    invalid = [t for t in chosen if t not in allowed]
    if invalid:
        return make_envelope(
            tool,
            root,
            ok=False,
            data={},
            errors=[f"invalid targets: {invalid}"],
        )
    ensure_hooks_path(root)
    from artifact_contract import (  # noqa: WPS433
        env_loop_policy_enabled,
        inspect_build_result_contract,
        inspect_verify_result_contract,
    )
    from validate_artifacts import ValidationResult, validate_current_plan  # noqa: WPS433

    path_map = {
        "current_plan": root / "docs" / "current-plan.md",
        "build_result": root / "build-result.md",
        "verify_result": root / "verify-result.md",
    }
    per_file: dict[str, Any] = {}
    all_issues: list[dict[str, str]] = []
    loop_strict = env_loop_policy_enabled(root)

    for key in chosen:
        path = path_map[key]
        rel = path.relative_to(root).as_posix()
        if not path.is_file():
            per_file[key] = {
                "path": rel,
                "present": False,
                "structural_pass": False,
                "issues": [{"severity": "error", "file": rel, "code": "missing", "message": "file missing"}],
            }
            all_issues.extend(per_file[key]["issues"])
            continue
        text = path.read_text(encoding="utf-8")
        issues: list[dict[str, str]] = []
        if key == "current_plan":
            vr = ValidationResult()
            validate_current_plan(path, vr, require_closeout=False)
            for item in vr.issues:
                issues.append(
                    {
                        "severity": "error",
                        "file": rel,
                        "code": item.code,
                        "message": item.message,
                    }
                )
        elif key == "build_result":
            contract = inspect_build_result_contract(text, loop_policy_strict=loop_strict)
            for row in _issues_from_contract(contract.issues):
                row["file"] = rel
                issues.append(row)
        else:
            contract = inspect_verify_result_contract(text)
            for row in _issues_from_contract(contract.issues):
                row["file"] = rel
                issues.append(row)
        structural_pass = len(issues) == 0
        per_file[key] = {
            "path": rel,
            "present": True,
            "structural_pass": structural_pass,
            "issues": issues,
        }
        all_issues.extend(issues)

    return make_envelope(
        tool,
        root,
        ok=True,
        data={
            "files": per_file,
            "structural_pass_all": all(
                f.get("structural_pass") for f in per_file.values() if f.get("present")
            )
            and bool(per_file),
            "disclaimer": "Structural check only — not orchestration PASS; see canonical handoff files.",
            "issues": all_issues,
        },
    )


def mat_worktree_attribution(root: Path) -> dict[str, Any]:
    tool = "mat_worktree_attribution"
    try:
        hook_utils = root / ".cursor" / "hooks"
        if str(hook_utils) not in sys.path:
            sys.path.insert(0, str(hook_utils))
        from utils.worktree_attribution import classify_worktree_attribution  # noqa: WPS433

        payload = classify_worktree_attribution(root, changed_files=None, run_id=None)
        return make_envelope(tool, root, ok=True, data=payload)
    except Exception as exc:  # noqa: BLE001
        return make_envelope(tool, root, ok=False, data={}, errors=[str(exc)])


def _loop_policy_enabled(root: Path) -> bool:
    ensure_hooks_path(root)
    from artifact_contract import env_loop_policy_enabled  # noqa: WPS433

    return env_loop_policy_enabled(root)


def mat_loop_policy_evaluate(
    root: Path,
    manifest_path: str | None = None,
    event_path: str | None = None,
) -> dict[str, Any]:
    tool = "mat_loop_policy_evaluate"
    if not _loop_policy_enabled(root):
        return make_envelope(
            tool,
            root,
            ok=True,
            data={
                "skipped": True,
                "reason": "CURSOR_MAT_LOOP_POLICY is not enabled",
            },
        )
    manifest = Path(manifest_path) if manifest_path else root / "artifacts" / "loop" / "manifest.json"
    if not manifest.is_file():
        return make_envelope(
            tool,
            root,
            ok=True,
            data={
                "skipped": True,
                "reason": f"manifest missing: {manifest.relative_to(root) if manifest.is_relative_to(root) else manifest}",
            },
        )
    try:
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        if event_path:
            event = json.loads(Path(event_path).read_text(encoding="utf-8"))
        else:
            event = {"kind": "mcp_probe", "source": "mat_loop_policy_evaluate"}
        policy_script = root / "scripts" / "mat_loop_policy.py"
        spec = importlib.util.spec_from_file_location("mat_loop_policy_mcp", policy_script)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load mat_loop_policy.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.evaluate(manifest_data, event)
        return make_envelope(
            tool,
            root,
            ok=True,
            data={
                "skipped": False,
                "manifest_path": str(manifest.resolve()),
                "evaluate_result": result,
            },
        )
    except Exception as exc:  # noqa: BLE001
        return make_envelope(tool, root, ok=False, data={}, errors=[str(exc)])
