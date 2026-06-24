# MAT updater architecture and rollout

## Goal

Slice 1 establishes a safe foundation for refreshing MAT-managed assets in adopted repositories without mutating real production targets. The updater remains dry-run first, audit-friendly, and explicit about what it may and may not touch.

## Design principles

- Treat project-owned `AGENTS.md` files as product content, not MAT-owned content.
- Keep `.mat/` as the reference sidecar surface for packaged MAT material.
- Prefer repository-native files and standard library Python over opaque automation.
- Record every update attempt with enough metadata to reconstruct the decision.
- Fail closed on ambiguous footprint or compatibility cases.

## Cost & context hygiene (rollout note)

MAT defaults include file-scoped context guidance (`.cursor/rules/cost-context-hygiene.mdc`), stack-aware `.cursorignore` templates under `docs/templates/cursorignore-mat-*` (mirrored under `.mat/docs/templates/` after bootstrap) with a shared `cursorignore-mat-shared.inc` block, install of the selected template when root `.cursorignore` is missing (**new-project** and **existing-project**), and `scripts/validate_cost_context_hygiene_pack.py` (structured severities, `--report`, `auto` enforcement from `.mat/cost-hygiene-adoption.json`, optional `CURSOR_MAT_COST_HYGIENE_ENFORCE`; template checks resolve `docs/templates/` or `.mat/docs/templates/` by basename) wired into `scripts/phase1-verify.sh`. **Existing-project** adoption writes `warn_first` and never overwrites an existing product `.cursorignore`; sidecar `*.mat-suggest` under `.mat/docs/templates/` supports optional merge review. Upstream refreshes should keep `adoption-layout-v1.json`, bootstrap, and the validator in sync so downstream repos do not silently lose the pack.

## Contract layers

1. **Source layout manifest**: `scripts/adoption/adoption-layout-v1.json` defines what the workflow repo packages into adopted repos (including `docs/workflow-artifact-contract.md` → `.mat/docs/workflow-artifact-contract.md` for the human-readable build/verify artifact contract; hooks prefer root `docs/` when present, else the sidecar copy).
2. **Target footprint manifest**: `scripts/adoption/mat-footprint-v1.json` defines the preserve list, protected handoffs, doc bundle, and role contract for an adopted repo.
3. **Updater contract module**: `scripts/adoption/update_mat_contracts.py` validates footprint manifests, loads JSON payloads, and serializes advisor summaries.
4. **CLI updater**: `scripts/adoption/update-mat.py` keeps the operational flow, emits dry-run plan artifacts, and writes audit metadata. On **dry-run** (no `--apply`), it also attaches a **`legacy_cleanup_preview`** array to the plan JSON and prints a **Legacy cleanup preview** section to stdout: the same `apply_legacy_cleanup(..., dry_run=True)` decisions against the **target repo root** (no JSONL/quarantine writes from that pass; no audit-directory mkdir for legacy-only dry-run). Layout comparison treats paths listed in `mat-legacy-migrations-v1.json` as **allowed extras** inside MAT-owned trees so obsolete command files on the target do not spuriously conflict with upstream (they are surfaced only via the legacy preview).
5. **Legacy migration manifest**: `scripts/adoption/mat-legacy-migrations-v1.json` lists obsolete MAT-managed files (for example old `.cursor/commands/*` names replaced by `mat-*` commands). Before processing, `validate_mat_legacy_migrations()` rejects invalid entries (schema, fingerprints, **`fingerprint_provenance`** on fingerprinted `backup_then_remove` / `auto_remove` rows, handling, successor shape, overlap with `preserve_paths` / `protected_handoff_paths`, or enumerated product-only root filenames). `scripts/adoption/apply_mat_legacy_cleanup.py` classifies each present file by **sha256** against known MAT fingerprints (for several commands, the manifest unions every distinct blob from `git log aefa9f7^ -- <path>` in this repo, plus the regression-test stub for `plan_w_team.md`). Exact match may be removed or quarantined per entry `handling`; customized content is not deleted (quarantine copy + keep original, or `warn_only`). Audit: `artifacts/update-mat/legacy-cleanup.jsonl` (machine-oriented fields per line: `run_id`, `manifest_schema_version`, `legacy_cleanup_jsonl_schema`, `action`, …); quarantine: `artifacts/update-mat/legacy-quarantine/<timestamp>/`. **Re-bootstrap** and **`update-mat.py --apply`** (staged worktree) run the applicator after new layout files are in place. Use `scripts/adoption/mat-legacy-fingerprints.py` to recompute or verify fingerprint unions against git history. **`--verify-all`** (also run from `scripts/phase1-verify.sh` when the script is present) checks every fingerprinted manifest entry in one pass, honoring each entry’s `fingerprint_provenance.boundary`. Use **`--strict`** when you want manifest-only hashes (for example test stubs) to fail the check; default lenient mode allows documented extras beyond git-only history.

   **Coverage note (2026-06-22):** the shipped manifest now fingerprint-covers the remaining git-evidenced pre-`mat-*` slash commands under `.cursor/commands/` (`plan.md`, `plan_onboarding.md`, `doctor.md`, `lite.md`, `sprint.md`, `subagents_spawn.md`, `update_mat.md`, `check_worktrees.md`, plus earlier entries for `plan_w_team.md`, `build.md`, `review.md`, and `long-run.md`). **`plan-team.md`** remains `warn_only` without fingerprints. Agents, skills, hooks, and `output-styles/*` are not in scope.

## Rollback / review (legacy cleanup)

After refresh, inspect `artifacts/update-mat/legacy-cleanup.jsonl` (or `python3 scripts/adoption/apply_mat_legacy_cleanup.py --report`, or `bash doctor.sh --legacy-cleanup`). If entries show `quarantined_customized_left_in_place`, compare the repo file to the copy under `artifacts/update-mat/legacy-quarantine/.../customized-*`, merge any wanted edits into current MAT commands, then delete the legacy file manually if appropriate. To promote a path from `warn_only` to fingerprinted `backup_then_remove`, first capture git-derived hashes with `mat-legacy-fingerprints.py --path …`, merge into the manifest with evidence, then re-run verify. Removing the wrong file is avoided by fingerprint checks; restoring from quarantine is a simple file copy if you delete a stub by mistake.

## Update flow

1. Load the source layout and target footprint manifests.
2. Resolve upstream source content and the adopted target root.
3. Compare layout-driven MAT-managed files to the target repo.
4. Analyze compatibility against the preserve list and protected handoff paths.
5. Produce a dry-run plan and patch preview first, including the non-mutating legacy migration preview for the target tree.
6. If the operator explicitly approves apply-mode staging, stage in an isolated worktree or branch-like path.
7. Write audit metadata and stop before commit or PR creation.

## Refresh vs re-bootstrap (operator mental model)

| Mechanism | What it refreshes | What it intentionally preserves / avoids |
|-----------|-------------------|----------------------------------------|
| `update-mat.py` dry-run → optional `--apply` | Files the layout/footprint manifests classify as MAT-managed, with explicit conflict reporting | Product prose in root `AGENTS.md` / nested agent files except managed pointer blocks; does not silently rewrite unrelated product docs |
| Re-run `bootstrap-workflow-into-repo.sh` | Full layout copy: `.cursor/`, packaged `scripts/`, `.mat/docs/`, `.mat/tests/`, `.mat/AGENTS.mat.md`, templates, `.env.sample`, cost-hygiene sidecar metadata | In `existing-project` mode: existing root `README.md`, `CHANGELOG.md`, `AGENTS.md`; existing `docs/current-plan.md` and `docs/long-run-state.md` when present; never overwrites an existing root `.cursorignore` |

After either path, verify from the adopted repo root with `bash scripts/phase1-verify.sh` (and optionally your product CI). Review `.cursorignore` suggestions under `.mat/docs/templates/*.mat-suggest` when `warn_first` adoption applies.

## Rollout phases

### Slice 1

- manifest-driven detection
- compatibility analysis
- dry-run planning
- patch and plan artifact emission
- audit metadata
- role prompt templates
- advisor/task-session summary schema
- documentation bundle

### Slice 2 (shipped)

- CI wiring via standard `test_*.py` discovery in `scripts/phase1-verify.sh` (no separate hook)
- integration harness: `tests/test_mat_updater_integration.py` (`MatUpdaterIntegrationTest`) calling `scripts/adoption/update-mat.py` in temp repos only
- dry-run default, plan/patch artifact emission, AGENTS non-destructive handling, explicit `--apply` + `--approved` gates, no auto-commit regression lock
- drift/conflict fail-closed regression locked (integration harness + `tests/test_update_mat.py`)
- expanded `validation-report.md` with fast vs full updater verify commands

### Slice 3 (shipped)

- operator-facing validation report with end-to-end checklist ([`validation-report.md`](../../validation-report.md) slice 3)
- adoption doc polish: [`docs/getting-started-existing-projects.md`](../getting-started-existing-projects.md), [`docs/getting-started-new-projects.md`](../getting-started-new-projects.md), [`docs/adoption-safe-defaults.md`](../adoption-safe-defaults.md), [`docs/MAINTAINER.md`](../MAINTAINER.md) (MAT updater operator runbook)
- security posture documentation and `MatUpdaterSecurityDocsTest` regression locks in `tests/test_workflow_docs.py`
- `specs/update-mat/tasks.json` TASK-001–005 complete

## Security posture (slice 3)

- **Fail-closed on drift and conflict:** target changes after dry-run or unresolved footprint/AGENTS ambiguity block apply; integration harness locks this in temp repos.
- **No silent AGENTS overwrite:** product-owned `AGENTS.md` prose stays intact; the sidecar helper updates pointer blocks non-destructively.
- **Temp-repo-only integration tests:** `MatUpdaterIntegrationTest` never mutates production adopted trees.
- **Audit JSONL trail:** `artifacts/update-mat/legacy-cleanup.jsonl` and quarantine paths support rollback review.
- **No auto-commit or auto-PR:** apply mode stages in a disposable worktree and stops before commit or PR creation.

## Safety boundary

This bundle does not:

- update any production repository during automated tests
- auto-commit or auto-open PRs
- overwrite product-owned `AGENTS.md` prose silently
- ship RFU-7 observability retention/redaction automation

## Success criterion

The first slice is shippable when the updater foundation can explain what it would change, why the change is compatible, and how to roll it back before any real mutation is approved.
