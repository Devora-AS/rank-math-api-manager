# Long-run mission state — coverage + PHPCS quality

**Last updated:** 2026-11-05

---

## Mission

- **Goal:** PHPCS on main plugin file (TASK-005) + PHPUnit coverage gate (80% lines on `rank-math-api-manager.php`) with risk-based integration tests.
- **execution_mode:** `long-run`
- **Branch:** `feat/coverage-phpcs-quality-mission`
- **Spec:** `specs/plugin-coverage-phpcs-mission.md`

## Slice preflight decision (active)

- **execution_mode:** `builder_plus_verifier`
- **execution_rationale:** PHPCS mass-format plus new tests and CI; builder implements, verifier validates read-only.

## Ordered slice queue

| # | Slice id | Summary | Status |
|---|----------|---------|--------|
| 1 | `task-005-phpcs` | phpcbf + WPCS fixes; remove PHPCS exclude; green PHPCS | `in_progress` |
| 2 | `coverage-ci-tests` | pcov, coverage script, integration tests, qa.yml gate | `pending` |

## Active slice

- **Slice id:** `task-005-phpcs`
- **Pointer:** `docs/current-plan.md`

## Continuation policy

- After slice 1: commit, PR, merge when CI green.
- After slice 2: commit, PR, merge when CI green including coverage.

## Stop-reason policy

| Stop reason | Meaning |
|-------------|---------|
| `mission_complete` | Both slices merged; QA green |
| `hard_blocker` | Cannot run tests or CI |
| `approval_needed` | Scope beyond spec |

## Parent mission gate compliance

- [ ] Slice 1 PASS not labeled as full mission complete while slice 2 pending.

## Current stop / continuation

- **Continue:** `yes`
- **Last classified stop reason:** _(none — mission active)_
