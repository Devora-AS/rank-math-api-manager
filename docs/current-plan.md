# Current plan — v1.0.9.2 verification reconcile (slice 1)

**Status:** Active orchestration slice  
**Tier:** standard (execution projection)  
**Contract:** v0.1 — [`.mat/docs/plan-contract.md`](../.mat/docs/plan-contract.md)  
**Preflight:** `builder_plus_verifier`  
**Last updated:** 2026-11-05  
**Branch:** `chore/v1.0.9.2-mat-verification-closeout`  
**Mission:** `docs/architecture/long-run-state.md` slice `v1092-verify-reconcile`

---

## Task

Re-verify the approved v1.0.9.2 plan against `main`. Product scope (icons, pages, QA workflow, packaging script, integration tests, verification matrix) is **already shipped** at tag `v1.0.9.2`. This slice lands only verified gaps:

1. PHPCS doc-comment capitalization in `tests/integration/TextdomainLoadingTest.php` (local `vendor/bin/phpcs` currently fails).
2. Align GitHub updater `tested` metadata with plugin header / `readme.txt` (`7.1`, not `6.9.3`).

## Context

| Anchor | Role |
|--------|------|
| Approved user plan | Icons, page, CI, packaging, docs |
| `main` @ `62029d8` | Contains 1.0.9.2 product code; release published |
| `scripts/run-phpunit-local.sh` | Local PHPUnit mirror of `qa.yml` |
| `.github/workflows/qa.yml` | Authoritative CI gate |

## Implementation steps

- [wip] **Step 1 — Fix PHPCS in textdomain integration test**
  - Capitalize short descriptions on affected `@` docblocks in `tests/integration/TextdomainLoadingTest.php`.

- [] **Step 2 — Align updater tested version**
  - Set `'tested' => '7.1'` in `check_for_update()` and `plugin_info()` response arrays in `rank-math-api-manager.php`.

- [] **Step 3 — Validation**
  - `vendor/bin/phpcs --standard=phpcs.xml.dist`
  - `./scripts/run-phpunit-local.sh`
  - `./scripts/package-plugin.sh` (confirm icons in ZIP)
  - `bash scripts/phase1-verify.sh`

- [] **Step 4 — Handoff**
  - `build-result.md` per workflow artifact contract.

## Acceptance criteria

- [] **AC-1:** PHPCS exits 0 on the repository standard (`phpcs.xml.dist`).
- [] **AC-2:** PHPUnit integration suite passes (WooCommerce skip allowed).
- [] **AC-3:** Updater `tested` fields match `7.1` in both update transient and plugin info paths.
- [] **AC-4:** Re-verification documents that icons, page support, QA workflow, and packaging script already satisfy the approved v1.0.9.2 plan on `main` (no duplicate feature work).

## Verification plan

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| PHPCS | `vendor/bin/phpcs --standard=phpcs.xml.dist` | Fix until exit 0 |
| PHPUnit | `./scripts/run-phpunit-local.sh` | Fix until exit 0 |
| Package | `./scripts/package-plugin.sh` && unzip -l rank-math-api-manager.zip \| grep icon | Icons present |
| Phase1 | `bash scripts/phase1-verify.sh` | Exit 0 |

### Global validation commands (before handoff)

1. `bash scripts/doctor.sh`
2. `bash scripts/phase1-verify.sh`
3. `gh act -j phpcs --container-architecture linux/amd64` (optional pre-push if Docker healthy)

## Amendments

- 2026-11-05T10:05:00Z — orchestrator — Slice scoped to verification gaps after confirming v1.0.9.2 already released on GitHub.

## Recommended Next Command

After build handoff: `/mat-review` (verifier) with `docs/current-plan.md` and `build-result.md`.
