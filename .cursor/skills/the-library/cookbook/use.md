# Use An Entry From The Library

## Purpose

Use this guide when the user wants to pull or refresh a skill, agent, or prompt from the catalog. In this repository, that means reading `library.yaml`, selecting the right entry, and then doing the requested copy or fetch steps explicitly.

## Steps

1. Read `.cursor/skills/the-library/library.yaml`.
2. Search the relevant catalog section for the requested entry:
   - `catalog.skills`
   - `catalog.agents`
   - `catalog.prompts` when this repo starts tracking prompts
3. If multiple matches are plausible, show the options and ask the user to choose.
4. Inspect the entry source:
   - Local file path: copy from the parent directory of the referenced file.
   - Pinned raw GitHub URL: fetch or clone only what is needed, then copy the referenced parent directory or file into the target Cursor path.
   - For skills, copy the whole parent directory, not just `SKILL.md`, so sibling docs such as `cookbook/*.md` stay intact.
5. Keep the destination Cursor-first:
   - Skills: `.cursor/skills/<name>/`
   - Agents: `.cursor/agents/`
   - Commands/prompts: `.cursor/commands/`
6. Verify that the copied target contains the main file (`SKILL.md`, `AGENT.md`, or prompt markdown file).
7. Report what was installed or refreshed, where it landed, and whether anything was overwritten.

## Guardrails

- Do not claim that a `/library use` command exists here unless the repo actually adds one.
- Only pull the entry the user asked for.
- Prefer pinned sources over loose repository references so the result is reproducible.
