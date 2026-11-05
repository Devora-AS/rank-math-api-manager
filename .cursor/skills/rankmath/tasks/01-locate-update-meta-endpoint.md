# Task: Locate the updateMeta endpoint

## Goal
Identify the exact file, class, registration call, permission callback, and write handler for Rank Math's primary SEO metadata update endpoint.

## What to return
- route path
- file path
- class name
- registration method
- callback method
- permission callback
- 1 short explanation of what payload shape it expects

## Acceptance criteria
- cites `rank-math.php` and `includes/rest/class-shared.php`
- names `RankMath\Rest\Shared::update_metadata()`
- names `RankMath\Rest\Rest_Helper::get_object_permissions_check()`
