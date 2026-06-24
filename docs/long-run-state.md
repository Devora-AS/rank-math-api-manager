# Long-run mission state

**Mission:** Ship v1.0.9.2 release hardening on `feature/v1.0.9.2`
**Last updated:** 2026-06-24
**Branch:** `feature/v1.0.9.2`
**Package:** [`specs/v1-0-9-2/`](../specs/v1-0-9-2/)

---

## Mission

- **Goal:** Land v1.0.9.2 release-hardening WIP with CI/QA green, single PR strategy (OQ-006), and no MAT adoption regressions.
- **execution_mode:** `long-run`
- **Success signals:** TASK-001..004 and TASK-006 done with verify PASS; TASK-005 explicitly skipped; logical local commit per completed TASK; operator can push/open PR.

## Scope / hard constraints / non-goals

- **Hard constraints:**
  - One PR `feature/v1.0.9.2` → `main` (OQ-006); logical local commit per completed TASK-###.
  - Do NOT modify `.mat/` adoption sidecar except `tasks.json` status sync + long-run handoffs.
  - Do NOT run `update-mat.py --apply`.
  - Do NOT push to GitHub unless operator explicitly asks.
  - TASK-003: `release.yml` AND `qa.yml` php-lint `find -maxdepth 5` (OQ-005).
  - TASK-005: SKIP — deferred OQ-002; do not block mission.
  - `php -l` on changed `*.php` each slice; composer/phpunit when TASK-002+ touches toolchain.
- **Non-goals:** MAT hooks/MAO gate changes, RFU-7 observability, `.cursor/` git policy, PHPCS main-file (TASK-005).

## Slice preflight decision (active)

- **execution_mode:** `builder_plus_verifier`
- **execution_rationale:** TASK-001 is docs-only but verifier runs read-only checks; builder implements, verifier validates version grep + phase1-verify.

## Ordered slice queue

| # | Slice id | TASK | Summary | execution_mode | Status |
|---|----------|------|---------|----------------|--------|
| 1 | `task-001` | TASK-001 | Version and documentation sync | `builder_plus_verifier` | `done` |
| 2 | `task-002` | TASK-002 | Land QA toolchain files | `builder_plus_verifier` | `done` |
| 3 | `task-003` | TASK-003 | CI workflows + release maxdepth 5 | `builder_plus_verifier` | `done` |
| 4 | `task-004` | TASK-004 | Packaging, icons, plugin WIP + CI verify | `builder_plus_verifier` | `in_progress` |
| 5 | `task-005` | TASK-005 | PHPCS main-file (optional) | `skipped` | `skipped` — deferred OQ-002 |
| 6 | `task-006` | TASK-006 | Release smoke + PR checklist | `builder_plus_verifier` | `pending` |

## Active slice

- **Slice id:** `task-006`
- **TASK:** TASK-006 — Release smoke + PR checklist
- **Pointer:** `docs/current-plan.md`
- **execution_mode:** `builder_plus_verifier`
- **execution_rationale:** Land composer/phpcs/phpunit/tests; run composer validate + phpunit if env allows.

## Completed slices

| Slice id | TASK | Outcome | Commit | Notes |
|----------|------|---------|--------|-------|
| `task-004` | TASK-004 | PASS | `39f2fcf` | Packaging, icons, plugin WIP |

## Continuation policy

- **Default:** After each verifier PASS, run post-slice mission gate; advance to next pending slice unless `hard_blocker` or `approval_needed`.
- **Skip TASK-005:** Do not spawn; mark `skipped` in queue and `tasks.json`.
- **MAO per slice:** Reset canonical three todos for each new slice (plan → build → verify).

## Stop-reason policy

| Stop reason | Meaning |
|-------------|---------|
| `mission_complete` | TASK-001..004 + TASK-006 PASS; TASK-005 skipped; session-summary written. |
| `hard_blocker` | Composer, WP test install, CI, or repeated builder/verifier failure. |
| `approval_needed` | Push, PR open, merge, or TASK-005 override requires operator. |
| `planning_gap` | Queue empty but mission goal not satisfied. |
| `unexpected_termination` | Abnormal end; partial state recorded. |

---

## Parent mission gate compliance (per verifier PASS)

**Honesty boundary:** Hooks do **not** enforce this gate. Compliance is parent-owned.

- [ ] Gate questions answered or one explicit stop reason recorded.
- [ ] Slice PASS not mislabeled as mission success while queue has pending slices.

---

## Current stop / continuation (living)

- **Last classified stop reason:** _(none — mission started)_
- **Continue:** `yes` — active slice TASK-001
