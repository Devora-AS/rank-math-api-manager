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

$wp_tests_functions = $wp_tests_dir . '/includes/functions.php';
if ( ! is_readable( $wp_tests_functions ) ) {
	// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- CLI path message.
	echo "WordPress test functions not found at {$wp_tests_functions}\n";
	exit( 1 );
}

require_once $wp_tests_functions;

$polyfills_path = dirname( __DIR__ ) . '/vendor/yoast/phpunit-polyfills';
if ( is_dir( $polyfills_path ) && ! defined( 'WP_TESTS_PHPUNIT_POLYFILLS_PATH' ) ) {
	define( 'WP_TESTS_PHPUNIT_POLYFILLS_PATH', $polyfills_path );
}

/**
 * Ensure plugin files exist under WP_PLUGIN_DIR with a normal plugin basename.
 *
 * @return string Absolute path to the main plugin file inside the test sandbox.
 */
function rank_math_api_manager_tests_plugin_file() {
	$repo_root       = dirname( __DIR__ );
	$plugin_slug_dir = WP_PLUGIN_DIR . '/rank-math-api-manager';

	if ( ! is_dir( $plugin_slug_dir ) ) {
		wp_mkdir_p( $plugin_slug_dir );
	}

	$items = array(
		'rank-math-api-manager.php' => 'file',
		'assets'                    => 'dir',
	);

	foreach ( $items as $item => $type ) {
		$target = $plugin_slug_dir . '/' . $item;
		$source = $repo_root . '/' . $item;

		if ( file_exists( $target ) || ! file_exists( $source ) ) {
			continue;
		}

		if ( 'dir' === $type && is_dir( $source ) ) {
			symlink( $source, $target );
			continue;
		}

		if ( 'file' === $type && is_file( $source ) ) {
			symlink( $source, $target );
		}
	}

	return $plugin_slug_dir . '/rank-math-api-manager.php';
}

/**
 * Mark Rank Math SEO as active for dependency checks.
 *
 * @param array|false $plugins Active plugins option value.
 * @return array
 */
function rank_math_api_manager_tests_active_plugins( $plugins ) {
	if ( ! is_array( $plugins ) ) {
		$plugins = array();
	}

	$required = array(
		'seo-by-rank-math/rank-math.php',
		'rank-math-api-manager/rank-math-api-manager.php',
	);

	foreach ( $required as $plugin ) {
		if ( ! in_array( $plugin, $plugins, true ) ) {
			$plugins[] = $plugin;
		}
	}

	return $plugins;
}

/**
 * Load plugin after WordPress core bootstrap (plugins_loaded has not run yet here).
 */
function rank_math_api_manager_tests_load_plugin() {
	if ( ! class_exists( 'RankMath', false ) ) {
		/**
		 * Minimal Rank Math stub for dependency checks in integration tests.
		 *
		 * @phpcs:disable Generic.Classes.DuplicateClassName.Found
		 */
		class RankMath {
		}
	}

	if ( ! function_exists( 'rank_math' ) ) {
		/**
		 * Minimal rank_math() stub for dependency checks in integration tests.
		 *
		 * @return RankMath
		 */
		function rank_math() { // phpcs:ignore WordPress.NamingConventions.PrefixAllGlobals.NonPrefixedFunctionFound -- stub mimics Rank Math API.
			return new RankMath();
		}
	}

	if ( ! class_exists( 'WooCommerce', false ) ) {
		/**
		 * Minimal WooCommerce class stub for product post-type coverage in integration tests.
		 *
		 * @phpcs:disable Generic.Classes.DuplicateClassName.Found
		 */
		class WooCommerce {
		}
	}

	if ( ! function_exists( 'wc_get_product' ) ) {
		/**
		 * Minimal wc_get_product() stub for product REST tests without full WooCommerce.
		 *
		 * @param int $product_id Product post ID.
		 * @return object|false
		 */
		function wc_get_product( $product_id ) { // phpcs:ignore WordPress.NamingConventions.PrefixAllGlobals.NonPrefixedFunctionFound -- stub mimics WooCommerce API.
			$post = get_post( $product_id );
			if ( ! $post || 'product' !== $post->post_type ) {
				return false;
			}

			return (object) array(
				'id' => (int) $product_id,
			);
		}
	}

	add_filter( 'option_active_plugins', 'rank_math_api_manager_tests_active_plugins' );

	$plugin_file = rank_math_api_manager_tests_plugin_file();
	if ( ! is_readable( $plugin_file ) ) {
		// phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- CLI path message.
		echo "Plugin file not found: {$plugin_file}\n";
		exit( 1 );
	}

	require_once $plugin_file;

	if ( function_exists( 'rank_math_api_manager_init' ) ) {
		rank_math_api_manager_init();
	}
}

tests_add_filter( 'muplugins_loaded', 'rank_math_api_manager_tests_load_plugin' );

require_once $wp_tests_dir . '/includes/bootstrap.php';
