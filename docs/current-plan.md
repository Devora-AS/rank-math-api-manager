# Current plan

## Task

First real MAT adoption on rank-math-api-manager (bootstrap slice on `chore/mat-adoption`).

## DoR

- Bootstrap completed with `bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive`.
- `.mat/` sidecar and `.cursor/` workflow surfaces exist on disk.
- `bash scripts/phase1-verify.sh` and `bash scripts/doctor.sh` exit 0 before enabling hooks.

## Binary acceptance criteria

- [x] `.mat/` and `.cursor/` present after bootstrap.
- [x] `bash scripts/phase1-verify.sh` exits 0.
- [x] `bash scripts/doctor.sh` exits 0.
- [x] No plugin PHP modified by bootstrap (`rank-math-api-manager.php` hash unchanged).
- [x] Single local MAT-only commit on `chore/mat-adoption` (no push unless operator approves).

## Non-goals

- No `update-mat.py --apply` in this slice.
- No observability apps/server stack (RFU-7 deferred per appendix).
- No merge of in-flight v1.0.9.2 plugin work into the MAT commit.

## Verification plan

### First slice validation gate

- **PHP syntax:** `php -l` on changed PHP files (matches `.github/workflows/release.yml` intent).
- **MAT contract:** `bash scripts/phase1-verify.sh`.
- **Operator readiness:** `bash scripts/doctor.sh`.

### Hooks

Enable incrementally after `doctor` is clean. Review `.cursor/hooks.json` and Python hook dependencies before copying secrets into `.env`.

### Observability

Defer per [`.mat/docs/adoption-observability-appendix.md`](../.mat/docs/adoption-observability-appendix.md): opt-in only, manual `events.sqlite` rotation, no shipped automatic purge.
