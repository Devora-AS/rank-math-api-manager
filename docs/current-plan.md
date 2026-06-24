# Current plan

## Slice

**v1.0.9.2 release hardening — planning package (Phase B)**

- **Status:** Planning complete — Phase C **not started**
- **Package:** [`specs/v1-0-9-2/`](../specs/v1-0-9-2/) (`prd.md`, `spec.md`, `tasks.json`, `plan-summary.md`)
- **Branch:** `feature/v1.0.9.2`
- **Preflight:** `builder_plus_verifier` (planning slice)

## Task

Planning-only slice: produce approved onboarding package from existing WIP. **No Phase C implementation** — no landing of untracked composer/tests/qa.yml/assets in this slice.

## Phase C (next — operator approval required)

Execution order per [`specs/v1-0-9-2/tasks.json`](../specs/v1-0-9-2/tasks.json):

1. **TASK-001** — Version/docs sync (`docs/README.md` → 1.0.9.2)
2. **TASK-002** — Land QA toolchain (composer, phpcs, phpunit, tests)
3. **TASK-003** — Land CI workflows (`qa.yml`, `release.yml` alignment)
4. **TASK-004** — Land packaging, icons, plugin WIP; verify CI green
5. **TASK-005** — PHPCS main-file follow-up (optional/deferred)
6. **TASK-006** — PR checklist and release smoke

Start via `/mat-long-run` or per-slice `/mat-plan-team` after reviewing [`specs/v1-0-9-2/plan-summary.md`](../specs/v1-0-9-2/plan-summary.md).

## Definition of Done (planning slice)

- [x] `specs/v1-0-9-2/` package complete and cross-traced
- [x] `docs/current-plan.md` links package; Phase C marked not started
- [ ] `build-result.md` — builder PASS
- [ ] `verify-result.md` — verifier PASS
- [ ] Operator approval gate (plan-summary checklist)

## Non-goals

MAT adoption, `update-mat --apply`, `.cursor/` git policy, RFU-7 observability, commit/push/merge.

## Validation

```bash
bash scripts/phase1-verify.sh
```

## Closeout

Planning artifacts ready for operator review. Phase C lands WIP per `tasks.json` in separate slices.
