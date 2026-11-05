<?php
/**
 * Integration tests: textdomain loads on init, not during early get_plugin_data().
 *
 * @package Rank_Math_API_Manager
 */

/**
 * Class TextdomainLoadingTest
 */
class TextdomainLoadingTest extends WP_UnitTestCase {

	/**
	 * Domain slug for this plugin.
	 *
	 * @var string
	 */
	private $text_domain = 'rank-math-api-manager';

	/**
	 * Plugin singleton instance.
	 *
	 * @return Rank_Math_API_Manager_Extended
	 */
	private function plugin_instance() {
		$this->assertTrue(
			class_exists( 'Rank_Math_API_Manager_Extended', false ),
			'Plugin class should be loaded by tests/bootstrap.php'
		);

		return Rank_Math_API_Manager_Extended::get_instance();
	}

	/**
	 * init priority 0 must register load_textdomain on the plugin instance.
	 */
	public function test_init_registers_load_textdomain_at_priority_zero() {
		$instance = $this->plugin_instance();

		$this->assertTrue(
			method_exists( $instance, 'load_textdomain' ),
			'Plugin must expose a public load_textdomain() method.'
		);

		$priority = has_action( 'init', array( $instance, 'load_textdomain' ) );
		$this->assertSame(
			0,
			$priority,
			'load_textdomain must be hooked to init at priority 0.'
		);
	}

	/**
	 * Reading plugin headers without translation must not trigger JIT textdomain load.
	 */
	public function test_get_plugin_data_without_translate_does_not_trigger_jit_notice() {
		if ( ! function_exists( 'get_plugin_data' ) ) {
			require_once ABSPATH . 'wp-admin/includes/plugin.php';
		}

		$jit_notices = array();

		add_action(
			'doing_it_wrong_run',
			static function ( $function_name, $message ) use ( &$jit_notices ) {
				if ( '_load_textdomain_just_in_time' !== $function_name ) {
					return;
				}
				if ( false !== strpos( $message, 'rank-math-api-manager' ) ) {
					$jit_notices[] = $message;
				}
			},
			10,
			2
		);

		get_plugin_data( RANK_MATH_API_PLUGIN_FILE, false, false );

		$this->assertEmpty(
			$jit_notices,
			'get_plugin_data( ..., false, false ) must not trigger _load_textdomain_just_in_time for this domain.'
		);
	}

	/**
	 * load_textdomain callback registers the plugin languages path with WordPress.
	 */
	public function test_load_textdomain_callback_loads_domain_on_init() {
		global $wp_textdomain_registry;

		$instance = $this->plugin_instance();

		$instance->load_textdomain();

		$this->assertInstanceOf(
			WP_Textdomain_Registry::class,
			$wp_textdomain_registry,
			'WordPress textdomain registry should be available.'
		);

		$this->assertTrue(
			$wp_textdomain_registry->has( $this->text_domain ),
			'load_textdomain() must register rank-math-api-manager with the textdomain registry.'
		);

		$expected_languages_dir = WP_PLUGIN_DIR . '/rank-math-api-manager/languages';
		$registered_path        = $wp_textdomain_registry->get( $this->text_domain, get_locale() );
		$this->assertSame(
			trailingslashit( $expected_languages_dir ),
			$registered_path,
			'Registry should point at the plugin languages directory.'
		);
	}
}
