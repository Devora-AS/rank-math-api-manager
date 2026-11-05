# List The Local Library Catalog

## Purpose

Use this guide when the user wants to inspect what the local catalog knows about without modifying anything.

## Steps

1. Read `.cursor/skills/the-library/library.yaml`.
2. Group entries by section:
   - `catalog.skills`
   - `catalog.agents`
   - `catalog.prompts` if present
3. For each entry, report:
   - Name
   - Description
   - Source
   - Install path
   - Status or phase when present
4. If the user asks which items are already present locally, compare the catalog install paths with the working tree and report only what you actually observe.
5. Summarize totals by section.

## Output suggestion

Use a small grouped table or flat bullet list. Prefer accuracy over a fully automated "installed/not installed" claim if the repo does not currently maintain that state explicitly.

## Guardrails

- Do not imply that `/library list` is a built-in command here.
- Do not claim install status unless you checked the relevant path.
