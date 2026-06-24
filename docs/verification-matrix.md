# Verification Matrix

## Release Artifact Verification

| Scenario | Expected Result |
| --- | --- |
| Download latest release asset | Asset name is exactly `rank-math-api-manager.zip` |
| Inspect ZIP root | Top-level folder is exactly `rank-math-api-manager/` |
| Inspect main plugin file path | `rank-math-api-manager/rank-math-api-manager.php` exists |
| Open plugin header | Version matches the release tag |

## Update Verification

| Scenario | Expected Result |
| --- | --- |
| Site running `1.0.8` clears update caches and checks again | WordPress shows update to `1.0.9.2` |
| Site running `1.0.9` checks for updates | WordPress shows update to `1.0.9.2` |
| Site running `1.0.9.1` checks for updates | WordPress shows update to `1.0.9.2` |
| Site running legacy folder name `Rank Math API Manager-plugin-kopi` checks for updates | Update detection still works |
| User opens “View details” modal | Plugin information loads without fatal errors |

## Admin Notice Verification

| Scenario | Expected Result |
| --- | --- |
| Rank Math dependency missing | Dependency notice renders |
| Dependency restored | Success notice renders once |
| Dependency deactivated | Warning notice renders once |
| Legacy folder name detected | Folder-normalization warning renders |
| Administrator dismisses folder notice | Notice stays dismissed for that user |
| Non-admin user visits dashboard/plugins | No plugin notice actions are available |

## Telemetry Verification

| Scenario | Expected Result |
| --- | --- |
| Plugin activates | Anonymous site ID exists and activation event is attempted |
| Telemetry remains enabled | Privacy notice appears until the operator acts |
| Operator disables telemetry | `rank_math_api_telemetry_settings.enabled` becomes false |
| Heartbeat cron fires twice quickly | Rate limit prevents duplicate heartbeat sends |
| Plugin deactivates | Deactivation event is attempted and heartbeat hook is cleared |
| Plugin uninstalls | Telemetry settings, heartbeat state, and dismissals are removed |

## Local verification (PHPCS, PHPUnit, WordPress test env)

### Composer and tools

From the plugin root:

```bash
composer install
vendor/bin/phpcs
vendor/bin/phpunit
```

- **PHPCS**: Lints plugin PHP against WordPress Coding Standards (PHP 7.4+, WordPress plugin). Configuration: `phpcs.xml.dist`.
- **PHPUnit**: Runs integration tests under `tests/integration/`. Requires a WordPress test environment (see below).

### WordPress test environment (for PHPUnit)

Integration tests need a running WordPress test suite so that `tests/bootstrap.php` can load WordPress and the plugin.

1. **Option A – Install WordPress test library (recommended)**  
   From the [WordPress develop repository](https://develop.svn.wordpress.org/) or the [make install-wp-tests script](https://make.wordpress.org/cli/handbook/misc/plugin-unit-tests/), set up a test database and the test suite. Then:

   ```bash
   export WP_TESTS_DIR=/path/to/wordpress-tests-lib   # or your test suite path
   vendor/bin/phpunit
   ```

   If `WP_TESTS_DIR` is not set, the bootstrap exits with instructions.

2. **Option B – Docker**  
   If contributors cannot run Composer or a local WordPress install, use a Docker setup that mounts the plugin and runs `composer install`, sets `WP_TESTS_DIR` to the container’s test suite path, and runs `vendor/bin/phpunit` inside the container.

3. **Option C – LocalWP (e.g. devora-ny.local)** Use LocalWP DB credentials and install the test suite with `install-wp-tests.sh` (or `bin/install-wp-tests.sh` after `wp scaffold plugin-tests rank-math-api-manager`). Then `export WP_TESTS_DIR=/tmp/wordpress-tests-lib` and run `vendor/bin/phpunit --configuration phpunit.xml.dist`.

4. **Option D – WordPress Playground** Use [WordPress Playground](https://wordpress.github.io/wordpress-playground/) (browser) or [Playground CLI](https://wordpress.github.io/wordpress-playground/developers/local-development/wp-playground-cli/) to run tests without a local server; document steps in PRs as needed.

### What the tests assert

- **Page support**: Updating and reading Rank Math fields (`rank_math_title`, `rank_math_description`, `rank_math_canonical_url`, `rank_math_focus_keyword`) for post type `page`; success and correct meta values.
- **Unsupported object type**: Updating meta for a custom post type not in the allowed list returns 400 and error code `invalid_post_id`.
- **Post**: Updating Rank Math meta for a `post` succeeds and meta is stored.
- **Product** (when WooCommerce is active): Updating Rank Math meta for a `product` succeeds; test is skipped if WooCommerce is not active.
- **Updater icons**: The object returned by the plugin’s update flow (`pre_set_site_transient_update_plugins`) and by `plugin_info` (`plugins_api`) includes an `icons` array whose values are valid URLs containing the plugin URL constant and asset path.

## Manual checks (v1.0.9.2)

| Scenario | Expected Result |
| --- | --- |
| Icon visibility in plugin/update UI | Plugin icon and update modal show expected assets (e.g. from `assets/` or `assets/images/` if present). |
| Page update via API | REST update succeeds; e.g. `curl -X POST .../wp-json/rank-math-api/v1/update-meta` or WP-CLI with valid auth updates post meta. |
| Release asset contents and folder structure | Downloaded `rank-math-api-manager.zip` contains top-level `rank-math-api-manager/`, main file `rank-math-api-manager/rank-math-api-manager.php`, and `rank-math-api-manager/assets/` (and `assets/images/` when used). No `.cursor/`, `agent-skills/`, or other dev-only paths in ZIP. |

Example API check (WP-CLI or curl):

```bash
# WP-CLI (with application password or logged-in user)
wp rest post /rank-math-api/v1/update-meta post_id=1 title="Test" description="Test" --user=admin

# curl (replace SITE, USER, APP_PASSWORD)
curl -X POST "https://SITE/wp-json/rank-math-api/v1/update-meta" \
  -u "USER:APP_PASSWORD" -H "Content-Type: application/json" \
  -d '{"post_id":1,"title":"Test","description":"Test"}'
```

## Automated CI checks (QA workflow)

The `.github/workflows/qa.yml` workflow runs on pull requests to `main`/`master`, push to `main`/`master`, and `workflow_dispatch`. Each job must pass for a green run.

| Job | What runs | Pass means |
| --- | --- | --- |
| **PHP Lint** | `php -l` on all PHP files (excl. `.git`, `vendor`) | No syntax errors; at least one PHP file found. |
| **PHPCS (WPCS)** | `vendor/bin/phpcs --standard=phpcs.xml.dist` after `composer install` | No WordPress coding standards violations. |
| **Plugin Check** | WordPress Plugin Check in wp-env (exclude `plugin_updater`; ignore `invalid_tested_upto_minor`) | No errors from Plugin Check; GitHub-only updater exclusions applied. |
| **Package smoke test** | `scripts/package-plugin.sh` then ZIP verification | ZIP contains `rank-math-api-manager/`, main file, `assets/`, `assets/images/` with `icon-128x128.png`, `icon-256x256.png`, `icon.svg`; no forbidden dev artifacts. |
| **PHPUnit** | MySQL service + `install-wp-tests.sh`, then `vendor/bin/phpunit` with `WP_TESTS_DIR` | WordPress integration tests run; all tests pass; exit code 0. |

Plugin Check ignore/exclude notes: `plugin_updater` is excluded because the plugin uses a GitHub-only update mechanism; `invalid_tested_upto_minor` can be ignored for “Tested up to” minor-version warnings. See `docs/release-process.md` for local Plugin Check commands.

## Suggested Local Checks

```bash
wp option get rank_math_api_telemetry_settings
wp option get rank_math_api_dismissed_notices
wp option get rank_math_api_notice_events
wp cron event list | grep rank_math_api
wp option delete _site_transient_update_plugins
wp transient delete rank_math_api_github_release
wp option delete rank_math_api_last_github_check
```

## Acceptance Criteria

- Release ZIP layout is correct
- WordPress update notices appear for supported upgrade paths
- Legacy-folder installs receive guidance without blocking updates
- Telemetry is documented, minimal, and can be disabled
- No syntax or lint errors are introduced by the release

---

**Last Updated**: March 2026  
**Version**: 1.0.9.2
