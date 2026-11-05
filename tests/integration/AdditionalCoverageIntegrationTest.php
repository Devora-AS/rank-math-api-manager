<?php
/**
 * Integration tests: additional REST, updater errors, and notice bundles.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class AdditionalCoverageIntegrationTest
 */
class AdditionalCoverageIntegrationTest extends WP_UnitTestCase {

	/**
	 * Plugin instance.
	 *
	 * @var Rank_Math_API_Manager_Extended
	 */
	private $plugin;

	/**
	 * Editor user ID.
	 *
	 * @var int
	 */
	private $user_id;

	/**
	 * Set up.
	 */
	public function set_up() {
		parent::set_up();
		$this->plugin  = Rank_Math_API_Manager_Extended::get_instance();
		$this->user_id = $this->factory->user->create( array( 'role' => 'editor' ) );
	}

	/**
	 * Attachment post type is rejected by update-meta endpoint.
	 */
	public function test_update_meta_rejects_attachment_post_type() {
		wp_set_current_user( $this->user_id );
		$attachment_id = $this->factory->post->create(
			array(
				'post_type'   => 'attachment',
				'post_status' => 'inherit',
			)
		);

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $attachment_id );
		$request->set_param( 'rank_math_title', 'Should Fail' );
		$response = rest_do_request( $request );

		$this->assertSame( 400, $response->get_status() );
	}

	/**
	 * Update all supported SEO fields in one request.
	 */
	public function test_update_meta_sets_all_supported_fields() {
		wp_set_current_user( $this->user_id );
		$post_id = $this->factory->post->create(
			array(
				'post_type'   => 'post',
				'post_status' => 'publish',
			)
		);

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $post_id );
		$request->set_param( 'rank_math_title', 'All Fields Title' );
		$request->set_param( 'rank_math_description', 'All Fields Description' );
		$request->set_param( 'rank_math_canonical_url', 'https://example.com/canonical' );
		$request->set_param( 'rank_math_focus_keyword', 'all-fields' );
		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status() );
		$this->assertSame( 'All Fields Title', get_post_meta( $post_id, 'rank_math_title', true ) );
		$this->assertSame( 'All Fields Description', get_post_meta( $post_id, 'rank_math_description', true ) );
	}

	/**
	 * GitHub API non-200 response does not populate update response.
	 */
	public function test_github_api_http_error_does_not_add_update() {
		delete_transient( 'rank_math_api_github_release' );
		update_option( 'rank_math_api_last_github_check', 0, false );

		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'api.github.com' ) ) {
					return array(
						'response' => array( 'code' => 500 ),
						'body'     => 'error',
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

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );
		$this->assertEmpty( $filtered->response );
	}

	/**
	 * Deactivation cleanup sends telemetry when enabled.
	 */
	public function test_handle_plugin_deactivation_cleanup_with_telemetry_enabled() {
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

		$this->plugin->handle_plugin_deactivation_cleanup();
		$this->assertFalse( wp_next_scheduled( 'rank_math_api_telemetry_heartbeat' ) );
	}

	/**
	 * on_plugin_deactivated for dependency queues deactivation notice path.
	 */
	public function test_on_plugin_deactivated_for_rank_math_dependency() {
		$this->plugin->on_plugin_deactivated( 'seo-by-rank-math/rank-math.php' );
		$events = get_option( 'rank_math_api_notice_events', array() );
		$this->assertArrayHasKey( 'dependency_deactivated', $events );
	}

	/**
	 * Render bundled notice events on plugins screen.
	 */
	public function test_render_admin_notices_with_multiple_queued_events() {
		$admin_id = $this->factory->user->create( array( 'role' => 'administrator' ) );
		wp_set_current_user( $admin_id );
		set_current_screen( 'plugins' );

		$this->plugin->queue_notice_event( 'dependency_restored' );
		$this->plugin->queue_notice_event( 'dependency_deactivated' );
		$this->plugin->queue_notice_event( 'telemetry_enabled' );
		$this->plugin->queue_notice_event( 'telemetry_disabled' );

		ob_start();
		$this->plugin->render_admin_notices();
		$output = ob_get_clean();

		$this->assertStringContainsString( 'Rank Math API Manager', $output );
	}

	/**
	 * Plugin version accessor returns constant value.
	 */
	public function test_get_version_returns_plugin_constant() {
		$this->assertSame( RANK_MATH_API_VERSION, $this->plugin->get_version() );
	}

	/**
	 * check_for_update ignores unrelated plugins in checked list.
	 */
	public function test_check_for_update_ignores_when_plugin_not_in_checked_list() {
		$transient = (object) array(
			'checked'  => array(
				'hello.php' => '1.7.2',
			),
			'response' => array(),
		);

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );
		$this->assertSame( $transient, $filtered );
	}

	/**
	 * Invalid update transient shape returns early without errors.
	 */
	public function test_check_for_update_returns_early_for_invalid_transient() {
		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', 'not-an-object' );
		$this->assertSame( 'not-an-object', $filtered );
	}
}
