#!/usr/bin/env bash
# mat-sync.sh — unified MAT adoption sync state machine (detect → route → plan → approve → verify).
# Wraps bootstrap-workflow-into-repo.sh, update-mat.py, doctor.sh, and phase1-verify.sh.
# Dry-run/plan by default; mutations require --approve-plan matching the latest saved plan.
#
# .mat/source-config.json schemas (optional; slice 2+ may write on bootstrap):
#   v1: { "mat_source": "/absolute/or/relative/path/to/MAT-source-repo" }
#   v2: { "schema_version": 2, "repository": "OWNER/REPO", "ref": "main",
#         "cache_dir": "~/.cache/mat-source" }
#
# Planned resolution precedence (mat_source_config.py; full wire in slice 2):
#   1. --source PATH (local)
#   2. --repository + --ref (GitHub materialize)
#   3. .mat/source-config.json v2
#   4. .mat/source-config.json v1 mat_source
#   5. Sibling heuristic (multi-agent-teams | multi-agent-workflow)
#   6. $MAT_SOURCE
#   7. fail clear
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/mktemp-portable.sh
source "${SCRIPT_DIR}/lib/mktemp-portable.sh"
MAT_SCRIPT_HOME="$(cd "${SCRIPT_DIR}/.." && pwd)"
BOOTSTRAP_SCRIPT="${MAT_SCRIPT_HOME}/scripts/adoption/bootstrap-workflow-into-repo.sh"
UPDATE_SCRIPT="${MAT_SCRIPT_HOME}/scripts/adoption/update-mat.py"

SOURCE_ARG=""
REPOSITORY_ARG=""
REF_ARG="HEAD"
UPDATER_REF="HEAD"
REPO_ROOT_ARG=""
MAT_SOURCE_RESOLUTION_JSON=""
MAT_SOURCE_RESOLUTION_FILE=""
APPROVE_PLAN_ARG=""
FORCE_REBOOTSTRAP=0
SKIP_VERIFY=0
STRICT_DOCTOR=0

usage() {
  cat <<'EOF'
mat-sync.sh — MAT adoption sync state machine

Usage:
  mat-sync.sh [--source PATH] [--repository OWNER/REPO] [--ref REF] [--repo-root PATH]
              [--approve-plan PLAN.json] [--force-rebootstrap] [--skip-verify]
              [--strict-doctor] [--help]

Phases (always in order):
  1. detect  — sidecar markers, custom agents, MAT source resolution
  2. route   — bootstrap | update_dry_run | rebootstrap | stop (rationale on stdout)
  3. plan    — human-readable summary + plan JSON under artifacts/mat-sync/
  4. gate    — apply/bootstrap only when --approve-plan matches the latest plan file
  5. verify  — bash scripts/doctor.sh then bash scripts/phase1-verify.sh on target root

MAT_SOURCE resolution (first match wins; mat_source_config.py):
  1. --source PATH (local dev override)
  2. --repository OWNER/REPO + --ref REF (GitHub materialize)
  3. <target>/.mat/source-config.json v2 (repository + ref)
  4. <target>/.mat/source-config.json v1 mat_source path
  5. Sibling heuristic: multi-agent-teams or multi-agent-workflow beside target
  6. $MAT_SOURCE environment variable

Safety:
  - Plan/dry-run by default; no bootstrap or apply without --approve-plan
  - No git commit on the target root (staging/bootstrap only)
  - Reuses existing bootstrap and updater tools (no new merge engine)

Verify:
  - doctor runs advisory-first; stale worktree WARN/FAIL does not fail verify when
    phase1-verify passes (use --strict-doctor or MAT_SYNC_STRICT_DOCTOR=1 to fail closed)
  - trailing whitespace in docs/current-plan.md or verify-result.md emits a fix hint
    (non-destructive; see tests/test_artifact_validation.py)
  - MAT_SYNC_SKIP_GITIGNORE_TRACKABILITY=1 skips post-approve git check-ignore gate

Examples (zsh-safe — quote paths that contain spaces):
  mat-sync.sh --repo-root "/path/to/adopted repo"
  mat-sync.sh --source "/path/to/MAT source" --repo-root "/path/to/adopted repo"
  mat-sync.sh --source "/path/to/MAT source" --repo-root "/path/to/adopted repo" \
    --approve-plan "/path/to/adopted repo/artifacts/mat-sync/latest-plan.json"
EOF
}

log() {
  printf 'mat-sync: %s\n' "$*" >&2
}

die() {
  log "error: $*"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      [[ $# -ge 2 ]] || die "--source requires a path argument"
      SOURCE_ARG="$2"
      if [[ ! -d "${SOURCE_ARG}" ]]; then
        die "--source path is not a directory: ${SOURCE_ARG}"
      fi
      shift 2
      ;;
    --repository)
      [[ $# -ge 2 ]] || die "--repository requires OWNER/REPO"
      REPOSITORY_ARG="$2"
      shift 2
      ;;
    --ref)
      [[ $# -ge 2 ]] || die "--ref requires a value"
      REF_ARG="$2"
      shift 2
      ;;
    --repo-root)
      [[ $# -ge 2 ]] || die "--repo-root requires a path"
      REPO_ROOT_ARG="$2"
      shift 2
      ;;
    --approve-plan)
      [[ $# -ge 2 ]] || die "--approve-plan requires a plan JSON path argument"
      APPROVE_PLAN_ARG="$2"
      shift 2
      ;;
    --force-rebootstrap)
      FORCE_REBOOTSTRAP=1
      shift
      ;;
    --skip-verify)
      SKIP_VERIFY=1
      shift
      ;;
    --strict-doctor)
      STRICT_DOCTOR=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1 (try --help)"
      ;;
  esac
done

if [[ -n "${REPO_ROOT_ARG}" ]]; then
  TARGET_ROOT="$(cd "${REPO_ROOT_ARG}" && pwd)"
else
  TARGET_ROOT="$(pwd)"
fi

if [[ "${MAT_SYNC_STRICT_DOCTOR:-0}" == "1" ]]; then
  STRICT_DOCTOR=1
fi

print_quiet_updater_summary() {
  local updater_plan_file="${1:-}"
  python3 - "${updater_plan_file}" <<'PY'
import json, pathlib, sys

plan_path = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else ""
counts: dict[str, int] = {}
rec = None
rationale = None
if plan_path and pathlib.Path(plan_path).is_file():
    payload = json.loads(pathlib.Path(plan_path).read_text(encoding="utf-8"))
    inner = payload.get("plan") or {}
    routing = inner.get("conflict_routing") or payload.get("conflict_routing") or {}
    counts = (
        payload.get("conflict_bucket_counts")
        or inner.get("conflict_bucket_counts")
        or routing.get("conflict_bucket_counts")
        or {}
    )
    rec = payload.get("routing_recommendation") or inner.get("routing_recommendation")
    rationale = payload.get("routing_rationale") or inner.get("routing_rationale")

if counts:
    print("Conflict buckets:", file=sys.stderr)
    for key in (
        "stale_layout_manifest",
        "product_extensions",
        "stale_registry",
        "registry_integrity",
        "true_drift",
    ):
        print(f"  {key}: {counts.get(key, 0)}", file=sys.stderr)
if rec:
    print(f"routing_recommendation: {rec}", file=sys.stderr)
if rationale:
    print(f"routing_rationale: {rationale}", file=sys.stderr)
if plan_path and pathlib.Path(plan_path).is_file():
    print(f"updater-plan-file={plan_path}", file=sys.stderr)
    print(
        "mat-sync: full patch/conflict detail is in the updater plan JSON (not printed here)",
        file=sys.stderr,
    )
PY
}

handoff_whitespace_preflight() {
  python3 - "${TARGET_ROOT}" <<'PY'
import pathlib, sys

root = pathlib.Path(sys.argv[1])
candidates = [root / "docs" / "current-plan.md", root / "verify-result.md"]
issues: list[tuple[pathlib.Path, int]] = []
for path in candidates:
    if not path.is_file():
        continue
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line != line.rstrip():
            issues.append((path, lineno))
if not issues:
    sys.exit(0)
print(
    "mat-sync: warning: trailing whitespace in handoff file(s) fails artifact validation",
    file=sys.stderr,
)
for path, lineno in issues:
    print(f"  {path}:{lineno}", file=sys.stderr)
seen: set[pathlib.Path] = set()
for path, _ in issues:
    if path in seen:
        continue
    seen.add(path)
    print(
        f"mat-sync: fix {path}: "
        f"python3 -c \"import pathlib; p=pathlib.Path({str(path)!r}); "
        f"t=p.read_text(encoding='utf-8'); "
        f"p.write_text('\\\\n'.join(l.rstrip() for l in t.splitlines())"
        f"+('\\\\n' if t else ''), encoding='utf-8')\"",
        file=sys.stderr,
    )
PY
}

resolve_mat_source() {
  local config_py="${MAT_SCRIPT_HOME}/scripts/adoption/mat_source_config.py"
  local -a cmd=(
    python3 "${config_py}" resolve
    --repo-root "${TARGET_ROOT}"
    --json
  )

  if [[ -n "${SOURCE_ARG}" ]]; then
    cmd+=(--source "${SOURCE_ARG}")
  elif [[ -n "${REPOSITORY_ARG}" ]]; then
    cmd+=(--repository "${REPOSITORY_ARG}" --ref "${REF_ARG}")
  fi

  local stderr_file
  stderr_file="$(mat_mktemp_file mat-sync-resolve-stderr)"
  if ! MAT_SOURCE_RESOLUTION_JSON="$("${cmd[@]}" 2>"${stderr_file}")"; then
    if [[ -s "${stderr_file}" ]]; then
      cat "${stderr_file}" >&2
    fi
    rm -f "${stderr_file}"
    MAT_SOURCE_RESOLVED=""
    return 1
  fi
  rm -f "${stderr_file}"

  MAT_SOURCE_RESOLUTION_FILE="$(mat_mktemp_file mat-sync-resolution)"
  printf '%s' "${MAT_SOURCE_RESOLUTION_JSON}" >"${MAT_SOURCE_RESOLUTION_FILE}"

  UPDATER_REF="$(MAT_SOURCE_RESOLUTION_FILE="${MAT_SOURCE_RESOLUTION_FILE}" python3 - "${REF_ARG}" <<'PY'
import json, os, pathlib, sys

resolution_path = os.environ.get("MAT_SOURCE_RESOLUTION_FILE", "")
resolution = {}
if resolution_path and pathlib.Path(resolution_path).is_file():
    resolution = json.loads(pathlib.Path(resolution_path).read_text(encoding="utf-8"))
cli_ref = sys.argv[1]
provenance = resolution.get("provenance") or {}
if resolution.get("source_kind") == "github_materialized" and provenance.get("resolved_sha"):
    print(provenance["resolved_sha"])
elif provenance.get("requested_ref"):
    print(provenance["requested_ref"])
else:
    print(cli_ref)
PY
)"

  MAT_SOURCE_RESOLVED="$(python3 -c "import json,sys; print(json.load(sys.stdin)['mat_source'])" <<<"${MAT_SOURCE_RESOLUTION_JSON}")"
  return 0
}

list_custom_agents() {
  local mat_source="$1"
  local target="$2"
  python3 - "${mat_source}" "${target}" <<'PY'
import pathlib, sys

mat_source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
baseline_dir = mat_source / ".cursor" / "agents"
target_dir = target / ".cursor" / "agents"
baseline = {p.name for p in baseline_dir.glob("*.md")} if baseline_dir.is_dir() else set()
custom = []
if target_dir.is_dir():
    for path in sorted(target_dir.glob("*.md")):
        if path.name not in baseline:
            custom.append(path.name)
print("\n".join(custom))
PY
}

list_custom_skills() {
  local mat_source="$1"
  local target="$2"
  python3 - "${mat_source}" "${target}" <<'PY'
import pathlib, sys

mat_source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
baseline_dir = mat_source / ".cursor" / "skills"
target_dir = target / ".cursor" / "skills"
baseline = {p.name for p in baseline_dir.iterdir() if p.is_dir()} if baseline_dir.is_dir() else set()
custom = []
if target_dir.is_dir():
    for path in sorted(target_dir.iterdir()):
        if path.is_dir() and path.name not in baseline:
            custom.append(path.name)
print("\n".join(custom))
PY
}

list_custom_commands() {
  local mat_source="$1"
  local target="$2"
  python3 - "${mat_source}" "${target}" <<'PY'
import pathlib, sys

mat_source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
baseline_dir = mat_source / ".cursor" / "commands"
target_dir = target / ".cursor" / "commands"
baseline = {p.name for p in baseline_dir.glob("*.md")} if baseline_dir.is_dir() else set()
custom = []
if target_dir.is_dir():
    for path in sorted(target_dir.glob("*.md")):
        if path.name not in baseline:
            custom.append(path.name)
print("\n".join(custom))
PY
}

phase_detect() {
  local mat_source="$1"
  local sidecar_readme=0
  local sidecar_agents_mat=0
  [[ -f "${TARGET_ROOT}/.mat/README.md" ]] && sidecar_readme=1
  [[ -f "${TARGET_ROOT}/.mat/AGENTS.mat.md" ]] && sidecar_agents_mat=1

  local custom_agents custom_skills custom_commands
  custom_agents="$(list_custom_agents "${mat_source}" "${TARGET_ROOT}")"
  custom_skills="$(list_custom_skills "${mat_source}" "${TARGET_ROOT}")"
  custom_commands="$(list_custom_commands "${mat_source}" "${TARGET_ROOT}")"
  local custom_agent_count=0 custom_skill_count=0 custom_command_count=0
  if [[ -n "${custom_agents}" ]]; then
    custom_agent_count="$(printf '%s\n' "${custom_agents}" | sed '/^$/d' | wc -l | tr -d ' ')"
  fi
  if [[ -n "${custom_skills}" ]]; then
    custom_skill_count="$(printf '%s\n' "${custom_skills}" | sed '/^$/d' | wc -l | tr -d ' ')"
  fi
  if [[ -n "${custom_commands}" ]]; then
    custom_command_count="$(printf '%s\n' "${custom_commands}" | sed '/^$/d' | wc -l | tr -d ' ')"
  fi

  log "phase detect: target=${TARGET_ROOT}"
  log "phase detect: mat_source=${mat_source}"
  log "phase detect: sidecar_readme=${sidecar_readme} sidecar_agents_mat=${sidecar_agents_mat} custom_agents=${custom_agent_count} custom_skills=${custom_skill_count} custom_commands=${custom_command_count}"

  local product_extensions_reconciled=""
  if [[ "${sidecar_agents_mat}" -eq 1 ]]; then
    product_extensions_reconciled="$(python3 - "${mat_source}" "${TARGET_ROOT}" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]) / "scripts" / "adoption"))
from update_mat_conflict_routing import maybe_reconcile_product_extensions

source_root = Path(sys.argv[1])
target_root = Path(sys.argv[2])
out = maybe_reconcile_product_extensions(source_root, target_root)
if out is not None:
    print(out)
PY
    )"
    if [[ -n "${product_extensions_reconciled}" ]]; then
      log "phase detect: product-extensions reconciled=${product_extensions_reconciled}"
    fi
  fi

  DETECT_JSON="$(python3 - "${TARGET_ROOT}" "${mat_source}" "${sidecar_readme}" "${sidecar_agents_mat}" "${custom_agents}" "${custom_skills}" "${custom_commands}" "${product_extensions_reconciled}" <<'PY'
import json, sys
target, mat_source, sidecar_readme, sidecar_agents_mat, agents_blob, skills_blob, commands_blob, reconciled = sys.argv[1:9]
agents = [line for line in agents_blob.splitlines() if line.strip()]
skills = [line for line in skills_blob.splitlines() if line.strip()]
commands = [line for line in commands_blob.splitlines() if line.strip()]
print(json.dumps({
    "target_root": target,
    "mat_source": mat_source,
    "sidecar_readme": bool(int(sidecar_readme)),
    "sidecar_agents_mat": bool(int(sidecar_agents_mat)),
    "custom_agent_count": len(agents),
    "custom_agents": agents,
    "custom_skill_count": len(skills),
    "custom_skills": skills,
    "custom_command_count": len(commands),
    "custom_commands": commands,
    "product_extensions_reconciled": reconciled or None,
}, sort_keys=True))
PY
)"
}

phase_route() {
  local mat_source="$1"
  ROUTE="stop"
  ROUTE_REASON=""

  if [[ "${FORCE_REBOOTSTRAP}" -eq 1 ]]; then
    ROUTE="rebootstrap"
    ROUTE_REASON="operator requested --force-rebootstrap"
    log "phase route: ${ROUTE} (${ROUTE_REASON})"
    return 0
  fi

  local sidecar_agents_mat
  sidecar_agents_mat="$(python3 -c "import json; print(json.loads('''${DETECT_JSON}''')['sidecar_agents_mat'])")"

  if [[ "${sidecar_agents_mat}" != "True" && "${sidecar_agents_mat}" != "true" ]]; then
    ROUTE="bootstrap"
    ROUTE_REASON="missing .mat/AGENTS.mat.md — first adoption bootstrap required"
    log "phase route: ${ROUTE} (${ROUTE_REASON})"
    return 0
  fi

  ROUTE="update_dry_run"
  ROUTE_REASON="sidecar present — incremental updater dry-run"
  log "phase route: ${ROUTE} (${ROUTE_REASON})"
}

write_mat_sync_plan() {
  local mat_source="$1"
  local updater_plan_file="${2:-}"
  local conflict_state="${3:-clear}"
  local sync_dir="${TARGET_ROOT}/artifacts/mat-sync"
  mkdir -p "${sync_dir}"

  local timestamp
  timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
  PLAN_FILE="${sync_dir}/mat-sync-plan-${timestamp}.json"

  MAT_SOURCE_RESOLUTION_FILE="${MAT_SOURCE_RESOLUTION_FILE:-}" MAT_SCRIPT_HOME="${MAT_SCRIPT_HOME}" python3 - "${PLAN_FILE}" "${ROUTE}" "${ROUTE_REASON}" "${mat_source}" "${TARGET_ROOT}" "${REF_ARG}" "${DETECT_JSON}" "${updater_plan_file}" "${conflict_state}" <<'PY'
import json, os, pathlib, sys, datetime

plan_path = pathlib.Path(sys.argv[1])
route = sys.argv[2]
route_reason = sys.argv[3]
mat_source_arg = sys.argv[4]
repo_root = pathlib.Path(sys.argv[5])
ref = sys.argv[6]
detect = json.loads(sys.argv[7])
updater_plan = sys.argv[8] or None
conflict_state = sys.argv[9]
resolution_path = os.environ.get("MAT_SOURCE_RESOLUTION_FILE", "")
mat_script_home = os.environ.get("MAT_SCRIPT_HOME", "")
resolution = {}
if resolution_path and pathlib.Path(resolution_path).is_file():
    try:
        resolution = json.loads(pathlib.Path(resolution_path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        resolution = {}
provenance = resolution.get("provenance") or {}

def _adoption_helper_dir(helper: str) -> pathlib.Path | None:
    for candidate in (
        pathlib.Path(mat_source_arg) / "scripts" / "adoption" if mat_source_arg else None,
        repo_root / "scripts" / "adoption",
        pathlib.Path(mat_script_home) / "scripts" / "adoption" if mat_script_home else None,
    ):
        if candidate is not None and (candidate / helper).is_file():
            return candidate
    return None

cursor_dir = _adoption_helper_dir("mat_cursorignore_merge.py")
if cursor_dir is None:
    raise SystemExit("mat-sync: mat_cursorignore_merge helper not found")
sys.path.insert(0, str(cursor_dir))
from mat_cursorignore_merge import compute_cursorignore_merge_preview

git_dir = _adoption_helper_dir("mat_gitignore_merge.py")
compute_gitignore_merge_preview = None
compute_gitignore_rewrite_preview = None
if git_dir is not None:
    if str(git_dir) not in sys.path:
        sys.path.insert(0, str(git_dir))
    from mat_gitignore_merge import compute_gitignore_merge_preview
    try:
        from mat_gitignore_merge import compute_gitignore_rewrite_preview
    except ImportError:
        compute_gitignore_rewrite_preview = None

env_dir = _adoption_helper_dir("mat_env_sample_merge.py")
compute_env_sample_merge_preview = None
if env_dir is not None:
    if str(env_dir) not in sys.path:
        sys.path.insert(0, str(env_dir))
    from mat_env_sample_merge import compute_env_sample_merge_preview

preflight_dir = _adoption_helper_dir("mat_adopt_preflight.py")
if preflight_dir is None:
    raise SystemExit("mat-sync: mat_adopt_preflight helper not found")
if str(preflight_dir) not in sys.path:
    sys.path.insert(0, str(preflight_dir))
from mat_adopt_preflight import compute_preflight

payload = {
    "schema_version": "mat-sync-plan/v1",
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "route": route,
    "route_reason": route_reason,
    "mat_source": mat_source_arg,
    "repo_root": str(repo_root),
    "ref": ref,
    "detect": detect,
    "updater_plan_file": updater_plan,
    "conflict_state": conflict_state,
    "routing_recommendation": None,
    "cursorignore_merge_preview": None,
    "gitignore_merge_preview": None,
    "gitignore_rewrite_preview": None,
    "env_sample_merge_preview": None,
    "preflight": None,
    "source_kind": resolution.get("source_kind"),
}
for key in (
    "repository",
    "requested_ref",
    "resolved_sha",
    "cache_path",
    "materialized_at",
):
    value = provenance.get(key)
    if value is not None:
        payload[key] = value
if updater_plan:
    up = pathlib.Path(updater_plan)
    if up.is_file():
        udata = json.loads(up.read_text(encoding="utf-8"))
        inner = udata.get("plan") or udata
        payload["routing_recommendation"] = udata.get("routing_recommendation") or inner.get("routing_recommendation")
preview = compute_cursorignore_merge_preview(repo_root)
payload["cursorignore_merge_preview"] = preview.as_plan_field()
if compute_gitignore_merge_preview is not None:
    git_preview = compute_gitignore_merge_preview(repo_root)
    payload["gitignore_merge_preview"] = git_preview.as_plan_field()
if compute_gitignore_rewrite_preview is not None:
    rewrite_preview = compute_gitignore_rewrite_preview(repo_root)
    payload["gitignore_rewrite_preview"] = rewrite_preview.as_plan_field()
mat_source_path = pathlib.Path(mat_source_arg) if mat_source_arg else repo_root
if compute_env_sample_merge_preview is not None:
    upstream_sample = mat_source_path / ".mat.env.sample" if mat_source_path.is_dir() else None
    env_preview = compute_env_sample_merge_preview(repo_root, upstream_path=upstream_sample)
    payload["env_sample_merge_preview"] = env_preview.as_plan_field()
payload["preflight"] = compute_preflight(repo_root, mat_source_path)
prov_dir = _adoption_helper_dir("adoption_provenance.py")
if prov_dir is not None:
    if str(prov_dir) not in sys.path:
        sys.path.insert(0, str(prov_dir))
    from adoption_provenance import enrich_plan_provenance
    payload = enrich_plan_provenance(payload, mat_source=mat_source_path if mat_source_path.is_dir() else None)
text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
plan_path.write_text(text, encoding="utf-8")
latest = plan_path.parent / "latest-plan.json"
latest.write_text(text, encoding="utf-8")
if route in ("bootstrap", "rebootstrap"):
    blockers = payload["preflight"].get("gitignore_blockers") or []
    if blockers:
        print(
            "preflight: gitignore blockers detected: " + "; ".join(blockers),
            file=sys.stderr,
        )
    policy_flags = payload["preflight"].get("policy_flags") or []
    if "builder_verify_empty" in policy_flags:
        print(
            "preflight: .mat/adoption-profile.json has empty validation_commands.builder_verify "
            "— map your repo lint/test commands before first /mat-sprint or /mat-plan-team",
            file=sys.stderr,
        )
print(plan_path)
PY

  log "phase plan: saved ${PLAN_FILE}"
  printf 'mat-sync-plan-file=%s\n' "${PLAN_FILE}"
}

phase_plan() {
  local mat_source="$1"
  UPDATER_PLAN_FILE=""
  CONFLICT_STATE="clear"
  UPDATER_EXIT=0

  case "${ROUTE}" in
    bootstrap|rebootstrap)
      write_mat_sync_plan "${mat_source}" "" "clear"
      log "phase plan: bootstrap path — review plan JSON; rerun with --approve-plan to mutate"
      ;;
    update_dry_run)
      local updater_log
      updater_log="$(mat_mktemp_file mat-sync-updater)"
      set +e
      python3 "${UPDATE_SCRIPT}" \
        --source "${mat_source}" \
        --ref "${UPDATER_REF}" \
        --repo-root "${TARGET_ROOT}" \
        >"${updater_log}" 2>&1
      UPDATER_EXIT=$?
      set -e

      # Parse from the log file — avoid loading full updater stdout into a bash variable (CI size limits).
      if grep -qE '^plan-file=' "${updater_log}" 2>/dev/null; then
        UPDATER_PLAN_FILE="$(grep -E '^plan-file=' "${updater_log}" | tail -n 1 | cut -d= -f2-)"
      fi

      local routing_recommendation="incremental"
      local routing_rationale=""
      if [[ -n "${UPDATER_PLAN_FILE}" && -f "${UPDATER_PLAN_FILE}" ]]; then
        read -r routing_recommendation routing_rationale < <(
          python3 - "${UPDATER_PLAN_FILE}" <<'PY'
import json, pathlib, sys
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
plan = payload.get("plan") or payload
rec = payload.get("routing_recommendation") or plan.get("routing_recommendation") or "incremental"
rationale = payload.get("routing_rationale") or plan.get("routing_rationale") or ""
print(rec, rationale)
PY
        )
      fi

      if [[ "${routing_recommendation}" == "rebootstrap" ]]; then
        CONFLICT_STATE="routable"
        ROUTE="rebootstrap"
        ROUTE_REASON="${routing_rationale:-updater recommends re-bootstrap}"
        log "phase route: ${ROUTE} (${ROUTE_REASON})"
      elif [[ "${routing_recommendation}" == "stop" ]] || [[ "${UPDATER_EXIT}" -eq 2 ]] || grep -qE '^conflicts: [1-9]' "${updater_log}" 2>/dev/null; then
        CONFLICT_STATE="blocked"
        ROUTE="stop"
        ROUTE_REASON="${routing_rationale:-updater dry-run reported conflicts — resolve or choose --force-rebootstrap}"
        log "phase route: ${ROUTE} (${ROUTE_REASON})"
      elif [[ "${UPDATER_EXIT}" -ne 0 ]]; then
        rm -f "${updater_log}"
        die "update-mat dry-run failed (exit ${UPDATER_EXIT})"
      fi

      if [[ "${ROUTE}" == "rebootstrap" || "${ROUTE}" == "stop" ]]; then
        print_quiet_updater_summary "${UPDATER_PLAN_FILE}"
      else
        cat "${updater_log}" >&2
      fi

      if [[ "${ROUTE}" == "update_dry_run" ]]; then
        [[ -n "${UPDATER_PLAN_FILE}" ]] || die "update-mat dry-run did not emit plan-file= (cannot save apply-ready plan)"
        [[ -f "${UPDATER_PLAN_FILE}" ]] || die "updater plan file missing after dry-run: ${UPDATER_PLAN_FILE}"
      fi

      write_mat_sync_plan "${mat_source}" "${UPDATER_PLAN_FILE}" "${CONFLICT_STATE}"
      rm -f "${updater_log}"
      ;;
    stop)
      write_mat_sync_plan "${mat_source}" "" "blocked"
      log "phase plan: stop route — no mutation commands available"
      ;;
    *)
      die "internal error: unknown route ${ROUTE}"
      ;;
  esac
}

plans_match() {
  local approved="$1"
  local latest="$2"
  python3 - "${approved}" "${latest}" <<'PY'
import hashlib, pathlib, sys

def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

approved = pathlib.Path(sys.argv[1]).resolve()
latest = pathlib.Path(sys.argv[2]).resolve()
if not approved.is_file():
    sys.exit(2)
if not latest.is_file():
    sys.exit(3)
sys.exit(0 if digest(approved) == digest(latest) else 1)
PY
}

phase_gate() {
  local mat_source="$1"
  local approved="${APPROVE_PLAN_ARG}"
  local latest="${TARGET_ROOT}/artifacts/mat-sync/latest-plan.json"

  [[ -f "${approved}" ]] || die "--approve-plan file not found: ${approved} (run plan phase first; path must be a saved mat-sync-plan-*.json or latest-plan.json)"

  if [[ -f "${latest}" ]]; then
    if ! plans_match "${approved}" "${latest}"; then
      die "--approve-plan does not match latest saved plan at ${latest} (re-run plan phase or pass the current latest-plan.json path)"
    fi
  fi

  local route conflict_state updater_plan
  route="$(python3 -c "import json; print(json.load(open('${approved}', encoding='utf-8'))['route'])")"
  conflict_state="$(python3 -c "import json; print(json.load(open('${approved}', encoding='utf-8')).get('conflict_state','clear'))")"
  updater_plan="$(python3 -c "import json; d=json.load(open('${approved}', encoding='utf-8')); print(d.get('updater_plan_file') or '')")"

  if [[ "${conflict_state}" == "blocked" ]] || [[ "${route}" == "stop" ]]; then
    die "plan is blocked/stop — cannot apply"
  fi

  case "${route}" in
    bootstrap|rebootstrap)
      log "phase gate: running bootstrap (${route})"
      MULTI_AGENT_WORKFLOW_ROOT="${mat_source}" bash "${BOOTSTRAP_SCRIPT}" \
        --mode existing-project \
        --non-interactive \
        "${TARGET_ROOT}"
      apply_cursorignore_merge_post_bootstrap "${approved}"
      apply_gitignore_merge_post_bootstrap "${approved}"
      apply_env_sample_merge_post_bootstrap "${approved}" "${mat_source}"
      ;;
    update_dry_run)
      [[ -n "${updater_plan}" ]] || die "plan missing updater_plan_file for apply"
      [[ -f "${updater_plan}" ]] || die "updater plan file not found: ${updater_plan}"
      log "phase gate: running updater apply staging"
      set +e
      local apply_out
      apply_out="$(python3 "${UPDATE_SCRIPT}" \
        --source "${mat_source}" \
        --ref "${UPDATER_REF}" \
        --repo-root "${TARGET_ROOT}" \
        --apply \
        --approved \
        --plan-file "${updater_plan}" 2>&1)"
      local apply_exit=$?
      set -e
      printf '%s\n' "${apply_out}" >&2
      [[ "${apply_exit}" -eq 0 ]] || die "update-mat apply failed (exit ${apply_exit})"
      if ! printf '%s\n' "${apply_out}" | grep -q "approval required before commit or PR creation"; then
        die "apply stdout missing approval stop line"
      fi
      apply_cursorignore_merge_from_plan "${approved}"
      apply_gitignore_merge_on_approve "${approved}"
      apply_env_sample_merge_on_approve "${approved}" "${mat_source}"
      ;;
    *)
      die "unsupported route for apply: ${route}"
      ;;
  esac
}

apply_cursorignore_merge_post_bootstrap() {
  local approved="$1"
  log "phase gate: cursorignore merge (post-bootstrap recompute)"
  python3 - "${approved}" "${MAT_SOURCE_RESOLVED}" <<'PY' || die "cursorignore merge helper failed"
import json, pathlib, sys

approved = pathlib.Path(sys.argv[1])
mat_source = pathlib.Path(sys.argv[2])
plan = json.loads(approved.read_text(encoding="utf-8"))
repo_root = pathlib.Path(plan["repo_root"])
for candidate in (mat_source / "scripts" / "adoption", repo_root / "scripts" / "adoption"):
    if (candidate / "mat_cursorignore_merge.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit("mat-sync: mat_cursorignore_merge helper not found")
from mat_cursorignore_merge import apply_cursorignore_merge, compute_cursorignore_merge_preview

plan_lines = plan.get("cursorignore_merge_preview")
plan_list = [str(x) for x in plan_lines] if isinstance(plan_lines, list) else None

preview = compute_cursorignore_merge_preview(repo_root)
recomputed_lines = list(preview.lines) if preview.eligible else []

if plan_list is not None and plan_list != recomputed_lines:
    print(
        "mat-sync: cursorignore plan preview differed from post-bootstrap recompute; using recomputed lines",
        file=sys.stderr,
    )

if not recomputed_lines:
    reason = preview.skip_reason or "no_lines_to_append"
    print(f"mat-sync: post-bootstrap cursorignore merge skipped ({reason})", file=sys.stderr)
    sys.exit(0)

result = apply_cursorignore_merge(repo_root, lines=recomputed_lines)
if result.get("applied"):
    appended = result.get("appended_lines") or []
    print(
        f"mat-sync: post-bootstrap cursorignore merge appended {len(appended)} line(s)",
        file=sys.stderr,
    )
else:
    reason = result.get("reason") or "unknown"
    print(f"mat-sync: post-bootstrap cursorignore merge skipped ({reason})", file=sys.stderr)
PY
}

apply_cursorignore_merge_from_plan() {
  local approved="$1"
  log "phase gate: cursorignore merge (append-only when plan preview present)"
  python3 - "${approved}" "${MAT_SOURCE_RESOLVED}" <<'PY' || die "cursorignore merge helper failed"
import json, pathlib, sys

approved = pathlib.Path(sys.argv[1])
mat_source = pathlib.Path(sys.argv[2])
repo_root = pathlib.Path(json.loads(approved.read_text(encoding="utf-8"))["repo_root"])
for candidate in (mat_source / "scripts" / "adoption", repo_root / "scripts" / "adoption"):
    if (candidate / "mat_cursorignore_merge.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit("mat-sync: mat_cursorignore_merge helper not found")
from mat_cursorignore_merge import apply_cursorignore_merge

plan = json.loads(approved.read_text(encoding="utf-8"))
lines = plan.get("cursorignore_merge_preview")
if lines is None:
    print("mat-sync: cursorignore merge skipped (no preview in plan)", file=sys.stderr)
    sys.exit(0)
if not isinstance(lines, list):
    print("mat-sync: cursorignore_merge_preview must be a list", file=sys.stderr)
    sys.exit(1)
result = apply_cursorignore_merge(repo_root, lines=[str(x) for x in lines])
if result.get("applied"):
    appended = result.get("appended_lines") or []
    print(
        f"mat-sync: cursorignore merge appended {len(appended)} line(s)",
        file=sys.stderr,
    )
else:
    reason = result.get("reason") or "unknown"
    print(f"mat-sync: cursorignore merge skipped ({reason})", file=sys.stderr)
PY
}

apply_gitignore_merge_post_bootstrap() {
  local approved="$1"
  log "phase gate: gitignore merge (post-bootstrap recompute)"
  python3 - "${approved}" "${MAT_SOURCE_RESOLVED}" <<'PY' || die "gitignore merge helper failed"
import json, pathlib, sys

approved = pathlib.Path(sys.argv[1])
mat_source = pathlib.Path(sys.argv[2])
plan = json.loads(approved.read_text(encoding="utf-8"))
repo_root = pathlib.Path(plan["repo_root"])
for candidate in (mat_source / "scripts" / "adoption", repo_root / "scripts" / "adoption"):
    if (candidate / "mat_gitignore_merge.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit("mat-sync: mat_gitignore_merge helper not found")
from mat_gitignore_merge import apply_gitignore_merge, compute_gitignore_merge_preview
try:
    from mat_gitignore_merge import apply_gitignore_rewrite
except ImportError:
    apply_gitignore_rewrite = None

if apply_gitignore_rewrite is not None:
    rewrite_result = apply_gitignore_rewrite(repo_root)
    if rewrite_result.get("applied"):
        rewritten = rewrite_result.get("rewritten_lines") or []
        print(
            f"mat-sync: post-bootstrap gitignore rewrite applied {len(rewritten)} line(s)",
            file=sys.stderr,
        )

plan_lines = plan.get("gitignore_merge_preview")
plan_list = [str(x) for x in plan_lines] if isinstance(plan_lines, list) else None

preview = compute_gitignore_merge_preview(repo_root)
recomputed_lines = list(preview.lines) if preview.eligible else []

if plan_list is not None and plan_list != recomputed_lines:
    print(
        "mat-sync: gitignore plan preview differed from post-bootstrap recompute; using recomputed lines",
        file=sys.stderr,
    )

if not recomputed_lines:
    reason = preview.skip_reason or "no_lines_to_append"
    print(f"mat-sync: post-bootstrap gitignore merge skipped ({reason})", file=sys.stderr)
    sys.exit(0)

result = apply_gitignore_merge(repo_root, lines=recomputed_lines)
if result.get("applied"):
    appended = result.get("appended_lines") or []
    print(
        f"mat-sync: post-bootstrap gitignore merge appended {len(appended)} line(s)",
        file=sys.stderr,
    )
else:
    reason = result.get("reason") or "unknown"
    print(f"mat-sync: post-bootstrap gitignore merge skipped ({reason})", file=sys.stderr)
PY
}

apply_gitignore_merge_on_approve() {
  local approved="$1"
  log "phase gate: gitignore merge (live recompute with plan fallback)"
  python3 - "${approved}" "${MAT_SOURCE_RESOLVED}" <<'PY' || die "gitignore merge helper failed"
import json, pathlib, sys

approved = pathlib.Path(sys.argv[1])
mat_source = pathlib.Path(sys.argv[2])
plan = json.loads(approved.read_text(encoding="utf-8"))
repo_root = pathlib.Path(plan["repo_root"])
for candidate in (mat_source / "scripts" / "adoption", repo_root / "scripts" / "adoption"):
    if (candidate / "mat_gitignore_merge.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit("mat-sync: mat_gitignore_merge helper not found")
from mat_gitignore_merge import apply_gitignore_merge, compute_gitignore_merge_preview
try:
    from mat_gitignore_merge import apply_gitignore_rewrite
except ImportError:
    apply_gitignore_rewrite = None

if apply_gitignore_rewrite is not None:
    rewrite_result = apply_gitignore_rewrite(repo_root)
    if rewrite_result.get("applied"):
        rewritten = rewrite_result.get("rewritten_lines") or []
        print(
            f"mat-sync: gitignore rewrite applied {len(rewritten)} line(s)",
            file=sys.stderr,
        )

plan_lines = plan.get("gitignore_merge_preview")
plan_list = [str(x) for x in plan_lines] if isinstance(plan_lines, list) else None

preview = compute_gitignore_merge_preview(repo_root)
recomputed_lines = list(preview.lines) if preview.eligible else []
lines_to_apply = recomputed_lines if recomputed_lines else (plan_list or [])

if recomputed_lines and plan_list is not None and plan_list != recomputed_lines:
    print(
        "mat-sync: gitignore plan preview differed from live recompute; using recomputed lines",
        file=sys.stderr,
    )

if not lines_to_apply:
    reason = preview.skip_reason or "no_preview_in_plan"
    print(f"mat-sync: gitignore merge skipped ({reason})", file=sys.stderr)
    sys.exit(0)

result = apply_gitignore_merge(repo_root, lines=lines_to_apply)
if result.get("applied"):
    appended = result.get("appended_lines") or []
    print(
        f"mat-sync: gitignore merge appended {len(appended)} line(s)",
        file=sys.stderr,
    )
else:
    reason = result.get("reason") or "unknown"
    print(f"mat-sync: gitignore merge skipped ({reason})", file=sys.stderr)
PY
}

apply_env_sample_merge_post_bootstrap() {
  local approved="$1"
  local mat_source="$2"
  log "phase gate: env sample merge (post-bootstrap recompute)"
  MAT_SCRIPT_HOME="${MAT_SCRIPT_HOME}" python3 - "${approved}" "${mat_source}" <<'PY' || die "env sample merge helper failed"
import json, os, pathlib, sys

approved = pathlib.Path(sys.argv[1])
mat_source = pathlib.Path(sys.argv[2])
mat_script_home = os.environ.get("MAT_SCRIPT_HOME", "")
plan = json.loads(approved.read_text(encoding="utf-8"))
repo_root = pathlib.Path(plan["repo_root"])

def _adoption_helper_dir(helper: str) -> pathlib.Path | None:
    for candidate in (
        mat_source / "scripts" / "adoption",
        repo_root / "scripts" / "adoption",
        pathlib.Path(mat_script_home) / "scripts" / "adoption" if mat_script_home else None,
    ):
        if candidate is not None and (candidate / helper).is_file():
            return candidate
    return None

env_dir = _adoption_helper_dir("mat_env_sample_merge.py")
if env_dir is None:
    raise SystemExit("mat-sync: mat_env_sample_merge helper not found")
sys.path.insert(0, str(env_dir))
from mat_env_sample_merge import apply_env_sample_merge, compute_env_sample_merge_preview

upstream = mat_source / ".mat.env.sample"
upstream_path = upstream if upstream.is_file() else None
plan_field = plan.get("env_sample_merge_preview")

preview = compute_env_sample_merge_preview(repo_root, upstream_path=upstream_path)
recomputed_field = preview.as_plan_field()

if plan_field is not None and recomputed_field != plan_field:
    print(
        "mat-sync: env sample plan preview differed from post-bootstrap recompute; using recomputed merge",
        file=sys.stderr,
    )

if not preview.eligible or preview.merged_text is None:
    reason = preview.skip_reason or "not_eligible"
    print(f"mat-sync: post-bootstrap env sample merge skipped ({reason})", file=sys.stderr)
    sys.exit(0)

result = apply_env_sample_merge(
    repo_root,
    upstream_path=upstream_path,
    merged_text=preview.merged_text,
)
if result.get("applied"):
    print("mat-sync: post-bootstrap env sample merge applied", file=sys.stderr)
else:
    reason = result.get("reason") or "unknown"
    print(f"mat-sync: post-bootstrap env sample merge skipped ({reason})", file=sys.stderr)
PY
}

apply_env_sample_merge_on_approve() {
  local approved="$1"
  local mat_source="$2"
  log "phase gate: env sample merge (live recompute with plan fallback)"
  MAT_SCRIPT_HOME="${MAT_SCRIPT_HOME}" python3 - "${approved}" "${mat_source}" <<'PY' || die "env sample merge helper failed"
import json, os, pathlib, sys

approved = pathlib.Path(sys.argv[1])
mat_source = pathlib.Path(sys.argv[2])
mat_script_home = os.environ.get("MAT_SCRIPT_HOME", "")
plan = json.loads(approved.read_text(encoding="utf-8"))
repo_root = pathlib.Path(plan["repo_root"])

def _adoption_helper_dir(helper: str) -> pathlib.Path | None:
    for candidate in (
        mat_source / "scripts" / "adoption",
        repo_root / "scripts" / "adoption",
        pathlib.Path(mat_script_home) / "scripts" / "adoption" if mat_script_home else None,
    ):
        if candidate is not None and (candidate / helper).is_file():
            return candidate
    return None

env_dir = _adoption_helper_dir("mat_env_sample_merge.py")
if env_dir is None:
    raise SystemExit("mat-sync: mat_env_sample_merge helper not found")
sys.path.insert(0, str(env_dir))
from mat_env_sample_merge import apply_env_sample_merge, compute_env_sample_merge_preview

upstream = mat_source / ".mat.env.sample"
upstream_path = upstream if upstream.is_file() else None
plan_field = plan.get("env_sample_merge_preview")

preview = compute_env_sample_merge_preview(repo_root, upstream_path=upstream_path)
recomputed_field = preview.as_plan_field()

if plan_field is not None and recomputed_field != plan_field:
    print(
        "mat-sync: env sample plan preview differed from live recompute; using recomputed merge",
        file=sys.stderr,
    )

if not preview.eligible or preview.merged_text is None:
    reason = preview.skip_reason or "not_eligible"
    print(f"mat-sync: env sample merge skipped ({reason})", file=sys.stderr)
    sys.exit(0)

result = apply_env_sample_merge(
    repo_root,
    upstream_path=upstream_path,
    merged_text=preview.merged_text,
)
if result.get("applied"):
    print("mat-sync: env sample merge applied", file=sys.stderr)
else:
    reason = result.get("reason") or "unknown"
    print(f"mat-sync: env sample merge skipped ({reason})", file=sys.stderr)
PY
}

phase_verify() {
  [[ "${SKIP_VERIFY}" -eq 1 ]] && {
    log "phase verify: skipped (--skip-verify)"
    return 0
  }

  local doctor_script="${TARGET_ROOT}/scripts/doctor.sh"
  local verify_script="${TARGET_ROOT}/scripts/phase1-verify.sh"
  [[ -x "${doctor_script}" || -f "${doctor_script}" ]] || die "missing ${doctor_script} on target"
  [[ -x "${verify_script}" || -f "${verify_script}" ]] || die "missing ${verify_script} on target"

  handoff_whitespace_preflight

  if [[ "${MAT_SYNC_SKIP_GITIGNORE_TRACKABILITY:-0}" != "1" ]] && [[ -d "${TARGET_ROOT}/.git" ]]; then
    log "phase verify: gitignore workflow trackability"
    local track_exit=0
    set +e
    python3 - "${TARGET_ROOT}" "${MAT_SOURCE_RESOLVED}" <<'PY' >&2
import json, pathlib, sys

repo_root = pathlib.Path(sys.argv[1])
mat_source = pathlib.Path(sys.argv[2])
for candidate in (mat_source / "scripts" / "adoption", repo_root / "scripts" / "adoption"):
    if (candidate / "mat_gitignore_merge.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    print("mat-sync: mat_gitignore_merge helper not found for trackability check", file=sys.stderr)
    sys.exit(2)
try:
    from mat_gitignore_merge import verify_workflow_paths_trackable
except ImportError:
    sys.exit(0)

result = verify_workflow_paths_trackable(repo_root)
if not result.get("git_available"):
    sys.exit(0)
still_ignored = result.get("still_ignored") or []
if still_ignored:
    for item in still_ignored:
        path = item.get("path", "unknown")
        rule = item.get("rule", "unknown")
        print(
            "mat-sync: .gitignore still ignores MAT workflow path "
            f"{path} (blocking rule: {rule}) — rewrite directory-ignore "
            ".cursor/ to .cursor/* then append MAT negations "
            "(re-run --approve-plan or: python3 scripts/adoption/mat_gitignore_merge.py "
            f"--repo-root {repo_root} rewrite-apply)",
            file=sys.stderr,
        )
    sys.exit(1)
sys.exit(0)
PY
    track_exit=$?
    set -e
    [[ "${track_exit}" -eq 0 ]] || die "gitignore workflow paths remain ignored (see stderr above)"
  fi

  log "phase verify: doctor"
  local doctor_exit=0
  set +e
  bash "${doctor_script}" >&2
  doctor_exit=$?
  set -e

  local verify_env=()
  if [[ -f "${TARGET_ROOT}/.mat/README.md" ]]; then
    verify_env=(env PHASE1_VERIFY_SKIP_BUN=1 PHASE1_VERIFY_SKIP_CLIENT=1)
  fi

  log "phase verify: phase1-verify"
  local verify_exit=0
  set +e
  (cd "${TARGET_ROOT}" && "${verify_env[@]}" bash scripts/phase1-verify.sh) >&2
  verify_exit=$?
  set -e

  if [[ "${verify_exit}" -ne 0 ]]; then
    die "phase1-verify failed (exit ${verify_exit})"
  fi

  if [[ "${doctor_exit}" -ne 0 ]]; then
    if [[ "${STRICT_DOCTOR}" -eq 1 ]]; then
      die "doctor failed (exit ${doctor_exit}) — phase1-verify passed but --strict-doctor requires doctor PASS"
    fi
    log "phase verify: doctor reported issues (exit ${doctor_exit}) — non-fatal because phase1-verify passed"
  fi
}

MAT_SOURCE_RESOLVED=""
if ! resolve_mat_source; then
  log "phase detect: could not resolve MAT source"
  mkdir -p "${TARGET_ROOT}/artifacts/mat-sync"
  ROUTE="stop"
  ROUTE_REASON="MAT source not found — set --source, --repository/--ref, .mat/source-config.json, sibling checkout, or MAT_SOURCE"
  DETECT_JSON='{"target_root":"'"${TARGET_ROOT}"'","mat_source":null,"sidecar_readme":false,"sidecar_agents_mat":false,"custom_agent_count":0,"custom_agents":[],"custom_skill_count":0,"custom_skills":[],"custom_command_count":0,"custom_commands":[]}'
  write_mat_sync_plan "${MAT_SCRIPT_HOME}" "" "blocked"
  log "phase route: stop (${ROUTE_REASON})"
  exit 2
fi

BOOTSTRAP_SCRIPT="${MAT_SOURCE_RESOLVED}/scripts/adoption/bootstrap-workflow-into-repo.sh"
UPDATE_SCRIPT="${MAT_SOURCE_RESOLVED}/scripts/adoption/update-mat.py"

phase_detect "${MAT_SOURCE_RESOLVED}"

if [[ -n "${APPROVE_PLAN_ARG}" ]]; then
  phase_gate "${MAT_SOURCE_RESOLVED}"
  phase_verify
  log "complete: sync finished (no git commit on target root)"
  exit 0
fi

phase_route "${MAT_SOURCE_RESOLVED}"
phase_plan "${MAT_SOURCE_RESOLVED}"

log "next: review ${PLAN_FILE} and rerun with --approve-plan <plan.json> to mutate"
if [[ "${ROUTE}" == "stop" ]] || [[ "${CONFLICT_STATE:-clear}" == "blocked" ]]; then
  exit 2
fi
exit 0