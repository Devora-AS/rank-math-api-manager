# Task: Trace SEO title save flow

## Goal
Trace how a title entered in the Rank Math editor becomes stored metadata.

## What to return
- JS action path from editor interaction to dirty metadata
- UI key used in JS
- final stored meta key
- REST handler or classic save handler involved
- sanitizer used before persistence

## Acceptance criteria
- mentions `updateTitle()`
- mentions `updateAppData()`
- ends at `rank_math_title`
- cites either REST write flow or metabox save flow
