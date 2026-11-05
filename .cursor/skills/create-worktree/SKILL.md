---
name: Create Worktree
description: Creates isolated git worktrees for parallel development. Use when the user asks to create a worktree, set up parallel environments, or needs to work on multiple branches simultaneously.
---

# Create Worktree

Lightweight skill for creating configured git worktrees with MAT bootstrap.

## Instructions

### Step 1: Parse the request

Extract from the user's request:

- **Branch / worktree name** (required) — passed to `bootstrap_worktree.sh` (drives observability port hints).
- Whether they need **deps install** (`--install`) or **metadata-only** (default).

### Step 2: Choose isolation path

- Cursor product: `/worktree` (one run) or `/best-of-n` (comparisons; no auto-merge), or Agents Window managed worktree.
- Manual MAT path: `/mat-wt-create <branch-name>`.

All paths should run the same MAT bootstrap so `.cursor/worktree/*` markers match.

### Step 3: Execute creation (manual path)

```text
/mat-wt-create <branch-name>
```

Bootstrap inside the new tree:

```bash
bash .cursor/hooks/bootstrap_worktree.sh --install --copy-env '<branch-name>'
# or safe default:
bash .cursor/hooks/bootstrap_worktree.sh --metadata-only '<branch-name>'
```

### Step 4: Share results

Report:

- Worktree path and branch
- Bootstrap mode used
- Contents of `.cursor/worktree/runtime.env` when present (`OBSERVABILITY_PORT`, `OBSERVABILITY_CLIENT_PORT`)
- How to start observability apps (`scripts/start-system.sh` or per-app dev servers) and how to remove the worktree later (`/mat-wt-remove`; refuse dirty unless forced)

## Examples

**Simple creation:**

"Create a worktree for feature-auth" → `/mat-wt-create feature-auth`

**Multiple worktrees:**

"I need worktrees for feature-a, feature-b, and feature-c" → Run `/mat-wt-create` for each branch; bootstrap derives distinct port hints from each name via `cksum`. Stay under Cursor’s default **25** worktree cap when advising cleanup.
