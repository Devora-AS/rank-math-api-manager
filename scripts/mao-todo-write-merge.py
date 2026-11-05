#!/usr/bin/env python3
"""
Merge MAO todo_mutations into a Cursor-style todo list (stdin JSON).

Reads JSON from stdin with shape:
  { "todos": [ { "id": "...", "content": "[mao:plan] ...", "status": "..." }, ... ],
    "todo_mutations": { "[mao:plan]": "completed", ... }   # optional if --from-suggested
  }

With --from-suggested, loads todo_mutations from artifacts/mao/suggested-todo-mutation.json
(relative to --repo). Fails if that file is missing or todo_mutations is empty unless
--allow-empty-mutations.

Prints JSON: { "todos": [...], "validation_ok", "validation_errors", "todo_mutations_used" }.

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
    apply_parent_todo_mutations_to_cursor_todos,
    validate_mao_todo_mutations_against_todos,
)


def _load_suggested_mutations(repo: Path) -> dict[str, str]:
    path = repo / "artifacts" / "mao" / "suggested-todo-mutation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    raw = data.get("todo_mutations") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--from-suggested",
        action="store_true",
        help="Load todo_mutations from artifacts/mao/suggested-todo-mutation.json",
    )
    parser.add_argument(
        "--allow-empty-mutations",
        action="store_true",
        help="Do not error when todo_mutations is empty (still validates as ok)",
    )
    args = parser.parse_args()
    repo = args.repo.resolve()

    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        print(json.dumps({"error": "stdin_must_be_json_object"}), file=sys.stderr)
        return 2
    todos = payload.get("todos")
    if not isinstance(todos, list):
        print(json.dumps({"error": "missing_or_invalid_todos_array"}), file=sys.stderr)
        return 2

    mutations: dict[str, str]
    if args.from_suggested:
        try:
            mutations = _load_suggested_mutations(repo)
        except (OSError, json.JSONDecodeError) as e:
            print(json.dumps({"error": "suggested_file_unreadable", "detail": str(e)}), file=sys.stderr)
            return 1
    else:
        m = payload.get("todo_mutations")
        if m is None:
            print(
                json.dumps({"error": "todo_mutations_required_unless_from_suggested"}),
                file=sys.stderr,
            )
            return 2
        if not isinstance(m, dict):
            print(json.dumps({"error": "todo_mutations_must_be_object"}), file=sys.stderr)
            return 2
        mutations = {str(k): str(v) for k, v in m.items()}

    if not mutations and not args.allow_empty_mutations and args.from_suggested:
        print(json.dumps({"error": "empty_todo_mutations_in_suggested"}), file=sys.stderr)
        return 1

    ok, errors = validate_mao_todo_mutations_against_todos(todos, mutations)
    merged = apply_parent_todo_mutations_to_cursor_todos(todos, mutations)
    out = {
        "todos": merged,
        "validation_ok": ok,
        "validation_errors": errors,
        "todo_mutations_used": mutations,
    }
    print(json.dumps(out, indent=2))
    return 0 if ok or not mutations else 1


if __name__ == "__main__":
    raise SystemExit(main())
