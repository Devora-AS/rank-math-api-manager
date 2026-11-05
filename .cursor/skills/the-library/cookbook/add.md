# Add A New Library Entry

## Purpose

Use this guide when the user wants to register a new skill, agent, or prompt source in the local catalog.

## Steps

1. Read `.cursor/skills/the-library/library.yaml`.
2. Determine the entry type from the file and user request:
   - `SKILL.md` usually means `catalog.skills`
   - `AGENT.md` usually means `catalog.agents`
   - Prompt markdown belongs in `catalog.prompts` once this repo starts using that section
3. Validate the source:
   - Local path points to a specific file.
   - GitHub source is a pinned raw or browser URL to a specific file.
4. Add the new entry under the correct catalog section with:
   - `id`
   - `name`
   - `description`
   - `source`
   - `install_path`
   - optional phase/status metadata when it helps this repo track adoption honestly
5. Keep the entry consistent with the existing Cursor-first catalog shape and pinned-source style.
6. Re-read the edited YAML to confirm formatting and field names are valid.
7. If the user asked for it, follow up by using the new entry via the `use` cookbook flow.

## Guardrails

- Do not convert the catalog into an auto-install manifest.
- Do not add invented fields that the rest of the local catalog does not use.
- If the source or ownership is ambiguous, stop and ask instead of guessing.
