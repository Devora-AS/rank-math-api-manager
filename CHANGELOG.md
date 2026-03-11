# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.9] - 2026-03-11

### Changed

- Verified compatibility with WordPress 6.9.3 during local runtime testing.
- Verified compatibility with Rank Math SEO 1.0.265 during local runtime testing.
- Updated plugin metadata and documentation to reflect current compatibility coverage.

### Security

- Split REST route authorization from REST-exposed meta authorization callbacks.
- Added field-level sanitization for both the custom endpoint and native REST meta updates.
- Hardened GitHub updater input validation and PHP 8.x safety checks.
- Removed stored GitHub token during uninstall.

### Fixed

- Returned `unchanged` instead of `failed` for idempotent metadata updates.
- Corrected documentation for authentication, permissions, error responses, and installation flow.

## [1.0.8] - 2025-07-31

### Added

- ✅ **Complete WordPress Auto-Update System**: Production-ready auto-update implementation
  - WordPress native update integration using `pre_set_site_transient_update_plugins` filter
  - GitHub API integration for checking latest releases with proper caching
  - Custom ZIP asset support with correct folder structure handling
  - "View Details" modal support via `plugins_api` filter
  - Auto-update toggle functionality for users
  - Enhanced debug logging and error handling
- **GitHub Rate Limiting**: 5-minute intervals between API calls to prevent abuse
- **Transient Caching**: 1-hour GitHub API response caching for improved performance
- **Update URI Header**: Prevents conflicts with WordPress.org update system

### Changed

- Enhanced class structure with proper singleton pattern implementation
- Improved error handling with comprehensive debug logging
- Updated plugin version to 1.0.8
- Optimized GitHub API communication with fallback mechanisms

### Security

- Enhanced input validation and sanitization for all API endpoints
- Proper object-level capability checks (`edit_post`) for all update operations
- Secure GitHub API communication with proper error handling
- Rate limiting to prevent API abuse

### Fixed

- Proper ZIP file structure handling for WordPress plugin updates
- Version comparison logic for accurate update detection
- Plugin folder naming consistency during updates

## [1.0.7] - 2025-07-29

### Added

- Enhanced plugin dependency checking
- Comprehensive documentation in /docs folder
- WordPress Plugin Check (PCP) compatibility improvements

### Removed

- **Auto-Update System**: Removed previous auto-update implementation to prepare for fresh implementation
  - Removed GitHub API integration
  - Removed update manager class
  - Removed auto-update related hooks and filters
  - Cleaned up update-related options and transients

### Changed

- Improved code structure with singleton pattern
- Enhanced security measures with proper nonce verification
- Better error handling and logging throughout the plugin
- Updated plugin version to 1.0.7

### Security

- Implemented proper input validation and sanitization
- Added capability checks for all admin functions
- Secure API communication with GitHub
- Rate limiting for update checks

## [Unreleased]

### Changed

- Improved error handling and validation
- Enhanced security measures
- Better integration with n8n workflows

### Fixed

- Various bug fixes and performance improvements

## [1.0.6] -

### Removed

- Schema markup-related code (moved to roadmap for future development)

### Changed

- Improved code quality and WordPress standards compliance
- Updated plugin description

## [1.0.5] -

### Added

- Support for WooCommerce products
- Enhanced error handling

### Changed

- Improved validation mechanisms

## [1.0.0] -

### Added

- Initial release
- Basic SEO field support (SEO Title, SEO Description, Canonical URL, Focus Keyword)
- REST API endpoints for metadata updates
- Integration with n8n workflows
- Support for WordPress posts and WooCommerce products
- Authentication and permission validation
- Input sanitization and validation
