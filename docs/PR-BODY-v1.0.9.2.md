# PR: v1.0.9.2 — Page support, updater icons, and QA hardening

**Title:** `feat(release): v1.0.9.2 page support, updater icons, and CI QA`

**Base:** `main` ← **Head:** `feature/v1.0.9.2`

## Summary

- Add WordPress **page** support to `/update-meta` alongside posts and WooCommerce products.
- Ship plugin **icons** in the GitHub updater response and release ZIP (`assets/images/`).
- Land **QA toolchain** (Composer, PHPCS, PHPUnit) and **`qa.yml`** CI (php-lint, phpcs, plugin-check, package-smoke, phpunit).
- Align **`release.yml`** packaging with `scripts/package-plugin.sh` and php-lint `find -maxdepth 5`.
- Bump version and docs to **1.0.9.2**; TASK-005 PHPCS main-file follow-up deferred (OQ-002).

## Acceptance criteria (AC-001–AC-012)

| ID | Criterion | Status |
|----|-----------|--------|
| AC-001 | Version strings `1.0.9.2` | TASK-001 (`3f38103`) |
| AC-002 | Page `/update-meta` + unsupported type error | TASK-004 + integration tests |
| AC-003 | Post/product regression tests | `tests/integration/UpdateMetaPostTest.php`, `UpdateMetaProductTest.php` |
| AC-004 | Updater icon URLs | `rank-math-api-manager.php:1568-1571`, `1741-1744` |
| AC-005 | ZIP contains icon PNGs + SVG | `qa.yml` package-smoke; `scripts/package-plugin.sh` |
| AC-006 | ZIP excludes dev artifacts | `qa.yml:122-125`, `release.yml` verify |
| AC-007 | `qa.yml` all jobs on PR | Operator: push branch and confirm Actions green |
| AC-008 | PHPUnit in CI (MySQL + install-wp-tests) | `qa.yml:128-174` |
| AC-009 | `release.yml` php-lint maxdepth 5 | `release.yml:50`, `qa.yml:35` |
| AC-010 | PR checklist mappable to shipped files | `docs/PR-CHECKLIST-v1.0.9.2.md` |
| AC-011 | verification-matrix manual + automated | `docs/verification-matrix.md` |
| AC-012 | CHANGELOG documents pages + icons | `CHANGELOG.md:18-22` |

## Task commits

| TASK | Commit | Message |
|------|--------|---------|
| TASK-001 | `3f38103` | docs(release): TASK-001 version and documentation sync |
| TASK-002 | `793b90e` | chore(qa): TASK-002 land QA toolchain files |
| TASK-003 | `c30bdbc` | chore(ci): TASK-003 land QA workflow and align release lint scope |
| TASK-004 | `39f2fcf` | feat(release): TASK-004 packaging icons and plugin WIP |
| TASK-005 | — | skipped (OQ-002 PHPCS main-file follow-up) |
| TASK-006 | *(this PR)* | docs(release): TASK-006 PR checklist and release smoke |

## Test plan

- [ ] Push `feature/v1.0.9.2` and confirm **QA** workflow green: php-lint, phpcs, plugin-check, package-smoke, phpunit.
- [ ] Review PR against `docs/PR-CHECKLIST-v1.0.9.2.md`.
- [ ] Optional local: `composer install && vendor/bin/phpcs`; `bash scripts/package-plugin.sh` and inspect ZIP icon paths.
- [ ] Optional local PHPUnit: set `WP_TESTS_DIR` per `docs/verification-matrix.md` (LocalWP / install-wp-tests).
- [ ] After merge: tag `v1.0.9.2`, run `release.yml`, verify `rank-math-api-manager.zip` on GitHub release.
- [ ] Smoke on staging: update-meta for a **page** ID; confirm plugin icon in Plugins / update modal.

## Operator notes

- Do **not** merge until CI is green on the PR.
- TASK-005 remains skipped; `rank-math-api-manager.php` may stay excluded from PHPCS until a follow-up slice.
- Design-only assets (`icon-direction-*.svg`, `icon-proof.html`) are untracked and not in the release ZIP.
