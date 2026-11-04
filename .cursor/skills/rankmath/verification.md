# Verification

## Goal

Confirm that every documented route, function, and snippet still matches the analyzed Rank Math source tree.

## Static verification steps

### 1. Confirm the REST bootstrap
Run:

```bash
rg "init_rest_api|new \\\\RankMath\\\\Rest\\\\Admin|new \\\\RankMath\\\\Rest\\\\Shared|new \\\\RankMath\\\\Rest\\\\Post|new \\\\RankMath\\\\Rest\\\\Headless" rank-math.php
```

Expected:
- `rank-math.php` contains `RankMath::init_rest_api()`
- that method instantiates the core controllers

### 2. Confirm the route registrations
Run:

```bash
rg "register_rest_route\\(" includes/rest
```

Expected:
- matches in:
  - `includes/rest/class-shared.php`
  - `includes/rest/class-post.php`
  - `includes/rest/class-front.php`
  - `includes/rest/class-headless.php`
  - `includes/rest/class-admin.php`
  - `includes/rest/class-setup-wizard.php`

### 3. Confirm the main metadata writer
Run:

```bash
rg "function update_metadata|rank_math/filter_metadata|rank_math/pre_update_metadata" includes/rest/class-shared.php
```

Expected:
- `RankMath\Rest\Shared::update_metadata()` exists
- filter and action hooks are present

### 4. Confirm the bulk writer
Run:

```bash
rg "updateMetaBulk|function update_bulk_meta|function save_column" includes/rest/class-post.php
```

Expected:
- bulk route exists
- `save_column()` only allows the documented bulk fields

### 5. Confirm field sanitization
Run:

```bash
rg "rank_math_title|rank_math_description|rank_math_facebook_title|rank_math_twitter_title|rank_math_canonical_url" includes/rest/class-sanitize.php
```

Expected:
- the documented fields appear in `RankMath\Rest\Sanitize::sanitize()`

### 6. Confirm UI-to-meta-key mapping
Run:

```bash
rg "focusKeywords|canonicalUrl|facebookTitle|twitterTitle" includes/admin/metabox/class-screen.php
rg "rank_math_title|rank_math_description|rank_math_focus_keyword|rank_math_canonical_url" assets/admin/src/redux/actions
```

Expected:
- editor store keys map cleanly to Rank Math meta keys

## Runtime verification steps

### 1. Browser-authenticated write test
Prerequisites:
- logged-in WordPress session
- REST nonce from wp-admin
- user with capability to edit the target object

Call:
- `POST /wp-json/rankmath/v1/updateMeta`

Verify:
- route returns `200`
- title/description changes appear in the Rank Math editor UI
- updated meta exists in post, term, or user metadata

### 2. Bulk write test
Call:
- `POST /wp-json/rankmath/v1/updateMetaBulk`

Verify:
- response contains `success: true`
- only supported columns update
- first focus keyword changes as expected

### 3. Headless exposure test
Enable:
- Rank Math headless support

Call:
- `GET /wp-json/rankmath/v1/getHead?url=<internal-url>`

Verify:
- response contains `success: true`
- `head` includes expected title/meta tags

### 4. Homepage special-case test
Call:
- `POST /wp-json/rankmath/v1/updateMeta` with `objectID = 0`

Verify:
- response is `{"slug":"/","schemas":[]}` or equivalent
- homepage settings change in Rank Math titles/general settings

## Human review items

- Confirm whether the target site allows Application Password auth for these routes.
- Confirm whether any required module is active for schema or redirection routes.
- Confirm exact `updateSettings` payloads from a live request if you need to automate global settings.
- Confirm whether a target field is free-version or module-dependent before promising availability.
