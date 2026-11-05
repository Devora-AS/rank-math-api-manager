# The Library

**Source:** disler/the-library
**Status:** Translated for Cursor (install paths updated; catalog sources pinned; local cookbooks added)
**Phase:** Stage 7 (Optional enhancement)

---

## Purpose

The Library is a meta-skill for private-first distribution of skills, agents, and
prompts across your agents, devices, and teams. Use it to install curated skill
catalogs from a central `library.yaml` manifest.

---

## Usage

In Cursor, activate this skill by referencing it in a command or agent prompt:

```
Use the library skill to install [skill-name] from the catalog.
```

This repository does not currently ship a `/library` slash command. Use this skill by referencing it from prompts until an explicit command is added.

## Cookbook

Read the matching local cookbook before acting on a library request. These guides adapt the upstream `disler/the-library` flows to this repository's Cursor-first reality: prompt-driven/manual steps, pinned file sources, and no bundled `/library` automation.

If you distribute this skill from `library.yaml`, copy the entire parent skill directory, not only `SKILL.md`, because the cookbook docs live beside it. If you are reading a single-file copy, use the GitHub fallback links below.

| Workflow | Local cookbook | Use when |
| --- | --- | --- |
| install | `cookbook/install.md` ([GitHub](https://github.com/Devora-AS/multi-agent-workflow/blob/main/.cursor/skills/the-library/cookbook/install.md)) | You want to adopt the library pattern in a new Cursor repo or on another machine. |
| use | `cookbook/use.md` ([GitHub](https://github.com/Devora-AS/multi-agent-workflow/blob/main/.cursor/skills/the-library/cookbook/use.md)) | You want to pull or refresh a skill from the catalog into this repo. |
| add | `cookbook/add.md` ([GitHub](https://github.com/Devora-AS/multi-agent-workflow/blob/main/.cursor/skills/the-library/cookbook/add.md)) | You want to register a new skill/agent/prompt source in `library.yaml`. |
| list | `cookbook/list.md` ([GitHub](https://github.com/Devora-AS/multi-agent-workflow/blob/main/.cursor/skills/the-library/cookbook/list.md)) | You want to inspect the catalog and see what is already represented locally. |
| search | `cookbook/search.md` ([GitHub](https://github.com/Devora-AS/multi-agent-workflow/blob/main/.cursor/skills/the-library/cookbook/search.md)) | You know the capability you want, but not the exact catalog entry name. |

## Cursor-First Operating Rules

- Treat `library.yaml` as a catalog of available items, not an auto-installed manifest.
- Keep install targets Cursor-first: `.cursor/skills/`, `.cursor/agents/`, and `.cursor/commands/`.
- Prefer pinned raw file URLs or explicit local file paths for sources so catalog entries stay auditable.
- Only perform fetch/copy/git steps the user actually asked for; this repo ships the pattern, not a background sync daemon.
- `push`, `remove`, and `sync` remain upstream concepts, but this repository does not yet ship local cookbook automation for them.

---

## Install Path (Cursor-First)

Skills are installed to `.cursor/skills/` by default (translated from `.claude/skills/`).

```yaml
# library.yaml default_install_dir:
default_install_dir: .cursor/skills/
```

---

## Skill Catalog

See `library.yaml` for the full catalog of available skills and their pinned source files.

---

## Notes

- Translated from: disler/the-library SKILL.md
- Original install path `.claude/skills/` → Updated to `.cursor/skills/`
- This repository does not currently ship a `/library` slash command; invoke the skill from prompts until one is intentionally added.
- Full activation requires Stage 6 pilot to pass and Stage 7 go-criteria to be met
  (see `docs/reference/decision-record.md → Optional Enhancement 2: The Library`)
