#!/usr/bin/env python3
"""
Evaluate verifier autostart intent (advisory) and optionally delete when consumable.

Reads ``evaluate_verifier_autostart_intent()`` from mao_gate.py. Does not call TodoWrite
or spawn agents. Exit code is always 0 when the script completes (including when the
intent is absent or not consumable).

Destructive ``--delete-if-consumable`` requires environment variable
``CURSOR_MAO_PARENT_CONSUME_VERIFIER_INTENT_OK`` set to exactly ``1`` (ASCII; no other
value enables delete). If unset or any other value, delete is refused.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "hooks"))

from mao_gate import (  # noqa: E402
    delete_verifier_autostart_intent,
    evaluate_verifier_autostart_intent,
)

_PARENT_CONSUME_ENV = "CURSOR_MAO_PARENT_CONSUME_VERIFIER_INTENT_OK"


def _human_summary(ev: dict) -> str:
    lines = [
        f"consumable: {ev.get('consumable')}",
        f"intent_present: {ev.get('intent_present')}",
        f"parse_ok: {ev.get('parse_ok')}",
        f"intent_path: {ev.get('intent_path')}",
        f"repo_root_resolved: {ev.get('repo_root_resolved')}",
        f"repo_root_matches: {ev.get('repo_root_matches')}",
        f"plan_mtime_matches: {ev.get('plan_mtime_matches')}",
        f"build_mtime_matches: {ev.get('build_mtime_matches')}",
        f"blocked_reasons: {ev.get('blocked_reasons')}",
        "",
        "operator_summary:",
        str(ev.get("operator_summary") or ""),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full evaluation JSON",
    )
    parser.add_argument(
        "--delete-if-consumable",
        action="store_true",
        help=(
            f"Remove intent file only when consumable and {_PARENT_CONSUME_ENV}=1 "
            "(exactly); otherwise refuse delete"
        ),
    )
    args = parser.parse_args()
    root = args.repo.resolve()
    ev = evaluate_verifier_autostart_intent(root)

    if args.delete_if_consumable:
        flag = os.environ.get(_PARENT_CONSUME_ENV)
        if flag != "1":
            msg = (
                f"refused delete: {_PARENT_CONSUME_ENV} must be exactly '1' "
                f"(got {flag!r}); intent file left untouched"
            )
            print(msg, file=sys.stderr)
        elif not ev.get("consumable"):
            print(
                "refused delete: intent not consumable; file left untouched",
                file=sys.stderr,
            )
        else:
            removed = delete_verifier_autostart_intent(root)
            print(
                "deleted verifier-autostart-intent.json"
                if removed
                else "delete skipped (file already absent)",
                file=sys.stderr,
            )

    if args.json:
        print(json.dumps(ev, indent=2, default=str))
    else:
        sys.stdout.write(_human_summary(ev))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
