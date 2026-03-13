<?php
/**
 * Plugin Name: Rank Math API Manager
 * Plugin URI: https://devora.no/plugins/rankmath-api-manager
 * Description: A WordPress extension that manages the update of Rank Math metadata (SEO Title, SEO Description, Canonical URL, Focus Keyword) via the REST API for WordPress posts and WooCommerce products.
 * Version: 1.0.9.1
 * Author: Devora AS
 * Author URI: https://devora.no
 * License: GPL v3 or later
 * License URI: https://www.gnu.org/licenses/gpl-3.0.html
 * Text Domain: rank-math-api-manager
 * Update URI: https://github.com/devora-as/rank-math-api-manager
 * Requires at least: 5.0
 * Tested up to: 6.9.3
 * Requires PHP: 7.4
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// Define plugin constants
define('RANK_MATH_API_VERSION', '1.0.9.1');
define('RANK_MATH_API_PLUGIN_FILE', __FILE__);
define('RANK_MATH_API_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('RANK_MATH_API_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * Main Plugin Class
 *
 * @since 1.0.7
 */
class Rank_Math_API_Manager_Extended {
	
	/**
	 * Plugin instance
	 *
	 * @var Rank_Math_API_Manager_Extended
	 */
	private static $instance = null;

	/**
	 * Plugin data
	 *
	 * @var array
	 */
	private $plugin_data = null;

	/**
	 * GitHub repository information
	 *
	 * @var array
	 */
	private $github_repo = array(
		'owner' => 'devora-as',
		'repo'  => 'rank-math-api-manager',
		'api_url' => 'https://api.github.com/repos/devora-as/rank-math-api-manager/releases/latest'
	);

	/**
	 * GitHub API authentication token
	 *
	 * @var string|null
	 */
	private $github_token = null;

	/**
	 * Get plugin instance
	 *
	 * @return Rank_Math_API_Manager_Extended
	 */
	public static function get_instance() {
		if (null === self::$instance) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	/**
	 * Constructor
	 */
	private function __construct() {
		$this->init_plugin_data();
		$this->init_hooks();
	}

	/**
	 * Initialize plugin data
	 *
	 * @since 1.0.7
	 */
	private function init_plugin_data() {
		if ( ! function_exists( 'get_plugin_data' ) ) {
			require_once ABSPATH . 'wp-admin/includes/plugin.php';
		}
		
		$this->plugin_data = get_plugin_data( RANK_MATH_API_PLUGIN_FILE );
		if ( ! is_array( $this->plugin_data ) ) {
			$this->plugin_data = array();
		}
		
		// Initialize GitHub token for higher rate limits
		$this->init_github_auth();
	}

	/**
	 * Initialize GitHub authentication
	 *
	 * @since 1.0.8
	 */
	private function init_github_auth() {
		// Check for GitHub token in WordPress options (secure storage)
		$this->github_token = get_option( 'rank_math_api_github_token' );
		
		// If no token, check for environment variable
		if ( ! $this->github_token && defined( 'RANK_MATH_GITHUB_TOKEN' ) ) {
			$this->github_token = RANK_MATH_GITHUB_TOKEN;
		}
	}

	/**
	 * Initialize WordPress hooks
	 */
	private function init_hooks() {
		// Check dependencies first
		add_action( 'plugins_loaded', [ $this, 'check_dependencies' ], 5 );
		
		// Monitor plugin activation/deactivation
		add_action( 'activated_plugin', [ $this, 'on_plugin_activated' ] );
		add_action( 'deactivated_plugin', [ $this, 'on_plugin_deactivated' ] );
		add_action( 'admin_init', [ $this, 'handle_notice_actions' ] );
		add_action( 'admin_init', [ $this, 'register_plugin_settings' ] );
		add_action( 'rank_math_api_telemetry_heartbeat', [ $this, 'send_scheduled_telemetry' ] );
		
		// Auto-update system hooks
		add_filter( 'pre_set_site_transient_update_plugins', [ $this, 'check_for_update' ] );
		add_filter( 'plugins_api', [ $this, 'plugin_info' ], 10, 3 );
		
		// Only register core functionality hooks if dependencies are met
		if ( $this->are_dependencies_met() ) {
			add_action( 'rest_api_init', [ $this, 'register_meta_fields' ] );
			add_action( 'rest_api_init', [ $this, 'register_api_routes' ] );
			add_action( 'admin_enqueue_scripts', [ $this, 'enqueue_admin_scripts' ] );
		}
		
		// Admin notices and operator actions.
		add_action( 'admin_notices', [ $this, 'render_admin_notices' ] );
	}

	/**
	 * Check if required plugins are active
	 *
	 * @since 1.0.7
	 * @return bool True if all dependencies are met
	 */
	public function are_dependencies_met() {
		$status = $this->get_dependency_status();
		return $status['dependencies_met'];
	}

	/**
	 * Get list of required plugins
	 *
	 * @since 1.0.7
	 * @return array Array of required plugins
	 */
	private function get_required_plugins() {
		return array(
			array(
				'name' => 'Rank Math SEO',
				'file' => 'seo-by-rank-math/rank-math.php',
				'version' => '1.0.0',
				'url' => 'https://wordpress.org/plugins/seo-by-rank-math/',
				'description' => 'Required for SEO metadata management'
			)
		);
	}

	/**
	 * Get supported post types for Rank Math updates.
	 *
	 * @since 1.0.8
	 * @return array
	 */
	private function get_allowed_post_types() {
		$post_types = array( 'post' );

		if ( class_exists( 'WooCommerce' ) ) {
			$post_types[] = 'product';
		}

		return $post_types;
	}

	/**
	 * Get supported Rank Math meta field definitions.
	 *
	 * @since 1.0.8
	 * @return array
	 */
	private function get_supported_meta_fields() {
		return array(
			'rank_math_title'         => array(
				'description'       => 'SEO Title',
				'sanitize_callback' => array( $this, 'sanitize_rank_math_text_field' ),
			),
			'rank_math_description'   => array(
				'description'       => 'SEO Description',
				'sanitize_callback' => array( $this, 'sanitize_rank_math_text_field' ),
			),
			'rank_math_canonical_url' => array(
				'description'       => 'Canonical URL',
				'sanitize_callback' => array( $this, 'sanitize_rank_math_canonical_url' ),
			),
			'rank_math_focus_keyword' => array(
				'description'       => 'Focus Keyword',
				'sanitize_callback' => array( $this, 'sanitize_rank_math_focus_keyword' ),
			),
		);
	}

	/**
	 * Check whether a post target is supported by this plugin.
	 *
	 * @since 1.0.8
	 * @param int $post_id Post ID.
	 * @return bool
	 */
	private function is_supported_post_target( $post_id ) {
		$post = get_post( $post_id );

		if ( ! $post ) {
			return false;
		}

		return in_array( $post->post_type, $this->get_allowed_post_types(), true );
	}

	/**
	 * Sanitize Rank Math text-based fields to mirror Rank Math behavior.
	 *
	 * @since 1.0.8
	 * @param mixed $value Raw field value.
	 * @return string
	 */
	public function sanitize_rank_math_text_field( $value ) {
		if ( ! is_scalar( $value ) ) {
			return '';
		}

		return wp_filter_nohtml_kses( (string) $value );
	}

	/**
	 * Sanitize Rank Math canonical URL values.
	 *
	 * @since 1.0.8
	 * @param mixed $value Raw field value.
	 * @return string
	 */
	public function sanitize_rank_math_canonical_url( $value ) {
		if ( ! is_scalar( $value ) ) {
			return '';
		}

		return esc_url_raw( (string) $value );
	}

	/**
	 * Sanitize Rank Math focus keyword values.
	 *
	 * @since 1.0.8
	 * @param mixed $value Raw field value.
	 * @return string
	 */
	public function sanitize_rank_math_focus_keyword( $value ) {
		if ( ! is_scalar( $value ) ) {
			return '';
		}

		return sanitize_text_field( (string) $value );
	}

	/**
	 * Check if a specific plugin is active
	 *
	 * @since 1.0.7
	 * @param string $plugin_file Plugin file path
	 * @return bool True if plugin is active
	 */
	private function is_plugin_active( $plugin_file ) {
		if ( ! function_exists( 'is_plugin_active' ) ) {
			require_once ABSPATH . 'wp-admin/includes/plugin.php';
		}
		
		return is_plugin_active( $plugin_file );
	}

	/**
	 * Check plugin dependencies and store status
	 *
	 * @since 1.0.7
	 */
	public function check_dependencies() {
		$dependencies_met = $this->are_dependencies_met();
		$current_status = get_option( 'rank_math_api_dependencies_status', false );
		
		// Update status if it changed
		if ( $current_status !== $dependencies_met ) {
			update_option( 'rank_math_api_dependencies_status', $dependencies_met, false );
		}
	}

	/**
	 * Get the plugin directory slug from the active installation.
	 *
	 * @since 1.0.9.1
	 * @return string
	 */
	private function get_plugin_directory_slug() {
		return dirname( plugin_basename( RANK_MATH_API_PLUGIN_FILE ) );
	}

	/**
	 * Check whether the plugin is installed in the expected directory.
	 *
	 * @since 1.0.9.1
	 * @return bool
	 */
	private function is_standard_plugin_directory() {
		return 'rank-math-api-manager' === $this->get_plugin_directory_slug();
	}

	/**
	 * Register plugin settings.
	 *
	 * @since 1.0.9.1
	 */
	public function register_plugin_settings() {
		register_setting(
			'rank_math_api_manager',
			'rank_math_api_telemetry_settings',
			array(
				'type'              => 'array',
				'sanitize_callback' => array( $this, 'sanitize_telemetry_settings' ),
				'default'           => $this->get_default_telemetry_settings(),
				'show_in_rest'      => false,
			)
		);
	}

	/**
	 * Get the default telemetry settings.
	 *
	 * @since 1.0.9.1
	 * @return array
	 */
	private function get_default_telemetry_settings() {
		return array(
			'enabled' => true,
			'site_id' => '',
		);
	}

	/**
	 * Sanitize telemetry settings before persisting them.
	 *
	 * @since 1.0.9.1
	 * @param mixed $settings Raw settings.
	 * @return array
	 */
	public function sanitize_telemetry_settings( $settings ) {
		$current_settings = $this->get_telemetry_settings();
		$settings         = is_array( $settings ) ? $settings : array();

		$current_settings['enabled'] = ! empty( $settings['enabled'] );

		if ( empty( $current_settings['site_id'] ) ) {
			$current_settings['site_id'] = wp_generate_uuid4();
		}

		return $current_settings;
	}

	/**
	 * Get the persisted telemetry settings merged with defaults.
	 *
	 * @since 1.0.9.1
	 * @return array
	 */
	private function get_telemetry_settings() {
		$settings = get_option( 'rank_math_api_telemetry_settings', array() );
		$settings = is_array( $settings ) ? $settings : array();

		return wp_parse_args( $settings, $this->get_default_telemetry_settings() );
	}

	/**
	 * Persist telemetry settings.
	 *
	 * @since 1.0.9.1
	 * @param array $settings Settings to save.
	 */
	private function update_telemetry_settings( array $settings ) {
		update_option( 'rank_math_api_telemetry_settings', $settings, false );
	}

	/**
	 * Ensure the anonymous telemetry site ID exists.
	 *
	 * @since 1.0.9.1
	 * @return string
	 */
	private function ensure_telemetry_site_id() {
		$settings = $this->get_telemetry_settings();

		if ( empty( $settings['site_id'] ) ) {
			$settings['site_id'] = wp_generate_uuid4();
			$this->update_telemetry_settings( $settings );
		}

		return $settings['site_id'];
	}

	/**
	 * Schedule the recurring telemetry heartbeat.
	 *
	 * @since 1.0.9.1
	 */
	private function schedule_telemetry_heartbeat() {
		if ( ! wp_next_scheduled( 'rank_math_api_telemetry_heartbeat' ) ) {
			wp_schedule_event( time() + HOUR_IN_SECONDS, 'daily', 'rank_math_api_telemetry_heartbeat' );
		}
	}

	/**
	 * Get the current notice event queue.
	 *
	 * @since 1.0.9.1
	 * @return array
	 */
	private function get_notice_events() {
		$events = get_option( 'rank_math_api_notice_events', array() );
		return is_array( $events ) ? $events : array();
	}

	/**
	 * Queue a transient admin notice event.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 */
	public function queue_notice_event( $notice_id ) {
		$notice_id = sanitize_key( $notice_id );

		if ( '' === $notice_id ) {
			return;
		}

		$events               = $this->get_notice_events();
		$events[ $notice_id ] = time();
		update_option( 'rank_math_api_notice_events', $events, false );
	}

	/**
	 * Check whether a transient notice event is queued.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 * @return bool
	 */
	private function has_notice_event( $notice_id ) {
		$events = $this->get_notice_events();
		return isset( $events[ $notice_id ] );
	}

	/**
	 * Consume a transient notice event after it has been displayed.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 */
	private function consume_notice_event( $notice_id ) {
		$events = $this->get_notice_events();

		if ( isset( $events[ $notice_id ] ) ) {
			unset( $events[ $notice_id ] );
			update_option( 'rank_math_api_notice_events', $events, false );
		}
	}

	/**
	 * Get site-wide dismissed notices.
	 *
	 * @since 1.0.9.1
	 * @return array
	 */
	private function get_site_dismissed_notices() {
		$dismissed_notices = get_option( 'rank_math_api_dismissed_notices', array() );
		return is_array( $dismissed_notices ) ? $dismissed_notices : array();
	}

	/**
	 * Mark a site-wide notice as dismissed.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 */
	private function dismiss_notice_for_site( $notice_id ) {
		$dismissed_notices               = $this->get_site_dismissed_notices();
		$dismissed_notices[ $notice_id ] = RANK_MATH_API_VERSION;
		update_option( 'rank_math_api_dismissed_notices', $dismissed_notices, false );
	}

	/**
	 * Check whether a site-wide notice has been dismissed.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 * @return bool
	 */
	private function is_notice_dismissed_for_site( $notice_id ) {
		$dismissed_notices = $this->get_site_dismissed_notices();
		return isset( $dismissed_notices[ $notice_id ] );
	}

	/**
	 * Get the user-meta key used for notice dismissals.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 * @return string
	 */
	private function get_user_notice_meta_key( $notice_id ) {
		return 'rank_math_api_dismissed_' . sanitize_key( $notice_id );
	}

	/**
	 * Mark a notice as dismissed for the current user.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 */
	private function dismiss_notice_for_user( $notice_id ) {
		$user_id = get_current_user_id();

		if ( $user_id ) {
			update_user_meta( $user_id, $this->get_user_notice_meta_key( $notice_id ), RANK_MATH_API_VERSION );
		}
	}

	/**
	 * Check whether the current user has dismissed a notice.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_id Notice identifier.
	 * @return bool
	 */
	private function is_notice_dismissed_for_user( $notice_id ) {
		$user_id = get_current_user_id();

		if ( ! $user_id ) {
			return false;
		}

		return '' !== (string) get_user_meta( $user_id, $this->get_user_notice_meta_key( $notice_id ), true );
	}

	/**
	 * Build a URL for a protected notice action.
	 *
	 * @since 1.0.9.1
	 * @param string $notice_action Action identifier.
	 * @param string $notice_id     Notice identifier.
	 * @return string
	 */
	private function get_notice_action_url( $notice_action, $notice_id ) {
		$url = add_query_arg(
			array(
				'rank_math_api_notice_action' => sanitize_key( $notice_action ),
				'rank_math_api_notice_id'     => sanitize_key( $notice_id ),
			),
			admin_url( 'plugins.php' )
		);

		return wp_nonce_url( $url, 'rank_math_api_notice_action', 'rank_math_api_notice_nonce' );
	}

	/**
	 * Handle notice actions coming from WordPress admin links.
	 * Redirects only when a known action was handled to avoid redirecting on invalid params.
	 *
	 * @since 1.0.9.1
	 */
	public function handle_notice_actions() {
		if ( ! is_admin() || ! current_user_can( 'manage_options' ) ) {
			return;
		}

		$notice_action = isset( $_GET['rank_math_api_notice_action'] ) ? sanitize_key( wp_unslash( $_GET['rank_math_api_notice_action'] ) ) : '';
		$notice_id     = isset( $_GET['rank_math_api_notice_id'] ) ? sanitize_key( wp_unslash( $_GET['rank_math_api_notice_id'] ) ) : '';
		$nonce         = isset( $_GET['rank_math_api_notice_nonce'] ) ? sanitize_text_field( wp_unslash( $_GET['rank_math_api_notice_nonce'] ) ) : '';

		if ( '' === $notice_action || '' === $notice_id || ! wp_verify_nonce( $nonce, 'rank_math_api_notice_action' ) ) {
			return;
		}

		$handled = false;

		switch ( $notice_action ) {
			case 'dismiss':
				$dismissible_notice_ids = array( 'folder_name_notice', 'telemetry_privacy_notice' );
				if ( ! in_array( $notice_id, $dismissible_notice_ids, true ) ) {
					break;
				}
				if ( 'folder_name_notice' === $notice_id ) {
					$this->dismiss_notice_for_user( $notice_id );
				} else {
					$this->dismiss_notice_for_site( $notice_id );
				}
				$handled = true;
				break;

			case 'telemetry_opt_out':
				$settings            = $this->get_telemetry_settings();
				$settings['enabled'] = false;
				$this->update_telemetry_settings( $settings );
				$this->dismiss_notice_for_site( 'telemetry_privacy_notice' );
				$this->queue_notice_event( 'telemetry_disabled' );
				$handled = true;
				break;

			case 'telemetry_keep_enabled':
				$this->dismiss_notice_for_site( 'telemetry_privacy_notice' );
				$this->queue_notice_event( 'telemetry_enabled' );
				$handled = true;
				break;
		}

		if ( ! $handled ) {
			return;
		}

		wp_safe_redirect(
			remove_query_arg(
				array(
					'rank_math_api_notice_action',
					'rank_math_api_notice_id',
					'rank_math_api_notice_nonce',
				),
				wp_get_referer() ? wp_get_referer() : admin_url( 'plugins.php' )
			)
		);
		exit;
	}

	/**
	 * Determine whether the current screen should render a notice.
	 *
	 * @since 1.0.9.1
	 * @param array $notice Notice definition.
	 * @return bool
	 */
	private function should_render_notice_on_current_screen( array $notice ) {
		if ( empty( $notice['screen_ids'] ) ) {
			return true;
		}

		if ( ! function_exists( 'get_current_screen' ) ) {
			return true;
		}

		$screen = get_current_screen();

		if ( ! $screen || empty( $screen->id ) ) {
			return true;
		}

		return in_array( $screen->id, $notice['screen_ids'], true );
	}

	/**
	 * Build the active admin notices for the current request.
	 *
	 * @since 1.0.9.1
	 * @return array
	 */
	private function get_active_admin_notices() {
		$notices            = array();
		$telemetry_settings = $this->get_telemetry_settings();

		if ( ! $this->are_dependencies_met() ) {
			$notices[] = array(
				'id'         => 'dependency_issues',
				'type'       => 'error',
				'message'    => $this->get_dependency_notice_markup(),
				'screen_ids' => array(),
			);
		}

		if ( $this->has_notice_event( 'dependency_restored' ) ) {
			$notices[] = array(
				'id'         => 'dependency_restored',
				'type'       => 'success',
				'message'    => '<p><strong>' . esc_html__( 'Rank Math API Manager', 'rank-math-api-manager' ) . '</strong>: ' . esc_html__( 'Dependencies are now met and plugin functionality is enabled again.', 'rank-math-api-manager' ) . '</p>',
				'screen_ids' => array( 'plugins', 'dashboard' ),
				'consume'    => true,
			);
		}

		if ( $this->has_notice_event( 'dependency_deactivated' ) ) {
			$notices[] = array(
				'id'         => 'dependency_deactivated',
				'type'       => 'warning',
				'message'    => '<p><strong>' . esc_html__( 'Rank Math API Manager', 'rank-math-api-manager' ) . '</strong>: ' . esc_html__( 'A required dependency has been deactivated. Rank Math API Manager functionality is currently disabled.', 'rank-math-api-manager' ) . '</p>',
				'screen_ids' => array( 'plugins', 'dashboard' ),
				'consume'    => true,
			);
		}

		if ( $this->has_notice_event( 'telemetry_enabled' ) ) {
			$notices[] = array(
				'id'         => 'telemetry_enabled',
				'type'       => 'success',
				'message'    => '<p><strong>' . esc_html__( 'Rank Math API Manager', 'rank-math-api-manager' ) . '</strong>: ' . esc_html__( 'Anonymous telemetry remains enabled. Only the documented minimal payload is sent to Devora Update API.', 'rank-math-api-manager' ) . '</p>',
				'screen_ids' => array( 'plugins', 'dashboard' ),
				'consume'    => true,
			);
		}

		if ( $this->has_notice_event( 'telemetry_disabled' ) ) {
			$notices[] = array(
				'id'         => 'telemetry_disabled',
				'type'       => 'success',
				'message'    => '<p><strong>' . esc_html__( 'Rank Math API Manager', 'rank-math-api-manager' ) . '</strong>: ' . esc_html__( 'Anonymous telemetry has been disabled for this site.', 'rank-math-api-manager' ) . '</p>',
				'screen_ids' => array( 'plugins', 'dashboard' ),
				'consume'    => true,
			);
		}

		if ( ! $this->is_standard_plugin_directory() && ! $this->is_notice_dismissed_for_user( 'folder_name_notice' ) ) {
			$notices[] = array(
				'id'         => 'folder_name_notice',
				'type'       => 'warning',
				'message'    => $this->get_folder_name_notice_markup(),
				'screen_ids' => array( 'plugins', 'dashboard' ),
				'actions'    => array(
					array(
						'label' => __( 'Dismiss', 'rank-math-api-manager' ),
						'url'   => $this->get_notice_action_url( 'dismiss', 'folder_name_notice' ),
						'class' => 'button button-secondary',
					),
				),
			);
		}

		if ( ! $this->is_notice_dismissed_for_site( 'telemetry_privacy_notice' ) && ! empty( $telemetry_settings['enabled'] ) ) {
			$notices[] = array(
				'id'         => 'telemetry_privacy_notice',
				'type'       => 'info',
				'message'    => $this->get_telemetry_notice_markup(),
				'screen_ids' => array( 'plugins', 'dashboard' ),
				'actions'    => array(
					array(
						'label' => __( 'Keep enabled', 'rank-math-api-manager' ),
						'url'   => $this->get_notice_action_url( 'telemetry_keep_enabled', 'telemetry_privacy_notice' ),
						'class' => 'button button-primary',
					),
					array(
						'label' => __( 'Disable anonymous telemetry', 'rank-math-api-manager' ),
						'url'   => $this->get_notice_action_url( 'telemetry_opt_out', 'telemetry_privacy_notice' ),
						'class' => 'button button-secondary',
					),
				),
			);
		}

		return $notices;
	}

	/**
	 * Render active admin notices through a shared renderer.
	 *
	 * @since 1.0.9.1
	 */
	public function render_admin_notices() {
		if ( ! is_admin() || ! current_user_can( 'manage_options' ) ) {
			return;
		}

		foreach ( $this->get_active_admin_notices() as $notice ) {
			if ( ! $this->should_render_notice_on_current_screen( $notice ) ) {
				continue;
			}

			$this->render_admin_notice( $notice );

			if ( ! empty( $notice['consume'] ) ) {
				$this->consume_notice_event( $notice['id'] );
			}
		}
	}

	/**
	 * Render a single admin notice.
	 *
	 * @since 1.0.9.1
	 * @param array $notice Notice definition.
	 */
	private function render_admin_notice( array $notice ) {
		$classes = array(
			'notice',
			'notice-' . ( isset( $notice['type'] ) ? sanitize_html_class( $notice['type'] ) : 'info' ),
			'rank-math-api-notice',
		);

		echo '<div class="' . esc_attr( implode( ' ', $classes ) ) . '">';
		// Allow details/summary for expandable content (e.g. folder reinstall steps); WP 5.0 post list does not include them.
		$allowed = wp_kses_allowed_html( 'post' );
		$allowed['details'] = array( 'class' => true );
		$allowed['summary'] = array();
		$allowed['div']     = array_merge( isset( $allowed['div'] ) ? $allowed['div'] : array(), array( 'class' => true ) );
		echo wp_kses( $notice['message'], $allowed );

		if ( ! empty( $notice['actions'] ) && is_array( $notice['actions'] ) ) {
			echo '<p class="rank-math-api-notice-actions">';

			foreach ( $notice['actions'] as $action ) {
				$label = isset( $action['label'] ) ? $action['label'] : '';
				$url   = isset( $action['url'] ) ? $action['url'] : '';
				$class = isset( $action['class'] ) ? $action['class'] : 'button button-secondary';

				echo '<a class="' . esc_attr( $class ) . '" href="' . esc_url( $url ) . '">' . esc_html( $label ) . '</a> ';
			}

			echo '</p>';
		}

		echo '</div>';
	}

	/**
	 * Build the dependency notice markup.
	 *
	 * @since 1.0.9.1
	 * @return string
	 */
	private function get_dependency_notice_markup() {
		$status = $this->get_dependency_status();

		ob_start();
		?>
		<p><strong><?php echo esc_html__( 'Rank Math API Manager - Dependency Issues', 'rank-math-api-manager' ); ?></strong></p>
		<?php if ( ! empty( $status['missing_plugins'] ) ) : ?>
			<p><?php echo esc_html__( 'The following required plugins are missing or inactive:', 'rank-math-api-manager' ); ?></p>
			<ul>
				<?php foreach ( $status['missing_plugins'] as $plugin ) : ?>
					<li>
						<strong><?php echo esc_html( $plugin['name'] ); ?></strong> - <?php echo esc_html( $plugin['description'] ); ?>
						<?php if ( $this->is_plugin_installed( $plugin['file'] ) ) : ?>
							<a href="<?php echo esc_url( admin_url( 'plugins.php' ) ); ?>"><?php echo esc_html__( 'Activate Plugin', 'rank-math-api-manager' ); ?></a>
						<?php else : ?>
							<a href="<?php echo esc_url( $plugin['url'] ); ?>" target="_blank" rel="noreferrer noopener"><?php echo esc_html__( 'Install Plugin', 'rank-math-api-manager' ); ?></a>
						<?php endif; ?>
					</li>
				<?php endforeach; ?>
			</ul>
		<?php endif; ?>
		<?php if ( ! empty( $status['configuration_issues'] ) ) : ?>
			<p><?php echo esc_html__( 'Configuration issues detected:', 'rank-math-api-manager' ); ?></p>
			<ul>
				<?php foreach ( $status['configuration_issues'] as $issue ) : ?>
					<li>
						<strong><?php echo esc_html( $issue['plugin'] ); ?></strong>: <?php echo esc_html( $issue['issue'] ); ?>
						<?php if ( isset( $issue['debug'] ) && is_array( $issue['debug'] ) ) : ?>
							<br>
							<small>
								<strong><?php echo esc_html__( 'Debug Info', 'rank-math-api-manager' ); ?>:</strong>
								<?php
								$debug_parts = array();

								foreach ( $issue['debug'] as $key => $value ) {
									$debug_parts[] = $key . ': ' . ( is_bool( $value ) ? ( $value ? 'Yes' : 'No' ) : $value );
								}

								echo esc_html( implode( ', ', $debug_parts ) );
								?>
							</small>
						<?php endif; ?>
					</li>
				<?php endforeach; ?>
			</ul>
		<?php endif; ?>
		<?php if ( ! empty( $status['recommendations'] ) ) : ?>
			<p><strong><?php echo esc_html__( 'Recommendations:', 'rank-math-api-manager' ); ?></strong></p>
			<ul>
				<?php foreach ( $status['recommendations'] as $recommendation ) : ?>
					<li><?php echo esc_html( $recommendation ); ?></li>
				<?php endforeach; ?>
			</ul>
		<?php endif; ?>
		<p><?php echo esc_html__( 'Rank Math API Manager functionality is currently disabled until all dependencies are met.', 'rank-math-api-manager' ); ?></p>
		<?php

		return (string) ob_get_clean();
	}

	/**
	 * Build the non-standard plugin folder notice markup.
	 * Uses <details>/<summary> so steps are hidden by default and expand in place (no JS).
	 *
	 * @since 1.0.9.1
	 * @return string
	 */
	private function get_folder_name_notice_markup() {
		$current_directory = $this->get_plugin_directory_slug();
		$releases_url      = 'https://github.com/Devora-AS/rank-math-api-manager/releases';

		$summary   = esc_html__( 'Show reinstall steps', 'rank-math-api-manager' );
		$step1     = esc_html__( 'Deactivate the plugin.', 'rank-math-api-manager' );
		$step2     = esc_html__( 'Delete it (Plugins → Deactivate → Delete).', 'rank-math-api-manager' );
		$step3     = sprintf(
			/* translators: %s: link to GitHub Releases */
			esc_html__( 'Download the latest rank-math-api-manager.zip from %s.', 'rank-math-api-manager' ),
			'<a href="' . esc_url( $releases_url ) . '" target="_blank" rel="noreferrer noopener">' . esc_html__( 'GitHub Releases', 'rank-math-api-manager' ) . '</a>'
		);
		$step4     = esc_html__( 'Plugins → Add New → Upload Plugin → choose the ZIP → Install Now → Activate.', 'rank-math-api-manager' );
		// Escape translatable parts so translations cannot inject HTML (translation safety).
		$after     = esc_html( __( 'The plugin will then be in wp-content/plugins/', 'rank-math-api-manager' ) )
			. '<code>rank-math-api-manager</code>'
			. esc_html( __( '/.', 'rank-math-api-manager' ) );

		$intro = sprintf(
			'<p><strong>%1$s</strong>: %2$s %3$s <code>%4$s</code>. %5$s <code>rank-math-api-manager</code>.</p>',
			esc_html__( 'Rank Math API Manager', 'rank-math-api-manager' ),
			esc_html__( 'This site is running the plugin from a legacy folder name.', 'rank-math-api-manager' ),
			esc_html__( 'Current folder:', 'rank-math-api-manager' ),
			esc_html( $current_directory ),
			esc_html__( 'New releases use the folder', 'rank-math-api-manager' )
		);

		$steps = sprintf(
			'<ol class="rank-math-api-reinstall-steps"><li>%1$s</li><li>%2$s</li><li>%3$s</li><li>%4$s</li></ol><p>%5$s</p>',
			$step1,
			$step2,
			$step3,
			$step4,
			$after
		);

		return $intro
			. '<details class="rank-math-api-notice-details">'
			. '<summary>' . $summary . '</summary>'
			. '<div class="rank-math-api-notice-details-content">' . $steps . '</div>'
			. '</details>';
	}

	/**
	 * Build the telemetry privacy notice markup.
	 *
	 * @since 1.0.9.1
	 * @return string
	 */
	private function get_telemetry_notice_markup() {
		$privacy_doc = 'https://github.com/devora-as/rank-math-api-manager/blob/main/docs/telemetry-and-privacy.md';

		return sprintf(
			'<p><strong>%1$s</strong>: %2$s</p><p>%3$s</p><p>%4$s <a href="%5$s" target="_blank" rel="noreferrer noopener">%6$s</a>.</p>',
			esc_html__( 'Rank Math API Manager', 'rank-math-api-manager' ),
			esc_html__( 'Anonymous telemetry is enabled to help Devora validate update health and compatibility.', 'rank-math-api-manager' ),
			esc_html__( 'The plugin sends only the plugin slug, plugin version, WordPress version, PHP version, event type, timestamp, and an anonymous site ID. No site URL, email addresses, usernames, SEO content, or authentication data is sent.', 'rank-math-api-manager' ),
			esc_html__( 'You can keep it enabled or disable it for this site at any time. See the full privacy note in', 'rank-math-api-manager' ),
			esc_url( $privacy_doc ),
			esc_html__( 'Telemetry and Privacy', 'rank-math-api-manager' )
		);
	}

	/**
	 * Check if a plugin is installed (but not necessarily active)
	 *
	 * @since 1.0.7
	 * @param string $plugin_file Plugin file path
	 * @return bool True if plugin is installed
	 */
	private function is_plugin_installed( $plugin_file ) {
		$plugins = get_plugins();
		return isset( $plugins[ $plugin_file ] );
	}

	/**
	 * Check if Rank Math is properly configured
	 *
	 * @since 1.0.7
	 * @return bool True if Rank Math is configured
	 */
	private function is_rank_math_configured() {
		// Basic check: if Rank Math class exists and function is available, consider it configured
		// This is more lenient and should work for most Rank Math installations
		if ( class_exists( 'RankMath' ) && function_exists( 'rank_math' ) ) {
			return true;
		}
		
		// Fallback: check if Rank Math meta fields are registered
		// This indicates Rank Math has been initialized
		global $wp_meta_keys;
		if ( isset( $wp_meta_keys ) && is_array( $wp_meta_keys ) ) {
			foreach ( $wp_meta_keys as $post_type => $meta_keys ) {
				if ( isset( $meta_keys['rank_math_title'] ) || isset( $meta_keys['rank_math_description'] ) ) {
					return true;
				}
			}
		}
		
		return false;
	}

	/**
	 * Get detailed dependency status
	 *
	 * @since 1.0.7
	 * @return array Array with dependency status details
	 */
	public function get_dependency_status() {
		$status = array(
			'dependencies_met' => false,
			'missing_plugins' => array(),
			'configuration_issues' => array(),
			'recommendations' => array(),
			'debug_info' => array()
		);
		
		$dependencies = $this->get_required_plugins();
		
		foreach ( $dependencies as $plugin ) {
			if ( ! $this->is_plugin_active( $plugin['file'] ) ) {
				$status['missing_plugins'][] = $plugin;
			}
		}
		
		// Check Rank Math configuration with detailed debugging
		if ( $this->is_plugin_active( 'seo-by-rank-math/rank-math.php' ) ) {
			$rank_math_debug = $this->get_rank_math_debug_info();
			$status['debug_info']['rank_math'] = $rank_math_debug;
			
			if ( ! $this->is_rank_math_configured() ) {
				$status['configuration_issues'][] = array(
					'plugin' => 'Rank Math SEO',
					'issue' => 'Plugin is active but not properly configured',
					'debug' => $rank_math_debug
				);
			}
		}
		
		$status['dependencies_met'] = empty( $status['missing_plugins'] ) && empty( $status['configuration_issues'] );
		
		// Add recommendations
		if ( ! empty( $status['missing_plugins'] ) ) {
			$status['recommendations'][] = 'Install and activate all required plugins';
		}
		
		if ( ! empty( $status['configuration_issues'] ) ) {
			$status['recommendations'][] = 'Configure Rank Math SEO plugin properly';
		}
		
		return $status;
	}

	/**
	 * Get detailed debug information about Rank Math
	 *
	 * @since 1.0.7
	 * @return array Debug information
	 */
	private function get_rank_math_debug_info() {
		$debug = array();
		
		// Check if RankMath class exists
		$debug['class_exists'] = class_exists( 'RankMath' );
		
		// Check if rank_math function exists
		$debug['function_exists'] = function_exists( 'rank_math' );
		
		// Try to get Rank Math instance
		if ( $debug['function_exists'] ) {
			try {
				$rank_math = rank_math();
				$debug['instance_created'] = is_object( $rank_math );
				$debug['instance_type'] = get_class( $rank_math );
				
				if ( is_object( $rank_math ) ) {
					$debug['has_get_settings'] = method_exists( $rank_math, 'get_settings' );
					$debug['has_get_helper'] = method_exists( $rank_math, 'get_helper' );
					$debug['has_get_admin'] = method_exists( $rank_math, 'get_admin' );
				}
			} catch ( Throwable $e ) {
				$debug['exception'] = $e->getMessage();
			}
		}
		
		// Check if Rank Math is in the global scope
		global $rank_math;
		$debug['global_exists'] = isset( $rank_math );
		
		return $debug;
	}

	/**
	 * Handle plugin activation
	 *
	 * @since 1.0.7
	 * @param string $plugin_file Activated plugin file
	 */
	public function on_plugin_activated( $plugin_file ) {
		// Check if the activated plugin is one of our dependencies
		$dependencies = $this->get_required_plugins();
		$is_dependency = false;
		
		foreach ( $dependencies as $dependency ) {
			if ( $dependency['file'] === $plugin_file ) {
				$is_dependency = true;
				break;
			}
		}
		
		if ( $is_dependency ) {
			// Re-check dependencies after a short delay
			add_action( 'admin_init', function() {
				$this->check_dependencies();
			});

			$this->queue_notice_event( 'dependency_restored' );
		}
	}

	/**
	 * Handle plugin deactivation
	 *
	 * @since 1.0.7
	 * @param string $plugin_file Deactivated plugin file
	 */
	public function on_plugin_deactivated( $plugin_file ) {
		// Check if the deactivated plugin is one of our dependencies
		$dependencies = $this->get_required_plugins();
		$is_dependency = false;
		
		foreach ( $dependencies as $dependency ) {
			if ( $dependency['file'] === $plugin_file ) {
				$is_dependency = true;
				break;
			}
		}
		
		if ( $is_dependency ) {
			// Re-check dependencies
			$this->check_dependencies();

			$this->queue_notice_event( 'dependency_deactivated' );
		}
	}

	/**
	 * Enqueue admin scripts and styles
	 */
	public function enqueue_admin_scripts($hook) {
		$allowed_hooks = array( 'plugins.php', 'index.php' );

		if ( false === strpos( $hook, 'rank-math-api' ) && ! in_array( $hook, $allowed_hooks, true ) ) {
			return;
		}

		wp_enqueue_script(
			'rank-math-api-admin',
			RANK_MATH_API_PLUGIN_URL . 'assets/js/admin.js',
			array('jquery'),
			RANK_MATH_API_VERSION,
			true
		);

		wp_enqueue_style(
			'rank-math-api-admin',
			RANK_MATH_API_PLUGIN_URL . 'assets/css/admin.css',
			array(),
			RANK_MATH_API_VERSION
		);
	}

	/**
	 * Prepare plugin activation state for telemetry and notice handling.
	 *
	 * @since 1.0.9.1
	 */
	public function prepare_plugin_activation() {
		$this->ensure_telemetry_site_id();
		$this->schedule_telemetry_heartbeat();
		$this->send_telemetry_event( 'activate' );
	}

	/**
	 * Handle telemetry and scheduling cleanup when the plugin is deactivated.
	 *
	 * @since 1.0.9.1
	 */
	public function handle_plugin_deactivation_cleanup() {
		$this->send_telemetry_event( 'deactivate' );
		wp_clear_scheduled_hook( 'rank_math_api_telemetry_heartbeat' );
	}

	/**
	 * Send the scheduled telemetry heartbeat if telemetry is still enabled.
	 *
	 * @since 1.0.9.1
	 */
	public function send_scheduled_telemetry() {
		$last_run = (int) get_option( 'rank_math_api_heartbeat_last_run', 0 );

		if ( $last_run && ( time() - $last_run ) < ( DAY_IN_SECONDS / 2 ) ) {
			return;
		}

		if ( $this->send_telemetry_event( 'heartbeat' ) ) {
			update_option( 'rank_math_api_heartbeat_last_run', time(), false );
		}
	}

	/**
	 * Send a privacy-safe telemetry event.
	 *
	 * @since 1.0.9.1
	 * @param string $event_type Telemetry event type.
	 * @return bool
	 */
	public function send_telemetry_event( $event_type ) {
		$allowed_events = array( 'activate', 'deactivate', 'heartbeat' );

		if ( ! in_array( $event_type, $allowed_events, true ) ) {
			return false;
		}

		$settings = $this->get_telemetry_settings();

		if ( empty( $settings['enabled'] ) ) {
			return false;
		}

		$endpoint = $this->get_telemetry_endpoint();

		if ( ! $this->is_valid_devora_api_url( $endpoint, '/v1/telemetry' ) ) {
			return false;
		}

		$payload = array(
			'site_id'        => $this->ensure_telemetry_site_id(),
			'plugin_slug'    => 'rank-math-api-manager',
			'plugin_version' => RANK_MATH_API_VERSION,
			'wp_version'     => get_bloginfo( 'version' ),
			'php_version'    => PHP_VERSION,
			'event_type'     => $event_type,
			'timestamp'      => gmdate( 'c' ),
		);

		$response = wp_remote_post(
			$endpoint,
			array(
				'timeout'     => 5,
				'redirection' => 0,
				'blocking'    => false,
				'headers'     => array(
					'Content-Type' => 'application/json; charset=' . get_bloginfo( 'charset' ),
				),
				'body'        => wp_json_encode( $payload ),
			)
		);

		if ( is_wp_error( $response ) ) {
			$this->log_debug( 'Telemetry request failed for event: ' . $event_type );
			return false;
		}

		return true;
	}

	/**
	 * Get the fixed telemetry endpoint.
	 * If this return value is ever made filterable, callers must still validate the URL
	 * with is_valid_devora_api_url() before sending any request (SSRF prevention).
	 *
	 * @since 1.0.9.1
	 * @return string
	 */
	private function get_telemetry_endpoint() {
		return 'https://updates.devora.no/v1/telemetry';
	}

	/**
	 * Validate a Devora API URL before sending data to it.
	 *
	 * @since 1.0.9.1
	 * @param string $url           Candidate URL.
	 * @param string $expected_path Expected leading path.
	 * @return bool
	 */
	private function is_valid_devora_api_url( $url, $expected_path ) {
		$parts = wp_parse_url( $url );

		if ( empty( $parts['scheme'] ) || empty( $parts['host'] ) || empty( $parts['path'] ) ) {
			return false;
		}

		if ( 'https' !== strtolower( $parts['scheme'] ) || 'updates.devora.no' !== strtolower( $parts['host'] ) ) {
			return false;
		}

		return 0 === strpos( strtolower( $parts['path'] ), strtolower( $expected_path ) );
	}

	/**
	 * Register meta fields for REST API
	 */
	public function register_meta_fields() {
		foreach ( $this->get_allowed_post_types() as $post_type ) {
			foreach ( $this->get_supported_meta_fields() as $meta_key => $field_config ) {
				$args = array(
					'show_in_rest'       => true,
					'single'             => true,
					'type'               => 'string',
					'description'        => $field_config['description'],
					'auth_callback'      => array( $this, 'check_meta_auth_permission' ),
					'sanitize_callback'  => $field_config['sanitize_callback'],
				);

				register_post_meta( $post_type, $meta_key, $args );
			}
		}
	}

	/**
	 * Register REST API routes
	 */
	public function register_api_routes() {
		register_rest_route( 'rank-math-api/v1', '/update-meta', [
			'methods'             => 'POST',
			'callback'            => [ $this, 'update_rank_math_meta' ],
			'permission_callback' => [ $this, 'check_update_permission' ],
			'args'                => [
				'post_id' => [
					'type'              => 'integer',
					'required'          => true,
					'sanitize_callback' => 'absint',
					'validate_callback' => function ( $param ) {
						$post_id = absint( $param );
						return $this->is_supported_post_target( $post_id );
					}
				],
				'rank_math_title'         => [ 'type' => 'string', 'sanitize_callback' => [ $this, 'sanitize_rank_math_text_field' ] ],
				'rank_math_description'   => [ 'type' => 'string', 'sanitize_callback' => [ $this, 'sanitize_rank_math_text_field' ] ],
				'rank_math_canonical_url' => [ 'type' => 'string', 'sanitize_callback' => [ $this, 'sanitize_rank_math_canonical_url' ] ],
				'rank_math_focus_keyword' => [ 'type' => 'string', 'sanitize_callback' => [ $this, 'sanitize_rank_math_focus_keyword' ] ],
			],
		] );
	}

	/**
	 * Update Rank Math meta data
	 *
	 * @param WP_REST_Request $request Request object
	 * @return WP_REST_Response|WP_Error Response object
	 */
	public function update_rank_math_meta( WP_REST_Request $request ) {
		$post_id = absint( $request->get_param( 'post_id' ) );
		$fields  = $this->get_supported_meta_fields();

		$result = [];

		if ( ! $post_id || ! $this->is_supported_post_target( $post_id ) ) {
			return new WP_Error( 'invalid_post_id', 'A supported post or product ID is required', [ 'status' => 400 ] );
		}

		do_action( 'rank_math/pre_update_metadata', $post_id, get_post_type( $post_id ), get_post_field( 'post_content', $post_id ) );

		foreach ( $fields as $field => $field_config ) {
			$value = $request->get_param( $field );

			if ( $value !== null ) {
				$value = call_user_func( $field_config['sanitize_callback'], $value );
				$current_value = get_post_meta( $post_id, $field, true );

				if ( (string) $current_value === (string) $value ) {
					$result[ $field ] = 'unchanged';
					continue;
				}

				$update_result = update_post_meta( $post_id, $field, $value );
				$result[ $field ] = $update_result ? 'updated' : 'failed';
			}
		}

		if ( empty( $result ) ) {
			return new WP_Error( 'no_update', 'No metadata was updated', [ 'status' => 400 ] );
		}

		return new WP_REST_Response( $result, 200 );
	}

	/**
	 * Check update permission
	 *
	 * @param WP_REST_Request $request Request object.
	 * @return bool|WP_Error True if user can edit the requested post.
	 */
	public function check_update_permission( WP_REST_Request $request ) {
		$post_id = absint( $request->get_param( 'post_id' ) );

		if ( ! is_user_logged_in() ) {
			return new WP_Error(
				'rest_forbidden',
				__( 'Authentication required.', 'rank-math-api-manager' ),
				[ 'status' => 401 ]
			);
		}

		if ( ! $post_id ) {
			return new WP_Error(
				'invalid_post_id',
				__( 'A valid post ID is required.', 'rank-math-api-manager' ),
				[ 'status' => 400 ]
			);
		}

		if ( ! $this->is_supported_post_target( $post_id ) ) {
			return new WP_Error(
				'invalid_post_id',
				__( 'A supported post or product ID is required.', 'rank-math-api-manager' ),
				[ 'status' => 400 ]
			);
		}

		if ( ! current_user_can( 'edit_post', $post_id ) ) {
			return new WP_Error(
				'rest_forbidden',
				__( 'You cannot edit this post.', 'rank-math-api-manager' ),
				[ 'status' => 403 ]
			);
		}

		return true;
	}

	/**
	 * Check meta authorization for REST-exposed post meta.
	 *
	 * @since 1.0.8
	 * @param bool   $allowed   Current authorization state.
	 * @param string $meta_key  Meta key.
	 * @param int    $object_id Post ID.
	 * @param int    $user_id   User ID.
	 * @param string $cap       Requested capability.
	 * @param array  $caps      Primitive capabilities.
	 * @return bool
	 */
	public function check_meta_auth_permission( $allowed, $meta_key, $object_id, $user_id, $cap, $caps ) {
		unset( $allowed, $meta_key, $user_id, $cap, $caps );

		if ( ! $object_id || ! $this->is_supported_post_target( $object_id ) ) {
			return false;
		}

		return current_user_can( 'edit_post', $object_id );
	}

	/**
	 * Get plugin version
	 *
	 * @return string Plugin version
	 */
	public function get_version() {
		return RANK_MATH_API_VERSION;
	}

	/**
	 * Log debug messages
	 *
	 * @since 1.0.7
	 * @param string $message Debug message to log
	 */
	private function log_debug( $message ) {
		if ( defined( 'WP_DEBUG' ) && WP_DEBUG ) {
			// phpcs:ignore WordPress.PHP.DevelopmentFunctions.error_log_error_log -- Only runs when WP_DEBUG is enabled.
			error_log( 'Rank Math API Manager: ' . $message );
		}
	}

	/**
	 * Check for plugin updates from GitHub
	 *
	 * @since 1.0.7
	 * @param object $transient WordPress update transient
	 * @return object Modified transient
	 */
	public function check_for_update( $transient ) {
		$this->log_debug( 'check_for_update called' );
		
		// Ensure we have a valid transient object
		if ( ! is_object( $transient ) || empty( $transient->checked ) || ! is_array( $transient->checked ) ) {
			$this->log_debug( 'Transient checked is empty, returning early' );
			return $transient;
		}

		// Get plugin basename
		$plugin_slug = plugin_basename( RANK_MATH_API_PLUGIN_FILE );
		
		// Only check if our plugin is in the checked list
		if ( ! isset( $transient->checked[ $plugin_slug ] ) ) {
			$this->log_debug( 'Plugin not in checked list: ' . $plugin_slug );
			return $transient;
		}
		
		$this->log_debug( 'Plugin found in checked list, proceeding with update check' );

		// Get current version
		$current_version = isset( $this->plugin_data['Version'] ) ? $this->plugin_data['Version'] : RANK_MATH_API_VERSION;

		// Check for cached release data first
		$cache_key = 'rank_math_api_github_release';
		$release_data = get_transient( $cache_key );

		if ( false === $release_data ) {
			$this->log_debug( 'No cached release data, fetching from GitHub API' );
			// Get latest release from GitHub with rate limiting
			$release_data = $this->get_latest_github_release();
			
			if ( is_wp_error( $release_data ) ) {
				$this->log_debug( 'GitHub API error: ' . $release_data->get_error_message() );
				return $transient;
			}

			set_transient( $cache_key, $release_data, 3600 );
			$this->log_debug( 'Successfully fetched release data from GitHub' );
		}

		$this->log_debug( 'Using cached release data' );

		if ( ! $release_data || ! isset( $release_data['version'] ) ) {
			$this->log_debug( 'Invalid release data or missing version info' );
			return $transient;
		}

		$this->log_debug( 'Comparing versions: Current=' . $current_version . ', Remote=' . $release_data['version'] );

		// Compare versions
		if ( version_compare( $release_data['version'], $current_version, '>' ) ) {
			$this->log_debug( 'Update available! Adding to transient' );
			// Update available - add to response
			$plugin_data = (object) array(
				'slug'         => dirname( $plugin_slug ),
				'plugin'       => $plugin_slug,
				'new_version'  => $release_data['version'],
				'url'          => isset( $this->plugin_data['PluginURI'] ) ? $this->plugin_data['PluginURI'] : '',
				'package'      => $release_data['download_url'],
				'icons'        => array(),
				'banners'      => array(),
				'banners_rtl'  => array(),
				'tested'       => '6.9.3',
				'requires_php' => '7.4',
			);

			$transient->response[ $plugin_slug ] = $plugin_data;
			$this->log_debug( 'Successfully added update to WordPress transient' );
		} else {
			$this->log_debug( 'No update needed - version is current' );
		}

		return $transient;
	}

	/**
	 * Get latest release information from GitHub
	 *
	 * @since 1.0.7
	 * @return array|WP_Error Release data or error
	 */
	private function get_latest_github_release() {
		$this->log_debug( 'Starting GitHub API request' );
		
		// Rate limiting check
		$last_check = get_option( 'rank_math_api_last_github_check', 0 );
		$check_interval = 300; // 5 minutes minimum between checks

		if ( time() - $last_check < $check_interval ) {
			$this->log_debug( 'Rate limited - too many recent requests' );
			return new WP_Error( 'rate_limited', 'Rate limited: too many requests' );
		}

		// Prepare headers with optional authentication
		$headers = array(
			'Accept'     => 'application/vnd.github.v3+json',
			'User-Agent' => 'WordPress/' . get_bloginfo( 'version' ) . '; ' . get_bloginfo( 'url' )
		);

		// Add authentication header if token is available
		if ( $this->github_token ) {
			$headers['Authorization'] = 'token ' . $this->github_token;
			$this->log_debug( 'Using authenticated GitHub API request (5000/hour limit)' );
		} else {
			$this->log_debug( 'Using unauthenticated GitHub API request (60/hour limit)' );
		}

		// Make API request
		$response = wp_remote_get( $this->github_repo['api_url'], array(
			'timeout' => 15,
			'headers' => $headers
		) );

		// Update last check time
		update_option( 'rank_math_api_last_github_check', time() );

		if ( is_wp_error( $response ) ) {
			$this->log_debug( 'GitHub API request failed: ' . $response->get_error_message() );
			return new WP_Error( 'api_error', 'GitHub API request failed: ' . $response->get_error_message() );
		}

		$response_code = wp_remote_retrieve_response_code( $response );
		$this->log_debug( 'GitHub API response code: ' . $response_code );
		
		if ( 200 !== $response_code ) {
			$this->log_debug( 'GitHub API error - status: ' . $response_code );
			return new WP_Error( 'api_error', 'GitHub API returned status: ' . $response_code );
		}

		$body = wp_remote_retrieve_body( $response );
		$data = json_decode( $body, true );

		if ( ! $data || ! isset( $data['tag_name'] ) ) {
			$this->log_debug( 'Invalid GitHub API response - no tag_name found' );
			return new WP_Error( 'invalid_response', 'Invalid GitHub API response' );
		}

		// Parse version from tag (remove 'v' prefix if present)
		$version = ltrim( $data['tag_name'], 'v' );
		$this->log_debug( 'Found GitHub release version: ' . $version );

		// Look for the expected release ZIP asset only.
		$download_url = null;
		$assets_count = isset( $data['assets'] ) ? count( $data['assets'] ) : 0;
		$this->log_debug( 'Release has ' . $assets_count . ' assets' );
		
		if ( isset( $data['assets'] ) && is_array( $data['assets'] ) ) {
			foreach ( $data['assets'] as $asset ) {
				if ( empty( $asset['name'] ) || empty( $asset['browser_download_url'] ) ) {
					continue;
				}

				$this->log_debug( 'Found asset: ' . $asset['name'] );
				if ( 'rank-math-api-manager.zip' === $asset['name'] && $this->is_valid_release_download_url( $asset['browser_download_url'] ) ) {
					$download_url = $asset['browser_download_url'];
					$this->log_debug( 'Using custom ZIP asset: ' . $download_url );
					break;
				}
			}
		}

		if ( ! $download_url ) {
			$this->log_debug( 'ERROR: No valid release ZIP asset found' );
			return new WP_Error( 'no_download', 'No valid release ZIP asset found in release' );
		}

		return array(
			'version'      => $version,
			'url'          => $data['html_url'],
			'download_url' => $download_url,
			'published_at' => $data['published_at'],
			'description'  => isset( $data['body'] ) ? $data['body'] : '',
		);
	}

	/**
	 * Provide plugin information for the "View Details" modal
	 *
	 * @since 1.0.7
	 * @param object $res    Plugin information result
	 * @param string $action Action being performed
	 * @param object $args   Additional arguments
	 * @return object|false Modified result or false
	 */
	public function plugin_info( $res, $action, $args ) {
		$slug = ( is_object( $args ) && isset( $args->slug ) ) ? $args->slug : '';

		// Only handle plugin_information requests for our plugin
		if ( 'plugin_information' !== $action || 'rank-math-api-manager' !== $slug ) {
			return false;
		}

		// Get cached release data
		$cache_key = 'rank_math_api_github_release';
		$release_data = get_transient( $cache_key );

		if ( false === $release_data ) {
			$release_data = $this->get_latest_github_release();
			
			if ( is_wp_error( $release_data ) ) {
				return false;
			}

			set_transient( $cache_key, $release_data, 3600 );
		}

		if ( ! $release_data ) {
			return false;
		}

		// Format changelog
		$changelog = '';
		if ( ! empty( $release_data['description'] ) ) {
			$changelog = wp_kses_post( nl2br( $release_data['description'] ) );
		}

		// Return plugin information object
		return (object) array(
			'name'           => isset( $this->plugin_data['Name'] ) ? $this->plugin_data['Name'] : 'Rank Math API Manager',
			'slug'           => 'rank-math-api-manager',
			'version'        => $release_data['version'],
			'author'         => '<a href="' . esc_url( isset( $this->plugin_data['AuthorURI'] ) ? $this->plugin_data['AuthorURI'] : '' ) . '">' . esc_html( isset( $this->plugin_data['AuthorName'] ) ? $this->plugin_data['AuthorName'] : 'Devora AS' ) . '</a>',
			'homepage'       => isset( $this->plugin_data['PluginURI'] ) ? $this->plugin_data['PluginURI'] : '',
			'requires'       => '5.0',
			'tested'         => '6.9.3',
			'requires_php'   => '7.4',
			'last_updated'   => $release_data['published_at'],
			'download_link'  => $release_data['download_url'],
			'sections'       => array(
				'description' => '<p>' . esc_html( isset( $this->plugin_data['Description'] ) ? $this->plugin_data['Description'] : '' ) . '</p>',
				'changelog'   => $changelog,
			),
		);
	}

	/**
	 * Validate a GitHub release download URL before exposing it to WordPress.
	 *
	 * @since 1.0.8
	 * @param string $download_url Candidate download URL.
	 * @return bool
	 */
	private function is_valid_release_download_url( $download_url ) {
		$parts = wp_parse_url( $download_url );

		if ( empty( $parts['scheme'] ) || empty( $parts['host'] ) || empty( $parts['path'] ) ) {
			return false;
		}

		if ( 'https' !== strtolower( $parts['scheme'] ) || 'github.com' !== strtolower( $parts['host'] ) ) {
			return false;
		}

		$expected_path = strtolower( '/' . $this->github_repo['owner'] . '/' . $this->github_repo['repo'] . '/releases/download/' );
		$actual_path   = strtolower( $parts['path'] );

		return 0 === strpos( $actual_path, $expected_path );
	}
}

// Initialize the plugin
function rank_math_api_manager_init() {
	return Rank_Math_API_Manager_Extended::get_instance();
}

// Start the plugin
add_action('plugins_loaded', 'rank_math_api_manager_init');

/**
 * Plugin activation function
 * 
 * Sets up necessary directories and options when the plugin is activated
 * 
 * @since 1.0.0
 */
function rank_math_api_manager_activate() {
	// Create necessary directories
	$upload_dir = wp_upload_dir();
	$plugin_dir = $upload_dir['basedir'] . '/rank-math-api-manager';
	
	if (!file_exists($plugin_dir)) {
		wp_mkdir_p($plugin_dir);
	}
	
	// Add activation timestamp
	update_option('rank_math_api_activated', current_time('mysql'));
	
	// Check dependencies on activation
	$plugin_instance = Rank_Math_API_Manager_Extended::get_instance();
	if ( method_exists( $plugin_instance, 'check_dependencies' ) ) {
		$plugin_instance->check_dependencies();
	}

	if ( method_exists( $plugin_instance, 'prepare_plugin_activation' ) ) {
		$plugin_instance->prepare_plugin_activation();
	}
}

/**
 * Plugin deactivation function
 * 
 * Cleans up scheduled events and caches when the plugin is deactivated
 * 
 * @since 1.0.0
 */
function rank_math_api_manager_deactivate() {
	$plugin_instance = Rank_Math_API_Manager_Extended::get_instance();

	if ( method_exists( $plugin_instance, 'handle_plugin_deactivation_cleanup' ) ) {
		$plugin_instance->handle_plugin_deactivation_cleanup();
	}

	// Clear scheduled events
	wp_clear_scheduled_hook('rank_math_api_update_check');
	
	// Clear update-related caches
	delete_transient('rank_math_api_github_release');
	delete_option('rank_math_api_last_github_check');
}

// Activation hook
register_activation_hook(__FILE__, 'rank_math_api_manager_activate');

// Deactivation hook
register_deactivation_hook(__FILE__, 'rank_math_api_manager_deactivate');

/**
 * Plugin uninstall function
 * 
 * Removes all plugin data when the plugin is uninstalled
 * 
 * @since 1.0.0
 */
function rank_math_api_manager_uninstall() {
	// Remove all plugin options
	delete_option('rank_math_api_activated');
	delete_option('rank_math_api_dependencies_status');
	delete_option('rank_math_api_dismissed_notices');
	delete_option('rank_math_api_notice_events');
	delete_option('rank_math_api_last_github_check');
	delete_option('rank_math_api_github_token');
	delete_option('rank_math_api_telemetry_settings');
	delete_option('rank_math_api_heartbeat_last_run');
	
	// Remove transients
	delete_transient('rank_math_api_github_release');
	
	// Clear any scheduled events
	wp_clear_scheduled_hook('rank_math_api_update_check');
	wp_clear_scheduled_hook('rank_math_api_telemetry_heartbeat');

	global $wpdb;

	if ( isset( $wpdb->usermeta ) ) {
		$meta_like = $wpdb->esc_like( 'rank_math_api_dismissed_' ) . '%';
		// phpcs:ignore WordPress.DB.DirectDatabaseQuery.DirectQuery, WordPress.DB.DirectDatabaseQuery.NoCaching -- Uninstall cleanup; no caching for one-time delete.
		$wpdb->query(
			$wpdb->prepare(
				"DELETE FROM {$wpdb->usermeta} WHERE meta_key LIKE %s",
				$meta_like
			)
		);
	}
}

// Uninstall hook
register_uninstall_hook(__FILE__, 'rank_math_api_manager_uninstall');
