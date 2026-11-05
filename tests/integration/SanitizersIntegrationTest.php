<?php
/**
 * Integration tests: public sanitizer methods.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class SanitizersIntegrationTest
 */
class SanitizersIntegrationTest extends WP_UnitTestCase {

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
	 * Non-scalar text values sanitize to empty string.
	 */
	public function test_sanitize_rank_math_text_field_rejects_non_scalar() {
		$this->assertSame( '', $this->plugin->sanitize_rank_math_text_field( array( 'x' ) ) );
	}

	/**
	 * Non-scalar canonical values sanitize to empty string.
	 */
	public function test_sanitize_rank_math_canonical_url_rejects_non_scalar() {
		$this->assertSame( '', $this->plugin->sanitize_rank_math_canonical_url( new stdClass() ) );
	}

	/**
	 * Non-scalar focus keyword values sanitize to empty string.
	 */
	public function test_sanitize_rank_math_focus_keyword_rejects_non_scalar() {
		$this->assertSame( '', $this->plugin->sanitize_rank_math_focus_keyword( null ) );
	}
}
