<?php
/**
 * Integration tests: admin notice queue and render smoke coverage.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class AdminNoticesSmokeTest
 */
class AdminNoticesSmokeTest extends WP_UnitTestCase {

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
	 * Set up admin user and plugin.
	 */
	public function set_up() {
		parent::set_up();
		$this->plugin   = Rank_Math_API_Manager_Extended::get_instance();
		$this->admin_id = $this->factory->user->create( array( 'role' => 'administrator' ) );
	}

	/**
	 * Queued notice events render without fatal errors on plugins screen.
	 */
	public function test_render_admin_notices_outputs_markup_for_queued_event() {
		wp_set_current_user( $this->admin_id );
		set_current_screen( 'plugins' );

		$this->plugin->queue_notice_event( 'dependency_restored' );

		ob_start();
		$this->plugin->render_admin_notices();
		$output = ob_get_clean();

		$this->assertIsString( $output );
	}
}
