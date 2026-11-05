# Current plan — Fix #5 textdomain on `init`

**Status:** Active orchestration slice  
**Tier:** standard (execution projection)  
**Contract:** v0.1 — [`.mat/docs/plan-contract.md`](../.mat/docs/plan-contract.md)  
**Preflight:** `builder_plus_verifier`  
**Last updated:** 2026-11-04  
**Branch:** `fix/issue-5-textdomain-init`  
**Issue:** https://github.com/Devora-AS/rank-math-api-manager/issues/5  

---

## Task

Eliminate the WordPress 6.7+ `_load_textdomain_just_in_time` notice for domain `rank-math-api-manager` by (1) stopping early translated `get_plugin_data()` during `plugins_loaded` construction and (2) loading the plugin textdomain on `init` (priority 0), with a regression PHPUnit test and path-scoped docs touch only as needed for this slice.

## Root cause (verified)

Constructor runs on `plugins_loaded` via `rank_math_api_manager_init` and calls:

```php
get_plugin_data( RANK_MATH_API_PLUGIN_FILE ); // defaults: $markup=true, $translate=true
```

With `$translate = true`, core `_get_plugin_data_markup_translate()` loads/translates the plugin Text Domain **before** `init`, which WP 6.7+ flags as incorrect usage. There is currently **no** `load_plugin_textdomain` on `init`.

## Non-goals

- v1.0.9.2 TASK-001+ packaging / QA workflow land (separate mission)
- Rank Math core / other plugins’ similar notices
- Broad i18n catalog (`.po`/`.mo`) authoring
- MAT sidecar / `.cursor/` / `.mat/` dirty-tree cleanup or commits
- Changing submitted/blocked statuses on unrelated issues

## Context

| Anchor | Role |
|--------|------|
| GitHub Issue #5 | Approved scope |
| `rank-math-api-manager.php` | Bootstrap + i18n load |
| `tests/integration/` | Regression coverage |
| `docs/current-plan.md` | This execution projection |

## Implementation steps

- [x] **Step 1 — RED: failing regression test**
  - Add `tests/integration/TextdomainLoadingTest.php`
  - Assert `init` (priority 0) has a callback that loads domain `rank-math-api-manager`
  - Assert no `_load_textdomain_just_in_time` `doing_it_wrong_run` for this domain when re-reading plugin headers the way bootstrap does (or equivalent observable: early `get_plugin_data` must not translate)
  - Run targeted PHPUnit and confirm RED before production edits

- [x] **Step 2 — GREEN: bootstrap fix**
  - In `init_plugin_data()`: `get_plugin_data( RANK_MATH_API_PLUGIN_FILE, false, false )` (no markup, no translate)
  - Register `add_action( 'init', [ $this, 'load_textdomain' ], 0 );` in `init_hooks()`
  - Implement `load_textdomain()` calling `load_plugin_textdomain( 'rank-math-api-manager', false, dirname( plugin_basename( RANK_MATH_API_PLUGIN_FILE ) ) . '/languages' );`
  - Optional header only if needed: `Domain Path: /languages` (create empty `languages/` only if load path requires it — prefer not adding empty dirs unless justified)

- [x] **Step 3 — GREEN verify + lint honesty**
  - Re-run targeted + full integration PHPUnit via `./scripts/run-phpunit-local.sh` (or scoped `vendor/bin/phpunit --filter TextdomainLoading`)
  - PHP lint on touched PHP files (`php -l`)
  - Keep markers updated on this plan

- [x] **Step 4 — Handoff**
  - Write `build-result.md` per `.mat/docs/workflow-artifact-contract.md`

## Binary acceptance criteria (verifier)

- [x] **AC-1:** `get_plugin_data()` in `init_plugin_data()` uses `$markup = false` and `$translate = false`
- [x] **AC-2:** Textdomain is loaded via `load_plugin_textdomain( 'rank-math-api-manager', … )` hooked to `init` at priority `0`
- [x] **AC-3:** Integration test `TextdomainLoadingTest` exists and PASSes under the repo PHPUnit path
- [x] **AC-4:** No new translation/`__()` calls introduced on `plugins_loaded` / constructor path for this domain
- [x] **AC-5:** Diff scoped to issue #5 (plugin bootstrap + test + minimal docs if required); no unrelated MAT/`.cursor` commits in the slice commit

## Verification plan

### Per-phase validation loops (loop until pass)

| Phase | Command | Loop until pass |
|-------|---------|-----------------|
| RED/GREEN targeted | `./scripts/run-phpunit-local.sh -- --filter TextdomainLoading` (or `vendor/bin/phpunit --configuration phpunit.xml.dist --filter TextdomainLoading` when `WP_TESTS_DIR` set) | Fix until green after RED observed |
| Full integration suite | `./scripts/run-phpunit-local.sh` | All integration tests green |
| PHP syntax | `php -l rank-math-api-manager.php` and `php -l tests/integration/TextdomainLoadingTest.php` | Exit 0 |
| Local GHA approx (optional pre-push) | `gh act -j phpunit --container-architecture linux/amd64` if job id exists in `.github/workflows/qa.yml`; else skip with note | Job green or documented skip |

### Global validation commands (before handoff)

1. `php -l rank-math-api-manager.php && php -l tests/integration/TextdomainLoadingTest.php`
2. `./scripts/run-phpunit-local.sh`
3. Confirm `build-result.md` matches workflow artifact contract (`Status`, `Acceptance Criteria`, `Linting / Type-Check`)

## Expected output artifacts

- `build-result.md` — builder handoff
- `verify-result.md` — parent-serialized from verifier payload
- Git commit on `fix/issue-5-textdomain-init` (slice-related paths only)
- PR → `main`, CI green via `/loop-on-ci`, merge when green
- Local deploy via `./deploy.sh` (no backup flag) after merge/validation

## Closeout checklist (parent, after verify PASS)

- [x] Low-risk `/update-docs` for slice-related README/CHANGELOG note only
- [x] Commit (no force-push)
- [x] Push + PR + `gh pr checks` / loop-on-ci until green
- [x] Merge to `main` when green
- [x] `./deploy.sh` (no backup) to Local `devora-ny` (DEST_DIR corrected locally to Bedrock `web/app/plugins`; `deploy.sh` is gitignored)

## Amendments

- 2026-11-04T14:20:00Z — orchestrator — Initial execution plan for Issue #5; root cause = early `get_plugin_data(..., translate=true)` on `plugins_loaded`; preflight `builder_plus_verifier`.
- 2026-11-04T14:25:00Z — orchestrator — Builder PASS + verifier PASS; parent PHPUnit green; CHANGELOG Unreleased note; serializing verify-result.md and committing slice paths only.
- 2026-11-04T14:30:00Z — orchestrator — PR #7 squash-merged to main after CI green; Issue #5 closed; Local deploy succeeded after Bedrock DEST_DIR fix (gitignored deploy.sh).
