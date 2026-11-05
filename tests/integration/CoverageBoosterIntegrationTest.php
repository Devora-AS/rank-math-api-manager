<?php
/**
 * Integration tests: remaining admin/updater branches for coverage gate.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class CoverageBoosterIntegrationTest
 */
class CoverageBoosterIntegrationTest extends WP_UnitTestCase {

	/**
	 * Plugin instance.
	 *
	 * @var Rank_Math_API_Manager_Extended
	 */
	private $plugin;

	/**
	 * Set up plugin instance.
	 */
	public function set_up() {
		parent::set_up();
		$this->plugin = Rank_Math_API_Manager_Extended::get_instance();
	}

	/**
	 * Bootstrap function returns singleton instance.
	 */
	public function test_rank_math_api_manager_init_returns_instance() {
		$instance = rank_math_api_manager_init();
		$this->assertInstanceOf( Rank_Math_API_Manager_Extended::class, $instance );
	}

	/**
	 * Folder notice markup includes expandable reinstall instructions.
	 */
	public function test_folder_name_notice_markup_contains_reinstall_summary() {
		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'get_folder_name_notice_markup' );
		$markup     = $method->invoke( $this->plugin );
		$this->assertStringContainsString( 'Show reinstall steps', $markup );
	}

	/**
	 * Admin notice renderer outputs folder notice when WP admin context is active.
	 */
	public function test_render_admin_notices_outputs_queued_success_notice() {
		if ( ! defined( 'WP_ADMIN' ) ) {
			define( 'WP_ADMIN', true );
		}

		$admin_id = $this->factory->user->create( array( 'role' => 'administrator' ) );
		wp_set_current_user( $admin_id );
		set_current_screen( 'plugins' );

		$this->plugin->queue_notice_event( 'telemetry_disabled' );

		ob_start();
		$this->plugin->render_admin_notices();
		$output = ob_get_clean();

		$this->assertStringContainsString( 'telemetry has been disabled', strtolower( $output ) );
	}

	/**
	 * GitHub updater uses Authorization header when token is configured on the instance.
	 */
	public function test_github_request_includes_auth_header_when_token_configured() {
		update_option( 'rank_math_api_last_github_check', 0, false );
		delete_transient( 'rank_math_api_github_release' );

		$reflection = new ReflectionClass( $this->plugin );
		$property   = $reflection->getProperty( 'github_token' );
		$property->setValue( $this->plugin, 'test-token-value' );

		$auth_seen = false;
		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) use ( &$auth_seen ) {
				unset( $preempt );
				if ( false !== strpos( $url, 'api.github.com' ) ) {
					if ( ! empty( $args['headers']['Authorization'] ) ) {
						$auth_seen = true;
					}
					return array(
						'response' => array( 'code' => 404 ),
						'body'     => '',
					);
				}
				return $preempt;
			},
			10,
			3
		);

		$basename  = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
		$transient = (object) array(
			'checked'  => array(
				$basename => '1.0.0',
			),
			'response' => array(),
		);

		apply_filters( 'pre_set_site_transient_update_plugins', $transient );

		$this->assertTrue( $auth_seen );
	}

	/**
	 * Scheduled telemetry heartbeat updates last-run when send succeeds.
	 */
	public function test_scheduled_telemetry_updates_last_run_on_success() {
		update_option( 'rank_math_api_heartbeat_last_run', 0, false );
		update_option(
			'rank_math_api_telemetry_settings',
			array(
				'enabled' => true,
			),
			false
		);

		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'updates.devora.no' ) ) {
					return array(
						'response' => array( 'code' => 204 ),
						'body'     => '',
					);
				}
				return $preempt;
			},
			10,
			3
		);

		$this->plugin->send_scheduled_telemetry();

		$this->assertGreaterThan( 0, (int) get_option( 'rank_math_api_heartbeat_last_run', 0 ) );
	}

	/**
	 * check_dependencies persists updated dependency status flag.
	 */
	public function test_check_dependencies_updates_status_option() {
		update_option( 'rank_math_api_dependencies_status', false, false );
		$this->plugin->check_dependencies();
		$this->assertTrue( (bool) get_option( 'rank_math_api_dependencies_status', false ) );
	}

	/**
	 * plugins_api returns false for non-plugin_information actions.
	 */
	public function test_plugins_api_ignores_non_information_action() {
		$args   = (object) array( 'slug' => 'rank-math-api-manager' );
		$result = apply_filters( 'plugins_api', false, 'query_plugins', $args );
		$this->assertFalse( $result );
	}

	/**
	 * prepare_plugin_activation ensures telemetry site id option exists.
	 */
	public function test_prepare_plugin_activation_ensures_site_id() {
		delete_option( 'rank_math_api_telemetry_settings' );
		$this->plugin->prepare_plugin_activation();
		$settings = get_option( 'rank_math_api_telemetry_settings', array() );
		$this->assertNotEmpty( $settings['site_id'] );
	}

	/**
	 * plugin_info returns structured data when release transient is populated.
	 */
	public function test_plugin_info_returns_release_object_from_cache() {
		set_transient(
			'rank_math_api_github_release',
			array(
				'version'      => '9.9.9',
				'download_url' => 'https://github.com/devora-as/rank-math-api-manager/releases/download/v9.9.9/rank-math-api-manager.zip',
				'published_at' => gmdate( 'c' ),
				'description'  => 'Changelog line',
			),
			HOUR_IN_SECONDS
		);

		$args   = (object) array( 'slug' => 'rank-math-api-manager' );
		$result = $this->plugin->plugin_info( false, 'plugin_information', $args );

		$this->assertIsObject( $result );
		$this->assertSame( '9.9.9', $result->version );
		$this->assertStringContainsString( 'Changelog line', $result->sections['changelog'] );
	}

	/**
	 * enqueue_admin_scripts registers assets on plugins screen hook.
	 */
	public function test_enqueue_admin_scripts_loads_assets_on_plugins_screen() {
		$this->plugin->enqueue_admin_scripts( 'plugins.php' );
		$this->assertTrue( wp_script_is( 'rank-math-api-admin', 'enqueued' ) );
		$this->assertTrue( wp_style_is( 'rank-math-api-admin', 'enqueued' ) );
	}

	/**
	 * send_telemetry_event rejects unknown event types.
	 */
	public function test_send_telemetry_event_rejects_unknown_event_type() {
		$this->assertFalse( $this->plugin->send_telemetry_event( 'not-a-real-event' ) );
	}

	/**
	 * Telemetry privacy notice markup is built for the settings UI copy.
	 */
	public function test_telemetry_notice_markup_contains_opt_out_language() {
		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'get_telemetry_notice_markup' );
		$markup     = $method->invoke( $this->plugin );
		$this->assertStringContainsString( 'telemetry', strtolower( $markup ) );
	}
}
