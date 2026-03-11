# Rank Math API Manager Plugin - TODO / Roadmap

## Current Status

Version `1.0.9` is release-ready after verified compatibility work for WordPress `6.9.3` and Rank Math SEO `1.0.265`.

Recently completed:

- Verified local runtime compatibility with the latest supported WordPress and Rank Math releases.
- Hardened REST authorization and sanitization handling.
- Improved updater validation and PHP 8.x safety checks.
- Updated user-facing and technical documentation for the `1.0.9` release.

## High Priority Roadmap

### 1. Add support for pages

- Add support for the `page` post type in the custom REST endpoint.
- Register Rank Math meta fields for pages in native REST responses.
- Verify permission checks, sanitization, and idempotent updates for pages.
- Update API documentation and examples to cover posts, pages, and products where relevant.

### 2. Add CI/CD pipeline and GitHub Actions workflows

- Add a CI workflow for pull requests and pushes to protected branches.
- Add a release workflow for packaging, validation, and tagged releases.
- Add [Plugin Check Action](https://github.com/WordPress/plugin-check-action) to run Plugin Check against the plugin.
- Add PHP CodeSniffer (PHPCS).
- Add WPCS (WordPress Coding Standards).
- Add unit tests with PHPUnit.
- Add [WordPress Plugin Integration Test](https://github.com/marketplace/actions/wordpress-plugin-integration-test).
- Add checks for plugin/package syntax, malware or virus scanning, and known vulnerability auditing.

### 3. Strengthen automated quality gates

- Add minimum PHP and WordPress version coverage to CI.
- Add smoke tests for REST updates against posts, pages, and WooCommerce products.
- Fail builds on coding standards violations, fatal errors, and packaging problems.
- Archive build artifacts for release verification.

## Medium Priority Roadmap

### 4. Improve observability and operations

- Add structured debug logging controls for troubleshooting.
- Add clearer admin diagnostics for dependency and updater failures.
- Document a repeatable local and staging verification flow.

### 5. Expand API capabilities

- Evaluate optional endpoint-level rate limiting.
- Consider API key or token-based authentication for headless integrations.
- Consider audit logging for SEO metadata changes.

### 6. Broaden compatibility coverage

- Test against additional PHP versions supported by the plugin.
- Test against more WordPress minor releases and common hosting environments.
- Validate behavior with more Rank Math and WooCommerce combinations.

## Lower Priority Ideas

### 7. Admin UX improvements

- Add a dedicated admin settings page for plugin diagnostics and configuration.
- Add a release/debug status panel for updater and dependency health.

### 8. Internationalization

- Expand and maintain Norwegian and English documentation in parallel.
- Add translation-ready strings review for all user-facing messages.

## Documentation Follow-ups

- Keep `README.md`, `README-NORWEGIAN.md`, `readme.txt`, and `docs/` aligned for each release.
- Update roadmap items whenever a feature is completed or deferred.
- Add CI/CD documentation once workflows are introduced.

## Resources

- [WordPress Auto-Update Documentation](https://developer.wordpress.org/plugins/wordpress-org/plugin-developer-faq/#how-does-the-wordpress-org-plugin-update-system-work)
- [WordPress Plugin Update API](https://developer.wordpress.org/rest-api/reference/plugins/)
- [WordPress Coding Standards](https://developer.wordpress.org/coding-standards/)
- [Plugin Check Action](https://github.com/WordPress/plugin-check-action)
- [WordPress Plugin Integration Test](https://github.com/marketplace/actions/wordpress-plugin-integration-test)

---

**Last Updated**: March 2026  
**Status**: Active maintenance / release readiness
