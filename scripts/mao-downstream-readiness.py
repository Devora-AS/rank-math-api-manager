#!/usr/bin/env python3
"""
Print parent-oriented downstream readiness advisory JSON (repo root).

Wraps evaluate_parent_downstream_readiness_advisory() in mao_gate.py: includes a live
recompute, optional on-disk artifact comparison, trusted_snapshot_for_hint, and
interpretation. Does not call TodoWrite or spawn agents.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "hooks"))

from mao_gate import (  # noqa: E402
    evaluate_parent_downstream_readiness_advisory,
    interpret_unblock_semantic_for_parent,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--interpret-edges",
        action="store_true",
        help="Add unblock_semantic_interpretation for each edge in live_snapshot",
    )
    args = parser.parse_args()
    root = args.repo.resolve()
    out = evaluate_parent_downstream_readiness_advisory(root)
    if args.interpret_edges:
        live = out.get("live_snapshot") or {}
        edges: dict[str, object] = {}
        for key in ("plan_to_build", "build_to_validate"):
            edge = live.get(key)
            if isinstance(edge, dict):
                sem = str(edge.get("unblock_semantic") or "")
                edges[key] = {
                    "edge_readiness": edge,
                    "unblock_semantic_interpretation": interpret_unblock_semantic_for_parent(sem),
                }
            else:
                edges[key] = {"edge_readiness": edge, "unblock_semantic_interpretation": None}
        out = dict(out)
        out["edge_unblock_interpretations"] = edges
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
