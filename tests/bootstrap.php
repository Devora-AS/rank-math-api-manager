<?php
/**
 * PHPUnit bootstrap for Rank Math API Manager integration tests.
 *
 * Loads the WordPress test suite and then the plugin so integration tests
 * run against a full WordPress environment.
 *
 * Requires WP_TESTS_DIR to be set (e.g. from make install-wp-tests or
 * bin/install-wp-tests.sh). See docs/verification-matrix.md or README.
 *
 * @package Rank_Math_API_Manager
 */

// Composer autoload when present.
$autoload = dirname( __DIR__ ) . '/vendor/autoload.php';
if ( is_readable( $autoload ) ) {
	require_once $autoload;
}

$wp_tests_dir = getenv( 'WP_TESTS_DIR' );
if ( ! $wp_tests_dir ) {
	// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- CLI message.
	echo "WP_TESTS_DIR must be set. See README or docs/verification-matrix.md.\n";
	exit( 1 );
}

if ( ! is_dir( $wp_tests_dir ) || ! is_readable( $wp_tests_dir . '/includes/bootstrap.php' ) ) {
	// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- CLI path message.
	echo "WordPress test bootstrap not found at {$wp_tests_dir}/includes/bootstrap.php\n";
	exit( 1 );
}

require_once $wp_tests_dir . '/includes/bootstrap.php';

// Load the plugin so REST routes and hooks are registered.
$plugin_file = dirname( __DIR__ ) . '/rank-math-api-manager.php';
if ( ! is_readable( $plugin_file ) ) {
	// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- CLI path message.
	echo "Plugin file not found: {$plugin_file}\n";
	exit( 1 );
}
require_once $plugin_file;
