# MAT Worktree Remove

Remove a git worktree, stop its services, and clean up its branch.

## Usage

```
/mat-wt-remove <branch-name>
```

## Instructions

You are a **worktree cleanup agent**. Your job is to safely remove a worktree and all associated resources.

### Workflow

#### Step 1 — Identify the Worktree

```bash
git worktree list --porcelain
```

Find the worktree associated with `<branch-name>`. If not found, stop and report that no worktree exists for this branch.

#### Step 2 — Stop Running Services

Read the worktree's `.env` to find configured ports, then stop any services:

```bash
# Find and stop processes on the server port
lsof -ti :<server-port> | xargs kill -9 2>/dev/null

# Find and stop processes on the client port
lsof -ti :<client-port> | xargs kill -9 2>/dev/null
```

If no services are running, note that in the report.

#### Step 3 — Inspect dirtiness (exact path only)

```bash
# Refuse broad globs — operate on the exact worktree path from Step 1
git -C <worktree-path> status --porcelain
git -C <worktree-path> rev-list --left-right --count main...<branch-name> 2>/dev/null || true
```

If the worktree is **dirty** (uncommitted changes) or the branch has **unmerged** commits relative to the integration branch:

- **Refuse** removal and report the dirty/unmerged state.
- Proceed only when the operator **explicitly forces** cleanup (for example they said “force remove” / confirmed `--force`).

Respect Cursor’s machine-wide worktree cap (`cursor.worktreeMaxCount`, default **25**) when advising cleanup priority — remove stale exact paths first; never infer targets from broad globs.

#### Step 4 — Remove the Worktree

```bash
# Clean tree: graceful removal
git worktree remove <worktree-path>

# Dirty/unmerged: only after explicit operator force
git worktree remove <worktree-path> --force
```

#### Step 5 — Delete the Branch

```bash
# Prefer safe delete; use -D only after explicit force when unmerged
git branch -d <branch-name>
# Forced (operator-approved only):
git branch -D <branch-name>
```

#### Step 6 — Prune Stale References

```bash
git worktree prune
```

#### Step 7 — Validate Cleanup

```bash
# Confirm worktree is gone
git worktree list

# Confirm branch is gone
git branch | grep <branch-name>

# Confirm directory is gone
ls <worktree-path> 2>/dev/null
```

#### Step 8 — Report

```
## Worktree Removed

### Details
- **Branch:** <branch-name>
- **Path:** <absolute-path> — removed
- **Server Port:** <port> — freed
- **Client Port:** <port> — freed

### Cleanup Status
- [x] Services stopped on ports <port>, <port>
- [x] Git worktree removed
- [x] Git branch deleted
- [x] Stale references pruned
- [x] Directory removed from disk

### Remaining Worktrees
<output of `git worktree list`>

### Notes
<any warnings, e.g., "branch had unmerged commits that are now lost">
```

---

## Error Handling

- If the worktree is dirty or unmerged: **refuse** until the operator explicitly forces removal
- If the branch does not exist: skip branch deletion, note in report
- If services are not running: skip service stop, note in report
- If the worktree directory doesn't exist: run `git worktree prune` and note it as already cleaned
- **Never remove the main worktree** — if the user targets the main branch, refuse and explain
- **Never** expand globs or fuzzy path guesses into removal targets

## Related

- Agents Window closeout: [`docs/guides/agents-window.md`](../../.mat/docs/guides/agents-window.md)
- Create: [`mat-wt-create.md`](mat-wt-create.md) · List: [`mat-wt-list.md`](mat-wt-list.md) · Check: [`mat-wt-check.md`](mat-wt-check.md)
