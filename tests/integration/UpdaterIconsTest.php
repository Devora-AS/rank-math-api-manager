<?php
/**
 * Integration tests: Updater / plugin_info response includes icons with valid URLs.
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class UpdaterIconsTest
 */
class UpdaterIconsTest extends WP_UnitTestCase {

	/**
	 * Plugin basename.
	 *
	 * @var string
	 */
	private $plugin_basename;

	/**
	 * Set up plugin basename.
	 */
	public function set_up() {
		parent::set_up();
		$this->plugin_basename = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
	}

	/**
	 * Update transient flow: object in response includes icons array with valid URLs.
	 */
	public function test_update_response_includes_icons_with_plugin_url() {
		// Simulate an update available so the plugin adds its data to the transient.
		$newer_version   = '99.0.0';
		$current_version = defined( 'RANK_MATH_API_VERSION' ) ? RANK_MATH_API_VERSION : '1.0.0';
		if ( version_compare( $newer_version, $current_version, '<=' ) ) {
			$this->markTestSkipped( 'Cannot simulate newer version; test assumes remote is newer.' );
		}

		// Force the plugin to add update data by mocking the release transient.
		$release_data = array(
			'version'      => $newer_version,
			'download_url' => 'https://github.com/devora-as/rank-math-api-manager/releases/download/v99.0.0/rank-math-api-manager.zip',
			'published_at' => gmdate( 'c' ),
			'description'  => '',
			'url'          => 'https://github.com/devora-as/rank-math-api-manager/releases',
		);
		set_transient( 'rank_math_api_github_release', $release_data, 3600 );

		$transient = (object) array(
			'checked'  => array(
				$this->plugin_basename => $current_version,
			),
			'response' => array(),
		);

		$filtered = apply_filters( 'pre_set_site_transient_update_plugins', $transient );

		$this->assertObjectHasAttribute( 'response', $filtered );
		$this->assertArrayHasKey( $this->plugin_basename, $filtered->response );
		$plugin_data = $filtered->response[ $this->plugin_basename ];
		$this->assertObjectHasAttribute( 'icons', $plugin_data );
		$this->assertIsArray( $plugin_data->icons );
		$this->assertNotEmpty( $plugin_data->icons );

		$plugin_url = defined( 'RANK_MATH_API_PLUGIN_URL' ) ? RANK_MATH_API_PLUGIN_URL : '';
		$this->assertNotEmpty( $plugin_url, 'RANK_MATH_API_PLUGIN_URL should be defined' );
		foreach ( $plugin_data->icons as $key => $url ) {
			$this->assertIsString( $url );
			$this->assertStringContainsString( $plugin_url, $url, "Icon URL for key {$key} should contain plugin URL" );
			$this->assertMatchesRegularExpression( '#^https?://#', $url );
		}
	}

	/**
	 * Plugin info (plugins_api) flow: returned object includes icons array with valid URLs.
	 */
	public function test_plugin_info_includes_icons_with_plugin_url() {
		$release_data = array(
			'version'      => '1.0.9',
			'download_url' => 'https://github.com/devora-as/rank-math-api-manager/releases/download/v1.0.9/rank-math-api-manager.zip',
			'published_at' => gmdate( 'c' ),
			'description'  => 'Release notes',
			'url'          => 'https://github.com/devora-as/rank-math-api-manager/releases',
		);
		set_transient( 'rank_math_api_github_release', $release_data, 3600 );

		$args = (object) array( 'slug' => 'rank-math-api-manager' );
		$res  = apply_filters( 'plugins_api', false, 'plugin_information', $args );

		$this->assertNotFalse( $res );
		$this->assertIsObject( $res );
		$this->assertObjectHasAttribute( 'icons', $res );
		$this->assertIsArray( $res->icons );
		$this->assertNotEmpty( $res->icons );

		$plugin_url = defined( 'RANK_MATH_API_PLUGIN_URL' ) ? RANK_MATH_API_PLUGIN_URL : '';
		$this->assertNotEmpty( $plugin_url );
		foreach ( $res->icons as $key => $url ) {
			$this->assertIsString( $url );
			$this->assertStringContainsString( $plugin_url, $url );
			$this->assertMatchesRegularExpression( '#^https?://#', $url );
		}
	}
}
