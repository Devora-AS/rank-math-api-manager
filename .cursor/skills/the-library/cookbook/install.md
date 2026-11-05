# Install The Library Pattern In Cursor

## Purpose

Use this guide when you want to adopt the library pattern in a Cursor repo or on another machine. This repository already includes a translated local copy under `.cursor/skills/the-library/`; there is no bundled `/library install` command.

## What this does

- Verifies that the translated skill and catalog exist locally.
- Confirms Cursor-first install paths.
- Gives a manual bootstrap path for teams that want their own private library repo.

## Steps

1. Verify the local translated files exist:
   - `.cursor/skills/the-library/SKILL.md`
   - `.cursor/skills/the-library/library.yaml`
2. Confirm the catalog paths are Cursor-first in `library.yaml`:
   - `default_install_dir: .cursor/skills/`
   - `agent_dir: .cursor/agents/`
   - `commands_dir: .cursor/commands/`
3. If you want a private shared library repo, clone or create that repo separately and point its catalog entries at pinned file sources.
4. Keep the local skill translated for Cursor wording and paths before sharing it with another repo or machine.
5. Verify the setup by reading `SKILL.md`, `library.yaml`, and one cookbook file from this directory.

## Notes

- This repo ships the pattern and documentation, not a one-shot installer.
- If you later add explicit automation, document it separately instead of implying it already exists.
