# Spec: Plugin coverage gate + PHPCS main file (TASK-005)

**Preflight classification:** `ready_for_execution_handoff`

**Task type:** `enhancement`  
**Complexity:** `complex`

## Task Description

Enable PHPUnit line coverage for `rank-math-api-manager.php` with pcov in CI (initial gate 80%), expand risk-based integration tests (REST permissions, updater, telemetry privacy, uninstall), and bring the main plugin file under PHPCS by removing the `phpcs.xml.dist` exclude after WPCS fixes.

## Objective

Production-quality hygiene: green PHPCS including main file, measurable coverage with CI enforcement, and regression tests for security-sensitive paths.

## Scope

- PHPCS: `phpcbf`, manual WPCS fixes, remove exclude pattern, green `qa.yml` PHPCS job.
- Coverage: `phpunit.xml.dist` coverage include, `scripts/check-plugin-coverage.sh`, extend `qa.yml` PHPUnit job with pcov + threshold.
- Tests: new integration tests under `tests/integration/` for permissions, telemetry opt-out, uninstall cleanup, updater edge paths, sanitizers.

## Assumptions

- MySQL-backed WP test suite remains the integration harness (`tests/bootstrap.php`).
- WooCommerce product test may remain skipped without WC in CI unless a follow-up adds WC install.
- 80% line coverage applies to `rank-math-api-manager.php` only (not `.mat/` or scripts).

## Non-Goals

- 100% line coverage on every branch in one slice.
- Refactoring plugin into multiple PHP files.
- Playwright E2E of wp-admin notices.

## Problem Statement

Main file was excluded from PHPCS; coverage is unmeasured; critical paths (permissions, telemetry, uninstall) lack dedicated regression tests.

## Solution Approach

Two ordered long-run slices: (1) PHPCS TASK-005, (2) coverage tooling + risk-based tests + CI gate. Each slice: plan → build → verify → commit → PR → merge when green.

## Relevant Files / Areas

- [existing] `rank-math-api-manager.php` — PHPCS fixes and coverage target
- [existing] `phpcs.xml.dist` — remove main-file exclude
- [existing] `phpunit.xml.dist` — coverage configuration
- [existing] `.github/workflows/qa.yml` — pcov + coverage check
- [new] `scripts/check-plugin-coverage.sh` — threshold enforcement
- [new] `tests/integration/*Test.php` — permissions, telemetry, uninstall, updater

## Task Traceability

| Task | Requirement |
|------|-------------|
| PHPCS slice | Main file in ruleset; `vendor/bin/phpcs --standard=phpcs.xml.dist` exit 0 |
| Coverage slice | pcov in CI; ≥80% lines on main file |
| REST/security tests | Map to permission callbacks and REST routes |
| Telemetry tests | Opt-out sends no HTTP; enabled uses validated endpoint only |
| Uninstall tests | Options cleared after uninstall hook |

## Testing Strategy

Risk-based integration tests first; coverage gate validates aggregate line coverage on the main file. TDD for new test files (red → green where behavior already exists).

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| PHPCS | `vendor/bin/phpcs --standard=phpcs.xml.dist` | Re-run after fixes until exit 0 |
| PHPUnit | `./scripts/run-phpunit-local.sh` | Re-run until green |
| Coverage | `./scripts/check-plugin-coverage.sh` | Re-run after adding tests until threshold met |
| Package | `./scripts/package-plugin.sh` | Once per slice closeout |

### Global validation commands (before handoff)

1. `vendor/bin/phpcs --standard=phpcs.xml.dist`
2. `./scripts/run-phpunit-local.sh`
3. `./scripts/check-plugin-coverage.sh`
4. `bash scripts/phase1-verify.sh` (if MAT gates apply)

Hard orchestration gates remain `build-result.md` / `verify-result.md`.

## Acceptance Criteria

- [ ] `phpcs.xml.dist` does not exclude `rank-math-api-manager.php` and PHPCS passes.
- [ ] CI PHPCS job passes on PR.
- [ ] PHPUnit reports ≥80% line coverage for `rank-math-api-manager.php`.
- [ ] New integration tests cover REST permission denial, telemetry opt-out, and uninstall option cleanup.
- [ ] PR merged to `main` with green QA workflow.

## Risks and Open Questions

- Hitting 80% may require additional tests for admin notices/GitHub HTTP paths.
- Local pcov may be absent; CI is authoritative for coverage gate.

## Amendments

- 2026-11-05T10:30:00Z — orchestrator — Initial spec for coverage + PHPCS mission.

## Recommended Next Command

Project into `docs/current-plan.md` and run `/mat-long-run` with slice queue `task-005-phpcs` then `coverage-ci-tests`.
