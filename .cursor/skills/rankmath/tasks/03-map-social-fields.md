# Task: Map social SEO fields

## Goal
Map the Facebook and Twitter editor fields to their persisted Rank Math meta keys and REST payload keys.

## What to return
- table of UI key -> stored meta key
- whether the field is visible in `Screen::get_object_values()`
- example `updateMeta` payload fragment

## Acceptance criteria
- includes Facebook title, description, image, image ID
- includes Twitter title, description, image, image ID
- uses exact `rank_math_*` keys from source
