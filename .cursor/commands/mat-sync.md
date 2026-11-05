# MAT Sync

Unified shell entry for MAT adoption sync: **detect → route → plan → approve → verify**. Wraps `bootstrap-workflow-into-repo.sh`, `update-mat.py`, `doctor.sh`, and `phase1-verify.sh` with dry-run-first safety (no mutation without `--approve-plan`, no git commit on target).

## Usage

```text
/mat-sync
```

Optional context (production repos with v2 `source-config.json`):

```text
/mat-sync refresh adopted repo at "/path/to/product repo"
```

Maintainer dev (local MAT checkout override):

```text
/mat-sync refresh adopted repo at "/path/to/product repo" from MAT source "/path/to/multi-agent-teams"
```

## Related docs

- [`docs/guides/mat-sync-team-runbook.md`](../../.mat/docs/guides/mat-sync-team-runbook.md) — **team runbook** (GitHub-first production path)

- [`scripts/mat-sync.sh`](../../scripts/mat-sync.sh) — state machine implementation and `--help`
- [`.cursor/commands/mat-update-mat.md`](mat-update-mat.md) — guided Cursor orchestrator (same semantics, chat-native)
- [`docs/update-mat/index.md`](../../.mat/docs/update-mat/index.md) — updater foundation bundle
- [`docs/guides/getting-started-existing-projects.md`](../../.mat/docs/getting-started-existing-projects.md) — first adoption vs refresh
- [`.cursor/commands/mat-adopt.md`](mat-adopt.md) — first-adoption orchestrator entry (MAT source workspace; delegates to `mat-adopt.sh`)

---

## First adoption (un-adopted product repo)

**Primary path:** mat-sync plan → approve from the **MAT source** repo with `--repo-root` and `--repository` (v2). **`/mat-sync` is not available** inside an un-adopted product repo — slash commands install with the adopted `.cursor/commands/` bundle on first approve.

**Chat entry (MAT source workspace):** use **[`/mat-adopt`](mat-adopt.md)** for the guided plan → review → approve flow with one `txt` block per step. Shell equivalent from MAT source or product repo:

**1. Plan (dry-run):**

```txt
bash "/path/to/multi-agent-teams/scripts/adoption/mat-adopt.sh" \
  --repo-root "/path/to/product-repo" \
  --repository Devora-AS/multi-agent-workflow
```

**2. Review** `mat-sync-plan-file=` (or `artifacts/mat-sync/latest-plan.json` on the product repo). Route is typically `bootstrap` for virgin trees. Check **`preflight`** (gitignore blockers, custom agents, scripts overlap, sidecar presence) alongside merge previews.

**3. Approve:**

```txt
bash scripts/mat-sync.sh --repo-root "/path/to/product-repo" \
  --approve-plan "/path/to/product-repo/artifacts/mat-sync/latest-plan.json"
```

After approve, **`/mat-sync`** and other `mat-*` slash commands become available in the product repo. Packaged `.mat/docs/` refreshes on bootstrap/rebootstrap approve; incremental `update_dry_run` apply also updates individual `.mat/docs/` mappings when upstream differs.

**Maintainer/debug fallback:** raw `bootstrap-workflow-into-repo.sh --mode existing-project` — not the team default. See [`getting-started-existing-projects.md`](../../.mat/docs/getting-started-existing-projects.md).

---

## Installer flow (adopted repo with v2 `source-config.json`)

When `.mat/source-config.json` already pins upstream (`schema_version` 2 with `repository` + `ref`), operators need **at most three shell steps** — plan, review the printed plan path, approve. Copy-paste safe in zsh (quote paths that contain spaces).

**1. Plan (dry-run, no mutations):**

```txt
cd "/path/to/adopted repo"
bash scripts/mat-sync.sh --repo-root "$(pwd)"
```

MAT source resolves from `.mat/source-config.json` (no `--source` required when v2 config is valid). Stderr ends with `mat-sync-plan-file=…` and `next: review …`.

**2. Review** the plan JSON at the printed path (or `artifacts/mat-sync/latest-plan.json`). Check `route`, `routing_recommendation`, `conflict_state`, **`preflight`**, `cursorignore_merge_preview`, `gitignore_rewrite_preview`, `gitignore_merge_preview`, and **`env_sample_merge_preview`** when `.mat.env.sample` is customized. For `rebootstrap` or `stop` routes, stdout shows **bucket counts and rationale only** — full patch/conflict detail stays in the plan JSON.

### Preflight report (`preflight` in plan JSON)

Bootstrap and rebootstrap plans include a **`preflight`** object with detect-only signals before approve:

| Key | Meaning |
|-----|---------|
| `gitignore_blockers` | Broad `.cursor` ignores without MAT workflow negations (subtype: append negations for `.cursor/*` vs rewrite `.cursor/` → `.cursor/*` then append) |
| `gitignore_workflow_untrackable` | MAT workflow probe paths still matched by `git check-ignore` (empty when trackable or not a git repo) |
| `env_sample_blocked_by` | Rules that would git-ignore `.env.sample` (check-ignore or simulation) |
| `custom_skills` | Product `.cursor/skills/<name>/` directories not in MAT baseline |
| `custom_agents` | Product `.cursor/agents/*.md` not in MAT baseline |
| `custom_commands` | Product `.cursor/commands/*.md` not in MAT baseline |
| `scripts_path_overlap` | Product `scripts/` paths that MAT bootstrap would overwrite |
| `sidecar_present` | Whether `.mat/AGENTS.mat.md` already exists |
| `policy_flags` | Advisory flags (e.g. `builder_verify_empty` when adoption profile lacks verify commands) |

When `gitignore_blockers` is non-empty on bootstrap/rebootstrap, stderr prints `preflight: gitignore blockers detected: …` — review before `--approve-plan`.

**3. Approve** (mutations + verify):

```txt
bash scripts/mat-sync.sh --repo-root "$(pwd)" \
  --approve-plan "$(pwd)/artifacts/mat-sync/latest-plan.json"
```

Local dev override (optional):

```txt
bash scripts/mat-sync.sh --source "/path/to/multi-agent-teams" --repo-root "$(pwd)"
```

---

## Safety invariants

Same as `/mat-update-mat`:

- **Dry-run/plan by default** — bootstrap or apply only with `--approve-plan <plan.json>` matching the latest saved plan under `artifacts/mat-sync/`.
- **No auto-commit** on the target root.
- **Preserve product `AGENTS.md`** — sidecar helper; inline fallback is explicit only.
- **Fail-closed** on blocked updater dry-runs (conflicts) — route `stop`, exit non-zero.

### Product-extensions registry integrity

`.mat/product-extensions.json` (**schema v3**) is a **reconciled cache**, not authority. Conflict routing verifies each custom agent, command, **skill** (`SKILL.md` sha256), and **rule** (file sha256) against live disk and the upstream MAT bundle:

- Wrong or stale registry rows **cannot** classify `.cursor/hooks` or `.cursor/rules` drift as `product_extensions`.
- Hand-edited or mismatched registry hashes route **`stop`** (`registry_integrity`).
- Missing registry rows for deleted custom files surface as `stale_registry` (advisory) and does not mask `true_drift`.
- **`rebootstrap`** is recommended only when `true_drift` and `registry_integrity` are both zero and conflicts are verified product extensions and/or stale layout footprint.

See [`docs/update-mat/architecture-and-rollout.md`](../../.mat/docs/update-mat/architecture-and-rollout.md#product-extensions-registry-security-schema-v2).

### `.cursorignore` fragment merge (`warn_first`)

When `.mat/cost-hygiene-adoption.json` records **`warn_first`** + **`root_cursorignore_preserved`**, plan JSON includes **`cursorignore_merge_preview`**: ignore lines missing from the stack template under `.mat/docs/templates/` (MAT runtime noise such as `__pycache__/`, `.cursor/hooks/state/`, `.cursor/settings.json`, `artifacts/`). On **`--approve-plan`**, `mat-sync.sh` appends a marked block only (`# BEGIN MAT runtime fragments` … `# END MAT runtime fragments`); it never replaces the product file. For **`bootstrap`** and **`rebootstrap`** routes, approve **recomputes** the preview **after** bootstrap (plan-time preview may be stale when `.cursorignore` or the adoption sidecar did not exist yet) and applies using the live recompute. **`update_dry_run`** still uses the plan JSON preview. Second run is idempotent (marker present → skip). Review the preview before approve; set **`CURSOR_MAT_COST_HYGIENE_ENFORCE=strict`** in CI when you want hard-fail until fragments are merged.

### `.gitignore` MAT workflow merge (existing-project)

When the root **`.gitignore`** broadly ignores `.cursor` workflow paths without MAT workflow negations, plan JSON may include:

| Field | Meaning |
|-------|---------|
| **`gitignore_rewrite_preview`** | Surgical single-line mappings (`.cursor/` → `.cursor/*`, etc.) when directory-ignore patterns block negations |
| **`gitignore_merge_preview`** | Missing lines from `docs/templates/gitignore-mat-existing-project.fragment` (negations for `.cursor/agents/`, `commands/`, `hooks/`, …; `!.env.sample`; local-only runtime paths) |

**Negation-sufficient (`.cursor/*` Omniroute-class):** append marked block only. **Rewrite-required (`.cursor/`, `.cursor/**`, `**/.cursor/`):** approve runs **`apply_gitignore_rewrite`** first, then recomputes merge preview and appends (`# BEGIN MAT git tracking` … `# END MAT git tracking`); never bulk-replaces the product file. **`bootstrap`** / **`rebootstrap`** recompute after bootstrap; **`update_dry_run`** prefers live recompute with plan fallback. Second run is idempotent (marker present → skip). Review both previews before approve.

**Verify fail-closed:** `phase_verify` runs `git check-ignore` on canonical workflow probe paths before doctor; when paths remain ignored, mat-sync exits non-zero with remediation (rewrite `.cursor/` → `.cursor/*` then negations). Skip with **`MAT_SYNC_SKIP_GITIGNORE_TRACKABILITY=1`** for debugging only.

### `.mat.env.sample` MAT-tool merge (`env_sample_merge_preview`)

When the product repo has a customized `.mat.env.sample`, plan JSON may include:

| Field | Meaning |
|-------|---------|
| **`env_sample_merge_preview`** | `{ "path": ".mat.env.sample", "changed": true }` when upstream MAT-tool block differs; absent or `changed: false` when merge would be a no-op |

On **`--approve-plan`** for **`bootstrap`**, **`rebootstrap`**, and **`update_dry_run`**, mat-sync runs **`mat_env_sample_merge.py`**: replaces **only** content between `# ─── MAT-tool ───` and `# ─── /MAT-tool ───` from upstream; preserves all lines outside those markers. Root **`.env.sample`** is product-only. Bootstrap uses the same helper instead of blind overwrite.

**Honesty:** MAT does **not** auto-merge live **`.env`** or **`.mat.env`** — operators copy from the samples manually. Review `env_sample_merge_preview` before approve when customized MAT sample lines exist.

### Quiet routing stdout (`rebootstrap` / `stop`)

When the updater recommends **`rebootstrap`** or **`stop`**, `mat-sync.sh` prints **conflict bucket counts**, **`routing_recommendation`**, **`routing_rationale`**, and the updater plan path — not the full patch preview or per-file conflict dump. Inspect `artifacts/mat-sync/latest-plan.json` and the embedded `updater_plan_file` for full detail.

### Verify: doctor vs phase1-verify

Verify runs **doctor** then **phase1-verify** on the target. Stale worktree WARN/FAIL from doctor does **not** fail mat-sync when phase1-verify passes (advisory doctor). Use **`--strict-doctor`** or **`MAT_SYNC_STRICT_DOCTOR=1`** to fail closed on doctor issues.

### Handoff whitespace preflight

Before verify, if `docs/current-plan.md` or `verify-result.md` on the target have trailing whitespace, mat-sync emits a **non-destructive** one-line `python3 -c …` fix per file (aligned with `tests/test_artifact_validation.py`). It does not auto-strip.

---

## Operator commands (copy-paste)

**Production default (v2 `source-config.json` on target):**

```txt
cd "/path/to/adopted repo"
bash scripts/mat-sync.sh --repo-root "$(pwd)"
bash scripts/mat-sync.sh --repo-root "$(pwd)" \
  --approve-plan "$(pwd)/artifacts/mat-sync/latest-plan.json"
```

**Maintainer dev override (`--source` local checkout):**

```txt
bash scripts/mat-sync.sh --source "/path/to/MAT source" --repo-root "/path/to/adopted repo"
```

**First bootstrap or re-bootstrap after review (dev override shown; production uses v2 config without `--source`):**

```txt
bash scripts/mat-sync.sh --source "/path/to/MAT source" --repo-root "/path/to/adopted repo" \
  --approve-plan "/path/to/adopted repo/artifacts/mat-sync/latest-plan.json"
```

**Force re-bootstrap route when sidecar exists:**

```txt
bash scripts/mat-sync.sh --repo-root "/path/to/adopted repo" --force-rebootstrap
```

**Incremental apply after dry-run plan (plan JSON embeds `updater_plan_file`):**

```txt
bash scripts/mat-sync.sh --repo-root "/path/to/adopted repo" \
  --approve-plan "/path/to/adopted repo/artifacts/mat-sync/latest-plan.json"
```

**Strict doctor (optional):**

```txt
bash scripts/mat-sync.sh --repo-root "/path/to/adopted repo" \
  --approve-plan "/path/to/adopted repo/artifacts/mat-sync/latest-plan.json" \
  --strict-doctor
```

MAT source resolution order: `--source` → `--repository`/`--ref` → `.mat/source-config.json` v2 → v1 → sibling heuristic → `$MAT_SOURCE` (see `mat-sync.sh --help`).

Common errors:

- `--source path is not a directory` — fix the path or omit `--source` when v2 config resolves upstream.
- `--approve-plan file not found` — run plan phase first; pass a real `mat-sync-plan-*.json` or `latest-plan.json` path.
- `--approve-plan does not match latest saved plan` — re-run plan phase after tree changes.

---

## First adoption vs refresh (phases)

| Phase | First adoption (un-adopted product repo) | Refresh (adopted repo with v2 `source-config.json`) |
|-------|------------------------------------------|-----------------------------------------------------|
| **Where to run** | MAT source checkout with `--repo-root <product>` | Adopted product repo (`--repo-root "$(pwd)"`) |
| **Slash entry** | [`/mat-adopt`](mat-adopt.md) (MAT source workspace only) | `/mat-sync` or [`/mat-update-mat`](mat-update-mat.md) |
| **detect** | Sidecar absent; resolve MAT source via `--repository` / v2 materialize | Sidecar markers; resolve upstream from `.mat/source-config.json` v2 |
| **route** | Typically `bootstrap` for virgin trees | `update_dry_run` \| `rebootstrap` \| `stop` |
| **plan** | Dry-run log + plan JSON with **`preflight`**, merge previews | Same; incremental routes may embed `updater_plan_file` |
| **gate** | `--approve-plan` runs bootstrap + post-bootstrap merge recomputes | `--approve-plan` runs updater apply or rebootstrap per route |
| **verify** | Doctor (advisory) + `phase1-verify` on product repo | Same |

Shared phase detail:

| Phase | Action |
|-------|--------|
| detect | Sidecar markers, custom agents vs MAT baseline, resolve MAT source |
| route | `bootstrap` \| `update_dry_run` \| `rebootstrap` \| `stop` |
| plan | Human-readable log + `artifacts/mat-sync/mat-sync-plan-*.json` (includes **`preflight`** on bootstrap/rebootstrap; `cursorignore_merge_preview` when `warn_first` adoption preserved root `.cursorignore`; `gitignore_rewrite_preview` when directory-ignore `.cursor/` needs rewrite; `gitignore_merge_preview` when broad `.gitignore` needs MAT negations; **`env_sample_merge_preview`** when `.mat.env.sample` MAT-tool block would change) |
| gate | Bootstrap or `update-mat.py --apply --approved --plan-file` when `--approve-plan` matches latest plan; bootstrap/rebootstrap then **post-bootstrap** append-only `.cursorignore` and `.gitignore` MAT fragment merges (rewrite directory-ignore first, then live recompute) plus **`.mat.env.sample` MAT-tool merge**; `update_dry_run` uses plan preview for cursorignore, live recompute (plan fallback) for gitignore, and **`mat_env_sample_merge.py`** for `.mat.env.sample` |
| verify | Handoff whitespace preflight; **git check-ignore workflow trackability** (fail-closed; `MAT_SYNC_SKIP_GITIGNORE_TRACKABILITY=1` to skip); `bash scripts/doctor.sh` (advisory unless `--strict-doctor`); then `bash scripts/phase1-verify.sh` on target (skips Bun/client on adopted sidecar) |

---

## End-of-pass rule

After running the script, inspect `mat-sync-plan-file=` in stderr/stdout and the printed route rationale. Re-run with `--approve-plan` only after human review.
