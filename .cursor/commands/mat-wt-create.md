# MAT Worktree Create

Create a new git worktree for isolated parallel development.

## Usage

```
/mat-wt-create <branch-name>
```

- `branch-name`: Name for the new branch and worktree (required).

There is **no** `port-offset` argument wired into MAT bootstrap. Observability port hints are derived inside `.cursor/hooks/bootstrap_worktree.sh` from the worktree name (see below).

## Cursor vs MAT (parity)

| Path | Who creates the checkout | MAT bootstrap |
|------|--------------------------|---------------|
| **Agents Window** managed worktree | Cursor | Run bootstrap in the tree (default `--metadata-only`) |
| **`/worktree`** | Cursor (one isolated run) | Same markers via bootstrap |
| **`/best-of-n`** | Cursor (parallel comparisons; does **not** auto-merge) | Same markers per comparison tree |
| **`/mat-wt-create` / manual `git worktree add`** | Operator / this command | Prefer `--install --copy-env` when deps + env copy are intentional |

Cursor can manage worktrees for Agents Window / `/worktree` / `/best-of-n` ([Cursor Worktrees](https://cursor.com/docs/configuration/worktrees)). It does **not** invent a new git worktree for every parallel Task subagent unless you (or those product flows) create one. Machine-wide default cap: **`cursor.worktreeMaxCount` = 25**.

**This command** is the **manual** path: `git worktree add` (or your wrapper) plus MAT bootstrap so hooks and observability see consistent `.cursor/worktree/*` markers.

## Bootstrap modes

```bash
# Default / safe: markers + runtime.env only (no package/network/env copy)
bash .cursor/hooks/bootstrap_worktree.sh --metadata-only '<branch-name>'

# Full setup: print planned installs, then run them; opt-in env copy
bash .cursor/hooks/bootstrap_worktree.sh --install --copy-env '<branch-name>'

# Validate markers / runtime.env (no installs)
bash .cursor/hooks/bootstrap_worktree.sh --check '<branch-name>'
```

## Instructions

You are a **worktree creation agent**. Your job is to set up a functional isolated development environment in a git worktree.

### Observability port hints (actual bootstrap contract)

After the worktree exists, bootstrap writes `.cursor/worktree/runtime.env` with collision-aware values:

| Variable | Meaning |
|----------|---------|
| `OBSERVABILITY_PORT` | API / event sink port chosen from a window starting at `3001 + offset` |
| `OBSERVABILITY_CLIENT_PORT` | Dashboard dev port chosen from a window starting at `5173 + offset` |

Where `offset = (cksum of worktree name) mod 200`, then `pick_free_port` selects the first free port in each window (see `scripts/lib/pick-free-port.sh`). These are **hints** for local dev, not a guarantee that your app processes bind to them unless your stack reads `runtime.env`.

Prefer reading `.cursor/worktree/runtime.env` over hand-editing duplicate port fields in `.env` unless your project explicitly requires app-level `SERVER_PORT` / `CLIENT_PORT` there.

### Workflow

#### Step 1 — Validate prerequisites

```bash
git rev-parse --git-dir          # Confirm we're in a git repo
git worktree list                # Check existing worktrees
git branch -a                    # Check existing branches
```

If the branch already exists or a worktree path already exists, stop and report the conflict.

#### Step 2 — Create worktree

```bash
# Example: sibling directory next to the main checkout
git worktree add ../<repo-name>-<branch-name> -b <branch-name>
```

Adjust the path to match your layout; some operators use Cursor-managed paths via `/worktree` or the Agents Window instead.

#### Step 3 — Bootstrap in the new worktree

```bash
cd ../<repo-name>-<branch-name>

# Full create flow: install deps + optional env copy from main checkout
bash .cursor/hooks/bootstrap_worktree.sh --install --copy-env '<branch-name>'
```

For metadata-only (no network/package calls), use `--metadata-only` instead. `--install` prints **Planned** commands before executing. `--copy-env` is required to copy `.env` / `.mat.env` when missing.

#### Step 4 — Validate setup

```bash
git worktree list
bash .cursor/hooks/bootstrap_worktree.sh --check '<branch-name>'
test -f .cursor/worktree/runtime.env && cat .cursor/worktree/runtime.env
test -f .cursor/worktree/name && cat .cursor/worktree/name
```

#### Step 5 — Report

Produce a report including branch, absolute path, bootstrap mode used, contents of `runtime.env` (if present), and next steps to open the folder in Cursor and start apps if applicable.

---

## Error handling

- Branch or path conflict: stop; suggest a new name.
- Dependency install failure: report; worktree may still be usable for read-only / metadata-only work.
- Bootstrap failure: report; do not claim ports were written if `runtime.env` is absent.

## Related

- Agents Window mapping: [`docs/guides/agents-window.md`](../../.mat/docs/guides/agents-window.md) (one active slice per worktree/branch).
- Procedural playbook: [`.cursor/skills/create-worktree/SKILL.md`](../skills/create-worktree/SKILL.md) (hybrid with this command; see [skills vs commands routing](../../.mat/docs/decision-record.md#p1-audit--skills-vs-commands-routing)).
- Example native setup keys: [`.cursor/worktrees.json.example`](../worktrees.json.example).
- Spec: [`specs/worktree-native-wrapper-v1.md`](../../.mat/docs/specs/worktree-native-wrapper-v1.md).
- MAT strategy (hybrid): [`docs/reference/decision-record.md`](../../.mat/docs/decision-record.md#p2-audit--worktree-wrapper-strategy).
