# MAT Worktree Check

Run a quick health check over local git worktrees.

## Usage

```text
/mat-wt-check
```

## Instructions

1. Run:

```bash
bash scripts/check-worktrees.sh
```

2. Return the script output in a concise report.
3. If warnings appear, suggest the smallest corrective next step:
   - stale worktree path -> `git worktree prune`
   - missing bootstrap marker -> rerun `bash .cursor/hooks/bootstrap_worktree.sh --metadata-only <name>` (or `--install --copy-env` when deps are needed)
   - port collision warning -> rerun bootstrap in one worktree to refresh runtime hints

## Rules

- Read-only command: do not create/remove worktrees.
- Do not kill processes.
- Keep the response short and operational.

## Related

- Agents Window mapping: [`docs/guides/agents-window.md`](../../.mat/docs/guides/agents-window.md)
- Create: [`mat-wt-create.md`](mat-wt-create.md) · List: [`mat-wt-list.md`](mat-wt-list.md) · Remove: [`mat-wt-remove.md`](mat-wt-remove.md)
