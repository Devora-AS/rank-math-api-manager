<?php
/**
 * Integration tests: Rank Math meta update for WooCommerce product (when WooCommerce is present).
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class UpdateMetaProductTest
 */
class UpdateMetaProductTest extends WP_UnitTestCase {

	/**
	 * Product ID (only set when WooCommerce is active).
	 *
	 * @var int|null
	 */
	private $product_id;

	/**
	 * User ID with edit_posts capability.
	 *
	 * @var int
	 */
	private $user_id;

	/**
	 * Set up: create product and user if WooCommerce exists.
	 */
	public function set_up() {
		parent::set_up();
		$this->user_id = $this->factory->user->create( array( 'role' => 'editor' ) );

		if ( ! class_exists( 'WooCommerce' ) || ! function_exists( 'wc_get_product' ) ) {
			return;
		}

		$this->product_id = $this->factory->post->create(
			array(
				'post_type'   => 'product',
				'post_title'  => 'Test Product for Rank Math API',
				'post_status' => 'publish',
			)
		);
	}

	/**
	 * If WooCommerce is present, update Rank Math meta for a product and assert success.
	 */
	public function test_update_rank_math_meta_for_product_succeeds_when_woocommerce_active() {
		if ( ! $this->product_id ) {
			$this->markTestSkipped( 'WooCommerce not active; product support test skipped.' );
		}

		wp_set_current_user( $this->user_id );

		$request = new WP_REST_Request( 'POST', '/rank-math-api/v1/update-meta' );
		$request->set_param( 'post_id', $this->product_id );
		$request->set_param( 'rank_math_title', 'Product SEO Title' );
		$request->set_param( 'rank_math_focus_keyword', 'product keyword' );

		$response = rest_do_request( $request );

		$this->assertSame( 200, $response->get_status() );
		$this->assertSame( 'Product SEO Title', get_post_meta( $this->product_id, 'rank_math_title', true ) );
		$this->assertSame( 'product keyword', get_post_meta( $this->product_id, 'rank_math_focus_keyword', true ) );
	}
}
