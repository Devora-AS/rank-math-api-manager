# Technical Specification — v1.0.9.2 Release Hardening

**Package:** `specs/v1-0-9-2/`  
**Traces to:** `prd.md` (FR-###, AC-###)  
**Implementation state:** WIP on branch (untracked + modified); Phase C lands files

---

## SPEC-001 — Version and documentation sync

**PRD:** FR-001, FR-012; AC-001, AC-011, AC-012  
**OQ-003:** resolved

### Current state

| Location | Version |
|----------|---------|
| `rank-math-api-manager.php` header + constant | `1.0.9.2` ✓ |
| `CHANGELOG.md` `[1.0.9.2]` | ✓ |
| `README.md`, `readme.txt` | `1.0.9.2` ✓ |
| `docs/README.md` | `1.0.9.1` ✗ — fix in Phase C |

### Phase C actions

- Update `docs/README.md` current version lines to `1.0.9.2`.
- Confirm `docs/verification-matrix.md`, `docs/api-documentation.md`, `docs/troubleshooting.md` reference page support and CI paths.
- No plugin PHP changes required if WIP already correct.

### Validation

```bash
grep -r "1.0.9.1" docs/README.md README.md readme.txt CHANGELOG.md rank-math-api-manager.php
# Expect no stale 1.0.9.1 in docs/README.md after TASK-001
```

---

## SPEC-002 — CI workflows (qa.yml + release.yml alignment)

**PRD:** FR-007, FR-008, FR-009; AC-007, AC-008, AC-009  
**OQ-004:** resolved (PHPUnit in CI)  
**OQ-005:** open (php-lint depth alignment)

### qa.yml (authoritative QA pipeline)

**Triggers:** `pull_request`, `push` (main/master), `workflow_dispatch`

| Job | Purpose |
|-----|---------|
| `php-lint` | `find . -maxdepth 5` + `php -l` on all `*.php` (excludes vendor) |
| `phpcs` | `composer install` → `vendor/bin/phpcs --standard=phpcs.xml.dist` |
| `plugin-check` | Staged build dir; `exclude-checks: plugin_updater`; `ignore-codes: invalid_tested_upto_minor` |
| `package-smoke` | `scripts/package-plugin.sh` + ZIP structure asserts (root folder, main file, `assets/images/`, icon files, no forbidden paths) |
| `phpunit` | MySQL 5.7 service; `install-wp-tests.sh` → `WP_TESTS_DIR=/tmp/wordpress-tests-lib`; `vendor/bin/phpunit` |

**Reconciliation:** `docs/v1.0.9.2-plan-status.md` “Partially completed / Not completed — PHPUnit in CI” is **stale**. Untracked `qa.yml` implements full WordPress test suite install. Mark resolved in operator docs during TASK-003 or doc-only follow-up.

### release.yml

- Triggers: `release: published`, `workflow_dispatch` (tag input).
- Uses `scripts/package-plugin.sh` for ZIP creation.
- PHP lint: `find . -maxdepth 3` — **narrower than qa.yml**; align to maxdepth 5 in TASK-003 so `tests/` PHP is linted consistently (OQ-005).
- ZIP verification: root folder, main plugin file, `assets/`, `assets/images/`, forbidden artifact grep (matches qa package-smoke intent).

### Edge cases

- Plugin Check build dir is minimal copy (not full package script output) — acceptable for static analysis.
- `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` on both workflows.

### Validation

- Land `qa.yml` (currently untracked) in TASK-003.
- Open PR; confirm all five jobs green.
- Optional: `workflow_dispatch` on qa.yml from feature branch before merge.

---

## SPEC-003 — Composer, PHPCS, PHPUnit toolchain

**PRD:** FR-010, FR-011; AC-007, AC-008

### composer.json

- PHP `>=7.4`; dev: `phpunit/phpunit ^9.6`, `squizlabs/php_codesniffer`, `wp-coding-standards/wpcs`, `dealerdirect/phpcodesniffer-composer-installer`.
- Scripts: `phpcs`, `phpcbf`, `phpunit`, `test` (phpcs + phpunit).

### phpcs.xml.dist

- Ruleset: WordPress (WPCS).
- **Exclude:** `rank-math-api-manager.php` (main file) until WPCS violations fixed — documented follow-up TASK-005.
- Excludes: vendor, .git, .github, .cursor, tests/dependency-check-test.php.

### phpunit.xml.dist

- Bootstrap: `tests/bootstrap.php` (requires `WP_TESTS_DIR`).
- Testsuite: `tests/integration/*Test.php`.

### Integration tests (WIP)

| File | Coverage |
|------|----------|
| `UpdateMetaPageTest.php` | Page post type via REST |
| `UpdateMetaPostTest.php` | Post regression |
| `UpdateMetaProductTest.php` | Product (WooCommerce) |
| `UpdateMetaUnsupportedTypeTest.php` | Rejects invalid types |
| `UpdaterIconsTest.php` | `icons` in update/plugin_info responses |

### Local validation

```bash
composer install
vendor/bin/phpcs
export WP_TESTS_DIR=/path/to/wordpress-tests-lib
vendor/bin/phpunit
```

### Phase C

- TASK-002: commit `composer.json`, `composer.lock`, `phpcs.xml.dist`, `phpunit.xml.dist`, `tests/`.
- `.gitignore` should include `vendor/` (modified in WIP).

---

## SPEC-004 — Packaging script and release assets

**PRD:** FR-005, FR-006; AC-005, AC-006

### scripts/package-plugin.sh

- Output: `rank-math-api-manager.zip` with root folder `rank-math-api-manager/`.
- Copies: main PHP, `includes/`, `assets/` (preserves `assets/images/`), README, LICENSE, CHANGELOG, readme.txt.
- Strips: .git, .github, tests, .cursor, agent-skills, transcripts, node_modules, .env, etc.

### Icon assets (WIP untracked)

- `assets/images/icon-128x128.png`, `icon-256x256.png`, `icon.svg`
- Optional design artifacts: `icon-direction-*.svg`, `icon-proof.html` (exclude from ZIP if not under assets/ or not copied)

### CI verification

- package-smoke asserts all three icon files in ZIP.
- release.yml verifies `assets/images/` directory present.

### Validation

```bash
bash scripts/package-plugin.sh
unzip -l rank-math-api-manager.zip | grep assets/images
```

---

## SPEC-005 — Plugin features (page support + updater icons)

**PRD:** FR-002, FR-003, FR-004; AC-002, AC-003, AC-004

**Note:** Implementation already in modified `rank-math-api-manager.php` (WIP). Phase C does not re-implement — verify only.

### Page support

- `get_allowed_post_types()` returns `['post', 'page']` + `'product'` if WooCommerce.
- REST permission and error strings reference “post, page, or product”.
- Docs: page-based curl example in `docs/api-documentation.md`.

### Updater icons

- `check_for_update()` ~line 1568: `icons` with 128/256 URLs via `RANK_MATH_API_PLUGIN_URL`.
- `plugin_info()` ~line 1741: same pattern.
- Requires `assets/images/` in deployed plugin (SPEC-004).

### Edge cases

- WooCommerce absent: product type not in allowed list; `UpdateMetaProductTest` may skip or require WC bootstrap.
- `UpdaterIconsTest` may skip if cannot simulate newer remote version.
- Idempotent meta updates return `unchanged` (existing behavior).

### Validation

- Integration tests (SPEC-003) + manual matrix in `docs/verification-matrix.md`.

---

## SPEC-006 — PHPCS main-file follow-up (deferred)

**PRD:** FR-010; OQ-002 deferred

### Current

Main plugin file excluded in `phpcs.xml.dist` so CI passes.

### Phase C (optional TASK-005)

1. Remove `<exclude-pattern>rank-math-api-manager.php</exclude-pattern>`.
2. Run `vendor/bin/phpcbf` where safe; fix remaining WPCS manually.
3. Confirm phpcs job still green.

**Status:** deferred — not blocking v1.0.9.2 release.

---

## SPEC-007 — PR checklist and operator handoff

**PRD:** AC-010, AC-011

### docs/PR-CHECKLIST-v1.0.9.2.md

Maps acceptance criteria to files and local commands. Use at PR open/review.

### docs/verification-matrix.md

Manual checks (icon visibility, page API, release ZIP) + automated CI table referencing qa.yml jobs.

### Merge prerequisites

- All TASK-001–004 done (TASK-005 optional).
- CI green on PR against `main`.
- Operator review of `plan-summary.md` approval gate passed.

---

## Cross-cutting validation approach

| Layer | Tool |
|-------|------|
| Syntax | `php -l` (qa + release) |
| Standards | PHPCS (excludes main file) |
| WP.org rules | Plugin Check action |
| Packaging | package-plugin.sh + ZIP asserts |
| Behavior | PHPUnit integration (WP test lib) |
| Planning | `bash scripts/phase1-verify.sh` |

## Dependencies

- GitHub Actions (ubuntu-latest, PHP 8.1)
- MySQL service for PHPUnit job
- wp-cli `install-wp-tests.sh` template (downloaded at CI runtime)
- Rank Math SEO for full manual E2E (tests may stub meta)

## Out of scope (technical)

- MAT hooks, MAO gate changes, `.mat/` edits
- `update-mat.py --apply`
- RFU-7 telemetry observability beyond existing plugin telemetry
