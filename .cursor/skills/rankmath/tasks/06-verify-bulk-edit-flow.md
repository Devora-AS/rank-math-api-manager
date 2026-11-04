# Task: Verify the bulk edit flow

## Goal
Explain exactly what Rank Math's bulk SEO editor can and cannot update through `updateMetaBulk`.

## What to return
- allowed fields
- storage keys written for each field
- object types supported
- capability checks involved
- one limitation or edge case that could surprise implementers

## Acceptance criteria
- mentions the five allowed columns in `save_column()`
- notes the first-keyword-only behavior for `focus_keyword`
- distinguishes post and term processing
