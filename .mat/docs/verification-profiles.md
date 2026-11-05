# Verification profiles (v1)

Named Phase 1 verification profiles make green status honest: every run states which profile executed, and `artifacts/phase1/verification-manifest.json` records pass / fail / skip with reasons.

## Profiles

| Profile | Tree | Behavior |
|---------|------|----------|
| `source-full` | MAT source (no `.mat/README.md`) | All checks: workflow/planning artifacts, unit tests, legacy fingerprints, Bun server + client. **Fails** (does not skip) when Bun checks cannot run — use `source-python-only` for Bun-free loops. |
| `source-python-only` | MAT source | Python/docs checks only; Bun server/client recorded as **skip** (never pass) |
| `adopted-operational` | Adopted sidecar (`.mat/README.md` present) | Default adopted skips documented; source-only checks skipped; Bun checks skipped; **`.mat/tests` skipped**; **`adopted-sidecar` doc link validation skipped** (operational green ≠ full contract graph) |
| `adopted-contract` | Adopted sidecar | Same as operational, but runs packaged `.mat/tests` (`PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1`), **`adopted-sidecar` doc link validation**, and records `doc_link_validation` pass; Bun checks skipped |

**Staging worktree:** `update-mat.py --apply` leaves the **live** `--repo-root` unchanged; run `phase1-verify` / `validate_doc_links` from the **`staging-worktree=`** path to preflight staged output, then again from the live root after you promote. See [`getting-started-existing-projects.md`](../guides/getting-started-existing-projects.md).

## Defaults

- Source tree → `source-full`
- Adopted sidecar → `adopted-operational`

Override with:

```bash
bash scripts/phase1-verify.sh --profile source-full
bash scripts/phase1-verify.sh --profile source-python-only --manifest artifacts/phase1/verification-manifest.json
```

Plain `bash scripts/phase1-verify.sh` remains supported (auto-selects the default profile).

## Manifest

Schema: `artifacts/verification-manifest.schema.json`  
Default runtime path: `artifacts/phase1/verification-manifest.json` (gitignored)

```json
{
  "profile": "source-full",
  "repo_layout": "source",
  "started_at": "2026-08-24T10:00:00Z",
  "finished_at": "2026-08-24T10:05:00Z",
  "overall": "pass",
  "checks": [
    {"id": "workflow_artifacts", "status": "pass", "reason": "...", "duration_ms": 12},
    {"id": "bun_server_smoke", "status": "skip", "reason": "source-python-only profile excludes Bun checks", "duration_ms": 0}
  ]
}
```

### Honesty rules

- **skip ≠ pass** — skipped checks must use `status: skip` and a non-empty `reason`.
- **Placeholder guard** — empty / `true` / `:` verify commands cannot record `pass`.
- **Green manifest completeness** — `overall: pass` requires every stable CHECK_ID exactly once; profile-planned `run` checks must be `pass`; profile must match `repo_layout`.
- **Early exit** — `phase1_verify_exit` is recorded only on abnormal script exit; it is not part of the stable pass set.

## Doctor

```bash
bash scripts/doctor.sh --verification-profile
```

Default `doctor` output also prints the resolved default profile and points here.

## CI

Release CI runs:

```bash
bash scripts/phase1-verify.sh --profile source-full --manifest artifacts/phase1/verification-manifest.json
```

Adopted fixture job documents and runs `adopted-contract` via `scripts/ci/run-adopted-contract-verify.sh` (includes `validate_doc_links --profile adopted-sidecar` before `phase1-verify`).

On the MAT **source** tree, `doc_link_validation` runs `source` + `source-archive` profiles. See [`doc-link-validation.md`](doc-link-validation.md).

## Implementation

- `scripts/verification_profiles.py` — registry, manifest writer/validator, CLI
- `scripts/phase1-verify.sh` — `--profile` / `--manifest`, per-check recording (includes `scope_audit` self-test on source trees)
- `tests/test_verification_profiles.py` — schema, skip≠pass, placeholder guard
- `scripts/mat-scope-audit.py` — advisory role scope audit (`check --self-test` = `scope_audit` check)
- **Observability security (E6-baseline):** covered by `python_unittest` via `tests/test_observability_security.py` (redaction patterns, bind fail-closed, purge `--dry-run`) and Bun server tests (`apps/server/src/security.test.ts`) under `bun_server_smoke` / `bun test` — no separate CHECK_ID; see `specs/observability-security-baseline-v1.md`

## Related

- Normative spec: [`specs/verification-profiles-v1.md`](specs/verification-profiles-v1.md)
- Manifest schema: `artifacts/verification-manifest.schema.json`
- Validator module: `scripts/verification_profiles.py`
