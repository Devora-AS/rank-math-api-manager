# Search The Library Catalog

## Purpose

Use this guide when the user knows the capability they want, but not the exact catalog entry name.

## Steps

1. Read `.cursor/skills/the-library/library.yaml`.
2. Search case-insensitively across each entry's:
   - `name`
   - `description`
   - optionally `id` when that helps resolve near-matches
3. Return the best matches grouped by type.
4. If nothing matches, say so directly and suggest broader keywords or a full catalog listing.
5. If the user chooses a result, continue with the `use` cookbook flow.

## Output suggestion

Format matches as a short table with:

- Type
- Name
- Description
- Source

## Guardrails

- Search the actual catalog contents, not remembered assumptions.
- Do not say "run `/library search`" as if the command already exists in this repo.
