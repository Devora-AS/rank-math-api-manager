<?php
/**
 * Integration tests: Rank Math meta update and read for post type "page".
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class UpdateMetaPageTest
 */
class UpdateMetaPageTest extends WP_UnitTestCase {

	/**
	 * Page ID used in tests.
	 *
	 * @var int
	 */
	private $page_id;

	/**
	 * User ID with edit_posts capability.
	 *
	 * @var int
	 */
	private $user_id;

	/**
	 * Set up test page and editor user.
	 */
	public function set_up() {
		parent::set_up();
		$this->page_id = $this->factory->post->create(
			array(
				'post_type'   => 'page',
				'post_title'  => 'Test Page for Rank Math API',
				'post_status' => 'publish',
			)
		);
		$this->user_id = $this->factory->user->create(
			array(
				'role' => 'editor',
			)
		);
	}

	/**
	 * Update Rank Math fields for a page and assert success and correct meta.
	 */
	public function test_update_and_read_rank_math_meta_for_page() {
		wp_set_current_user( $this->user_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->page_id );
		$request->set_param( 'rank_math_title', 'Page SEO Title' );
		$request->set_param( 'rank_math_description', 'Page meta description.' );
		$request->set_param( 'rank_math_canonical_url', 'https://example.com/canonical-page' );
		$request->set_param( 'rank_math_focus_keyword', 'page keyword' );

		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status(), 'Update meta for page should succeed' );
		$data = $response->get_data();
		$this->assertIsArray( $data );
		$this->assertArrayHasKey( 'rank_math_title', $data );
		$this->assertArrayHasKey( 'rank_math_description', $data );
		$this->assertArrayHasKey( 'rank_math_canonical_url', $data );
		$this->assertArrayHasKey( 'rank_math_focus_keyword', $data );

		$this->assertSame( 'Page SEO Title', get_post_meta( $this->page_id, 'rank_math_title', true ) );
		$this->assertSame( 'Page meta description.', get_post_meta( $this->page_id, 'rank_math_description', true ) );
		$this->assertSame( 'https://example.com/canonical-page', get_post_meta( $this->page_id, 'rank_math_canonical_url', true ) );
		$this->assertSame( 'page keyword', get_post_meta( $this->page_id, 'rank_math_focus_keyword', true ) );
	}
}
