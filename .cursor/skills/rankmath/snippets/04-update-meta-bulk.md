# Bulk metadata save path

Source A:
- Path: `includes/rest/class-post.php`
- Lines: `38-49`
- Symbol: `RankMath\Rest\Post::register_routes()`

```php
public function register_routes() {
	register_rest_route(
		$this->namespace,
		'/updateMetaBulk',
		[
			'methods'             => WP_REST_Server::CREATABLE,
			'permission_callback' => function () {
				return \RankMath\Helper::has_cap( 'onpage_general' );
			},
			'callback'            => [ $this, 'update_bulk_meta' ],
			'args'                => $this->get_update_bulk_meta_args(),
		]
	);
}
```

Source B:
- Path: `includes/rest/class-post.php`
- Lines: `158-185`
- Symbol: `RankMath\Rest\Post::save_column()`

```php
private function save_column( $object_id, $object_type, $column, $value ) {
	if ( ! in_array( $column, [ 'focus_keyword', 'title', 'description', 'image_alt', 'image_title' ], true ) ) {
		return;
	}

	$sanitizer = Sanitize::get();
	if ( 'image_title' === $column ) {
		wp_update_post(
			[
				'ID'         => $object_id,
				'post_title' => $sanitizer->sanitize( 'image_title', $value ),
			]
		);
		return;
	}

	if ( 'focus_keyword' === $column ) {
		$focus_keyword    = get_post_meta( $object_id, 'rank_math_' . $column, true );
		$focus_keyword    = explode( ',', $focus_keyword );
		$focus_keyword[0] = $value;
		$value            = implode( ',', $focus_keyword );
	}

	$column = 'image_alt' === $column ? '_wp_attachment_image_alt' : 'rank_math_' . $column;

	$method = $object_type === 'term' ? 'update_term_meta' : 'update_post_meta';
	$method( $object_id, $column, $sanitizer->sanitize( $column, $value ) );
}
```

Why it matters:
- bulk list editing is not fully generic
- focus keyword handling is special and only replaces the primary keyword slot
