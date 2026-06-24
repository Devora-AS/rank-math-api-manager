#!/usr/bin/env python3
"""Cost hygiene cursorignore + adoption sidecar: called from bootstrap-workflow-into-repo.sh."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow `python3 scripts/adoption/apply_cost_hygiene_bootstrap.py` from repo root
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from detect_cost_hygiene_template import detect_cursorignore_template_key  # noqa: E402


def _load_layout(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _template_src_for_key(layout: dict[str, Any], key: str) -> str:
    t = layout["cursorignore_template_map"]
    if key not in t:
        raise KeyError(f"unknown template key {key!r} (valid: {sorted(t)!r})")
    return t[key]


def _append_telemetry(dest_root: Path, payload: dict[str, Any]) -> None:
    outdir = dest_root / "artifacts" / "cost-hygiene"
    outdir.mkdir(parents=True, exist_ok=True)
    line = {**payload, "ts_utc": datetime.now(timezone.utc).isoformat()}
    with (outdir / "bootstrap-events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def apply(
    *,
    source_root: Path,
    dest_root: Path,
    mode: str,
    layout_path: Path,
) -> int:
    layout = _load_layout(layout_path)
    src_root = source_root.resolve()
    dest_root = dest_root.resolve()
    det = detect_cursorignore_template_key(dest_root)
    key = det.key
    template_rel = _template_src_for_key(layout, key)
    mat_docs = dest_root / ".mat" / "docs" / "templates"
    mat_docs.mkdir(parents=True, exist_ok=True)

    for _tkey, rel in layout["cursorignore_template_map"].items():
        s = src_root / rel
        d = mat_docs / Path(rel).name
        if not s.is_file():
            print(f"apply_cost_hygiene_bootstrap: missing source template {s}", file=sys.stderr)
            return 1
        shutil.copy2(s, d)
        print(f"bootstrap-workflow-into-repo: copied {rel} -> .mat/docs/templates/{d.name}")

    if layout.get("cursorignore_adoption_schema"):
        sch = src_root / layout["cursorignore_adoption_schema"]
        if sch.is_file():
            dest_sch = mat_docs / sch.name
            shutil.copy2(sch, dest_sch)
            rel_p = sch.relative_to(src_root)
            print(
                f"bootstrap-workflow-into-repo: copied {rel_p} -> "
                f"{dest_sch.relative_to(dest_root)}"
            )

    ignore_path = dest_root / ".cursorignore"
    root_existed = ignore_path.is_file()
    sidecar_suggest = True

    if mode == "new-project":
        enforcement = "strict"
        if root_existed:
            preserve = True
            print("bootstrap-workflow-into-repo: preserving existing .cursorignore (new-project)")
        else:
            preserve = False
            tpl = src_root / template_rel
            shutil.copy2(tpl, ignore_path)
            print(
                f"bootstrap-workflow-into-repo: created .cursorignore from {template_rel} (key={key})"
            )
    else:
        enforcement = "warn_first"
        if root_existed:
            preserve = True
            print("bootstrap-workflow-into-repo: preserving existing .cursorignore (existing-project)")
        else:
            preserve = False
            tpl = src_root / template_rel
            shutil.copy2(tpl, ignore_path)
            print(
                f"bootstrap-workflow-into-repo: created .cursorignore from {template_rel} "
                f"(key={key}, existing-project — root was absent)"
            )

    suggest_name = f"cursorignore-mat-{key}.mat-suggest"
    s_src = src_root / template_rel
    s_dest = mat_docs / suggest_name
    shutil.copy2(s_src, s_dest)
    print(f"bootstrap-workflow-into-repo: wrote {s_dest.relative_to(dest_root)}")

    adoption: dict[str, Any] = {
        "schema_version": 1,
        "bootstrap_mode": mode,
        "enforcement": enforcement,
        "selected_template": key,
        "detection_reason": det.reason,
        "detection_signals": det.signals,
        "sidecar_suggest_writable": sidecar_suggest,
        "root_cursorignore_preserved": preserve,
        "root_cursorignore_created": bool(not root_existed and ignore_path.is_file()),
    }
    (dest_root / ".mat").mkdir(parents=True, exist_ok=True)
    adoption_path = dest_root / ".mat" / "cost-hygiene-adoption.json"
    adoption_path.write_text(
        json.dumps(adoption, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"bootstrap-workflow-into-repo: wrote {adoption_path.relative_to(dest_root)}")

    _append_telemetry(
        dest_root,
        {
            "event": "cost_hygiene_bootstrap",
            "template_key": key,
            "enforcement": enforcement,
            "mode": mode,
        },
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--dest", type=Path, required=True)
    p.add_argument(
        "--mode", choices=("new-project", "existing-project"), required=True
    )
    p.add_argument(
        "--layout",
        type=Path,
        help="Path to adoption-layout-v1.json (default: <source>/scripts/adoption/...)",
    )
    args = p.parse_args()
    src = args.source.resolve()
    dst = args.dest.resolve()
    layout_path = args.layout
    if layout_path is None:
        layout_path = src / "scripts" / "adoption" / "adoption-layout-v1.json"
    else:
        layout_path = args.layout.resolve()
    if not layout_path.is_file():
        print(f"apply_cost_hygiene_bootstrap: layout not found: {layout_path}", file=sys.stderr)
        return 2
    if not src.is_dir() or not dst.is_dir():
        print("apply_cost_hygiene_bootstrap: invalid --source or --dest", file=sys.stderr)
        return 2
    return apply(source_root=src, dest_root=dst, mode=args.mode, layout_path=layout_path)


if __name__ == "__main__":
    raise SystemExit(main())
