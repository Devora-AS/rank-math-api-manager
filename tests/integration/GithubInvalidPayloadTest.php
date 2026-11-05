<?php
/**
 * Integration tests: invalid GitHub API payloads.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class GithubInvalidPayloadTest
 */
class GithubInvalidPayloadTest extends WP_UnitTestCase {

	/**
	 * Invalid JSON body does not add plugin update response.
	 */
	public function test_github_invalid_json_body_is_handled() {
		delete_transient( 'rank_math_api_github_release' );
		update_option( 'rank_math_api_last_github_check', 0, false );

		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'api.github.com' ) ) {
					return array(
						'response' => array( 'code' => 200 ),
						'body'     => 'not-json',
					);
				}
				return $preempt;
			},
			10,
			3
		);

		$basename  = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
		$transient = (object) array(
			'checked'  => array(
				$basename => '1.0.0',
			),
			'response' => array(),
		);

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );
		$this->assertEmpty( $filtered->response );
	}

	/**
	 * JSON without tag_name is rejected.
	 */
	public function test_github_missing_tag_name_is_handled() {
		delete_transient( 'rank_math_api_github_release' );
		update_option( 'rank_math_api_last_github_check', 0, false );

		add_filter(
			'pre_http_request',
			function ( $preempt, $args, $url ) {
				unset( $preempt, $args );
				if ( false !== strpos( $url, 'api.github.com' ) ) {
					return array(
						'response' => array( 'code' => 200 ),
						'body'     => wp_json_encode( array( 'assets' => array() ) ),
					);
				}
				return $preempt;
			},
			10,
			3
		);

		$basename  = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
		$transient = (object) array(
			'checked'  => array(
				$basename => '1.0.0',
			),
			'response' => array(),
		);

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );
		$this->assertEmpty( $filtered->response );
	}
}
