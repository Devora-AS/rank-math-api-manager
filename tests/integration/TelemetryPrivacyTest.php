<?php
/**
 * Integration tests: telemetry opt-out and privacy-safe payloads.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class TelemetryPrivacyTest
 */
class TelemetryPrivacyTest extends WP_UnitTestCase {

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
	 * Telemetry disabled must not send HTTP requests.
	 */
	public function test_telemetry_disabled_does_not_send_http() {
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

		$result = $this->plugin->send_telemetry_event( 'heartbeat' );

		$this->assertFalse( $result );
		$this->assertFalse( $http_called, 'Telemetry HTTP must not run when disabled.' );
	}

	/**
	 * Invalid event types are rejected without HTTP.
	 */
	public function test_telemetry_rejects_unknown_event_type() {
		update_option(
			'rank_math_api_telemetry_settings',
			array(
				'enabled' => true,
			),
			false
		);

		$this->assertFalse( $this->plugin->send_telemetry_event( 'invalid_event' ) );
	}

	/**
	 * Enabled telemetry posts JSON to the fixed Devora endpoint.
	 */
	public function test_telemetry_enabled_sends_to_devora_endpoint() {
		update_option(
			'rank_math_api_telemetry_settings',
			array(
				'enabled' => true,
			),
			false
		);

		$captured_url    = '';
		$captured_body   = '';
		$filter_callback = function ( $preempt, $args, $url ) use ( &$captured_url, &$captured_body ) {
			unset( $preempt );
			$captured_url  = $url;
			$captured_body = isset( $args['body'] ) ? $args['body'] : '';
			return array(
				'response' => array( 'code' => 204 ),
				'body'     => '',
			);
		};
		add_filter( 'pre_http_request', $filter_callback, 10, 3 );

		$result = $this->plugin->send_telemetry_event( 'activate' );

		remove_filter( 'pre_http_request', $filter_callback, 10 );

		$this->assertTrue( $result );
		$this->assertSame( 'https://updates.devora.no/v1/telemetry', $captured_url );
		$decoded = json_decode( $captured_body, true );
		$this->assertIsArray( $decoded );
		$this->assertSame( 'activate', $decoded['event_type'] );
		$this->assertSame( 'rank-math-api-manager', $decoded['plugin_slug'] );
		$this->assertArrayNotHasKey( 'admin_email', $decoded );
		$this->assertArrayNotHasKey( 'site_url', $decoded );
	}
}
