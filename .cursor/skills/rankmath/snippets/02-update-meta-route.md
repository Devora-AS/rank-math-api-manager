# Core write routes

Source:
- Path: `includes/rest/class-shared.php`
- Lines: `47-79`
- Symbol: `RankMath\Rest\Shared::register_routes()`

```php
public function register_routes() {

	register_rest_route(
		$this->namespace,
		'/updateRedirection',
		[
			'methods'             => WP_REST_Server::CREATABLE,
			'callback'            => [ $this, 'update_redirection' ],
			'args'                => $this->get_update_redirection_args(),
			'permission_callback' => [ '\\RankMath\\Rest\\Rest_Helper', 'get_redirection_permissions_check' ],
		]
	);

	register_rest_route(
		$this->namespace,
		'/updateMeta',
		[
			'methods'             => WP_REST_Server::CREATABLE,
			'callback'            => [ $this, 'update_metadata' ],
			'args'                => $this->get_update_metadata_args(),
			'permission_callback' => [ '\\RankMath\\Rest\\Rest_Helper', 'get_object_permissions_check' ],
		]
	);

	register_rest_route(
		$this->namespace,
		'/updateSchemas',
		[
			'methods'             => WP_REST_Server::CREATABLE,
			'callback'            => [ $this, 'update_schemas' ],
			'args'                => $this->get_update_schemas_args(),
			'permission_callback' => [ '\\RankMath\\Rest\\Rest_Helper', 'get_schema_permissions_check' ],
		]
	);
}
```

Why it matters:
- `updateMeta` is the main generic SEO metadata writer
- `updateSchemas` and `updateRedirection` are adjacent write flows used by the editor
