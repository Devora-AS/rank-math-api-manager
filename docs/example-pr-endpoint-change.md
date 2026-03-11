# Example PR: Tighten `update-meta` post authorization

## Summary

- What changed: the `POST /wp-json/rank-math-api/v1/update-meta` endpoint now validates `post_id` as an integer, rejects unsupported targets, and checks `current_user_can( 'edit_post', $post_id )` instead of a broad post-edit capability.
- Why: the endpoint should authorize access against the specific object being updated and return clearer request errors.

## Endpoint Change Details

### Capability Review

- Purpose: restrict updates to users who can edit the exact requested post.
- Why needed: a broad capability check is weaker than an object-level permission check for per-post mutations.
- Allowed callers: authenticated users who can edit the target post.

### Input Validation

| Field | Type | Required | Validation |
| --- | --- | --- | --- |
| `post_id` | `integer` | `yes` | must be a positive integer, must resolve to an existing supported post object |
| `rank_math_title` | `string` | `no` | sanitized with `wp_filter_nohtml_kses()` |
| `rank_math_description` | `string` | `no` | sanitized with `wp_filter_nohtml_kses()` |
| `rank_math_canonical_url` | `string` | `no` | valid URL, sanitized with `esc_url_raw()` |
| `rank_math_focus_keyword` | `string` | `no` | sanitized with `sanitize_text_field()` |

### Sanitization And Escaping

- Input sanitization: `post_id` uses `absint`; SEO title/description use `wp_filter_nohtml_kses()`; focus keyword uses `sanitize_text_field()`; canonical URL uses `esc_url_raw()`.
- Storage sanitization: only sanitized values are written to post meta.
- Output escaping: endpoint returns status strings only; docs examples escape user-provided values when rendered in HTML.

### Response Shape Review

- Success status and shape: `200`, JSON object containing only changed keys with `"updated"` as the value.
- Error status and shape: `400` for invalid `post_id`, `401` for unauthenticated access, `403` for insufficient permission.

Success example:

```json
{
  "rank_math_title": "updated",
  "rank_math_description": "updated"
}
```

Error example:

```json
{
  "code": "rest_forbidden",
  "message": "You cannot edit this post.",
  "data": {
    "status": 403
  }
}
```

### Manual HTTP Verification

```bash
curl --request POST "https://example.com/wp-json/rank-math-api/v1/update-meta" \
  --header "Content-Type: application/json" \
  --user "automation-user:app-password" \
  --data '{
    "post_id": 123,
    "rank_math_title": "Updated SEO title",
    "rank_math_description": "Updated SEO description"
  }'
```

Expected response:

```json
{
  "rank_math_title": "updated",
  "rank_math_description": "updated"
}
```

## Security Checklist

- Threat model: unauthorized metadata mutation, invalid object targeting, and accidental exposure of internal error detail.
- Authentication and authorization: WordPress Application Passwords or another authenticated REST context; object-level permission enforced with `current_user_can( 'edit_post', $post_id )`.
- Rate limiting and abuse mitigation: no plugin-level rate limiter yet; endpoint remains authenticated and limited to users with edit capability. Follow-up rate limiting can be added separately if abuse risk increases.
- Data exposure and PII review: endpoint returns only changed field status values and no sensitive metadata.
- Input validation and sanitization summary: see validation and sanitization sections above; all user-controlled fields are sanitized before storage.
- Logging and error handling: no credentials or request bodies logged; client receives standard `WP_Error` responses with explicit HTTP status codes.

## Docs And Tests

- Updated docs: `.cursor/README.md`, `README.md`, and API usage examples if applicable.
- Updated tests or manual verification: manual `curl` verification updated to match the object-level permission behavior.
- Migration note, if needed: callers that relied on a broad editor capability must now authenticate as a user who can edit the specific post.

## Reviewer Checklist

- [x] Forbidden-files check completed
- [x] REST checklist completed
- [x] Release packaging exclusions verified
- [x] Agent scope confirmed
- [x] Security checklist completed
- [x] Documentation and test examples updated for route/auth/payload change
