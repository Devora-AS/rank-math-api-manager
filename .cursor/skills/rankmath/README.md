# Rank Math Skill

This skill packages a focused analysis of the public Rank Math SEO plugin repository for Cursor agents. It is tuned for tracing REST routes, permissions, sanitization, meta-key mappings, and the editor flows that save Rank Math SEO fields.

Source analyzed:
- Repo: `https://github.com/rankmath/seo-by-rank-math`
- Branch: `master`
- Commit: `0b67698`

## Install

This `rankmath/` directory is already structured as a project skill.

Recommended project location:

```text
.cursor/skills/rankmath/
```

## Files

- `SKILL.md`: main entrypoint for the agent
- `OVERVIEW.md`: repo map and important caveats
- `endpoints.md`: relevant REST endpoints and payload shapes
- `functions.md`: key classes/functions and file locations
- `examples.md`: request examples and workflow patterns
- `snippets/`: source-backed excerpts with path and line ranges
- `tasks/`: reusable prompts with acceptance criteria
- `verification.md`: checklist to confirm the skill against the repo

## How an AI assistant should use this skill

1. Start with `SKILL.md`.
2. Read `OVERVIEW.md` to understand the core write path.
3. Use `endpoints.md` to answer route questions.
4. Use `functions.md` and `snippets/` to support explanations or implementation proposals.
5. Use `examples.md` when the user asks for cURL, JSON, or n8n examples.
6. Use `tasks/` as prompt templates for deeper analysis or code design work.

## Concrete example

Confirmed internal route for metadata updates:

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

Expected response shape from `includes/rest/class-shared.php`, `RankMath\Rest\Shared::update_metadata()`:

```json
{
  "slug": true,
  "schemas": {}
}
```

`slug` can also be a changed permalink slug string, and `schemas` varies with current schema state.

## Human review notes

- Rank Math's own JS uses authenticated wp-admin REST calls with nonce/cookie auth.
- External automation with Application Passwords may work on a target site, but verify in staging because the repo itself does not document that as the primary path for these routes.
