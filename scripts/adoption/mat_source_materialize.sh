#!/usr/bin/env bash
# mat_source_materialize.sh — clone or reuse cached MAT upstream checkout.
set -euo pipefail

REPOSITORY=""
REF=""
CACHE_DIR="${HOME}/.cache/mat-source"
JSON_OUT=0

usage() {
  cat <<'EOF'
Usage:
  mat_source_materialize.sh --repository OWNER/REPO --ref REF [--cache-dir DIR] [--json]

Environment:
  MAT_SOURCE_CLONE_URL   Optional clone URL override (tests: file:///path/to/bare.git)

Outputs:
  --json                 Resolution JSON on stdout (mat_source, provenance fields)
  default                Absolute mat_source path on stdout
EOF
}

log() {
  printf 'mat_source_materialize: %s\n' "$*" >&2
}

die() {
  log "error: $*"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repository)
      [[ $# -ge 2 ]] || die "--repository requires a value"
      REPOSITORY="$2"
      shift 2
      ;;
    --ref)
      [[ $# -ge 2 ]] || die "--ref requires a value"
      REF="$2"
      shift 2
      ;;
    --cache-dir)
      [[ $# -ge 2 ]] || die "--cache-dir requires a path"
      CACHE_DIR="$2"
      shift 2
      ;;
    --json)
      JSON_OUT=1
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

[[ -n "${REPOSITORY}" ]] || die "--repository is required"
[[ -n "${REF}" ]] || die "--ref is required"

slug="${REPOSITORY//\//-}"
expanded_cache_dir="${CACHE_DIR/#\~/${HOME}}"
cache_path="${expanded_cache_dir}/${slug}"
clone_url="${MAT_SOURCE_CLONE_URL:-https://github.com/${REPOSITORY}.git}"

mkdir -p "${expanded_cache_dir}"

if [[ -d "${cache_path}/.git" ]]; then
  git -C "${cache_path}" fetch origin --prune
else
  git clone "${clone_url}" "${cache_path}"
fi

git -C "${cache_path}" fetch origin "${REF}"
git -C "${cache_path}" checkout --detach FETCH_HEAD

update_mat="${cache_path}/scripts/adoption/update-mat.py"
if [[ ! -f "${update_mat}" ]]; then
  die "missing scripts/adoption/update-mat.py after checkout: ${cache_path}"
fi

mat_source="$(cd "${cache_path}" && pwd)"
resolved_sha="$(git -C "${cache_path}" rev-parse HEAD)"
materialized_at="$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")"

if [[ "${JSON_OUT}" -eq 1 ]]; then
  python3 - "${mat_source}" "${REPOSITORY}" "${REF}" "${resolved_sha}" "${cache_path}" "${materialized_at}" <<'PY'
import json, sys

mat_source, repository, requested_ref, resolved_sha, cache_path, materialized_at = sys.argv[1:7]
print(
    json.dumps(
        {
            "mat_source": mat_source,
            "repository": repository,
            "requested_ref": requested_ref,
            "resolved_sha": resolved_sha,
            "cache_path": cache_path,
            "materialized_at": materialized_at,
        },
        indent=2,
        sort_keys=True,
    )
)
PY
else
  printf '%s\n' "${mat_source}"
fi
