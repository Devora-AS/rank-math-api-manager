<?php
/**
 * Integration tests: post meta REST auth callback.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class MetaAuthPermissionTest
 */
class MetaAuthPermissionTest extends WP_UnitTestCase {

	/**
	 * Plugin instance.
	 *
	 * @var Rank_Math_API_Manager_Extended
	 */
	private $plugin;

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
	 * Set up plugin, post, and user.
	 */
	public function set_up() {
		parent::set_up();
		$this->plugin  = Rank_Math_API_Manager_Extended::get_instance();
		$this->post_id = $this->factory->post->create(
			array(
				'post_type'   => 'post',
				'post_status' => 'publish',
			)
		);
		$this->user_id = $this->factory->user->create( array( 'role' => 'editor' ) );
	}

	/**
	 * Meta auth callback allows editors to update supported meta keys.
	 */
	public function test_meta_auth_allows_editor_for_supported_post() {
		wp_set_current_user( $this->user_id );

		$allowed = $this->plugin->check_meta_auth_permission( false, 'rank_math_title', $this->post_id, $this->user_id, 'edit_post', array() );

		$this->assertTrue( $allowed );
	}

	/**
	 * Meta auth callback denies unsupported post targets.
	 */
	public function test_meta_auth_denies_invalid_post_target() {
		wp_set_current_user( $this->user_id );

		$allowed = $this->plugin->check_meta_auth_permission( false, 'rank_math_title', 0, $this->user_id, 'edit_post', array() );

		$this->assertFalse( $allowed );
	}
}
