# MAT sync team runbook

- **Purpose:** Team-portable operator playbook for `/mat-sync` and `.mat/source-config.json` v2 (GitHub-first production path).
- **Audience:** Maintainers refreshing MAT in adopted product repos without a maintainer-local MAT checkout.
- **Prerequisites:** Adopted repo with `.mat/README.md`, network access to GitHub (or pre-warmed cache), `bash`, `python3`, `git`.
- **Status:** complete
- **Last updated:** 2026-08-21

## Related files

- [`.cursor/commands/mat-adopt.md`](../../.cursor/commands/mat-adopt.md) — first-adoption orchestrator entry (MAT source workspace)
- [`.cursor/commands/mat-sync.md`](../../.cursor/commands/mat-sync.md) — slash command and installer flow
- [`scripts/mat-sync.sh`](../../scripts/mat-sync.sh) — state machine (`--help`)
- [`docs/update-mat/architecture-and-rollout.md`](../update-mat/architecture-and-rollout.md#mat-source-config-matsource-configjson) — source-config v1/v2 schemas and resolution precedence
- [`docs/guides/getting-started-existing-projects.md`](getting-started-existing-projects.md) — first adoption vs refresh
- [`docs/update-mat/index.md`](../update-mat/index.md) — updater foundation bundle

**Production default:** `.mat/source-config.json` **v2** (`repository` + `ref`) materializes upstream from GitHub into a local cache. **Local path overrides** (`--source`, `$MAT_SOURCE`, v1 `mat_source`) are **maintainer dev only** — do not document them as the team default.

### Packaging prerequisite (adoption layout)

The adopted-repo installer (`bash scripts/mat-sync.sh` from the product tree) requires **layout-shipped scripts** in `adoption-layout-v1.json` `root_scripts_copy`: `scripts/mat-sync.sh`, `scripts/adoption/mat_source_config.py`, `scripts/adoption/mat_source_materialize.sh`, `scripts/adoption/update_mat_conflict_routing.py`, and `scripts/adoption/mat_cursorignore_merge.py`. Fresh or re-bootstrapped adopted repos receive these on copy.

**Trees bootstrapped before this layout shipped** (for example Wattif @ pre-packaging SHA) may lack `scripts/mat-sync.sh` or the adoption helpers even when `.mat/README.md` is present. The honest transitional path is **one rebootstrap** (`bootstrap-workflow-into-repo.sh --mode existing-project`) after MAT slice 6 is on GitHub `main`, then use the adopted-repo quick-start below. Do not treat maintainer-local `--source` or ad-hoc cache copies as the team default for those trees.

---

## 1. First adoption / refresh with source-config v2

### First existing-project adoption (primary — mat-sync plan → approve)

**Production default:** run mat-sync from the **MAT source** checkout with `--repo-root` pointing at the product repo. Use `--repository` (v2) when the product tree has no `.mat/source-config.json` yet.

**Slash command honesty:** **`/mat-sync`** is **not** available inside an un-adopted product repo — slash commands ship with the adopted `.cursor/commands/` bundle after first approve. Until then, run **`/mat-adopt`** from the **MAT source** workspace (guided plan → review → approve) or shell `scripts/mat-sync.sh` from MAT source with `--repo-root`. Slice F ships `mat-adopt.sh` for zero-checkout installs — see [`.cursor/commands/mat-adopt.md`](../../.cursor/commands/mat-adopt.md).

**1. Plan (dry-run, from MAT source):**

```txt
cd "/path/to/multi-agent-teams"   # MAT source
bash scripts/mat-sync.sh --repo-root "/path/to/product-repo" --repository Devora-AS/multi-agent-workflow
```

**2. Review** `mat-sync-plan-file=` (route is typically `bootstrap` for virgin trees). Check `routing_recommendation`, `conflict_state`, `preflight`, `cursorignore_merge_preview`, `gitignore_rewrite_preview`, `gitignore_merge_preview`, and **`env_sample_merge_preview`** when the product tree has a customized `.mat.env.sample` (directory-ignore `.cursor/` repos need rewrite before negations — see [`getting-started-existing-projects.md`](getting-started-existing-projects.md)).

**3. Approve:**

```txt
bash scripts/mat-sync.sh --repo-root "/path/to/product-repo" \
  --approve-plan "/path/to/product-repo/artifacts/mat-sync/latest-plan.json"
```

After approve, confirm `.mat/README.md`, `.mat/AGENTS.mat.md`, and `.mat/source-config.json` (v2) exist:

```json
{
  "schema_version": 2,
  "repository": "Devora-AS/multi-agent-workflow",
  "ref": "main",
  "cache_dir": "~/.cache/mat-source"
}
```

Packaged operator docs under `.mat/docs/` refresh on **bootstrap/rebootstrap** approve (full layout copy). **Incremental** `update_dry_run` apply via `update-mat.py` also refreshes individual `.mat/docs/` mappings when upstream differs — see [`getting-started-existing-projects.md`](getting-started-existing-projects.md) § Refreshing MAT later.

**Maintainer/debug fallback:** raw `bootstrap-workflow-into-repo.sh --mode existing-project` when mat-sync routing fails or you need a minimal repro outside the state machine — **not** the team default. See [`getting-started-existing-projects.md`](getting-started-existing-projects.md).

After first adoption, incremental refresh from the **adopted repo** no longer requires a local MAT checkout when v2 config is valid.

### Incremental refresh (team default)

From the **adopted repo** (or with `--repo-root` pointing at it):

**1. Plan (dry-run):**

```txt
cd "/path/to/adopted-repo"
bash scripts/mat-sync.sh --repo-root "$(pwd)"
```

**2. Review** `mat-sync-plan-file=` (or `artifacts/mat-sync/latest-plan.json`): `route`, `routing_recommendation`, `conflict_state`, `preflight`, `cursorignore_merge_preview`, `gitignore_rewrite_preview`, `gitignore_merge_preview`, and **`env_sample_merge_preview`** when `.mat.env.sample` is customized.

**3. Approve:**

```txt
bash scripts/mat-sync.sh --repo-root "$(pwd)" \
  --approve-plan "$(pwd)/artifacts/mat-sync/latest-plan.json"
```

MAT source resolves from v2 config — **no `--source` required** when config is valid.

---

## 2. Pin tag vs SHA

Set `ref` in `.mat/source-config.json` to control which upstream commit materializes:

| `ref` value | Use when |
|-------------|----------|
| Branch (e.g. `main`) | Rolling team refresh; tracks upstream default branch |
| Tag (e.g. `v2026.06.26`) | Reproducible upgrades across machines; document tag in PR |
| Full SHA | Audit lock; immutable pin for compliance or incident replay |

After changing `ref`, re-run **plan** before **approve**. Plan JSON records `provenance.resolved_sha` when materialized from GitHub.

**Honesty:** Pinning a tag or SHA does not bypass dry-run or `--approve-plan`. Mutations still require explicit human review.

---

## 3. Cache location and refresh

| Item | Location / behavior |
|------|---------------------|
| Default cache root | `~/.cache/mat-source` |
| Per-repo working tree | `<cache_dir>/<owner-repo-slug>` (slashes in `OWNER/REPO` → hyphens) |
| Override | Optional `cache_dir` in `.mat/source-config.json` |
| Materialize | Clone on first use; `git fetch` + detached checkout on later runs |

**Refresh cache manually** when upstream refs look stale or a corrupted clone is suspected:

```txt
rm -rf ~/.cache/mat-source/Devora-AS-multi-agent-workflow
```

Then re-run mat-sync **plan**. Materialize re-clones on next resolution.

**Offline / CI tests** may set `MAT_SOURCE_CLONE_URL=file:///…` against a bare fixture — production operators use GitHub.

---

## 4. Troubleshooting

### `.gitignore` workflow paths still ignored after approve

- **Symptom:** `phase_verify` fails with `git check-ignore` on `.cursor/hooks.json` (or similar); `preflight.gitignore_workflow_untrackable` non-empty.
- **Action:** Re-plan; confirm non-empty `gitignore_rewrite_preview` (`.cursor/` → `.cursor/*`) was applied on approve. Manual check: `git check-ignore -v .cursor/hooks.json` must exit non-zero. Debug-only skip: `MAT_SYNC_SKIP_GITIGNORE_TRACKABILITY=1`.
- **Detail:** [`getting-started-existing-projects.md`](getting-started-existing-projects.md) and [`.cursor/commands/mat-sync.md`](../../.cursor/commands/mat-sync.md).

### `true_drift`

Updater conflict routing bucket for unmanaged file differences (not verified product extensions, not stale layout manifest).

- **Symptom:** `routing_recommendation: stop`, `conflict_bucket_counts.true_drift` > 0.
- **Action:** Stop before `--approve-plan`. Inspect `artifacts/mat-sync/latest-plan.json` and embedded `updater_plan_file`. Resolve drift manually or choose an honest **rebootstrap** only when routing recommends it and `true_drift` is zero.
- **Do not** `--apply` past unresolved `true_drift`.

### `.mat.env.sample` MAT-tool merge (`env_sample_merge_preview`)

When the product repo has a customized `.mat.env.sample`, plan JSON may include **`env_sample_merge_preview`** (`path`: `.mat.env.sample`, `changed`). On **`--approve-plan`** for **`bootstrap`**, **`rebootstrap`**, and **`update_dry_run`**, mat-sync applies **`mat_env_sample_merge.py`**: it replaces **only** the block between `# ─── MAT-tool ───` and `# ─── /MAT-tool ───` from upstream; all lines outside those markers are preserved. Root **`.env.sample`** is product-only and is not MAT-merged. Bootstrap uses the same merge helper instead of blind overwrite.

**Honesty:** MAT does **not** auto-merge live **`.env`** or **`.mat.env`** — operators copy values from the samples manually. Review `env_sample_merge_preview` before approve when customized MAT sample lines exist.

### `product-extensions` schema v3 (skills + rules)

`.mat/product-extensions.json` **schema v3** registers product-owned **agents**, **commands**, **skills** (directory name + `SKILL.md` sha256), and **rules** (basename + file sha256). Reconcile on detect/plan so a product-only skill or rule does **not** route as **`true_drift`**. Unregistered hook drift under `.cursor/hooks/` remains **`true_drift`** (fail-closed).

### `registry_integrity`

`.mat/product-extensions.json` is a reconciled cache, not authority. Wrong or stale sha256 rows fail closed.

- **Symptom:** `routing_recommendation: stop`, `registry_integrity` > 0.
- **Action:** Re-run plan after `phase detect: product-extensions reconciled=` output. Fix registry rows or restore custom agent/command files to match live disk. Rebootstrap is **not** a shortcut past `registry_integrity`.

### Doctor worktrees (advisory)

Verify runs `bash scripts/doctor.sh` then `bash scripts/phase1-verify.sh`. Stale worktree WARN/FAIL from doctor does **not** fail mat-sync when phase1-verify passes.

- **Symptom:** Doctor warns on old `.cursor/worktree/` trees; mat-sync still exits 0 after verify.
- **Action:** Clean experimental worktrees (`/mat-wt-remove`, `git worktree prune`) when convenient. Use **`--strict-doctor`** or **`MAT_SYNC_STRICT_DOCTOR=1`** only when you want fail-closed on doctor issues.

### Handoff whitespace (verify preflight)

`docs/current-plan.md` and `verify-result.md` trailing whitespace fails `tests/test_artifact_validation.py` and `git diff --check`.

- **Symptom:** mat-sync prints a one-line `python3 -c …` fix per file before verify.
- **Action:** Run the suggested command (non-destructive strip) or edit manually. mat-sync does **not** auto-strip.

### Other quick fixes

| Error | Fix |
|-------|-----|
| `--approve-plan file not found` | Run plan phase first |
| `--approve-plan does not match latest saved plan` | Re-plan after tree changes |
| MAT source not found | Ensure v2 config, network, and cache; dev fallback: `--source /path/to/MAT-source` |

---

## 5. Wattif-style rebootstrap expectations

Heavy adopted trees (many custom agents/commands, stale `adoption-layout-v1.json` footprint) often route **`rebootstrap`** instead of incremental apply.

**Expected stdout (quiet routing):**

- Conflict **bucket counts** and `routing_recommendation` / `routing_rationale`
- **No** raw per-file `Conflicts:` bullet dump (detail stays in plan JSON)

**When rebootstrap is honest:**

- `true_drift` and `registry_integrity` are **zero**
- Conflicts are verified **product_extensions** and/or **stale_layout_manifest**
- Operator reviewed `artifacts/mat-sync/latest-plan.json`

**Approve path:** Same three-step flow; `--approve-plan` runs bootstrap when route is `rebootstrap`. Preserves root `README.md`, `CHANGELOG.md`, and product `AGENTS.md` in `--mode existing-project`.

Regression evidence: `bash scripts/demo/mat-sync-production-scenarios.sh` (Wattif-like scenario).

---

## 6. Optional: Wattif re-upgrade replay (v2 only, no local MAT path)

For adopted repos that already have valid v2 `source-config.json`, operators can replay an upgrade **from the product repo only** — no `MAT_SOURCE`, no `--source`, no sibling checkout.

**Pre-flight (product repo):**

```txt
cd "/path/to/adopted-repo"
git status --short
cat .mat/source-config.json
```

**Plan:**

```txt
bash scripts/mat-sync.sh --repo-root "$(pwd)" --skip-verify
```

Check `routing_recommendation` (often `rebootstrap` on Wattif-like trees). Stop if `stop` or `true_drift` > 0.

**Approve + verify:**

```txt
bash scripts/mat-sync.sh --repo-root "$(pwd)" \
  --approve-plan "$(pwd)/artifacts/mat-sync/latest-plan.json"
```

**Post-flight:**

```txt
bash scripts/phase1-verify.sh
git status --short
```

MAT never auto-commits. Record plan path and `provenance.resolved_sha` from plan JSON for audit.

Maintainer-local replay with `--source` remains valid for MAT repo development; it is not the team production default.

---

## Verification commands (MAT source repo)

```txt
python3 -m unittest tests.test_workflow_docs.MatSyncTeamRunbookDocsTest -v
bash scripts/demo/mat-sync-walkthrough.sh
bash scripts/demo/mat-sync-production-scenarios.sh
```
