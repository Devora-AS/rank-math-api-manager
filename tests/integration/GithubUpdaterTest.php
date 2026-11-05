<?php
/**
 * Integration tests: GitHub updater HTTP fetch and release validation.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class GithubUpdaterTest
 */
class GithubUpdaterTest extends WP_UnitTestCase {

	/**
	 * Plugin basename.
	 *
	 * @var string
	 */
	private $plugin_basename;

	/**
	 * Set up basename.
	 */
	public function set_up() {
		parent::set_up();
		$this->plugin_basename = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
		delete_transient( 'rank_math_api_github_release' );
		delete_option( 'rank_math_api_last_github_check' );
	}

	/**
	 * Mock GitHub API response populates release transient with validated download URL.
	 */
	public function test_github_release_fetch_caches_valid_release() {
		$release_json = wp_json_encode(
			array(
				'tag_name'     => 'v2.0.0',
				'html_url'     => 'https://github.com/devora-as/rank-math-api-manager/releases/tag/v2.0.0',
				'published_at' => gmdate( 'c' ),
				'body'         => 'Release notes',
				'assets'       => array(
					array(
						'name'                 => 'rank-math-api-manager.zip',
						'browser_download_url' => 'https://github.com/devora-as/rank-math-api-manager/releases/download/v2.0.0/rank-math-api-manager.zip',
					),
				),
			)
		);

		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) use ( $release_json ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'api.github.com/repos/devora-as/rank-math-api-manager/releases/latest' ) ) {
					return array(
						'response' => array( 'code' => 200 ),
						'body'     => $release_json,
					);
				}
				return $preempt;
			},
			10,
			3
		);

		$transient = (object) array(
			'checked'  => array(
				$this->plugin_basename => RANK_MATH_API_VERSION,
			),
			'response' => array(),
		);

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );

		$cached = get_transient( 'rank_math_api_github_release' );
		$this->assertIsArray( $cached );
		$this->assertSame( '2.0.0', $cached['version'] );
		$this->assertStringContainsString( 'releases/download/v2.0.0/', $cached['download_url'] );
		$this->assertObjectHasProperty( 'response', $filtered );
		$this->assertArrayHasKey( $this->plugin_basename, $filtered->response );
	}

	/**
	 * Release with invalid download path must not populate update response.
	 */
	public function test_github_release_with_invalid_asset_is_ignored() {
		$release_json = wp_json_encode(
			array(
				'tag_name'     => 'v3.0.0',
				'html_url'     => 'https://github.com/evil/example/releases/tag/v3.0.0',
				'published_at' => gmdate( 'c' ),
				'assets'       => array(
					array(
						'name'                 => 'evil.zip',
						'browser_download_url' => 'https://evil.example/download.zip',
					),
				),
			)
		);

		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) use ( $release_json ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'api.github.com' ) ) {
					return array(
						'response' => array( 'code' => 200 ),
						'body'     => $release_json,
					);
				}
				return $preempt;
			},
			10,
			3
		);

		$transient = (object) array(
			'checked'  => array(
				$this->plugin_basename => '1.0.0',
			),
			'response' => array(),
		);

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );

		$this->assertEmpty( $filtered->response );
	}
}
