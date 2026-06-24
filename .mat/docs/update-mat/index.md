# MAT updater foundation

This bundle covers **slices 1–3** of the MAT updater + advisor coordination mission. The updater is dry-run first, audit-friendly, and explicit about what it may and may not touch. It does **not** auto-commit, auto-open PRs, or silently overwrite product-owned `AGENTS.md` prose.

**Operator entry:** start with [`validation-report.md`](../../validation-report.md) (slice 3 checklist: dry-run → review → apply staging → manual commit decision).

## Operator demo

Run the recorded end-to-end walkthrough against a disposable temp adopted fixture:

```txt
bash scripts/demo/updater-operator-walkthrough.sh
```

The script bootstraps a temp repo, runs dry-run then `--apply --approved --plan-file`, asserts **no new commit** on the target root, and writes captured stdout plus artifact paths to [`artifacts/update-mat/demo-walkthrough-latest.md`](../../artifacts/update-mat/demo-walkthrough-latest.md) (gitignored). See [`validation-report.md`](../../validation-report.md) slice 3 Commands for verify commands and the operator checklist.

## Contents

- [`architecture-and-rollout.md`](architecture-and-rollout.md) — design for the updater foundation, compatibility checks, dry-run planning, staged rollout, slice boundaries, and security posture
- [`role-prompt-templates.md`](role-prompt-templates.md) — role prompts for updater, watcher, scanner, analyzer, architect, generator, test, CI, reviewer, security, and rollback sessions
- [`advisor-task-session-summary.schema.json`](advisor-task-session-summary.schema.json) — machine-readable summary schema for advisor/task session handoffs
- [`advisor-task-session-summary.examples.json`](advisor-task-session-summary.examples.json) — example payloads that satisfy the schema
- [`../../scripts/adoption/mat-footprint-v1.json`](../../scripts/adoption/mat-footprint-v1.json) — machine-readable target-repo MAT footprint manifest
- [`../../scripts/adoption/mat-legacy-migrations-v1.json`](../../scripts/adoption/mat-legacy-migrations-v1.json) — legacy paths (e.g. pre-`mat-*` slash command filenames) and handling: `auto_remove` (fingerprint match only), `backup_then_remove`, or `warn_only`. **Fingerprints** are SHA256 of exact file bytes: for several legacy commands we list the union of every distinct blob from `git log aefa9f7^ -- <path>` in this repository (last revision before namespaced `mat-*` commands), plus the small stub bytes used in MAT's own regression tests for `plan_w_team.md`. Covered command examples include `plan_w_team.md`, `build.md`, `review.md`, `long-run.md`, `plan.md`, `plan_onboarding.md`, `doctor.md`, `lite.md`, `sprint.md`, `subagents_spawn.md`, `update_mat.md`, and `check_worktrees.md`; **`plan-team.md`** stays **`warn_only`** (no single canonical body). Agents, skills, hooks, and `output-styles/*` are out of scope for this manifest. Fingerprinted `backup_then_remove` / `auto_remove` entries carry **`fingerprint_provenance`** (`boundary`, `source`, `generated_at`, optional `note`) so CI and operators know how each union was produced (`git_log_union`, `git_log_union_plus_stub`, or `manual`). Anything whose bytes are **not** in that set is treated as customized — quarantine copy, original retained — not deleted. The manifest is **validated** before any applicator run: blocked paths overlap `preserve_paths` / `protected_handoff_paths`, enumerated product-only root filenames, malformed fingerprints, missing provenance on fingerprinted entries, unknown `handling`, or `backup_then_remove` / `auto_remove` without fingerprints cause a hard error (operators must not ship invalid manifests).
- [`../../scripts/adoption/mat-legacy-fingerprints.py`](../../scripts/adoption/mat-legacy-fingerprints.py) — operator helper: default `git log aefa9f7^ -- <path>` walks; prints a sorted SHA256 union of historical file bodies for `--path`. **`--verify`** checks that every git-derived blob for that path appears in the checked-in manifest (exit non-zero if git has undocumented bytes); uses per-entry `fingerprint_provenance.boundary` when set. **`--verify-all`** runs that check for every manifest entry with non-empty fingerprints (wired into `scripts/phase1-verify.sh` on the **MAT source** profile where this repo's git history is available). **`--strict`** additionally fails when the manifest lists hashes not seen in that git slice (useful for catching typos; off by default so documented test stubs may exceed git-only history).
- [`../../scripts/adoption/apply_mat_legacy_cleanup.py`](../../scripts/adoption/apply_mat_legacy_cleanup.py) — applies that manifest, appends `artifacts/update-mat/legacy-cleanup.jsonl`, and quarantines under `artifacts/update-mat/legacy-quarantine/<run-id>/` when needed. Manifest entries must not name `mat-footprint-v1.json` preserve/protected paths (validation rejects them). Each JSONL record includes `run_id`, `manifest_schema_version`, and `legacy_cleanup_jsonl_schema` for audit correlation. **`--report`** prints a stdout summary of the latest `run_id` slice; **`bash doctor.sh --legacy-cleanup`** runs the same report from the repo root.
- **`update-mat.py` dry-run** runs the same legacy engine against the **adopted target tree** with `dry_run=True` (no JSONL append, no quarantine writes, no `artifacts/update-mat/` directory creation from the legacy applicator alone) and records structured decisions under `legacy_cleanup_preview` in the plan JSON and in the human-readable plan/patch stdout section (`would_remove`, `would_quarantine_and_remove`, `would_quarantine_customized`, `warn_only`, `skipped_preserve_paths`, `skipped_absent`, `skipped_customized`, `skipped_not_file`, etc., matching `apply_mat_legacy_cleanup` action names). Apply mode still runs real cleanup on the staging worktree after layout copy.

## Cost & context hygiene pack (MAT default)

Bootstrap and `scripts/phase1-verify.sh` ship an **enforced pack**: always-on [`.cursor/rules/cost-context-hygiene.mdc`](../../.cursor/rules/cost-context-hygiene.mdc), root [`.cursorignore`](../../.cursorignore) (stack-detected template from [`docs/templates/`](../../docs/templates/) in the MAT source tree; in adopted repos templates also live under `.mat/docs/templates/`), [`scripts/validate_cost_context_hygiene_pack.py`](../../scripts/validate_cost_context_hygiene_pack.py) (structured `FAIL`/`WARN`/`INFO`, `--report`, `--enforce auto|strict|warn_first` reading `.mat/cost-hygiene-adoption.json` when present; validator resolves each template from `docs/templates/<name>` or `.mat/docs/templates/<name>`), and optional `bash doctor.sh --cost-hygiene`. **New-project** installs the selected template when root `.cursorignore` is missing. **Existing-project** runs set `warn_first` in the adoption file: they **never overwrite** an existing product `.cursorignore`; when root `.cursorignore` is absent, they install the same stack-detected template as new-project. Use **`CURSOR_MAT_COST_HYGIENE_ENFORCE=strict`** in downstream CI to opt into a hard-fail until fragments match. `artifacts/cost-hygiene/` (from `--report`) is local, gitignored, advisory only — not billing. Re-bootstrap or copy those paths when refreshing an adopted repo; CI fails if the pack is gutted (unless only WARN under warn-first and no FAIL).

## Workflow artifact contract (dual location)

`build-result.md` and `verify-result.md` must follow the same section contract as the MAT source file `docs/workflow-artifact-contract.md`. In adopted repositories that contract is also copied to **`.mat/docs/workflow-artifact-contract.md`**; bootstrap adjusts `.cursor/` prompts so links do not assume a bulk-copied root `docs/` tree. Runtime validation resolves the readable doc from root `docs/` first, then `.mat/docs/`.

**Source-only vs adopted:** the full MAT **source** repository keeps broad `docs/`, `specs/`, `apps/`, and the primary `tests/` suite. Adopted repos get **minimal** root `docs/` (typically `current-plan.md` and `long-run-state.md` only), packaged manuals under **`.mat/docs/`**, contract tests under **`.mat/tests/`**, and `scripts/phase1-verify.sh` runs the **adopted** profile when `.mat/README.md` is present (optional handoff validation, `.mat/tests` unittest target, skips Bun smoke without `apps/server`).

## Adoption observability

- [`adoption-observability-appendix.md`](../adoption-observability-appendix.md) — opt-in observability posture for product repos: enablement, `events.sqlite`, manual rotation, gitignore surfaces, preview-vs-full-row honesty, hook capture dirs, RFU-7 deferral link, and a README checklist. Copied to **`.mat/docs/adoption-observability-appendix.md`** on bootstrap/update via `adoption-layout-v1.json`.
- Maintainer depth: [`observability-retention-policy.md`](../observability-retention-policy.md).

## Slice boundary

| Slice | Shipped scope |
| --- | --- |
| **1** | Footprint manifest, role prompts, summary schema, dry-run planning, patch/plan artifacts |
| **2** | CI-visible integration harness (`MatUpdaterIntegrationTest`), temp-repo regression locks, fast/full verify commands |
| **3** | Operator validation report checklist, adoption doc polish, security doc locks (`MatUpdaterSecurityDocsTest`) |

**Not shipped (honest non-goals):**

- Auto-commit or auto-PR creation
- Silent overwrite of product-owned `AGENTS.md` prose
- RFU-7 observability retention/redaction automation
