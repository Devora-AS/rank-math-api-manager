# Current plan — slice `coverage-ci-tests`

**Tier:** standard  
**Branch:** `feat/coverage-phpcs-quality-mission`  
**Spec:** `specs/plugin-coverage-phpcs-mission.md`

## Goal

Add pcov coverage gate (80% lines on main file), risk-based integration tests, and CI enforcement in `qa.yml`.

## Implementation steps

- [x] Configure `phpunit.xml.dist` coverage include for `rank-math-api-manager.php`
- [x] Add `scripts/check-plugin-coverage.sh` threshold script
- [x] Extend `qa.yml` PHPUnit job with pcov + coverage gate
- [x] Add integration tests (permissions, telemetry, uninstall, updater, meta auth, admin notices smoke)
- [x] PHPCS on new test files

## Acceptance criteria

- [x] `./scripts/run-phpunit-local.sh` passes (25 tests, 1 skipped WC)
- [ ] `./scripts/check-plugin-coverage.sh` ≥80% (CI authoritative when local pcov absent)
- [x] `vendor/bin/phpcs --standard=phpcs.xml.dist` passes
- [ ] GitHub QA workflow green on PR

## Verification plan

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| PHPUnit | `./scripts/run-phpunit-local.sh` | Loop until pass |
| PHPCS | `vendor/bin/phpcs --standard=phpcs.xml.dist` | Loop until pass |
| Coverage | `./scripts/check-plugin-coverage.sh` | Loop until pass in CI |

### Global validation commands (before handoff)

1. `vendor/bin/phpcs --standard=phpcs.xml.dist`
2. `./scripts/run-phpunit-local.sh`
3. GitHub `gh pr checks` on PR

## Amendments

- 2026-11-05T12:00:00Z — orchestrator — Slice 2 plan projected after TASK-005 commit.
