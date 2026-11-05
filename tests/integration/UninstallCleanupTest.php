<?php
/**
 * Integration tests: uninstall hook removes plugin options.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class UninstallCleanupTest
 */
class UninstallCleanupTest extends WP_UnitTestCase {

	/**
	 * Seed options then run uninstall cleanup.
	 */
	public function test_uninstall_removes_plugin_options() {
		update_option( 'rank_math_api_activated', '2020-01-01 00:00:00', false );
		update_option( 'rank_math_api_dependencies_status', true, false );
		update_option( 'rank_math_api_github_token', 'test-token', false );
		update_option(
			'rank_math_api_telemetry_settings',
			array(
				'enabled' => true,
				'site_id' => 'test-site-id',
			),
			false
		);
		set_transient( 'rank_math_api_github_release', array( 'version' => '9.9.9' ), 3600 );

		rank_math_api_manager_uninstall();

		$this->assertFalse( get_option( 'rank_math_api_activated', false ) );
		$this->assertFalse( get_option( 'rank_math_api_dependencies_status', false ) );
		$this->assertFalse( get_option( 'rank_math_api_github_token', false ) );
		$this->assertFalse( get_option( 'rank_math_api_telemetry_settings', false ) );
		$this->assertFalse( get_transient( 'rank_math_api_github_release' ) );
	}
}
