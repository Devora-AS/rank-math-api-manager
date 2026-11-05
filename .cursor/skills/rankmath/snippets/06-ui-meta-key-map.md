# UI key to Rank Math meta key map

Source A:
- Path: `includes/admin/metabox/class-screen.php`
- Lines: `210-239`
- Symbol: `RankMath\Admin\Metabox\Screen::get_object_values()`

```php
public function get_object_values() {
	$keys = $this->do_filter(
		'metabox/' . $this->get_object_type() . '/meta_keys',
		[
			'title'                    => 'title',
			'description'              => 'description',
			'focusKeywords'            => 'focus_keyword',
			'pillarContent'            => 'pillar_content',
			'canonicalUrl'             => 'canonical_url',
			'breadcrumbTitle'          => 'breadcrumb_title',
			'advancedRobots'           => 'advanced_robots',

			// Facebook.
			'facebookTitle'            => 'facebook_title',
			'facebookDescription'      => 'facebook_description',
			'facebookImage'            => 'facebook_image',
			'facebookImageID'          => 'facebook_image_id',
			'facebookHasOverlay'       => 'facebook_enable_image_overlay',
			'facebookImageOverlay'     => 'facebook_image_overlay',
			'facebookAuthor'           => 'facebook_author',

			// Twitter.
			'twitterCardType'          => 'twitter_card_type',
			'twitterUseFacebook'       => 'twitter_use_facebook',
			'twitterTitle'             => 'twitter_title',
			'twitterDescription'       => 'twitter_description',
			'twitterImage'             => 'twitter_image',
			'twitterImageID'           => 'twitter_image_id',
			'twitterHasOverlay'        => 'twitter_enable_image_overlay',
			'twitterImageOverlay'      => 'twitter_image_overlay',
```

Source B:
- Path: `assets/admin/src/redux/actions/metadata.js`
- Lines: `16-37`
- Symbol: `updateAppData()`

```js
export function updateAppData( key, value, metaKey = false, metaValue = null ) {
	value = applyFilters( 'rank_math_sanitize_data', value, key, metaKey )
	if ( null !== metaValue ) {
		metaValue = applyFilters(
			'rank_math_sanitize_meta_value',
			metaValue,
			key,
			metaKey
		)
	}

	metaValue = null === metaValue ? value : metaValue

	doAction( 'rank_math_data_changed', key, value, metaKey )

	return {
		type: 'RANK_MATH_APP_DATA',
		key,
		value,
		metaKey,
		metaValue,
	}
}
```

Why it matters:
- the editor works with friendly keys like `facebookTitle`
- dirty metadata tracks the actual storage key like `rank_math_facebook_title`
