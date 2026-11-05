# Overview

## Repository anchor points

- REST bootstrap: `rank-math.php`, `RankMath::init_rest_api()`
- Core REST helpers: `includes/rest/class-rest-helper.php`, `RankMath\Rest\Rest_Helper`
- Main SEO metadata writer: `includes/rest/class-shared.php`, `RankMath\Rest\Shared::update_metadata()`
- Bulk list writer: `includes/rest/class-post.php`, `RankMath\Rest\Post::update_bulk_meta()`
- Sanitizer: `includes/rest/class-sanitize.php`, `RankMath\Rest\Sanitize::sanitize()`
- UI meta-key map: `includes/admin/metabox/class-screen.php`, `RankMath\Admin\Metabox\Screen::get_object_values()`
- Editor-side dirty-meta builder: `assets/admin/src/redux/actions/metadata.js`, `updateAppData()`

## Where REST API endpoints are implemented

### Core REST bootstrap
- Path: `rank-math.php`
- Function: `RankMath::init_rest_api()`
- Behavior: instantiates the core controllers and calls `register_routes()` on each

Controllers registered there:
- `RankMath\Rest\Admin`
- `RankMath\Rest\Front`
- `RankMath\Rest\Shared`
- `RankMath\Rest\Post`
- `RankMath\Rest\Headless`
- `RankMath\Rest\Setup_Wizard`

### Core endpoint classes relevant to SEO fields
- `includes/rest/class-shared.php`
  - `RankMath\Rest\Shared::register_routes()`
  - `update_metadata()`
  - `update_schemas()`
  - `update_redirection()`
  - `update_site_editor_homepage()`
- `includes/rest/class-post.php`
  - `RankMath\Rest\Post::register_routes()`
  - `update_bulk_meta()`
  - `save_column()`
  - also exposes a REST field for Site Editor page objects
- `includes/rest/class-front.php`
  - `RankMath\Rest\Front::get_featured_image_id()`
- `includes/rest/class-headless.php`
  - `RankMath\Rest\Headless::get_head()`
- `includes/rest/class-admin.php`
  - `RankMath\Rest\Admin::update_seo_score()`
  - `update_settings()` for global settings, including titles/meta settings

## Relevant hooks and filters

### PHP hooks and filters
- `rank_math/filter_metadata`
  - Path: `includes/rest/class-shared.php`
  - Use: mutate incoming `meta` before persistence
- `rank_math/pre_update_metadata`
  - Path: `includes/rest/class-shared.php`
  - Use: side effects before writing SEO metadata
- `rank_math/schema/filter_data`
  - Path: `includes/rest/class-shared.php`
  - Use: mutate schema payload before saving
- `rank_math/pre_update_schema`
  - Path: `includes/rest/class-shared.php`
  - Use: pre-save hook for schema updates
- `rank_math/schema/update`
  - Path: `includes/rest/class-shared.php`
  - Use: post-save hook for schema updates
- `metabox/{object_type}/meta_keys`
  - Path: `includes/admin/metabox/class-screen.php`
  - Use: extend the UI-to-meta-key mapping used by the editor

### JS hooks in the editor data flow
- `rank_math_sanitize_data`
  - Path: `assets/admin/src/redux/actions/metadata.js`
  - Use: sanitize UI data before it becomes dirty metadata
- `rank_math_sanitize_meta_value`
  - Path: `assets/admin/src/redux/actions/metadata.js`
  - Use: sanitize explicit meta values before submission
- `rank_math_data_changed`
  - Path: `assets/admin/src/redux/actions/metadata.js`
  - Use: observe UI/meta changes
- `rank_math_metadata_updated`
  - Paths:
    - `assets/admin/src/gutenberg/DataCollector.js`
    - `includes/3rdparty/elementor/assets/src/DataCollector.js`
    - `includes/3rdparty/divi/assets/src/DataCollector.js`
  - Use: notify after successful REST metadata save

## Relevant functions and classes that manipulate SEO fields

### Metadata write path
- `RankMath\Rest\Shared::update_metadata()`
  - Generic writer for `rank_math_*` metadata via REST
- `RankMath\Traits\Meta::update_meta()`
  - Writes protected meta by dispatching to `update_post_meta`, `update_term_meta`, or `update_user_meta`
- `RankMath\Rest\Sanitize::sanitize()`
  - Applies field-specific sanitization rules
- `RankMath\Rest\Shared::update_site_editor_homepage()`
  - Special-case mapping when `objectID = 0`
- `RankMath\Rest\Post::save_column()`
  - Bulk edit writer for selected post list columns
- `RankMath\ContentAI\Bulk_Edit_SEO_Meta::task()`
  - Background process that updates title/description in bulk without REST

### UI-to-meta-key mapping
- `RankMath\Admin\Metabox\Screen::get_object_values()`
  - Maps editor keys like `title`, `focusKeywords`, `facebookTitle`, `twitterTitle` to Rank Math meta keys
- `assets/admin/src/redux/actions/post.js`
  - `updateTitle()` -> `rank_math_title`
  - `updateDescription()` -> `rank_math_description`
- `assets/admin/src/redux/actions/data.js`
  - `updateKeywords()` -> `rank_math_focus_keyword`
  - `updateCanonicalUrl()` -> `rank_math_canonical_url`
- `assets/admin/src/redux/actions/facebook.js`
  - social Facebook keys
- `assets/admin/src/redux/actions/twitter.js`
  - social Twitter keys

## High-value field map

Common fields confirmed in this repo:
- `rank_math_title`
- `rank_math_description`
- `rank_math_focus_keyword`
- `rank_math_canonical_url`
- `rank_math_facebook_title`
- `rank_math_facebook_description`
- `rank_math_facebook_image`
- `rank_math_facebook_image_id`
- `rank_math_twitter_title`
- `rank_math_twitter_description`
- `rank_math_twitter_image`
- `rank_math_twitter_image_id`
- `rank_math_robots`
- `rank_math_advanced_robots`
- `rank_math_breadcrumb_title`
- `rank_math_seo_score`

## Limitations and assumptions

- No dedicated external-automation REST API exists specifically for third-party tools. The main write route is an internal editor endpoint that accepts generic `meta`.
- `updateMeta` is flexible but not self-documenting; accepted keys are shaped by UI mappings and sanitization logic.
- `updateMetaBulk` is intentionally narrower than `updateMeta`.
- `updateSettings` can modify global titles/meta settings, but its payload contract is less obvious from source alone and may need runtime capture.
- `getHead` is read-only and only registers when `general.headless_support` is enabled.
- The repo confirms browser nonce/cookie auth. External Application Password use is plausible but should be runtime-tested.
- Some module- or settings-dependent behavior needs human review on a live site.
