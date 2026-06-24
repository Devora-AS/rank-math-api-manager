# Current plan

## Slice

**v1.0.9.2 release hardening — planning approved (Phase B closeout)**

- **Status:** Planning **approved** — Phase C **ready**
- **Next slice:** **TASK-001** — Version and documentation sync
- **Package:** [`specs/v1-0-9-2/`](../specs/v1-0-9-2/) (`prd.md`, `spec.md`, `tasks.json`, `plan-summary.md`)
- **Branch:** `feature/v1.0.9.2`
- **PR strategy (OQ-006):** Single PR `feature/v1.0.9.2` → `main`; logical local commits per TASK-### during Phase C

## Task

Planning package complete and operator-approved. **Do not implement TASK-001+ in this document** — project TASK-001 into a new `/mat-plan-team` or `/mat-long-run` slice when starting Phase C.

## Phase C execution order

Per [`specs/v1-0-9-2/tasks.json`](../specs/v1-0-9-2/tasks.json):

1. **TASK-001** — Version/docs sync (`docs/README.md` → 1.0.9.2) ← **next**
2. **TASK-002** — Land QA toolchain (composer, phpcs, phpunit, tests)
3. **TASK-003** — Land CI workflows; `release.yml` + `qa.yml` php-lint **maxdepth 5** (OQ-005)
4. **TASK-004** — Land packaging, icons, plugin WIP; verify CI green
5. **TASK-005** — PHPCS main-file follow-up (optional/deferred)
6. **TASK-006** — PR checklist and release smoke (single PR to `main`)

Start via `/mat-long-run` or `/mat-plan-team` projecting **TASK-001** from the package.

## Operator decisions (2026-06-24)

| ID | Resolution |
|----|------------|
| OQ-005 | `release.yml` find maxdepth **5** (match `qa.yml`) — TASK-003 |
| OQ-006 | Single PR to `main`; local commits per task |

## Definition of Done (planning)

- [x] `specs/v1-0-9-2/` package complete and cross-traced
- [x] `build-result.md` / `verify-result.md` PASS
- [x] Operator approval gate (plan-summary checklist)
- [x] OQ-005 / OQ-006 recorded as resolved

## Non-goals

MAT adoption, `update-mat --apply`, `.cursor/` git policy, RFU-7 observability. Phase B did not land product WIP.

## Validation

```bash
bash scripts/phase1-verify.sh
```

## Closeout

Package approved — ready for Phase C **TASK-001**. See [`specs/v1-0-9-2/plan-summary.md`](../specs/v1-0-9-2/plan-summary.md).
