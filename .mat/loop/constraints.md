# MAT loop constraints (operator template)

Advisory guardrails for orchestrated slice loops. Copy or customize under `.mat/loop/` on adoption. File handoffs (`docs/current-plan.md`, `build-result.md`, `verify-result.md`) and MAO gates remain **authoritative**; loop policy is opt-in (`CURSOR_MAT_LOOP_POLICY=1`).

Canonical reference: [`docs/reference/loop-policy.md`](../../docs/reference/loop-policy.md) on the MAT source tree, or `.mat/docs/loop-policy.md` when packaged on adopted trees.

## Path denylist

Agents in a loop must **not** write, delete, or rename these paths without explicit operator approval:

| Pattern | Rationale |
|---------|-----------|
| `.env`, `.env.*` (except `.env.sample`) | Secrets and local credentials |
| `**/*credentials*`, `**/*secret*`, `**/*.pem`, `**/*.key` | Key material |
| `.git/` | Git internals |
| `node_modules/`, `vendor/`, `.venv/` | Dependency trees (regenerate, do not hand-edit) |
| `artifacts/**` (except loop manifest paths when policy is on) | Local runtime / audit (gitignored) |
| Product root `README.md`, `CHANGELOG.md`, `AGENTS.md` on **existing-project** adoption | Product-owned identity files |

Narrow edits to the active slice scope listed in `docs/current-plan.md`.

## Max attempts

- Default per-`slice_class` budgets live in [budget.md](budget.md) (mirrors `scripts/mat_loop_policy.py` / loop-policy.md).
- Parent orchestrator owns **escalate** and **stop** when budgets exhaust or `terminal` is set on the manifest.
- Same `failure_fingerprint` **≥ 2** times → escalate (see loop-policy.md).

## No auto-merge

- Loop retries do **not** imply permission to merge, push, or open/merge PRs.
- Commits require explicit operator request; push and merge stay human-gated unless the mission spec says otherwise.
- Parallel worktrees each use their own manifest `run_id`; reconcile at slice boundaries only.

## Maker-checker

- **Builder** may mutate implementation and `build-result.md`.
- **Verifier** stays read-only on implementation files.
- **Parent** owns subagent spawn, MAO todo transitions, and loop `evaluate()` follow-up — hooks do not auto-spawn from loop output.
