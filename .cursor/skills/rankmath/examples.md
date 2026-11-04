# Examples

## Confirmed browser-authenticated metadata update

This matches the repo's internal `apiFetch()` usage pattern.

```bash
curl --request POST "https://example.com/wp-json/rankmath/v1/updateMeta" \
  --header "Content-Type: application/json" \
  --header "X-WP-Nonce: YOUR_WP_REST_NONCE" \
  --cookie "wordpress_logged_in_HASH=YOUR_SESSION_COOKIE" \
  --data '{
    "objectID": 123,
    "objectType": "post",
    "meta": {
      "rank_math_title": "Custom SEO Title",
      "rank_math_description": "Custom meta description",
      "rank_math_focus_keyword": "primary keyword,secondary keyword",
      "rank_math_canonical_url": "https://example.com/custom-url/"
    },
    "content": "<p>Current post content</p>"
  }'
```

Expected response shape:
```json
{
  "slug": true,
  "schemas": {}
}
```

## Social metadata update

```bash
curl --request POST "https://example.com/wp-json/rankmath/v1/updateMeta" \
  --header "Content-Type: application/json" \
  --header "X-WP-Nonce: YOUR_WP_REST_NONCE" \
  --cookie "wordpress_logged_in_HASH=YOUR_SESSION_COOKIE" \
  --data '{
    "objectID": 123,
    "objectType": "post",
    "meta": {
      "rank_math_facebook_title": "Facebook SEO Title",
      "rank_math_facebook_description": "Facebook SEO description",
      "rank_math_facebook_image": "https://example.com/uploads/fb-image.jpg",
      "rank_math_facebook_image_id": 987,
      "rank_math_twitter_title": "Twitter SEO Title",
      "rank_math_twitter_description": "Twitter SEO description",
      "rank_math_twitter_image": "https://example.com/uploads/twitter-image.jpg",
      "rank_math_twitter_image_id": 988
    },
    "content": "<p>Current post content</p>"
  }'
```

## Homepage update through Site Editor special case

`objectID = 0` is special.

```bash
curl --request POST "https://example.com/wp-json/rankmath/v1/updateMeta" \
  --header "Content-Type: application/json" \
  --header "X-WP-Nonce: YOUR_WP_REST_NONCE" \
  --cookie "wordpress_logged_in_HASH=YOUR_SESSION_COOKIE" \
  --data '{
    "objectID": 0,
    "objectType": "post",
    "meta": {
      "rank_math_title": "Homepage SEO Title",
      "rank_math_description": "Homepage SEO description",
      "rank_math_facebook_title": "Homepage Facebook Title",
      "rank_math_facebook_description": "Homepage Facebook Description"
    }
  }'
```

Expected response from source:
```json
{
  "slug": "/",
  "schemas": []
}
```

## Bulk list edit

```bash
curl --request POST "https://example.com/wp-json/rankmath/v1/updateMetaBulk" \
  --header "Content-Type: application/json" \
  --header "X-WP-Nonce: YOUR_WP_REST_NONCE" \
  --cookie "wordpress_logged_in_HASH=YOUR_SESSION_COOKIE" \
  --data '{
    "rows": {
      "123": {
        "title": "Bulk SEO title",
        "description": "Bulk SEO description",
        "focus_keyword": "primary keyword"
      }
    },
    "objectType": "post"
  }'
```

Expected response:
```json
{
  "success": true
}
```

## Headless head exposure

This is read-only and only exists when Rank Math headless support is enabled.

```bash
curl "https://example.com/wp-json/rankmath/v1/getHead?url=https%3A%2F%2Fexample.com%2Fsample-post%2F"
```

Expected response shape:
```json
{
  "success": true,
  "head": "<title>...</title><meta ...>"
}
```

## Application Password variant for external automation
Human review and runtime test required.

The repo confirms nonce+cookie usage. If your WordPress site supports Application Passwords for these routes, this pattern may work:

```bash
curl --request POST "https://example.com/wp-json/rankmath/v1/updateMeta" \
  --user "editor-user:application-password" \
  --header "Content-Type: application/json" \
  --data '{
    "objectID": 123,
    "objectType": "post",
    "meta": {
      "rank_math_title": "External automation title",
      "rank_math_description": "External automation description"
    },
    "content": "<p>Current post content</p>"
  }'
```

Use staging first. Permission callbacks still require the authenticated user to be allowed to edit the object.

## n8n pseudocode

### HTTP Request node
- Method: `POST`
- URL: `https://example.com/wp-json/rankmath/v1/updateMeta`
- Authentication:
  - preferred confirmed path: session-based browser context, not typical for n8n
  - runtime-verify alternative: WordPress Application Password
- Body type: JSON

### Example body
```json
{
  "objectID": "={{ $json.post_id }}",
  "objectType": "post",
  "meta": {
    "rank_math_title": "={{ $json.seo_title }}",
    "rank_math_description": "={{ $json.seo_description }}",
    "rank_math_focus_keyword": "={{ $json.focus_keywords }}",
    "rank_math_canonical_url": "={{ $json.canonical_url }}",
    "rank_math_facebook_title": "={{ $json.facebook_title }}",
    "rank_math_twitter_title": "={{ $json.twitter_title }}"
  },
  "content": "={{ $json.rendered_content }}"
}
```

### Safer wrapper-plugin pattern
For external automation, prefer a thin custom plugin endpoint that:
- authenticates external callers explicitly
- validates only the allowed Rank Math fields you want to expose
- calls Rank Math internals or writes the exact `rank_math_*` keys after capability checks
- avoids depending directly on Rank Math's editor-internal payload shape
