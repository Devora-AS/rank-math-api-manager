# Endpoints

All paths below are relative to `/wp-json/`.

## 1. `POST /rankmath/v1/updateMeta`
Primary per-object SEO metadata write endpoint.

- Path: `includes/rest/class-shared.php`
- Class: `RankMath\Rest\Shared`
- Route registration: `register_routes()`
- Handler: `update_metadata()`
- Permission callback: `RankMath\Rest\Rest_Helper::get_object_permissions_check()`
- Supported object types: `post`, `term`, `user`
- Special case: `objectID = 0` updates homepage settings through `update_site_editor_homepage()`

### Request payload
```json
{
  "objectID": 123,
  "objectType": "post",
  "meta": {
    "rank_math_title": "Custom SEO Title",
    "rank_math_description": "Custom SEO description",
    "rank_math_focus_keyword": "primary keyword,secondary keyword",
    "rank_math_canonical_url": "https://example.com/custom-url/",
    "rank_math_facebook_title": "Facebook title",
    "rank_math_facebook_description": "Facebook description",
    "rank_math_twitter_title": "Twitter title",
    "rank_math_twitter_description": "Twitter description",
    "permalink": "optional-slug"
  },
  "content": "<p>Current post content</p>"
}
```

### Behavior
- Runs `rank_math/filter_metadata`
- Runs `rank_math/pre_update_metadata`
- Temporarily restricts protected meta writes to keys starting with `rank_math_`
- Deletes metadata when a provided value is empty
- Sanitizes field values with `RankMath\Rest\Sanitize::sanitize()`
- Can update the post slug if `meta.permalink` is present
- Returns updated schema data for the object

### Response shape
Inferred from `RankMath\Rest\Shared::update_metadata()`:

```json
{
  "slug": true,
  "schemas": {}
}
```

Notes:
- `slug` may be `true`, `/`, or a slug string depending on request path and permalink behavior.
- `schemas` varies with current schema state.

### Exact source references
- `includes/rest/class-shared.php`, `RankMath\Rest\Shared::register_routes()`
- `includes/rest/class-shared.php`, `RankMath\Rest\Shared::update_metadata()`
- `includes/rest/class-rest-helper.php`, `RankMath\Rest\Rest_Helper::get_object_permissions_check()`
- `includes/rest/class-sanitize.php`, `RankMath\Rest\Sanitize::sanitize()`

## 2. `POST /rankmath/v1/updateMetaBulk`
Bulk write endpoint used by Rank Math post list and term list screens.

- Path: `includes/rest/class-post.php`
- Class: `RankMath\Rest\Post`
- Route registration: `register_routes()`
- Handler: `update_bulk_meta()`
- Permission gate:
  - route-level `RankMath\Helper::has_cap( 'onpage_general' )`
  - per-object checks in `can_process()`

### Request payload
```json
{
  "rows": {
    "123": {
      "title": "Bulk SEO title",
      "description": "Bulk SEO description",
      "focus_keyword": "primary keyword"
    },
    "456": {
      "title": "Another SEO title"
    }
  },
  "objectType": "post"
}
```

### Supported columns
Only these are accepted by `save_column()`:
- `title`
- `description`
- `focus_keyword`
- `image_alt`
- `image_title`

Important:
- `focus_keyword` only replaces the first keyword in the stored comma-separated list.
- `title` and `description` become `rank_math_title` and `rank_math_description`.
- `image_alt` writes `_wp_attachment_image_alt`.
- `image_title` writes the attachment post title with `wp_update_post()`.

### Response shape
```json
{
  "success": true
}
```

### Exact source references
- `includes/rest/class-post.php`, `RankMath\Rest\Post::register_routes()`
- `includes/rest/class-post.php`, `RankMath\Rest\Post::update_bulk_meta()`
- `includes/rest/class-post.php`, `RankMath\Rest\Post::can_process()`
- `includes/rest/class-post.php`, `RankMath\Rest\Post::save_column()`
- Client caller: `assets/admin/src/post-list.js`

## 3. `POST /rankmath/v1/updateSchemas`
Schema write endpoint. Not a generic title/description endpoint, but directly relevant to rich snippet SEO data.

- Path: `includes/rest/class-shared.php`
- Class: `RankMath\Rest\Shared`
- Handler: `update_schemas()`
- Permission callback: `RankMath\Rest\Rest_Helper::get_schema_permissions_check()`

### Request payload
```json
{
  "objectID": 123,
  "objectType": "post",
  "schemas": {
    "new-0": {
      "@type": "Article",
      "headline": "Example headline",
      "metadata": {}
    }
  }
}
```

### Response shape
Map of temporary schema IDs to saved metadata IDs:

```json
{
  "new-0": 4567
}
```

### Exact source references
- `includes/rest/class-shared.php`, `RankMath\Rest\Shared::register_routes()`
- `includes/rest/class-shared.php`, `RankMath\Rest\Shared::update_schemas()`
- `includes/rest/class-rest-helper.php`, `RankMath\Rest\Rest_Helper::get_schema_permissions_check()`

## 4. `POST /rankmath/v1/updateRedirection`
Supporting SEO endpoint for redirect metadata, not direct title/description fields.

- Path: `includes/rest/class-shared.php`
- Class: `RankMath\Rest\Shared`
- Handler: `update_redirection()`
- Permission callback: `RankMath\Rest\Rest_Helper::get_redirection_permissions_check()`

### Relevant because
- often paired with permalink or SEO URL changes
- used by editor flows alongside `updateMeta`

### Request payload
```json
{
  "objectID": 123,
  "objectType": "post",
  "hasRedirect": true,
  "redirectionID": "",
  "redirectionUrl": "https://example.com/new-target/",
  "redirectionSources": "old-path/",
  "redirectionType": "301"
}
```

### Exact source references
- `includes/rest/class-shared.php`, `RankMath\Rest\Shared::update_redirection()`

## 5. `POST /rankmath/v1/updateSeoScore`
Supporting SEO endpoint for score persistence.

- Path: `includes/rest/class-admin.php`
- Class: `RankMath\Rest\Admin`
- Handler: `update_seo_score()`
- Permission callback: `RankMath\Rest\Admin::can_edit_posts()`

### Request payload
```json
{
  "postScores": {
    "123": 84,
    "456": 72
  }
}
```

### Response shape
Returns `1` on success path, `0` when empty payload.

### Exact source references
- `includes/rest/class-admin.php`, `RankMath\Rest\Admin::update_seo_score()`
- `includes/rest/class-admin.php`, `RankMath\Rest\Admin::can_edit_posts()`

## 6. `POST /rankmath/v1/updateSettings`
Supporting global settings endpoint. Relevant when you need homepage or global titles/meta settings, not per-post metadata.

- Path: `includes/rest/class-admin.php`
- Class: `RankMath\Rest\Admin`
- Handler: `update_settings()`
- Permission callback: `RankMath\Rest\Rest_Helper::can_manage_settings()`

### Notes
- `type` can include `general`, `titles`, `sitemap`, `roleCapabilities`, `redirections`, `instant-indexing`
- `type = titles` is the relevant branch for global titles/meta settings
- payload structure varies by settings screen and needs runtime capture for exact automation use

### Exact source references
- `includes/rest/class-admin.php`, `RankMath\Rest\Admin::update_settings()`
- `includes/rest/class-rest-helper.php`, `RankMath\Rest\Rest_Helper::can_manage_settings()`

## 7. `GET /rankmath/v1/getHead`
Read-only headless endpoint that exposes generated SEO head markup.

- Path: `includes/rest/class-headless.php`
- Class: `RankMath\Rest\Headless`
- Handler: `get_head()`
- Permission callback: `__return_true`
- Registration condition: only when `general.headless_support` is enabled

### Request payload
Query string:
- `url`: required internal URL

### Response shape
```json
{
  "success": true,
  "head": "<title>...</title><meta ...>"
}
```

### Exact source references
- `includes/rest/class-headless.php`, `RankMath\Rest\Headless::register_routes()`
- `includes/rest/class-headless.php`, `RankMath\Rest\Headless::get_head()`

## 8. `POST /rankmath/v1/getFeaturedImageId`
Supporting helper endpoint for social preview/image workflows.

- Path: `includes/rest/class-front.php`
- Class: `RankMath\Rest\Front`
- Handler: `get_featured_image_id()`
- Permission gate: `RankMath\Helper::has_cap( 'onpage_general' )` plus per-post checks inside handler

### Request payload
```json
{
  "postId": 123
}
```

### Response shape
Success:
```json
{
  "success": true,
  "featImgId": 987
}
```

Failure examples are also returned as JSON payloads with `success: false`.

### Exact source references
- `includes/rest/class-front.php`, `RankMath\Rest\Front::get_featured_image_id()`

## REST field exposure, not a route
Relevant exposure mechanism for Full Site Editor:

- Path: `includes/rest/class-post.php`
- Class: `RankMath\Rest\Post`
- In `register_routes()`, when `Helper::is_site_editor()` is true, a REST field `rankMath` is registered on the `page` object type
- Getter: `get_post_screen_meta()`

This is important when tracing how Rank Math exposes page metadata in Site Editor contexts.
