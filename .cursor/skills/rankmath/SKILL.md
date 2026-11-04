---
name: rankmath
description: Analyze Rank Math SEO core behavior, especially REST routes, meta-key storage, sanitization, permissions, and headless output. Use when working with rankmath/seo-by-rank-math, tracing how Rank Math saves SEO fields, or designing a wrapper plugin that exposes Rank Math data safely.
---

# Rank Math

## When to use

Use this skill when the task involves:

- the `rankmath/seo-by-rank-math` repository
- Rank Math REST endpoints under `rankmath/v1`
- post, term, user, or homepage SEO metadata
- schema metadata updates
- social metadata such as Facebook or Twitter title/description/image fields
- evaluating whether Rank Math's internal endpoints are suitable for external automation
- designing wrapper routes for a plugin such as Rank Math API Manager

## Quick start

1. Read `OVERVIEW.md`.
2. Read `endpoints.md` for route-level behavior.
3. Read `functions.md` for class and function mapping.
4. Read `examples.md` for request payloads.
5. Read `snippets/*.md` when you need source-backed excerpts.
6. Read `tasks/*.md` when the user wants a concrete analysis or implementation prompt.

## High-signal facts

- Core REST namespace: `rankmath/v1`
- REST bootstrap: `rank-math.php`, `RankMath::init_rest_api()`
- Main write route for SEO meta: `POST /wp-json/rankmath/v1/updateMeta`
- Bulk list-edit route: `POST /wp-json/rankmath/v1/updateMetaBulk`
- Schema write route: `POST /wp-json/rankmath/v1/updateSchemas`
- Public headless read route: `GET /wp-json/rankmath/v1/getHead` when headless support is enabled
- Generic object types for `updateMeta`: `post`, `term`, `user`
- Special homepage case: `objectID = 0` updates homepage settings instead of post meta
- Rank Math editor UI writes generic `meta` payloads keyed by `rank_math_*` meta keys
- `updateMetaBulk` is narrower than `updateMeta`; it only accepts `title`, `description`, `focus_keyword`, `image_alt`, `image_title`

## Safe interpretation rules

- Treat these routes as internal Rank Math/editor endpoints first, not public automation APIs.
- Assume cookie + nonce auth is the confirmed path, because that is what the repo JS uses.
- Treat Basic Auth or Application Password examples as runtime-verify guidance unless you have tested the target site.
- Do not assume every `rank_math_*` key is valid for every object type.
- When documenting a field, cite the exact repo path and symbol that handles it.

## What to read for common requests

For "Where is a route registered?":
- `endpoints.md`
- `snippets/01-rest-bootstrap.md`
- `snippets/02-update-meta-route.md`

For "How is SEO title/description saved?":
- `functions.md`
- `snippets/03-update-meta-implementation.md`
- `snippets/05-sanitize-fields.md`
- `snippets/06-ui-meta-key-map.md`

For "Can I call this from n8n or a custom plugin?":
- `examples.md`
- `verification.md`
- `tasks/04-assess-external-automation.md`

For "How do social fields map to meta keys?":
- `functions.md`
- `examples.md`
- `tasks/03-map-social-fields.md`

## Limitations

- This skill is based on repo analysis of `master` at commit `0b67698`.
- Runtime behavior can still vary because of settings, active modules, permissions, and site-specific auth.
- Rank Math Pro behavior is not fully covered unless visible in this repo path.
