#!/usr/bin/env bash
# Operator diagnostics for local workflow readiness.
set -euo pipefail

RUN_FULL=0
COST_HYGIENE=0
LEGACY_CLEANUP_REPORT=0
LOOP_POLICY=0
QUALITY_COMMANDS=0
RESEARCH_SKILLS=0
RULES_PRECEDENCE=0
VERIFICATION_PROFILE=0
ADOPTION=0
MAO_ARTIFACTS=0
COMMANDS=0
RUN_MANIFEST=0
PLUGIN=0
MCP=0
if [ "${1:-}" = "--full" ]; then
  RUN_FULL=1
elif [ "${1:-}" = "--cost-hygiene" ] || [ "${1:-}" = "cost-hygiene" ]; then
  COST_HYGIENE=1
elif [ "${1:-}" = "--legacy-cleanup" ] || [ "${1:-}" = "legacy-cleanup" ]; then
  LEGACY_CLEANUP_REPORT=1
elif [ "${1:-}" = "--loop-policy" ] || [ "${1:-}" = "loop-policy" ]; then
  LOOP_POLICY=1
elif [ "${1:-}" = "--quality-commands" ] || [ "${1:-}" = "quality-commands" ]; then
  QUALITY_COMMANDS=1
elif [ "${1:-}" = "--research-skills" ] || [ "${1:-}" = "research-skills" ]; then
  RESEARCH_SKILLS=1
elif [ "${1:-}" = "--rules-precedence" ] || [ "${1:-}" = "rules-precedence" ]; then
  RULES_PRECEDENCE=1
elif [ "${1:-}" = "--verification-profile" ] || [ "${1:-}" = "verification-profile" ]; then
  VERIFICATION_PROFILE=1
elif [ "${1:-}" = "--adoption" ] || [ "${1:-}" = "adoption" ]; then
  ADOPTION=1
elif [ "${1:-}" = "--mao" ] || [ "${1:-}" = "mao" ] || [ "${1:-}" = "--mao-artifacts" ]; then
  MAO_ARTIFACTS=1
elif [ "${1:-}" = "--commands" ] || [ "${1:-}" = "commands" ]; then
  COMMANDS=1
elif [ "${1:-}" = "--run-manifest" ] || [ "${1:-}" = "run-manifest" ]; then
  RUN_MANIFEST=1
elif [ "${1:-}" = "--plugin" ] || [ "${1:-}" = "plugin" ]; then
  PLUGIN=1
elif [ "${1:-}" = "--mcp" ] || [ "${1:-}" = "mcp" ]; then
  MCP=1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/ensure-bun-path.sh
. "$ROOT/scripts/lib/ensure-bun-path.sh"
cd "$ROOT"

if [ "$COST_HYGIENE" = "1" ]; then
  echo "doctor: cost & context hygiene (non-fatal diagnostic)"
  set +e
  python3 "$ROOT/scripts/validate_cost_context_hygiene_pack.py" \
    --repo-root "$ROOT" \
    --report \
    --no-fail
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "doctor: unexpected validator exit: $rc" >&2
    exit 1
  fi
  echo "doctor: cost-hygiene section complete (see artifacts/cost-hygiene/ for JSON)"
  exit 0
fi

if [ "$MCP" = "1" ]; then
  echo "doctor: MAT Workflow MCP (workspace, python, SDK import)"
  set +e
  python3 "$ROOT/scripts/mat_mcp_doctor.py" --repo-root "$ROOT"
  mcp_rc=$?
  set -e
  if [ "$mcp_rc" -ne 0 ]; then
    echo "doctor result: FAIL (mcp)" >&2
    exit 1
  fi
  echo "doctor result: PASS (mcp)"
  exit 0
fi

if [ "$PLUGIN" = "1" ]; then
  echo "doctor: Cursor plugin packaging (committed tree + MCP stub scan + local install)"
  FAILED=0
  if ! python3 "$ROOT/scripts/package-cursor-plugin.py" --repo-root "$ROOT" --validate-committed; then
    FAILED=1
  fi
  set +e
  python3 "$ROOT/scripts/package-cursor-plugin.py" --repo-root "$ROOT" --inspect-install
  inspect_rc=$?
  set -e
  if [ "$inspect_rc" -ne 0 ]; then
    echo "WARN doctor: local plugin install hook entrypoints incomplete (see inspect-install output)" >&2
    echo "      team marketplace may still be cloning; retry after Reload Window if errors persist" >&2
  else
    echo "OK   local plugin install hook entrypoints (inspect-install)"
  fi
  set +e
  python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
packager = root / "scripts" / "package-cursor-plugin.py"
import importlib.util

spec = importlib.util.spec_from_file_location("package_cursor_plugin", packager)
if spec is None or spec.loader is None:
    print("FAIL package-cursor-plugin.py import", file=sys.stderr)
    sys.exit(1)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
hits = mod.repo_plugin_mcp_stub_errors(root)
if hits:
    print("plugin MCP stub scan FAILED:", file=sys.stderr)
    for h in hits:
        print(f"  - {h}", file=sys.stderr)
    sys.exit(1)
print("OK   plugin MCP stub scan (source + committed package)")
sys.exit(0)
PY
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    FAILED=1
  fi
  if [ "$FAILED" -eq 0 ]; then
    echo "doctor result: PASS (plugin)"
    exit 0
  fi
  echo "doctor result: FAIL (plugin)" >&2
  exit 1
fi

if [ "$LEGACY_CLEANUP_REPORT" = "1" ]; then
  echo "doctor: MAT legacy cleanup audit summary (artifacts/update-mat/legacy-cleanup.jsonl)"
  python3 "$ROOT/scripts/adoption/apply_mat_legacy_cleanup.py" --repo-root "$ROOT" --report
  exit 0
fi

if [ "$LOOP_POLICY" = "1" ]; then
  echo "doctor: loop policy (non-fatal diagnostic)"
  set +e
  python3 - "$ROOT" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
issues: list[str] = []

policy_path = root / "scripts" / "mat_loop_policy.py"
if policy_path.is_file():
    spec = importlib.util.spec_from_file_location("mat_loop_policy_doctor", policy_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        budgets = getattr(mod, "DEFAULT_BUDGETS", None)
        if isinstance(budgets, dict) and budgets:
            print(f"OK   mat_loop_policy import ({len(budgets)} slice classes)")
        unified = getattr(mod, "unified_budget_summary", None)
        if callable(unified):
            ub = unified()
            print(
                "OK   unified budgets: "
                f"repair_attempt_limit={ub.get('repair_attempt_limit')} "
                f"stop_followup_limit={ub.get('stop_followup_limit')} "
                f"mission_slice_limit={ub.get('mission_slice_limit')}"
            )
        else:
            issues.append("mat_loop_policy.DEFAULT_BUDGETS missing or empty")
    else:
        issues.append("mat_loop_policy import spec failed")
else:
    print("WARN mat_loop_policy.py not found (expected on MAT source tree)")

schema_path = root / "docs" / "schemas" / "loop-policy-schema.v1.json"
if schema_path.is_file():
    try:
        json.loads(schema_path.read_text(encoding="utf-8"))
        print(f"OK   loop policy schema {schema_path.relative_to(root)}")
    except json.JSONDecodeError as exc:
        issues.append(f"loop policy schema invalid JSON: {exc}")
else:
    issues.append(f"missing schema: {schema_path.relative_to(root)}")

legacy_manifest = root / "artifacts" / "loop" / "manifest.json"
if legacy_manifest.is_file():
    try:
        data = json.loads(legacy_manifest.read_text(encoding="utf-8"))
        required = ("run_id", "slice_id", "slice_class")
        missing = [k for k in required if not data.get(k)]
        if missing:
            issues.append(f"legacy manifest missing keys: {', '.join(missing)}")
        else:
            print(f"OK   readable manifest {legacy_manifest.relative_to(root)}")
    except json.JSONDecodeError as exc:
        issues.append(f"legacy manifest invalid JSON: {exc}")
else:
    print("OK   no artifacts/loop/manifest.json (optional)")

mat_loop_constraints = root / ".mat" / "loop" / "constraints.md"
mat_loop_budget = root / ".mat" / "loop" / "budget.md"
if mat_loop_constraints.is_file() and mat_loop_budget.is_file():
    print("OK   .mat/loop/ templates present (adopted sidecar)")
elif (root / ".mat" / "README.md").is_file():
    print("WARN .mat/loop/ templates missing — rebootstrap or mat-sync to refresh")

for msg in issues:
    print(f"WARN {msg}")

if issues:
    print("doctor: loop-policy section complete (advisory warnings above)")
else:
    print("doctor: loop-policy section complete (no warnings)")
PY
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "doctor: unexpected loop-policy diagnostic exit: $rc" >&2
    exit 1
  fi
  exit 0
fi

if [ "$QUALITY_COMMANDS" = "1" ]; then
  echo "doctor: quality commands (non-fatal diagnostic)"
  set +e
  python3 "$ROOT/scripts/validate_quality_commands.py" --repo-root "$ROOT"
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "doctor: unexpected quality-commands validator exit: $rc" >&2
    exit 1
  fi
  echo "doctor: quality-commands section complete (advisory warnings above)"
  exit 0
fi

if [ "$RESEARCH_SKILLS" = "1" ]; then
  echo "doctor: research skills (non-fatal diagnostic)"
  set +e
  python3 "$ROOT/scripts/validate_research_skills.py" --repo-root "$ROOT"
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "doctor: unexpected research-skills validator exit: $rc" >&2
    exit 1
  fi
  echo "doctor: research-skills section complete (advisory warnings above)"
  exit 0
fi

if [ "$RULES_PRECEDENCE" = "1" ]; then
  echo "doctor: rules precedence (non-fatal diagnostic)"
  set +e
  python3 "$ROOT/scripts/rules_precedence_diagnostic.py" --repo-root "$ROOT" --write-artifact
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "doctor: unexpected rules-precedence diagnostic exit: $rc" >&2
    exit 1
  fi
  echo "doctor: rules-precedence section complete (advisory; see artifacts/doctor/rules-precedence-last.json)"
  exit 0
fi

if [ "$VERIFICATION_PROFILE" = "1" ]; then
  echo "doctor: verification profile guidance"
  if [ -f "$ROOT/scripts/verification_profiles.py" ]; then
    python3 "$ROOT/scripts/verification_profiles.py" doctor-hint --repo-root "$ROOT"
  else
    echo "doctor: scripts/verification_profiles.py not present (typical thin adopted tree)"
    echo "doctor: see docs/reference/verification-profiles.md when packaged, or MAT source tree"
  fi
  exit 0
fi

if [ "$ADOPTION" = "1" ]; then
  echo "doctor: adoption provenance (non-fatal diagnostic)"
  python3 "$ROOT/scripts/adoption/adoption_provenance.py" "$ROOT"
  exit 0
fi

if [ "$MAO_ARTIFACTS" = "1" ]; then
  echo "doctor: MAO generated-artifact status (non-fatal diagnostic)"
  python3 "$ROOT/scripts/mao_artifact_status.py" --repo-root "$ROOT"
  exit 0
fi

if [ "$COMMANDS" = "1" ]; then
  echo "doctor: primary entry paths (command registry)"
  python3 "$ROOT/scripts/generate-command-index.py" --print-primary --repo-root "$ROOT"
  exit 0
fi

if [ "$RUN_MANIFEST" = "1" ]; then
  echo "doctor: N4 run manifest (non-fatal diagnostic)"
  set +e
  python3 - "$ROOT" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
script = root / "scripts" / "mat_run_manifest.py"
if not script.is_file():
    print("WARN mat_run_manifest.py not found")
    sys.exit(0)

spec = importlib.util.spec_from_file_location("mat_run_manifest_doctor", script)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

runs_dir = root / "artifacts" / "mat-runs"
if not runs_dir.is_dir():
    print(
        "OK   no artifacts/mat-runs/ "
        "(optional; enable with CURSOR_MAT_RUN_MANIFEST=1 closeout) gate_impact=none"
    )
    sys.exit(0)

manifest_files = sorted(
    runs_dir.glob("*/manifest.json"),
    key=lambda path: path.stat().st_mtime,
    reverse=True,
)
if not manifest_files:
    print("OK   artifacts/mat-runs/ exists but no manifests yet gate_impact=none")
    sys.exit(0)

print(f"OK   found {len(manifest_files)} manifest(s); showing up to 10 newest")
warn_count = 0
for manifest_path in manifest_files[:10]:
    run_id = manifest_path.parent.name
    report = mod.check_manifest(root, run_id)
    ok = bool(report.get("ok"))
    stale = report.get("stale") or []
    missing = report.get("missing") or []
    status = "OK  " if ok else "WARN"
    if not ok:
        warn_count += 1
    print(
        f"{status} run_id={run_id} stale={stale or '-'} missing={missing or '-'} "
        f"gate_impact={report.get('gate_impact', 'none')}"
    )

if warn_count:
    print(
        "doctor: run-manifest section complete "
        f"(advisory: {warn_count} stale/mismatch report(s); not a verify gate)"
    )
else:
    print("doctor: run-manifest section complete (no stale hashes)")
PY
  rc=$?
  set -e
  if [ "$rc" -ne 0 ]; then
    echo "doctor: unexpected run-manifest diagnostic exit: $rc" >&2
    exit 1
  fi
  exit 0
fi

echo "doctor: repo=$ROOT"

if [ -f "$ROOT/mat-command-registry.yaml" ] && [ -f "$ROOT/scripts/generate-command-index.py" ] && command -v python3 >/dev/null 2>&1; then
  python3 "$ROOT/scripts/generate-command-index.py" --print-primary --repo-root "$ROOT"
fi

if [ -f "$ROOT/scripts/verification_profiles.py" ]; then
  echo "verification profiles: $(python3 "$ROOT/scripts/verification_profiles.py" default-profile --repo-root "$ROOT") (default); see docs/reference/verification-profiles.md or doctor --verification-profile"
else
  echo "verification profiles: helper not packaged on this tree (optional); see docs/reference/verification-profiles.md"
fi

echo "rules precedence: advisory scan via bash scripts/doctor.sh --rules-precedence (Team Rules not repo-readable; see docs/reference/capability-precedence.md)"

echo "observability: default bind is local-only (127.0.0.1). Remote bind requires OBSERVABILITY_ALLOW_REMOTE=1 and OBSERVABILITY_AUTH_TOKEN (fail-closed). See docs/architecture/observability-retention-policy.md and scripts/observability-purge.py --dry-run."

echo "run manifest: optional artifacts/mat-runs/ — advisory stale check via bash scripts/doctor.sh --run-manifest (CURSOR_MAT_RUN_MANIFEST=1 closeout; not a verify gate)"

check_file() {
  local path="$1"
  if [ -e "$path" ]; then
    echo "OK   $path"
  else
    echo "FAIL $path"
    return 1
  fi
}

FAILED=0

for path in \
  ".cursor/hooks.json" \
  ".cursor/worktrees.json" \
  ".cursor/mcp.json" \
  ".cursor/commands/mat-doctor.md" \
  ".cursor/commands/mat-wt-check.md" \
  ".cursor/agents/test-writer.md" \
  ".cursor/agents/style-reviewer.md" \
  "scripts/setup-dev.sh" \
  "scripts/check-worktrees.sh" \
  "scripts/phase1-verify.sh"; do
  check_file "$path" || FAILED=1
done

if command -v python3 >/dev/null 2>&1; then
  echo "OK   python3=$(python3 --version 2>&1)"
else
  echo "FAIL python3 missing"
  FAILED=1
fi

if command -v bun >/dev/null 2>&1; then
  echo "OK   bun=$(bun --version 2>&1)"
else
  echo "WARN bun missing (required for observability apps)"
fi

python3 - <<'PY' || FAILED=1
import json
from pathlib import Path

for path in [".cursor/hooks.json", ".cursor/worktrees.json", ".cursor/mcp.json"]:
    json.loads(Path(path).read_text())
print("OK   core JSON files parse")
PY

bash scripts/check-worktrees.sh --strict || FAILED=1

if [ "$RUN_FULL" -eq 1 ]; then
  echo "Running full verification via scripts/phase1-verify.sh ..."
  bash scripts/phase1-verify.sh || FAILED=1
fi

if [ "$FAILED" -eq 0 ]; then
  echo "doctor result: PASS"
  exit 0
fi

echo "doctor result: FAIL"
exit 1
