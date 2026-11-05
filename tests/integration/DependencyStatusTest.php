<?php
/**
 * Integration tests: dependency status reporting.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class DependencyStatusTest
 */
class DependencyStatusTest extends WP_UnitTestCase {

	/**
	 * Dependency status includes Rank Math when stubbed active.
	 */
	public function test_get_dependency_status_reports_rank_math_active() {
		$plugin = Rank_Math_API_Manager_Extended::get_instance();
		$status = $plugin->get_dependency_status();

		$this->assertIsArray( $status );
		$this->assertArrayHasKey( 'dependencies_met', $status );
		$this->assertTrue( $status['dependencies_met'] );
		$this->assertArrayHasKey( 'missing_plugins', $status );
	}
}
