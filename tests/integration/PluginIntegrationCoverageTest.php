<?php
/**
 * Integration tests: lifecycle, updater branches, admin notices, and settings sanitization.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class PluginIntegrationCoverageTest
 */
class PluginIntegrationCoverageTest extends WP_UnitTestCase {

	/**
	 * Plugin instance.
	 *
	 * @var Rank_Math_API_Manager_Extended
	 */
	private $plugin;

	/**
	 * Admin user ID.
	 *
	 * @var int
	 */
	private $admin_id;

	/**
	 * Set up.
	 */
	public function set_up() {
		parent::set_up();
		$this->plugin   = Rank_Math_API_Manager_Extended::get_instance();
		$this->admin_id = $this->factory->user->create( array( 'role' => 'administrator' ) );
	}

	/**
	 * Activation and deactivation hooks run without error.
	 */
	public function test_plugin_activate_and_deactivate_hooks() {
		rank_math_api_manager_activate();
		$this->assertNotFalse( get_option( 'rank_math_api_activated', false ) );

		rank_math_api_manager_deactivate();
		$this->assertFalse( wp_next_scheduled( 'rank_math_api_update_check' ) );
	}

	/**
	 * Telemetry settings sanitizer normalizes enabled flag.
	 */
	public function test_sanitize_telemetry_settings_normalizes_enabled_boolean() {
		$sanitized = $this->plugin->sanitize_telemetry_settings(
			array(
				'enabled' => 'yes',
			)
		);

		$this->assertIsArray( $sanitized );
		$this->assertTrue( $sanitized['enabled'] );
	}

	/**
	 * Admin scripts enqueue on plugins screen hook.
	 */
	public function test_enqueue_admin_scripts_on_plugins_screen() {
		wp_set_current_user( $this->admin_id );
		$this->plugin->enqueue_admin_scripts( 'plugins.php' );
		$this->assertTrue( wp_script_is( 'rank-math-api-admin', 'enqueued' ) );
		$this->assertTrue( wp_style_is( 'rank-math-api-admin', 'enqueued' ) );
	}

	/**
	 * plugins_api filter returns plugin info with icons when release cached.
	 */
	public function test_plugins_api_returns_info_with_icons() {
		set_transient(
			'rank_math_api_github_release',
			array(
				'version'      => RANK_MATH_API_VERSION,
				'download_url' => 'https://github.com/devora-as/rank-math-api-manager/releases/download/v1.0.9.2/rank-math-api-manager.zip',
				'published_at' => gmdate( 'c' ),
				'description'  => 'Notes',
			),
			3600
		);

		$args = (object) array(
			'slug' => 'rank-math-api-manager',
		);

		$result = apply_filters( 'plugins_api', false, 'plugin_information', $args );

		$this->assertIsObject( $result );
		$this->assertObjectHasProperty( 'icons', $result );
		$this->assertNotEmpty( $result->icons );
	}

	/**
	 * Update check skips adding response when remote version matches current.
	 */
	public function test_check_for_update_skips_when_versions_match() {
		$basename = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
		set_transient(
			'rank_math_api_github_release',
			array(
				'version'      => RANK_MATH_API_VERSION,
				'download_url' => 'https://github.com/devora-as/rank-math-api-manager/releases/download/v' . RANK_MATH_API_VERSION . '/rank-math-api-manager.zip',
			),
			3600
		);

		$transient = (object) array(
			'checked'  => array(
				$basename => RANK_MATH_API_VERSION,
			),
			'response' => array(),
		);

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );

		$this->assertEmpty( $filtered->response );
	}

	/**
	 * GitHub rate limit path returns WP_Error without HTTP when checked recently.
	 */
	public function test_github_rate_limit_blocks_rapid_release_fetch() {
		update_option( 'rank_math_api_last_github_check', time(), false );
		delete_transient( 'rank_math_api_github_release' );

		$basename  = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
		$transient = (object) array(
			'checked'  => array(
				$basename => '1.0.0',
			),
			'response' => array(),
		);

		$http_called = false;
		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) use ( &$http_called ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'api.github.com' ) ) {
					$http_called = true;
				}
				return $preempt;
			},
			10,
			3
		);

		apply_filters( 'pre_set_site_transient_update_plugins', $transient );

		$this->assertFalse( $http_called, 'Rate limit should prevent GitHub HTTP fetch.' );
	}

	/**
	 * Missing dependency renders dependency admin notice markup.
	 */
	public function test_dependency_missing_renders_error_notice() {
		wp_set_current_user( $this->admin_id );
		set_current_screen( 'plugins' );

		add_filter(
			'option_active_plugins',
			function ( $plugins ) {
				if ( ! is_array( $plugins ) ) {
					return $plugins;
				}
				return array_values(
					array_diff( $plugins, array( 'seo-by-rank-math/rank-math.php' ) )
				);
			}
		);

		ob_start();
		$this->plugin->render_admin_notices();
		$output = ob_get_clean();

		$this->assertStringContainsString( 'Rank Math API Manager', $output );
	}

	/**
	 * Telemetry privacy notice markup renders when enabled and not dismissed.
	 */
	public function test_telemetry_privacy_notice_renders_when_enabled() {
		wp_set_current_user( $this->admin_id );
		set_current_screen( 'plugins' );
		update_option(
			'rank_math_api_telemetry_settings',
			array(
				'enabled' => true,
			),
			false
		);
		delete_option( 'rank_math_api_dismissed_notices' );

		ob_start();
		$this->plugin->render_admin_notices();
		$output = ob_get_clean();

		$this->assertStringContainsString( 'Telemetry', $output );
	}

	/**
	 * Scheduled telemetry heartbeat respects opt-out.
	 */
	public function test_scheduled_telemetry_respects_opt_out() {
		update_option(
			'rank_math_api_telemetry_settings',
			array(
				'enabled' => false,
			),
			false
		);

		$http_called = false;
		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) use ( &$http_called ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'updates.devora.no' ) ) {
					$http_called = true;
				}
				return $preempt;
			},
			10,
			3
		);

		$this->plugin->send_scheduled_telemetry();

		$this->assertFalse( $http_called );
	}

	/**
	 * on_plugin_activated rechecks dependencies when Rank Math is activated.
	 */
	public function test_on_plugin_activated_for_dependency_triggers_recheck() {
		$this->plugin->on_plugin_activated( 'seo-by-rank-math/rank-math.php' );
		$this->assertTrue( (bool) get_option( 'rank_math_api_dependencies_status', false ) );
	}
}
