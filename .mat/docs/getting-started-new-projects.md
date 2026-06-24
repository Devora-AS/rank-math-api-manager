# Getting Started In New Projects

- Purpose: Show how to install this Cursor-native multi-agent workflow into a brand new repository.
- Audience: Developers bootstrapping a fresh project.
- Prerequisites: A new project folder, Git, Cursor, Python 3, and any runtime dependencies used by your target codebase.
- Status: complete
- Last updated: 2026-04-16
- Author: Cursor agent (GPT-5.4)

## Missing Prerequisites

- In **this MAT reference repository**, `apps/server/package.json` and `apps/client/package.json` define the Bun/Vue observability stack. In a **brand-new empty repo** you adopt into, copy those app trees (or equivalent manifests) from your runnable source of truth before expecting `bun install` in those paths to work.

## Related Files

- [Adoption safe defaults](adoption-safe-defaults.md) — conservative first-run profile (internal)
- [Root README](../README.md)
- [Agent instructions](../AGENTS.md)
- [Hook manifest](../.cursor/hooks.json)
- [Configuration](configuration.md)
- [Components](components.md) (MAT reference repo); in an adopted repo, the packaged copy is under `.mat/docs/components.md`.
- [Inventory](inventory.json)
- [Migration backlog](migration-backlog.md) - historical Stage 0 reference only; use `ROADMAP.md` for active work
- [Pilot report](pilot-report.md)
- [Artifacts index](artifacts-index.md)
- [Capability precedence](capability-precedence.md) — project-first routing when mixing global, plugin, and `.mat/` assets

## Prerequisites

- A git repository initialized with `main` or your preferred base branch.
- Cursor configured to load project `.cursor/commands`, `.cursor/agents`, `.cursor/skills`, and project hooks.
- API keys as needed:
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - `ELEVENLABS_API_KEY` (optional)
- Optional local tools for validators and formatting:
  - `ruff`
  - `ty`, `pyright`, or your preferred type checker
  - `prettier` for JS/TS formatting

## Recommended Project Layout (MAT v1 sidecar)

Product identity stays at the repository root. MAT-packaged manuals and workflow contract tests live under **`.mat/`** so they do not compete with your product `docs/` tree. New-project bootstrap writes a product-first `AGENTS.md` that points at `.mat/AGENTS.mat.md`; use the helper's `--inline-fallback` flag only when you explicitly want the delimited inline MAT section in a particular file.

```text
your-project/
  .cursor/
    agents/
    commands/
    hooks/
    skills/
    hooks.json
    mcp.json
    worktrees.json
  .mat/
    README.md
    docs/           # packaged MAT workflow documentation
    tests/          # workflow unittest modules (contract tests)
    AGENTS.mat.md   # full MAT operator reference (from source AGENTS.md)
  AGENTS.md         # product-first; points at .mat/ for deep reference
  .env.sample
  docs/             # minimal workflow handoffs only: current-plan, long-run-state
```

## Installation Steps

1. Initialize the new repository with your normal starter files (`README.md`, optional `LICENSE`, language/runtime files).
2. Run the non-interactive bootstrap from this workflow repo:

```bash
export MULTI_AGENT_WORKFLOW_ROOT=/absolute/path/to/multi-agent-workflow
bash "$MULTI_AGENT_WORKFLOW_ROOT/scripts/adoption/bootstrap-workflow-into-repo.sh" --mode new-project --non-interactive "$(pwd)"
```

3. Review the copied workflow assets and adapt `AGENTS.md` plus `.env.sample` for your project.
4. If the repo later grows nested packages or services with their own `AGENTS.md` files, rerun `python3 scripts/adoption/manage-agents-sidecars.py --repo-root .` to refresh the relative sidecar pointers without overwriting product-owned content.
5. Decide whether to include the observability apps immediately or defer them until after the basic agent flow works. When you enable them later, use [`adoption-observability-appendix.md`](adoption-observability-appendix.md) for opt-in enablement, `events.sqlite` storage, manual rotate/prune, gitignore expectations, and shared `OBSERVABILITY_API_TOKEN` guidance (packaged to `.mat/docs/` on bootstrap/update). For reproducible bootstrap + dry-run evidence, see the [adoption observability pilot report](../artifacts/report/adoption-observability-pilot-2026-06-23.md) (2026-06-23).

The bootstrap creates a curated workflow surface: `.cursor/commands/`, `.cursor/agents/`, hook/config files, root `docs/current-plan.md` and `docs/long-run-state.md` (minimal MAO/mat-long-run handoffs), **`.mat/docs/`** for packaged MAT documentation, and **`.mat/tests/`** for workflow contract tests. Run those tests with:

`python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v`

If you later want to refresh the MAT-owned workflow files from upstream, use `python3 scripts/adoption/update-mat.py --source <upstream-repo-or-url> --ref <ref>` and inspect the **dry-run** diff first (default mode). Existing project-owned `AGENTS.md` content still stays under the sidecar helper’s control, and the updater's contract bundle lives in [`docs/update-mat/`](update-mat/index.md). For the full operator checklist (dry-run → review → apply staging → manual commit), see [`validation-report.md`](../validation-report.md) slice 3 and [`docs/adoption-safe-defaults.md`](adoption-safe-defaults.md).

## Environment Variables

Start from `.env.sample` and fill at least the values you intend to use:

```bash
cp .env.sample .env
```

Important variables:

| Variable | Required | Why it matters |
|----------|----------|----------------|
| `OBSERVABILITY_SERVER_URL` | Recommended | Tells hooks where to POST events. |
| `ANTHROPIC_API_KEY` | Optional | Enables Anthropic-backed summaries and agent naming. |
| `OPENAI_API_KEY` | Optional | Enables OpenAI-backed summaries and TTS. |
| `ELEVENLABS_API_KEY` | Optional | Enables ElevenLabs TTS. |
| `CURSOR_DESKTOP_NOTIFICATIONS` | Optional | Enables macOS stop notifications. |
| `CURSOR_STORE_PROMPTS` | Optional | Persists prompts to `.cursor/data/sessions/`. |
| `CURSOR_NAME_AGENT` | Optional | Generates session agent names. |
| `CURSOR_VALIDATE_PROMPTS` | Optional | Turns on prompt blocking rules. |
| `CURSOR_HOOKS_LOG_DIR` | Optional | Overrides the default `logs/` directory. |

## Starting The Stack

If you copied the observability applications and they are runnable in your project:

```bash
cd apps/server && bun install && bun run dev
cd apps/client && bun install && bun run dev
```

Then open the project in Cursor and run:

```text
/mat-prime
/mat-plan-team Build a tiny smoke-test feature for this new project
```

## Verifying The Setup

Check these in order:

1. `.cursor/hooks.json` loads without Cursor errors.
2. Slash commands appear from `.cursor/commands/`.
3. `docs/current-plan.md` and `docs/long-run-state.md` were created by the bootstrap.
4. `logs/<session_id>/user_prompts.json` appears after the first prompt.
5. `build-result.md` and `verify-result.md` appear after `/mat-plan-team`.
6. If the observability stack is running, events appear from `.cursor/hooks/send_event.py`.

## Practical Example

For a brand new Python project:

```text
/mat-plan-team Create a hello-world module with tests and verify it
```

Expected outcome:

- The parent writes `docs/current-plan.md`.
- The builder implements the module and writes `build-result.md`.
- The verifier writes `verify-result.md`.
- Hook logs are created in `logs/<session_id>/`.

## Common Setup Mistakes

- Copying `commands/` and `agents/` without `hooks.json`.
- Forgetting to add `.env`, then expecting summaries or TTS to work.
- Enabling prompt validation before defining blocked patterns in `before_submit_prompt.py`.
- Assuming worktree bootstrap or observability apps are complete without checking their local runtime dependencies.

## Acceptance Checklist

- [ ] The new repo contains `.cursor/agents`, `.cursor/commands`, `.cursor/hooks`, `.cursor/skills`, `.mat/` (docs + tests + `AGENTS.mat.md`), `AGENTS.md`, and `.env.sample`.
- [ ] Cursor recognizes the slash commands.
- [ ] A first `/mat-prime` or `/mat-plan-team` prompt produces log files in `logs/`.
- [ ] `docs/current-plan.md`, `build-result.md`, and `verify-result.md` are created during an orchestrated run.
- [ ] Optional observability endpoints work if `apps/server` and `apps/client` were installed.
