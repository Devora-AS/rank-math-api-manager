# Getting Started In Existing Projects

- Purpose: Explain how to add the multi-agent workflow to an already active repository with minimal disruption.
- Audience: Maintainers integrating this workflow into a codebase with existing conventions, branches, and CI.
- Prerequisites: Existing git repo, Cursor, ability to test changes safely, and familiarity with your current project build/test commands.
- Status: complete
- Last updated: 2026-10-16
- Author: Cursor agent (GPT-5.4)

## Related Files

- [Adoption safe defaults](guides/adoption-safe-defaults.md) — conservative first-run profile (internal)
- [MAT sync team runbook](guides/mat-sync-team-runbook.md) — GitHub-first plan → approve playbook
- [Root README](../../README.md)
- [Agent instructions](../../AGENTS.md)
- [Hook manifest](../../.cursor/hooks.json)
- [Configuration](configuration.md)
- [Agent teams](agent-teams.md)
- [Workflows](orchestration-workflow.md)
- [Migration backlog](../archive/migration-backlog.md) - historical Stage 0 reference only; use `ROADMAP.md` for active work
- [Pilot report](../archive/pilot-report.md)
- [Artifacts index](artifacts-index.md)
- [Capability precedence](capability-precedence.md) — how project `.cursor/` relates to `.mat/`, plugins, and global defaults
- [Environment write contract](env-write-contract.md) — which routes may touch live `.env` / `.mat.env` vs samples only (CI fail-closed)
- [MAT operator playbook](guides/mat-operator-playbook.md) — shipped-capability working habits (MAO, verify profiles, mat-sync vs plugin, env ownership)

## Sidecar mental model (MAT v1)

Bootstrap (via mat-sync approve or maintainer/debug bootstrap) keeps **product-owned** README/CHANGELOG/AGENTS at the repo root when those files already exist. Full MAT reference material is written to **`.mat/`** (documentation under `.mat/docs/`, contract tests under `.mat/tests/`, and `.mat/AGENTS.mat.md`). The adoption helper adds a short pointer note to each detected product-owned `AGENTS.md` by default, computes the link relative to the file being edited, and leaves the inline delimited MAT section for an explicit `--inline-fallback` run. Root `docs/` only receives minimal workflow handoff files (`docs/current-plan.md`, `docs/architecture/long-run-state.md`) when missing.

**Packaged docs honesty:** Operator-facing guides under **`.mat/docs/`** (including a copy of this file) refresh on **bootstrap or rebootstrap** approve (full layout copy). **Incremental** `update-mat.py` dry-run → apply also updates individual **`.mat/docs/`** mappings when upstream differs — review `changed_files` / plan JSON before `--apply`. Until you run incremental apply or rebootstrap, product trees may carry an older `.mat/docs/` snapshot even when MAT source docs are newer.

**`.mat.env.sample` merge (not wholesale overwrite):** When the product repo already customizes `.mat.env.sample`, MAT uses **`# ─── MAT-tool ───` … `# ─── /MAT-tool ───`** markers. Plan JSON includes **`env_sample_merge_preview`** (`path`: `.mat.env.sample`); approve/bootstrap and incremental apply replace **only** the MAT-tool block from upstream and preserve customized lines outside the markers. Root **`.env.sample`** stays product-only. MAT does **not** auto-merge live **`.env`** or **`.mat.env`** — copy values from the samples manually after merge. Full route table, intentional writers (`setup-dev.sh`, worktree `--copy-env`), read vs write, and **M1** deferred hook-unification note: [`env-write-contract.md`](env-write-contract.md). CI regression: `tests/test_adopt_env_write_contract.py` (**fail closed** on live-env mutation during adopt/update paths).

**Loop policy (opt-in):** Bootstrap ships advisory loop templates under **`.mat/loop/`** (`constraints.md`, `budget.md`). Enable orchestrated loops with `CURSOR_MAT_LOOP_POLICY=1`; see MAT source [`loop-policy.md`](loop-policy.md) or run `bash scripts/doctor.sh --loop-policy` on the source tree for a non-fatal diagnostic.

## Migration Checklist

- [ ] Review the current repo layout and existing automation.
- [ ] Decide whether hooks should be enabled immediately or staged behind a feature branch.
- [ ] Run **first adoption** via mat-sync plan → approve from the MAT source repo (primary) or maintainer/debug bootstrap when routing requires it.
- [ ] Keep or merge your existing `AGENTS.md`; treat `.mat/AGENTS.mat.md` as the full MAT encyclopedia without replacing your product narrative file blindly.
- [ ] Merge `.env.sample` and `.mat.env.sample` into your secret management (MAT-tool marker merge on `.mat.env.sample` preserves customized MAT sample lines; live `.env` / `.mat.env` stay operator-owned).
- [ ] Map the builder/verifier validation commands to your repo's real test and lint commands (edit `.mat/adoption-profile.json` → `validation_commands.builder_verify` when the bootstrap scaffold is empty).
- [ ] Run a pilot workflow before enabling the setup for daily work.

## Safe Integration Steps

1. Create a dedicated integration branch.

2. **Primary — first adoption via `/mat-adopt`, `mat-adopt.sh`, or mat-sync** (from the **MAT source** repo for chat/slash; shell `mat-adopt.sh` works zero-checkout with `--repository`):

**Chat entry (recommended):** run **[`/mat-adopt`](../../.cursor/commands/mat-adopt.md)** from the MAT source workspace and name the product repo path. The orchestrator walks plan → review preflight/previews → approve with one copy-paste `txt` block per step.

**Zero-checkout shell (pin upstream by ref):**

```txt
curl -fsSL "https://raw.githubusercontent.com/Devora-AS/multi-agent-workflow/main/scripts/adoption/mat-adopt.sh" \
  -o /tmp/mat-adopt.sh
bash /tmp/mat-adopt.sh --repo-root "/path/to/product-repo" \
  --repository Devora-AS/multi-agent-workflow --ref main
# review mat-sync-plan-file=… then approve with the same --repository/--ref:
bash /tmp/mat-adopt.sh --repo-root "/path/to/product-repo" \
  --repository Devora-AS/multi-agent-workflow --ref main \
  --approve-plan "/path/to/product-repo/artifacts/mat-sync/latest-plan.json"
```

Replace `main` with a tag or SHA for reproducible first adoption. Raw `main` tracks upstream tip — review the plan JSON before approve.

**Shell entry from MAT source checkout (same semantics):**

```txt
cd "/path/to/multi-agent-teams"
bash scripts/adoption/mat-adopt.sh --repo-root "/path/to/product-repo" \
  --repository Devora-AS/multi-agent-workflow --ref main
bash scripts/adoption/mat-adopt.sh --repo-root "/path/to/product-repo" \
  --repository Devora-AS/multi-agent-workflow --ref main \
  --approve-plan "/path/to/product-repo/artifacts/mat-sync/latest-plan.json"
```

MAT source resolves from `--repository` (v2 semantics) when the product repo has no `.mat/source-config.json` yet. After approve, confirm `.mat/README.md`, `.mat/AGENTS.mat.md`, `.mat/source-config.json`, and `.mat/adoption-profile.json` exist in the product repo.

**Slash command honesty:** **`/mat-sync`** is **not** available inside an un-adopted product repo — Cursor slash commands ship with the adopted `.cursor/commands/` bundle. Until first approve completes, run **`/mat-adopt`** from the MAT source workspace, **`mat-adopt.sh`** with `--repository` (zero-checkout), or `scripts/mat-sync.sh` from the MAT source checkout with `--repo-root`. See [`.cursor/commands/mat-adopt.md`](../../.cursor/commands/mat-adopt.md).

3. If your repo already has an older `docs/long-run-state.md` at the repo root, run the upgrade helper to migrate it to `docs/architecture/long-run-state.md`:

```bash
python3 scripts/adoption/migrate-long-run-state.py docs/long-run-state.md
```

4. If you need to refresh nested or monorepo `AGENTS.md` files after a repo layout change, run `python3 scripts/adoption/manage-agents-sidecars.py --repo-root .` from the adopted repo root.
5. Keep `CURSOR_VALIDATE_PROMPTS=false` and `CURSOR_DESKTOP_NOTIFICATIONS=false` until the basic hook flow is stable.
6. Verify hooks and slash commands in Cursor before enabling more aggressive validators.
7. Run a small orchestrated task rather than a large production change as the first trial.

First adoption preserves existing `docs/current-plan.md` and `docs/architecture/long-run-state.md` files when they already exist. Packaged MAT documentation is installed under **`.mat/docs/`** (not merged into your product `docs/` tree). Workflow contract tests ship under **`.mat/tests/`**; run them with `python3 -m unittest discover -s .mat/tests -p 'test_*.py' -v` when you want MAT regression coverage in the adopted repo. The sidecar helper writes a temporary backup copy of each edited `AGENTS.md` before changing it, so recovered content stays available without polluting the repo.

The migration helper only auto-fixes the specific stale case where the mission section is missing `- **execution_mode:** \`long-run\`` or `short-run`; otherwise it exits non-zero with a remediation message so you can update the file deliberately.

### Maintainer/debug fallback — raw bootstrap

When mat-sync routing fails, you need a minimal repro outside the state machine, or you are developing adoption layout changes in the MAT source repo, use raw bootstrap **only** as a maintainer/debug path — **not** the team default:

```bash
export MULTI_AGENT_WORKFLOW_ROOT=/absolute/path/to/multi-agent-workflow
bash "$MULTI_AGENT_WORKFLOW_ROOT/scripts/adoption/bootstrap-workflow-into-repo.sh" --mode existing-project --non-interactive "$(pwd)"
```

Prefer mat-sync plan → approve for production first adoption; raw bootstrap does not replace dry-run review, conflict routing, or verify phases that mat-sync provides.

## First adoption vs refresh

**Primary first-time existing-project adoption:** **mat-sync plan → approve** from the MAT source repo with `--repo-root` and `--repository` (v2). See [`mat-sync-team-runbook.md`](guides/mat-sync-team-runbook.md) § First adoption / refresh with source-config v2.

A pristine `update-mat.py` dry-run on a repo without `.mat/AGENTS.mat.md` is expected to fail — complete first adoption via mat-sync or maintainer/debug bootstrap before pristine `update-mat.py` dry-run. See [`docs/pilot/pilot-existing/README.md`](../pilot/pilot-existing/README.md) for adoption pilot evidence and sidecar-before-updater order.

## Refreshing MAT later

**Production default (team):** After first adoption, **`.mat/source-config.json` v2** (`repository` + `ref`) lets **`/mat-sync`** / [`scripts/mat-sync.sh`](../../scripts/mat-sync.sh) materialize upstream from GitHub — no maintainer-local MAT checkout. Full playbook: [`mat-sync-team-runbook.md`](guides/mat-sync-team-runbook.md).

```txt
cd "/path/to/adopted-repo"
bash scripts/mat-sync.sh --repo-root "$(pwd)"
# review mat-sync-plan-file=… then:
bash scripts/mat-sync.sh --repo-root "$(pwd)" \
  --approve-plan "$(pwd)/artifacts/mat-sync/latest-plan.json"
```

**IDE entry (adopted repos only):** **`/mat-sync`** ([`.cursor/commands/mat-sync.md`](../../.cursor/commands/mat-sync.md)) or **`/mat-update-mat`** ([`.cursor/commands/mat-update-mat.md`](../../.cursor/commands/mat-update-mat.md)) for guided detect → route → plan → approve → verify. Prefer `/mat-sync` when v2 config is present. These slash commands exist only after the adopted `.cursor/commands/` bundle is installed.

**`.gitignore` (Omniroute-class and directory-ignore repos):** When the product `.gitignore` broadly ignores `.cursor` workflow paths, review **`preflight.gitignore_blockers`**, **`preflight.gitignore_workflow_untrackable`**, **`gitignore_rewrite_preview`**, and **`gitignore_merge_preview`** in the mat-sync plan JSON before approve.

| Pattern shape | Negations alone? | MAT approve behavior |
|---------------|------------------|----------------------|
| **`.cursor/*`** (contents-ignore; Omniroute-class) | Yes — directory is walkable; append MAT negations | Append marked `# BEGIN MAT git tracking` block only |
| **`.cursor/`**, **`.cursor/**`**, **`**/.cursor/`** (directory-ignore) | **No** — git never evaluates child `!` negations | **Rewrite** matched line to `.cursor/*` (or `**/.cursor/*`), then append negations |

Non-empty **`gitignore_merge_preview`** means mat-sync will append a marked block on **`--approve-plan`** (all routes) so MAT workflow paths (`.cursor/agents/`, `commands/`, `hooks/`, etc.) become trackable. When **`gitignore_rewrite_preview`** is non-empty, approve applies a **surgical single-line rewrite** first (previewed in plan JSON; never bulk-replaces the product file). Bootstrap/rebootstrap stderr prints `preflight: gitignore blockers detected: …` when blockers are present (subtype-specific: append negations vs rewrite-then-append). **`phase_verify`** fails closed when `git check-ignore` still matches workflow probe paths after approve — skip with `MAT_SYNC_SKIP_GITIGNORE_TRACKABILITY=1` only for debugging.

**Manual check (after approve or hand-fix):** `git check-ignore -v .cursor/hooks.json` must exit **non-zero** (path trackable). Manual hand-editing `.gitignore` is a **fallback** when previews are empty or you need product-specific exceptions beyond the template fragment.

**Preflight inventory (custom extensions):** Review **`preflight.custom_skills`**, **`preflight.custom_agents`**, and **`preflight.custom_commands`** in the plan JSON — each lists product-owned paths not in the MAT baseline (skills are directory names under `.cursor/skills/`). When **`preflight.env_sample_blocked_by`** is non-empty, `.env.sample` would be git-ignored today; the `gitignore_merge_preview` fragment includes `!.env.sample` negations on approve when eligible.

**Three honest paths:**

1. **`mat-sync.sh` (preferred for adopted repos with v2 config)** — GitHub-first detect → route → plan → approve → verify. Dry-run by default; mutations only with `--approve-plan`. See [`mat-sync-team-runbook.md`](guides/mat-sync-team-runbook.md).

2. **`update-mat.py` (incremental drift; maintainer dev or explicit `--source`)** — compares your adopted tree against a resolved MAT checkout (from v2 materialize or local `--source`), shows a dry-run plan first, and can stage changes in an isolated worktree. Incremental apply refreshes **`.mat/docs/`** mappings and merges **`.mat.env.sample`** via MAT-tool markers (not blind overwrite). Plan JSON includes **`env_sample_merge_preview`** when the MAT sample is customized. It respects footprint rules for product-owned files; review `.cursorignore`, root `AGENTS.md`, and any product docs the diff touches before approving `--apply`. See [`docs/update-mat/index.md`](update-mat/index.md), [`docs/update-mat/architecture-and-rollout.md`](update-mat/architecture-and-rollout.md), and the slice 3 operator checklist in [`validation-report.md`](../../validation-report.md).

3. **Re-run mat-sync with `rebootstrap` route or maintainer/debug `bootstrap-workflow-into-repo.sh`** — overwrites **MAT-managed** paths from the layout manifest (`.cursor/` workflow bundle, `scripts/` copies, `.mat/docs/`, `.mat/tests/`, sidecar README, vendor README, `.mat.env.sample`, product `.env.sample` when missing, etc.) while **preserving** existing root `README.md`, `CHANGELOG.md`, and `AGENTS.md` in `--mode existing-project`, and preserving `docs/current-plan.md` / `docs/architecture/long-run-state.md` when already present. It does **not** bulk-merge MAT's full root `docs/` tree into your product docs. Bootstrap ends with **legacy cleanup**: `apply_mat_legacy_cleanup.py` reads `scripts/adoption/mat-legacy-migrations-v1.json`, retires known obsolete slash-command stubs when safe (fingerprint match or warn-only policy), and never removes paths listed in `scripts/adoption/mat-footprint-v1.json` `preserve_paths`. After either path, run `bash scripts/phase1-verify.sh` from the adopted repo root (it runs the **adopted_operational** profile when `.mat/README.md` exists: workflow validation, cost-hygiene, hooks/surfaces — **skips** `.mat/tests` by default with a visible banner; set **`PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1`** to run packaged contract tests). If your tree still tracks MAT runtime noise (`__pycache__/`, `.cursor/hooks/state/`, `.cursor/settings.json`, `artifacts/`), merge the latest `docs/templates/cursorignore-mat-*` fragments into root `.cursorignore` or re-bootstrap when safe.

### Updater checklist (dry-run first)

Follow [`validation-report.md`](../../validation-report.md) slice 3 — summary:

1. **Dry-run (default):** from adopted repo with v2 config, `bash scripts/mat-sync.sh --repo-root "$(pwd)"`; or `python3 scripts/adoption/update-mat.py --repo-root "$(pwd)"` when mat-sync has already materialized upstream (omit `--source` when v2 config resolves). Maintainer dev: add `--source /path/to/MAT-source --ref main`.
2. **Review:** `plan-file=`, `patch-file=`, `audit-file=`, compatibility snapshot, and `legacy_cleanup_preview` in the plan JSON.
3. **Resolve conflicts** and nested `AGENTS.md` ambiguity before apply (`manage-agents-sidecars.py` when needed).
4. **Apply staging only with explicit flags:** `--apply --approved --plan-file <plan.json>`.
5. **Inspect** `staging-worktree=` output; confirm **no new commit** on the target root.
6. **Manual commit/PR** — the updater stops before those steps ([`docs/guides/adoption-safe-defaults.md`](guides/adoption-safe-defaults.md)).
7. **Staging vs live tree:** `update-mat.py --apply` writes MAT-managed paths under **`staging-worktree=`** only. Your **live product checkout** (`--repo-root`) is unchanged until you review the staging tree and promote (copy, `rsync`, or merge) into the live root, then commit. `mat-sync` **`update_dry_run` approve** runs the same staging apply plus optional `.gitignore` / `.mat.env.sample` merges on the **live** root — it still does **not** auto-copy the full staging tree into place. To verify **staged** output before promotion, run from the staging path: `PHASE1_VERIFY_ADOPTED_CONTRACT_TESTS=1 bash scripts/phase1-verify.sh` (and `python3 scripts/validate_doc_links.py --profile adopted-sidecar --repo-root <staging>` when the validator is packaged). To verify the **live** tree after promotion, run the same commands from your product repo root.

```bash
bash scripts/mat-sync.sh --repo-root "$(pwd)"
```

That command defaults to **dry-run** (plan JSON under `artifacts/mat-sync/`). For raw updater dry-run with explicit local checkout:

```bash
python3 scripts/adoption/update-mat.py --source /path/to/MAT-source --ref main --repo-root "$(pwd)"
```

The updater path defaults to **dry-run** and prints a patch preview first. Review the summary, the compatibility snapshot from `scripts/adoption/mat-footprint-v1.json`, and the supporting bundle in [`docs/update-mat/`](update-mat/index.md). Confirm that the only project-owned edits are the `AGENTS.md` pointer or inline-fallback blocks handled by the sidecar helper, and only then rerun with `--apply --approved --plan-file <saved-plan.json>` to stage the update in an isolated worktree or branch-like path.

If the preview shows conflicts or nested `AGENTS.md` ambiguity, stop and resolve it manually before any commit or PR step. The updater intentionally **stops before commit or PR creation** so the operator can make the final call.

## Worktree Hints

Worktrees are the safest way to test parallel-agent behavior in an existing codebase. Prefer Cursor managed worktrees (Agents Window), `/worktree`, `/best-of-n`, or manual `git worktree` / `/mat-wt-create`. Cursor does not invent a tree for every parallel Task subagent without those flows. After each tree exists, run MAT bootstrap — default `--metadata-only` writes `.cursor/worktree/runtime.env` without package/network calls; use `--install --copy-env` when deps and env copy are intentional (see `.cursor/hooks/bootstrap_worktree.sh` and `.cursor/worktrees.json.example`).

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
6. Optional observability apps and TTS integrations — defer until the basic agent flow works; when you enable them, follow [`adoption-observability-appendix.md`](../archive/adoption-observability-appendix.md) for opt-in posture, `events.sqlite` gitignore, manual rotation, and shared-environment token guidance. For reproducible bootstrap + `update-mat.py` dry-run evidence, see the [adoption observability pilot report](../../artifacts/report/adoption-observability-pilot-2026-06-23.md) (`artifacts/report/adoption-observability-pilot-2026-06-23.md` when generated locally).

## Common Pitfalls

- Replacing existing repo instructions instead of merging them into `AGENTS.md`.
- Assuming Claude-specific task-board or messaging features exist in Cursor.
- Turning on stop-loop enforcement before builders and verifiers are tuned to your repo's real acceptance criteria.
- Forgetting that worktrees may need extra setup for databases, generated files, or package installs.
- Expecting PermissionRequest-like hooks; Cursor handles permission gating differently inside the runtime.
- Running **`/mat-sync`** inside a product repo before first adoption — use MAT source + `--repo-root` until `.cursor/commands/` is installed.

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
- [ ] If observability is enabled, operators read [`adoption-observability-appendix.md`](../archive/adoption-observability-appendix.md) (packaged to `.mat/docs/` on bootstrap/update) for manual rotation, gitignore surfaces, and RFU-7 deferral honesty.
