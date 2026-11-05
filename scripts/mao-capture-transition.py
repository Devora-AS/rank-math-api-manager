#!/usr/bin/env python3
"""
Run a parent-owned MAO transition capture from the repo root (CLI helper).

Evaluates the transition, appends `artifacts/mao/transition-events.jsonl`, overwrites
`artifacts/mao/suggested-todo-mutation.json` when append succeeds, and prints JSON
with `todo_mutations` for the parent to apply via Cursor `TodoWrite`.

Optional `--with-downstream-readiness` embeds `evaluate_parent_downstream_readiness_advisory()`
inside `parent_transition_bundle` (live vs on-disk readiness trust bundle).

`--bundle-only` prints `evaluate_mao_parent_transition_bundle()` without appending
transition-events or suggested-todo-mutation files.

`--show-hook-flags` prints whether hook automation env toggles are enabled (no transition arg).

Does not call TodoWrite or spawn subagents.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "hooks"))

from mao_gate import (  # noqa: E402
    capture_transition_decision,
    evaluate_mao_parent_transition_bundle,
    mao_gate_enabled,
    mao_hook_auto_transition_capture_enabled,
    mao_verifier_autostart_enabled,
    mao_verifier_autostart_require_todo_observation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "transition",
        nargs="?",
        choices=("plan_to_build", "build_to_validate"),
        default=None,
        help="MAO transition to capture (omit with --show-hook-flags)",
    )
    parser.add_argument(
        "--show-hook-flags",
        action="store_true",
        help="Print hook automation env toggles (CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE, "
        "VERIFIER_AUTOSTART, etc.) and exit",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--emit-observability",
        action="store_true",
        help="Attempt fail-open POST to observability API (same as Python API flag)",
    )
    parser.add_argument(
        "--with-downstream-readiness",
        action="store_true",
        help="Include evaluate_parent_downstream_readiness_advisory() in printed JSON",
    )
    parser.add_argument(
        "--bundle-only",
        action="store_true",
        help="Do not append transition-events or suggested file; print parent bundle only",
    )
    args = parser.parse_args()
    root = args.repo.resolve()
    dr_adv = args.with_downstream_readiness

    if args.show_hook_flags:
        print(
            json.dumps(
                {
                    "CURSOR_MAO_GATE_enabled": mao_gate_enabled(),
                    "CURSOR_MAO_HOOK_AUTO_TRANSITION_CAPTURE": (
                        mao_hook_auto_transition_capture_enabled()
                    ),
                    "CURSOR_MAO_VERIFIER_AUTOSTART": mao_verifier_autostart_enabled(),
                    "CURSOR_MAO_VERIFIER_AUTOSTART_REQUIRE_TODO_OBSERVATION": (
                        mao_verifier_autostart_require_todo_observation()
                    ),
                },
                indent=2,
            )
        )
        return 0

    if args.transition is None:
        parser.error("transition is required unless --show-hook-flags is set")

    if args.bundle_only:
        bundle = evaluate_mao_parent_transition_bundle(
            root,
            args.transition,
            include_downstream_readiness_advisory=dr_adv,
        )
        print(json.dumps(bundle, indent=2, default=str))
        return 0

    result = capture_transition_decision(
        root,
        args.transition,
        emit_observability=args.emit_observability,
    )
    bundle = evaluate_mao_parent_transition_bundle(
        root,
        args.transition,
        include_downstream_readiness_advisory=dr_adv,
    )
    summary = {
        "transition": args.transition,
        "allowed": result["event"]["allowed"],
        "todo_mutations": result["todo_mutations"],
        "todo_mutations_applicable": result["event"]["todo_mutations_applicable"],
        "todo_mutations_blocked_reasons": result["event"]["todo_mutations_blocked_reasons"],
        "artifact_written": result["artifact_written"],
        "suggested_todo_mutation_path": result["suggested_todo_mutation_path"],
        "decision_mode": result["decision"]["decision_mode"],
        "parent_transition_bundle": bundle,
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
