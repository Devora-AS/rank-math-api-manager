---
name: Worktree Manager
description: Comprehensive git worktree management for parallel development. Use when creating, removing, listing, or managing worktrees and parallel environments.
---

# Worktree Manager

Complete worktree lifecycle management for parallel development environments with Cursor-managed or manual git isolation plus MAT bootstrap metadata.

## When to use

- **Create** a new worktree for parallel development
- **Remove** an existing worktree
- **List** all worktrees and their status
- **Check** worktree configuration or status

## Operations

| Operation | Command | When to use |
|-----------|---------|-------------|
| **Create** | `/mat-wt-create` | New parallel environment needed (manual path) |
| **List** | `/mat-wt-list` | See existing worktrees and `runtime.env` hints |
| **Remove** | `/mat-wt-remove` | Delete a worktree (exact path; refuse dirty unless forced) |
| **Check** | `/mat-wt-check` | Health / collision checks |

## Product parity

| Cursor product | Role | MAT layer |
|----------------|------|-----------|
| Agents Window managed worktree | Isolation | `bootstrap_worktree.sh` markers |
| `/worktree` | One isolated run | Same markers |
| `/best-of-n` | Parallel comparisons (no auto-merge) | Same markers per tree |
| `/mat-wt-*` + `git worktree` | Manual operator path | Create / list / check / remove |

Default machine-wide cap: `cursor.worktreeMaxCount` = **25**.

## Decision tree

### User wants to CREATE

Keywords: create, new, setup, make, build, start, initialize

Action: Prefer Cursor `/worktree` or Agents Window when product isolation is enough; use `/mat-wt-create` for explicit manual trees. After the checkout exists, run:

```bash
bash .cursor/hooks/bootstrap_worktree.sh --metadata-only '<name>'
# or full deps:
bash .cursor/hooks/bootstrap_worktree.sh --install --copy-env '<name>'
```

### User wants to LIST

Keywords: list, show, display, status, check, view

Action: Use `/mat-wt-list`; read `.cursor/worktree/runtime.env` per tree for `OBSERVABILITY_PORT` / `OBSERVABILITY_CLIENT_PORT`.

### User wants to REMOVE

Keywords: remove, delete, cleanup, destroy, stop, kill

Action: Use `/mat-wt-remove` with `<branch-name>`. Refuse dirty/unmerged exact-path removal unless the operator explicitly forces it.

## Observability port hints

Bootstrap writes `.cursor/worktree/runtime.env` using seeds **`3001 + offset`** and **`5173 + offset`** where `offset = cksum(worktree name) mod 200`, then picks free ports in a bounded window. The shipped script does **not** implement any legacy base-4000 observability port ladder.

## Important notes

- Cursor **can** create managed worktrees (Agents Window, `/worktree`, `/best-of-n`); it does not invent one per every parallel Task subagent without those flows.
- Default bootstrap mode is **`--metadata-only`** (zero package/network calls). Use `--install` when dependency install is intentional.
- Slash commands document the flow; hooks do not spawn worktrees.
- Use `git worktree list` to verify worktree state.
- Example native keys: `.cursor/worktrees.json.example`.
