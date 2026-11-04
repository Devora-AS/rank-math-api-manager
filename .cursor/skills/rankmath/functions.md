# Functions and Classes

## REST bootstrap

### `RankMath::init_rest_api()`
- Path: `rank-math.php`
- Purpose: register the main REST controllers
- Input: none
- Output: none
- Notes: all core Rank Math REST routes begin here

### `RankMath\Rest\Rest_Helper`
- Path: `includes/rest/class-rest-helper.php`
- Purpose: namespace constant and permission checks
- Key members:
  - `BASE = 'rankmath/v1'`
  - `get_object_permissions_check()`
  - `get_post_permissions_check()`
  - `get_term_permissions_check()`
  - `get_user_permissions_check()`
  - `get_schema_permissions_check()`
  - `get_redirection_permissions_check()`

## Metadata write path

### `RankMath\Rest\Shared::update_metadata( WP_REST_Request $request )`
- Path: `includes/rest/class-shared.php`
- Purpose: generic REST writer for Rank Math object metadata
- Input:
  - `objectID`
  - `objectType`
  - `meta`
  - `content`
- Output:
  - array with `slug` and `schemas`
- Important details:
  - runs `rank_math/filter_metadata`
  - runs `rank_math/pre_update_metadata`
  - accepts any `rank_math_*` protected meta key after sanitization
  - deletes metadata for empty values
  - special-cases `permalink`
  - special-cases homepage updates when `objectID = 0`

### `RankMath\Traits\Meta::update_meta( $object_type, $object_id, $key, $value )`
- Path: `includes/traits/class-meta.php`
- Purpose: dispatch to `update_post_meta`, `update_term_meta`, or `update_user_meta`
- Input:
  - object type
  - object id
  - meta key
  - sanitized value
- Output:
  - result of the underlying WordPress metadata update
- Guardrail:
  - only writes protected meta keys

### `RankMath\Rest\Sanitize::sanitize( $field_id, $value )`
- Path: `includes/rest/class-sanitize.php`
- Purpose: apply field-specific sanitization
- Input:
  - concrete field id such as `rank_math_title`
- Output:
  - sanitized scalar or array
- Notable cases:
  - titles and descriptions -> `wp_filter_nohtml_kses`
  - canonical URL -> `esc_url_raw`
  - complex schema-ish arrays -> recursive sanitize
  - fallback -> `RankMath\CMB2::sanitize_textfield`

### `RankMath\Rest\Shared::update_site_editor_homepage( $meta )`
- Path: `includes/rest/class-shared.php`
- Purpose: map REST meta payload into homepage settings when `objectID = 0`
- Input:
  - `rank_math_title`
  - `rank_math_description`
  - `rank_math_facebook_title`
  - `rank_math_facebook_description`
  - `rank_math_facebook_image`
  - `rank_math_facebook_image_id`
  - `rank_math_robots`
  - `rank_math_advanced_robots`
  - `rank_math_breadcrumb_title`
- Output:
  - updates Rank Math option arrays via `Helper::update_all_settings()`

## Bulk editing path

### `RankMath\Rest\Post::update_bulk_meta( WP_REST_Request $request )`
- Path: `includes/rest/class-post.php`
- Purpose: bulk save post-list or term-list SEO columns
- Input:
  - `rows`
  - `objectType`
- Output:
  - `['success' => true]`
- Notes:
  - loops rows and skips objects that fail capability/access checks

### `RankMath\Rest\Post::save_column( $object_id, $object_type, $column, $value )`
- Path: `includes/rest/class-post.php`
- Purpose: normalize allowed bulk-edit columns to actual storage keys
- Allowed columns:
  - `focus_keyword`
  - `title`
  - `description`
  - `image_alt`
  - `image_title`
- Important detail:
  - only the first focus keyword is replaced when bulk-editing

## UI mapping and editor state

### `RankMath\Admin\Metabox\Screen::get_object_values()`
- Path: `includes/admin/metabox/class-screen.php`
- Purpose: map UI store keys to underlying Rank Math meta suffixes
- Examples:
  - `title` -> `title`
  - `description` -> `description`
  - `focusKeywords` -> `focus_keyword`
  - `canonicalUrl` -> `canonical_url`
  - `facebookTitle` -> `facebook_title`
  - `twitterTitle` -> `twitter_title`
- Why it matters:
  - explains how JS store keys become `rank_math_*` meta keys

### `updateAppData( key, value, metaKey, metaValue )`
- Path: `assets/admin/src/redux/actions/metadata.js`
- Purpose: central editor action for dirty metadata
- Output:
  - Redux action with `key`, `value`, `metaKey`, `metaValue`
- Hooks:
  - `rank_math_sanitize_data`
  - `rank_math_sanitize_meta_value`
  - `rank_math_data_changed`

### `updateTitle()`, `updateDescription()`, `updateKeywords()`, `updateCanonicalUrl()`
- Paths:
  - `assets/admin/src/redux/actions/post.js`
  - `assets/admin/src/redux/actions/data.js`
- Purpose: map editor updates to concrete Rank Math meta keys
- Examples:
  - `updateTitle()` -> `rank_math_title`
  - `updateDescription()` -> `rank_math_description`
  - `updateKeywords()` -> `rank_math_focus_keyword`
  - `updateCanonicalUrl()` -> `rank_math_canonical_url`

### `updateFacebookTitle()` / `updateFacebookDescription()` / `updateFacebookImage()`
- Path: `assets/admin/src/redux/actions/facebook.js`
- Purpose: map social Facebook UI fields to Rank Math meta keys

### `updateTwitterTitle()` / `updateTwitterDescription()` / `updateTwitterImage()`
- Path: `assets/admin/src/redux/actions/twitter.js`
- Purpose: map social Twitter UI fields to Rank Math meta keys

## Related but not core write-path functions

### `RankMath\Rest\Admin::update_settings()`
- Path: `includes/rest/class-admin.php`
- Purpose: update global settings, including titles/meta settings
- Use when:
  - working on homepage defaults or site-wide title/meta settings

### `RankMath\Rest\Admin::update_seo_score()`
- Path: `includes/rest/class-admin.php`
- Purpose: persist `rank_math_seo_score`

### `RankMath\Rest\Headless::get_head()`
- Path: `includes/rest/class-headless.php`
- Purpose: expose generated SEO head HTML for an internal URL

### `RankMath\Admin\Metabox\Metabox::save_meta()`
- Path: `includes/admin/metabox/class-metabox.php`
- Purpose: classic save handler for metabox forms
- Guardrails:
  - verifies nonce
  - prevents autosave handling
  - checks `edit_post`

### `RankMath\ContentAI\Bulk_Edit_SEO_Meta::task()`
- Path: `includes/modules/content-ai/class-bulk-edit-seo-meta.php`
- Purpose: background-process bulk update of `rank_math_title` and `rank_math_description`
- Notes:
  - not a REST route
  - useful when looking for alternate server-side writers
