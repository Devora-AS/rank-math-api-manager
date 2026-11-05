# Contributing

This repository ships a public WordPress plugin. Local development aids must stay out of commits, pull requests, and release artifacts unless the project owner explicitly asks for them.

## Private-Only Guardrail

Rule:

Do not commit private Cursor machine state (`.cursor/mcp.json`, `.cursor/settings.json`, `.cursor/cache/`, `.cursor/hooks/state/`), `agent-skills/` outside the tracked MAT surfaces below, `*.code-workspace`, `transcripts`, local notes, or other local agent artifacts unless explicitly requested by the project owner. Tracked MAT workflow surfaces under `.cursor/agents/`, `.cursor/commands/`, `.cursor/hooks/` (source only), `.cursor/rules/`, and `.cursor/skills/` are allowed after owner opt-in via mat-sync gitignore merge.

Scope:

- all commits
- all pull requests
- all automated suggestions
- all release packages

Reviewer verification:

- Check the PR file list for forbidden paths before approval.
- Block the PR if any forbidden path is present without explicit owner approval.
- Confirm the PR checklist line for forbidden files is checked.

## Cursor / MAT workflow

This repo uses a tracked MAT sidecar (`.mat/`, `scripts/phase1-verify.sh`, `AGENTS.md` pointer) plus selectively tracked MAT workflow surfaces under `.cursor/` (agents, commands, hooks source, rules, skills). Private machine files (`.cursor/mcp.json`, settings, cache, hook state) stay gitignored. After clone, run `bash scripts/doctor.sh` (and `/mat-sync` when refreshing from upstream). Incremental MAT template updates use `scripts/mat-sync.sh` / `scripts/adoption/update-mat.py` (dry-run first); `--approve-plan` / `--apply` are optional and separate from plugin releases. See `docs/mat-adoption-notes.md` and `.mat/source-config.json` (v2).

## Review Documents

Use these documents when reviewing or preparing changes:

- `docs/rules/REST_CHECKLIST.md`
- `docs/rules/SECURITY_CHECKLIST.md`
- `docs/rules/PACKAGING.md`
- `docs/rules/AGENT_SCOPE.md`
- `docs/rules/DOCUMENTATION_GUIDE.md`

Reviewer verification:

- Confirm the PR template sections that apply to the change are filled out.
- If an endpoint, auth flow, payload, packaging rule, or agent doc changes, confirm the matching guidance file is followed or updated in the same PR.
