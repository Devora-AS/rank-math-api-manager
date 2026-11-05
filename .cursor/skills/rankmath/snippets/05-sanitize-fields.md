# Field-specific sanitization

Source:
- Path: `includes/rest/class-sanitize.php`
- Lines: `49-113`
- Symbol: `RankMath\Rest\Sanitize::sanitize()`

```php
public function sanitize( $field_id, $value ) {
	$sanitized_value = '';
	switch ( $field_id ) {
		case 'rank_math_title':
		case 'rank_math_description':
		case 'rank_math_snippet_name':
		case 'rank_math_snippet_desc':
		case 'rank_math_facebook_title':
		case 'rank_math_facebook_description':
		case 'rank_math_twitter_title':
		case 'rank_math_twitter_description':
			$sanitized_value = wp_filter_nohtml_kses( $value );
			break;
		case 'rank_math_snippet_recipe_ingredients':
		case 'rank_math_snippet_recipe_instructions':
		case 'rank_math_snippet_recipe_single_instructions':
			$sanitized_value = $this->sanitize_textarea( $field_id, $value );
			break;
		case 'rank_math_canonical_url':
			$sanitized_value = esc_url_raw( $value );
			break;
		default:
			$sanitized_value = is_array( $value ) ? $this->loop_sanitize( $value ) : CMB2::sanitize_textfield( $value );
	}

	return $sanitized_value;
}
```

Why it matters:
- title/description/social text are stripped to no-html text
- canonical URL gets URL-specific sanitization
- arrays recurse through a different path
