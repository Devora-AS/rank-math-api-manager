# Product Requirements — v1.0.9.2 Release Hardening

**Package:** `specs/v1-0-9-2/`  
**Branch:** `feature/v1.0.9.2`  
**Status:** Planning approved (Phase B complete); Phase C not started  
**Traceability:** Each `TASK-###` in `tasks.json` maps to `spec_ids` and `prd_ids` (FR/AC) below.

---

## Problem & audience

**Problem:** v1.0.9.2 release hardening work exists as uncommitted WIP on `feature/v1.0.9.2` — CI/QA toolchain, packaging, icons, page support, integration tests, and doc updates — but lacks an approved, traceable execution package before landing to the branch and opening a PR.

**Audience:** Devora operators and maintainers shipping Rank Math API Manager to production WordPress sites via GitHub releases and native auto-update.

**Why now:** MAT adoption merged to `main` (PR #3); plugin header already at `1.0.9.2`; WIP is functionally complete but needs structured Phase C slices, verification gates, and operator handoff.

---

## Goals & success metrics

| Metric | Target |
|--------|--------|
| CI green on PR | `qa.yml` jobs pass: php-lint, phpcs, plugin-check, package-smoke, phpunit |
| Release asset integrity | `release.yml` builds ZIP via `scripts/package-plugin.sh`; assets/images present |
| API coverage | `/update-meta` accepts post, page, and product IDs |
| Updater UX | `check_for_update()` / `plugin_info()` return `icons` with plugin URLs |
| Test confidence | Five integration tests run in CI with WordPress test suite |
| Docs accuracy | Version `1.0.9.2` consistent across plugin, CHANGELOG, README, readme.txt, docs |

---

## Scope (in)

1. **CI/QA pipeline** — Land `qa.yml` with php-lint, PHPCS, Plugin Check, package smoke, PHPUnit (MySQL + `install-wp-tests.sh`).
2. **Release workflow** — Align `release.yml` with shared packaging script and ZIP verification (icons, forbidden artifacts).
3. **Version & documentation sync** — `1.0.9.2` everywhere including `docs/README.md` (currently `1.0.9.1`).
4. **Page post-type support** — Already in WIP; verify and document.
5. **Updater icons** — PNG/SVG assets + updater response; packaging includes `assets/images/`.
6. **Composer dev toolchain** — `composer.json`, PHPCS/PHPUnit configs, integration tests.
7. **PR checklist** — Use `docs/PR-CHECKLIST-v1.0.9.2.md` at merge time.

---

## Non-goals (out of scope)

- MAT adoption files, `.mat/` bootstrap duplicates, or `update-mat.py --apply`
- `.cursor/` git tracking policy changes (Option A: gitignored stays)
- RFU-7 observability stack
- Final approved icon design pass (placeholders acceptable for v1.0.9.2)
- Re-including `rank-math-api-manager.php` in PHPCS and fixing all WPCS violations (deferred follow-up)
- Committing, pushing, merging to `main`, or creating GitHub release (operator-owned after Phase C)

---

## Assumptions

1. WIP on `feature/v1.0.9.2` is the authoritative implementation source; Phase C lands untracked files rather than re-implementing.
2. `qa.yml` (untracked) is authoritative for CI PHPUnit behavior — supersedes stale claims in `docs/v1.0.9.2-plan-status.md`.
3. Rank Math SEO remains a runtime dependency; integration tests mock or stub Rank Math meta where needed.
4. PHP 8.1 in CI; plugin supports PHP 7.4+ per header.
5. Human operator approves planning package before any Phase C slice runs.

---

## Functional requirements

| ID | Requirement |
|----|-------------|
| **FR-001** | Plugin version `1.0.9.2` in header and `RANK_MATH_API_VERSION` constant. |
| **FR-002** | `get_allowed_post_types()` includes `post`, `page`, and `product` (when WooCommerce active). |
| **FR-003** | REST `/update-meta` accepts page IDs with same validation as posts/products. |
| **FR-004** | `check_for_update()` and `plugin_info()` return `icons` array pointing to `assets/images/icon-128x128.png` and `icon-256x256.png`. |
| **FR-005** | `assets/images/` contains required icon files (128, 256 PNG; SVG for smoke test). |
| **FR-006** | `scripts/package-plugin.sh` produces production ZIP with correct folder structure and icon assets. |
| **FR-007** | `qa.yml` runs on PR/push to main/master and workflow_dispatch. |
| **FR-008** | `qa.yml` phpunit job installs WordPress test suite via `install-wp-tests.sh` and runs integration tests. |
| **FR-009** | `release.yml` uses `package-plugin.sh` and verifies ZIP structure including `assets/images/`. |
| **FR-010** | PHPCS runs via `phpcs.xml.dist` in CI (main plugin file excluded until follow-up). |
| **FR-011** | Integration tests cover page, post, product, unsupported type, and updater icons. |
| **FR-012** | Documentation reflects page support, icons, CI commands, and version `1.0.9.2`. |

---

## Acceptance criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| **AC-001** | All version strings show `1.0.9.2` (including `docs/README.md`) | Grep / manual review |
| **AC-002** | Page ID succeeds on `/update-meta`; unsupported type returns error | `UpdateMetaPageTest`, `UpdateMetaUnsupportedTypeTest` |
| **AC-003** | Post and product regression tests pass | `UpdateMetaPostTest`, `UpdateMetaProductTest` |
| **AC-004** | Updater responses include valid icon URLs | `UpdaterIconsTest` |
| **AC-005** | Package ZIP contains `rank-math-api-manager/assets/images/icon-*.png` and `icon.svg` | package-smoke job / local `package-plugin.sh` |
| **AC-006** | ZIP excludes `.cursor/`, tests, vendor, agent artifacts | package-smoke + release verify steps |
| **AC-007** | `qa.yml` all jobs pass on PR | GitHub Actions |
| **AC-008** | PHPUnit integration suite runs in CI (not local-only) | qa.yml phpunit job logs |
| **AC-009** | `release.yml` php-lint scope consistent with qa (see SPEC-002) | Workflow diff review |
| **AC-010** | `docs/PR-CHECKLIST-v1.0.9.2.md` items mappable to shipped files | PR review |
| **AC-011** | `docs/verification-matrix.md` documents manual + automated checks | Doc review |
| **AC-012** | CHANGELOG `[1.0.9.2]` section documents page support and icons | CHANGELOG review |

---

## Open questions

| ID | Question | Status | Resolution / notes |
|----|----------|--------|-------------------|
| **OQ-001** | Final icon motif: “SEO + API bridge” vs current gear/badge placeholders? | **deferred** | Ship current Devora-palette PNGs/SVG; optional design pass post-release. |
| **OQ-002** | When to re-include `rank-math-api-manager.php` in PHPCS? | **deferred** | TASK-005 optional slice; exclude remains until WPCS fixes land. |
| **OQ-003** | `docs/README.md` still lists `1.0.9.1` — include in version sync? | **resolved** | Yes; TASK-001 updates to `1.0.9.2`. |
| **OQ-004** | Does PHPUnit run in CI? `v1.0.9.2-plan-status.md` says no. | **resolved** | `qa.yml` phpunit job uses MySQL + `install-wp-tests.sh` + `WP_TESTS_DIR`; authoritative over stale plan-status partial claim. Update plan-status in Phase C doc slice if desired. |
| **OQ-005** | Align `release.yml` `php -l` find depth (3) with `qa.yml` (5)? | **open** | TASK-003 should align scopes; tests/ at depth 4+ only in qa today. |
| **OQ-006** | Single PR vs multiple Phase C commits? | **open** | Operator choice; `tasks.json` supports slice-by-slice or batched landing. |

---

## User stories (summary)

1. **As a site admin**, I can update Rank Math SEO meta for pages via the REST API so automation covers all primary content types.
2. **As a site admin**, I see plugin icons in the WordPress Plugins screen after update checks.
3. **As a maintainer**, I get CI feedback on lint, standards, plugin check, packaging, and integration tests on every PR.
4. **As a releaser**, I trigger `release.yml` and receive a verified ZIP with icons included.

---

## Traceability note

- `spec.md` sections `SPEC-###` implement clusters of FR/AC.
- `tasks.json` entries reference `prd_ids` (e.g. `FR-001`, `AC-007`) and `spec_ids` (e.g. `SPEC-003`).
- Phase C parent orchestrator should project one `TASK-###` at a time into `docs/current-plan.md` per `plan-summary.md`.
