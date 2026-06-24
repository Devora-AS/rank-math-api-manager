# Getting Started In Existing Projects

- Purpose: Explain how to add the multi-agent workflow to an already active repository with minimal disruption.
- Audience: Maintainers integrating this workflow into a codebase with existing conventions, branches, and CI.
- Prerequisites: Existing git repo, Cursor, ability to test changes safely, and familiarity with your current project build/test commands.
- Status: complete
- Last updated: 2026-06-24
- Author: Cursor agent (GPT-5.4)

## Related Files

- [Adoption safe defaults](adoption-safe-defaults.md) — conservative first-run profile (internal)
- [Root README](../README.md)
- [Agent instructions](../AGENTS.md)
- [Hook manifest](../.cursor/hooks.json)
- [Configuration](configuration.md)
- [Agent teams](agent-teams.md)
- [Workflows](orchestration-workflow.md)
- [Migration backlog](migration-backlog.md) - historical Stage 0 reference only; use `ROADMAP.md` for active work
- [Pilot report](pilot-report.md)
- [Artifacts index](artifacts-index.md)
- [Capability precedence](capability-precedence.md) — how project `.cursor/` relates to `.mat/`, plugins, and global defaults

## Sidecar mental model (MAT v1)

Bootstrap keeps **product-owned** README/CHANGELOG/AGENTS at the repo root when those files already exist. Full MAT reference material is written to **`.mat/`** (documentation under `.mat/docs/`, contract tests under `.mat/tests/`, and `.mat/AGENTS.mat.md`). The adoption helper adds a short pointer note to each detected product-owned `AGENTS.md` by default, computes the link relative to the file being edited, and leaves the inline delimited MAT section for an explicit `--inline-fallback` run. Root `docs/` only receives minimal workflow handoff files (`docs/current-plan.md`, `docs/long-run-state.md`) when missing.

## Migration Checklist

- [ ] Review the current repo layout and existing automation.
- [ ] Decide whether hooks should be enabled immediately or staged behind a feature branch.
- [ ] Copy `.cursor/agents`, `.cursor/commands`, `.cursor/hooks`, `.cursor/skills`, `hooks.json`, `mcp.json`, and `worktrees.json` (or run the bootstrap script, which installs them).
- [ ] Keep or merge your existing `AGENTS.md`; treat `.mat/AGENTS.mat.md` as the full MAT encyclopedia without replacing your product narrative file blindly.
- [ ] Merge `.env.sample` requirements into your existing secret management.
- [ ] Map the builder/verifier validation commands to your repo's real test and lint commands.
- [ ] Run a pilot workflow before enabling the setup for daily work.

## Safe Integration Steps

1. Create a dedicated integration branch.
2. Run the non-interactive adoption bootstrap from this workflow repo:

```bash
export MULTI_AGENT_WORKFLOW_ROOT=/absolute/path/to/multi-agent-workflow
bash "$MULTI_AGENT_WORKFLOW_ROOT/scripts/adoption/bootstrap-workflow-into-repo.sh" --mode existing-project --non-interactive "$(pwd)"
```

3. If your repo already has an older `docs/long-run-state.md`, run the upgrade helper in the adopted repo:

```bash
python3 scripts/adoption/migrate-long-run-state.py docs/long-run-state.md
```

4. If you need to refresh nested or monorepo `AGENTS.md` files after a repo layout change, run `python3 scripts/adoption/manage-agents-sidecars.py --repo-root .` from the adopted repo root.
5. Keep `CURSOR_VALIDATE_PROMPTS=false` and `CURSOR_DESKTOP_NOTIFICATIONS=false` until the basic hook flow is stable.
6. Verify hooks and slash commands in Cursor before enabling more aggressive validators.
7. Run a small orchestrated task rather than a large production change as the first trial.

The bootstrap preserves existing `docs/current-plan.md` and `docs/long-run-state.md` files when they already exist. Packaged MAT documentation is installed under **`.mat/docs/`** (not merged into your product `docs/` tree). Workflow contract tests ship under **`.mat/tests/`**; run them with `python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v` when you want MAT regression coverage in the adopted repo. The sidecar helper writes a temporary backup copy of each edited `AGENTS.md` before changing it, so recovered content stays available without polluting the repo.

The migration helper only auto-fixes the specific stale case where the mission section is missing `- **execution_mode:** \`long-run\`` or `short-run`; otherwise it exits non-zero with a remediation message so you can update the file deliberately.

## First adoption vs refresh

**First-time existing-project adoption requires bootstrap** (`bootstrap-workflow-into-repo.sh` above). A pristine `update-mat.py` dry-run on a repo without `.mat/AGENTS.mat.md` is expected to fail — run bootstrap first, then use `update-mat.py` for incremental refresh after the sidecar exists. See the [rank-math-api-manager adoption pilot](../artifacts/report/adoption-rank-math-api-manager-pilot-2026-06-24.md) (2026-06-24) for disposable evidence of that order.

## Refreshing MAT later

**Two honest paths:**

1. **`update-mat.py` (preferred for incremental drift)** — compares your adopted tree against a checked-out MAT **source** repo, shows a dry-run plan first, and can stage changes in an isolated worktree. It respects footprint rules for product-owned files; review `.cursorignore`, root `AGENTS.md`, and any product docs the diff touches before approving `--apply`. See [`docs/update-mat/index.md`](update-mat/index.md), [`docs/update-mat/architecture-and-rollout.md`](update-mat/architecture-and-rollout.md), and the slice 3 operator checklist in [`validation-report.md`](../validation-report.md).

2. **Re-run `bootstrap-workflow-into-repo.sh`** — overwrites **MAT-managed** paths from the layout manifest (`.cursor/` workflow bundle, `scripts/` copies, `.mat/docs/`, `.mat/tests/`, sidecar README, vendor README, `.env.sample`, etc.) while **preserving** existing root `README.md`, `CHANGELOG.md`, and `AGENTS.md` in `--mode existing-project`, and preserving `docs/current-plan.md` / `docs/long-run-state.md` when already present. It does **not** bulk-merge MAT’s full root `docs/` tree into your product docs. Bootstrap ends with **legacy cleanup**: `apply_mat_legacy_cleanup.py` reads `scripts/adoption/mat-legacy-migrations-v1.json`, retires known obsolete slash-command stubs when safe (fingerprint match or warn-only policy), and never removes paths listed in `scripts/adoption/mat-footprint-v1.json` `preserve_paths`. After either path, run `bash scripts/phase1-verify.sh` from the adopted repo root (it runs the **adopted** profile when `.mat/README.md` exists: packaged `.mat/tests`, explicit skips for unpackaged surfaces).

### Updater checklist (dry-run first)

Follow [`validation-report.md`](../validation-report.md) slice 3 — summary:

1. **Dry-run (default):** `python3 scripts/adoption/update-mat.py --source /absolute/path/to/multi-agent-workflow --ref main`
2. **Review:** `plan-file=`, `patch-file=`, `audit-file=`, compatibility snapshot, and `legacy_cleanup_preview` in the plan JSON.
3. **Resolve conflicts** and nested `AGENTS.md` ambiguity before apply (`manage-agents-sidecars.py` when needed).
4. **Apply staging only with explicit flags:** `--apply --approved --plan-file <plan.json>`.
5. **Inspect** `staging-worktree=` output; confirm **no new commit** on the target root.
6. **Manual commit/PR** — the updater stops before those steps ([`docs/adoption-safe-defaults.md`](adoption-safe-defaults.md)).

```bash
python3 scripts/adoption/update-mat.py --source /absolute/path/to/multi-agent-workflow --ref main
```

That command defaults to **dry-run** and prints a patch preview first. Review the summary, the compatibility snapshot from `scripts/adoption/mat-footprint-v1.json`, and the supporting bundle in [`docs/update-mat/`](update-mat/index.md). Confirm that the only project-owned edits are the `AGENTS.md` pointer or inline-fallback blocks handled by the sidecar helper, and only then rerun with `--apply --approved --plan-file <saved-plan.json>` to stage the update in an isolated worktree or branch-like path.

If the preview shows conflicts or nested `AGENTS.md` ambiguity, stop and resolve it manually before any commit or PR step. The updater intentionally **stops before commit or PR creation** so the operator can make the final call.

## Worktree Hints

Worktrees are the safest way to test parallel-agent behavior in an existing codebase. Create them **explicitly** (`git worktree`, Cursor `/worktree`, etc.); Cursor 3 does not silently add a git worktree per parallel agent. After each tree exists, run MAT bootstrap so `.cursor/worktree/runtime.env` records collision-aware `OBSERVABILITY_PORT` / `OBSERVABILITY_CLIENT_PORT` hints (see `.cursor/hooks/bootstrap_worktree.sh`).

```text
/mat-wt-create feature-multi-agent-docs
/mat-wt-list
```

Why this helps:

- Builder and verifier can run against isolated branches.
- Bootstrap can copy `.env` from the project root and keep observability hints in `runtime.env` separate from the main workspace.
- You can remove the experiment cleanly if needed.

## Suggested Roll-In Order

1. `AGENTS.md`
2. `.cursor/commands/`
3. `.cursor/agents/`
4. `.cursor/hooks.json` and `.cursor/hooks/`
5. `.cursor/worktrees.json`
6. Optional observability apps and TTS integrations — defer until the basic agent flow works; when you enable them, follow [`adoption-observability-appendix.md`](adoption-observability-appendix.md) for opt-in posture, `events.sqlite` gitignore, manual rotation, and shared-environment token guidance. For reproducible bootstrap + `update-mat.py` dry-run evidence, see the [adoption observability pilot report](../artifacts/report/adoption-observability-pilot-2026-06-23.md) (2026-06-23).

## Common Pitfalls

- Replacing existing repo instructions instead of merging them into `AGENTS.md`.
- Assuming Claude-specific task-board or messaging features exist in Cursor.
- Turning on stop-loop enforcement before builders and verifiers are tuned to your repo's real acceptance criteria.
- Forgetting that worktrees may need extra setup for databases, generated files, or package installs.
- Expecting PermissionRequest-like hooks; Cursor handles permission gating differently inside the runtime.

## Rollback Steps

If the integration causes friction, revert in this order:

1. Disable or remove `.cursor/hooks.json`.
2. Remove `.cursor/hooks/` if hook execution is the source of failures.
3. Keep `AGENTS.md` if it is still useful as human-readable guidance.
4. Remove or archive `.cursor/commands/` if you want to fall back to manual prompting.
5. Delete experimental worktrees with `/mat-wt-remove <branch>`.

## Practical Example

Trial the workflow on a documentation-only change first:

```text
/mat-plan-team Add a short integration guide for our API package
```

Verification targets:

- Hook logs appear in `logs/<session_id>/`.
- The parent produces `docs/current-plan.md`.
- The verifier report is readable and evidence-based.
- No unrelated project files are modified.

## Acceptance Checklist

- [ ] The workflow was introduced on an isolated branch or worktree.
- [ ] Existing project instructions in `AGENTS.md` were preserved or deliberately merged; `.mat/AGENTS.mat.md` holds the full MAT reference.
- [ ] A small pilot task completed with `build-result.md` and `verify-result.md`.
- [ ] Rollback is documented and tested at least once.
- [ ] Maintainers understand which parts are optional: observability apps, TTS, HITL, and external MCP integrations.
- [ ] If observability is enabled, operators read [`adoption-observability-appendix.md`](adoption-observability-appendix.md) (packaged to `.mat/docs/` on bootstrap/update) for manual rotation, gitignore surfaces, and RFU-7 deferral honesty.
