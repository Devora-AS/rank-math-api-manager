<?php
/**
 * Integration tests: REST permission checks for update-meta.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class RestPermissionTest
 */
class RestPermissionTest extends WP_UnitTestCase {

	/**
	 * Post ID owned by editor.
	 *
	 * @var int
	 */
	private $post_id;

	/**
	 * Editor user ID.
	 *
	 * @var int
	 */
	private $editor_id;

	/**
	 * Subscriber user ID.
	 *
	 * @var int
	 */
	private $subscriber_id;

	/**
	 * Set up users and post.
	 */
	public function set_up() {
		parent::set_up();
		$this->post_id       = $this->factory->post->create(
			array(
				'post_type'   => 'post',
				'post_status' => 'publish',
			)
		);
		$this->editor_id     = $this->factory->user->create( array( 'role' => 'editor' ) );
		$this->subscriber_id = $this->factory->user->create( array( 'role' => 'subscriber' ) );
	}

	/**
	 * Logged-out requests receive 401.
	 */
	public function test_update_meta_requires_authentication() {
		wp_set_current_user( 0 );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->post_id );
		$response = rest_do_request( $request );

		$this->assertSame( 401, $response->get_status() );
	}

	/**
	 * Users without edit_post capability receive 403.
	 */
	public function test_update_meta_denies_user_without_edit_post_cap() {
		wp_set_current_user( $this->subscriber_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->post_id );
		$request->set_param( 'rank_math_title', 'Denied Title' );
		$response = rest_do_request( $request );

		$this->assertSame( 403, $response->get_status() );
	}

	/**
	 * Editor can update own editable post.
	 */
	public function test_update_meta_allows_editor_with_capability() {
		wp_set_current_user( $this->editor_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->post_id );
		$request->set_param( 'rank_math_title', 'Allowed Title' );
		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status() );
	}
}
