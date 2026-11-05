# MAT Worktree List

List all git worktrees with their status and configuration.

## Usage

```
/mat-wt-list
```

## Instructions

You are a **worktree status reporter**. Your job is to gather information about all active worktrees and present a comprehensive overview.

### Port hints (MAT bootstrap)

Observability port hints for a checkout live in **`<worktree-path>/.cursor/worktree/runtime.env`** as `OBSERVABILITY_PORT` and `OBSERVABILITY_CLIENT_PORT`. They are chosen collision-aware from seeds `3001 + offset` and `5173 + offset` with `offset = cksum(worktree name) mod 200` inside `bootstrap_worktree.sh`, not from any deprecated base-4000 port story and not from an optional `/mat-wt-create` numeric argument.

If `runtime.env` is missing, note that bootstrap may not have run or port selection may have been skipped. Application listen ports (if any) still come from each app’s config and `.env`, not necessarily the same values.

### Workflow

#### Step 1 — List worktrees

```bash
git worktree list --porcelain
```

Parse the output to get each worktree's path, branch, and HEAD commit.

#### Step 2 — Gather configuration for each worktree

For each worktree found:

```bash
# Observability hints written by bootstrap
cat <worktree-path>/.cursor/worktree/runtime.env 2>/dev/null

# Optional: app-level env (may or may not duplicate port vars)
grep -E "PORT|port" <worktree-path>/.env 2>/dev/null

# Dependency markers (example: Bun lockfile at repo root or under apps/*)
ls <worktree-path>/node_modules 2>/dev/null
ls <worktree-path>/apps/server/node_modules 2>/dev/null

# Branch status
cd <worktree-path> && git status --short && cd -
```

#### Step 3 — Check running services

For each worktree, if `runtime.env` defines ports:

```bash
lsof -i :<OBSERVABILITY_PORT> 2>/dev/null
lsof -i :<OBSERVABILITY_CLIENT_PORT> 2>/dev/null
```

#### Step 4 — Calculate statistics

- Total worktrees (including main)
- Active worktrees (with processes listening on hinted ports, if detectable)
- Idle worktrees

#### Step 5 — Report

```
## Worktree Status Report

### Summary
- **Total worktrees:** <count>
- **Active (hints in use):** <count>
- **Idle:** <count>

### Worktrees

#### 1. <branch-name> (main)
- **Path:** <absolute-path>
- **Branch:** <branch>
- **HEAD:** <short-sha> <commit-message>
- **runtime.env:** <OBSERVABILITY_PORT / OBSERVABILITY_CLIENT_PORT or absent>
- **Dependencies:** <installed|missing>
- **Uncommitted Changes:** <count> files

### Port map (example shape — use live runtime.env values)

| Worktree | OBSERVABILITY_PORT | OBSERVABILITY_CLIENT_PORT | Notes |
|----------|--------------------|---------------------------|-------|
| main     | (from runtime.env) | (from runtime.env)        | …     |
| feature  | (from runtime.env) | (from runtime.env)        | …     |

### Available actions
- Start stack: `bash scripts/start-system.sh` from that worktree when applicable
- Remove worktree: `/mat-wt-remove <branch-name>`
- Create new: `/mat-wt-create <branch-name>`
```

---

## Rules

- Read-only — do NOT modify any files or start/stop services
- If a worktree path no longer exists on disk, note it as "stale" and suggest pruning
- If `.env` is missing from a worktree, note it as "unconfigured" (bootstrap copies from root when possible)

## Related

- Agents Window mapping: [`docs/guides/agents-window.md`](../../.mat/docs/guides/agents-window.md)
- Create: [`mat-wt-create.md`](mat-wt-create.md) · Check: [`mat-wt-check.md`](mat-wt-check.md) · Remove: [`mat-wt-remove.md`](mat-wt-remove.md)
