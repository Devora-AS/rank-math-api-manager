<?php
/**
 * Integration tests: REST update-meta edge cases (unchanged values, canonical URL).
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class UpdateMetaEdgeCasesTest
 */
class UpdateMetaEdgeCasesTest extends WP_UnitTestCase {

	/**
	 * Post ID.
	 *
	 * @var int
	 */
	private $post_id;

	/**
	 * Editor user ID.
	 *
	 * @var int
	 */
	private $user_id;

	/**
	 * Set up post and editor.
	 */
	public function set_up() {
		parent::set_up();
		$this->post_id = $this->factory->post->create(
			array(
				'post_type'   => 'post',
				'post_status' => 'publish',
			)
		);
		$this->user_id = $this->factory->user->create( array( 'role' => 'editor' ) );
	}

	/**
	 * Unchanged meta values return status unchanged in response data.
	 */
	public function test_update_meta_reports_unchanged_when_value_matches() {
		wp_set_current_user( $this->user_id );
		update_post_meta( $this->post_id, 'rank_math_title', 'Existing Title' );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->post_id );
		$request->set_param( 'rank_math_title', 'Existing Title' );
		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status() );
		$data = $response->get_data();
		$this->assertIsArray( $data );
		$this->assertArrayHasKey( 'rank_math_title', $data );
		$this->assertSame( 'unchanged', $data['rank_math_title'] );
	}

	/**
	 * Canonical URL is sanitized to a safe URL string.
	 */
	public function test_update_meta_sanitizes_canonical_url() {
		wp_set_current_user( $this->user_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->post_id );
		$request->set_param( 'rank_math_canonical_url', 'https://example.com/path/?q=1' );
		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status() );
		$this->assertSame(
			'https://example.com/path/?q=1',
			get_post_meta( $this->post_id, 'rank_math_canonical_url', true )
		);
	}

	/**
	 * Invalid canonical URL is rejected or emptied by sanitizer.
	 */
	public function test_update_meta_rejects_invalid_canonical_url() {
		wp_set_current_user( $this->user_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->post_id );
		$request->set_param( 'rank_math_canonical_url', 'javascript:alert(1)' );
		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status() );
		$stored = get_post_meta( $this->post_id, 'rank_math_canonical_url', true );
		$this->assertSame( '', $stored );
	}
}
