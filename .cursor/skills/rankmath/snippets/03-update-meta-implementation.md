# `updateMeta` implementation

Source:
- Path: `includes/rest/class-shared.php`
- Lines: `123-176`
- Symbol: `RankMath\Rest\Shared::update_metadata()`

```php
public function update_metadata( WP_REST_Request $request ) {
	$object_id   = $request->get_param( 'objectID' );
	$object_type = $request->get_param( 'objectType' );
	$meta        = apply_filters( 'rank_math/filter_metadata', $request->get_param( 'meta' ), $request );
	$content     = $request->get_param( 'content' );

	if ( $object_id === 0 ) {
		$this->update_site_editor_homepage( $meta );
		return [
			'slug'    => '/',
			'schemas' => [],
		];
	}

	do_action( 'rank_math/pre_update_metadata', $object_id, $object_type, $content );
	$new_slug = true;
	if ( isset( $meta['permalink'] ) && ! empty( $meta['permalink'] ) && 'post' === $object_type ) {
		$post     = get_post( $object_id );
		$new_slug = wp_unique_post_slug( $meta['permalink'], $post->ID, $post->post_status, $post->post_type, $post->post_parent );
		if ( $new_slug !== $post->post_name ) {
			wp_update_post(
				[
					'ID'        => $object_id,
					'post_name' => $new_slug,
				]
			);
		}
		unset( $meta['permalink'] );
	}

	remove_all_filters( 'is_protected_meta' );
	add_filter( 'is_protected_meta', [ $this, 'only_this_plugin' ], 10, 2 );

	$sanitizer = Sanitize::get();
	foreach ( $meta as $meta_key => $meta_value ) {
		if ( empty( $meta_value ) ) {
			delete_metadata( $object_type, $object_id, $meta_key );
			continue;
		}

		$this->update_meta( $object_type, $object_id, $meta_key, $sanitizer->sanitize( $meta_key, $meta_value ) );
	}

	return [
		'slug'    => $new_slug,
		'schemas' => DB::get_schemas( $object_id, "{$object_type}meta", true ),
	];
}
```

Why it matters:
- shows the exact generic `meta` payload contract
- confirms the homepage special case and slug update behavior
- confirms empty values delete metadata
