#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  bootstrap-workflow-into-repo.sh [--mode new-project|existing-project] [--non-interactive] [--inline-fallback] <destination-repo>

  --inline-fallback   Write the explicit inline MAT fallback block instead of the default pointer note.

Environment:
  MULTI_AGENT_WORKFLOW_ROOT   Optional source repo root. Defaults to the repo that contains this script.
EOF
}

MODE="existing-project"
NON_INTERACTIVE=0
INLINE_FALLBACK=0

while [ $# -gt 0 ]; do
  case "$1" in
    --mode)
      shift
      MODE="${1:-}"
      ;;
    --mode=*)
      MODE="${1#--mode=}"
      ;;
    --non-interactive)
      NON_INTERACTIVE=1
      ;;
    --inline-fallback|--merge-agents)
      INLINE_FALLBACK=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --*)
      echo "bootstrap-workflow-into-repo: unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      break
      ;;
  esac
  shift
done

if [ $# -ne 1 ]; then
  usage
  exit 2
fi

case "$MODE" in
  new-project|existing-project) ;;
  *)
    echo "bootstrap-workflow-into-repo: unsupported mode '$MODE'" >&2
    exit 2
    ;;
esac

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_ROOT="${MULTI_AGENT_WORKFLOW_ROOT:-$SCRIPT_ROOT}"
DEST_INPUT="$1"
LAYOUT_JSON="$SOURCE_ROOT/scripts/adoption/adoption-layout-v1.json"

if [ ! -f "$LAYOUT_JSON" ]; then
  echo "bootstrap-workflow-into-repo: missing layout contract: $LAYOUT_JSON" >&2
  exit 2
fi

if [ ! -f "$SOURCE_ROOT/AGENTS.md" ] || [ ! -d "$SOURCE_ROOT/.cursor" ]; then
  echo "bootstrap-workflow-into-repo: invalid workflow source: $SOURCE_ROOT" >&2
  exit 2
fi

mkdir -p "$DEST_INPUT"
DEST_ROOT="$(cd "$DEST_INPUT" && pwd)"

copy_source_to_dest() {
  local rel_src="$1"
  local rel_dest="$2"
  mkdir -p "$DEST_ROOT/$(dirname "$rel_dest")"
  cp "$SOURCE_ROOT/$rel_src" "$DEST_ROOT/$rel_dest"
}

copy_dir_contents() {
  local rel_dir="$1"
  mkdir -p "$DEST_ROOT/$rel_dir"
  cp -R "$SOURCE_ROOT/$rel_dir/." "$DEST_ROOT/$rel_dir/"
}

install_template_if_missing() {
  local template_rel="$1"
  local target_rel="$2"
  if [ -e "$DEST_ROOT/$target_rel" ]; then
    echo "bootstrap-workflow-into-repo: preserving existing $target_rel"
    return 0
  fi
  mkdir -p "$DEST_ROOT/$(dirname "$target_rel")"
  cp "$SOURCE_ROOT/$template_rel" "$DEST_ROOT/$target_rel"
  echo "bootstrap-workflow-into-repo: created $target_rel"
}

write_mat_readme() {
  mkdir -p "$DEST_ROOT/.mat"
  cat <<'EOF' >"$DEST_ROOT/.mat/README.md"
# `.mat/` — Multi-agent workflow (MAT) sidecar

This directory holds **MAT-packaged** material for this repository: reference documentation and workflow contract tests copied from the MAT source repo. It keeps product documentation at the repo root separate from workflow manuals.

- **`.mat/docs/`** — packaged workflow documentation (components, getting started, MAO protocol, [workflow-artifact-contract.md](docs/workflow-artifact-contract.md) for `build-result.md` / `verify-result.md` section contracts, etc.).
- **`.mat/tests/`** — workflow contract tests (`unittest`); run with `python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v`.
- **`.mat/AGENTS.mat.md`** — full MAT operator reference from the source `AGENTS.md`.
- **`.mat/vendor/README-MAT.md`** — optional attribution copy of the MAT source `README.md`.

Entrypoints at repo root: **`scripts/phase1-verify.sh`**, **`.cursor/`** (hooks, commands, agents).

`phase1-verify.sh` detects this sidecar (presence of this file) and then: validates workflow markdown with **optional** `build-result.md` / `verify-result.md` when those handoffs are absent, skips closeout posture checks until `artifacts/agent-traces/comparison.json` exists, runs **`python3 -m unittest discover -s .mat/tests`** (not the product’s `tests/` tree), and skips the Bun observability smoke when `apps/server` is not packaged.

For product narrative, use the root **`README.md`** and your application docs — not this tree.
EOF
}

# --- Layout-driven copies (single source of truth: adoption-layout-v1.json) ---

python3 - "$LAYOUT_JSON" "$SOURCE_ROOT" "$DEST_ROOT" <<'PY'
import json
import pathlib
import shutil
import sys

layout_path, source_root, dest_root = sys.argv[1:4]
layout = json.loads(pathlib.Path(layout_path).read_text(encoding="utf-8"))
src = pathlib.Path(source_root)
dst = pathlib.Path(dest_root)

for item in layout["mat_docs"]:
    s, d = item["src"], item["dest"]
    pathlib.Path(dst / d).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / s, dst / d)
    print(f"bootstrap-workflow-into-repo: copied {s} -> {d}")

for rel in layout["mat_tests"]:
    dest = pathlib.Path(".mat/tests") / pathlib.Path(rel).name
    pathlib.Path(dst / dest).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / rel, dst / dest)
    print(f"bootstrap-workflow-into-repo: copied {rel} -> {dest}")

pathlib.Path(dst / ".mat/vendor").mkdir(parents=True, exist_ok=True)
vendor_src = layout.get("source_readme_for_vendor", "README.md")
vendor_dest = layout["mat_sidecar"]["vendor_readme_mat"]
shutil.copy2(src / vendor_src, dst / vendor_dest)
print(f"bootstrap-workflow-into-repo: copied {vendor_src} -> {vendor_dest}")

agents_mat = layout["mat_sidecar"]["agents_mat"]
shutil.copy2(src / layout["source_agents_for_mat"], dst / agents_mat)
print(f"bootstrap-workflow-into-repo: wrote {agents_mat} from {layout['source_agents_for_mat']}")
PY

write_mat_readme

for rel_dir in $(
  python3 -c "import json, pathlib; l=json.load(open(pathlib.Path('$LAYOUT_JSON'))); print(' '.join(l['cursor_copy']['dir_contents']))"
); do
  copy_dir_contents "$rel_dir"
done

for rel_path in $(
  python3 -c "import json, pathlib; l=json.load(open(pathlib.Path('$LAYOUT_JSON'))); print(' '.join(l['cursor_copy']['files']))"
); do
  copy_source_to_dest "$rel_path" "$rel_path"
done

# Point copied `.cursor/` prompts at the packaged contract under `.mat/docs/` when root `docs/` is minimal.
python3 - "$DEST_ROOT" <<'PY'
from __future__ import annotations

import pathlib
import re
import sys

dest_root = pathlib.Path(sys.argv[1]).resolve()
cursor_root = dest_root / ".cursor"
if not cursor_root.is_dir():
    raise SystemExit(0)

_STANDALONE_ROOT_DOCS = re.compile(
    r"(?<!\.mat/)docs/workflow-artifact-contract\.md"
)


def rewrite_text(text: str) -> str:
    text = text.replace(
        "../../docs/workflow-artifact-contract.md",
        "../../.mat/docs/workflow-artifact-contract.md",
    )
    text = _STANDALONE_ROOT_DOCS.sub(
        ".mat/docs/workflow-artifact-contract.md",
        text,
    )
    return text

changed = 0
for path in sorted(cursor_root.rglob("*")):
    if not path.is_file():
        continue
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue
    new = rewrite_text(raw)
    if new != raw:
        path.write_text(new, encoding="utf-8")
        changed += 1
print(f"bootstrap-workflow-into-repo: rewrote workflow-artifact-contract paths in {changed} files under .cursor/")
PY

for rel_path in $(
  python3 -c "import json, pathlib; l=json.load(open(pathlib.Path('$LAYOUT_JSON'))); print(' '.join(l['root_scripts_copy']))"
); do
  copy_source_to_dest "$rel_path" "$rel_path"
done

copy_dir_contents "$(
  python3 -c "import json, pathlib; print(json.load(open(pathlib.Path('$LAYOUT_JSON')))['scripts_lib_dir'])"
)"

copy_source_to_dest ".env.sample" ".env.sample"

# Root handoff templates (minimal workflow contract only at docs/)
# (Must not use a shell pipeline here: install_template_if_missing is a bash function and is not
# available in the subshell spawned by `|`.)
python3 - "$LAYOUT_JSON" "$SOURCE_ROOT" "$DEST_ROOT" <<'PY'
import json
import pathlib
import shutil
import sys

layout_path, source_root, dest_root = sys.argv[1:4]
layout = json.loads(pathlib.Path(layout_path).read_text(encoding="utf-8"))
src = pathlib.Path(source_root)
dst = pathlib.Path(dest_root)
t = layout["templates"]
x = layout["template_install_targets"]
for key in ("minimal_current_plan", "minimal_long_run_state"):
    rel_t = t[key]
    rel_target = x[key]
    target = dst / rel_target
    if target.exists():
        print(f"bootstrap-workflow-into-repo: preserving existing {rel_target}")
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / rel_t, target)
    print(f"bootstrap-workflow-into-repo: created {rel_target}")
PY

python3 "$SOURCE_ROOT/scripts/adoption/apply_cost_hygiene_bootstrap.py" \
  --source "$SOURCE_ROOT" \
  --dest "$DEST_ROOT" \
  --mode "$MODE" \
  --layout "$LAYOUT_JSON"

# Product-first README stub when missing (never MAT marketing README at root)
install_template_if_missing "$(
  python3 -c "import json, pathlib; print(json.load(open(pathlib.Path('$LAYOUT_JSON')))['templates']['product_readme_stub'])"
)" "README.md"

# Root AGENTS.md: product-first template when missing; never overwrite existing in existing-project
PRODUCT_AGENTS="$(
  python3 -c "import json, pathlib; print(json.load(open(pathlib.Path('$LAYOUT_JSON')))['templates']['agents_product_first'])"
)"

if [ ! -f "$DEST_ROOT/AGENTS.md" ]; then
  mkdir -p "$DEST_ROOT"
  cp "$SOURCE_ROOT/$PRODUCT_AGENTS" "$DEST_ROOT/AGENTS.md"
  echo "bootstrap-workflow-into-repo: created AGENTS.md from product-first template"
else
  echo "bootstrap-workflow-into-repo: preserving existing AGENTS.md"
fi

HELPER_ARGS=(--repo-root "$DEST_ROOT")
if [ "$INLINE_FALLBACK" = "1" ]; then
  HELPER_ARGS+=(--inline-fallback)
fi
python3 "$SOURCE_ROOT/scripts/adoption/manage-agents-sidecars.py" "${HELPER_ARGS[@]}"

python3 "$SOURCE_ROOT/scripts/adoption/apply_mat_legacy_cleanup.py" \
  --repo-root "$DEST_ROOT" \
  --manifest "$DEST_ROOT/scripts/adoption/mat-legacy-migrations-v1.json" \
  --footprint "$DEST_ROOT/scripts/adoption/mat-footprint-v1.json" \
  --audit-dir artifacts/update-mat

chmod +x \
  "$DEST_ROOT/scripts/phase1-verify.sh" \
  "$DEST_ROOT/scripts/start-system.sh" \
  "$DEST_ROOT/scripts/parallelism-gate.sh" \
  "$DEST_ROOT/scripts/check-worktrees.sh" \
  "$DEST_ROOT/scripts/doctor.sh" \
  "$DEST_ROOT/scripts/setup-dev.sh" \
  "$DEST_ROOT/.cursor/hooks/bootstrap_worktree.sh"

chmod +x "$DEST_ROOT/scripts/adoption/migrate-long-run-state.py"
chmod +x "$DEST_ROOT/scripts/adoption/bootstrap-workflow-into-repo.sh"
chmod +x "$DEST_ROOT/scripts/adoption/apply_mat_legacy_cleanup.py"
chmod +x "$DEST_ROOT/scripts/adoption/mat-legacy-fingerprints.py"
chmod +x "$DEST_ROOT/scripts/adoption/apply_cost_hygiene_bootstrap.py"
chmod +x "$DEST_ROOT/scripts/adoption/detect_cost_hygiene_template.py"

echo "bootstrap-workflow-into-repo: source=$SOURCE_ROOT"
echo "bootstrap-workflow-into-repo: destination=$DEST_ROOT"
echo "bootstrap-workflow-into-repo: mode=$MODE"
if [ "$NON_INTERACTIVE" = "1" ]; then
  echo "bootstrap-workflow-into-repo: non-interactive=yes"
fi
if [ "$INLINE_FALLBACK" = "1" ]; then
  echo "bootstrap-workflow-into-repo: inline-fallback=yes"
fi
