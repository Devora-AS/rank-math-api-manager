# PR Checklist – v1.0.9.2

Use this checklist when opening or reviewing the v1.0.9.2 PR against `main`.

## Acceptance criteria mapping

| Criterion | Location / How to verify |
|-----------|--------------------------|
| **Icons** Repository contains icon files at `assets/images/` | `assets/images/icon-128x128.png`, `icon-256x256.png` |
| **Icons** Updater response includes `icons` with installed-plugin URLs | `rank-math-api-manager.php`: `check_for_update()` and `plugin_info()` return `icons` array with `RANK_MATH_API_PLUGIN_URL . 'assets/images/...'` |
| **Icons** Packaging verifies ZIP contains assets | `.github/workflows/release.yml` and `qa.yml`: Verify step checks `rank-math-api-manager/assets/images/` |
| **Page support** `get_allowed_post_types()` includes `'page'` | `rank-math-api-manager.php` ~line 195 |
| **Page support** Docs state pages supported | README.md, readme.txt, docs/api-documentation.md, docs/troubleshooting.md, docs/verification-matrix.md, CHANGELOG.md |
| **Page support** Page-based API example | docs/api-documentation.md: "Page-based example" curl |
| **Page support** Integration tests for page + no regression for post/product | tests/integration/UpdateMetaPageTest.php, UpdateMetaPostTest.php, UpdateMetaProductTest.php |
| **CI** QA workflow runs on PR/push/main + dispatch | `.github/workflows/qa.yml` |
| **CI** PHP lint, PHPCS, Plugin Check, package smoke, PHPUnit jobs | qa.yml jobs: php-lint, phpcs, plugin-check, package-smoke, phpunit |
| **CI** Packaging script used by release and CI | `scripts/package-plugin.sh`; release.yml and qa package-smoke call it |
| **CI** PHPUnit integration tests run in CI | qa.yml phpunit job: MySQL + install-wp-tests.sh, then vendor/bin/phpunit with WP_TESTS_DIR; see docs/verification-matrix.md. Local: LocalWP or Playground options there. |

## Local verification commands

```bash
# Composer and PHPCS
composer install
vendor/bin/phpcs

# Packaging
bash scripts/package-plugin.sh
unzip -l rank-math-api-manager.zip | grep -E 'assets/images|rank-math-api-manager\.php'

# PHPUnit (requires WP test env)
export WP_TESTS_DIR=/path/to/wordpress-tests-lib
vendor/bin/phpunit
```

## Docker alternative (if no local Composer/WP)

See `docs/verification-matrix.md` and `docs/qa-workflow-report-v1.0.9.2.md` for Docker one-liners and CI job references.

## Files changed (summary)

- **Plugin**: `rank-math-api-manager.php` (version 1.0.9.2, icons in updater, page in allowed types, description/error strings)
- **Assets**: `assets/images/icon-128x128.png`, `icon-256x256.png`
- **Docs**: `README.md`, `readme.txt`, `CHANGELOG.md`, `docs/api-documentation.md`, `docs/troubleshooting.md`, `docs/verification-matrix.md`, `docs/art-brief-icons.md`
- **CI**: `.github/workflows/release.yml` (use package script), `.github/workflows/qa.yml` (new)
- **Packaging**: `scripts/package-plugin.sh`
- **QA**: `composer.json`, `composer.lock`, `phpcs.xml.dist`, `phpunit.xml.dist`, `tests/bootstrap.php`, `tests/integration/*.php`
- **Config**: `.gitignore` (vendor/, rank-math-api-manager/), `.deployignore` (source of truth note)

## Remaining TODOs (optional)

- Final approved icon design pass (SVG optional); current PNGs are placeholders per art brief.
- ~~Full WordPress test env in CI~~ Done: qa.yml runs MySQL + install-wp-tests.sh and PHPUnit. Local: use WP_TESTS_DIR; see verification-matrix (LocalWP, Playground).
- PHPCS: re-include `rank-math-api-manager.php` and fix WPCS violations in a follow-up.
