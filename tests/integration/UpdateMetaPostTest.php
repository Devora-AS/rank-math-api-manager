<?php
/**
 * Integration tests: Rank Math meta update for post type "post".
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class UpdateMetaPostTest
 */
class UpdateMetaPostTest extends WP_UnitTestCase {

	/**
	 * Post ID.
	 *
	 * @var int
	 */
	private $post_id;

	/**
	 * User ID with edit_posts capability.
	 *
	 * @var int
	 */
	private $user_id;

	/**
	 * Set up test post and editor user.
	 */
	public function set_up() {
		parent::set_up();
		$this->post_id = $this->factory->post->create(
			array(
				'post_type'   => 'post',
				'post_title'  => 'Test Post for Rank Math API',
				'post_status' => 'publish',
			)
		);
		$this->user_id = $this->factory->user->create( array( 'role' => 'editor' ) );
	}

	/**
	 * Update Rank Math meta for a post and assert success.
	 */
	public function test_update_rank_math_meta_for_post_succeeds() {
		wp_set_current_user( $this->user_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->post_id );
		$request->set_param( 'rank_math_title', 'Post SEO Title' );
		$request->set_param( 'rank_math_focus_keyword', 'post keyword' );

		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status() );
		$this->assertSame( 'Post SEO Title', get_post_meta( $this->post_id, 'rank_math_title', true ) );
		$this->assertSame( 'post keyword', get_post_meta( $this->post_id, 'rank_math_focus_keyword', true ) );
	}
}
