# MAT Adopt

Guided orchestrator for **first-time existing-project adoption** when the product repo does not yet have a MAT sidecar (`.mat/README.md`, `.mat/AGENTS.mat.md`).

This command walks operators through **plan → review preflight/previews → approve** using `scripts/adoption/mat-adopt.sh` (zero-checkout with `--repository`) or `scripts/mat-sync.sh` from the **MAT source** checkout with `--repo-root`. It does **not** add a new merge engine — it delegates to the same mat-sync state machine as [`/mat-sync`](mat-sync.md).

**Shell installer:** `scripts/adoption/mat-adopt.sh` — thin wrapper that materializes GitHub upstream when needed and delegates to `mat-sync.sh`.

## Usage

```text
/mat-adopt
```

Optional context (paste in the same message when helpful):

```text
/mat-adopt integrate MAT into /absolute/path/to/product-repo
```

When you draft operator prompts or copied snippets for this command, default to copy-pasteable fenced `txt` blocks unless the user asks for another format.

## Slash availability (read before running)

**Run `/mat-adopt` from the MAT source workspace** (this repository or any checkout where `.cursor/commands/mat-adopt.md` is installed). The operator names the **product repo** path in chat or in `--repo-root`.

**`/mat-sync` is not available** inside an un-adopted product repo — Cursor slash commands ship with the adopted `.cursor/commands/` bundle on first approve. Do not tell operators to run `/mat-sync` from the product tree until after approve completes.

After first approve, use **[`/mat-sync`](mat-sync.md)** or **[`/mat-update-mat`](mat-update-mat.md)** for incremental refresh from the adopted repo.

## Related docs

- [`docs/guides/mat-sync-team-runbook.md`](../../.mat/docs/guides/mat-sync-team-runbook.md) — GitHub-first team playbook
- [`docs/guides/getting-started-existing-projects.md`](../../.mat/docs/getting-started-existing-projects.md) — existing-project integration guide
- [`.cursor/commands/mat-sync.md`](mat-sync.md) — mat-sync phases table (first adoption + refresh)
- [`.cursor/commands/mat-update-mat.md`](mat-update-mat.md) — adopted-repo refresh orchestrator
- [`specs/mat-adopt-onboarding-unification.md`](../../.mat/docs/specs/mat-adopt-onboarding-unification.md) — full mission spec (`mat-adopt.sh` shipped Slice F)

---

## Safety invariants (always)

- **Dry-run/plan by default** — bootstrap or apply only with `--approve-plan` matching the latest saved plan under `artifacts/mat-sync/`.
- **No auto-commit** on the target root.
- **Preserve product `AGENTS.md`** — sidecar helper; inline fallback is explicit only.
- **Fail-closed** on blocked updater dry-runs — route `stop`, exit non-zero.
- **Maintainer/debug fallback only:** raw `bootstrap-workflow-into-repo.sh --mode existing-project` when mat-sync routing fails — not the team default.

---

## Orchestration instructions

You are the **first-adoption orchestrator**. Walk the operator through **plan → review preflight/previews → approve**. After each step, print **exactly one** recommended next command in a fenced `txt` block. Do not list multiple equally-weighted options — pick the honest branch and one command.

Confirm the workspace is the **MAT source** checkout (contains `scripts/mat-sync.sh`). Confirm the product repo path (operator message or ask once). If `.mat/AGENTS.mat.md` already exists in the product repo, redirect to [`/mat-sync`](mat-sync.md) or [`/mat-update-mat`](mat-update-mat.md) instead.

### Step 1 — Plan (dry-run)

Use `mat-adopt.sh` with `--repository` and an explicit `--ref` (pin upstream; do not rely on floating `main` in production). From the MAT source checkout, `mat-sync.sh --repo-root` with the same flags is an equivalent direct path.

Report: resolved product path, that `/mat-sync` is unavailable in the product repo until after approve, and that stderr will end with `mat-sync-plan-file=…`.

```txt
bash scripts/adoption/mat-adopt.sh --repo-root "/path/to/product-repo" \
  --repository Devora-AS/multi-agent-workflow --ref main
```

---

### Step 2 — Review preflight and merge previews

Operator must review the plan JSON at the printed path (or `artifacts/mat-sync/latest-plan.json` on the product repo) **before** approve.

Check:

| Field | What to check |
|-------|----------------|
| `route` | Typically `bootstrap` for virgin trees |
| `routing_recommendation` / `conflict_state` | Stop if route is `stop` or conflicts are unresolved |
| **`preflight`** | `gitignore_blockers`, `gitignore_workflow_untrackable`, `custom_agents`, `scripts_path_overlap`, `sidecar_present`, `policy_flags` |
| **`cursorignore_merge_preview`** | Append-only MAT runtime fragments when `warn_first` preserved root `.cursorignore` |
| **`gitignore_rewrite_preview`** | Directory-ignore `.cursor/` patterns requiring surgical rewrite to `.cursor/*` before negations |
| **`gitignore_merge_preview`** | Omniroute-class / post-rewrite `.gitignore` negations for trackable `.cursor/` workflow paths |

Summarize findings in chat. When `gitignore_blockers` is non-empty on bootstrap, stderr includes `preflight: gitignore blockers detected: …`. **Verify fails closed** when `preflight.gitignore_workflow_untrackable` is non-empty after approve (workflow paths still git-ignored).

```txt
# REVIEW — open mat-sync-plan-file= path or /path/to/product-repo/artifacts/mat-sync/latest-plan.json
# Confirm route, preflight, cursorignore_merge_preview, gitignore_rewrite_preview, and gitignore_merge_preview before Step 3
```

---

### Step 3 — Approve (mutations + verify)

Run only after human review of the plan JSON. Approve applies bootstrap, post-bootstrap merge recomputes when applicable, then verify (doctor advisory + `phase1-verify` on target).

After success, confirm `.mat/README.md`, `.mat/AGENTS.mat.md`, and `.mat/source-config.json` (v2) exist in the product repo. **`/mat-sync`** and other `mat-*` slash commands become available in the product repo.

```txt
bash scripts/adoption/mat-adopt.sh --repo-root "/path/to/product-repo" \
  --approve-plan "/path/to/product-repo/artifacts/mat-sync/latest-plan.json" \
  --repository Devora-AS/multi-agent-workflow --ref main
```

---

## Maintainer/debug fallback

When mat-sync routing fails or you need a minimal repro outside the state machine, raw bootstrap remains valid — **not** the team default:

```txt
MULTI_AGENT_WORKFLOW_ROOT="/path/to/multi-agent-teams" bash scripts/adoption/bootstrap-workflow-into-repo.sh --mode existing-project --non-interactive "/path/to/product-repo"
```

See [`docs/guides/getting-started-existing-projects.md`](../../.mat/docs/getting-started-existing-projects.md).

---

## End-of-pass rule

Print **exactly one** fenced `txt` block with the honest next command for the current step (plan, review, or approve). For un-adopted repos, default to Step 1 plan from MAT source — not raw bootstrap and not `/mat-sync` inside the product repo.
