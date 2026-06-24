<?php
/**
 * Integration tests: Rejection when updating meta for an unsupported post type.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class UpdateMetaUnsupportedTypeTest
 */
class UpdateMetaUnsupportedTypeTest extends WP_UnitTestCase {

	/**
	 * Post ID of a custom post type (not in allowed list).
	 *
	 * @var int
	 */
	private $cpt_id;

	/**
	 * User ID with edit_posts capability.
	 *
	 * @var int
	 */
	private $user_id;

	/**
	 * Set up: register a custom post type and create one post.
	 */
	public function set_up() {
		parent::set_up();

		register_post_type(
			'rm_unsupported_cpt',
			array(
				'public'       => true,
				'label'        => 'Unsupported CPT',
				'show_in_rest' => true,
			)
		);
		$this->cpt_id  = $this->factory->post->create(
			array(
				'post_type'   => 'rm_unsupported_cpt',
				'post_title'  => 'Unsupported CPT Post',
				'post_status' => 'publish',
			)
		);
		$this->user_id = $this->factory->user->create( array( 'role' => 'editor' ) );
	}

	/**
	 * Attempt to update meta for unsupported post type; assert rejection.
	 */
	public function test_update_meta_for_unsupported_post_type_is_rejected() {
		wp_set_current_user( $this->user_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->cpt_id );
		$request->set_param( 'rank_math_title', 'Should not be saved' );

		$response = rest_do_request( $request );

		$this->assertSame( 400, $response->get_status(), 'Unsupported post type should be rejected with 400' );
		$error = $response->as_error();
		$this->assertInstanceOf( WP_Error::class, $error );
		$this->assertSame( 'invalid_post_id', $error->get_error_code() );
	}
}
