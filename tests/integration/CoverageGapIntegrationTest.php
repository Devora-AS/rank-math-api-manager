<?php
/**
 * Integration tests: additional branches for the main-file coverage gate.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class CoverageGapIntegrationTest
 */
class CoverageGapIntegrationTest extends WP_UnitTestCase {

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
	 * sanitize_telemetry_settings normalizes enabled flag and preserves site id.
	 */
	public function test_sanitize_telemetry_settings_normalizes_payload() {
		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'sanitize_telemetry_settings' );
		$result     = $method->invoke(
			$this->plugin,
			array(
				'enabled' => 1,
				'site_id' => 'abc-123',
			)
		);

		$this->assertTrue( $result['enabled'] );
		$this->assertNotEmpty( $result['site_id'] );
	}

	/**
	 * send_telemetry_event sends activate payload when telemetry is enabled.
	 */
	public function test_send_telemetry_event_activate_when_enabled() {
		update_option(
			'rank_math_api_telemetry_settings',
			array(
				'enabled' => true,
				'site_id' => 'test-site-id',
			),
			false
		);

		$seen     = false;
		$method_s = null;
		$event_t  = null;
		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) use ( &$seen, &$method_s, &$event_t ) {
				unset( $preempt );
				if ( false !== strpos( $url, 'updates.devora.no' ) ) {
					$seen     = true;
					$method_s = isset( $args['method'] ) ? $args['method'] : '';
					$body     = json_decode( $args['body'], true );
					$event_t  = isset( $body['event_type'] ) ? $body['event_type'] : '';
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

		$this->assertTrue( $this->plugin->send_telemetry_event( 'activate' ) );
		$this->assertTrue( $seen );
		$this->assertSame( 'POST', $method_s );
		$this->assertSame( 'activate', $event_t );
	}

	/**
	 * handle_plugin_deactivation_cleanup clears scheduled telemetry hook.
	 */
	public function test_handle_plugin_deactivation_cleanup_clears_schedule() {
		wp_schedule_event( time() + HOUR_IN_SECONDS, 'daily', 'rank_math_api_telemetry_heartbeat' );
		$this->plugin->handle_plugin_deactivation_cleanup();
		$this->assertFalse( wp_next_scheduled( 'rank_math_api_telemetry_heartbeat' ) );
	}

	/**
	 * on_plugin_activated queues dependency restored notice for Rank Math.
	 */
	public function test_on_plugin_activated_queues_dependency_restored_for_rank_math() {
		$this->plugin->on_plugin_activated( 'seo-by-rank-math/rank-math.php' );
		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'has_notice_event' );
		$this->assertTrue( $method->invoke( $this->plugin, 'dependency_restored' ) );
	}

	/**
	 * on_plugin_deactivated queues dependency warning when Rank Math is deactivated.
	 */
	public function test_on_plugin_deactivated_queues_dependency_deactivated_for_rank_math() {
		$this->plugin->on_plugin_deactivated( 'seo-by-rank-math/rank-math.php' );
		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'has_notice_event' );
		$this->assertTrue( $method->invoke( $this->plugin, 'dependency_deactivated' ) );
	}

	/**
	 * is_valid_release_download_url rejects non-GitHub hosts.
	 */
	public function test_is_valid_release_download_url_rejects_invalid_host() {
		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'is_valid_release_download_url' );
		$this->assertFalse(
			$method->invoke( $this->plugin, 'https://evil.example/not-a-release.zip' )
		);
	}

	/**
	 * get_latest_github_release returns WP_Error when HTTP transport fails.
	 */
	public function test_get_latest_github_release_surfaces_transport_errors() {
		update_option( 'rank_math_api_last_github_check', 0, false );

		add_filter(
			'pre_http_request',
			function () {
				return new WP_Error( 'http_fail', 'Transport failed' );
			},
			10,
			3
		);

		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'get_latest_github_release' );
		$result     = $method->invoke( $this->plugin );
		$this->assertWPError( $result );
		$this->assertSame( 'api_error', $result->get_error_code() );
	}

	/**
	 * render_admin_notice outputs action buttons when actions are present.
	 */
	public function test_render_admin_notice_outputs_action_links() {
		if ( ! defined( 'WP_ADMIN' ) ) {
			define( 'WP_ADMIN', true );
		}

		$reflection = new ReflectionClass( $this->plugin );
		$method     = $reflection->getMethod( 'render_admin_notice' );
		ob_start();
		$method->invoke(
			$this->plugin,
			array(
				'type'    => 'info',
				'message' => '<p>Test notice body</p>',
				'actions' => array(
					array(
						'label' => 'Action label',
						'url'   => 'https://example.com/action',
						'class' => 'button',
					),
				),
			)
		);
		$output = ob_get_clean();
		$this->assertStringContainsString( 'Action label', $output );
		$this->assertStringContainsString( 'https://example.com/action', $output );
	}

	/**
	 * check_for_update skips when plugin is not in the checked list.
	 */
	public function test_check_for_update_skips_when_plugin_not_in_checked_list() {
		$transient = (object) array(
			'checked'  => array(),
			'response' => array(),
		);

		$result = $this->plugin->check_for_update( $transient );
		$this->assertSame( $transient, $result );
	}
}
