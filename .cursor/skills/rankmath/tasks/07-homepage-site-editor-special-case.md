# Task: Explain homepage Site Editor special case

## Goal
Explain why `objectID = 0` in `updateMeta` does not write normal post meta and what settings it updates instead.

## What to return
- trigger condition
- exact handler method
- fields mapped to homepage settings
- return payload shape
- why this matters for wrapper-plugin design

## Acceptance criteria
- cites `update_site_editor_homepage()`
- includes at least title, description, and one social field
- explains that settings storage differs from normal post meta
