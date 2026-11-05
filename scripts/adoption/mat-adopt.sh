#!/usr/bin/env bash
# mat-adopt.sh — thin first-adoption installer: resolve/materialize MAT source → mat-sync.sh
# Plan-only by default; pass --approve-plan to mutate. No duplicate merge engine.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PY="${SCRIPT_DIR}/mat_source_config.py"
MATERIALIZE_SH="${SCRIPT_DIR}/mat_source_materialize.sh"
DEFAULT_REF="main"
CACHE_DIR="${HOME}/.cache/mat-source"

REPO_ROOT_ARG=""
REPOSITORY_ARG=""
REF_ARG=""
APPROVE_PLAN_ARG=""

usage() {
  cat <<'EOF'
mat-adopt.sh — first existing-project adoption (delegates to mat-sync.sh)

Usage:
  mat-adopt.sh --repo-root PATH [--repository OWNER/REPO] [--ref REF]
               [--approve-plan PLAN.json] [--help]

Defaults:
  Plan-only (dry-run) — no bootstrap without --approve-plan matching latest plan.
  When --repository is set without --ref, ref defaults to main for materialize.

MAT source resolution:
  1. When this script lives inside a MAT source tree, delegate to that tree's mat-sync.sh.
  2. Otherwise --repository (and optional --ref) materializes upstream via mat_source helpers.

Examples:
  mat-adopt.sh --repo-root "/path/to/product" \
    --repository Devora-AS/multi-agent-workflow --ref main
  mat-adopt.sh --repo-root "/path/to/product" \
    --approve-plan "/path/to/product/artifacts/mat-sync/latest-plan.json"
EOF
}

log() {
  printf 'mat-adopt: %s\n' "$*" >&2
}

die() {
  log "error: $*"
  exit 1
}

is_mat_source_tree() {
  local root="$1"
  [[ -f "${root}/scripts/adoption/update-mat.py" ]]
}

materialize_inline() {
  local repository="$1"
  local ref="$2"
  local slug="${repository//\//-}"
  local cache_path="${CACHE_DIR}/${slug}"
  local clone_url="${MAT_SOURCE_CLONE_URL:-https://github.com/${repository}.git}"

  mkdir -p "${CACHE_DIR}"

  if [[ -d "${cache_path}/.git" ]]; then
    git -C "${cache_path}" fetch origin --prune
  else
    git clone "${clone_url}" "${cache_path}"
  fi

  git -C "${cache_path}" fetch origin "${ref}"
  git -C "${cache_path}" checkout --detach FETCH_HEAD

  if [[ ! -f "${cache_path}/scripts/adoption/update-mat.py" ]]; then
    die "materialize missing scripts/adoption/update-mat.py under ${cache_path}"
  fi

  (cd "${cache_path}" && pwd)
}

resolve_materialized_source() {
  local target_root="$1"
  local repository="$2"
  local ref="$3"

  if [[ -f "${MATERIALIZE_SH}" ]]; then
    bash "${MATERIALIZE_SH}" --repository "${repository}" --ref "${ref}" --cache-dir "${CACHE_DIR}"
    return 0
  fi

  if [[ -f "${CONFIG_PY}" ]]; then
    python3 "${CONFIG_PY}" resolve \
      --repo-root "${target_root}" \
      --repository "${repository}" \
      --ref "${ref}"
    return 0
  fi

  materialize_inline "${repository}" "${ref}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      [[ $# -ge 2 ]] || die "--repo-root requires a path"
      REPO_ROOT_ARG="$2"
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
    --approve-plan)
      [[ $# -ge 2 ]] || die "--approve-plan requires a plan JSON path"
      APPROVE_PLAN_ARG="$2"
      shift 2
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

[[ -n "${REPO_ROOT_ARG}" ]] || die "--repo-root is required (try --help)"

TARGET_ROOT="$(cd "${REPO_ROOT_ARG}" && pwd)"

MAT_SYNC=""
if [[ -f "${SCRIPT_DIR}/../mat-sync.sh" ]] && is_mat_source_tree "$(cd "${SCRIPT_DIR}/../.." && pwd)"; then
  MAT_SYNC="$(cd "${SCRIPT_DIR}/.." && pwd)/mat-sync.sh"
else
  [[ -n "${REPOSITORY_ARG}" ]] || die \
    "--repository is required when mat-adopt.sh is not run from a MAT source checkout"
  REF_EFFECTIVE="${REF_ARG:-${DEFAULT_REF}}"
  MAT_SOURCE="$(resolve_materialized_source "${TARGET_ROOT}" "${REPOSITORY_ARG}" "${REF_EFFECTIVE}")"
  MAT_SYNC="${MAT_SOURCE}/scripts/mat-sync.sh"
fi

[[ -f "${MAT_SYNC}" ]] || die "mat-sync.sh not found: ${MAT_SYNC}"

cmd=(bash "${MAT_SYNC}" --repo-root "${TARGET_ROOT}")

if [[ -n "${REPOSITORY_ARG}" ]]; then
  cmd+=(--repository "${REPOSITORY_ARG}")
  if [[ -n "${REF_ARG}" ]]; then
    cmd+=(--ref "${REF_ARG}")
  else
    cmd+=(--ref "${DEFAULT_REF}")
  fi
fi

if [[ -n "${APPROVE_PLAN_ARG}" ]]; then
  cmd+=(--approve-plan "${APPROVE_PLAN_ARG}")
fi

log "delegating to ${MAT_SYNC}"
exec "${cmd[@]}"
